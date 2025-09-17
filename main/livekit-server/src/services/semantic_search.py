"""
Semantic Search Module for Music and Stories
Enhanced version with Qdrant integration
"""

import logging
import random
from typing import Dict, List, Optional
from dataclasses import dataclass
from .qdrant_semantic_search import QdrantSemanticSearch, QDRANT_AVAILABLE

logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    """Data class for search results"""
    title: str
    filename: str
    language_or_category: str
    score: float
    metadata: Dict

class SemanticSearchService:
    """
    Semantic search service for music and stories
    Uses Qdrant when available, falls back to text matching otherwise
    """

    def __init__(self):
        self.qdrant_search = QdrantSemanticSearch() if QDRANT_AVAILABLE else None
        self.is_qdrant_initialized = False
        self.logger = logger

        if not QDRANT_AVAILABLE:
            self.logger.warning("Qdrant not available, using fallback text search")

    async def initialize(self) -> bool:
        """Initialize Qdrant search using existing cloud collections only"""
        if not self.qdrant_search:
            return False

        try:
            # Initialize Qdrant connection
            initialized = await self.qdrant_search.initialize()
            if not initialized:
                return False

            # Just verify collections exist and use existing cloud data
            try:
                music_info = self.qdrant_search.client.get_collection(self.qdrant_search.config["music_collection"])
                self.logger.info(f"Using existing music collection with {music_info.points_count} songs")
            except Exception as e:
                self.logger.warning(f"Music collection not accessible: {e}")

            try:
                stories_info = self.qdrant_search.client.get_collection(self.qdrant_search.config["stories_collection"])
                self.logger.info(f"Using existing stories collection with {stories_info.points_count} stories")
            except Exception as e:
                self.logger.warning(f"Stories collection not accessible: {e}")

            self.is_qdrant_initialized = True
            self.logger.info("Qdrant semantic search initialized successfully (cloud-only)")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize Qdrant search: {e}")
            return False

    async def search_music(self, query: str, language: Optional[str] = None, limit: int = 5) -> List[SearchResult]:
        """Search for music using Qdrant cloud API only"""
        if self.is_qdrant_initialized:
            try:
                qdrant_results = await self.qdrant_search.search_music(query, language, limit)
                # Convert to SearchResult format
                results = []
                for result in qdrant_results:
                    results.append(SearchResult(
                        title=result.title,
                        filename=result.filename,
                        language_or_category=result.language_or_category,
                        score=result.score,
                        metadata=result.metadata
                    ))
                return results
            except Exception as e:
                self.logger.warning(f"Qdrant search failed: {e}")
                return []

        # No fallback - purely cloud-based
        self.logger.warning("Qdrant not initialized, cannot search")
        return []

    async def search_stories(self, query: str, category: Optional[str] = None, limit: int = 5) -> List[SearchResult]:
        """Search for stories using Qdrant cloud API only"""
        if self.is_qdrant_initialized:
            try:
                qdrant_results = await self.qdrant_search.search_stories(query, category, limit)
                # Convert to SearchResult format
                results = []
                for result in qdrant_results:
                    results.append(SearchResult(
                        title=result.title,
                        filename=result.filename,
                        language_or_category=result.language_or_category,
                        score=result.score,
                        metadata=result.metadata
                    ))
                return results
            except Exception as e:
                self.logger.warning(f"Qdrant search failed: {e}")
                return []

        # No fallback - purely cloud-based
        self.logger.warning("Qdrant not initialized, cannot search")
        return []


    async def get_random_music(self, language: Optional[str] = None) -> Optional[SearchResult]:
        """Get a random music item using Qdrant cloud API"""
        if self.is_qdrant_initialized:
            try:
                qdrant_result = await self.qdrant_search.get_random_music(language)
                if qdrant_result:
                    return SearchResult(
                        title=qdrant_result.title,
                        filename=qdrant_result.filename,
                        language_or_category=qdrant_result.language_or_category,
                        score=qdrant_result.score,
                        metadata=qdrant_result.metadata
                    )
            except Exception as e:
                self.logger.warning(f"Qdrant random music failed: {e}")

        return None

    async def get_random_story(self, category: Optional[str] = None) -> Optional[SearchResult]:
        """Get a random story item using Qdrant cloud API"""
        if self.is_qdrant_initialized:
            try:
                qdrant_result = await self.qdrant_search.get_random_story(category)
                if qdrant_result:
                    return SearchResult(
                        title=qdrant_result.title,
                        filename=qdrant_result.filename,
                        language_or_category=qdrant_result.language_or_category,
                        score=qdrant_result.score,
                        metadata=qdrant_result.metadata
                    )
            except Exception as e:
                self.logger.warning(f"Qdrant random story failed: {e}")

        return None

    async def get_available_languages(self) -> List[str]:
        """Get available music languages from Qdrant cloud API"""
        if self.is_qdrant_initialized:
            try:
                return await self.qdrant_search.get_available_languages()
            except Exception as e:
                self.logger.warning(f"Failed to get languages from Qdrant: {e}")

        return []

    async def get_available_categories(self) -> List[str]:
        """Get available story categories from Qdrant cloud API"""
        if self.is_qdrant_initialized:
            try:
                return await self.qdrant_search.get_available_categories()
            except Exception as e:
                self.logger.warning(f"Failed to get categories from Qdrant: {e}")

        return []