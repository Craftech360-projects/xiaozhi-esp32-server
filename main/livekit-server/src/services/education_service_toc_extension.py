"""
TOC-Guided Query Extension for Education Service
Add this method to EducationService class for TOC-guided retrieval
"""

from typing import Dict, List, Optional, Any
import logging
from ..rag.toc_manager import TOCManager
from ..rag.retriever import RetrievalResult

logger = logging.getLogger(__name__)


# Add this method to EducationService class:

async def answer_question_with_toc(
    self,
    question: str,
    grade: Optional[int] = None,
    subject: Optional[str] = None,
    use_toc_routing: bool = True,
    include_examples: bool = True
) -> Dict[str, Any]:
    """
    Answer question using TOC-guided retrieval

    This is an enhanced version of answer_question() that uses the TOC structure
    to route queries to the most relevant content sections.

    Benefits:
    - Faster retrieval (search TOC first, then content)
    - Better activity detection (activities preserved as complete units)
    - Content priority boosting (teaching content ranked higher)
    - More accurate results for chapter/section-specific queries
    """

    if not self.is_initialized:
        return {"error": "Education service not initialized"}

    try:
        # Use provided context or fall back to current context
        student_grade = grade or self.current_student_grade
        target_subject = subject or self.current_subject

        logger.info(f"TOC-guided query for Grade {student_grade} {target_subject}: {question}")

        # Initialize TOC manager if needed
        if not hasattr(self, 'toc_manager') or self.toc_manager is None:
            collection_name = f"{self.qdrant_manager.get_collection_name(student_grade, target_subject)}_toc"
            self.toc_manager = TOCManager(
                qdrant_client=self.qdrant_manager.client,
                collection_name=collection_name
            )

        # Step 1: Search TOC to find relevant sections
        if use_toc_routing:
            toc_sections = await self.toc_manager.search_toc_sections(
                query=question,
                chapter=None,  # Auto-detect from query
                section_type=None,  # Auto-detect
                limit=3
            )

            if toc_sections:
                logger.info(f"Found {len(toc_sections)} relevant TOC sections")

                # Build filter for content retrieval based on TOC sections
                relevant_section_ids = [s['id'] for s in toc_sections]

                # Retrieve content from these sections
                results = await self._retrieve_by_toc_sections(
                    section_ids=relevant_section_ids,
                    query=question,
                    grade=student_grade,
                    subject=target_subject,
                    limit=5
                )

                if results:
                    # Generate answer from TOC-guided results
                    answer_data = await self._generate_educational_answer(
                        question, results, student_grade,
                        include_examples=include_examples,
                        include_visual_aids=True
                    )

                    # Add TOC metadata
                    answer_data['retrieval_method'] = 'toc_guided'
                    answer_data['toc_sections_used'] = [
                        {
                            'id': s['id'],
                            'title': s['title'],
                            'type': s['type'],
                            'chapter': s['chapter']
                        }
                        for s in toc_sections
                    ]

                    return answer_data
                else:
                    logger.info("TOC sections found, but no content retrieved. Falling back to semantic search.")

        # Step 2: Fallback to regular semantic search if TOC routing fails
        logger.info("Using fallback semantic search")

        results = await self.retriever.retrieve(
            query=question,
            grade=student_grade,
            subject=target_subject,
            limit=5,
            include_related=include_examples
        )

        if not results:
            return {
                "answer": "I don't have information about that specific topic in my textbooks right now. Could you rephrase your question or ask about a different topic?",
                "confidence": 0.0,
                "sources": [],
                "retrieval_method": "none",
                "suggestions": await self._get_topic_suggestions(question, student_grade, target_subject)
            }

        # Filter by confidence threshold
        high_confidence_results = [r for r in results if r.score >= self.min_score_threshold]

        if not high_confidence_results:
            return {
                "answer": "I found some related topics, but I'm not confident about the answer. Could you be more specific?",
                "confidence": max([r.score for r in results]) if results else 0.0,
                "sources": [],
                "retrieval_method": "semantic_low_confidence",
                "suggestions": await self._get_topic_suggestions(question, student_grade, target_subject)
            }

        # Generate answer
        answer_data = await self._generate_educational_answer(
            question, high_confidence_results, student_grade,
            include_examples=include_examples,
            include_visual_aids=True
        )

        answer_data['retrieval_method'] = 'semantic_search'

        return answer_data

    except Exception as e:
        logger.error(f"Failed to answer question with TOC: {e}")
        return {"error": f"Failed to process question: {str(e)}"}


async def _retrieve_by_toc_sections(
    self,
    section_ids: List[str],
    query: str,
    grade: int,
    subject: str,
    limit: int = 5
) -> List[RetrievalResult]:
    """
    Retrieve content from specific TOC sections

    Uses toc_section_id metadata filter to get content from the identified sections
    """

    try:
        from qdrant_client.models import Filter, FieldCondition, MatchAny

        # Get collection name
        collection_name = self.qdrant_manager.get_collection_name(grade, subject)

        # Generate query embedding
        query_embedding = await self.embedding_manager.get_text_embedding(query)
        if not query_embedding:
            logger.error("Failed to generate query embedding")
            return []

        # Search with TOC section filter
        search_results = self.qdrant_manager.client.search(
            collection_name=collection_name,
            query_vector=query_embedding,
            query_filter=Filter(
                must=[
                    FieldCondition(
                        key="toc_section_id",
                        match=MatchAny(any=section_ids)
                    )
                ]
            ),
            limit=limit,
            with_payload=True
        )

        # Convert to RetrievalResult objects
        results = []
        for result in search_results:
            retrieval_result = RetrievalResult(
                id=str(result.id),
                content=result.payload.get("content", ""),
                score=result.score,
                collection_name=collection_name,
                metadata=result.payload
            )
            results.append(retrieval_result)

        logger.info(f"Retrieved {len(results)} content chunks from {len(section_ids)} TOC sections")

        return results

    except Exception as e:
        logger.error(f"Failed to retrieve by TOC sections: {e}")
        return []


async def get_toc_for_chapter(
    self,
    chapter: int,
    grade: Optional[int] = None,
    subject: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get the complete Table of Contents for a specific chapter

    Useful for:
    - Showing students what topics are covered in a chapter
    - Planning study sessions
    - Understanding chapter structure
    """

    try:
        student_grade = grade or self.current_student_grade
        target_subject = subject or self.current_subject

        # Initialize TOC manager if needed
        if not hasattr(self, 'toc_manager') or self.toc_manager is None:
            collection_name = f"{self.qdrant_manager.get_collection_name(student_grade, target_subject)}_toc"
            self.toc_manager = TOCManager(
                qdrant_client=self.qdrant_manager.client,
                collection_name=collection_name
            )

        # Get TOC for chapter
        toc = await self.toc_manager.get_toc_by_chapter(chapter)

        if not toc:
            return {
                "error": f"No TOC found for Chapter {chapter}",
                "chapter": chapter,
                "grade": student_grade,
                "subject": target_subject
            }

        # Format TOC for user-friendly display
        formatted_sections = []
        for section in toc['sections']:
            formatted_section = {
                'id': section['id'],
                'title': section['title'],
                'type': section['type'],
                'page': section['page'],
                'description': section.get('expanded_description', ''),
                'key_concepts': section.get('key_concepts', []),
                'difficulty': section.get('difficulty_level', 'beginner'),
                'cognitive_level': section.get('cognitive_level', 'understand')
            }
            formatted_sections.append(formatted_section)

        return {
            'chapter': toc['chapter'],
            'title': toc['title'],
            'grade': student_grade,
            'subject': target_subject,
            'total_sections': len(formatted_sections),
            'sections': formatted_sections
        }

    except Exception as e:
        logger.error(f"Failed to get TOC for chapter {chapter}: {e}")
        return {"error": f"Failed to get TOC: {str(e)}"}


async def search_activities(
    self,
    chapter: Optional[int] = None,
    grade: Optional[int] = None,
    subject: Optional[str] = None
) -> Dict[str, Any]:
    """
    Search for all activities in a chapter or subject

    Activities are preserved as complete units in TOC-guided RAG,
    making this search very accurate and complete.
    """

    try:
        student_grade = grade or self.current_student_grade
        target_subject = subject or self.current_subject

        # Initialize TOC manager if needed
        if not hasattr(self, 'toc_manager') or self.toc_manager is None:
            collection_name = f"{self.qdrant_manager.get_collection_name(student_grade, target_subject)}_toc"
            self.toc_manager = TOCManager(
                qdrant_client=self.qdrant_manager.client,
                collection_name=collection_name
            )

        # Search TOC for activities
        activity_sections = await self.toc_manager.search_toc_sections(
            query="activity experiment hands-on",
            chapter=chapter,
            section_type="activity",
            limit=20
        )

        if not activity_sections:
            return {
                "message": f"No activities found in Chapter {chapter}" if chapter else "No activities found",
                "total_activities": 0,
                "activities": []
            }

        # Format activities
        formatted_activities = []
        for activity in activity_sections:
            formatted_activity = {
                'id': activity['id'],
                'title': activity['title'],
                'chapter': activity['chapter'],
                'chapter_title': activity.get('chapter_title', ''),
                'description': activity.get('expanded_description', ''),
                'learning_objectives': activity.get('learning_objectives', []),
                'key_concepts': activity.get('key_concepts', []),
                'difficulty': activity.get('difficulty_level', 'beginner')
            }
            formatted_activities.append(formatted_activity)

        return {
            'grade': student_grade,
            'subject': target_subject,
            'chapter': chapter,
            'total_activities': len(formatted_activities),
            'activities': formatted_activities
        }

    except Exception as e:
        logger.error(f"Failed to search activities: {e}")
        return {"error": f"Failed to search activities: {str(e)}"}
