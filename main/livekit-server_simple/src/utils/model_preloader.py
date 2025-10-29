"""
Background Model Preloader Service
Loads heavy models in the background when the server starts
"""

import logging
import threading
import time
import os
from typing import Optional
from .model_cache import model_cache

logger = logging.getLogger(__name__)

class ModelPreloader:
    """Background service to preload models"""

    def __init__(self):
        self.is_running = False
        self.preload_thread = None
        self.startup_complete = False

    def start_background_loading(self):
        """Start background model loading"""
        if self.is_running:
            logger.info("Model preloader already running")
            return

        self.is_running = True
        self.preload_thread = threading.Thread(
            target=self._preload_all_models,
            daemon=True,
            name="ModelPreloader"
        )
        self.preload_thread.start()
        logger.info("[PRELOAD] Started background model preloader")

    def _preload_all_models(self):
        """Preload only essential models in background"""
        try:
            start_time = time.time()
            logger.info("[PRELOAD] Starting simple background model preloading...")

            # 1. Skip VAD model in background (must be loaded on main thread)
            logger.info("[PRELOAD] Skipping VAD model (will load on main thread)")

            # 2. Skip embedding model (not needed for simple version)
            logger.info("[PRELOAD] Skipping embedding model (not needed for simple version)")

            # 3. Skip Qdrant client (not needed for simple version)
            logger.info("[PRELOAD] Skipping Qdrant client (not needed for simple version)")

            total_time = time.time() - start_time
            logger.info(f"[PRELOAD] Simple background model preloading completed in {total_time:.2f}s")

            # Mark startup as complete
            self.startup_complete = True

            # Display cache stats
            stats = model_cache.get_cache_stats()
            logger.info(f"[PRELOAD] Cache stats: {stats['cache_size']} models loaded: {stats['cached_models']}")

        except Exception as e:
            logger.error(f"[PRELOAD] Background model preloading failed: {e}")
        finally:
            self.is_running = False

    def wait_for_startup(self, timeout: int = 30) -> bool:
        """
        Wait for startup to complete

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            True if startup completed, False if timeout
        """
        start_time = time.time()
        while not self.startup_complete and (time.time() - start_time) < timeout:
            time.sleep(0.1)

        return self.startup_complete

    def is_ready(self) -> bool:
        """Check if preloading is complete"""
        return self.startup_complete

    def get_status(self) -> dict:
        """Get preloader status"""
        return {
            "is_running": self.is_running,
            "startup_complete": self.startup_complete,
            "cache_stats": model_cache.get_cache_stats()
        }

# Global instance
model_preloader = ModelPreloader()