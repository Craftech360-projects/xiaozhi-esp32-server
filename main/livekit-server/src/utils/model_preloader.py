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
        """Preload all required models in background"""
        try:
            start_time = time.time()
            logger.info("[PRELOAD] Starting background model preloading...")

            # 1. Skip VAD model in background (must be loaded on main thread)
            logger.info("[PRELOAD] Skipping VAD model (will load on main thread)")

            # 2. Load embedding model (usually slow)
            try:
                embed_start = time.time()
                model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
                embedding = model_cache.get_embedding_model(model_name)
                embed_time = time.time() - embed_start
                if embedding:
                    logger.info(f"[PRELOAD] Embedding model '{model_name}' loaded in {embed_time:.2f}s")
                else:
                    logger.warning(f"[PRELOAD] Embedding model '{model_name}' failed to load")
            except Exception as e:
                logger.error(f"[PRELOAD] Embedding model loading failed: {e}")

            # 3. Load Qdrant client (usually fast)
            try:
                qdrant_start = time.time()
                qdrant = model_cache.get_qdrant_client()
                qdrant_time = time.time() - qdrant_start
                if qdrant:
                    logger.info(f"[PRELOAD] Qdrant client loaded in {qdrant_time:.2f}s")
                else:
                    logger.info("[PRELOAD] Qdrant client not configured (optional)")
            except Exception as e:
                logger.error(f"[PRELOAD] Qdrant client loading failed: {e}")

            # 4. Preload Whisper model
            try:
                whisper_start = time.time()
                self._preload_whisper_model()
                whisper_time = time.time() - whisper_start
                logger.info(f"[PRELOAD] Whisper model checked/downloaded in {whisper_time:.2f}s")
            except Exception as e:
                logger.error(f"[PRELOAD] Whisper model preload failed: {e}")

            # 5. Preload Piper TTS model
            try:
                piper_start = time.time()
                self._preload_piper_model()
                piper_time = time.time() - piper_start
                logger.info(f"[PRELOAD] Piper TTS model checked/downloaded in {piper_time:.2f}s")
            except Exception as e:
                logger.error(f"[PRELOAD] Piper TTS model preload failed: {e}")

            total_time = time.time() - start_time
            logger.info(f"[PRELOAD] Background model preloading completed in {total_time:.2f}s")

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

    def _preload_whisper_model(self):
        """Check and download Whisper model if needed"""
        from pathlib import Path
        import urllib.request

        # Get model configuration
        model_size = os.getenv('WHISPER_MODEL', 'large-v3')
        model_cache_dir = Path(__file__).parent.parent.parent / "model_cache" / "whisper"
        model_cache_dir.mkdir(parents=True, exist_ok=True)

        # Whisper model filename
        model_file = model_cache_dir / f"{model_size}.pt"

        if model_file.exists():
            logger.info(f"[PRELOAD] Whisper model '{model_size}' already cached at {model_file}")
            return

        # Download from OpenAI
        logger.info(f"[PRELOAD] Downloading Whisper model '{model_size}' (~3GB, this may take a while)...")

        # Whisper download URLs
        base_url = "https://openaipublic.azureedge.net/main/whisper/models/"
        model_urls = {
            "tiny.en": base_url + "d3dd57d32accea0b295c96e26691aa14d8822fac7d9d27d5dc00b4ca2826dd03/tiny.en.pt",
            "tiny": base_url + "65147644a518d12f04e32d6f3b26facc3f8dd46e5390956a9424a650c0ce22b9/tiny.pt",
            "base.en": base_url + "25a8566e1d0c1e2231d1c762132cd20e0f96a85d16145c3a00adf5d1ac670ead/base.en.pt",
            "base": base_url + "ed3a0b6b1c0edf879ad9b11b1af5a0e6ab5db9205f891f668f8b0e6c6326e34e/base.pt",
            "small.en": base_url + "f953ad0fd29cacd07d5a9eda5624af0f6bcf2258be67c92b79389873d91e0872/small.en.pt",
            "small": base_url + "9ecf779972d90ba49c06d968637d720dd632c55bbf19d441fb42bf17a411e794/small.pt",
            "medium.en": base_url + "d7440d1dc186f76616474e0ff0b3b6b879abc9d1a4926b7adfa41db2d497ab4f/medium.en.pt",
            "medium": base_url + "345ae4da62f9b3d59415adc60127b97c714f32e89e936602e85993674d08dcb1/medium.pt",
            "large-v1": base_url + "e4b87e7e0bf463eb8e6956e646f1e277e901512310def2c24bf0e11bd3c28e9a/large-v1.pt",
            "large-v2": base_url + "81f7c96c852ee8fc832187b0132e569d6c3065a3252ed18e56effd0b6a73e524/large-v2.pt",
            "large-v3": base_url + "e5b1a55b89c1367dacf97e3e19bfd829a01529dbfdeefa8caeb59b3f1b81dadb/large-v3.pt",
            "large": base_url + "e5b1a55b89c1367dacf97e3e19bfd829a01529dbfdeefa8caeb59b3f1b81dadb/large-v3.pt",
        }

        if model_size not in model_urls:
            logger.warning(f"[PRELOAD] Unknown Whisper model size: {model_size}, skipping download")
            return

        url = model_urls[model_size]

        try:
            urllib.request.urlretrieve(url, str(model_file))
            logger.info(f"[PRELOAD] Whisper model '{model_size}' downloaded successfully")
        except Exception as e:
            logger.error(f"[PRELOAD] Failed to download Whisper model: {e}")

    def _preload_piper_model(self):
        """Check and download Piper TTS model if needed"""
        from pathlib import Path
        import urllib.request

        # Get model configuration
        voice_name = os.getenv('PIPER_VOICE', 'en_US-lessac-medium')
        models_dir = Path(__file__).parent.parent.parent / "model_cache" / "piper" / "voices"
        models_dir.mkdir(parents=True, exist_ok=True)

        model_file = models_dir / f"{voice_name}.onnx"
        config_file = models_dir / f"{voice_name}.onnx.json"

        if model_file.exists() and config_file.exists():
            logger.info(f"[PRELOAD] Piper model '{voice_name}' already cached at {models_dir}")
            return

        # Download from HuggingFace
        logger.info(f"[PRELOAD] Downloading Piper model '{voice_name}' (~60MB)...")

        base_url = "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/"

        files = [
            (f"{voice_name}.onnx", model_file),
            (f"{voice_name}.onnx.json", config_file),
        ]

        try:
            for filename, filepath in files:
                if not filepath.exists():
                    url = base_url + filename
                    urllib.request.urlretrieve(url, str(filepath))
                    logger.info(f"[PRELOAD] Downloaded {filename}")

            logger.info(f"[PRELOAD] Piper model '{voice_name}' downloaded successfully")
        except Exception as e:
            logger.error(f"[PRELOAD] Failed to download Piper model: {e}")

# Global instance
model_preloader = ModelPreloader()