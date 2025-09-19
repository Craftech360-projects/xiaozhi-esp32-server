"""
Sample script to test textbook ingestion
This script demonstrates how to ingest educational content into the RAG system
"""

import asyncio
import logging
import sys
import os
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


async def test_ingestion_pipeline():
    """Test the textbook ingestion pipeline with sample content"""

    # Initialize the pipeline
    pipeline = TextbookIngestionPipeline()

    logger.info("Initializing ingestion pipeline...")
    success = await pipeline.initialize()

    if not success:
        logger.error("Failed to initialize pipeline")
        return False

    logger.info("Pipeline initialized successfully")

    # Test collection creation
    logger.info("Testing collection management...")
    stats = await pipeline.get_ingestion_status()
    logger.info(f"Current status: {stats}")

    # Create sample textbook content (since we don't have actual PDFs)
    await create_sample_content(pipeline)

    return True


async def create_sample_content(pipeline):
    """Create sample educational content for testing"""

    # Sample content for Grade 8 Mathematics
    sample_chunks = [
        {
            "id": 1,  # Integer ID instead of string
            "text_embedding": [0.1] * 384,  # Dummy embedding for all-MiniLM-L6-v2
            "payload": {
                "content": "A linear equation is an equation in which the highest power of the variable is 1. For example, 2x + 3 = 7 is a linear equation.",
                "content_type": "definition",
                "textbook_name": "Sample Mathematics Grade 8",
                "textbook_author": "Test Author",
                "isbn": "123-456-789",
                "grade": 8,
                "subject": "mathematics",
                "page_number": 45,
                "chapter": "Chapter 3: Linear Equations",
                "section": "3.1 Introduction to Linear Equations",
                "topic": ["linear equations", "algebra"],
                "keywords": ["linear", "equation", "variable", "power"],
                "difficulty_level": "intermediate",
                "cognitive_level": "understand",
                "concepts": ["linear equations", "algebraic expressions"]
            }
        },
        {
            "id": 2,  # Integer ID
            "text_embedding": [0.2] * 384,  # Dummy embedding for all-MiniLM-L6-v2
            "payload": {
                "content": "To solve a linear equation like 2x + 3 = 7, subtract 3 from both sides: 2x = 4, then divide by 2: x = 2.",
                "content_type": "example",
                "textbook_name": "Sample Mathematics Grade 8",
                "textbook_author": "Test Author",
                "isbn": "123-456-789",
                "grade": 8,
                "subject": "mathematics",
                "page_number": 46,
                "chapter": "Chapter 3: Linear Equations",
                "section": "3.2 Solving Linear Equations",
                "topic": ["solving equations", "algebra"],
                "keywords": ["solve", "subtract", "divide", "steps"],
                "difficulty_level": "intermediate",
                "cognitive_level": "apply",
                "concepts": ["equation solving", "algebraic operations"]
            }
        },
        {
            "id": 3,  # Integer ID
            "text_embedding": [0.3] * 384,  # Dummy embedding for all-MiniLM-L6-v2
            "payload": {
                "content": "Exercise: Solve the equation 3x - 5 = 10. Show all steps in your solution.",
                "content_type": "exercise",
                "textbook_name": "Sample Mathematics Grade 8",
                "textbook_author": "Test Author",
                "isbn": "123-456-789",
                "grade": 8,
                "subject": "mathematics",
                "page_number": 48,
                "chapter": "Chapter 3: Linear Equations",
                "section": "3.3 Practice Problems",
                "topic": ["practice problems", "algebra"],
                "keywords": ["exercise", "solve", "steps"],
                "difficulty_level": "intermediate",
                "cognitive_level": "apply",
                "concepts": ["problem solving", "linear equations"]
            }
        }
    ]

    # Get collection name for Grade 8 Mathematics
    collection_name = pipeline.qdrant_manager.get_collection_name(8, "mathematics")

    logger.info(f"Inserting sample content into collection: {collection_name}")

    # Insert sample content
    success = await pipeline.qdrant_manager.upsert_content(collection_name, sample_chunks)

    if success:
        logger.info("Sample content inserted successfully")

        # Validate the content
        validation_result = await pipeline.validate_ingested_content(collection_name, 3)
        logger.info(f"Validation result: {validation_result}")

    else:
        logger.error("Failed to insert sample content")


async def test_education_service():
    """Test the education service with sample queries"""

    from src.services.education_service import EducationService

    # Initialize education service
    education_service = EducationService()

    logger.info("Initializing education service...")
    success = await education_service.initialize()

    if not success:
        logger.error("Failed to initialize education service")
        return False

    logger.info("Education service initialized successfully")

    # Set student context
    await education_service.set_student_context(grade=8, subject="mathematics")

    # Test queries
    test_queries = [
        "What is a linear equation?",
        "How do I solve linear equations?",
        "Give me practice problems for linear equations"
    ]

    for query in test_queries:
        logger.info(f"\nTesting query: {query}")
        result = await education_service.answer_question(query)
        logger.info(f"Answer: {result.get('answer', 'No answer')}")
        logger.info(f"Confidence: {result.get('confidence', 0.0)}")

        if result.get('sources'):
            source = result['sources'][0]
            logger.info(f"Source: {source.get('textbook', 'Unknown')} - Page {source.get('page', 'Unknown')}")

    return True


async def main():
    """Main test function"""

    logger.info("Starting RAG system test...")

    try:
        # Test ingestion pipeline
        logger.info("=== Testing Ingestion Pipeline ===")
        await test_ingestion_pipeline()

        # Wait a moment for indexing
        await asyncio.sleep(2)

        # Test education service
        logger.info("\n=== Testing Education Service ===")
        await test_education_service()

        logger.info("\n=== Test completed successfully ===")

    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Make sure environment variables are set
    required_env_vars = ["QDRANT_URL", "QDRANT_API_KEY"]

    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        logger.error("Please set these in your .env file")
        sys.exit(1)

    # Run the test
    asyncio.run(main())