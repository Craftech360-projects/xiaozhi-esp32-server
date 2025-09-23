"""
Utils module initialization with automatic model preloading
"""

import os
import logging

logger = logging.getLogger(__name__)

# Auto-start model preloading when utils module is imported
# This ensures models start loading as soon as the server starts
def _auto_start_preloading():
    """Auto-start model preloading if enabled"""
    try:
        # Check if auto-preloading is enabled (default: true)
        auto_preload = os.getenv("AUTO_PRELOAD_MODELS", "true").lower() == "true"

        if auto_preload:
            from .model_preloader import model_preloader
            if not model_preloader.is_running and not model_preloader.is_ready():
                model_preloader.start_background_loading()
                logger.info("[PRELOAD] Auto-started model preloading")

    except Exception as e:
        logger.warning(f"Auto-preloading failed: {e}")

# Start preloading when module is imported
_auto_start_preloading()