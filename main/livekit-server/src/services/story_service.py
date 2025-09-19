"""
Story Service Module for LiveKit Agent
Handles story search and playback with AWS CloudFront streaming
"""

import json
import os
import random
import logging
from typing import Dict, List, Optional
from pathlib import Path
import urllib.parse
from .semantic_search import QdrantSemanticSearch

logger = logging.getLogger(__name__)

class StoryService:
    """Service for handling story playback and search"""

    def __init__(self):
        self.metadata = {}
        self.cloudfront_domain = os.getenv("CLOUDFRONT_DOMAIN", "")
        self.s3_base_url = os.getenv("S3_BASE_URL", "")
        self.use_cdn = os.getenv("USE_CDN", "true").lower() == "true"
        self.is_initialized = False
        self.semantic_search = QdrantSemanticSearch()

    async def initialize(self) -> bool:
        """Initialize story service using only Qdrant cloud API"""
        try:
            # Initialize semantic search without local metadata
            try:
                initialized = await self.semantic_search.initialize()
                if initialized:
                    logger.info("✅ Story service initialized with Qdrant cloud API")
                    self.is_initialized = True
                    return True
                else:
                    logger.warning("⚠️ Qdrant initialization failed, story service will be limited")
                    return False
            except Exception as e:
                logger.error(f"Failed to initialize Qdrant semantic search: {e}")
                return False

        except Exception as e:
            logger.error(f"Failed to initialize story service: {e}")
            return False

    def get_story_url(self, filename: str, category: str = "Adventure") -> str:
        """Generate URL for story file"""
        audio_path = f"stories/{category}/{filename}"
        encoded_path = urllib.parse.quote(audio_path)

        if self.use_cdn and self.cloudfront_domain:
            return f"https://{self.cloudfront_domain}/{encoded_path}"
        else:
            return f"{self.s3_base_url}/{encoded_path}"

    async def search_stories(self, query: str, category: Optional[str] = None) -> List[Dict]:
        """Search for stories using enhanced semantic search with spell tolerance"""
        if not self.is_initialized:
            logger.warning(f"Story service not initialized - cannot search for '{query}'")
            return []

        try:
            # Use semantic search service with enhanced fuzzy matching
            search_results = await self.semantic_search.search_stories(query, category, limit=5)

            # Convert search results to expected format
            results = []
            for result in search_results:
                results.append({
                    'title': result.title,
                    'filename': result.filename,
                    'category': result.language_or_category,
                    'url': self.get_story_url(result.filename, result.language_or_category),
                    'score': result.score
                })

            if results:
                logger.info(f"📚 Found {len(results)} stories for '{query}' - top match: '{results[0]['title']}' (score: {results[0]['score']:.2f})")
            else:
                logger.warning(f"📚 No stories found for '{query}' - check spelling or try different terms")

            return results
            
        except Exception as e:
            logger.error(f"Error searching stories for '{query}': {e}")
            return []

    async def get_random_story(self, category: Optional[str] = None) -> Optional[Dict]:
        """Get a random story using Qdrant cloud API"""
        if not self.is_initialized:
            return None

        # Use semantic search service to get random story from Qdrant cloud
        result = await self.semantic_search.get_random_story(category)

        if result:
            return {
                'title': result.title,
                'filename': result.filename,
                'category': result.language_or_category,
                'url': self.get_story_url(result.filename, result.language_or_category)
            }

        return None

    async def get_all_categories(self) -> List[str]:
        """Get list of all available story categories from Qdrant cloud"""
        if not self.is_initialized:
            return []

        return await self.semantic_search.get_available_categories()