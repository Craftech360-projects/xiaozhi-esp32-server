"""
Simple Qdrant Client for Random Song Selection
No semantic search, no embeddings - just random selection
"""
import random
import logging
from typing import Optional, Dict
from qdrant_client import QdrantClient

logger = logging.getLogger(__name__)

class SimpleQdrantMusic:
    """Minimal Qdrant client for random song selection"""

    def __init__(self, url: str, api_key: str, cloudfront_domain: str):
        self.client = QdrantClient(url=url, api_key=api_key, timeout=10)
        self.collection = "xiaozhi_music"
        self.cloudfront_domain = cloudfront_domain
        self.is_initialized = False

    async def initialize(self) -> bool:
        """Test connection to Qdrant"""
        try:
            collection_info = self.client.get_collection(self.collection)
            logger.info(f"✅ Connected to Qdrant: {collection_info.points_count} songs available")
            self.is_initialized = True
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to Qdrant: {e}")
            return False

    def get_random_song(self, language: Optional[str] = None) -> Optional[Dict]:
        """
        Get a random song from Qdrant collection

        Args:
            language: Optional language filter (e.g., "English", "Hindi")

        Returns:
            Dict with song info or None if no songs found
        """
        if not self.is_initialized:
            logger.warning("Qdrant not initialized")
            return None

        try:
            # Fetch random sample of songs
            scroll_result = self.client.scroll(
                collection_name=self.collection,
                limit=100,  # Get 100 songs to choose from
                with_payload=True
            )

            points = scroll_result[0]

            if not points:
                logger.warning("No songs found in Qdrant")
                return None

            # Filter by language if specified
            if language:
                points = [p for p in points if p.payload.get('language') == language]
                if not points:
                    logger.warning(f"No songs found for language: {language}")
                    return None

            # Pick a random song
            random_point = random.choice(points)
            payload = random_point.payload

            # Build CDN URL
            filename = payload.get('filename')
            song_language = payload.get('language')
            cdn_url = f"https://{self.cloudfront_domain}/music/{song_language}/{filename}"

            song_info = {
                'title': payload.get('title'),
                'filename': filename,
                'language': song_language,
                'url': cdn_url
            }

            logger.info(f"🎵 Selected random song: '{song_info['title']}' ({song_info['language']})")
            return song_info

        except Exception as e:
            logger.error(f"❌ Error getting random song: {e}")
            return None

    def get_available_languages(self) -> list:
        """Get list of all available languages"""
        if not self.is_initialized:
            return []

        try:
            scroll_result = self.client.scroll(
                collection_name=self.collection,
                limit=1000,
                with_payload=["language"]
            )

            languages = set()
            for point in scroll_result[0]:
                if 'language' in point.payload:
                    languages.add(point.payload['language'])

            return sorted(list(languages))

        except Exception as e:
            logger.error(f"Error getting languages: {e}")
            return []
