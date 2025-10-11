"""
Music Service Module for LiveKit Agent
Handles music search and playback from LOCAL FILES
"""

import random
import logging
from typing import Dict, List, Optional
from pathlib import Path
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

class MusicService:
    """Service for handling LOCAL music playback and search"""

    def __init__(self, preloaded_model=None, preloaded_client=None):
        # Note: preloaded_model and preloaded_client kept for backward compatibility
        # Base path for local media files
        self.media_base_path = Path(__file__).parent.parent.parent / "media" / "music"
        self.is_initialized = False
        self.music_index = {}  # Cache of available music files
        logger.info(f"[LOCAL MUSIC] ===== MusicService INITIALIZED (LOCAL VERSION) =====")
        logger.info(f"[LOCAL MUSIC] Base path: {self.media_base_path}")
        logger.info(f"[LOCAL MUSIC] This is the NEW local-file-based music service")

    async def initialize(self) -> bool:
        """Initialize local music service by scanning media folder"""
        try:
            if not self.media_base_path.exists():
                logger.error(f"[LOCAL MUSIC] Media folder not found: {self.media_base_path}")
                return False

            # Scan all language folders
            self._build_music_index()

            if self.music_index:
                logger.info(f"[LOCAL MUSIC] Initialized with {sum(len(songs) for songs in self.music_index.values())} songs across {len(self.music_index)} languages")
                self.is_initialized = True
                return True
            else:
                logger.warning("[LOCAL MUSIC] No music files found in media folder")
                return False

        except Exception as e:
            logger.error(f"[LOCAL MUSIC] Failed to initialize: {e}")
            return False

    def _build_music_index(self):
        """Build index of all available music files"""
        self.music_index = {}

        # Scan each language folder
        for language_folder in self.media_base_path.iterdir():
            if language_folder.is_dir():
                language_name = language_folder.name
                songs = []

                # Find all audio files
                for audio_file in language_folder.glob("*.mp3"):
                    if audio_file.name.startswith("."):
                        continue  # Skip hidden files

                    # Extract song title (remove .mp3 extension)
                    title = audio_file.stem

                    songs.append({
                        "title": title,
                        "filename": audio_file.name,
                        "path": audio_file,
                        "language": language_name
                    })

                if songs:
                    self.music_index[language_name] = songs
                    logger.info(f"[LOCAL MUSIC] Found {len(songs)} songs in {language_name}")

    def get_song_url(self, filepath: Path) -> str:
        """Generate file:// URL for local song file"""
        # Convert Windows path to file:// URL
        url = filepath.as_uri()
        logger.info(f"[LOCAL MUSIC] Generated URL: {url[:80]}...")
        return url

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

    async def search_songs(self, query: str, language: Optional[str] = None) -> List[Dict]:
        """Search for songs using simple fuzzy matching"""
        logger.info(f"[LOCAL MUSIC] ===== SEARCH_SONGS CALLED =====")
        logger.info(f"[LOCAL MUSIC] Query: '{query}', Language: '{language}'")
        logger.info(f"[LOCAL MUSIC] Initialized: {self.is_initialized}")

        if not self.is_initialized:
            logger.warning(f"[LOCAL MUSIC] Service not initialized - cannot search for '{query}'")
            return []

        try:
            results = []

            # Determine which languages to search
            if language and language in self.music_index:
                search_languages = [language]
            else:
                search_languages = list(self.music_index.keys())

            logger.info(f"[LOCAL MUSIC] Searching in languages: {search_languages}")

            # Search through songs
            for lang in search_languages:
                for song in self.music_index[lang]:
                    score = self._similarity_score(query, song["title"])

                    # Only include if score is above threshold
                    if score > 0.3:  # Adjust threshold as needed
                        results.append({
                            "title": song["title"],
                            "filename": song["filename"],
                            "language": song["language"],
                            "url": self.get_song_url(song["path"]),
                            "score": score
                        })

            # Sort by score (highest first)
            results.sort(key=lambda x: x["score"], reverse=True)

            # Limit to top 5 results
            results = results[:5]

            if results:
                logger.info(f"🎵 [LOCAL] Found {len(results)} songs for '{query}' - top match: '{results[0]['title']}' (score: {results[0]['score']:.2f})")
            else:
                logger.warning(f"🎵 [LOCAL] No songs found for '{query}'")

            return results

        except Exception as e:
            logger.error(f"[LOCAL MUSIC] Error searching songs for '{query}': {e}")
            return []

    async def get_random_song(self, language: Optional[str] = None) -> Optional[Dict]:
        """Get a random song from local collection"""
        logger.info(f"[LOCAL MUSIC] ===== GET_RANDOM_SONG CALLED =====")
        logger.info(f"[LOCAL MUSIC] Language: '{language}'")
        logger.info(f"[LOCAL MUSIC] Initialized: {self.is_initialized}")

        if not self.is_initialized:
            logger.warning(f"[LOCAL MUSIC] Service not initialized")
            return None

        try:
            # Determine which languages to choose from
            if language and language in self.music_index:
                available_songs = self.music_index[language]
            else:
                # Get all songs from all languages
                available_songs = []
                for songs in self.music_index.values():
                    available_songs.extend(songs)

            if not available_songs:
                logger.warning(f"[LOCAL MUSIC] No songs available for language: {language}")
                return None

            # Pick random song
            song = random.choice(available_songs)

            logger.info(f"🎵 [LOCAL] Random song selected: '{song['title']}' ({song['language']})")

            return {
                "title": song["title"],
                "filename": song["filename"],
                "language": song["language"],
                "url": self.get_song_url(song["path"])
            }

        except Exception as e:
            logger.error(f"[LOCAL MUSIC] Error getting random song: {e}")
            return None

    async def get_all_languages(self) -> List[str]:
        """Get list of all available music languages"""
        if not self.is_initialized:
            return []

        return list(self.music_index.keys())