"""
Educational Retrieval System
Intelligent multi-collection search with query analysis and context enhancement
"""

import logging
import re
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
from enum import Enum
import asyncio

# Qdrant for vector search
try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Filter, FieldCondition, MatchValue, MatchAny, Range
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False

# Text processing
try:
    import nltk
    from nltk.corpus import stopwords
    from nltk.tokenize import word_tokenize
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False

logger = logging.getLogger(__name__)


class QuestionType(Enum):
    """Types of educational questions"""
    DEFINITION = "definition"
    EXPLANATION = "explanation"
    PROBLEM_SOLVING = "problem_solving"
    EXAMPLE_REQUEST = "example_request"
    COMPARISON = "comparison"
    PROCESS = "process"
    CALCULATION = "calculation"
    GENERAL = "general"


@dataclass
class QueryAnalysis:
    """Analysis of a user query"""
    question_type: QuestionType
    subject_hints: List[str]
    key_concepts: List[str]
    difficulty_indicators: List[str]
    requires_prerequisites: bool
    requires_examples: bool
    requires_visual_aids: bool
    cognitive_level: str
    estimated_complexity: float


@dataclass
class RetrievalResult:
    """Result from retrieval with enhanced metadata"""
    id: str
    content: str
    score: float
    collection_name: str
    metadata: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None
    related_content: Optional[List[Dict[str, Any]]] = None


class QueryAnalyzer:
    """Analyzes educational queries to understand intent and requirements"""

    def __init__(self):
        self.subject_keywords = {
            "mathematics": ["math", "algebra", "geometry", "calculus", "equation", "formula", "solve", "calculate"],
            "physics": ["force", "energy", "motion", "wave", "velocity", "acceleration", "physics"],
            "chemistry": ["molecule", "atom", "reaction", "compound", "element", "chemical", "bond"],
            "biology": ["cell", "organism", "dna", "protein", "evolution", "ecosystem", "biology"],
            "english": ["grammar", "literature", "writing", "essay", "poem", "novel", "language"],
            "computer_science": ["algorithm", "programming", "code", "software", "computer", "data"]
        }

        self.question_patterns = {
            QuestionType.DEFINITION: [
                r"what is", r"define", r"definition of", r"meaning of", r"explain what"
            ],
            QuestionType.EXPLANATION: [
                r"how does", r"why does", r"explain how", r"explain why", r"how can"
            ],
            QuestionType.PROBLEM_SOLVING: [
                r"solve", r"find", r"calculate", r"determine", r"how to"
            ],
            QuestionType.EXAMPLE_REQUEST: [
                r"example", r"show me", r"give me", r"provide", r"demonstrate"
            ],
            QuestionType.COMPARISON: [
                r"difference", r"compare", r"contrast", r"vs", r"versus", r"between"
            ],
            QuestionType.PROCESS: [
                r"steps", r"process", r"procedure", r"how to", r"method"
            ],
            QuestionType.CALCULATION: [
                r"calculate", r"compute", r"find the value", r"solve for", r"what is the"
            ]
        }

        self.difficulty_indicators = {
            "basic": ["simple", "basic", "easy", "fundamental", "introduction"],
            "intermediate": ["intermediate", "moderate", "standard", "typical"],
            "advanced": ["advanced", "complex", "difficult", "challenging", "sophisticated"]
        }

        self.cognitive_levels = {
            "remember": ["list", "recall", "name", "identify", "define"],
            "understand": ["explain", "describe", "interpret", "summarize", "classify"],
            "apply": ["solve", "use", "apply", "demonstrate", "calculate"],
            "analyze": ["analyze", "compare", "contrast", "examine", "distinguish"],
            "evaluate": ["evaluate", "assess", "judge", "critique", "argue"],
            "create": ["create", "design", "construct", "develop", "formulate"]
        }

    def analyze_query(self, query: str) -> QueryAnalysis:
        """Analyze a user query to understand educational intent"""
        query_lower = query.lower()

        # Detect question type
        question_type = self._detect_question_type(query_lower)

        # Detect subject hints
        subject_hints = self._detect_subjects(query_lower)

        # Extract key concepts
        key_concepts = self._extract_concepts(query)

        # Detect difficulty indicators
        difficulty_indicators = self._detect_difficulty(query_lower)

        # Determine if prerequisites are needed
        requires_prerequisites = self._needs_prerequisites(query_lower, question_type)

        # Determine if examples are needed
        requires_examples = self._needs_examples(query_lower, question_type)

        # Determine if visual aids are helpful
        requires_visual_aids = self._needs_visual_aids(query_lower, subject_hints)

        # Determine cognitive level
        cognitive_level = self._detect_cognitive_level(query_lower)

        # Estimate complexity
        estimated_complexity = self._estimate_complexity(query, key_concepts, difficulty_indicators)

        return QueryAnalysis(
            question_type=question_type,
            subject_hints=subject_hints,
            key_concepts=key_concepts,
            difficulty_indicators=difficulty_indicators,
            requires_prerequisites=requires_prerequisites,
            requires_examples=requires_examples,
            requires_visual_aids=requires_visual_aids,
            cognitive_level=cognitive_level,
            estimated_complexity=estimated_complexity
        )

    def _detect_question_type(self, query: str) -> QuestionType:
        """Detect the type of question being asked"""
        for question_type, patterns in self.question_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query):
                    return question_type
        return QuestionType.GENERAL

    def _detect_subjects(self, query: str) -> List[str]:
        """Detect subject hints in the query"""
        detected_subjects = []
        for subject, keywords in self.subject_keywords.items():
            for keyword in keywords:
                if keyword in query:
                    detected_subjects.append(subject)
                    break
        return list(set(detected_subjects))

    def _extract_concepts(self, query: str) -> List[str]:
        """Extract key concepts from the query"""
        # Simple approach - extract capitalized words and important terms
        concepts = []

        # Find capitalized words (likely proper nouns or important terms)
        capitalized_words = re.findall(r'\b[A-Z][a-z]+\b', query)
        concepts.extend(capitalized_words)

        # Find quoted terms
        quoted_terms = re.findall(r'"([^"]*)"', query)
        concepts.extend(quoted_terms)

        # Find mathematical terms
        math_terms = re.findall(r'\b(?:equation|formula|theorem|proof|function|derivative|integral)\b', query, re.IGNORECASE)
        concepts.extend(math_terms)

        return list(set(concepts))

    def _detect_difficulty(self, query: str) -> List[str]:
        """Detect difficulty indicators in the query"""
        detected_difficulty = []
        for level, indicators in self.difficulty_indicators.items():
            for indicator in indicators:
                if indicator in query:
                    detected_difficulty.append(level)
                    break
        return detected_difficulty

    def _needs_prerequisites(self, query: str, question_type: QuestionType) -> bool:
        """Determine if the query likely needs prerequisite knowledge"""
        prerequisite_indicators = ["advanced", "complex", "assuming", "given that", "prerequisite"]
        return any(indicator in query for indicator in prerequisite_indicators) or \
               question_type in [QuestionType.PROBLEM_SOLVING, QuestionType.CALCULATION]

    def _needs_examples(self, query: str, question_type: QuestionType) -> bool:
        """Determine if examples would be helpful"""
        return question_type in [QuestionType.EXAMPLE_REQUEST, QuestionType.EXPLANATION, QuestionType.PROCESS] or \
               any(word in query for word in ["example", "show", "demonstrate"])

    def _needs_visual_aids(self, query: str, subjects: List[str]) -> bool:
        """Determine if visual aids would be helpful"""
        visual_keywords = ["graph", "chart", "diagram", "figure", "image", "picture", "visualization"]
        return any(keyword in query for keyword in visual_keywords) or \
               any(subject in ["physics", "chemistry", "biology", "geometry"] for subject in subjects)

    def _detect_cognitive_level(self, query: str) -> str:
        """Detect cognitive level based on Bloom's taxonomy"""
        for level, keywords in self.cognitive_levels.items():
            for keyword in keywords:
                if keyword in query:
                    return level
        return "understand"  # Default level

    def _estimate_complexity(self, query: str, concepts: List[str], difficulty: List[str]) -> float:
        """Estimate query complexity on a scale of 0-1"""
        complexity = 0.3  # Base complexity

        # Add complexity based on query length
        complexity += min(len(query.split()) / 100, 0.2)

        # Add complexity based on number of concepts
        complexity += min(len(concepts) / 10, 0.2)

        # Add complexity based on difficulty indicators
        if "advanced" in difficulty:
            complexity += 0.3
        elif "intermediate" in difficulty:
            complexity += 0.2
        elif "basic" in difficulty:
            complexity += 0.1

        return min(complexity, 1.0)


class EducationalRetriever:
    """Intelligent retrieval system for educational content across multiple collections"""

    def __init__(self, qdrant_client: QdrantClient, embedding_manager):
        self.client = qdrant_client
        self.embedding_manager = embedding_manager
        self.query_analyzer = QueryAnalyzer()

        # Collection name patterns
        self.collection_pattern = r"grade_(\d+)_(.+)"

        # Subject mappings
        self.subject_synonyms = {
            "math": "mathematics",
            "physics": "physics",
            "chemistry": "chemistry",
            "bio": "biology",
            "cs": "computer_science",
            "programming": "computer_science"
        }

    async def retrieve(
        self,
        query: str,
        grade: int,
        subject: Optional[str] = None,
        limit: int = 10,
        include_related: bool = True
    ) -> List[RetrievalResult]:
        """Main retrieval method with intelligent collection selection and filtering"""

        # Analyze the query
        analysis = self.query_analyzer.analyze_query(query)
        logger.info(f"Query analysis: {analysis.question_type}, subjects: {analysis.subject_hints}")

        # Determine target collections
        target_collections = await self._determine_target_collections(grade, subject, analysis)

        # Generate query embedding
        query_embedding = await self.embedding_manager.get_text_embedding(query)
        if not query_embedding:
            logger.error("Failed to generate query embedding")
            return []

        # Search across target collections
        all_results = []
        for collection_name in target_collections:
            collection_results = await self._search_collection(
                collection_name=collection_name,
                query_embedding=query_embedding,
                analysis=analysis,
                limit=limit
            )
            all_results.extend(collection_results)

        # Re-rank and filter results
        ranked_results = await self._rerank_results(all_results, query, analysis, limit)

        # Enhance with related content if requested
        if include_related:
            enhanced_results = await self._enhance_with_context(ranked_results)
        else:
            enhanced_results = ranked_results

        return enhanced_results

    async def _determine_target_collections(
        self,
        grade: int,
        subject: Optional[str],
        analysis: QueryAnalysis
    ) -> List[str]:
        """Determine which collections to search based on query analysis"""

        target_collections = []

        # Normalize subject
        normalized_subject = self._normalize_subject(subject)

        if normalized_subject:
            # Search specified subject with special handling for Grade 6 science
            if grade == 6 and normalized_subject == "science":
                target_collections.append("grade_06_science")
            else:
                target_collections.append(f"grade_{grade}_{normalized_subject}")

            # Include prerequisite grades if needed
            if analysis.requires_prerequisites and grade > 6:
                for prereq_grade in range(max(6, grade - 2), grade):
                    if prereq_grade == 6 and normalized_subject == "science":
                        target_collections.append("grade_06_science")
                    else:
                        target_collections.append(f"grade_{prereq_grade}_{normalized_subject}")

        else:
            # Auto-detect subjects from query
            detected_subjects = analysis.subject_hints
            if not detected_subjects:
                # If no subjects detected, search common subjects for the grade
                detected_subjects = self._get_common_subjects_for_grade(grade)

            for subj in detected_subjects:
                normalized_subj = self._normalize_subject(subj)
                if normalized_subj:
                    # Special handling for Grade 6 science
                    if grade == 6 and normalized_subj == "science":
                        target_collections.append("grade_06_science")
                    else:
                        target_collections.append(f"grade_{grade}_{normalized_subj}")

                    # Include prerequisites if needed
                    if analysis.requires_prerequisites and grade > 6:
                        for prereq_grade in range(max(6, grade - 1), grade):
                            if prereq_grade == 6 and normalized_subj == "science":
                                target_collections.append("grade_06_science")
                            else:
                                target_collections.append(f"grade_{prereq_grade}_{normalized_subj}")

        # Remove duplicates and validate collections exist
        unique_collections = list(set(target_collections))
        valid_collections = await self._validate_collections(unique_collections)

        logger.info(f"Target collections: {valid_collections}")
        return valid_collections

    def _normalize_subject(self, subject: Optional[str]) -> Optional[str]:
        """Normalize subject name to match collection naming"""
        if not subject:
            return None

        subject_lower = subject.lower().replace(" ", "_").replace("-", "_")

        # Map all science subjects to unified "science" collection for Grade 10
        science_subjects = ["physics", "chemistry", "biology", "science"]
        if subject_lower in science_subjects:
            return "science"

        # Check synonyms
        if subject_lower in self.subject_synonyms:
            return self.subject_synonyms[subject_lower]

        return subject_lower

    def _get_common_subjects_for_grade(self, grade: int) -> List[str]:
        """Get common subjects for a grade level"""
        common_subjects = {
            6: ["mathematics", "science", "english"],
            7: ["mathematics", "science", "english"],
            8: ["mathematics", "physics", "chemistry", "biology", "english"],
            9: ["mathematics", "physics", "chemistry", "biology", "english"],
            10: ["mathematics", "science", "english"],  # Unified science collection for Grade 10
            11: ["mathematics", "physics", "chemistry", "biology", "english"],
            12: ["mathematics", "physics", "chemistry", "biology", "english"]
        }
        return common_subjects.get(grade, ["mathematics", "science", "english"])

    async def _validate_collections(self, collection_names: List[str]) -> List[str]:
        """Validate that collections exist"""
        valid_collections = []
        for collection_name in collection_names:
            try:
                collection_info = self.client.get_collection(collection_name)
                if collection_info:
                    valid_collections.append(collection_name)
            except Exception:
                logger.warning(f"Collection {collection_name} does not exist")
                continue
        return valid_collections

    async def _search_collection(
        self,
        collection_name: str,
        query_embedding: List[float],
        analysis: QueryAnalysis,
        limit: int
    ) -> List[RetrievalResult]:
        """Search a specific collection with intelligent filtering"""

        try:
            # Build filters based on query analysis
            filters = self._build_filters(analysis)

            # Perform vector search
            search_results = self.client.search(
                collection_name=collection_name,
                query_vector=query_embedding,
                query_filter=filters if filters else None,
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

            return results

        except Exception as e:
            logger.error(f"Failed to search collection {collection_name}: {e}")
            return []

    def _build_filters(self, analysis: QueryAnalysis) -> Optional[Filter]:
        """Build Qdrant filters based on query analysis"""
        must_conditions = []

        # Filter by content type if specific question type
        if analysis.question_type == QuestionType.DEFINITION:
            must_conditions.append(
                FieldCondition(
                    key="content_type",
                    match=MatchAny(any=["definition", "concept"])
                )
            )
        elif analysis.question_type == QuestionType.EXAMPLE_REQUEST:
            must_conditions.append(
                FieldCondition(
                    key="content_type",
                    match=MatchAny(any=["example", "exercise"])
                )
            )
        elif analysis.question_type == QuestionType.PROBLEM_SOLVING:
            must_conditions.append(
                FieldCondition(
                    key="content_type",
                    match=MatchAny(any=["example", "exercise", "solution"])
                )
            )

        # Filter by difficulty if specified
        if analysis.difficulty_indicators:
            must_conditions.append(
                FieldCondition(
                    key="difficulty_level",
                    match=MatchAny(any=analysis.difficulty_indicators)
                )
            )

        # Filter by cognitive level
        cognitive_levels = self._get_appropriate_cognitive_levels(analysis.cognitive_level)
        if cognitive_levels:
            must_conditions.append(
                FieldCondition(
                    key="cognitive_level",
                    match=MatchAny(any=cognitive_levels)
                )
            )

        # Return filter if we have conditions
        if must_conditions:
            return Filter(must=must_conditions)

        return None

    def _get_appropriate_cognitive_levels(self, target_level: str) -> List[str]:
        """Get appropriate cognitive levels including prerequisites"""
        level_hierarchy = ["remember", "understand", "apply", "analyze", "evaluate", "create"]

        try:
            target_index = level_hierarchy.index(target_level)
            # Include current level and lower levels
            return level_hierarchy[:target_index + 1]
        except ValueError:
            return ["understand"]  # Default

    async def _rerank_results(
        self,
        results: List[RetrievalResult],
        query: str,
        analysis: QueryAnalysis,
        limit: int
    ) -> List[RetrievalResult]:
        """Re-rank results based on educational relevance"""

        if not results:
            return []

        # Score adjustments based on educational factors
        for result in results:
            # Boost score for content type match
            content_type = result.metadata.get("content_type", "")
            if self._is_content_type_relevant(content_type, analysis.question_type):
                result.score *= 1.2

            # Boost score for difficulty match
            difficulty = result.metadata.get("difficulty_level", "")
            if difficulty in analysis.difficulty_indicators:
                result.score *= 1.1

            # Boost score for examples if needed
            if analysis.requires_examples and "example" in content_type:
                result.score *= 1.15

            # Boost score for visual content if needed
            if analysis.requires_visual_aids and result.metadata.get("figure_refs"):
                result.score *= 1.1

            # Penalize if too advanced or too basic
            if difficulty == "advanced" and "basic" in analysis.difficulty_indicators:
                result.score *= 0.8
            elif difficulty == "basic" and "advanced" in analysis.difficulty_indicators:
                result.score *= 0.8

        # Sort by adjusted score
        sorted_results = sorted(results, key=lambda x: x.score, reverse=True)

        # Remove duplicates based on content similarity
        deduplicated = self._remove_duplicates(sorted_results)

        return deduplicated[:limit]

    def _is_content_type_relevant(self, content_type: str, question_type: QuestionType) -> bool:
        """Check if content type is relevant for question type"""
        relevance_map = {
            QuestionType.DEFINITION: ["definition", "concept"],
            QuestionType.EXPLANATION: ["text", "concept", "definition"],
            QuestionType.PROBLEM_SOLVING: ["example", "exercise", "solution"],
            QuestionType.EXAMPLE_REQUEST: ["example", "exercise"],
            QuestionType.CALCULATION: ["formula", "example", "exercise"],
            QuestionType.PROCESS: ["text", "example"],
            QuestionType.COMPARISON: ["text", "concept"]
        }

        relevant_types = relevance_map.get(question_type, ["text"])
        return content_type in relevant_types

    def _remove_duplicates(self, results: List[RetrievalResult]) -> List[RetrievalResult]:
        """Remove duplicate results based on content similarity"""
        if not results:
            return []

        unique_results = [results[0]]  # Always include the first (highest scoring) result

        for result in results[1:]:
            is_duplicate = False
            for unique_result in unique_results:
                # Simple duplicate detection based on content similarity
                if self._are_similar_content(result.content, unique_result.content):
                    is_duplicate = True
                    break

            if not is_duplicate:
                unique_results.append(result)

        return unique_results

    def _are_similar_content(self, content1: str, content2: str, threshold: float = 0.8) -> bool:
        """Check if two content pieces are similar (simple approach)"""
        # Simple approach: check word overlap
        words1 = set(content1.lower().split())
        words2 = set(content2.lower().split())

        if len(words1) == 0 or len(words2) == 0:
            return False

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        jaccard_similarity = len(intersection) / len(union)
        return jaccard_similarity > threshold

    async def _enhance_with_context(self, results: List[RetrievalResult]) -> List[RetrievalResult]:
        """Enhance results with related content and context"""

        enhanced_results = []

        for result in results:
            # Fetch related content
            related_content = await self._fetch_related_content(result)

            # Fetch context (preceding/following content)
            context = await self._fetch_context(result)

            # Create enhanced result
            enhanced_result = RetrievalResult(
                id=result.id,
                content=result.content,
                score=result.score,
                collection_name=result.collection_name,
                metadata=result.metadata,
                context=context,
                related_content=related_content
            )

            enhanced_results.append(enhanced_result)

        return enhanced_results

    async def _fetch_related_content(self, result: RetrievalResult) -> List[Dict[str, Any]]:
        """Fetch related content (figures, tables, examples)"""
        related_content = []

        try:
            # Fetch referenced figures
            figure_refs = result.metadata.get("figure_refs", [])
            for fig_ref in figure_refs:
                figure_content = await self._fetch_figure_content(result.collection_name, fig_ref)
                if figure_content:
                    related_content.append({
                        "type": "figure",
                        "reference": fig_ref,
                        "content": figure_content
                    })

            # Fetch referenced tables
            table_refs = result.metadata.get("table_refs", [])
            for table_ref in table_refs:
                table_content = await self._fetch_table_content(result.collection_name, table_ref)
                if table_content:
                    related_content.append({
                        "type": "table",
                        "reference": table_ref,
                        "content": table_content
                    })

            # Fetch related examples
            if result.metadata.get("content_type") == "concept":
                examples = await self._fetch_related_examples(result)
                related_content.extend(examples)

        except Exception as e:
            logger.error(f"Failed to fetch related content: {e}")

        return related_content

    async def _fetch_context(self, result: RetrievalResult) -> Dict[str, Any]:
        """Fetch context around the result"""
        context = {}

        try:
            context["preceding"] = result.metadata.get("preceding_content", "")
            context["following"] = result.metadata.get("following_content", "")
            context["page_context"] = result.metadata.get("full_page_text", "")
            context["section_title"] = result.metadata.get("section", "")
            context["chapter"] = result.metadata.get("chapter", "")

        except Exception as e:
            logger.error(f"Failed to fetch context: {e}")

        return context

    async def _fetch_figure_content(self, collection_name: str, figure_ref: str) -> Optional[str]:
        """Fetch content for a specific figure reference"""
        # Implementation would search for figure content in the collection
        return None

    async def _fetch_table_content(self, collection_name: str, table_ref: str) -> Optional[str]:
        """Fetch content for a specific table reference"""
        # Implementation would search for table content in the collection
        return None

    async def _fetch_related_examples(self, result: RetrievalResult) -> List[Dict[str, Any]]:
        """Fetch related examples for a concept"""
        # Implementation would search for examples related to the same concept
        return []

    async def search_by_topic(
        self,
        topic: str,
        grade: int,
        subject: str,
        limit: int = 10
    ) -> List[RetrievalResult]:
        """Search for content by specific topic"""

        # Special handling for Grade 6 science
        normalized_subject = self._normalize_subject(subject)
        if grade == 6 and normalized_subject == "science":
            collection_name = "grade_06_science"
        else:
            collection_name = f"grade_{grade}_{normalized_subject}"

        try:
            # Search using metadata filter for topic
            search_results = self.client.scroll(
                collection_name=collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="topic",
                            match=MatchAny(any=[topic])
                        )
                    ]
                ),
                limit=limit,
                with_payload=True
            )

            results = []
            for result in search_results[0]:  # scroll returns (points, next_page_offset)
                retrieval_result = RetrievalResult(
                    id=str(result.id),
                    content=result.payload.get("content", ""),
                    score=1.0,  # No vector similarity, so use default score
                    collection_name=collection_name,
                    metadata=result.payload
                )
                results.append(retrieval_result)

            return results

        except Exception as e:
            logger.error(f"Failed to search by topic: {e}")
            return []

    async def get_curriculum_content(
        self,
        grade: int,
        subject: str,
        chapter: Optional[str] = None
    ) -> Dict[str, List[RetrievalResult]]:
        """Get structured curriculum content for a grade and subject"""

        # Special handling for Grade 6 science
        normalized_subject = self._normalize_subject(subject)
        if grade == 6 and normalized_subject == "science":
            collection_name = "grade_06_science"
        else:
            collection_name = f"grade_{grade}_{normalized_subject}"
        curriculum_content = {
            "concepts": [],
            "examples": [],
            "exercises": [],
            "definitions": []
        }

        try:
            # Build filter
            must_conditions = []
            if chapter:
                must_conditions.append(
                    FieldCondition(
                        key="chapter",
                        match=MatchValue(value=chapter)
                    )
                )

            # Search for different content types
            for content_type in curriculum_content.keys():
                if content_type == "concepts":
                    search_filter = Filter(
                        must=must_conditions + [
                            FieldCondition(
                                key="content_type",
                                match=MatchAny(any=["concept", "definition", "text"])
                            )
                        ]
                    )
                else:
                    search_filter = Filter(
                        must=must_conditions + [
                            FieldCondition(
                                key="content_type",
                                match=MatchValue(value=content_type.rstrip('s'))  # Remove plural 's'
                            )
                        ]
                    )

                search_results = self.client.scroll(
                    collection_name=collection_name,
                    scroll_filter=search_filter,
                    limit=50,
                    with_payload=True
                )

                for result in search_results[0]:
                    retrieval_result = RetrievalResult(
                        id=str(result.id),
                        content=result.payload.get("content", ""),
                        score=1.0,
                        collection_name=collection_name,
                        metadata=result.payload
                    )
                    curriculum_content[content_type].append(retrieval_result)

            return curriculum_content

        except Exception as e:
            logger.error(f"Failed to get curriculum content: {e}")
            return curriculum_content