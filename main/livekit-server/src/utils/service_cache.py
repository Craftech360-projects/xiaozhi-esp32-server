"""
Service Configuration Cache
Cache expensive service initialization data
"""

import logging
import time
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class ServiceCache:
    """Cache for expensive service initialization data"""
    _instance = None
    _cache: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def cache_music_metadata(self, languages: List[str], collections_info: Dict):
        """Cache music service metadata"""
        self._cache['music_languages'] = languages
        self._cache['music_collections'] = collections_info
        self._cache['music_cached_at'] = time.time()
        logger.info(f"[SERVICE_CACHE] Cached music metadata: {len(languages)} languages")

    def cache_story_metadata(self, categories: List[str], collections_info: Dict):
        """Cache story service metadata"""
        self._cache['story_categories'] = categories
        self._cache['story_collections'] = collections_info
        self._cache['story_cached_at'] = time.time()
        logger.info(f"[SERVICE_CACHE] Cached story metadata: {len(categories)} categories")

    def get_music_metadata(self) -> Optional[Dict]:
        """Get cached music metadata"""
        if 'music_languages' in self._cache:
            return {
                'languages': self._cache['music_languages'],
                'collections': self._cache['music_collections'],
                'cached_at': self._cache['music_cached_at']
            }
        return None

    def get_story_metadata(self) -> Optional[Dict]:
        """Get cached story metadata"""
        if 'story_categories' in self._cache:
            return {
                'categories': self._cache['story_categories'],
                'collections': self._cache['story_collections'],
                'cached_at': self._cache['story_cached_at']
            }
        return None

    def is_cache_valid(self, cache_key: str, max_age: int = 300) -> bool:
        """Check if cache is still valid (default: 5 minutes)"""
        cached_at_key = f"{cache_key}_cached_at"
        if cached_at_key in self._cache:
            age = time.time() - self._cache[cached_at_key]
            return age < max_age
        return False

# Global instance
service_cache = ServiceCache()