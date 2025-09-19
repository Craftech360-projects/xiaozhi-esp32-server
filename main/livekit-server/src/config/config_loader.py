from dotenv import load_dotenv
import os

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
            'llm_model': os.getenv('LLM_MODEL', 'openai/gpt-oss-20b'),
            'stt_model': os.getenv('STT_MODEL', 'whisper-large-v3-turbo'),
            'tts_model': os.getenv('TTS_MODEL', 'playai-tts'),
            'tts_voice': os.getenv('TTS_VOICE', 'Aaliyah-PlayAI'),
            'stt_language': os.getenv('STT_LANGUAGE', 'en'),
            'stt_provider': os.getenv('STT_PROVIDER', 'groq'),  # groq or deepgram
            'deepgram_model': os.getenv('DEEPGRAM_MODEL', 'nova-3')
        }

    @staticmethod
    def get_tts_config():
        """Get TTS configuration from environment variables"""
        return {
            'provider': os.getenv('TTS_PROVIDER', 'groq'),  # groq or elevenlabs
            'model': os.getenv('TTS_MODEL', 'playai-tts'),
            'voice': os.getenv('TTS_VOICE', 'Aaliyah-PlayAI'),
            'elevenlabs_voice_id': os.getenv('ELEVENLABS_VOICE_ID', ''),
            'elevenlabs_model': os.getenv('ELEVENLABS_MODEL', 'eleven_turbo_v2_5')
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