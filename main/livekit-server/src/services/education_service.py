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

logger = logging.getLogger(__name__)


class EducationService:
    """Main service for educational content retrieval and answer generation"""

    def __init__(self):
        self.qdrant_manager = QdrantEducationManager()
        self.embedding_manager = EmbeddingManager()
        self.retriever = None
        self.ingestion_pipeline = None

        self.is_initialized = False
        self.current_student_grade = None
        self.current_subject = None

        # Default settings
        self.default_retrieval_limit = 5
        self.min_score_threshold = 0.7

    async def initialize(self) -> bool:
        """Initialize the education service"""
        try:
            logger.info("Initializing Education Service...")

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

            # Initialize retriever
            self.retriever = EducationalRetriever(
                self.qdrant_manager.client,
                self.embedding_manager
            )

            # Initialize ingestion pipeline (lightweight - reuse components)
            self.ingestion_pipeline = TextbookIngestionPipeline()
            self.ingestion_pipeline.qdrant_manager = self.qdrant_manager  # Reuse initialized manager
            self.ingestion_pipeline.embedding_manager = self.embedding_manager  # Reuse initialized manager
            self.ingestion_pipeline.is_initialized = True  # Skip duplicate initialization
            logger.info("Textbook ingestion pipeline configured (reusing components)")

            self.is_initialized = True
            logger.info("Education Service initialized successfully")

            # Log collection statistics
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

            if not student_grade:
                return {"error": "No grade specified. Please set student context first."}

            logger.info(f"Answering question for Grade {student_grade}: {question}")

            # Retrieve relevant content
            results = await self.retriever.retrieve(
                query=question,
                grade=student_grade,
                subject=target_subject,
                limit=self.default_retrieval_limit,
                include_related=include_examples or include_visual_aids
            )

            if not results:
                return {
                    "answer": "I couldn't find information about that in your textbooks. Could you please rephrase your question or be more specific?",
                    "confidence": 0.0,
                    "sources": [],
                    "suggestions": await self._get_topic_suggestions(question, student_grade, target_subject)
                }

            # Filter results by confidence threshold
            high_confidence_results = [r for r in results if r.score >= self.min_score_threshold]

            if not high_confidence_results:
                return {
                    "answer": "I found some related content, but I'm not confident it answers your question exactly. Could you please be more specific?",
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
        """Generate a comprehensive educational answer"""

        # Combine content from top results
        main_content = []
        sources = []
        examples = []
        visual_aids = []

        for result in results:
            main_content.append(result.content)

            # Add source information
            sources.append({
                "textbook": result.metadata.get("textbook_name", "Unknown"),
                "page": result.metadata.get("page_number", "Unknown"),
                "chapter": result.metadata.get("chapter", ""),
                "section": result.metadata.get("section_title", "")
            })

            # Collect examples if requested
            if include_examples and result.related_content:
                for related in result.related_content:
                    if related.get("type") == "example":
                        examples.append(related.get("content", ""))

            # Collect visual aids if requested
            if include_visual_aids and result.metadata.get("figure_refs"):
                visual_aids.extend(result.metadata.get("figure_refs", []))

        # Create the main answer
        answer = self._format_answer_for_grade(main_content, grade)

        # Calculate confidence score
        confidence = sum(r.score for r in results) / len(results) if results else 0.0

        response = {
            "answer": answer,
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
        """Format answer appropriately for grade level"""
        # Combine content pieces
        combined_content = " ".join(content_pieces)

        # Format chemical formulas and equations for better TTS pronunciation
        formatted_content = self._format_chemical_content_for_audio(combined_content)

        # Adjust language complexity based on grade
        if grade <= 8:
            # Simplify for middle school
            return self._simplify_language(formatted_content)
        else:
            # Keep more sophisticated language for high school
            return formatted_content

    def _simplify_language(self, text: str) -> str:
        """Simplify language for younger students"""
        # Simple replacements for common complex terms
        replacements = {
            "utilize": "use",
            "demonstrate": "show",
            "consequently": "so",
            "furthermore": "also",
            "therefore": "so",
            "however": "but",
            "approximately": "about"
        }

        simplified = text
        for complex_word, simple_word in replacements.items():
            simplified = simplified.replace(complex_word, simple_word)

        return simplified

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