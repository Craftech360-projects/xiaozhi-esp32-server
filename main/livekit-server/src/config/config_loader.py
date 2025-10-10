from dotenv import load_dotenv
import os
import yaml
from pathlib import Path

class ConfigLoader:
    """Configuration loader for the agent system"""

    @staticmethod
    def load_env():
        """Load environment variables from .env file"""
        load_dotenv(".env")

    @staticmethod
    def get_groq_config():
        """Get Groq configuration from environment variables"""
        return {
            # LLM configuration
            'llm_provider': os.getenv('LLM_PROVIDER', 'groq'),  # groq or ollama
            'llm_model': os.getenv('LLM_MODEL', 'openai/gpt-oss-20b'),
            'llm_temperature': float(os.getenv('LLM_TEMPERATURE', '0.7')),
            'ollama_url': os.getenv('OLLAMA_URL', 'http://localhost:11434'),
            # STT configuration
            'stt_model': os.getenv('STT_MODEL', 'whisper-large-v3-turbo'),
            'stt_language': os.getenv('STT_LANGUAGE', 'en'),
            'stt_provider': os.getenv('STT_PROVIDER', 'groq'),  # groq, deepgram, or local_whisper
            'deepgram_model': os.getenv('DEEPGRAM_MODEL', 'nova-3'),
            'whisper_model': os.getenv('WHISPER_MODEL', 'base'),
            'whisper_device': os.getenv('WHISPER_DEVICE', 'cpu'),
            'whisper_compute_type': os.getenv('WHISPER_COMPUTE_TYPE', 'int8'),
            # TTS configuration
            'tts_model': os.getenv('TTS_MODEL', 'playai-tts'),
            'tts_voice': os.getenv('TTS_VOICE', 'Aaliyah-PlayAI'),
            # Fallback configuration
            'fallback_enabled': os.getenv('FALLBACK_ENABLED', 'false').lower() == 'true',
            'fallback_llm_provider': os.getenv('FALLBACK_LLM_PROVIDER', 'groq'),
            'fallback_llm_model': os.getenv('FALLBACK_LLM_MODEL', 'llama-3.1-8b-instant'),
            'fallback_stt_provider': os.getenv('FALLBACK_STT_PROVIDER', 'groq'),
        }

    @staticmethod
    def get_tts_config():
        """Get TTS configuration from environment variables"""
        return {
            'provider': os.getenv('TTS_PROVIDER', 'edge'),  # groq, elevenlabs, or edge
            'model': os.getenv('TTS_MODEL', 'playai-tts'),
            'voice': os.getenv('TTS_VOICE', 'Aaliyah-PlayAI'),
            # ElevenLabs configuration
            'elevenlabs_voice_id': os.getenv('ELEVENLABS_VOICE_ID', ''),
            'elevenlabs_model': os.getenv('ELEVENLABS_MODEL', 'eleven_turbo_v2_5'),
            # EdgeTTS configuration
            'edge_voice': os.getenv('EDGE_TTS_VOICE', 'en-US-AnaNeural'),
            'edge_rate': os.getenv('EDGE_TTS_RATE', '+0%'),
            'edge_volume': os.getenv('EDGE_TTS_VOLUME', '+0%'),
            'edge_pitch': os.getenv('EDGE_TTS_PITCH', '+0Hz'),
            'edge_sample_rate': int(os.getenv('EDGE_TTS_SAMPLE_RATE', '24000')),
            'edge_channels': int(os.getenv('EDGE_TTS_CHANNELS', '1')),
            # Piper TTS configuration (fast, lightweight, local)
            'piper_voice': os.getenv('PIPER_VOICE', 'en_US-lessac-medium'),
            'piper_sample_rate': int(os.getenv('PIPER_SAMPLE_RATE', '22050')),
            # pyttsx3 configuration (fully local)
            'pyttsx3_rate': int(os.getenv('PYTTSX3_RATE', '150')),
            'pyttsx3_volume': float(os.getenv('PYTTSX3_VOLUME', '1.0')),
            'pyttsx3_voice': int(os.getenv('PYTTSX3_VOICE', '0')),
            # Coqui TTS configuration
            'coqui_model': os.getenv('COQUI_MODEL', 'tts_models/en/ljspeech/tacotron2-DDC'),
            'coqui_use_gpu': os.getenv('COQUI_USE_GPU', 'false').lower() == 'true',
            'coqui_sample_rate': int(os.getenv('COQUI_SAMPLE_RATE', '24000')),
            # Fallback configuration
            'fallback_enabled': os.getenv('TTS_FALLBACK_ENABLED', 'false').lower() == 'true',
        }

    @staticmethod
    def get_livekit_config():
        """Get LiveKit configuration from environment variables"""
        return {
            'api_key': os.getenv('LIVEKIT_API_KEY'),
            'api_secret': os.getenv('LIVEKIT_API_SECRET'),
            'ws_url': os.getenv('LIVEKIT_URL')
        }

    @staticmethod
    def get_agent_config():
        """Get agent configuration from environment variables"""
        return {
            'preemptive_generation': os.getenv('PREEMPTIVE_GENERATION', 'false').lower() == 'true',
            'noise_cancellation': os.getenv('NOISE_CANCELLATION', 'true').lower() == 'true'
        }

    @staticmethod
    def load_yaml_config():
        """Load configuration from config.yaml"""
        config_path = Path(__file__).parent.parent.parent / "config.yaml"
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            print(f"Warning: config.yaml not found at {config_path}")
            return {}
        except Exception as e:
            print(f"Error loading config.yaml: {e}")
            return {}

    @staticmethod
    def should_read_from_api():
        """Check if configuration should be read from API"""
        config = ConfigLoader.load_yaml_config()
        return config.get('read_config_from_api', False)

    @staticmethod
    def get_default_prompt():
        """Get default prompt from config.yaml"""
        config = ConfigLoader.load_yaml_config()
        default_prompt = config.get('default_prompt', '')
        if not default_prompt:
            # Fallback prompt if none configured
            return "You are a helpful AI assistant."
        return default_prompt.strip()

    @staticmethod
    def get_manager_api_config():
        """Get manager API configuration from config.yaml"""
        config = ConfigLoader.load_yaml_config()
        return config.get('manager_api', {})