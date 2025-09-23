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
        self.secret = None
        self._cached_models = None
        self._cache_timestamp = 0
        self.cache_duration = 30  # Cache for 30 seconds

    def update_config(self, base_url: str, secret: str = None):
        """Update the configuration for the manager API"""
        self.base_url = base_url
        self.secret = secret
        logger.info(f"Updated ModelService config: base_url={base_url}, has_secret={bool(secret)}")

    def update_base_url(self, base_url: str):
        """Update the base URL for the manager API (for backward compatibility)"""
        self.base_url = base_url
        logger.info(f"Updated ModelService base URL to: {base_url}")

    def _get_headers(self) -> dict:
        """Get headers for API requests including authentication if configured"""
        headers = {"Content-Type": "application/json"}
        if self.secret:
            headers["Authorization"] = f"Bearer {self.secret}"
        return headers

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
            logger.info(f"Attempting to fetch models from: {endpoint}")

            headers = self._get_headers()
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.get(endpoint, headers=headers, timeout=3)
            )

            logger.info(f"Manager API response: status={response.status_code}")

            if response.status_code == 200:
                data = response.json()
                logger.info(f"Manager API response data: {data}")
                # Check for Manager API success format: code=0 means success
                if data.get('code') == 0 and data.get('data'):
                    return self._process_backend_response(data['data'])
            else:
                logger.warning(f"Manager API returned status {response.status_code}: {response.text}")

            # Fallback: try fetching individual model types
            logger.info("Falling back to individual model fetching...")
            return await self._fetch_individual_models()

        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error to Manager API at {self.base_url}: {e}")
            return None
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout connecting to Manager API at {self.base_url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching from backend at {self.base_url}: {e}")
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
                logger.info(f"Fetching {model_type} models from: {endpoint}?modelType={model_type}")

                headers = self._get_headers()
                response = await loop.run_in_executor(
                    None,
                    lambda: requests.get(endpoint, params=params, headers=headers, timeout=3)
                )

                logger.info(f"Individual model fetch for {model_type}: status={response.status_code}")

                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"Individual model data for {model_type}: {data}")
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
            # Map the model code to actual model name
            mapped_model = self._map_model_code(data['LLM_MODEL'])
            config['LLM_MODEL'] = mapped_model
            logger.info(f"Mapped LLM model: {data['LLM_MODEL']} -> {mapped_model}")

        if 'STT_MODEL' in data:
            # Map the model code to actual model name
            mapped_model = self._map_model_code(data['STT_MODEL'])
            config['STT_MODEL'] = mapped_model
            logger.info(f"Mapped STT model: {data['STT_MODEL']} -> {mapped_model}")

        if 'TTS_MODEL' in data:
            # Map the model code to actual model name
            mapped_model = self._map_model_code(data['TTS_MODEL'])
            config['TTS_MODEL'] = mapped_model
            logger.info(f"Mapped TTS model: {data['TTS_MODEL']} -> {mapped_model}")

        if 'TTS_PROVIDER' in data:
            config['TTS_PROVIDER'] = data['TTS_PROVIDER']

        logger.info(f"Final processed config: {config}")
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
            # Standard model codes
            'GroqLLM': 'llama-3.1-8b-instant',
            'GeminiLLM': 'gemini-1.5-flash',
            'GroqASR': 'whisper-large-v3-turbo',
            'OpenaiASR': 'whisper-1',
            'ElevenLabs': 'eleven_turbo_v2_5',
            'EdgeTTS': 'edge-tts',
            'openai': 'tts-1',
            'gemini': 'gemini-tts',
            # LiveKit-specific model codes
            'LiveKitGroqLLM': 'llama-3.1-8b-instant',
            'LiveKitGroqASR': 'whisper-large-v3-turbo',
            'LiveKitGroqTTS': 'edge-tts',  # Use EdgeTTS instead of Groq TTS
            'GroqTTS': 'edge-tts'  # Force Groq TTS to use EdgeTTS
        }
        return mapping.get(model_code, model_code)

    def _get_tts_provider(self, model_code: str) -> str:
        """Get TTS provider based on model code"""
        if model_code in ['ElevenLabs']:
            return 'elevenlabs'
        elif model_code in ['EdgeTTS', 'LiveKitGroqTTS', 'GroqTTS']:
            return 'edge'  # Force all TTS to use edge provider
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