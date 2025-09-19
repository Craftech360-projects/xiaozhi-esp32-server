"""
Delete all educational collections
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


async def delete_all_educational_collections():
    """Delete all educational collections"""

    try:
        # Initialize Qdrant manager
        qdrant_manager = QdrantEducationManager()

        logger.info("Getting existing collections...")
        existing_collections = await qdrant_manager.get_existing_collections()

        logger.info(f"Found {len(existing_collections)} collections")

        # Filter for educational collections (grade_X_subject pattern)
        educational_collections = [
            col for col in existing_collections
            if col.startswith('grade_') and '_' in col[6:]
        ]

        logger.info(f"Found {len(educational_collections)} educational collections to delete")

        deleted_count = 0
        for collection_name in educational_collections:
            try:
                logger.info(f"Deleting collection: {collection_name}")
                qdrant_manager.client.delete_collection(collection_name)
                deleted_count += 1
                logger.info(f"✅ Deleted: {collection_name}")
            except Exception as e:
                logger.error(f"❌ Failed to delete {collection_name}: {e}")

        logger.info(f"✅ Successfully deleted {deleted_count} educational collections")

    except Exception as e:
        logger.error(f"❌ Error deleting collections: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Main function"""

    logger.info("=== Deleting All Educational Collections ===")

    # Check environment variables
    required_env_vars = ["QDRANT_URL", "QDRANT_API_KEY"]

    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        sys.exit(1)

    await delete_all_educational_collections()

    logger.info("Collection deletion complete!")


if __name__ == "__main__":
    asyncio.run(main())