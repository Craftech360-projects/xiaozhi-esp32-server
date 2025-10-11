"""
Story Service Module for LiveKit Agent
Handles story search and playback from LOCAL FILES
"""

import os
import random
import logging
from typing import Dict, List, Optional
from pathlib import Path
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

class StoryService:
    """Service for handling LOCAL story playback and search"""

    def __init__(self, preloaded_model=None, preloaded_client=None):
        # Note: preloaded_model and preloaded_client kept for backward compatibility
        self.is_initialized = False

        # Base path for local story files (flat directory)
        self.stories_path = Path(__file__).parent.parent / "stories"
        self.story_index = {}  # Cache of available stories

        logger.info("[STORY SERVICE] ===== StoryService INITIALIZED (LOCAL FILE VERSION) =====")
        logger.info(f"[STORY SERVICE] Stories path: {self.stories_path}")
        logger.info("[STORY SERVICE] Will use file:// URLs for local playback")

    async def initialize(self) -> bool:
        """Initialize local story service by scanning stories folder"""
        try:
            if not self.stories_path.exists():
                logger.error(f"[STORY SERVICE] Stories folder not found: {self.stories_path}")
                return False

            # Scan all story files
            self._build_story_index()

            if self.story_index:
                logger.info(f"[STORY SERVICE] Initialized with {len(self.story_index)} stories")
                self.is_initialized = True
                return True
            else:
                logger.warning("[STORY SERVICE] No story files found in stories folder")
                return False

        except Exception as e:
            logger.error(f"[STORY SERVICE] Failed to initialize: {e}")
            return False

    def _build_story_index(self):
        """Build index of all available story files"""
        self.story_index = {}

        # Scan for MP3 files in stories directory (flat structure)
        for story_file in self.stories_path.glob("*.mp3"):
            if story_file.name.startswith("."):
                continue  # Skip hidden files

            # Extract story title (remove .mp3 extension)
            title = story_file.stem

            # Generate file:// URL
            file_url = story_file.as_uri()

            # Assign a default category (we don't have category folders)
            category = "Stories"

            self.story_index[title.lower()] = {
                "title": title.title(),  # Capitalize words
                "filename": story_file.name,
                "category": category,
                "path": story_file,
                "url": file_url
            }

            logger.debug(f"[STORY SERVICE] Cached: {title.title()} -> {file_url[:80]}...")

        logger.info(f"[STORY SERVICE] Cached {len(self.story_index)} stories with file:// URLs")

    def _similarity_score(self, query: str, title: str) -> float:
        """Calculate similarity between query and title"""
        query_lower = query.lower().strip()
        title_lower = title.lower().strip()

        # Exact match
        if query_lower == title_lower:
            return 1.0

        # Contains match
        if query_lower in title_lower:
            return 0.8

        # Fuzzy match using SequenceMatcher
        return SequenceMatcher(None, query_lower, title_lower).ratio()

    async def search_stories(self, query: str, category: Optional[str] = None) -> List[Dict]:
        """Search for stories using simple fuzzy matching"""
        logger.info(f"[STORY SERVICE] ===== SEARCH_STORIES CALLED =====")
        logger.info(f"[STORY SERVICE] Query: '{query}', Category: '{category}'")

        if not self.is_initialized:
            logger.warning(f"[STORY SERVICE] Service not initialized - cannot search for '{query}'")
            return []

        try:
            results = []

            # Search through stories
            for key, story in self.story_index.items():
                score = self._similarity_score(query, story["title"])

                # Only include if score is above threshold
                if score > 0.3:
                    results.append({
                        "title": story["title"],
                        "filename": story["filename"],
                        "category": story["category"],
                        "url": story["url"],
                        "score": score
                    })

            # Sort by score (highest first)
            results.sort(key=lambda x: x["score"], reverse=True)

            # Limit to top 5 results
            results = results[:5]

            if results:
                logger.info(f"📚 [LOCAL] Found {len(results)} stories for '{query}' - top match: '{results[0]['title']}' (score: {results[0]['score']:.2f})")
            else:
                logger.warning(f"📚 [LOCAL] No stories found for '{query}'")

            return results

        except Exception as e:
            logger.error(f"[STORY SERVICE] Error searching stories for '{query}': {e}")
            return []

    async def get_random_story(self, category: Optional[str] = None) -> Optional[Dict]:
        """Get a random story from local collection"""
        logger.info(f"[STORY SERVICE] ===== GET_RANDOM_STORY CALLED =====")
        logger.info(f"[STORY SERVICE] Category: '{category}'")

        if not self.is_initialized:
            logger.warning("[STORY SERVICE] Service not initialized")
            return None

        try:
            if not self.story_index:
                logger.warning("[STORY SERVICE] No stories available")
                return None

            # Get all stories as a list
            available_stories = list(self.story_index.values())

            # Pick random story
            story = random.choice(available_stories)

            logger.info(f"📚 [LOCAL] Random story selected: '{story['title']}'")

            return {
                "title": story["title"],
                "filename": story["filename"],
                "category": story["category"],
                "url": story["url"]
            }

        except Exception as e:
            logger.error(f"[STORY SERVICE] Error getting random story: {e}")
            return None

    async def get_all_categories(self) -> List[str]:
        """Get list of available story categories"""
        if not self.is_initialized:
            return []

        # Since we use a flat directory structure, return a generic category
        return ["Stories"]