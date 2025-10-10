#!/usr/bin/env python3
"""
Qdrant Collection Migration Script
Migrates collections from Qdrant Cloud to local Qdrant instance
"""
import os
import sys
from pathlib import Path
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Qdrant Cloud Configuration (from .env)
CLOUD_URL = os.getenv(
    "QDRANT_CLOUD_URL",
    "https://a2482b9f-2c29-476e-9ff0-741aaaaf632e.eu-west-1-0.aws.cloud.qdrant.io"
)
CLOUD_API_KEY = os.getenv(
    "QDRANT_CLOUD_API_KEY",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.zPBGAqVGy-edbbgfNOJsPWV496BsnQ4ELOFvsLNyjsk"
)

# Local Qdrant Configuration
LOCAL_URL = os.getenv("QDRANT_LOCAL_URL", "http://localhost:6333")

# Collections to migrate
COLLECTIONS = ["xiaozhi_music", "xiaozhi_stories"]


def migrate_collection(
    cloud_client: QdrantClient,
    local_client: QdrantClient,
    collection_name: str,
    batch_size: int = 100
):
    """
    Migrate a single collection from cloud to local

    Args:
        cloud_client: Qdrant cloud client
        local_client: Qdrant local client
        collection_name: Name of collection to migrate
        batch_size: Number of points to migrate at once
    """
    logger.info(f"Starting migration for collection: {collection_name}")

    try:
        # Get collection info from cloud
        collection_info = cloud_client.get_collection(collection_name)
        logger.info(f"Collection info: {collection_info}")

        # Get vector configuration
        vector_config = collection_info.config.params.vectors

        # Create collection in local instance
        logger.info(f"Creating collection '{collection_name}' in local Qdrant...")

        try:
            local_client.create_collection(
                collection_name=collection_name,
                vectors_config=vector_config,
            )
            logger.info(f"Collection '{collection_name}' created successfully")
        except Exception as e:
            if "already exists" in str(e).lower():
                logger.warning(f"Collection '{collection_name}' already exists, will append data")
            else:
                raise

        # Get all points from cloud (with pagination)
        offset = None
        total_migrated = 0

        while True:
            # Scroll through points
            points, next_offset = cloud_client.scroll(
                collection_name=collection_name,
                limit=batch_size,
                offset=offset,
                with_vectors=True,
                with_payload=True,
            )

            if not points:
                break

            # Convert Record objects to PointStruct format
            from qdrant_client.models import PointStruct
            converted_points = [
                PointStruct(
                    id=point.id,
                    vector=point.vector,
                    payload=point.payload
                )
                for point in points
            ]

            # Upload points to local instance
            local_client.upsert(
                collection_name=collection_name,
                points=converted_points,
            )

            total_migrated += len(points)
            logger.info(f"Migrated {total_migrated} points...")

            # Check if we're done
            if next_offset is None:
                break

            offset = next_offset

        logger.info(
            f"✅ Migration complete for '{collection_name}': "
            f"{total_migrated} points migrated"
        )

        return total_migrated

    except Exception as e:
        logger.error(f"❌ Error migrating collection '{collection_name}': {e}")
        raise


def main():
    """Main migration function"""
    logger.info("=" * 60)
    logger.info("Qdrant Collection Migration Tool")
    logger.info("=" * 60)

    # Connect to cloud Qdrant
    logger.info(f"Connecting to Qdrant Cloud: {CLOUD_URL}")
    try:
        cloud_client = QdrantClient(
            url=CLOUD_URL,
            api_key=CLOUD_API_KEY,
        )
        logger.info("✅ Connected to Qdrant Cloud")
    except Exception as e:
        logger.error(f"❌ Failed to connect to Qdrant Cloud: {e}")
        sys.exit(1)

    # Connect to local Qdrant
    logger.info(f"Connecting to Local Qdrant: {LOCAL_URL}")
    try:
        local_client = QdrantClient(url=LOCAL_URL)
        logger.info("✅ Connected to Local Qdrant")
    except Exception as e:
        logger.error(f"❌ Failed to connect to Local Qdrant: {e}")
        logger.error("Make sure Qdrant is running: docker-compose up -d qdrant")
        sys.exit(1)

    # Get list of collections from cloud
    try:
        cloud_collections = cloud_client.get_collections()
        logger.info(f"Available collections in cloud: {cloud_collections}")
    except Exception as e:
        logger.error(f"❌ Failed to get cloud collections: {e}")
        sys.exit(1)

    # Migrate each collection
    total_points = 0
    for collection_name in COLLECTIONS:
        try:
            points = migrate_collection(cloud_client, local_client, collection_name)
            total_points += points
        except Exception as e:
            logger.error(f"Failed to migrate {collection_name}: {e}")
            continue

    logger.info("=" * 60)
    logger.info(f"✅ Migration Complete!")
    logger.info(f"Total points migrated: {total_points}")
    logger.info(f"Collections migrated: {', '.join(COLLECTIONS)}")
    logger.info("=" * 60)
    logger.info("")
    logger.info("Next steps:")
    logger.info("1. Update .env to use local Qdrant:")
    logger.info("   QDRANT_URL=http://localhost:6333")
    logger.info("2. Remove QDRANT_API_KEY (not needed for local)")
    logger.info("3. Test the application with local Qdrant")


if __name__ == "__main__":
    main()
