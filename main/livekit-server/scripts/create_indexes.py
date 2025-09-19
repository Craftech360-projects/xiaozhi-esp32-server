"""
Script to create payload indexes for Qdrant collections
Run this to fix search filter issues
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


async def create_indexes():
    """Create payload indexes for all collections"""

    logger.info("Starting payload index creation...")

    # Initialize Qdrant manager
    qdrant_manager = QdrantEducationManager()

    try:
        # Create indexes for all collections
        success = await qdrant_manager.create_indexes_for_all_collections()

        if success:
            logger.info("✅ All payload indexes created successfully!")
        else:
            logger.error("❌ Failed to create some payload indexes")

    except Exception as e:
        logger.error(f"❌ Error creating indexes: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Main function"""

    # Check environment variables
    required_env_vars = ["QDRANT_URL", "QDRANT_API_KEY"]

    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        logger.error("Please set these in your .env file")
        sys.exit(1)

    # Create indexes
    await create_indexes()

    logger.info("Index creation complete!")


if __name__ == "__main__":
    asyncio.run(main())