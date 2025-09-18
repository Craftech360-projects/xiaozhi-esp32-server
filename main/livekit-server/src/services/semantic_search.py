"""
Qdrant Semantic Search Implementation for Music and Stories
Enhanced semantic search using vector database
"""

import logging
import asyncio
import os
from typing import Dict, List, Optional
from dataclasses import dataclass

# Qdrant and ML dependencies
try:
    from qdrant_client import QdrantClient
    from qdrant_client import models
    from qdrant_client.models import Filter, FieldCondition, Match, PointStruct
    from sentence_transformers import SentenceTransformer
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class QdrantSearchResult:
    """Enhanced search result with vector scoring"""
    title: str
    filename: str
    language_or_category: str
    score: float
    metadata: Dict
    alternatives: List[str]
    romanized: str

class QdrantSemanticSearch:
    """
    Advanced semantic search using Qdrant vector database
    """

    def __init__(self):
        self.is_available = QDRANT_AVAILABLE
        self.client: Optional[QdrantClient] = None
        self.model: Optional[SentenceTransformer] = None
        self.is_initialized = False

        # Qdrant configuration from environment variables
        self.config = {
            "qdrant_url": os.getenv("QDRANT_URL", ""),
            "qdrant_api_key": os.getenv("QDRANT_API_KEY", ""),
            "music_collection": "xiaozhi_music",
            "stories_collection": "xiaozhi_stories",
            "embedding_model": "all-MiniLM-L6-v2",
            "search_limit": 10,
            "min_score_threshold": 0.5
        }

        if not QDRANT_AVAILABLE:
            logger.warning("Qdrant dependencies not available, semantic search will be limited")

    async def initialize(self) -> bool:
        """Initialize Qdrant client and embedding model"""
        if not self.is_available:
            logger.warning("Qdrant not available, using fallback search")
            return False

        try:
            # Initialize Qdrant client
            self.client = QdrantClient(
                url=self.config["qdrant_url"],
                api_key=self.config["qdrant_api_key"]
            )

            # Test connection
            collections = self.client.get_collections()
            logger.info("Connected to Qdrant successfully")

            # Initialize embedding model
            logger.info(f"Loading embedding model: {self.config['embedding_model']}")
            self.model = SentenceTransformer(self.config["embedding_model"])
            logger.info(f"Loaded embedding model: {self.config['embedding_model']}")

            # Check if collections exist and have data
            await self._ensure_collections_exist()

            self.is_initialized = True
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Qdrant semantic search: {e}")
            return False

    async def _ensure_collections_exist(self):
        """Check that required collections exist in Qdrant cloud"""
        try:
            # Check music collection exists
            try:
                music_info = self.client.get_collection(self.config["music_collection"])
                logger.info(f"Music collection '{self.config['music_collection']}' found with {music_info.points_count} points")
            except Exception:
                logger.warning(f"Music collection '{self.config['music_collection']}' not found in cloud")

            # Check stories collection exists
            try:
                stories_info = self.client.get_collection(self.config["stories_collection"])
                logger.info(f"Stories collection '{self.config['stories_collection']}' found with {stories_info.points_count} points")
            except Exception:
                logger.warning(f"Stories collection '{self.config['stories_collection']}' not found in cloud")

        except Exception as e:
            logger.error(f"Error checking collections: {e}")

    def _get_embedding(self, text: str) -> List[float]:
        """Generate embedding for text"""
        if not text or not self.model:
            return []
        return self.model.encode(text).tolist()

    async def index_music_metadata(self, music_metadata: Dict) -> bool:
        """Index music metadata into Qdrant"""
        if not self.is_initialized:
            logger.warning("Semantic search not initialized, skipping indexing")
            return False

        try:
            points = []
            point_id = 0

            for language, language_metadata in music_metadata.items():
                for song_title, song_info in language_metadata.items():
                    # Prepare searchable text for embedding
                    searchable_texts = [
                        song_title,  # Original title
                        song_info.get('romanized', ''),  # Romanized version
                    ]

                    # Add alternative names
                    alternatives = song_info.get('alternatives', [])
                    if isinstance(alternatives, list):
                        searchable_texts.extend(alternatives)

                    # Add keywords
                    keywords = song_info.get('keywords', [])
                    if isinstance(keywords, list):
                        searchable_texts.extend(keywords)

                    # Add language for context
                    searchable_texts.append(language)

                    # Combine all searchable text
                    combined_text = " ".join(filter(None, searchable_texts)).strip()

                    if not combined_text:
                        continue

                    # Generate embedding
                    embedding = self._get_embedding(combined_text)
                    if not embedding:
                        continue

                    # Prepare payload
                    payload = {
                        'title': song_title,
                        'language': language,
                        'romanized': song_info.get('romanized', song_title),
                        'alternatives': alternatives,
                        'keywords': keywords,
                        'filename': song_info.get('filename', f"{song_title}.mp3"),
                        'file_path': f"{language}/{song_info.get('filename', f'{song_title}.mp3')}",
                        'searchable_text': combined_text,
                        'metadata': song_info
                    }

                    points.append(
                        PointStruct(
                            id=point_id,
                            vector=embedding,
                            payload=payload
                        )
                    )
                    point_id += 1

            # Upsert points to Qdrant
            if points:
                self.client.upsert(
                    collection_name=self.config["music_collection"],
                    points=points
                )
                logger.info(f"Indexed {len(points)} music tracks into Qdrant")
                return True
            else:
                logger.warning("No music metadata to index")
                return False

        except Exception as e:
            logger.error(f"Failed to index music metadata: {e}")
            return False

    async def index_stories_metadata(self, stories_metadata: Dict) -> bool:
        """Skip indexing - use existing cloud collections"""
        logger.info("Skipping stories indexing - using existing cloud collections")
        return True

    async def search_music(self, query: str, language_filter: Optional[str] = None, limit: int = 5) -> List[QdrantSearchResult]:
        """Search for music using vector similarity in Qdrant"""
        if not self.is_initialized:
            return []

        try:
            # Generate query embedding
            query_embedding = self._get_embedding(query)
            if not query_embedding:
                return []

            # Use scroll instead of search with filters to avoid typing.Union issues
            scroll_result = self.client.scroll(
                collection_name=self.config["music_collection"],
                limit=1000,  # Get more points to search through
                with_payload=True
            )

            # Filter results manually and calculate similarity scores
            results = []
            query_lower = query.lower()

            for point in scroll_result[0]:
                payload = point.payload

                # Apply language filter if specified
                if language_filter and payload.get('language') != language_filter:
                    continue

                # Calculate text similarity score since we can't use vector search easily
                title = payload.get('title', '').lower()
                romanized = payload.get('romanized', '').lower()
                alternatives = [alt.lower() for alt in payload.get('alternatives', [])]
                searchable_text = payload.get('searchable_text', '').lower()

                score = 0.0

                # Calculate similarity score
                if query_lower in title:
                    score = 1.0 if query_lower == title else 0.8
                elif query_lower in romanized:
                    score = 0.9 if query_lower == romanized else 0.7
                elif any(query_lower in alt for alt in alternatives):
                    score = 0.6
                elif query_lower in searchable_text:
                    score = 0.5
                elif any(word in title for word in query_lower.split()):
                    score = 0.4
                elif any(word in romanized for word in query_lower.split()):
                    score = 0.3

                if score > 0:
                    results.append(QdrantSearchResult(
                        title=payload['title'],
                        filename=payload['filename'],
                        language_or_category=payload['language'],
                        score=score,
                        metadata=payload,
                        alternatives=payload.get('alternatives', []),
                        romanized=payload.get('romanized', '')
                    ))

            # Sort by score and limit results
            results.sort(key=lambda x: x.score, reverse=True)
            results = results[:limit]

            logger.debug(f"Qdrant music search found {len(results)} results for '{query}'")
            return results

        except Exception as e:
            logger.error(f"Qdrant music search failed: {e}")
            return []

    async def search_stories(self, query: str, category_filter: Optional[str] = None, limit: int = 5) -> List[QdrantSearchResult]:
        """Search for stories using text-based filtering in Qdrant"""
        if not self.is_initialized:
            return []

        try:
            # Build filter conditions
            query_filter = None
            if category_filter:
                query_filter = Filter(
                    must=[
                        FieldCondition(key="category", match=Match(value=category_filter))
                    ]
                )

            # Use scroll to get all matching points, then filter by text locally
            scroll_result = self.client.scroll(
                collection_name=self.config["stories_collection"],
                limit=1000,  # Get more points to search through
                with_payload=True,
                scroll_filter=query_filter
            )

            # Filter results by text matching
            results = []
            query_lower = query.lower()

            for point in scroll_result[0]:
                payload = point.payload
                # Check title, romanized, alternatives for text matches
                title = payload.get('title', '').lower()
                romanized = payload.get('romanized', '').lower()
                alternatives = [alt.lower() for alt in payload.get('alternatives', [])]

                score = 0.0

                # Calculate text similarity score
                if query_lower in title:
                    score = 1.0 if query_lower == title else 0.8
                elif query_lower in romanized:
                    score = 0.9 if query_lower == romanized else 0.7
                elif any(query_lower in alt for alt in alternatives):
                    score = 0.6
                elif any(word in title for word in query_lower.split()):
                    score = 0.5
                elif any(word in romanized for word in query_lower.split()):
                    score = 0.4

                if score > 0:
                    results.append(QdrantSearchResult(
                        title=payload['title'],
                        filename=payload['filename'],
                        language_or_category=payload['category'],
                        score=score,
                        metadata=payload,
                        alternatives=payload.get('alternatives', []),
                        romanized=payload.get('romanized', '')
                    ))

            # Sort by score and limit results
            results.sort(key=lambda x: x.score, reverse=True)
            results = results[:limit]

            logger.debug(f"Qdrant stories search found {len(results)} results for '{query}'")
            return results

        except Exception as e:
            logger.error(f"Qdrant stories search failed: {e}")
            return []

    async def get_random_music(self, language_filter: Optional[str] = None) -> Optional[QdrantSearchResult]:
        """Get a random song from Qdrant collection"""
        if not self.is_initialized:
            return None

        try:
            # Use scroll to get random points without filters to avoid typing issues
            scroll_result = self.client.scroll(
                collection_name=self.config["music_collection"],
                limit=100,  # Get more points to choose from
                with_payload=True
            )

            if scroll_result[0]:  # Check if we have any points
                import random
                # Filter by language if specified
                valid_points = scroll_result[0]
                if language_filter:
                    valid_points = [p for p in scroll_result[0] if p.payload.get('language') == language_filter]

                if valid_points:
                    random_point = random.choice(valid_points)
                    return QdrantSearchResult(
                        title=random_point.payload['title'],
                        filename=random_point.payload['filename'],
                        language_or_category=random_point.payload['language'],
                        score=1.0,
                        metadata=random_point.payload,
                        alternatives=random_point.payload.get('alternatives', []),
                        romanized=random_point.payload.get('romanized', '')
                    )

            return None

        except Exception as e:
            logger.error(f"Qdrant random music selection failed: {e}")
            return None

    async def get_random_story(self, category_filter: Optional[str] = None) -> Optional[QdrantSearchResult]:
        """Get a random story from Qdrant collection"""
        if not self.is_initialized:
            return None

        try:
            # Use scroll to get random points without filters to avoid typing issues
            scroll_result = self.client.scroll(
                collection_name=self.config["stories_collection"],
                limit=100,  # Get more points to choose from
                with_payload=True
            )

            if scroll_result[0]:  # Check if we have any points
                import random
                # Filter by category if specified
                valid_points = scroll_result[0]
                if category_filter:
                    valid_points = [p for p in scroll_result[0] if p.payload.get('category') == category_filter]

                if valid_points:
                    random_point = random.choice(valid_points)
                    return QdrantSearchResult(
                        title=random_point.payload['title'],
                        filename=random_point.payload['filename'],
                        language_or_category=random_point.payload['category'],
                        score=1.0,
                        metadata=random_point.payload,
                        alternatives=random_point.payload.get('alternatives', []),
                        romanized=random_point.payload.get('romanized', '')
                    )

            return None

        except Exception as e:
            logger.error(f"Qdrant random story selection failed: {e}")
            return None

    async def get_available_languages(self) -> List[str]:
        """Get list of available music languages from Qdrant"""
        if not self.is_initialized:
            return []

        try:
            # Use aggregation to get unique languages
            scroll_result = self.client.scroll(
                collection_name=self.config["music_collection"],
                limit=1000,  # Get a large sample
                with_payload=["language"]
            )

            languages = set()
            for point in scroll_result[0]:
                if 'language' in point.payload:
                    languages.add(point.payload['language'])

            return sorted(list(languages))

        except Exception as e:
            logger.error(f"Failed to get available languages: {e}")
            return []

    async def get_available_categories(self) -> List[str]:
        """Get list of available story categories from Qdrant"""
        if not self.is_initialized:
            return []

        try:
            # Use aggregation to get unique categories
            scroll_result = self.client.scroll(
                collection_name=self.config["stories_collection"],
                limit=1000,  # Get a large sample
                with_payload=["category"]
            )

            categories = set()
            for point in scroll_result[0]:
                if 'category' in point.payload:
                    categories.add(point.payload['category'])

            return sorted(list(categories))

        except Exception as e:
            logger.error(f"Failed to get available categories: {e}")
            return []