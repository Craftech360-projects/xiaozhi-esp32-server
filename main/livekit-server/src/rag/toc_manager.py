"""
TOC Manager
Stores and retrieves Table of Contents from Qdrant vector database
"""

import logging
import json
from typing import Dict, List, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import (
    PointStruct,
    VectorParams,
    Distance,
    Filter,
    FieldCondition,
    MatchValue
)
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class TOCManager:
    """Manage TOC storage and retrieval in Qdrant"""

    def __init__(
        self,
        qdrant_client: QdrantClient,
        collection_name: str = "science_textbook_toc"
    ):
        self.client = qdrant_client
        self.collection_name = collection_name
        self.embedding_model = None

    def _load_embedding_model(self):
        """Lazy load embedding model"""
        if self.embedding_model is None:
            logger.info("Loading embedding model for TOC...")
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

    async def initialize_collection(self):
        """Initialize TOC collection in Qdrant"""

        self._load_embedding_model()

        # Check if collection exists
        collections = self.client.get_collections().collections
        collection_names = [c.name for c in collections]

        if self.collection_name in collection_names:
            logger.info(f"Collection {self.collection_name} already exists")
            return

        # Create collection
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=384,  # all-MiniLM-L6-v2 embedding size
                distance=Distance.COSINE
            )
        )

        # Create payload indexes
        self.client.create_payload_index(
            collection_name=self.collection_name,
            field_name="chapter",
            field_schema="integer"
        )

        self.client.create_payload_index(
            collection_name=self.collection_name,
            field_name="section_id",
            field_schema="keyword"
        )

        self.client.create_payload_index(
            collection_name=self.collection_name,
            field_name="section_type",
            field_schema="keyword"
        )

        logger.info(f"Created TOC collection: {self.collection_name}")

    async def store_toc(self, expanded_toc: Dict) -> int:
        """
        Store TOC in Qdrant

        Returns: Number of sections stored
        """

        self._load_embedding_model()

        chapter_num = expanded_toc['chapter']
        chapter_title = expanded_toc['title']

        points = []

        for section in expanded_toc['sections']:
            # Build section description for embedding
            section_desc = self._build_section_description(section)

            # Generate embedding
            embedding = self.embedding_model.encode(
                section_desc,
                convert_to_numpy=True
            ).tolist()

            # Create point
            point = PointStruct(
                id=self._generate_point_id(chapter_num, section['id']),
                vector=embedding,
                payload={
                    'chapter': chapter_num,
                    'chapter_title': chapter_title,
                    'section_id': section['id'],
                    'section_title': section['title'],
                    'section_type': section['type'],
                    'content_priority': section['content_priority'],

                    # Learning metadata
                    'expanded_description': section.get('expanded_description', ''),
                    'key_concepts': section.get('key_concepts', []),
                    'learning_objectives': section.get('learning_objectives', []),
                    'difficulty_level': section.get('difficulty_level', 'beginner'),
                    'cognitive_level': section.get('cognitive_level', 'understand'),
                    'related_activities': section.get('related_activities', []),

                    # For reconstruction
                    'start_text': section.get('start_text', ''),
                    'page': section.get('page', 1)
                }
            )

            points.append(point)

        # Upload to Qdrant
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )

        logger.info(
            f"Stored TOC for Chapter {chapter_num}: {len(points)} sections"
        )

        return len(points)

    async def get_toc_by_chapter(self, chapter_num: int) -> Optional[Dict]:
        """Retrieve TOC for a specific chapter"""

        results = self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter=Filter(
                must=[
                    FieldCondition(
                        key="chapter",
                        match=MatchValue(value=chapter_num)
                    )
                ]
            ),
            limit=100
        )

        if not results[0]:
            logger.warning(f"No TOC found for chapter {chapter_num}")
            return None

        # Reconstruct TOC from points
        sections = []
        chapter_title = None

        for point in results[0]:
            payload = point.payload

            if chapter_title is None:
                chapter_title = payload['chapter_title']

            section = {
                'id': payload['section_id'],
                'title': payload['section_title'],
                'page': payload['page'],
                'type': payload['section_type'],
                'content_priority': payload['content_priority'],
                'start_text': payload['start_text'],

                # Learning metadata
                'expanded_description': payload['expanded_description'],
                'key_concepts': payload['key_concepts'],
                'learning_objectives': payload['learning_objectives'],
                'difficulty_level': payload['difficulty_level'],
                'cognitive_level': payload['cognitive_level'],
                'related_activities': payload['related_activities']
            }

            sections.append(section)

        # Sort sections by ID
        sections.sort(key=lambda s: s['id'])

        toc = {
            'chapter': chapter_num,
            'title': chapter_title,
            'sections': sections
        }

        logger.info(f"Retrieved TOC for Chapter {chapter_num}: {len(sections)} sections")

        return toc

    async def search_toc_sections(
        self,
        query: str,
        chapter: Optional[int] = None,
        section_type: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict]:
        """
        Search TOC sections by semantic similarity

        Args:
            query: Search query
            chapter: Optional chapter filter
            section_type: Optional section type filter (teaching_text, activity, etc.)
            limit: Max results

        Returns: List of matching TOC sections
        """

        self._load_embedding_model()

        # Generate query embedding
        query_embedding = self.embedding_model.encode(
            query,
            convert_to_numpy=True
        ).tolist()

        # Build filter
        filter_conditions = []

        if chapter is not None:
            filter_conditions.append(
                FieldCondition(
                    key="chapter",
                    match=MatchValue(value=chapter)
                )
            )

        if section_type is not None:
            filter_conditions.append(
                FieldCondition(
                    key="section_type",
                    match=MatchValue(value=section_type)
                )
            )

        search_filter = Filter(must=filter_conditions) if filter_conditions else None

        # Search
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            query_filter=search_filter,
            limit=limit
        )

        # Extract sections
        sections = []
        for result in results:
            payload = result.payload
            section = {
                'id': payload['section_id'],
                'title': payload['section_title'],
                'chapter': payload['chapter'],
                'chapter_title': payload['chapter_title'],
                'type': payload['section_type'],
                'content_priority': payload['content_priority'],
                'key_concepts': payload['key_concepts'],
                'learning_objectives': payload['learning_objectives'],
                'similarity_score': result.score
            }
            sections.append(section)

        return sections

    def _build_section_description(self, section: Dict) -> str:
        """Build section description for embedding"""

        parts = [
            section['title'],
            section.get('expanded_description', ''),
            ' '.join(section.get('key_concepts', [])),
            ' '.join(section.get('learning_objectives', []))
        ]

        description = ' '.join(p for p in parts if p)
        return description

    def _generate_point_id(self, chapter: int, section_id: str) -> int:
        """
        Generate unique point ID from chapter and section ID

        Example: Chapter 1, Section 1.2 -> 1002
        Example: Chapter 1, Section activity_1.1 -> 1901
        """

        # Extract numeric part from section_id
        if section_id.startswith('activity_'):
            # activity_1.1 -> 1.1
            section_num = section_id.replace('activity_', '')
            # Use 900 offset for activities
            base = 900
        else:
            section_num = section_id
            base = 0

        # Parse section number (1.1 -> 1, 1)
        parts = section_num.split('.')
        major = int(parts[0]) if len(parts) > 0 else 0
        minor = int(parts[1]) if len(parts) > 1 else 0

        # Generate ID: chapter * 1000 + base + major * 10 + minor
        point_id = chapter * 1000 + base + major * 10 + minor

        return point_id
