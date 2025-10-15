"""
TOC-Guided RAG Processing Pipeline
Orchestrates PDF extraction, TOC extraction/expansion, semantic chunking, and Qdrant storage
"""

import asyncio
import logging
import sys
import os
from pathlib import Path
from typing import Dict, List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rag.pdf_extractor import PDFExtractor
from rag.toc_extractor import TOCExtractor
from rag.toc_expander import TOCExpander
from rag.semantic_chunker import SemanticChunker
from rag.chunk_validator import ChunkValidator
from rag.toc_manager import TOCManager
from rag.qdrant_manager import QdrantEducationManager
from sentence_transformers import SentenceTransformer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TOCGuidedPipeline:
    """TOC-guided RAG processing pipeline"""

    def __init__(self, grade: int = 6, subject: str = "science"):
        self.grade = grade
        self.subject = subject

        # Initialize components
        self.pdf_extractor = PDFExtractor()
        self.toc_extractor = TOCExtractor()
        self.toc_expander = TOCExpander()
        self.semantic_chunker = SemanticChunker(
            min_chunk_size=400,
            max_chunk_size=800
        )
        self.chunk_validator = ChunkValidator(similarity_threshold=0.65)

        # Qdrant components
        self.qdrant_manager = QdrantEducationManager()
        self.toc_manager = None  # Will be initialized after Qdrant client
        self.collection_name = self.qdrant_manager.get_collection_name(grade, subject)

        # Embedding model
        self.embedding_model = None

    def _load_embedding_model(self):
        """Lazy load embedding model"""
        if self.embedding_model is None:
            logger.info("Loading embedding model (all-MiniLM-L6-v2)...")
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

    async def initialize(self):
        """Initialize pipeline components"""
        logger.info("Initializing TOC-guided pipeline...")

        # Initialize Qdrant collection
        if self.grade == 6:
            success = await self.qdrant_manager.initialize_grade6_and_grade10_science()
        elif self.grade == 10:
            success = await self.qdrant_manager.initialize_grade10_science_only()
        else:
            logger.error(f"Unsupported grade: {self.grade}")
            return False

        if not success:
            logger.error("Failed to initialize Qdrant collection")
            return False

        # Initialize TOC manager
        self.toc_manager = TOCManager(
            qdrant_client=self.qdrant_manager.client,
            collection_name=f"{self.collection_name}_toc"
        )
        await self.toc_manager.initialize_collection()

        logger.info("Pipeline initialization complete")
        return True

    async def process_pdf(
        self,
        pdf_path: str,
        validate_chunks: bool = True,
        store_in_qdrant: bool = True
    ) -> Dict:
        """
        Process a single PDF through the TOC-guided pipeline

        Returns:
            {
                'pdf_path': str,
                'chapter_info': Dict,
                'toc': Dict,
                'expanded_toc': Dict,
                'chunks': List[Dict],
                'validation_report': str,
                'chunks_stored': int
            }
        """

        logger.info(f"Processing PDF: {pdf_path}")

        # Step 1: Extract PDF content
        logger.info("Step 1: Extracting PDF content...")
        pdf_data = self.pdf_extractor.extract_from_pdf(pdf_path)
        chapter_info = self.pdf_extractor.extract_chapter_info(pdf_path)

        logger.info(
            f"Extracted {len(pdf_data['pages'])} pages, "
            f"{len(pdf_data['full_text'])} characters"
        )

        # Step 2: Extract TOC structure
        logger.info("Step 2: Extracting TOC structure...")
        toc = await self.toc_extractor.extract_toc(
            pdf_data['full_text'],
            chapter_info
        )

        logger.info(f"Extracted TOC with {len(toc['sections'])} sections")

        # Step 3: Expand TOC with metadata
        logger.info("Step 3: Expanding TOC with learning metadata...")
        expanded_toc = await self.toc_expander.expand_toc(
            toc,
            pdf_data['full_text']
        )

        logger.info(f"Expanded {len(expanded_toc['sections'])} TOC sections")

        # Store TOC in Qdrant
        if store_in_qdrant:
            await self.toc_manager.store_toc(expanded_toc)
            logger.info("Stored TOC in Qdrant")

        # Step 4: Semantic chunking guided by TOC
        logger.info("Step 4: Creating semantic chunks guided by TOC...")
        chunks = self.semantic_chunker.chunk_by_toc(
            pdf_data['full_text'],
            expanded_toc
        )

        logger.info(f"Created {len(chunks)} chunks")

        # Log activity preservation
        activity_chunks = [c for c in chunks if c['metadata']['is_activity']]
        logger.info(f"Preserved {len(activity_chunks)} activities as complete units")

        # Step 5: Validate chunks (optional)
        validation_report = ""
        if validate_chunks:
            logger.info("Step 5: Validating chunks...")
            valid_chunks, flagged_chunks = await self.chunk_validator.validate_chunks(
                chunks,
                expanded_toc
            )

            validation_report = self.chunk_validator.generate_validation_report(
                flagged_chunks
            )

            if flagged_chunks:
                logger.warning(f"Flagged {len(flagged_chunks)} chunks during validation")
                logger.info(validation_report)
            else:
                logger.info("All chunks passed validation")

            # Use only valid chunks
            chunks = valid_chunks

        # Step 6: Generate embeddings and store in Qdrant
        chunks_stored = 0
        if store_in_qdrant:
            logger.info("Step 6: Generating embeddings and storing in Qdrant...")
            self._load_embedding_model()

            # Prepare chunks for Qdrant
            content_chunks = []
            for chunk in chunks:
                # Generate embedding
                embedding = self.embedding_model.encode(
                    chunk['content'],
                    convert_to_numpy=True
                ).tolist()

                # Prepare payload
                payload = {
                    'content': chunk['content'],
                    'content_type': chunk['metadata']['section_type'],
                    'chapter_number': chunk['metadata']['chapter_number'],
                    'chapter': chunk['metadata']['chapter_title'],
                    'section_title': chunk['metadata']['section_title'],
                    'grade': self.grade,
                    'subject': self.subject,

                    # TOC-guided metadata
                    'toc_section_id': chunk['toc_section_id'],
                    'section_type': chunk['metadata']['section_type'],
                    'content_priority': chunk['metadata']['content_priority'],
                    'content_weight': chunk['metadata']['content_weight'],
                    'is_activity': chunk['metadata']['is_activity'],

                    # Learning metadata
                    'key_concepts': chunk['metadata']['key_concepts'],
                    'learning_objectives': chunk['metadata']['learning_objectives'],
                    'difficulty_level': chunk['metadata']['difficulty_level'],
                    'cognitive_level': chunk['metadata']['cognitive_level'],
                    'related_activities': chunk['metadata']['related_activities']
                }

                content_chunks.append({
                    'id': chunk['id'],
                    'text_embedding': embedding,
                    'payload': payload
                })

            # Store in Qdrant
            success = await self.qdrant_manager.upsert_content(
                self.collection_name,
                content_chunks
            )

            if success:
                chunks_stored = len(content_chunks)
                logger.info(f"Successfully stored {chunks_stored} chunks in Qdrant")
            else:
                logger.error("Failed to store chunks in Qdrant")

        # Return results
        return {
            'pdf_path': pdf_path,
            'chapter_info': chapter_info,
            'toc': toc,
            'expanded_toc': expanded_toc,
            'chunks': chunks,
            'validation_report': validation_report,
            'chunks_stored': chunks_stored
        }

    async def process_directory(
        self,
        pdf_dir: str,
        validate_chunks: bool = True
    ) -> List[Dict]:
        """
        Process all PDFs in a directory

        Returns: List of processing results for each PDF
        """

        pdf_dir = Path(pdf_dir)
        if not pdf_dir.exists():
            logger.error(f"Directory not found: {pdf_dir}")
            return []

        # Find all PDFs
        pdf_files = list(pdf_dir.glob("*.pdf"))
        logger.info(f"Found {len(pdf_files)} PDF files in {pdf_dir}")

        # Process each PDF
        results = []
        for pdf_file in pdf_files:
            try:
                result = await self.process_pdf(
                    str(pdf_file),
                    validate_chunks=validate_chunks,
                    store_in_qdrant=True
                )
                results.append(result)
                logger.info(f"[OK] Processed {pdf_file.name}")
            except Exception as e:
                logger.error(f"[ERROR] Failed to process {pdf_file.name}: {e}")
                results.append({
                    'pdf_path': str(pdf_file),
                    'error': str(e)
                })

        # Summary
        successful = [r for r in results if 'error' not in r]
        failed = [r for r in results if 'error' in r]

        logger.info(
            f"\n{'='*60}\n"
            f"Processing Complete\n"
            f"{'='*60}\n"
            f"Total PDFs: {len(pdf_files)}\n"
            f"Successful: {len(successful)}\n"
            f"Failed: {len(failed)}\n"
            f"{'='*60}"
        )

        return results


async def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="TOC-guided RAG processing pipeline"
    )
    parser.add_argument(
        "pdf_path",
        type=str,
        help="Path to PDF file or directory"
    )
    parser.add_argument(
        "--grade",
        type=int,
        default=6,
        help="Grade level (default: 6)"
    )
    parser.add_argument(
        "--subject",
        type=str,
        default="science",
        help="Subject (default: science)"
    )
    parser.add_argument(
        "--no-validation",
        action="store_true",
        help="Skip chunk validation"
    )

    args = parser.parse_args()

    # Initialize pipeline
    pipeline = TOCGuidedPipeline(grade=args.grade, subject=args.subject)
    await pipeline.initialize()

    # Process PDF(s)
    pdf_path = Path(args.pdf_path)

    if pdf_path.is_file():
        # Single PDF
        result = await pipeline.process_pdf(
            str(pdf_path),
            validate_chunks=not args.no_validation
        )

        # Print summary
        print(f"\n{'='*60}")
        print("Processing Summary")
        print(f"{'='*60}")
        print(f"PDF: {result['pdf_path']}")
        print(f"Chapter: {result['chapter_info']['chapter_number']} - {result['chapter_info']['chapter_title']}")
        print(f"TOC Sections: {len(result['expanded_toc']['sections'])}")
        print(f"Chunks Created: {len(result['chunks'])}")
        print(f"Chunks Stored: {result['chunks_stored']}")

        if result['validation_report']:
            print(result['validation_report'])

        print(f"{'='*60}\n")

    elif pdf_path.is_dir():
        # Directory of PDFs
        results = await pipeline.process_directory(
            str(pdf_path),
            validate_chunks=not args.no_validation
        )

    else:
        logger.error(f"Invalid path: {pdf_path}")
        return


if __name__ == "__main__":
    asyncio.run(main())
