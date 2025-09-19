"""
Textbook Ingestion Pipeline
Orchestrates the complete process of ingesting textbooks into Qdrant collections
"""

import logging
import os
from typing import Dict, List, Optional, Any
from pathlib import Path
import asyncio

from ..rag.qdrant_manager import QdrantEducationManager
from ..rag.document_processor import TextbookProcessor, ContentChunk
from ..rag.embeddings import EmbeddingManager

logger = logging.getLogger(__name__)


class TextbookIngestionPipeline:
    """Complete pipeline for processing textbooks and storing them in Qdrant"""

    def __init__(self):
        self.qdrant_manager = QdrantEducationManager()
        self.document_processor = TextbookProcessor()
        self.embedding_manager = EmbeddingManager()

        self.is_initialized = False

    async def initialize(self) -> bool:
        """Initialize all components of the pipeline"""
        try:
            # Skip if already initialized
            if self.is_initialized:
                logger.info("Textbook ingestion pipeline already initialized, skipping...")
                return True

            logger.info("Initializing textbook ingestion pipeline...")

            # Initialize Qdrant collections (grade 10 science only)
            qdrant_success = await self.qdrant_manager.initialize_grade10_science_only()
            if not qdrant_success:
                logger.error("Failed to initialize Qdrant collections")
                return False

            # Initialize embedding manager
            embedding_success = await self.embedding_manager.initialize()
            if not embedding_success:
                logger.error("Failed to initialize embedding manager")
                return False

            self.is_initialized = True
            logger.info("Textbook ingestion pipeline initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize ingestion pipeline: {e}")
            return False

    async def ingest_textbook(
        self,
        pdf_path: str,
        grade: int,
        subject: str,
        textbook_name: str,
        author: str = "",
        isbn: str = "",
        overwrite: bool = False
    ) -> bool:
        """Ingest a single textbook into the appropriate collection"""

        if not self.is_initialized:
            logger.error("Pipeline not initialized. Call initialize() first.")
            return False

        try:
            logger.info(f"Starting ingestion of textbook: {textbook_name}")
            logger.info(f"Grade: {grade}, Subject: {subject}")

            # Validate inputs
            if not Path(pdf_path).exists():
                logger.error(f"PDF file not found: {pdf_path}")
                return False

            if grade < 6 or grade > 12:
                logger.error(f"Invalid grade: {grade}. Must be between 6 and 12.")
                return False

            # Get target collection name
            collection_name = self.qdrant_manager.get_collection_name(grade, subject)

            # Check if textbook already exists
            if not overwrite and await self._textbook_exists(collection_name, textbook_name, isbn):
                logger.warning(f"Textbook {textbook_name} already exists in {collection_name}")
                return False

            # Process the textbook
            logger.info("Processing textbook content...")
            chunks = await self.document_processor.process_textbook(
                pdf_path=pdf_path,
                grade=grade,
                subject=subject,
                textbook_name=textbook_name,
                author=author,
                isbn=isbn
            )

            if not chunks:
                logger.error("No content chunks extracted from textbook")
                return False

            logger.info(f"Extracted {len(chunks)} content chunks")

            # Generate embeddings for all chunks
            logger.info("Generating embeddings...")
            processed_chunks = await self._process_chunks_with_embeddings(chunks)

            if not processed_chunks:
                logger.error("Failed to generate embeddings for chunks")
                return False

            # Store in Qdrant
            logger.info(f"Storing content in collection: {collection_name}")
            success = await self.qdrant_manager.upsert_content(collection_name, processed_chunks)

            if success:
                logger.info(f"Successfully ingested textbook: {textbook_name}")
                await self._log_ingestion_stats(collection_name, len(processed_chunks))
                return True
            else:
                logger.error(f"Failed to store content in collection: {collection_name}")
                return False

        except Exception as e:
            logger.error(f"Failed to ingest textbook {textbook_name}: {e}")
            return False

    async def ingest_multiple_textbooks(
        self,
        textbook_configs: List[Dict[str, Any]],
        max_concurrent: int = 2
    ) -> Dict[str, bool]:
        """Ingest multiple textbooks concurrently"""

        if not self.is_initialized:
            logger.error("Pipeline not initialized. Call initialize() first.")
            return {}

        results = {}
        semaphore = asyncio.Semaphore(max_concurrent)

        async def ingest_single(config: Dict[str, Any]) -> None:
            async with semaphore:
                textbook_name = config.get("textbook_name", "Unknown")
                try:
                    success = await self.ingest_textbook(**config)
                    results[textbook_name] = success
                except Exception as e:
                    logger.error(f"Failed to ingest {textbook_name}: {e}")
                    results[textbook_name] = False

        # Create tasks for all textbooks
        tasks = [ingest_single(config) for config in textbook_configs]

        # Wait for all tasks to complete
        await asyncio.gather(*tasks, return_exceptions=True)

        # Log summary
        successful = sum(1 for success in results.values() if success)
        total = len(results)
        logger.info(f"Ingestion complete: {successful}/{total} textbooks successful")

        return results

    async def _textbook_exists(self, collection_name: str, textbook_name: str, isbn: str) -> bool:
        """Check if textbook already exists in collection"""
        try:
            # Simple check by searching for textbook name
            from qdrant_client.models import Filter, FieldCondition, MatchValue

            search_filter = Filter(
                must=[
                    FieldCondition(
                        key="textbook_name",
                        match=MatchValue(value=textbook_name)
                    )
                ]
            )

            results = self.qdrant_manager.client.scroll(
                collection_name=collection_name,
                scroll_filter=search_filter,
                limit=1
            )

            return len(results[0]) > 0

        except Exception as e:
            logger.warning(f"Failed to check if textbook exists: {e}")
            return False

    async def _process_chunks_with_embeddings(self, chunks: List[ContentChunk]) -> List[Dict[str, Any]]:
        """Process chunks and generate embeddings"""
        processed_chunks = []

        try:
            # Extract text content for batch embedding generation
            chunk_texts = [chunk.content for chunk in chunks]

            # Generate embeddings in batches
            logger.info("Generating text embeddings...")
            text_embeddings = await self.embedding_manager.batch_text_embeddings(chunk_texts)

            # Process each chunk
            for i, (chunk, text_embedding) in enumerate(zip(chunks, text_embeddings)):
                if text_embedding is None:
                    logger.warning(f"Failed to generate embedding for chunk {i}")
                    continue

                # Prepare chunk data for Qdrant
                chunk_data = {
                    "id": chunk.id,
                    "text_embedding": text_embedding,
                    "payload": {
                        # Core content
                        "content": chunk.content,
                        "content_type": chunk.content_type,

                        # Location metadata
                        "page_number": chunk.page_number,
                        "section_title": chunk.section_title,
                        "section_level": chunk.section_level,

                        # Textbook metadata
                        **chunk.metadata
                    }
                }

                # Add additional embeddings if available
                if chunk.metadata and chunk.metadata.get("formula_latex"):
                    formula_embedding = await self.embedding_manager.get_formula_embedding(
                        chunk.metadata["formula_latex"]
                    )
                    if formula_embedding:
                        chunk_data["formula_embedding"] = formula_embedding

                # Add visual embedding if image data is available
                if chunk.metadata and chunk.metadata.get("image_data"):
                    visual_embedding = await self.embedding_manager.get_visual_embedding(
                        chunk.metadata["image_data"]
                    )
                    if visual_embedding:
                        chunk_data["visual_embedding"] = visual_embedding

                processed_chunks.append(chunk_data)

            logger.info(f"Successfully processed {len(processed_chunks)} chunks with embeddings")
            return processed_chunks

        except Exception as e:
            logger.error(f"Failed to process chunks with embeddings: {e}")
            return []

    async def _log_ingestion_stats(self, collection_name: str, chunks_added: int) -> None:
        """Log ingestion statistics"""
        try:
            collection_info = await self.qdrant_manager.get_collection_info(collection_name)
            if collection_info:
                logger.info(f"Collection {collection_name} now has {collection_info.points_count} total points")
                logger.info(f"Added {chunks_added} new points")
        except Exception as e:
            logger.warning(f"Failed to log ingestion stats: {e}")

    async def update_textbook(
        self,
        pdf_path: str,
        grade: int,
        subject: str,
        textbook_name: str,
        author: str = "",
        isbn: str = ""
    ) -> bool:
        """Update an existing textbook (delete old content and re-ingest)"""

        try:
            logger.info(f"Updating textbook: {textbook_name}")

            # Delete existing content
            success = await self.delete_textbook(grade, subject, textbook_name, isbn)
            if not success:
                logger.warning("Failed to delete existing textbook content, proceeding with ingestion")

            # Re-ingest with new content
            return await self.ingest_textbook(
                pdf_path=pdf_path,
                grade=grade,
                subject=subject,
                textbook_name=textbook_name,
                author=author,
                isbn=isbn,
                overwrite=True
            )

        except Exception as e:
            logger.error(f"Failed to update textbook {textbook_name}: {e}")
            return False

    async def delete_textbook(
        self,
        grade: int,
        subject: str,
        textbook_name: str,
        isbn: str = ""
    ) -> bool:
        """Delete a textbook from the collection"""

        try:
            collection_name = self.qdrant_manager.get_collection_name(grade, subject)

            from qdrant_client.models import Filter, FieldCondition, MatchValue

            # Build filter to identify textbook content
            filter_conditions = [
                FieldCondition(
                    key="textbook_name",
                    match=MatchValue(value=textbook_name)
                )
            ]

            if isbn:
                filter_conditions.append(
                    FieldCondition(
                        key="isbn",
                        match=MatchValue(value=isbn)
                    )
                )

            delete_filter = Filter(must=filter_conditions)

            # Get points to delete
            points_to_delete = self.qdrant_manager.client.scroll(
                collection_name=collection_name,
                scroll_filter=delete_filter,
                limit=10000,  # Large limit to get all points
                with_payload=False
            )

            if points_to_delete[0]:
                point_ids = [point.id for point in points_to_delete[0]]

                # Delete points
                self.qdrant_manager.client.delete(
                    collection_name=collection_name,
                    points_selector=point_ids
                )

                logger.info(f"Deleted {len(point_ids)} points for textbook: {textbook_name}")
                return True
            else:
                logger.warning(f"No points found for textbook: {textbook_name}")
                return True

        except Exception as e:
            logger.error(f"Failed to delete textbook {textbook_name}: {e}")
            return False

    async def get_ingestion_status(self) -> Dict[str, Any]:
        """Get status of all collections and ingested content"""

        try:
            stats = await self.qdrant_manager.get_collection_stats()

            # Add embedding manager stats
            embedding_stats = self.embedding_manager.get_cache_stats()

            return {
                "collections": stats,
                "embeddings_cache": embedding_stats,
                "pipeline_initialized": self.is_initialized
            }

        except Exception as e:
            logger.error(f"Failed to get ingestion status: {e}")
            return {"error": str(e)}

    async def validate_ingested_content(self, collection_name: str, sample_size: int = 10) -> Dict[str, Any]:
        """Validate ingested content quality"""

        try:
            # Get sample points
            sample_points = self.qdrant_manager.client.scroll(
                collection_name=collection_name,
                limit=sample_size,
                with_payload=True
            )

            validation_results = {
                "total_sampled": len(sample_points[0]),
                "valid_content": 0,
                "has_embeddings": 0,
                "has_metadata": 0,
                "issues": []
            }

            for point in sample_points[0]:
                # Check if content exists
                if point.payload.get("content"):
                    validation_results["valid_content"] += 1
                else:
                    validation_results["issues"].append(f"Point {point.id} has no content")

                # Check if embeddings exist (point has vector)
                if hasattr(point, 'vector') and point.vector:
                    validation_results["has_embeddings"] += 1
                else:
                    validation_results["issues"].append(f"Point {point.id} has no embeddings")

                # Check if required metadata exists
                required_fields = ["textbook_name", "grade", "subject", "page_number"]
                if all(field in point.payload for field in required_fields):
                    validation_results["has_metadata"] += 1
                else:
                    missing_fields = [field for field in required_fields if field not in point.payload]
                    validation_results["issues"].append(f"Point {point.id} missing metadata: {missing_fields}")

            return validation_results

        except Exception as e:
            logger.error(f"Failed to validate ingested content: {e}")
            return {"error": str(e)}

    async def cleanup_failed_ingestion(self, collection_name: str, textbook_name: str) -> bool:
        """Clean up after failed ingestion"""

        try:
            logger.info(f"Cleaning up failed ingestion for {textbook_name}")

            # Delete any partial content
            await self.delete_textbook(
                grade=int(collection_name.split("_")[1]),
                subject="_".join(collection_name.split("_")[2:]),
                textbook_name=textbook_name
            )

            logger.info(f"Cleanup completed for {textbook_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to cleanup failed ingestion: {e}")
            return False