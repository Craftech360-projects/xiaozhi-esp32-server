"""
Simple File-Based Music Service (No Qdrant Required)
Handles music search and playback using direct file scanning
"""

import json
import os
import random
import logging
from typing import Dict, List, Optional
from pathlib import Path
import urllib.parse

logger = logging.getLogger(__name__)

class SimpleMusicService:
    """Service for handling music playback using file-based search (no Qdrant)"""

    def __init__(self):
        self.is_initialized = False

        # Media directory (where music files are stored)
        self.media_root = Path(__file__).parent.parent.parent / "media"
        self.music_cache = {}  # Cache of available songs

        logger.info("[SIMPLE MUSIC] ===== SimpleMusicService INITIALIZED (LOCAL FILE VERSION) =====")
        logger.info(f"[SIMPLE MUSIC] Media root: {self.media_root}")
        logger.info("[SIMPLE MUSIC] Will use file:// URLs for local playback")

    async def initialize(self) -> bool:
        """Initialize music service by scanning available music files"""
        try:
            logger.info("[SIMPLE MUSIC] Initializing file-based music service...")

            # Scan music directory and build cache
            self._scan_music_directory()

            if self.music_cache:
                logger.info(f"[SIMPLE MUSIC] Found {len(self.music_cache)} songs across {len(self._get_languages())} languages")
                self.is_initialized = True
                return True
            else:
                logger.warning("[SIMPLE MUSIC] No music files found in media directory")
                return False

        except Exception as e:
            logger.error(f"[SIMPLE MUSIC] Failed to initialize: {e}")
            return False

    def _scan_music_directory(self):
        """Scan music directory and build song cache"""
        music_dir = self.media_root / "music"

        if not music_dir.exists():
            logger.warning(f"[SIMPLE MUSIC] Music directory not found: {music_dir}")
            return

        # Scan each language folder
        for lang_dir in music_dir.iterdir():
            if not lang_dir.is_dir():
                continue

            language = lang_dir.name

            # Scan for MP3 files
            for music_file in lang_dir.glob("*.mp3"):
                # Create searchable entry
                filename = music_file.name
                title = filename.replace(".mp3", "").replace("_", " ")

                # Generate file:// URL for local file
                file_url = music_file.as_uri()

                # Add to cache
                cache_key = f"{language}:{filename.lower()}"
                self.music_cache[cache_key] = {
                    'title': title,
                    'filename': filename,
                    'language': language,
                    'url': file_url,  # Use file:// URL instead of HTTP
                    'searchable': title.lower(),
                    'file_path': music_file  # Keep path for reference
                }
                logger.debug(f"[SIMPLE MUSIC] Cached: {title} -> {file_url[:80]}...")

        logger.info(f"[SIMPLE MUSIC] Cached {len(self.music_cache)} songs with file:// URLs")

    async def search_songs(self, query: str, language: Optional[str] = None) -> List[Dict]:
        """Search for songs using simple text matching"""
        if not self.is_initialized:
            logger.warning(f"[SIMPLE MUSIC] Service not initialized - cannot search for '{query}'")
            return []

        try:
            query_lower = query.lower()
            results = []

            # Search through cached songs
            for cache_key, song in self.music_cache.items():
                # Filter by language if specified
                if language and song['language'] != language:
                    continue

                # Simple text matching
                searchable = song['searchable']

                # Calculate simple match score
                score = 0
                if query_lower == searchable:
                    score = 1.0  # Exact match
                elif query_lower in searchable:
                    score = 0.8  # Partial match
                elif any(word in searchable for word in query_lower.split()):
                    score = 0.6  # Word match
                else:
                    # Check if searchable contains parts of query
                    query_words = query_lower.split()
                    matching_words = sum(1 for word in query_words if word in searchable)
                    if matching_words > 0:
                        score = 0.4 * (matching_words / len(query_words))

                # Add to results if score is good enough
                if score > 0:
                    results.append({
                        'title': song['title'],
                        'filename': song['filename'],
                        'language': song['language'],
                        'url': song['url'],
                        'score': score
                    })

            # Sort by score (highest first)
            results.sort(key=lambda x: x['score'], reverse=True)

            # Limit to top 5 results
            results = results[:5]

            if results:
                logger.info(f"🎵 [SIMPLE] Found {len(results)} songs for '{query}' - top match: '{results[0]['title']}' (score: {results[0]['score']:.2f})")
            else:
                logger.warning(f"🎵 [SIMPLE] No songs found for '{query}'")

            return results

        except Exception as e:
            logger.error(f"[SIMPLE MUSIC] Search error: {e}")
            return []

    async def get_random_song(self, language: Optional[str] = None) -> Optional[Dict]:
        """Get a random song, optionally filtered by language"""
        if not self.is_initialized or not self.music_cache:
            logger.warning("[SIMPLE MUSIC] No songs available for random selection")
            return None

        try:
            # Filter songs by language if specified
            available_songs = [
                song for song in self.music_cache.values()
                if language is None or song['language'] == language
            ]

            if not available_songs:
                logger.warning(f"[SIMPLE MUSIC] No songs found for language: {language}")
                return None

            # Pick random song
            song = random.choice(available_songs)
            logger.info(f"🎵 [SIMPLE] Random song selected: '{song['title']}' ({song['language']})")

            return {
                'title': song['title'],
                'filename': song['filename'],
                'language': song['language'],
                'url': song['url']
            }

        except Exception as e:
            logger.error(f"[SIMPLE MUSIC] Error getting random song: {e}")
            return None

    def _get_languages(self) -> List[str]:
        """Get list of available languages"""
        languages = set()
        for song in self.music_cache.values():
            languages.add(song['language'])
        return sorted(list(languages))

    async def get_all_languages(self) -> List[str]:
        """Get all available music languages"""
        return self._get_languages()
