"""
Process Grade 10 Science textbook PDFs - focused on single collection
Creates only grade_10_science collection
"""

import asyncio
import logging
import sys
import os
import glob
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the parent directory to the path to enable absolute imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.rag.qdrant_manager import QdrantEducationManager
from src.rag.embeddings import EmbeddingManager
from src.rag.document_processor import TextbookProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def create_grade10_science_collection():
    """Create only the grade_10_science collection"""

    try:
        qdrant_manager = QdrantEducationManager()

        collection_name = "grade_10_science"

        logger.info(f"Creating collection: {collection_name}")

        # Check if collection exists
        try:
            existing = await qdrant_manager.get_existing_collections()
            if collection_name in existing:
                logger.info(f"Collection {collection_name} already exists")
                return True
        except:
            pass

        # Create the collection
        success = await qdrant_manager.create_collection(collection_name, "science")

        if success:
            logger.info(f"✅ Successfully created collection: {collection_name}")
            return True
        else:
            logger.error(f"❌ Failed to create collection: {collection_name}")
            return False

    except Exception as e:
        logger.error(f"❌ Error creating collection: {e}")
        return False


async def process_pdfs_to_collection():
    """Process Grade 10 science PDFs directly to the collection"""

    try:
        # Initialize components
        qdrant_manager = QdrantEducationManager()
        embedding_manager = EmbeddingManager()
        document_processor = TextbookProcessor()

        logger.info("Initializing embedding manager...")
        await embedding_manager.initialize()

        # Find PDF files
        pdf_folder = "D:/cheekofinal/xiaozhi-esp32-server/main/livekit-server/scripts/grade_10_science"
        pdf_files = glob.glob(os.path.join(pdf_folder, "*.pdf"))

        logger.info(f"Found {len(pdf_files)} PDF files to process")

        collection_name = "grade_10_science"
        processed_count = 0

        for pdf_path in pdf_files:
            try:
                # Extract chapter info
                filename = Path(pdf_path).stem
                logger.info(f"Processing: {filename}")

                # Extract chapter number and title
                chapter_info = filename.replace("Chapter ", "").strip()
                if " " in chapter_info:
                    chapter_parts = chapter_info.split(" ", 1)
                    chapter_number = chapter_parts[0]
                    chapter_title = chapter_parts[1] if len(chapter_parts) > 1 else f"Chapter {chapter_number}"
                else:
                    chapter_number = chapter_info
                    chapter_title = f"Chapter {chapter_number}"

                logger.info(f"Processing Chapter {chapter_number}: {chapter_title}")

                # Process PDF content
                metadata = {
                    "grade": 10,
                    "subject": "science",
                    "textbook_name": f"Grade 10 Science - {chapter_title}",
                    "textbook_author": "NCERT",
                    "isbn": f"NCERT-10-SCI-CH{chapter_number}",
                    "chapter": chapter_title,
                    "chapter_number": int(chapter_number) if chapter_number.isdigit() else 1
                }

                # Extract text chunks from PDF
                chunks = await document_processor.process_textbook(
                    pdf_path,
                    metadata["grade"],
                    metadata["subject"],
                    metadata["textbook_name"],
                    metadata["textbook_author"],
                    metadata["isbn"]
                )

                if not chunks:
                    logger.warning(f"No content extracted from {filename}")
                    continue

                logger.info(f"Extracted {len(chunks)} chunks from {filename}")

                # Generate embeddings and prepare for upload
                content_chunks = []

                for i, chunk in enumerate(chunks):
                    try:
                        # Generate embedding
                        embedding = await embedding_manager.get_text_embedding(chunk.content)

                        if embedding:
                            content_chunk = {
                                "id": int(f"{chapter_number}{i+1:03d}"),  # Convert to integer: chapter + chunk number (e.g., 1001, 1002, 2001)
                                "text_embedding": embedding,
                                "payload": {
                                    "content": chunk.content,
                                    "content_type": chunk.content_type,
                                    "textbook_name": metadata["textbook_name"],
                                    "textbook_author": metadata["textbook_author"],
                                    "isbn": metadata["isbn"],
                                    "grade": metadata["grade"],
                                    "subject": metadata["subject"],
                                    "page_number": chunk.page_number,
                                    "chapter": metadata["chapter"],
                                    "chapter_number": metadata["chapter_number"],
                                    "topic": [chapter_title.lower(), "science"],
                                    "keywords": chunk.keywords if hasattr(chunk, 'keywords') else [],
                                    "difficulty_level": "intermediate",
                                    "cognitive_level": "understand",
                                    "concepts": [chapter_title.lower()]
                                }
                            }
                            content_chunks.append(content_chunk)

                    except Exception as e:
                        logger.warning(f"Failed to process chunk {i}: {e}")

                # Upload to Qdrant
                if content_chunks:
                    logger.info(f"Uploading {len(content_chunks)} chunks to {collection_name}")

                    success = await qdrant_manager.upsert_content(collection_name, content_chunks)

                    if success:
                        logger.info(f"✅ Successfully uploaded {filename}")
                        processed_count += 1
                    else:
                        logger.error(f"❌ Failed to upload {filename}")
                else:
                    logger.warning(f"No valid chunks to upload for {filename}")

                # Small delay between files
                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"❌ Error processing {pdf_path}: {e}")

        logger.info(f"Processing complete! ✅ {processed_count} files processed successfully")
        return processed_count > 0

    except Exception as e:
        logger.error(f"❌ Error in processing: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_grade10_science():
    """Test the Grade 10 science collection"""

    try:
        from src.services.education_service import EducationService

        # Initialize education service
        education_service = EducationService()

        logger.info("Initializing education service for testing...")
        success = await education_service.initialize()

        if not success:
            logger.error("Failed to initialize education service")
            return False

        # Set context for Grade 10 Science
        await education_service.set_student_context(grade=10, subject="science")

        # Test chemistry queries
        test_queries = [
            "What is a chemical reaction?",
            "What are acids and bases?",
            "What are metals and non-metals?",
            "How do organisms reproduce?",
            "What is light reflection?"
        ]

        logger.info("\n=== Testing Grade 10 Science Queries ===")

        for i, query in enumerate(test_queries, 1):
            logger.info(f"\n--- Query {i}: {query} ---")

            try:
                result = await education_service.answer_question(query)

                answer = result.get('answer', 'No answer found')
                confidence = result.get('confidence', 0.0)
                sources = result.get('sources', [])

                logger.info(f"Answer: {answer[:200]}...")
                logger.info(f"Confidence: {confidence:.2f}")

                if sources:
                    source = sources[0]
                    textbook = source.get('textbook', 'Unknown')
                    page = source.get('page', 'Unknown')
                    logger.info(f"Source: {textbook}, Page {page}")

                if any(word in answer.lower() for word in ['chemical', 'acid', 'metal', 'organism', 'light', 'reaction']):
                    logger.info("✅ Relevant answer found!")

            except Exception as e:
                logger.error(f"Error with query '{query}': {e}")

        return True

    except Exception as e:
        logger.error(f"❌ Error in testing: {e}")
        return False


async def main():
    """Main function"""

    logger.info("=== Grade 10 Science Collection Processing ===")

    # Check environment variables
    required_env_vars = ["QDRANT_URL", "QDRANT_API_KEY"]

    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        sys.exit(1)

    # Step 1: Create collection
    logger.info("Step 1: Creating grade_10_science collection...")
    collection_success = await create_grade10_science_collection()

    if not collection_success:
        logger.error("Failed to create collection, exiting")
        return

    # Step 2: Process PDFs
    logger.info("Step 2: Processing Grade 10 Science PDFs...")
    processing_success = await process_pdfs_to_collection()

    if processing_success:
        # Step 3: Test
        logger.info("Step 3: Testing Grade 10 Science queries...")
        await test_grade10_science()
    else:
        logger.error("Processing failed, skipping tests")

    logger.info("\n=== Complete! ===")


if __name__ == "__main__":
    asyncio.run(main())