#!/usr/bin/env python3
"""
Media File Downloader
Downloads music and story files from cloud storage based on Qdrant database index

IMPORTANT: Run this script on the media server (192.168.1.99) to download files

Quick Start:
    # Default - downloads ALL languages to /var/www/html
    python3 download_media_files.py

    # Download only English music (saves space)
    LANGUAGE_FILTER=English python3 download_media_files.py

    # Download to custom location
    MEDIA_ROOT=/opt/media python3 download_media_files.py

    # Connect to remote Qdrant
    QDRANT_URL=http://192.168.1.2:6333 python3 download_media_files.py

Environment Variables:
    QDRANT_URL          Qdrant server URL (default: http://localhost:6333)
    MEDIA_ROOT          Destination directory (default: /var/www/html)
    LANGUAGE_FILTER     Comma-separated languages to download (default: English)
                        Set to empty string to download all: LANGUAGE_FILTER=""
    USE_CDN             Use CloudFront CDN (default: true)

See README_MEDIA_DOWNLOAD.md for full documentation
"""
import os
import sys
import urllib.request
import urllib.parse
from pathlib import Path
from qdrant_client import QdrantClient
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTIONS = ["xiaozhi_music", "xiaozhi_stories"]

# AWS S3 Configuration
S3_BASE_URL = os.getenv(
    "S3_BASE_URL",
    "https://cheeko-audio-files.s3.us-east-1.amazonaws.com"
)
CLOUDFRONT_DOMAIN = os.getenv("CLOUDFRONT_DOMAIN", "dbtnllz9fcr1z.cloudfront.net")
USE_CDN = os.getenv("USE_CDN", "true").lower() == "true"

# Media storage path - default to livekit-server/media directory
# This allows serving files directly from the LiveKit server
default_media_root = Path(__file__).parent.parent / "media"
MEDIA_ROOT = Path(os.getenv("MEDIA_ROOT", str(default_media_root)))

# Language filter - only download specific languages to save space
# Set to empty list to download all languages: LANGUAGE_FILTER = []
LANGUAGE_FILTER = os.getenv("LANGUAGE_FILTER", "English").split(",")
if LANGUAGE_FILTER and LANGUAGE_FILTER[0]:
    LANGUAGE_FILTER = [lang.strip() for lang in LANGUAGE_FILTER]
else:
    LANGUAGE_FILTER = []  # Empty means download all


def get_file_url(filename: str, language: str, collection_type: str) -> str:
    """
    Generate the URL to download a media file

    Args:
        filename: Name of the file
        language: Language folder
        collection_type: 'music' or 'stories'

    Returns:
        Full URL to download the file
    """
    # Determine folder based on collection type
    folder = collection_type.replace("xiaozhi_", "")  # xiaozhi_music -> music

    # Build path
    audio_path = f"{folder}/{language}/{filename}"
    encoded_path = urllib.parse.quote(audio_path)

    # Use CDN or S3 base URL
    if USE_CDN and CLOUDFRONT_DOMAIN:
        return f"https://{CLOUDFRONT_DOMAIN}/{encoded_path}"
    else:
        return f"{S3_BASE_URL}/{encoded_path}"


def download_file(url: str, local_path: Path) -> bool:
    """
    Download a file from URL to local path

    Args:
        url: URL to download from
        local_path: Local path to save file

    Returns:
        True if successful, False otherwise
    """
    try:
        # Create parent directory if it doesn't exist
        local_path.parent.mkdir(parents=True, exist_ok=True)

        # Download file
        logger.info(f"Downloading: {url}")
        urllib.request.urlretrieve(url, str(local_path))

        # Check if file was downloaded
        if local_path.exists() and local_path.stat().st_size > 0:
            file_size_mb = local_path.stat().st_size / (1024 * 1024)
            logger.info(f"✅ Downloaded: {local_path.name} ({file_size_mb:.2f} MB)")
            return True
        else:
            logger.error(f"❌ Download failed: File is empty or doesn't exist")
            return False

    except Exception as e:
        logger.error(f"❌ Error downloading {url}: {e}")
        return False


def download_collection_files(client: QdrantClient, collection_name: str) -> dict:
    """
    Download all media files for a collection

    Args:
        client: Qdrant client
        collection_name: Name of collection to download files for

    Returns:
        Dictionary with download statistics
    """
    logger.info(f"\n{'=' * 60}")
    logger.info(f"Processing collection: {collection_name}")
    logger.info(f"{'=' * 60}")

    stats = {
        "total": 0,
        "downloaded": 0,
        "skipped": 0,
        "failed": 0,
        "languages": set()
    }

    # Determine collection type (music or stories)
    collection_type = collection_name  # xiaozhi_music or xiaozhi_stories

    try:
        # Get all points from collection
        offset = None

        while True:
            # Scroll through points
            result = client.scroll(
                collection_name=collection_name,
                limit=100,
                offset=offset,
                with_payload=True,
                with_vectors=False,
            )

            points = result[0]
            next_offset = result[1]

            if not points:
                break

            # Process each point
            for point in points:
                payload = point.payload
                filename = payload.get("filename")
                language = payload.get("language")
                title = payload.get("title", "Unknown")

                if not filename or not language:
                    logger.warning(f"⚠️ Skipping entry '{title}': Missing filename or language")
                    stats["skipped"] += 1
                    continue

                # Apply language filter if specified
                if LANGUAGE_FILTER and language not in LANGUAGE_FILTER:
                    logger.debug(f"⏭️  Skipping '{title}': Language '{language}' not in filter {LANGUAGE_FILTER}")
                    stats["skipped"] += 1
                    continue

                stats["total"] += 1
                stats["languages"].add(language)

                # Build local path
                folder_type = collection_type.replace("xiaozhi_", "")  # music or stories
                local_path = MEDIA_ROOT / folder_type / language / filename

                # Check if file already exists
                if local_path.exists() and local_path.stat().st_size > 0:
                    file_size_mb = local_path.stat().st_size / (1024 * 1024)
                    logger.info(f"⏭️  Skipping (already exists): {title} ({file_size_mb:.2f} MB)")
                    stats["skipped"] += 1
                    continue

                # Generate download URL
                url = get_file_url(filename, language, collection_type)

                # Download file
                logger.info(f"📥 Downloading: {title} ({language})")
                success = download_file(url, local_path)

                if success:
                    stats["downloaded"] += 1
                else:
                    stats["failed"] += 1

            # Check if we're done
            if next_offset is None:
                break

            offset = next_offset

        return stats

    except Exception as e:
        logger.error(f"❌ Error processing collection '{collection_name}': {e}")
        raise


def main():
    """Main download function"""
    logger.info("=" * 60)
    logger.info("Media File Downloader")
    logger.info("=" * 60)
    logger.info(f"Source: {'CloudFront CDN' if USE_CDN else 'S3 Direct'}")
    logger.info(f"Destination: {MEDIA_ROOT}")
    if LANGUAGE_FILTER:
        logger.info(f"Language Filter: {', '.join(LANGUAGE_FILTER)}")
    else:
        logger.info(f"Language Filter: None (downloading all languages)")
    logger.info("")

    # Check if destination exists and is writable
    if not MEDIA_ROOT.exists():
        logger.warning(f"⚠️  Destination {MEDIA_ROOT} does not exist. Creating it...")
        try:
            MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
            logger.info(f"✅ Created directory: {MEDIA_ROOT}")
        except Exception as e:
            logger.error(f"❌ Failed to create directory: {e}")
            logger.error("Please create the directory manually or run with sudo/admin privileges")
            sys.exit(1)

    # Test write permissions
    test_file = MEDIA_ROOT / ".test_write"
    try:
        test_file.touch()
        test_file.unlink()
        logger.info(f"✅ Write permissions verified")
    except Exception as e:
        logger.error(f"❌ No write permissions to {MEDIA_ROOT}: {e}")
        logger.error("Please run with appropriate permissions (sudo/admin)")
        sys.exit(1)

    # Connect to Qdrant
    logger.info(f"Connecting to Qdrant: {QDRANT_URL}")
    try:
        client = QdrantClient(url=QDRANT_URL)
        logger.info("✅ Connected to Qdrant")
    except Exception as e:
        logger.error(f"❌ Failed to connect to Qdrant: {e}")
        logger.error("Make sure Qdrant is running: docker-compose up -d qdrant")
        sys.exit(1)

    # Download files for each collection
    total_stats = {
        "total": 0,
        "downloaded": 0,
        "skipped": 0,
        "failed": 0,
        "languages": set()
    }

    for collection_name in COLLECTIONS:
        try:
            stats = download_collection_files(client, collection_name)

            # Merge stats
            total_stats["total"] += stats["total"]
            total_stats["downloaded"] += stats["downloaded"]
            total_stats["skipped"] += stats["skipped"]
            total_stats["failed"] += stats["failed"]
            total_stats["languages"].update(stats["languages"])

            # Print collection summary
            logger.info(f"\n📊 {collection_name} Summary:")
            logger.info(f"   Total files: {stats['total']}")
            logger.info(f"   Downloaded: {stats['downloaded']}")
            logger.info(f"   Skipped (already exist): {stats['skipped']}")
            logger.info(f"   Failed: {stats['failed']}")
            logger.info(f"   Languages: {', '.join(sorted(stats['languages']))}")

        except Exception as e:
            logger.error(f"Failed to process {collection_name}: {e}")
            continue

    # Print overall summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 OVERALL SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total files indexed: {total_stats['total']}")
    logger.info(f"Successfully downloaded: {total_stats['downloaded']}")
    logger.info(f"Skipped (already exist): {total_stats['skipped']}")
    logger.info(f"Failed: {total_stats['failed']}")
    logger.info(f"Languages found: {', '.join(sorted(total_stats['languages']))}")
    logger.info(f"Files saved to: {MEDIA_ROOT}")
    logger.info("=" * 60)

    if total_stats["downloaded"] > 0:
        logger.info("\n✅ Download complete!")
        logger.info("\nNext steps:")
        logger.info(f"1. Verify files in: {MEDIA_ROOT}")
        logger.info(f"2. Ensure HTTP server is running and serving from: {MEDIA_ROOT}")
        logger.info(f"3. Test access: curl http://localhost:8080/music/English/[filename].mp3")
        logger.info(f"4. Make sure LOCAL_MEDIA_URL in .env points to the correct server")
        logger.info("\nExample HTTP server setup (if not already running):")
        logger.info(f"   # Using Python:")
        logger.info(f"   cd {MEDIA_ROOT} && python3 -m http.server 8080")
        logger.info(f"   # Using Node.js:")
        logger.info(f"   cd {MEDIA_ROOT} && npx http-server -p 8080 --cors")
        logger.info(f"   # Using Nginx (recommended for production):")
        logger.info(f"   Configure nginx to serve {MEDIA_ROOT} on port 8080")

    # Exit with error if all downloads failed
    if total_stats["failed"] > 0 and total_stats["downloaded"] == 0:
        logger.error("\n❌ All downloads failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
