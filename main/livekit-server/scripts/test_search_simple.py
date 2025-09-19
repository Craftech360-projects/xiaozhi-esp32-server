"""
Simple test to verify search functionality works
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_simple_search():
    """Test simple search functionality"""

    try:
        from src.rag.qdrant_manager import QdrantEducationManager

        # Initialize Qdrant manager
        qdrant_manager = QdrantEducationManager()

        # Test basic connection
        logger.info("Testing Qdrant connection...")

        # Try to get existing collections
        collections = await qdrant_manager.get_existing_collections()
        logger.info(f"Found {len(collections)} collections")

        if "grade_8_mathematics" in collections:
            logger.info("✅ grade_8_mathematics collection exists")

            # Try simple search without filters to test basic retrieval
            try:
                collection_name = "grade_8_mathematics"

                # Test with direct Qdrant client search (no filters)
                search_result = qdrant_manager.client.search(
                    collection_name=collection_name,
                    query_vector=[0.1] * 384,  # Dummy vector for all-MiniLM-L6-v2
                    limit=5,
                    with_payload=True
                )

                if search_result:
                    logger.info(f"✅ Basic search returned {len(search_result)} results")
                    for i, result in enumerate(search_result):
                        content = result.payload.get('content', 'No content')[:100]
                        logger.info(f"  Result {i+1}: {content}...")
                else:
                    logger.info("❌ Search returned no results")

            except Exception as e:
                logger.error(f"❌ Search failed: {e}")

        else:
            logger.error("❌ grade_8_mathematics collection not found")

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Main function"""

    logger.info("=== Simple Search Test ===")

    # Check environment variables
    required_env_vars = ["QDRANT_URL", "QDRANT_API_KEY"]

    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        sys.exit(1)

    await test_simple_search()

    logger.info("Test complete!")


if __name__ == "__main__":
    asyncio.run(main())