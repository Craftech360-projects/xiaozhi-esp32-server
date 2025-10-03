"""
Persistent Model Cache for Heavy ML Models
Loads models once and reuses them across agent sessions
"""

import os
import logging
import threading
import time
from typing import Optional, Dict, Any
from pathlib import Path
import pickle

logger = logging.getLogger(__name__)

class ModelCache:
    """Singleton cache for heavy ML models"""
    _instance = None
    _lock = threading.Lock()
    _models: Dict[str, Any] = {}
    _loading_status: Dict[str, bool] = {}
    _cache_dir = "model_cache"

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._initialized = True
            self._ensure_cache_dir()
            logger.info("[CACHE] ModelCache singleton initialized")

    def _ensure_cache_dir(self):
        """Ensure cache directory exists"""
        Path(self._cache_dir).mkdir(exist_ok=True)

    def _get_cache_path(self, model_key: str) -> Path:
        """Get cache file path for a model"""
        return Path(self._cache_dir) / f"{model_key}.pkl"

    def get_model(self, model_key: str, loader_func=None, *args, **kwargs) -> Optional[Any]:
        """
        Get model from cache or load it if not cached

        Args:
            model_key: Unique identifier for the model
            loader_func: Function to load the model if not cached
            *args, **kwargs: Arguments for loader function
        """
        # Check if model is already in memory
        if model_key in self._models:
            logger.info(f"[CACHE] Using cached model: {model_key}")
            return self._models[model_key]

        # Check if another thread is loading this model
        if model_key in self._loading_status:
            logger.info(f"[CACHE] Waiting for model to finish loading: {model_key}")
            # Wait for loading to complete (with timeout)
            start_time = time.time()
            while model_key in self._loading_status and time.time() - start_time < 30:
                time.sleep(0.1)

            # Check if model is now available
            if model_key in self._models:
                return self._models[model_key]

        # Try to load from disk cache first
        cached_model = self._load_from_disk(model_key)
        if cached_model is not None:
            self._models[model_key] = cached_model
            logger.info(f"[CACHE] Loaded model from disk cache: {model_key}")
            return cached_model

        # Load model using provided function
        if loader_func is None:
            logger.warning(f"No loader function provided for model: {model_key}")
            return None

        with self._lock:
            # Double-check pattern
            if model_key in self._models:
                return self._models[model_key]

            # Mark as loading
            self._loading_status[model_key] = True

            try:
                logger.info(f"[CACHE] Loading model: {model_key}")
                start_time = time.time()

                model = loader_func(*args, **kwargs)

                load_time = time.time() - start_time
                logger.info(f"[CACHE] Model loaded in {load_time:.2f}s: {model_key}")

                # Cache in memory
                self._models[model_key] = model

                # Cache to disk (async, don't block)
                threading.Thread(
                    target=self._save_to_disk,
                    args=(model_key, model),
                    daemon=True
                ).start()

                return model

            except Exception as e:
                logger.error(f"[CACHE] Failed to load model {model_key}: {e}")
                return None
            finally:
                # Remove loading status
                self._loading_status.pop(model_key, None)

    def _load_from_disk(self, model_key: str) -> Optional[Any]:
        """Load model from disk cache"""
        try:
            cache_path = self._get_cache_path(model_key)
            if cache_path.exists():
                logger.info(f"[CACHE] Loading model from disk cache: {model_key}")
                with open(cache_path, 'rb') as f:
                    return pickle.load(f)
        except Exception as e:
            logger.warning(f"Failed to load model from disk cache {model_key}: {e}")
        return None

    def _save_to_disk(self, model_key: str, model: Any):
        """Save model to disk cache (background thread)"""
        # Skip certain models that can't be pickled
        if model_key in ['qdrant_client', 'vad_model']:
            logger.debug(f"[CACHE] Skipping disk cache for {model_key} (not serializable)")
            return

        try:
            cache_path = self._get_cache_path(model_key)
            logger.info(f"[CACHE] Saving model to disk cache: {model_key}")
            with open(cache_path, 'wb') as f:
                pickle.dump(model, f)
            logger.info(f"[CACHE] Model saved to disk: {model_key}")
        except Exception as e:
            logger.warning(f"Failed to save model to disk {model_key}: {e}")

    def preload_models(self):
        """Preload all required models in background"""
        def _background_loader():
            try:
                # Load VAD model
                self.get_vad_model()

                # Load embedding model
                self.get_embedding_model()

                # Load Qdrant client
                self.get_qdrant_client()

                logger.info("[PRELOAD] All models preloaded successfully")

            except Exception as e:
                logger.error(f"Background model loading failed: {e}")

        # Start background loading
        threading.Thread(target=_background_loader, daemon=True).start()
        logger.info("[PRELOAD] Started background model preloading")

    def get_vad_model(self):
        """Get VAD model with caching - must be called from main thread"""
        # Check if already cached
        if "vad_model" in self._models:
            return self._models["vad_model"]

        # VAD model must be loaded on main thread, not in background
        # This is a limitation of the Silero VAD plugin
        try:
            import threading
            if threading.current_thread() != threading.main_thread():
                logger.warning("[CACHE] VAD model must be loaded on main thread, deferring...")
                return None

            # Load VAD directly to avoid circular dependency with ProviderFactory
            from livekit.plugins import silero
            logger.info("[CACHE] Loading VAD model on main thread...")
            vad = silero.VAD.load()
            self._models["vad_model"] = vad
            logger.info("[CACHE] VAD model loaded and cached")
            return vad
        except Exception as e:
            logger.error(f"[CACHE] Failed to load VAD model: {e}")
            return None

    def get_embedding_model(self, model_name: Optional[str] = None):
        """Get embedding model with caching"""
        if model_name is None:
            model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

        model_key = f"embedding_{model_name}"

        def load_embedding():
            from sentence_transformers import SentenceTransformer
            return SentenceTransformer(model_name)

        return self.get_model(model_key, load_embedding)

    def get_qdrant_client(self):
        """Get Qdrant client with caching"""
        def load_qdrant():
            from qdrant_client import QdrantClient
            qdrant_url = os.getenv("QDRANT_URL", "")
            qdrant_api_key = os.getenv("QDRANT_API_KEY", "")

            if not qdrant_url or not qdrant_api_key:
                return None

            return QdrantClient(
                url=qdrant_url,
                api_key=qdrant_api_key,
                timeout=10
            )

        return self.get_model("qdrant_client", load_qdrant)

    def clear_cache(self):
        """Clear all cached models (for testing/debugging)"""
        with self._lock:
            self._models.clear()
            logger.info("[CACHE] Model cache cleared")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "cached_models": list(self._models.keys()),
            "loading_models": list(self._loading_status.keys()),
            "cache_size": len(self._models)
        }

    def cache_service(self, service_key: str, service_instance):
        """Cache a service instance"""
        self._models[service_key] = service_instance
        logger.info(f"[CACHE] Cached service: {service_key}")

    def get_cached_service(self, service_key: str):
        """Get cached service instance"""
        return self._models.get(service_key)

# Global instance
model_cache = ModelCache()