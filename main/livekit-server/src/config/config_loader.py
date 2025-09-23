"""
Configuration Loader for Xiaozhi ESP32 LiveKit Agent
Supports both YAML config and API-driven model fetching from manager-api backend
"""

import os
import yaml
import asyncio
import logging
from typing import Dict, Any, Optional
from ..services.model_service import model_service

logger = logging.getLogger(__name__)

class ConfigLoader:
    """Configuration loader that supports YAML and API-driven configuration"""

    _config = None
    _config_file = "config.yaml"

    @classmethod
    def _load_yaml_config(cls) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        if cls._config is not None:
            return cls._config

        config_path = cls._config_file
        if not os.path.exists(config_path):
            logger.error(f"Configuration file {config_path} not found")
            return {}

        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                cls._config = yaml.safe_load(file) or {}
                logger.info(f"Configuration loaded from {config_path}")
                return cls._config
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return {}

    @classmethod
    async def get_groq_config(cls) -> Dict[str, str]:
        """Get model configuration - ONLY from manager-api backend"""
        config = cls._load_yaml_config()

        # FORCE API configuration - no fallbacks allowed
        if not config.get('read_config_from_api', False):
            raise RuntimeError("read_config_from_api is disabled. Backend integration required!")

        # Initialize model_service with the correct URL and secret from config
        manager_api_config = config.get('manager_api', {})
        manager_api_url = manager_api_config.get('url', 'http://localhost:8080')
        manager_api_secret = manager_api_config.get('secret')
        model_service.update_config(manager_api_url, manager_api_secret)

        logger.info("Fetching model configuration from manager-api backend...")
        backend_models = await model_service.get_models()

        if not backend_models:
            logger.warning("Failed to fetch models from manager-api backend, using fallback configuration")
            # Use fallback configuration from config.yaml
            config = ConfigLoader._load_yaml_config()
            return {
                'llm_model': config['models']['llm']['model'],
                'stt_model': config['models']['stt']['model'],
                'stt_language': config['models']['stt']['language'],
                'tts_model': config['models']['tts']['model'],
                'tts_voice': config['models']['tts'].get('voice', 'default')
            }

        result = {
            'llm_model': backend_models.get('LLM_MODEL'),
            'stt_model': backend_models.get('STT_MODEL'),
            'tts_model': backend_models.get('TTS_MODEL'),
            'tts_voice': 'Aaliyah-PlayAI',  # Keep some UI defaults
            'stt_language': 'en',
            'stt_provider': 'groq',
            'deepgram_model': 'nova-3'
        }

        # Validate that we got required models
        if not result['llm_model'] or not result['stt_model'] or not result['tts_model']:
            raise RuntimeError(f"Backend returned incomplete model configuration: {backend_models}")

        logger.info(f"Successfully loaded models from backend: {result}")
        return result

    @classmethod
    async def get_tts_config(cls) -> Dict[str, str]:
        """Get TTS configuration - from API if enabled, otherwise from YAML"""
        config = cls._load_yaml_config()

        # Check if we should read from API
        if config.get('read_config_from_api', False):
            try:
                # Ensure model_service has the correct URL and secret
                manager_api_config = config.get('manager_api', {})
                manager_api_url = manager_api_config.get('url', 'http://localhost:8080')
                manager_api_secret = manager_api_config.get('secret')
                model_service.update_config(manager_api_url, manager_api_secret)

                tts_config = await model_service.get_tts_config()
                if tts_config:
                    logger.info(f"Successfully loaded TTS config from API: {tts_config}")
                    return {
                        'provider': tts_config.get('provider', 'edge'),
                        'model': tts_config.get('model', 'edge-tts'),
                        'voice': config.get('models', {}).get('tts', {}).get('voice', 'Aaliyah-PlayAI'),
                        'elevenlabs_voice_id': config.get('api_keys', {}).get('elevenlabs_voice_id', ''),
                        'elevenlabs_model': 'eleven_turbo_v2_5'
                    }
            except Exception as e:
                logger.error(f"Failed to fetch TTS config from API: {e}")

        # Fallback to YAML configuration
        tts_config = config.get('models', {}).get('tts', {})
        return {
            'provider': tts_config.get('provider', 'edge'),
            'model': tts_config.get('model', 'edge-tts'),
            'voice': tts_config.get('voice', 'Aaliyah-PlayAI'),
            'elevenlabs_voice_id': config.get('api_keys', {}).get('elevenlabs_voice_id', ''),
            'elevenlabs_model': 'eleven_turbo_v2_5'
        }

    @classmethod
    def get_livekit_config(cls) -> Dict[str, str]:
        """Get LiveKit configuration from YAML"""
        config = cls._load_yaml_config()
        livekit_config = config.get('livekit', {})

        return {
            'api_key': livekit_config.get('api_key', 'devkey'),
            'api_secret': livekit_config.get('api_secret', 'secret'),
            'ws_url': livekit_config.get('url', 'ws://localhost:7880')
        }

    @classmethod
    def get_agent_config(cls) -> Dict[str, bool]:
        """Get agent configuration from YAML"""
        config = cls._load_yaml_config()
        agent_config = config.get('agent', {})

        return {
            'preemptive_generation': agent_config.get('preemptive_generation', False),
            'noise_cancellation': agent_config.get('noise_cancellation', False)
        }

    @classmethod
    def get_api_keys(cls) -> Dict[str, str]:
        """Get API keys from YAML configuration"""
        config = cls._load_yaml_config()
        return config.get('api_keys', {})

    @classmethod
    def get_redis_config(cls) -> Dict[str, str]:
        """Get Redis configuration from YAML"""
        config = cls._load_yaml_config()
        redis_config = config.get('redis', {})

        return {
            'url': redis_config.get('url', ''),
            'password': redis_config.get('password', '')
        }

    @classmethod
    def get_mqtt_config(cls) -> Dict[str, Any]:
        """Get MQTT configuration from YAML"""
        config = cls._load_yaml_config()
        return config.get('mqtt', {})

    @classmethod
    def get_qdrant_config(cls) -> Dict[str, str]:
        """Get Qdrant configuration from YAML"""
        config = cls._load_yaml_config()
        return config.get('qdrant', {})

    @classmethod
    def is_api_config_enabled(cls) -> bool:
        """Check if API configuration is enabled"""
        config = cls._load_yaml_config()
        return config.get('read_config_from_api', False)

    @classmethod
    def get_manager_api_secret(cls) -> Optional[str]:
        """Get manager-api server secret from database"""
        config = cls._load_yaml_config()
        db_config = config.get('database', {})

        try:
            import pymysql

            connection = pymysql.connect(
                host=db_config.get('host', 'localhost'),
                port=db_config.get('port', 3307),
                user=db_config.get('user', 'manager'),
                password=db_config.get('password', 'managerpassword'),
                database=db_config.get('database', 'manager_api'),
                charset=db_config.get('charset', 'utf8mb4')
            )

            with connection.cursor() as cursor:
                cursor.execute("SELECT param_value FROM sys_params WHERE param_code = 'server.secret'")
                result = cursor.fetchone()
                if result:
                    return result[0]

            connection.close()

        except Exception as e:
            logger.error(f"Failed to fetch server secret from database: {e}")

        return None