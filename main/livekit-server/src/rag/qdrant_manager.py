"""
Qdrant Collection Manager for Educational Content
Manages separate collections for each grade-subject combination
"""

import logging
import os
from typing import Dict, List, Optional, Any
from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams,
    Distance,
    CollectionInfo,
    PointStruct,
    NamedVector,
    CreateCollection,
    VectorsConfig,
    PayloadSchemaType
)

logger = logging.getLogger(__name__)


class QdrantEducationManager:
    """Manages Qdrant collections for educational content with grade-subject organization"""

    # Class-level flag to track if indexes have been created globally
    _indexes_created = False

    @classmethod
    def check_indexes_created(cls) -> bool:
        """Check if indexes have been created using file flag"""
        return os.path.exists("education_indexes_created.flag")

    @classmethod
    def mark_indexes_created(cls):
        """Mark indexes as created using file flag"""
        cls._indexes_created = True
        with open("education_indexes_created.flag", "w") as f:
            f.write("indexes_created")

    def __init__(self):
        self.client = QdrantClient(
            url=os.getenv("QDRANT_URL", ""),
            api_key=os.getenv("QDRANT_API_KEY", "")
        )

        # Define subject mappings for each grade
        self.grade_subjects = {
            6: ["mathematics", "science", "english", "social_studies"],
            7: ["mathematics", "science", "english", "social_studies", "computer_science"],
            8: ["mathematics", "physics", "chemistry", "biology", "english", "social_studies", "computer_science"],
            9: ["mathematics", "physics", "chemistry", "biology", "english", "social_studies", "computer_science"],
            10: ["mathematics", "physics", "chemistry", "biology", "english", "social_studies", "computer_science"],
            11: ["mathematics", "physics", "chemistry", "biology", "english", "social_studies", "computer_science", "economics"],
            12: ["mathematics", "physics", "chemistry", "biology", "english", "social_studies", "computer_science", "economics"]
        }

        # Vector configurations for different content types
        self.vector_config = {
            "text": VectorParams(size=384, distance=Distance.COSINE),  # Sentence Transformers all-MiniLM-L6-v2
            "visual": VectorParams(size=512, distance=Distance.COSINE),  # CLIP ViT-B/32
            "formula": VectorParams(size=768, distance=Distance.COSINE)  # all-mpnet-base-v2
        }

        self.is_initialized = False

    def get_collection_name(self, grade: int, subject: str) -> str:
        """Generate collection name for grade-subject combination"""
        subject_clean = subject.lower().replace(' ', '_').replace('-', '_')
        return f"grade_{grade}_{subject_clean}"

    def get_all_collection_names(self) -> List[str]:
        """Get all possible collection names"""
        collections = []
        for grade, subjects in self.grade_subjects.items():
            for subject in subjects:
                collections.append(self.get_collection_name(grade, subject))
        return collections

    async def initialize_all_collections(self) -> bool:
        """Initialize all grade-subject collections"""
        try:
            # Check existing collections
            existing_collections = await self.get_existing_collections()
            logger.info(f"Found {len(existing_collections)} existing collections")

            created_count = 0
            for grade, subjects in self.grade_subjects.items():
                for subject in subjects:
                    collection_name = self.get_collection_name(grade, subject)

                    if collection_name not in existing_collections:
                        success = await self.create_collection(collection_name, subject)
                        if success:
                            created_count += 1
                            logger.info(f"Created collection: {collection_name}")
                        else:
                            logger.error(f"Failed to create collection: {collection_name}")
                    else:
                        logger.info(f"Collection already exists: {collection_name}")

            logger.info(f"Collection initialization complete. Created {created_count} new collections.")

            # Create indexes only for grade_10_science if not yet done globally
            if not QdrantEducationManager.check_indexes_created():
                await self.create_indexes_for_grade10_science()
                QdrantEducationManager.mark_indexes_created()

            self.is_initialized = True
            return True

        except Exception as e:
            logger.error(f"Failed to initialize collections: {e}")
            return False

    async def initialize_grade10_science_only(self) -> bool:
        """Initialize only the grade_10_science collection"""
        try:
            logger.info("Initializing grade_10_science collection only...")

            # Check if grade_10_science collection exists
            existing_collections = await self.get_existing_collections()
            collection_name = "grade_10_science"

            if collection_name not in existing_collections:
                success = await self.create_collection(collection_name, "science")
                if success:
                    logger.info(f"✅ Created collection: {collection_name}")
                else:
                    logger.error(f"❌ Failed to create collection: {collection_name}")
                    return False
            else:
                logger.info(f"Collection {collection_name} already exists")

            # Create indexes only for grade_10_science if not yet done globally
            if not QdrantEducationManager.check_indexes_created():
                await self.create_indexes_for_grade10_science()
                QdrantEducationManager.mark_indexes_created()

            self.is_initialized = True
            logger.info("✅ Grade 10 science collection initialization complete")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize grade_10_science collection: {e}")
            return False

    async def initialize_grade6_and_grade10_science(self) -> bool:
        """Initialize both grade_06_science and grade_10_science collections"""
        try:
            logger.info("Initializing grade_06_science and grade_10_science collections...")

            # Check existing collections
            existing_collections = await self.get_existing_collections()
            collections_to_check = ["grade_06_science", "grade_10_science"]

            success_count = 0
            for collection_name in collections_to_check:
                if collection_name not in existing_collections:
                    success = await self.create_collection(collection_name, "science")
                    if success:
                        logger.info(f"✅ Created collection: {collection_name}")
                        success_count += 1
                    else:
                        logger.error(f"❌ Failed to create collection: {collection_name}")
                else:
                    logger.info(f"Collection {collection_name} already exists")
                    success_count += 1

            # Create indexes if not yet done globally
            if not QdrantEducationManager.check_indexes_created():
                await self.create_indexes_for_science_collections()
                QdrantEducationManager.mark_indexes_created()

            self.is_initialized = True
            logger.info(f"✅ Science collections initialization complete ({success_count}/2 collections ready)")
            return success_count == 2

        except Exception as e:
            logger.error(f"Failed to initialize science collections: {e}")
            return False

    async def get_existing_collections(self) -> List[str]:
        """Get list of existing collection names"""
        try:
            collections = self.client.get_collections()
            return [col.name for col in collections.collections]
        except Exception as e:
            logger.error(f"Failed to get existing collections: {e}")
            return []

    async def create_collection(self, collection_name: str, subject: str) -> bool:
        """Create a new collection with subject-specific configuration"""
        try:
            # Use text vector config as primary (simplified for now)
            vectors_config = self.vector_config["text"]

            # Create collection
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=vectors_config
            )

            logger.info(f"Successfully created collection: {collection_name}")

            # Create payload indexes for filtering
            await self.create_payload_indexes(collection_name, subject)

            return True

        except Exception as e:
            logger.error(f"Failed to create collection {collection_name}: {e}")
            return False

    async def create_payload_indexes(self, collection_name: str, subject: str) -> bool:
        """Create payload indexes for efficient filtering"""
        try:
            # Essential indexes for search functionality
            indexes_to_create = [
                ("content_type", PayloadSchemaType.KEYWORD),
                ("topic", PayloadSchemaType.KEYWORD),
                ("difficulty_level", PayloadSchemaType.KEYWORD),
                ("grade", PayloadSchemaType.INTEGER),
                ("subject", PayloadSchemaType.KEYWORD),
                ("page_number", PayloadSchemaType.INTEGER),
                ("chapter_number", PayloadSchemaType.INTEGER),  # Added for chapter-based filtering
                ("chapter", PayloadSchemaType.KEYWORD),  # Added for chapter title search
                ("textbook_name", PayloadSchemaType.KEYWORD),
                ("cognitive_level", PayloadSchemaType.KEYWORD),
                ("keywords", PayloadSchemaType.KEYWORD),
                ("concepts", PayloadSchemaType.KEYWORD),

                # TOC-guided retrieval indexes
                ("toc_section_id", PayloadSchemaType.KEYWORD),  # Section ID from TOC (1.1, activity_1.1, etc.)
                ("section_type", PayloadSchemaType.KEYWORD),  # teaching_text, activity, example, practice
                ("content_priority", PayloadSchemaType.KEYWORD),  # high, medium, low
                ("content_weight", PayloadSchemaType.FLOAT),  # Content weighting score (0.7-1.0)
                ("is_activity", PayloadSchemaType.BOOL)  # Quick filter for activities
            ]

            for field_name, schema_type in indexes_to_create:
                try:
                    self.client.create_payload_index(
                        collection_name=collection_name,
                        field_name=field_name,
                        field_schema=schema_type
                    )
                    logger.debug(f"Created index for {field_name} in {collection_name}")
                except Exception as e:
                    # Silently ignore if index already exists (expected for existing collections)
                    if "already exists" in str(e).lower() or "index exists" in str(e).lower():
                        logger.debug(f"Index {field_name} already exists in {collection_name}")
                    else:
                        logger.warning(f"Failed to create index for {field_name}: {e}")

            return True

        except Exception as e:
            logger.error(f"Failed to create payload indexes for {collection_name}: {e}")
            return False

    async def create_indexes_for_grade10_science(self) -> bool:
        """Create payload indexes only for grade_10_science collection"""
        try:
            logger.info("Creating payload indexes for grade_10_science collection...")

            collection_name = "grade_10_science"

            # Check if collection exists
            existing_collections = await self.get_existing_collections()
            if collection_name in existing_collections:
                await self.create_payload_indexes(collection_name, "science")
                logger.info("✅ Finished creating payload indexes for grade_10_science")
            else:
                logger.warning(f"Collection {collection_name} does not exist, skipping indexing")

            return True

        except Exception as e:
            logger.error(f"Failed to create indexes for all collections: {e}")
            return False

    async def create_indexes_for_science_collections(self) -> bool:
        """Create payload indexes for both grade_06_science and grade_10_science collections"""
        try:
            logger.info("Creating payload indexes for science collections...")

            collections_to_index = ["grade_06_science", "grade_10_science"]
            existing_collections = await self.get_existing_collections()

            for collection_name in collections_to_index:
                if collection_name in existing_collections:
                    await self.create_payload_indexes(collection_name, "science")
                    logger.info(f"✅ Finished creating payload indexes for {collection_name}")
                else:
                    logger.warning(f"Collection {collection_name} does not exist, skipping indexing")

            return True

        except Exception as e:
            logger.error(f"Failed to create indexes for science collections: {e}")
            return False

    def get_subject_specific_schema(self, subject: str) -> Dict[str, Any]:
        """Get payload schema based on subject type"""

        # Base schema for all subjects
        base_schema = {
            # Core Content
            "content": {"type": "text"},
            "content_type": {"type": "keyword"},  # text|table|formula|diagram|example|exercise

            # Textbook Reference
            "textbook_name": {"type": "keyword"},
            "textbook_author": {"type": "keyword"},
            "isbn": {"type": "keyword"},
            "page_number": {"type": "integer"},
            "page_section": {"type": "keyword"},  # header|body|footer|sidebar

            # Chapter Organization
            "unit": {"type": "keyword"},
            "chapter": {"type": "keyword"},
            "chapter_number": {"type": "integer"},
            "section": {"type": "keyword"},
            "section_number": {"type": "float"},  # 1.1, 1.2, etc.
            "subsection": {"type": "keyword"},

            # Content Classification
            "topic": {"type": "keyword", "is_array": True},
            "subtopic": {"type": "keyword", "is_array": True},
            "keywords": {"type": "keyword", "is_array": True},
            "concepts": {"type": "keyword", "is_array": True},

            # Educational Metadata
            "difficulty_level": {"type": "keyword"},  # beginner|intermediate|advanced|expert
            "cognitive_level": {"type": "keyword"},  # Bloom's taxonomy
            "learning_objectives": {"type": "keyword", "is_array": True},
            "prerequisites": {"type": "keyword", "is_array": True},
            "estimated_time": {"type": "integer"},  # in minutes

            # Cross-References
            "related_chunks": {"type": "keyword", "is_array": True},
            "figure_refs": {"type": "keyword", "is_array": True},
            "table_refs": {"type": "keyword", "is_array": True},
            "equation_refs": {"type": "keyword", "is_array": True},
            "example_refs": {"type": "keyword", "is_array": True},

            # Context Preservation
            "preceding_content": {"type": "text"},
            "following_content": {"type": "text"},
            "full_page_text": {"type": "text"},

            # Quality Metrics
            "extraction_confidence": {"type": "float"},
            "ocr_confidence": {"type": "float"},
            "verified": {"type": "bool"},
            "last_updated": {"type": "datetime"}
        }

        # Subject-specific additions
        if subject == "mathematics":
            base_schema.update({
                "formula_latex": {"type": "text"},
                "formula_mathml": {"type": "text"},
                "formula_type": {"type": "keyword"},  # algebraic|geometric|calculus|statistics
                "variables": {"type": "keyword", "is_array": True},
                "solution_steps": {"type": "text"},
                "proof_type": {"type": "keyword"},
                "theorem_name": {"type": "keyword"},
                "problem_category": {"type": "keyword"}  # word_problem|proof|computation|graphing
            })

        elif subject in ["physics", "chemistry"]:
            base_schema.update({
                "formula_latex": {"type": "text"},
                "units": {"type": "keyword", "is_array": True},
                "constants": {"type": "text"},
                "experiment_name": {"type": "keyword"},
                "lab_requirements": {"type": "keyword", "is_array": True},
                "safety_notes": {"type": "keyword", "is_array": True},
                "practical_applications": {"type": "keyword", "is_array": True},
                "numerical_values": {"type": "text"}
            })

        elif subject == "biology":
            base_schema.update({
                "biological_system": {"type": "keyword"},
                "organism_type": {"type": "keyword"},
                "process_name": {"type": "keyword"},
                "diagram_labels": {"type": "text"},
                "terminology": {"type": "text"},
                "classification": {"type": "keyword", "is_array": True}
            })

        elif subject == "computer_science":
            base_schema.update({
                "code_language": {"type": "keyword"},
                "code_snippet": {"type": "text"},
                "algorithm_name": {"type": "keyword"},
                "complexity": {"type": "keyword"},  # O(n), O(log n), etc.
                "data_structure": {"type": "keyword"},
                "programming_concepts": {"type": "keyword", "is_array": True},
                "syntax_highlighted": {"type": "text"}
            })

        elif subject == "english":
            base_schema.update({
                "literary_device": {"type": "keyword", "is_array": True},
                "grammar_topic": {"type": "keyword"},
                "writing_style": {"type": "keyword"},
                "vocabulary_level": {"type": "keyword"},
                "text_type": {"type": "keyword"},  # narrative|expository|persuasive
                "author": {"type": "keyword"},
                "literary_period": {"type": "keyword"}
            })

        return base_schema

    async def upsert_content(
        self,
        collection_name: str,
        content_chunks: List[Dict[str, Any]]
    ) -> bool:
        """Insert content chunks into specified collection"""
        try:
            points = []

            for chunk in content_chunks:
                # Use single vector (text embedding) for simplicity
                vector = chunk.get("text_embedding")
                if not vector:
                    logger.warning(f"No text_embedding found in chunk {chunk.get('id', 'unknown')}")
                    continue

                # Create point with single vector
                point = PointStruct(
                    id=chunk.get("id", len(points)),
                    vector=vector,
                    payload=chunk.get("payload", {})
                )
                points.append(point)

            # Batch upsert
            batch_size = 100
            for i in range(0, len(points), batch_size):
                batch = points[i:i + batch_size]
                operation_info = self.client.upsert(
                    collection_name=collection_name,
                    points=batch,
                    wait=True
                )
                logger.info(f"Upserted batch {i//batch_size + 1} to {collection_name}")

            logger.info(f"Successfully upserted {len(points)} points to {collection_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to upsert content to {collection_name}: {e}")
            return False

    async def get_collection_info(self, collection_name: str) -> Optional[CollectionInfo]:
        """Get information about a specific collection"""
        try:
            return self.client.get_collection(collection_name)
        except Exception as e:
            logger.error(f"Failed to get collection info for {collection_name}: {e}")
            return None

    async def get_collections_for_grade(self, grade: int) -> List[str]:
        """Get all collection names for a specific grade"""
        collections = []
        if grade in self.grade_subjects:
            for subject in self.grade_subjects[grade]:
                collections.append(self.get_collection_name(grade, subject))
        return collections

    async def get_collections_for_subject(self, subject: str) -> List[str]:
        """Get all collection names for a specific subject across grades"""
        collections = []
        for grade, subjects in self.grade_subjects.items():
            if subject in subjects:
                collections.append(self.get_collection_name(grade, subject))
        return collections

    async def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection"""
        try:
            self.client.delete_collection(collection_name)
            logger.info(f"Successfully deleted collection: {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete collection {collection_name}: {e}")
            return False

    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics for all educational collections"""
        stats = {
            "total_collections": 0,
            "total_points": 0,
            "collections_by_grade": {},
            "collections_by_subject": {}
        }

        try:
            existing_collections = await self.get_existing_collections()
            educational_collections = [
                col for col in existing_collections
                if col.startswith("grade_")
            ]

            stats["total_collections"] = len(educational_collections)

            for collection_name in educational_collections:
                info = await self.get_collection_info(collection_name)
                if info:
                    stats["total_points"] += info.points_count

                    # Parse grade and subject from collection name
                    parts = collection_name.split("_")
                    if len(parts) >= 3:
                        grade = parts[1]
                        subject = "_".join(parts[2:])

                        if grade not in stats["collections_by_grade"]:
                            stats["collections_by_grade"][grade] = 0
                        stats["collections_by_grade"][grade] += info.points_count

                        if subject not in stats["collections_by_subject"]:
                            stats["collections_by_subject"][subject] = 0
                        stats["collections_by_subject"][subject] += info.points_count

            return stats

        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return stats

    async def create_visual_collection(self, base_collection_name: str) -> bool:
        """
        Create visual content collection for figures/tables

        Args:
            base_collection_name: Base collection name (e.g., "grade_06_science")

        Returns:
            True if successful
        """
        try:
            visual_collection_name = f"{base_collection_name}_visual"

            # Check if visual collection already exists
            existing_collections = await self.get_existing_collections()
            if visual_collection_name in existing_collections:
                logger.info(f"Visual collection {visual_collection_name} already exists")
                return True

            # Create collection with CLIP vector size (512-dim)
            vectors_config = self.vector_config["visual"]

            self.client.create_collection(
                collection_name=visual_collection_name,
                vectors_config=vectors_config
            )

            logger.info(f"Successfully created visual collection: {visual_collection_name}")

            # Create payload indexes for visual content
            await self.create_visual_payload_indexes(visual_collection_name)

            return True

        except Exception as e:
            logger.error(f"Failed to create visual collection: {e}")
            return False

    async def create_visual_payload_indexes(self, collection_name: str) -> bool:
        """Create payload indexes for visual content collections"""
        try:
            # Visual-specific indexes
            indexes_to_create = [
                ("type", PayloadSchemaType.KEYWORD),  # figure or table
                ("figure_id", PayloadSchemaType.KEYWORD),  # fig_1_1, fig_1_2
                ("table_id", PayloadSchemaType.KEYWORD),  # table_1_1, table_1_2
                ("page", PayloadSchemaType.INTEGER),
                ("caption", PayloadSchemaType.TEXT),
                ("nearby_text", PayloadSchemaType.TEXT),
                ("chapter_number", PayloadSchemaType.INTEGER),
                ("section_id", PayloadSchemaType.KEYWORD),
                ("has_image_data", PayloadSchemaType.BOOL),
            ]

            for field_name, schema_type in indexes_to_create:
                try:
                    self.client.create_payload_index(
                        collection_name=collection_name,
                        field_name=field_name,
                        field_schema=schema_type
                    )
                    logger.debug(f"Created visual index for {field_name} in {collection_name}")
                except Exception as e:
                    if "already exists" in str(e).lower() or "index exists" in str(e).lower():
                        logger.debug(f"Index {field_name} already exists in {collection_name}")
                    else:
                        logger.warning(f"Failed to create visual index for {field_name}: {e}")

            return True

        except Exception as e:
            logger.error(f"Failed to create visual payload indexes: {e}")
            return False

    async def upsert_visual_content(
        self,
        collection_name: str,
        visual_chunks: List[Dict[str, Any]]
    ) -> bool:
        """
        Insert visual content (figures/tables) into visual collection

        Args:
            collection_name: Visual collection name (e.g., "grade_06_science_visual")
            visual_chunks: List of processed figures/tables with embeddings

        Returns:
            True if successful
        """
        try:
            points = []

            for chunk in visual_chunks:
                embedding = chunk.get("embedding")
                if not embedding:
                    logger.warning(f"No embedding found in visual chunk {chunk.get('figure_id') or chunk.get('table_id')}")
                    continue

                # Prepare payload (remove embedding from payload)
                payload = {k: v for k, v in chunk.items() if k not in ['embedding', 'image_data']}

                # Add has_image_data flag
                payload['has_image_data'] = chunk.get('image_data') is not None

                # Generate ID if not present
                chunk_id = chunk.get('id') or chunk.get('figure_id') or chunk.get('table_id') or len(points)

                point = PointStruct(
                    id=chunk_id if isinstance(chunk_id, (int, str)) else str(chunk_id),
                    vector=embedding,
                    payload=payload
                )
                points.append(point)

            if not points:
                logger.warning("No valid visual content points to upsert")
                return True

            # Batch upsert
            batch_size = 50  # Smaller batch for visual content
            for i in range(0, len(points), batch_size):
                batch = points[i:i + batch_size]
                operation_info = self.client.upsert(
                    collection_name=collection_name,
                    points=batch,
                    wait=True
                )
                logger.info(f"Upserted visual batch {i//batch_size + 1} to {collection_name}")

            logger.info(f"Successfully upserted {len(points)} visual points to {collection_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to upsert visual content to {collection_name}: {e}")
            return False