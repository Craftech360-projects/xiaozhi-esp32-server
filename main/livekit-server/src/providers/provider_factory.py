import livekit.plugins.groq as groq
import livekit.plugins.elevenlabs as elevenlabs
import livekit.plugins.deepgram as deepgram
from livekit.plugins import silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from livekit.plugins.turn_detector.english import EnglishModel

# Import our custom EdgeTTS provider
from .edge_tts_provider import EdgeTTS

class ProviderFactory:
    """Factory class for creating AI service providers"""

    @staticmethod
    def create_llm(config):
        """Create LLM provider based on configuration"""
        return groq.LLM(model=config['llm_model'])

    @staticmethod
    def create_stt(config):
        """Create Speech-to-Text provider based on configuration"""
        provider = config.get('stt_provider', 'groq').lower()

        if provider == 'deepgram':
            return deepgram.STT(
                model=config.get('deepgram_model', 'nova-3'),
                language=config['stt_language']
            )
        else:
            # Default to Groq
            return groq.STT(
                model=config['stt_model'],
                language=config['stt_language']
            )

    @staticmethod
    def create_tts(groq_config, tts_config):
        """Create Text-to-Speech provider based on configuration"""
        provider = tts_config.get('provider', 'groq').lower()

        if provider == 'elevenlabs':
            return elevenlabs.TTS(
                voice_id=tts_config['elevenlabs_voice_id'],
                model=tts_config['elevenlabs_model']
            )
        elif provider == 'edge':
            return EdgeTTS(
                voice=tts_config.get('edge_voice', 'en-US-AvaNeural'),
                rate=tts_config.get('edge_rate', '+0%'),
                volume=tts_config.get('edge_volume', '+0%'),
                pitch=tts_config.get('edge_pitch', '+0Hz'),
                sample_rate=tts_config.get('edge_sample_rate', 24000),
                channels=tts_config.get('edge_channels', 1)
            )
        else:
            # Default to Groq
            return groq.TTS(
                model=groq_config['tts_model'],
                voice=groq_config['tts_voice']
            )

    @staticmethod
    def create_vad():
        """Create Voice Activity Detection provider"""
        return silero.VAD.load()

    @staticmethod
    def create_turn_detection():
        """Create turn detection model"""
        # Disable turn detection to avoid model download timeouts
        return None