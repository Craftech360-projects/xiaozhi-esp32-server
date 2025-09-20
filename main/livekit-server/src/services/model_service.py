"""
Model Service - Fetches model configurations from manager-api Java backend
"""

import requests
import asyncio
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class ModelService:
    """Service to fetch model configurations from manager-api backend"""

    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self._cached_models = None
        self._cache_timestamp = 0
        self.cache_duration = 30  # Cache for 30 seconds

    async def get_models(self) -> Dict[str, str]:
        """Get model configurations from backend"""
        current_time = asyncio.get_event_loop().time()

        # Return cached models if still valid
        if (self._cached_models and
            current_time - self._cache_timestamp < self.cache_duration):
            logger.debug("Using cached models")
            return self._cached_models

        # Fetch fresh models from backend
        models = await self._fetch_from_backend()
        if models:
            self._cached_models = models
            self._cache_timestamp = current_time
            logger.info("Successfully fetched and cached models from backend")
            return models

        # Return cached models if available
        if self._cached_models:
            logger.warning("Backend unavailable, using cached models")
            return self._cached_models

        # No fallback - return None to force config_loader to handle the error
        logger.error("Backend unavailable and no cached models - returning None")
        return None

    async def _fetch_from_backend(self) -> Optional[Dict[str, str]]:
        """Fetch models from manager-api backend"""
        try:
            # Try the /config/livekit/default-models endpoint first
            endpoint = f"{self.base_url}/config/livekit/default-models"

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.get(endpoint, timeout=3)
            )

            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('data'):
                    return self._process_backend_response(data['data'])

            # Fallback: try fetching individual model types
            return await self._fetch_individual_models()

        except Exception as e:
            logger.error(f"Error fetching from backend: {e}")
            return None

    async def _fetch_individual_models(self) -> Optional[Dict[str, str]]:
        """Fetch models by individual type from /models/names endpoint"""
        config = {}

        try:
            model_types = [
                ('llm', 'LLM_MODEL'),
                ('tts', 'TTS_MODEL'),
                ('asr', 'STT_MODEL')
            ]

            loop = asyncio.get_event_loop()

            for model_type, config_key in model_types:
                endpoint = f"{self.base_url}/models/names"
                params = {'modelType': model_type}

                response = await loop.run_in_executor(
                    None,
                    lambda: requests.get(endpoint, params=params, timeout=3)
                )

                if response.status_code == 200:
                    data = response.json()
                    if data.get('success') and data.get('data'):
                        models = data['data']

                        # Find Groq model first, then default, then first available
                        selected_model = self._select_best_model(models)
                        if selected_model:
                            mapped_model = self._map_model_code(selected_model.get('modelCode', ''))
                            config[config_key] = mapped_model

                            # Set TTS provider if this is TTS model
                            if model_type == 'tts':
                                config['TTS_PROVIDER'] = self._get_tts_provider(selected_model.get('modelCode', ''))

            return config if config else None

        except Exception as e:
            logger.error(f"Error fetching individual models: {e}")
            return None

    def _process_backend_response(self, data: dict) -> Dict[str, str]:
        """Process response from /config/livekit/default-models endpoint"""
        config = {}

        if 'LLM_MODEL' in data:
            config['LLM_MODEL'] = data['LLM_MODEL']
        if 'STT_MODEL' in data:
            config['STT_MODEL'] = data['STT_MODEL']
        if 'TTS_MODEL' in data:
            config['TTS_MODEL'] = data['TTS_MODEL']
        if 'TTS_PROVIDER' in data:
            config['TTS_PROVIDER'] = data['TTS_PROVIDER']

        return config

    def _select_best_model(self, models: list) -> Optional[dict]:
        """Select best model from list - prioritize Groq, then default, then first"""
        if not models:
            return None

        # First priority: Groq models
        for model in models:
            if 'Groq' in model.get('modelCode', ''):
                return model

        # Second priority: Default models
        for model in models:
            if model.get('isDefault', False):
                return model

        # Third priority: First available
        return models[0]

    def _map_model_code(self, model_code: str) -> str:
        """Map database model code to actual API model name"""
        mapping = {
            'GroqLLM': 'llama-3.1-8b-instant',
            'GeminiLLM': 'gemini-1.5-flash',
            'GroqASR': 'whisper-large-v3-turbo',
            'OpenaiASR': 'whisper-1',
            'ElevenLabs': 'eleven_turbo_v2_5',
            'EdgeTTS': 'edge-tts',
            'openai': 'tts-1',
            'gemini': 'gemini-tts'
        }
        return mapping.get(model_code, model_code)

    def _get_tts_provider(self, model_code: str) -> str:
        """Get TTS provider based on model code"""
        if model_code == 'ElevenLabs':
            return 'elevenlabs'
        elif model_code == 'EdgeTTS':
            return 'edge'
        elif model_code == 'openai':
            return 'openai'
        elif model_code == 'gemini':
            return 'gemini'
        else:
            return 'edge'  # Safe fallback

    def _get_fallback_models(self) -> Dict[str, str]:
        """Fallback models when backend is unavailable"""
        return {
            'LLM_MODEL': 'llama-3.1-8b-instant',
            'STT_MODEL': 'whisper-large-v3-turbo',
            'TTS_MODEL': 'edge-tts',
            'TTS_PROVIDER': 'edge'
        }

    async def get_llm_model(self) -> str:
        """Get LLM model name"""
        models = await self.get_models()
        return models.get('LLM_MODEL', 'llama-3.1-8b-instant')

    async def get_stt_model(self) -> str:
        """Get STT model name"""
        models = await self.get_models()
        return models.get('STT_MODEL', 'whisper-large-v3-turbo')

    async def get_tts_config(self) -> Dict[str, str]:
        """Get TTS configuration"""
        models = await self.get_models()
        return {
            'model': models.get('TTS_MODEL', 'edge-tts'),
            'provider': models.get('TTS_PROVIDER', 'edge')
        }

# Global instance
model_service = ModelService()