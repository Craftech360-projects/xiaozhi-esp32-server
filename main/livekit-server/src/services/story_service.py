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

logger = logging.getLogger(__name__)

class StoryService:
    """Service for handling story playback and search"""

    def __init__(self):
        self.metadata = {}
        self.cloudfront_domain = os.getenv("CLOUDFRONT_DOMAIN", "")
        self.s3_base_url = os.getenv("S3_BASE_URL", "")
        self.use_cdn = os.getenv("USE_CDN", "true").lower() == "true"
        self.is_initialized = False

    async def initialize(self) -> bool:
        """Initialize story service with simple search (no semantic search)"""
        try:
            # Simple initialization without semantic search
            logger.info("✅ Story service initialized with simple search (semantic search disabled)")
            self.is_initialized = True
            return True

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
        """Simple story search without semantic search - returns empty for now"""
        if not self.is_initialized:
            logger.warning(f"Story service not initialized - cannot search for '{query}'")
            return []

        try:
            # Simplified search - semantic search removed for performance
            logger.info(f"📚 Story search disabled (semantic search removed for performance) - returning random story instead")

            # Return empty list to trigger random story selection
            return []

        except Exception as e:
            logger.error(f"Error in story search for '{query}': {e}")
            return []

    async def get_random_story(self, category: Optional[str] = None) -> Optional[Dict]:
        """Get a random story - simplified without semantic search"""
        if not self.is_initialized:
            return None

        try:
            # Simplified random story - hardcoded for now since semantic search is removed
            # You can replace this with a simple file-based approach or API call
            sample_stories = [
                {
                    'title': 'The Three Little Pigs',
                    'filename': 'three_little_pigs.mp3',
                    'category': 'Adventure'
                },
                {
                    'title': 'Goldilocks and the Three Bears',
                    'filename': 'goldilocks.mp3',
                    'category': 'Adventure'
                },
                {
                    'title': 'Little Red Riding Hood',
                    'filename': 'red_riding_hood.mp3',
                    'category': 'Adventure'
                }
            ]

            # Select a random story
            story = random.choice(sample_stories)
            story['url'] = self.get_story_url(story['filename'], story['category'])

            logger.info(f"📚 Selected random story: {story['title']}")
            return story

        except Exception as e:
            logger.error(f"Error getting random story: {e}")
            return None

    async def get_all_categories(self) -> List[str]:
        """Get list of available story categories - simplified"""
        if not self.is_initialized:
            return []

        # Simplified categories list
        return ["Adventure", "Bedtime", "Educational", "Fantasy", "Comedy"]