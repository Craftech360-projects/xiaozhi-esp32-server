"""
Process a single Grade 10 Science chapter and test it quickly
"""

import asyncio
import logging
import sys
import os
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


async def process_single_chapter():
    """Process just Chapter 1 to test the system quickly"""

    try:
        # Initialize the ingestion pipeline
        pipeline = TextbookIngestionPipeline()

        logger.info("Initializing textbook ingestion pipeline...")
        success = await pipeline.initialize()

        if not success:
            logger.error("Failed to initialize pipeline")
            return False

        logger.info("Pipeline initialized successfully")

        # Process just Chapter 1
        pdf_path = "D:/cheekofinal/xiaozhi-esp32-server/main/livekit-server/scripts/grade_10_science/Chapter 1 Chemical Reactions and Equations.pdf"

        if not os.path.exists(pdf_path):
            logger.error(f"PDF file not found: {pdf_path}")
            return False

        logger.info("Processing Chapter 1: Chemical Reactions and Equations")

        success = await pipeline.ingest_textbook(
            pdf_path=pdf_path,
            grade=10,
            subject="science",
            textbook_name="Grade 10 Science - Chemical Reactions and Equations",
            author="NCERT",
            isbn="NCERT-10-SCI-CH1",
            chapter_number=1
        )

        if success:
            logger.info("✅ Successfully processed Chapter 1!")

            # Get status
            status = await pipeline.get_ingestion_status()
            logger.info(f"Ingestion status: {status}")

            return True
        else:
            logger.error("❌ Failed to process Chapter 1")
            return False

    except Exception as e:
        logger.error(f"❌ Error in processing: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_chemistry_queries():
    """Test with chemistry-related queries"""

    try:
        from src.services.education_service import EducationService

        # Initialize education service
        education_service = EducationService()

        logger.info("Initializing education service...")
        success = await education_service.initialize()

        if not success:
            logger.error("Failed to initialize education service")
            return False

        # Set context for Grade 10 Science
        await education_service.set_student_context(grade=10, subject="science")

        # Test chemistry queries
        test_queries = [
            "What is a chemical reaction?",
            "What are the types of chemical reactions?",
            "How do you balance chemical equations?",
            "What happens when magnesium burns?",
            "What is oxidation and reduction?"
        ]

        logger.info("\n=== Testing Chemistry Queries ===")

        for i, query in enumerate(test_queries, 1):
            logger.info(f"\n--- Query {i}: {query} ---")

            try:
                result = await education_service.answer_question(query)

                answer = result.get('answer', 'No answer found')
                confidence = result.get('confidence', 0.0)
                sources = result.get('sources', [])

                logger.info(f"Answer: {answer}")
                logger.info(f"Confidence: {confidence:.2f}")

                if sources:
                    source = sources[0]
                    textbook = source.get('textbook', 'Unknown')
                    page = source.get('page', 'Unknown')
                    logger.info(f"Source: {textbook}, Page {page}")

                if "chemical reaction" in answer.lower() or "equation" in answer.lower():
                    logger.info("✅ Relevant answer found!")
                else:
                    logger.warning("❓ Answer may not be directly relevant")

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

    logger.info("=== Single Chapter Test ===")

    # Check environment variables
    required_env_vars = ["QDRANT_URL", "QDRANT_API_KEY"]

    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        sys.exit(1)

    # Process single chapter
    logger.info("Step 1: Processing Chapter 1 (Chemical Reactions)...")
    processing_success = await process_single_chapter()

    if processing_success:
        logger.info("\nStep 2: Testing chemistry queries...")
        await test_chemistry_queries()
    else:
        logger.error("Processing failed, skipping tests")

    logger.info("\n=== Test Complete! ===")


if __name__ == "__main__":
    asyncio.run(main())