"""
Educational Service
Main service for handling educational queries using RAG system
"""

import logging
import os
from typing import Dict, List, Optional, Any, Tuple
import asyncio

from ..rag.qdrant_manager import QdrantEducationManager
from ..rag.embeddings import EmbeddingManager
from ..rag.retriever import EducationalRetriever, RetrievalResult
from ..education.textbook_ingestion import TextbookIngestionPipeline
from .shared_component_manager import get_shared_educational_components, SharedEducationalComponents

logger = logging.getLogger(__name__)


class EducationService:
    """Main service for educational content retrieval and answer generation"""

    def __init__(self):
        self.qdrant_manager = QdrantEducationManager()
        self.embedding_manager = EmbeddingManager()
        self.retriever = None
        self.ingestion_pipeline = None

        self.is_initialized = False
        # Always default to Grade 6 Science
        self.current_student_grade = 6
        self.current_subject = "science"

        # Default settings
        self.default_retrieval_limit = 5
        self.min_score_threshold = 0.5  # Lowered for better Grade 6 content retrieval

    async def initialize(self, use_shared_components: bool = True) -> bool:
        """Initialize the education service"""
        try:
            logger.info("Initializing Education Service...")

            # Check if we can use shared components to avoid expensive initialization
            if use_shared_components and SharedEducationalComponents.is_initialized():
                logger.info("Using shared educational components...")
                
                # Get shared components
                components = get_shared_educational_components()
                self.qdrant_manager = components['qdrant_manager']
                self.embedding_manager = components['embedding_manager']
                self.ingestion_pipeline = components['ingestion_pipeline']
            else:
                logger.info("Initializing components individually...")
                
                # Initialize Qdrant manager (for both grade_06_science and grade_10_science)
                qdrant_success = await self.qdrant_manager.initialize_grade6_and_grade10_science()
                if not qdrant_success:
                    logger.error("Failed to initialize Qdrant collections")
                    return False

                # Initialize embedding manager
                embedding_success = await self.embedding_manager.initialize()
                if not embedding_success:
                    logger.error("Failed to initialize embedding manager")
                    return False

                # Initialize ingestion pipeline (lightweight - reuse components)
                self.ingestion_pipeline = TextbookIngestionPipeline()
                self.ingestion_pipeline.qdrant_manager = self.qdrant_manager  # Reuse initialized manager
                self.ingestion_pipeline.embedding_manager = self.embedding_manager  # Reuse initialized manager
                self.ingestion_pipeline.is_initialized = True  # Skip duplicate initialization
                logger.info("Textbook ingestion pipeline configured (reusing components)")

            # Initialize retriever with the (potentially shared) components
            self.retriever = EducationalRetriever(
                self.qdrant_manager.client,
                self.embedding_manager
            )

            self.is_initialized = True
            logger.info("Education Service initialized successfully")

            # Log collection statistics only if not using shared components
            if not (use_shared_components and SharedEducationalComponents.is_initialized()):
                stats = await self.qdrant_manager.get_collection_stats()
                logger.info(f"Available collections: {stats['total_collections']}")
                logger.info(f"Total educational content points: {stats['total_points']}")

            return True

        except Exception as e:
            logger.error(f"Failed to initialize Education Service: {e}")
            return False

    async def set_student_context(self, grade: int, subject: Optional[str] = None) -> bool:
        """Set current student context (grade and subject)"""
        try:
            if grade < 6 or grade > 12:
                logger.error(f"Invalid grade: {grade}. Must be between 6 and 12.")
                return False

            self.current_student_grade = grade
            self.current_subject = subject

            logger.info(f"Student context set: Grade {grade}, Subject: {subject or 'Any'}")
            return True

        except Exception as e:
            logger.error(f"Failed to set student context: {e}")
            return False

    async def answer_question(
        self,
        question: str,
        grade: Optional[int] = None,
        subject: Optional[str] = None,
        include_examples: bool = True,
        include_visual_aids: bool = True
    ) -> Dict[str, Any]:
        """Answer an educational question using RAG retrieval"""

        if not self.is_initialized:
            return {"error": "Education service not initialized"}

        try:
            # Use provided context or fall back to current context
            student_grade = grade or self.current_student_grade
            target_subject = subject or self.current_subject

            # Always ensure we're working with Grade 6 science
            student_grade = 6
            target_subject = "science"

            logger.info(f"Answering Grade 6 science question: {question}")

            # Enhanced detection logic - check for chapter and/or activity queries
            import re
            chapter_match = re.search(r'chapter\s*(\d+)', question.lower())
            activity_match = re.search(r'activity\s*(\d+(?:\.\d+)?)', question.lower())

            if chapter_match:
                chapter_number = int(chapter_match.group(1))

                if activity_match:
                    # Both chapter and activity specified - use specific activity search
                    activity_number = activity_match.group(1)
                    logger.info(f"🎯 SERVICE: Detected chapter + activity query: Chapter {chapter_number}, Activity {activity_number}")

                    # Use combined chapter + activity search
                    activity_result = await self.search_by_chapter_and_activity(
                        chapter_number=chapter_number,
                        activity_number=activity_number,
                        grade=student_grade,
                        subject=target_subject
                    )

                    # If we found specific activity content, return it
                    if activity_result and "error" not in activity_result and len(activity_result.get("answer", "")) > 50:
                        logger.info(f"✅ SERVICE: Successfully retrieved Chapter {chapter_number} Activity {activity_number} content")
                        return activity_result
                    else:
                        logger.info(f"⚠️ SERVICE: Activity {activity_number} not found in Chapter {chapter_number}, falling back to chapter search")

                # Chapter-only query or activity search failed
                logger.info(f"🎯 SERVICE: Detected chapter query: Chapter {chapter_number}")

                # Use metadata filtering to get chapter content directly
                chapter_result = await self.search_by_chapter(
                    chapter_number=chapter_number,
                    grade=student_grade,
                    subject=target_subject
                )

                # If we found good chapter content, return it
                if chapter_result and "error" not in chapter_result and len(chapter_result.get("answer", "")) > 100:
                    logger.info(f"✅ SERVICE: Successfully retrieved Chapter {chapter_number} content via metadata")
                    return chapter_result
                else:
                    logger.info(f"⚠️ SERVICE: Chapter {chapter_number} metadata search failed, falling back to semantic search")

            # Retrieve relevant content using semantic search
            results = await self.retriever.retrieve(
                query=question,
                grade=student_grade,
                subject=target_subject,
                limit=self.default_retrieval_limit,
                include_related=include_examples or include_visual_aids
            )

            if not results:
                return {
                    "answer": "Hmm, that's a great question! I don't have information about that specific topic in my science books right now. Can you ask me about living things, plants, animals, magnets, materials, or other 6th grade science topics? I'd love to help you learn!",
                    "confidence": 0.0,
                    "sources": [],
                    "suggestions": await self._get_topic_suggestions(question, student_grade, target_subject)
                }

            # Filter results by confidence threshold
            high_confidence_results = [r for r in results if r.score >= self.min_score_threshold]

            if not high_confidence_results:
                return {
                    "answer": "I found some science topics that might be related, but I want to make sure I give you the best answer! Can you ask your question in a different way? For example, you could ask 'What are living things?' or 'How do magnets work?'",
                    "confidence": max([r.score for r in results]) if results else 0.0,
                    "sources": [],
                    "suggestions": await self._get_topic_suggestions(question, student_grade, target_subject)
                }

            # Generate educational answer
            answer_data = await self._generate_educational_answer(
                question, high_confidence_results, student_grade,
                include_examples=include_examples,
                include_visual_aids=include_visual_aids
            )

            return answer_data

        except Exception as e:
            logger.error(f"Failed to answer question: {e}")
            return {"error": f"Failed to process question: {str(e)}"}

    async def search_visual_content(
        self,
        query: str,
        grade: Optional[int] = None,
        subject: Optional[str] = None,
        limit: int = 5
    ) -> Dict[str, Any]:
        """
        Search for visual content (figures, tables) using text query

        Args:
            query: Text query (e.g., "show me diagram of photosynthesis")
            grade: Student grade level
            subject: Subject area
            limit: Number of results to return

        Returns:
            Dictionary with visual content results
        """
        try:
            student_grade = grade or self.current_student_grade
            target_subject = subject or self.current_subject

            if not student_grade or not target_subject:
                return {"error": "Grade and subject must be specified"}

            # Import visual embedding manager
            from ..rag.visual_embeddings import VisualEmbeddingManager

            # Initialize visual manager if not already
            visual_manager = VisualEmbeddingManager()
            if not visual_manager.is_initialized():
                visual_manager.initialize()

            # Determine visual collection name
            collection_name = f"grade_{student_grade:02d}_{target_subject}_visual"

            # Search for visual content
            results = await visual_manager.search_visual_content(
                query=query,
                qdrant_client=self.qdrant_manager.client,
                collection_name=collection_name,
                limit=limit
            )

            if not results:
                return {
                    "visual_aids": [],
                    "message": "No visual content found for this query. Try asking about diagrams, figures, or tables in your textbook."
                }

            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "type": result.get("type", "unknown"),
                    "id": result.get("figure_id") or result.get("id"),
                    "caption": result.get("caption", "No caption available"),
                    "page": result.get("page", 0),
                    "relevance_score": result.get("score", 0.0),
                    "context": result.get("nearby_text", "")[:200]  # Truncate to 200 chars
                })

            return {
                "visual_aids": formatted_results,
                "total_found": len(formatted_results),
                "message": f"Found {len(formatted_results)} visual aids related to your query."
            }

        except Exception as e:
            logger.error(f"Failed to search visual content: {e}")
            return {"error": f"Failed to search visual content: {str(e)}"}

    async def explain_concept(
        self,
        concept: str,
        grade: Optional[int] = None,
        subject: Optional[str] = None,
        detail_level: str = "medium"
    ) -> Dict[str, Any]:
        """Explain a specific concept with appropriate detail level"""

        try:
            student_grade = grade or self.current_student_grade
            if not student_grade:
                return {"error": "No grade specified"}

            # Build explanation query
            explanation_query = f"explain {concept} definition meaning"

            # Get concept explanation
            results = await self.retriever.retrieve(
                query=explanation_query,
                grade=student_grade,
                subject=subject or self.current_subject,
                limit=3
            )

            if not results:
                return {"error": f"Could not find explanation for concept: {concept}"}

            # Get related examples
            example_results = await self.retriever.retrieve(
                query=f"{concept} example problem demonstration",
                grade=student_grade,
                subject=subject or self.current_subject,
                limit=2
            )

            # Generate structured explanation
            explanation = await self._generate_concept_explanation(
                concept, results, example_results, student_grade, detail_level
            )

            return explanation

        except Exception as e:
            logger.error(f"Failed to explain concept {concept}: {e}")
            return {"error": f"Failed to explain concept: {str(e)}"}

    async def get_practice_problems(
        self,
        topic: str,
        grade: Optional[int] = None,
        subject: Optional[str] = None,
        difficulty: str = "medium",
        count: int = 3
    ) -> Dict[str, Any]:
        """Get practice problems for a specific topic"""

        try:
            student_grade = grade or self.current_student_grade
            if not student_grade:
                return {"error": "No grade specified"}

            # Search for exercises and problems
            problem_query = f"{topic} exercise problem practice {difficulty}"

            results = await self.retriever.retrieve(
                query=problem_query,
                grade=student_grade,
                subject=subject or self.current_subject,
                limit=count * 2  # Get more to filter for quality
            )

            # Filter for exercise/problem content
            problem_results = [
                r for r in results
                if r.metadata.get("content_type") in ["exercise", "example", "problem"]
            ]

            if not problem_results:
                return {"error": f"No practice problems found for topic: {topic}"}

            # Format practice problems
            practice_data = await self._format_practice_problems(
                problem_results[:count], topic, student_grade
            )

            return practice_data

        except Exception as e:
            logger.error(f"Failed to get practice problems: {e}")
            return {"error": f"Failed to get practice problems: {str(e)}"}

    async def get_step_by_step_solution(
        self,
        problem: str,
        grade: Optional[int] = None,
        subject: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get step-by-step solution for a problem"""

        try:
            student_grade = grade or self.current_student_grade
            if not student_grade:
                return {"error": "No grade specified"}

            # Search for solutions and examples
            solution_query = f"{problem} solution steps method solve"

            results = await self.retriever.retrieve(
                query=solution_query,
                grade=student_grade,
                subject=subject or self.current_subject,
                limit=3
            )

            if not results:
                return {"error": "Could not find solution method for this problem"}

            # Generate step-by-step solution
            solution_data = await self._generate_step_solution(
                problem, results, student_grade
            )

            return solution_data

        except Exception as e:
            logger.error(f"Failed to get step-by-step solution: {e}")
            return {"error": f"Failed to get solution: {str(e)}"}

    async def search_by_topic(
        self,
        topic: str,
        grade: Optional[int] = None,
        subject: Optional[str] = None,
        content_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Search for content by specific topic"""

        try:
            student_grade = grade or self.current_student_grade
            target_subject = subject or self.current_subject

            if not student_grade or not target_subject:
                return {"error": "Grade and subject must be specified"}

            results = await self.retriever.search_by_topic(
                topic=topic,
                grade=student_grade,
                subject=target_subject,
                limit=10
            )

            # Filter by content type if specified
            if content_type:
                results = [r for r in results if r.metadata.get("content_type") == content_type]

            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "content": result.content,
                    "page_reference": f"Page {result.metadata.get('page_number', 'Unknown')}",
                    "textbook": result.metadata.get('textbook_name', 'Unknown'),
                    "chapter": result.metadata.get('chapter', ''),
                    "section": result.metadata.get('section', ''),
                    "content_type": result.metadata.get('content_type', 'text')
                })

            return {
                "topic": topic,
                "results": formatted_results,
                "total_found": len(formatted_results)
            }

        except Exception as e:
            logger.error(f"Failed to search by topic: {e}")
            return {"error": f"Failed to search: {str(e)}"}

    async def get_curriculum_overview(
        self,
        grade: int,
        subject: str,
        chapter: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get curriculum overview for a grade and subject"""

        try:
            curriculum = await self.retriever.get_curriculum_content(
                grade=grade,
                subject=subject,
                chapter=chapter
            )

            # Format curriculum data
            formatted_curriculum = {}
            for content_type, results in curriculum.items():
                formatted_curriculum[content_type] = []
                for result in results[:10]:  # Limit to 10 items per type
                    formatted_curriculum[content_type].append({
                        "title": result.metadata.get('section_title', 'Untitled'),
                        "chapter": result.metadata.get('chapter', ''),
                        "page": result.metadata.get('page_number', 0),
                        "textbook": result.metadata.get('textbook_name', ''),
                        "preview": result.content[:200] + "..." if len(result.content) > 200 else result.content
                    })

            return {
                "grade": grade,
                "subject": subject,
                "chapter": chapter,
                "curriculum": formatted_curriculum
            }

        except Exception as e:
            logger.error(f"Failed to get curriculum overview: {e}")
            return {"error": f"Failed to get curriculum: {str(e)}"}

    # Helper methods for answer generation

    async def _generate_educational_answer(
        self,
        question: str,
        results: List[RetrievalResult],
        grade: int,
        include_examples: bool = True,
        include_visual_aids: bool = True
    ) -> Dict[str, Any]:
        """Generate a comprehensive educational answer with formatting"""

        # Combine content from top results
        main_content = []
        sources = []
        examples = []
        visual_aids = []
        key_concepts = set()

        for result in results:
            main_content.append(result.content)

            # Add source information
            sources.append({
                "textbook": result.metadata.get("textbook_name", "Unknown"),
                "page": result.metadata.get("page_number", "Unknown"),
                "chapter": result.metadata.get("chapter", ""),
                "section": result.metadata.get("section_title", "")
            })

            # Collect key concepts
            if result.metadata.get("key_concepts"):
                key_concepts.update(result.metadata.get("key_concepts", []))

            # Collect examples if requested
            if include_examples and result.related_content:
                for related in result.related_content:
                    if related.get("type") == "example":
                        examples.append(related.get("content", ""))

            # Collect visual aids if requested
            if include_visual_aids and result.metadata.get("figure_refs"):
                visual_aids.extend(result.metadata.get("figure_refs", []))

        # Create the main answer with grade-appropriate formatting
        base_answer = self._format_answer_for_grade(main_content, grade)

        # Apply answer template formatting based on question type
        try:
            from ..rag.answer_templates import detect_question_type, AnswerFormatter

            question_type = detect_question_type(question)
            formatter = AnswerFormatter()

            # Prepare content for formatting
            formatted_content = {
                'answer': base_answer,
                'key_concepts': list(key_concepts)
            }

            # Format answer based on question type
            formatted_answer = formatter.format_answer(formatted_content, question_type)

            # Use formatted answer if it's substantially different and improves clarity
            if formatted_answer and len(formatted_answer) > len(base_answer) * 0.8:
                answer = formatted_answer
            else:
                answer = base_answer

        except Exception as e:
            # Fallback to base answer if formatting fails
            import logging
            logging.getLogger(__name__).warning(f"Answer formatting failed: {e}")
            answer = base_answer

        # Calculate confidence score
        confidence = sum(r.score for r in results) / len(results) if results else 0.0

        # QUICK WIN 2: Clean and validate response for voice output
        cleaned_answer = self.validate_and_clean_response(answer)

        response = {
            "answer": cleaned_answer,
            "confidence": confidence,
            "sources": sources,
            "grade_level": grade
        }

        # Add examples if available
        if examples:
            response["examples"] = examples[:2]  # Limit to 2 examples

        # Add visual aid references if available
        if visual_aids:
            response["visual_aids"] = list(set(visual_aids))  # Remove duplicates

        # Add follow-up suggestions
        response["follow_up_suggestions"] = await self._generate_follow_up_questions(question, results)

        return response

    async def _generate_concept_explanation(
        self,
        concept: str,
        definition_results: List[RetrievalResult],
        example_results: List[RetrievalResult],
        grade: int,
        detail_level: str
    ) -> Dict[str, Any]:
        """Generate a structured concept explanation"""

        explanation_parts = []

        # Definition/Basic explanation
        if definition_results:
            definition = definition_results[0].content
            explanation_parts.append(f"**Definition**: {definition}")

        # Key points (from additional results)
        if len(definition_results) > 1:
            key_points = []
            for result in definition_results[1:]:
                key_points.append(result.content)

            if key_points:
                explanation_parts.append(f"**Key Points**: {' '.join(key_points)}")

        # Examples
        if example_results:
            examples_text = []
            for result in example_results:
                examples_text.append(result.content)

            if examples_text:
                explanation_parts.append(f"**Examples**: {' '.join(examples_text)}")

        # Combine explanation
        full_explanation = "\n\n".join(explanation_parts)

        return {
            "concept": concept,
            "explanation": full_explanation,
            "grade_level": grade,
            "detail_level": detail_level,
            "sources": [
                {
                    "textbook": r.metadata.get("textbook_name", "Unknown"),
                    "page": r.metadata.get("page_number", "Unknown")
                }
                for r in definition_results + example_results
            ]
        }

    async def _format_practice_problems(
        self,
        problem_results: List[RetrievalResult],
        topic: str,
        grade: int
    ) -> Dict[str, Any]:
        """Format practice problems for student use"""

        problems = []
        for i, result in enumerate(problem_results):
            problem_data = {
                "problem_number": i + 1,
                "problem_text": result.content,
                "topic": topic,
                "difficulty": result.metadata.get("difficulty_level", "medium"),
                "source": {
                    "textbook": result.metadata.get("textbook_name", "Unknown"),
                    "page": result.metadata.get("page_number", "Unknown")
                }
            }

            # Add hints if available
            if result.metadata.get("prerequisites"):
                problem_data["hints"] = result.metadata.get("prerequisites")

            problems.append(problem_data)

        return {
            "topic": topic,
            "grade": grade,
            "problems": problems,
            "total_problems": len(problems)
        }

    async def _generate_step_solution(
        self,
        problem: str,
        solution_results: List[RetrievalResult],
        grade: int
    ) -> Dict[str, Any]:
        """Generate step-by-step solution"""

        if not solution_results:
            return {"error": "No solution method found"}

        # Use the best matching result
        best_result = solution_results[0]

        # Try to extract steps from content
        steps = self._extract_solution_steps(best_result.content)

        return {
            "problem": problem,
            "steps": steps,
            "explanation": best_result.content,
            "grade_level": grade,
            "source": {
                "textbook": best_result.metadata.get("textbook_name", "Unknown"),
                "page": best_result.metadata.get("page_number", "Unknown")
            }
        }

    def _extract_solution_steps(self, content: str) -> List[str]:
        """Extract step-by-step instructions from content"""
        # Simple step extraction - could be enhanced with NLP
        steps = []

        # Look for numbered steps
        import re
        step_patterns = [
            r'Step \d+[:\.].*?(?=Step \d+|$)',
            r'\d+\.\s+.*?(?=\d+\.|$)',
            r'First.*?(?=Second|Next|Then|Finally|$)',
            r'Second.*?(?=Third|Next|Then|Finally|$)',
        ]

        for pattern in step_patterns:
            matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
            if matches:
                steps.extend([match.strip() for match in matches])
                break

        # If no structured steps found, split by sentences
        if not steps:
            sentences = content.split('.')
            steps = [s.strip() for s in sentences if len(s.strip()) > 20]

        return steps[:10]  # Limit to 10 steps

    def _format_answer_for_grade(self, content_pieces: List[str], grade: int) -> str:
        """Format answer appropriately for Grade 6 students"""
        # Combine content pieces
        combined_content = " ".join(content_pieces)

        # Always simplify for Grade 6 science (ages 11-12)
        simplified_content = self._simplify_language(combined_content)

        # Add examples for complex topics
        with_examples = self._add_examples_for_complex_topics(simplified_content)

        # Add encouraging and age-appropriate language
        grade6_friendly = self._make_grade6_friendly(with_examples)

        # Make TTS-friendly for Indian English
        tts_friendly = self._make_tts_friendly_indian_english(grade6_friendly)

        return tts_friendly

    def _simplify_language(self, text: str) -> str:
        """Simplify language for Grade 6 students (ages 11-12)"""
        # Extensive replacements for Grade 6 appropriate language
        replacements = {
            # Academic terms to simpler ones
            "utilize": "use",
            "demonstrate": "show",
            "consequently": "so",
            "furthermore": "also",
            "therefore": "so",
            "however": "but",
            "approximately": "about",
            "acquire": "get",
            "accumulate": "collect",
            "adequate": "enough",
            "adjacent": "next to",
            "alternative": "other choice",
            "analyze": "study",
            "apparatus": "equipment",
            "appropriate": "right",
            "ascertain": "find out",
            "calculate": "work out",
            "commence": "start",
            "comprehend": "understand",
            "conclude": "end",
            "construct": "build",
            "determine": "find",
            "establish": "set up",
            "evaluate": "judge",
            "examine": "look at",
            "exceed": "go over",
            "fundamental": "basic",
            "illustrate": "show",
            "implement": "do",
            "indicate": "show",
            "investigate": "look into",
            "maintain": "keep",
            "obtain": "get",
            "participate": "take part",
            "previously": "before",
            "procedure": "steps",
            "remainder": "what's left",
            "represent": "stand for",
            "require": "need",
            "subsequently": "then",
            "sufficient": "enough",
            "technique": "way",
            "terminate": "stop",
            "transform": "change",
            # Science-specific terms for Grade 6
            "organism": "living thing",
            "habitat": "home where animals live",
            "environment": "everything around us",
            "characteristic": "special thing about",
            "observation": "what you see",
            "experiment": "test to find out",
            "microscope": "tool to see tiny things",
            "photosynthesis": "how plants make food from sunlight",
            "respiration": "breathing",
            "reproduction": "making babies",
            "classify": "put into groups",
            "temperature": "how hot or cold",
            "magnetic": "can stick to magnets",
            "transparent": "see-through",
            "opaque": "cannot see through",
            "dissolve": "mix completely with water",
            "evaporation": "water turning into air",
            "condensation": "water drops forming",
            "nutrients": "good things in food",
            "vertebrate": "animal with backbone",
            "invertebrate": "animal without backbone"
        }

        simplified = text
        for complex_word, simple_word in replacements.items():
            # Use word boundaries to avoid partial replacements
            import re
            pattern = r'\b' + re.escape(complex_word) + r'\b'
            simplified = re.sub(pattern, simple_word, simplified, flags=re.IGNORECASE)

        return simplified

    def _make_grade6_friendly(self, text: str) -> str:
        """Make content friendly and encouraging for 6th grade students"""

        # Add encouraging phrases at the beginning
        encouraging_starters = [
            "Great question! Let me explain this in a simple way.",
            "This is a fun science topic! Here's what you need to know:",
            "You're learning something really cool! Here's how it works:",
            "This is easier than it looks! Let me break it down:",
            "Nice thinking! Let me help you understand this:",
            "Science is amazing! Here's what's happening:",
            "That's a wonderful science question! Let me explain:"
        ]

        # Check if text already starts with an encouraging phrase
        starts_with_encouragement = any(
            text.strip().startswith(starter.split('!')[0])
            for starter in encouraging_starters
        )

        if not starts_with_encouragement and len(text.strip()) > 20:
            import random
            starter = random.choice(encouraging_starters)
            text = f"{starter} {text}"

        # Make sentences shorter and clearer
        sentences = text.split('.')
        improved_sentences = []

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # Break very long sentences
            if len(sentence) > 100 and ',' in sentence:
                parts = sentence.split(',')
                for i, part in enumerate(parts):
                    part = part.strip()
                    if i == 0:
                        improved_sentences.append(part)
                    else:
                        improved_sentences.append(f"Also, {part}")
            else:
                improved_sentences.append(sentence)

        # Join sentences back with proper punctuation
        result = '. '.join(improved_sentences)
        if result and not result.endswith('.'):
            result += '.'

        # Add encouraging endings for explanations
        if len(result) > 100:
            encouraging_endings = [
                " Keep practicing and you'll get even better at this!",
                " You're doing great learning science!",
                " Science can be fun when you understand it like this!",
                " Great job working through this topic!",
                " You've got this - keep up the good work!",
                " Science is all around us - keep exploring!"
            ]

            if not any(result.endswith(ending.strip()) for ending in encouraging_endings):
                import random
                ending = random.choice(encouraging_endings)
                result += ending

        return result

    def _add_examples_for_complex_topics(self, text: str, topic_results: list = None) -> str:
        """Add simple examples to help explain complex science topics"""

        # Add examples for common complex topics
        example_mappings = {
            "magnet": "For example, a magnet can pick up paper clips or stick to your refrigerator.",
            "living things": "For example, plants, animals, and people are all living things because they grow, need food, and can have babies.",
            "non-living things": "For example, rocks, water, and toys are non-living because they don't grow or need food.",
            "states of matter": "For example, ice is solid water, regular water is liquid, and steam from hot water is gas.",
            "solid": "For example, ice cubes, rocks, and books are all solids because they keep their shape.",
            "liquid": "For example, water, milk, and juice are liquids because they can flow and take the shape of their container.",
            "gas": "For example, the air we breathe and the steam from hot soup are gases that float around.",
            "temperature": "For example, ice cream is cold (low temperature) and hot cocoa is warm (high temperature).",
            "measuring": "For example, we use a ruler to measure how long something is, or a scale to see how heavy it is.",
            "healthy food": "For example, fruits like apples, vegetables like carrots, and milk are healthy foods that help you grow strong.",
            "materials": "For example, wood comes from trees, metal comes from rocks in the ground, and plastic is made in factories.",
            "roots": "For example, carrots and radishes are roots we can eat, and tree roots help the tree get water from soil.",
            "leaves": "For example, lettuce and spinach are leaves we eat, and tree leaves make food for the tree using sunlight.",
            "stems": "For example, celery is a stem we can eat, and tree trunks are thick stems that hold up the tree.",
            "flowers": "For example, roses and daisies are flowers that smell nice and help plants make seeds.",
            "seeds": "For example, apple seeds can grow into apple trees, and bean seeds can grow into bean plants."
        }

        enhanced_text = text

        # Check if the text discusses any topics that could use examples
        for topic, example in example_mappings.items():
            if topic.lower() in enhanced_text.lower() and example not in enhanced_text:
                # Find a good place to insert the example
                sentences = enhanced_text.split('. ')
                for i, sentence in enumerate(sentences):
                    if topic.lower() in sentence.lower() and len(sentence) > 20:
                        # Insert example after this sentence
                        sentences.insert(i + 1, example)
                        enhanced_text = '. '.join(sentences)
                        break

        return enhanced_text

    def _make_tts_friendly_indian_english(self, text: str) -> str:
        """Make content TTS-friendly for Indian English pronunciation"""

        # Remove all emojis and special characters
        import re

        # Remove emojis
        emoji_pattern = re.compile("["
                                 u"\U0001F600-\U0001F64F"  # emoticons
                                 u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                                 u"\U0001F680-\U0001F6FF"  # transport & map
                                 u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                                 u"\U00002702-\U000027B0"
                                 u"\U000024C2-\U0001F251"
                                 u"\u2600-\u26FF"         # miscellaneous symbols
                                 u"\u2700-\u27BF"         # dingbats
                                 "]+", flags=re.UNICODE)

        text = emoji_pattern.sub('', text)

        # Remove checkmarks and other symbols
        text = text.replace('✅', '').replace('❌', '').replace('➤', '')
        text = text.replace('•', '').replace('◆', '').replace('★', '')

        # Convert scientific formulas and equations for Indian English TTS
        text = self._format_scientific_content_for_indian_tts(text)

        # Fix pronunciation for Indian English
        pronunciations = {
            # Numbers and measurements
            "0°C": "zero degrees Celsius",
            "100°C": "hundred degrees Celsius",
            "37°C": "thirty seven degrees Celsius",
            "°F": "degrees Fahrenheit",
            "cm": "centimetre",
            "mm": "millimetre",
            "km": "kilometre",
            "kg": "kilogram",
            "mg": "milligram",
            "ml": "millilitre",
            "pH": "pee aitch",

            # Common Indian English corrections for TTS
            "can't": "cannot",
            "won't": "will not",
            "don't": "do not",
            "isn't": "is not",
            "aren't": "are not",
            "wasn't": "was not",
            "weren't": "were not",
            "hasn't": "has not",
            "haven't": "have not",
            "doesn't": "does not",

            # Scientific terms with clear pronunciation
            "vs": "versus",
            "etc": "etcetera",
            "i.e.": "that is",
            "e.g.": "for example",
            "&": "and",
            "%": "percent",

            # Fix common mispronunciations in Indian TTS
            "iron": "eye-ron",
            "recipe": "res-i-pee",
            "vehicle": "vee-hi-kul",
            "adult": "a-dult",
            "debris": "deb-ree",
            "route": "root",
        }

        for term, pronunciation in pronunciations.items():
            # Use word boundaries to avoid partial replacements
            pattern = r'\b' + re.escape(term) + r'\b'
            text = re.sub(pattern, pronunciation, text, flags=re.IGNORECASE)

        # Clean up multiple spaces
        text = re.sub(r'\s+', ' ', text).strip()

        return text

    def _format_scientific_content_for_indian_tts(self, text: str) -> str:
        """Format scientific formulas and content for Indian English TTS"""
        import re

        # Chemical formulas with Indian pronunciation
        chemical_formulas = {
            "H2O": "H two O",
            "CO2": "carbon dioxide",
            "O2": "oxygen gas",
            "H2": "hydrogen gas",
            "N2": "nitrogen gas",
            "CO": "carbon monoxide",
            "NaCl": "sodium chloride",
            "CaCO3": "calcium carbonate",
            "H2SO4": "sulphuric acid",
            "HCl": "hydrochloric acid",
            "NaOH": "sodium hydroxide",
            "KOH": "potassium hydroxide",
            "NH3": "ammonia",
            "CH4": "methane",
            "Ca(OH)2": "calcium hydroxide",
            "MgO": "magnesium oxide",
            "CaO": "calcium oxide",
            "Fe2O3": "iron oxide",
            "Al2O3": "aluminium oxide"
        }

        # Replace chemical formulas
        for formula, pronunciation in chemical_formulas.items():
            text = text.replace(formula, pronunciation)

        # Handle mathematical expressions
        math_patterns = {
            r'\b(\d+)\s*\+\s*(\d+)\s*=\s*(\d+)\b': r'\1 plus \2 equal to \3',
            r'\b(\d+)\s*-\s*(\d+)\s*=\s*(\d+)\b': r'\1 minus \2 equal to \3',
            r'\b(\d+)\s*×\s*(\d+)\s*=\s*(\d+)\b': r'\1 multiplied by \2 equal to \3',
            r'\b(\d+)\s*÷\s*(\d+)\s*=\s*(\d+)\b': r'\1 divided by \2 equal to \3',
            r'\b(\d+)/(\d+)\b': r'\1 by \2',  # fractions
            r'\b(\d+)²\b': r'\1 squared',
            r'\b(\d+)³\b': r'\1 cubed',
        }

        for pattern, replacement in math_patterns.items():
            text = re.sub(pattern, replacement, text)

        # Handle units and measurements for Indian pronunciation
        unit_patterns = {
            r'(\d+)\s*m\b': r'\1 metre',
            r'(\d+)\s*cm\b': r'\1 centimetre',
            r'(\d+)\s*mm\b': r'\1 millimetre',
            r'(\d+)\s*km\b': r'\1 kilometre',
            r'(\d+)\s*g\b': r'\1 gram',
            r'(\d+)\s*kg\b': r'\1 kilogram',
            r'(\d+)\s*mg\b': r'\1 milligram',
            r'(\d+)\s*l\b': r'\1 litre',
            r'(\d+)\s*ml\b': r'\1 millilitre',
        }

        for pattern, replacement in unit_patterns.items():
            text = re.sub(pattern, replacement, text)

        # Handle temperature readings
        temp_patterns = {
            r'(\d+)°C': r'\1 degrees Celsius',
            r'(\d+)°F': r'\1 degrees Fahrenheit',
            r'(\d+)\s*degrees?\s*C\b': r'\1 degrees Celsius',
            r'(\d+)\s*degrees?\s*F\b': r'\1 degrees Fahrenheit',
        }

        for pattern, replacement in temp_patterns.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

        # Replace mathematical symbols
        symbol_replacements = {
            '→': ' leads to ',
            '←': ' comes from ',
            '↑': ' goes up ',
            '↓': ' goes down ',
            '∞': ' infinity ',
            '=': ' equal to ',
            '≈': ' approximately equal to ',
            '≠': ' does not equal ',
            '≥': ' greater than or equal to ',
            '≤': ' less than or equal to ',
            '>': ' greater than ',
            '<': ' less than ',
            '±': ' plus or minus ',
            '∆': ' delta ',
            'α': ' alpha ',
            'β': ' beta ',
            'γ': ' gamma ',
        }

        for symbol, replacement in symbol_replacements.items():
            text = text.replace(symbol, replacement)

        # Handle scientific notation
        text = re.sub(r'(\d+(?:\.\d+)?)\s*×\s*10\^?([+-]?\d+)', r'\1 times ten to the power \2', text)

        return text

    def _format_chemical_content_for_audio(self, text: str) -> str:
        """Format chemical formulas and equations for better TTS pronunciation"""
        import re

        # Dictionary of common chemical formulas and their pronunciations
        chemical_pronunciations = {
            "H2O": "H two O",
            "CO2": "C O two",
            "CO": "carbon monoxide",
            "H2SO4": "H two S O four",
            "HCl": "H C L",
            "NaCl": "sodium chloride",
            "CaCO3": "calcium carbonate",
            "NH3": "ammonia",
            "CH4": "methane",
            "C2H6": "ethane",
            "C2H4": "ethene",
            "C2H2": "ethyne",
            "CaO": "calcium oxide",
            "MgO": "magnesium oxide",
            "Fe2O3": "iron three oxide",
            "Al2O3": "aluminum oxide",
            "KOH": "potassium hydroxide",
            "NaOH": "sodium hydroxide",
            "Ca(OH)2": "calcium hydroxide",
            "H2": "hydrogen gas",
            "O2": "oxygen gas",
            "N2": "nitrogen gas",
            "Cl2": "chlorine gas"
        }

        formatted_text = text

        # Replace known chemical formulas
        for formula, pronunciation in chemical_pronunciations.items():
            formatted_text = formatted_text.replace(formula, pronunciation)

        # Handle general patterns for remaining formulas

        # Pattern 1: Simple subscripts (e.g., H2, O2, CH4)
        formatted_text = re.sub(r'([A-Z][a-z]?)(\d+)', r'\1 \2', formatted_text)

        # Pattern 2: Chemical equations with arrows
        formatted_text = formatted_text.replace('→', 'yields')
        formatted_text = formatted_text.replace('->', 'yields')
        formatted_text = formatted_text.replace('⇌', 'is in equilibrium with')
        formatted_text = formatted_text.replace('<->', 'is in equilibrium with')

        # Pattern 3: Plus signs in equations
        formatted_text = re.sub(r'\s*\+\s*', ' plus ', formatted_text)

        # Pattern 4: Common chemistry terms that need pronunciation help
        chemistry_terms = {
            "∆": "delta",
            "°C": "degrees Celsius",
            "mol": "moles",
            "M": "molar",
            "pH": "P H",
            "pOH": "P O H",
            "atm": "atmospheres",
            "kPa": "kilopascals"
        }

        for symbol, pronunciation in chemistry_terms.items():
            formatted_text = formatted_text.replace(symbol, pronunciation)

        # Pattern 5: Improve pronunciation of element names
        element_improvements = {
            " C ": " carbon ",
            " N ": " nitrogen ",
            " O ": " oxygen ",
            " H ": " hydrogen ",
            " S ": " sulfur ",
            " P ": " phosphorus ",
            " K ": " potassium ",
            " Na ": " sodium ",
            " Ca ": " calcium ",
            " Mg ": " magnesium ",
            " Al ": " aluminum ",
            " Fe ": " iron ",
            " Cl ": " chlorine "
        }

        for symbol, name in element_improvements.items():
            formatted_text = formatted_text.replace(symbol, name)

        return formatted_text

    async def _generate_follow_up_questions(
        self,
        original_question: str,
        results: List[RetrievalResult]
    ) -> List[str]:
        """Generate follow-up questions based on retrieved content"""

        suggestions = []

        # Extract topics from results
        topics = set()
        for result in results:
            if result.metadata.get("topic"):
                topics.update(result.metadata.get("topic", []))

        # Generate topic-based suggestions
        for topic in list(topics)[:3]:  # Limit to 3 topics
            suggestions.append(f"Can you explain more about {topic}?")
            suggestions.append(f"Can you show me an example of {topic}?")

        # Add generic follow-ups
        suggestions.extend([
            "Can you give me a simpler explanation?",
            "Do you have any practice problems for this?",
            "What should I learn before this topic?"
        ])

        return suggestions[:5]  # Limit to 5 suggestions

    async def _get_topic_suggestions(
        self,
        question: str,
        grade: int,
        subject: Optional[str]
    ) -> List[str]:
        """Get topic suggestions when no direct answer is found"""

        try:
            # Extract keywords from question
            import re
            keywords = re.findall(r'\b[a-zA-Z]{4,}\b', question.lower())

            suggestions = []
            for keyword in keywords[:3]:  # Try top 3 keywords
                topic_results = await self.retriever.search_by_topic(
                    topic=keyword,
                    grade=grade,
                    subject=subject,
                    limit=3
                )

                if topic_results:
                    for result in topic_results:
                        topic = result.metadata.get("topic", [])
                        if topic:
                            suggestions.extend(topic[:2])  # Add 2 topics

            # Remove duplicates and return
            return list(set(suggestions))[:5]

        except Exception as e:
            logger.error(f"Failed to get topic suggestions: {e}")
            return ["Try asking about a specific topic", "Be more specific in your question"]

    async def search_by_chapter_and_activity(
        self,
        chapter_number: int,
        activity_number: str,
        grade: Optional[int] = None,
        subject: Optional[str] = None
    ) -> Dict[str, Any]:
        """Search for specific activity content within a chapter using combined metadata filtering"""
        try:
            student_grade = grade or self.current_student_grade
            target_subject = subject or self.current_subject

            if not student_grade or not target_subject:
                return {"error": "Grade and subject must be specified"}

            from qdrant_client.models import Filter, FieldCondition, MatchValue, MatchText

            collection_name = f"grade_{student_grade:02d}_{target_subject}"

            # First, try to find content that mentions the specific activity within the chapter
            search_result = await asyncio.to_thread(
                self.qdrant_manager.client.scroll,
                collection_name=collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(key="chapter_number", match=MatchValue(value=chapter_number)),
                        FieldCondition(key="grade", match=MatchValue(value=student_grade)),
                        FieldCondition(key="subject", match=MatchValue(value=target_subject))
                    ]
                ),
                limit=50,  # Get more content to search through
                with_payload=True,
                with_vectors=False
            )

            points = search_result[0]
            if not points:
                return {"error": f"No content found for Chapter {chapter_number}"}

            # Filter points that contain the activity number in their content
            activity_points = []

            # Enhanced patterns for different activity types found in Grade 6 Science
            if activity_number.lower() in ['1', '2', '3', '4', '5']:
                activity_patterns = [
                    # Direct activity patterns
                    f"activity {activity_number}",
                    f"activity{activity_number}",
                    f"activity 3.{activity_number}",  # Chapter 3 specific

                    # "Let us" patterns from Chapter 3
                    f"let us record",          # Activity 3.1
                    f"let us explore",         # Activity 3.2
                    f"let us interact",        # Activity 3.3
                    f"let us investigate",     # Activities 3.5, 3.6, 3.7
                    f"let us find out",        # Activity 3.8

                    # Experiment patterns
                    f"experiment {activity_number}",
                    f"experiment{activity_number}",

                    # Question patterns
                    f"question {activity_number}",
                    f"question{activity_number}",

                    # General science activity patterns
                    "observe",
                    "experiment",
                    "investigation",
                    "first, we observe",
                    "thought-provoking experiments",
                    "record your observations",
                    "starch test",
                    "protein test",
                    "fat test"
                ]
            else:
                # For decimal numbers like 1.1, 1.2, etc.
                activity_patterns = [
                    f"activity {activity_number}",
                    f"activity{activity_number}",
                    f"experiment {activity_number}",
                    f"question {activity_number}"
                ]

            for point in points:
                content = point.payload.get("content", "").lower()
                # Check if any activity pattern matches
                if any(pattern in content for pattern in activity_patterns):
                    activity_points.append(point)

            if not activity_points:
                logger.info(f"No Activity {activity_number} found in Chapter {chapter_number} content")
                return {"error": f"Activity {activity_number} not found in Chapter {chapter_number}"}

            # Get chapter title from first point
            chapter_title = points[0].payload.get("chapter", f"Chapter {chapter_number}")

            # Combine activity content
            activity_content_pieces = []
            for point in activity_points[:3]:  # Use top 3 matching chunks
                content = point.payload.get("content", "")
                if content and len(content.strip()) > 10:
                    activity_content_pieces.append(content)

            if not activity_content_pieces:
                return {"error": f"No substantial Activity {activity_number} content found in Chapter {chapter_number}"}

            # Create a focused answer about the specific activity
            combined_content = " ".join(activity_content_pieces)
            formatted_answer = self._format_answer_for_grade(combined_content.split(), student_grade)

            return {
                "answer": f"Activity {activity_number} in Chapter {chapter_number}: {chapter_title}\n\n{formatted_answer}",
                "confidence": 1.0,  # High confidence since we found it by specific search
                "sources": [{
                    "textbook": activity_points[0].payload.get("textbook_name", "Unknown"),
                    "chapter": chapter_title,
                    "page": activity_points[0].payload.get("page_number", "Unknown"),
                    "activity": activity_number
                }],
                "chapter_title": chapter_title,
                "chapter_number": chapter_number,
                "activity_number": activity_number
            }

        except Exception as e:
            logger.error(f"Failed to search for Activity {activity_number} in Chapter {chapter_number}: {e}")
            return {"error": f"Failed to search activity content: {str(e)}"}

    async def search_by_chapter(self, chapter_number: int, grade: Optional[int] = None, subject: Optional[str] = None) -> Dict[str, Any]:
        """Search for content by chapter number using metadata filtering"""
        try:
            student_grade = grade or self.current_student_grade
            target_subject = subject or self.current_subject

            if not student_grade or not target_subject:
                return {"error": "Grade and subject must be specified"}

            from qdrant_client.models import Filter, FieldCondition, MatchValue

            # Use metadata filtering to find chapter content
            collection_name = f"grade_{student_grade:02d}_{target_subject}"

            # Search with chapter number filter
            search_result = await asyncio.to_thread(
                self.qdrant_manager.client.scroll,
                collection_name=collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(key="chapter_number", match=MatchValue(value=chapter_number)),
                        FieldCondition(key="grade", match=MatchValue(value=student_grade)),
                        FieldCondition(key="subject", match=MatchValue(value=target_subject))
                    ]
                ),
                limit=10,  # Get first 10 chunks from this chapter
                with_payload=True,
                with_vectors=False
            )

            points = search_result[0]
            if not points:
                return {"error": f"No content found for Chapter {chapter_number}"}

            # Get chapter title from first point
            chapter_title = points[0].payload.get("chapter", f"Chapter {chapter_number}")

            # Combine content from multiple chunks
            content_pieces = []
            for point in points:
                content = point.payload.get("content", "")
                if content and len(content.strip()) > 10:  # Skip very short content
                    content_pieces.append(content)

            if not content_pieces:
                return {"error": f"No substantial content found for Chapter {chapter_number}"}

            # Create a comprehensive answer
            combined_content = " ".join(content_pieces[:5])  # Use first 5 chunks
            formatted_answer = self._format_answer_for_grade(combined_content.split(), student_grade)

            return {
                "answer": f"Chapter {chapter_number}: {chapter_title}\n\n{formatted_answer}",
                "confidence": 1.0,  # High confidence since we found it by metadata
                "sources": [{
                    "textbook": points[0].payload.get("textbook_name", "Unknown"),
                    "chapter": chapter_title,
                    "page": points[0].payload.get("page_number", "Unknown")
                }],
                "chapter_title": chapter_title,
                "chapter_number": chapter_number
            }

        except Exception as e:
            logger.error(f"Failed to search by chapter {chapter_number}: {e}")
            return {"error": f"Failed to search chapter content: {str(e)}"}

    async def get_chapter_mapping(self, grade: int, subject: str) -> Dict[int, str]:
        """Get dynamic chapter mapping from Qdrant metadata"""
        try:
            from qdrant_client.models import Filter, FieldCondition, MatchValue

            # Get all unique chapters for this grade and subject
            collection_name = f"grade_{grade:02d}_{subject}" if grade < 10 else f"grade_{grade}_{subject}"

            # Query Qdrant for all unique chapter numbers and titles
            scroll_result = await asyncio.to_thread(
                self.qdrant_manager.client.scroll,
                collection_name=collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(key="grade", match=MatchValue(value=grade)),
                        FieldCondition(key="subject", match=MatchValue(value=subject))
                    ]
                ),
                limit=1000,  # Should be enough to get all chapters
                with_payload=True,
                with_vectors=False
            )

            # Extract unique chapter mappings
            chapter_mapping = {}
            seen_chapters = set()

            for point in scroll_result[0]:
                payload = point.payload
                chapter_number = payload.get("chapter_number")
                chapter_title = payload.get("chapter")

                if chapter_number and chapter_title and chapter_number not in seen_chapters:
                    chapter_mapping[chapter_number] = chapter_title
                    seen_chapters.add(chapter_number)

            logger.info(f"Found {len(chapter_mapping)} chapters for Grade {grade} {subject}")
            return chapter_mapping

        except Exception as e:
            logger.error(f"Failed to get chapter mapping: {e}")
            # Fallback to empty mapping
            return {}

    async def get_service_stats(self) -> Dict[str, Any]:
        """Get service statistics and health information"""
        try:
            stats = {
                "initialized": self.is_initialized,
                "current_context": {
                    "grade": self.current_student_grade,
                    "subject": self.current_subject
                }
            }

            if self.is_initialized:
                # Get collection stats
                collection_stats = await self.qdrant_manager.get_collection_stats()
                stats["collections"] = collection_stats

                # Get embedding cache stats
                embedding_stats = self.embedding_manager.get_cache_stats()
                stats["embeddings_cache"] = embedding_stats

            return stats

        except Exception as e:
            logger.error(f"Failed to get service stats: {e}")
            return {"error": str(e)}

    def validate_and_clean_response(self, response: str) -> str:
        """
        Validate and clean response for voice output (Quick Win 2)

        Fixes:
        - Strips markdown formatting (bold, italic, underline)
        - Removes extra whitespace
        - Truncates to max 150 words for voice
        - Detects and fixes any remaining reversed text

        Args:
            response: Raw response text

        Returns:
            Cleaned response suitable for TTS
        """
        import re

        if not response:
            return response

        # 1. Fix any remaining reversed text
        if self._detect_reversed_text(response):
            response = self._fix_reversed_text(response)

        # 2. Strip markdown formatting
        # Remove bold (**text** or __text__)
        response = re.sub(r'\*\*(.+?)\*\*', r'\1', response)
        response = re.sub(r'__(.+?)__', r'\1', response)

        # Remove italic (*text* or _text_)
        response = re.sub(r'\*(.+?)\*', r'\1', response)
        response = re.sub(r'_(.+?)_', r'\1', response)

        # Remove code blocks
        response = re.sub(r'`(.+?)`', r'\1', response)

        # Remove headers (# Header)
        response = re.sub(r'^#+\s+', '', response, flags=re.MULTILINE)

        # Remove bullet points and list markers
        response = re.sub(r'^\s*[-*•]\s+', '', response, flags=re.MULTILINE)
        response = re.sub(r'^\s*\d+\.\s+', '', response, flags=re.MULTILINE)

        # 3. Remove extra whitespace
        response = re.sub(r'\s+', ' ', response).strip()

        # 4. Truncate if too long (max 150 words for voice)
        words = response.split()
        if len(words) > 150:
            response = ' '.join(words[:150])
            # Try to end at a sentence boundary
            last_period = response.rfind('.')
            last_exclamation = response.rfind('!')
            last_question = response.rfind('?')
            last_sentence_end = max(last_period, last_exclamation, last_question)

            if last_sentence_end > len(response) * 0.7:  # If we're at least 70% through
                response = response[:last_sentence_end + 1]
            else:
                response += '...'

        return response

    def _detect_reversed_text(self, text: str) -> bool:
        """Detect if text contains reversed content"""
        if not text:
            return False

        reversed_indicators = ['edarG', 'ecneicS', 'koobtxeT', 'ytisoiruC', 'dlroW']
        text_sample = text[:500]  # Check first 500 chars
        return any(indicator in text_sample for indicator in reversed_indicators)

    def _fix_reversed_text(self, text: str) -> str:
        """Fix reversed text by reversing each word"""
        logger.info("Detected reversed text in response, fixing...")

        # Split into lines to preserve structure
        lines = text.split('\n')
        fixed_lines = []

        for line in lines:
            # Split line into words
            words = line.split()
            # Reverse each word
            fixed_words = [word[::-1] for word in words]
            # Join back
            fixed_lines.append(' '.join(fixed_words))

        return '\n'.join(fixed_lines)