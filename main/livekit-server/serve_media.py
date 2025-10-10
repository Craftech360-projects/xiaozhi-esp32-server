#!/usr/bin/env python3
"""
Simple HTTP server to serve media files (music/stories)
Serves files from the media/ directory on port 8080
"""
import os
import sys
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CORSHTTPRequestHandler(SimpleHTTPRequestHandler):
    """HTTP request handler with CORS support"""

    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def log_message(self, format, *args):
        # Custom logging format
        logger.info("%s - %s" % (self.address_string(), format % args))


def main():
    # Configuration
    PORT = int(os.getenv("MEDIA_SERVER_PORT", "8080"))
    MEDIA_DIR = Path(__file__).parent / "media"

    # Create media directory if it doesn't exist
    MEDIA_DIR.mkdir(exist_ok=True)

    logger.info("=" * 60)
    logger.info("Media File Server")
    logger.info("=" * 60)
    logger.info(f"Serving from: {MEDIA_DIR}")
    logger.info(f"Port: {PORT}")
    logger.info(f"URL: http://localhost:{PORT}")
    logger.info("=" * 60)

    # Check if media directory has files
    music_dir = MEDIA_DIR / "music"
    stories_dir = MEDIA_DIR / "stories"

    if music_dir.exists():
        music_count = sum(1 for _ in music_dir.rglob("*.mp3"))
        logger.info(f"Music files: {music_count}")
    else:
        logger.warning(f"Music directory not found: {music_dir}")
        logger.info(f"Run download script: python scripts/download_media_files.py")

    if stories_dir.exists():
        stories_count = sum(1 for _ in stories_dir.rglob("*.mp3"))
        logger.info(f"Story files: {stories_count}")
    else:
        logger.warning(f"Stories directory not found: {stories_dir}")

    logger.info("=" * 60)
    logger.info("")

    # Change to media directory
    os.chdir(MEDIA_DIR)

    # Create and start server
    try:
        server = HTTPServer(('0.0.0.0', PORT), CORSHTTPRequestHandler)
        logger.info(f"✅ Server started successfully")
        logger.info(f"Listening on http://0.0.0.0:{PORT}")
        logger.info("")
        logger.info("Press Ctrl+C to stop the server")
        logger.info("")

        # Test URLs
        logger.info("Test URLs:")
        logger.info(f"  http://localhost:{PORT}/music/English/")
        logger.info(f"  http://localhost:{PORT}/stories/English/")
        logger.info("")

        server.serve_forever()

    except KeyboardInterrupt:
        logger.info("\n\n⏹  Server stopped by user")
        server.shutdown()
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Failed to start server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
