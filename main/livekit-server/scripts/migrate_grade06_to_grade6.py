"""
Migrate data from grade_06_science to grade_6_science collection
This ensures the retriever can find the Grade 6 science content
"""

import asyncio
import logging
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.rag.qdrant_manager import QdrantEducationManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def migrate_grade06_to_grade6():
    """Migrate all points from grade_06_science to grade_6_science"""

    try:
        manager = QdrantEducationManager()

        source_collection = "grade_06_science"
        target_collection = "grade_6_science"

        logger.info(f"Starting migration from {source_collection} to {target_collection}")

        # Check source collection exists and has data
        try:
            source_info = manager.client.get_collection(source_collection)
            logger.info(f"Source collection {source_collection} has {source_info.points_count} points")

            if source_info.points_count == 0:
                logger.warning("Source collection is empty, nothing to migrate")
                return True

        except Exception as e:
            logger.error(f"Source collection {source_collection} not found: {e}")
            return False

        # Check target collection exists
        try:
            target_info = manager.client.get_collection(target_collection)
            logger.info(f"Target collection {target_collection} has {target_info.points_count} points")
        except Exception as e:
            logger.error(f"Target collection {target_collection} not found: {e}")
            return False

        # Get all points from source collection
        logger.info("Retrieving all points from source collection...")

        all_points = []
        offset = None
        batch_size = 100

        while True:
            result = manager.client.scroll(
                collection_name=source_collection,
                limit=batch_size,
                offset=offset,
                with_payload=True,
                with_vectors=True
            )

            points = result[0]  # points
            next_offset = result[1]  # next offset

            if not points:
                break

            all_points.extend(points)
            logger.info(f"Retrieved {len(all_points)} points so far...")

            if next_offset is None:
                break

            offset = next_offset

        logger.info(f"Retrieved total of {len(all_points)} points from source collection")

        if not all_points:
            logger.warning("No points found in source collection")
            return True

        # Upload points to target collection in batches
        logger.info("Uploading points to target collection...")

        batch_size = 50
        uploaded_count = 0

        for i in range(0, len(all_points), batch_size):
            batch = all_points[i:i + batch_size]

            try:
                # Upload batch
                manager.client.upsert(
                    collection_name=target_collection,
                    points=batch
                )

                uploaded_count += len(batch)
                logger.info(f"Uploaded {uploaded_count}/{len(all_points)} points")

            except Exception as e:
                logger.error(f"Failed to upload batch {i//batch_size + 1}: {e}")
                return False

        # Verify migration
        final_target_info = manager.client.get_collection(target_collection)
        logger.info(f"Migration complete! Target collection now has {final_target_info.points_count} points")

        if final_target_info.points_count >= source_info.points_count:
            logger.info("✅ Migration successful!")
            return True
        else:
            logger.error("❌ Migration incomplete - point counts don't match")
            return False

    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main function"""

    logger.info("=== Grade 06 to Grade 6 Science Collection Migration ===")

    # Check environment variables
    required_env_vars = ["QDRANT_URL", "QDRANT_API_KEY"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        sys.exit(1)

    # Run migration
    success = await migrate_grade06_to_grade6()

    if success:
        logger.info("\n=== Migration Complete! ===")
        logger.info("The Grade 6 science content is now available to the main server.")
    else:
        logger.error("\n=== Migration Failed! ===")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())