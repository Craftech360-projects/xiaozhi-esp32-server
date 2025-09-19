"""
Recreate collections with correct vector dimensions (384 for all-MiniLM-L6-v2)
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

from src.rag.qdrant_manager import QdrantEducationManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def recreate_grade_8_math_collection():
    """Recreate just the grade_8_mathematics collection for testing"""

    try:
        # Initialize Qdrant manager
        qdrant_manager = QdrantEducationManager()

        collection_name = "grade_8_mathematics"

        logger.info(f"Deleting existing collection: {collection_name}")

        try:
            # Delete existing collection
            qdrant_manager.client.delete_collection(collection_name)
            logger.info(f"✅ Deleted collection: {collection_name}")
        except Exception as e:
            logger.warning(f"Collection might not exist: {e}")

        # Wait a moment
        await asyncio.sleep(1)

        logger.info(f"Creating new collection with correct dimensions: {collection_name}")

        # Create new collection with correct dimensions (384)
        success = await qdrant_manager.create_collection(collection_name, "mathematics")

        if success:
            logger.info(f"✅ Successfully recreated collection: {collection_name}")
            logger.info("Collection now has 384-dimensional vectors (all-MiniLM-L6-v2)")
        else:
            logger.error(f"❌ Failed to recreate collection: {collection_name}")

    except Exception as e:
        logger.error(f"❌ Error recreating collection: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Main function"""

    logger.info("=== Recreating Collections with Correct Dimensions ===")

    # Check environment variables
    required_env_vars = ["QDRANT_URL", "QDRANT_API_KEY"]

    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        sys.exit(1)

    await recreate_grade_8_math_collection()

    logger.info("Collection recreation complete!")


if __name__ == "__main__":
    asyncio.run(main())