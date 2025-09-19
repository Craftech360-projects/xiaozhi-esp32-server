"""
Process Grade 10 Science textbook PDFs and upload to RAG system
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

from src.education.textbook_ingestion import TextbookIngestionPipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def process_grade10_science_textbooks():
    """Process all Grade 10 science PDF chapters"""

    try:
        # Initialize the ingestion pipeline
        pipeline = TextbookIngestionPipeline()

        logger.info("Initializing textbook ingestion pipeline...")
        success = await pipeline.initialize()

        if not success:
            logger.error("Failed to initialize pipeline")
            return False

        logger.info("Pipeline initialized successfully")

        # Find all PDF files in the grade 10 science folder
        pdf_folder = "D:/cheekofinal/xiaozhi-esp32-server/main/livekit-server/scripts/grade_10_science"
        pdf_files = glob.glob(os.path.join(pdf_folder, "*.pdf"))

        logger.info(f"Found {len(pdf_files)} PDF files to process")

        processed_count = 0
        failed_count = 0

        for pdf_path in pdf_files:
            try:
                # Extract chapter info from filename
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

                # Process the textbook
                logger.info(f"Ingesting Chapter {chapter_number}: {chapter_title}")

                success = await pipeline.ingest_textbook(
                    pdf_path=pdf_path,
                    grade=10,
                    subject="science",
                    textbook_name=f"Grade 10 Science - {chapter_title}",
                    author="NCERT",
                    isbn=f"NCERT-10-SCI-CH{chapter_number}",
                    chapter_number=int(chapter_number) if chapter_number.isdigit() else 1
                )

                if success:
                    logger.info(f"✅ Successfully processed: {filename}")
                    processed_count += 1
                else:
                    logger.error(f"❌ Failed to process: {filename}")
                    failed_count += 1

                # Small delay between processing
                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"❌ Error processing {pdf_path}: {e}")
                failed_count += 1

        logger.info(f"Processing complete! ✅ {processed_count} success, ❌ {failed_count} failed")

        # Get final status
        if processed_count > 0:
            status = await pipeline.get_ingestion_status()
            logger.info(f"Final status: {status}")

        return processed_count > 0

    except Exception as e:
        logger.error(f"❌ Error in processing: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_grade10_science_queries():
    """Test the system with Grade 10 science queries"""

    try:
        from src.services.education_service import EducationService

        # Initialize education service
        education_service = EducationService()

        logger.info("Initializing education service for testing...")
        success = await education_service.initialize()

        if not success:
            logger.error("Failed to initialize education service")
            return False

        logger.info("Education service initialized successfully")

        # Set student context for Grade 10 Science
        await education_service.set_student_context(grade=10, subject="science")

        # Test queries related to the chapters
        test_queries = [
            "What is a chemical reaction?",
            "What are acids and bases?",
            "What are metals and non-metals?",
            "How do organisms reproduce?",
            "What is light reflection?",
            "What is electricity?",
            "What is heredity?"
        ]

        logger.info("Testing Grade 10 Science queries...")

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
                else:
                    logger.info("No sources found")

            except Exception as e:
                logger.error(f"Error with query '{query}': {e}")

        return True

    except Exception as e:
        logger.error(f"❌ Error in testing: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main function"""

    logger.info("=== Grade 10 Science Textbook Processing ===")

    # Check environment variables
    required_env_vars = ["QDRANT_URL", "QDRANT_API_KEY"]

    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        sys.exit(1)

    # Process textbooks
    logger.info("Step 1: Processing Grade 10 Science textbook PDFs...")
    processing_success = await process_grade10_science_textbooks()

    if processing_success:
        logger.info("\nStep 2: Testing with Grade 10 Science queries...")
        await test_grade10_science_queries()
    else:
        logger.error("Processing failed, skipping tests")

    logger.info("\n=== Complete! ===")


if __name__ == "__main__":
    asyncio.run(main())