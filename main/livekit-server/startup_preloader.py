#!/usr/bin/env python3
"""
Startup Model Preloader
Preloads heavy models when the server starts, before any agent sessions
"""

import logging
import time
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dotenv import load_dotenv
from src.utils.model_preloader import model_preloader
from src.utils.model_cache import model_cache

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("startup_preloader")

def main():
    """Main startup preloader"""
    logger.info("[STARTUP] Starting model preloader...")

    # Load environment variables
    load_dotenv(".env")

    # Start background model loading
    model_preloader.start_background_loading()

    # Wait for completion
    logger.info("[STARTUP] Waiting for model preloading to complete...")
    start_time = time.time()

    if model_preloader.wait_for_startup(timeout=60):
        load_time = time.time() - start_time
        logger.info(f"[STARTUP] Model preloading completed in {load_time:.2f}s")

        # Display final stats
        stats = model_cache.get_cache_stats()
        logger.info(f"[STARTUP] Final cache stats: {stats}")

        return True
    else:
        logger.error("[STARTUP] Model preloading timed out")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)