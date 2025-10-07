import livekit.plugins.groq as groq
import livekit.plugins.elevenlabs as elevenlabs
from livekit.plugins import silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from livekit.plugins.turn_detector.english import EnglishModel
from .tts_wrapper import wrap_tts_with_sanitizer

class ProviderFactory:
    """Factory class for creating AI service providers"""

    @staticmethod
    def create_llm(config):
        """Create LLM provider based on configuration"""
        return groq.LLM(model=config['llm_model'])

    @staticmethod
    def create_stt(config):
        """Create Speech-to-Text provider based on configuration"""
        return groq.STT(
            model=config['stt_model'],
            language=config['stt_language']
        )

    @staticmethod
    def create_tts(groq_config, tts_config):
        """Create Text-to-Speech provider based on configuration"""
        provider = tts_config.get('provider', 'groq').lower()

        if provider == 'elevenlabs':
            base_tts = elevenlabs.TTS(
                voice_id=tts_config['elevenlabs_voice_id'],
                model=tts_config['elevenlabs_model']
            )
        else:
            # Default to Groq
            base_tts = groq.TTS(
                model=groq_config['tts_model'],
                voice=groq_config['tts_voice']
            )

        # Wrap the TTS with sanitization for better speech output
        return wrap_tts_with_sanitizer(base_tts, child_friendly=True)

    @staticmethod
    def create_vad():
        """Create Voice Activity Detection provider"""
        return silero.VAD.load()

    @staticmethod
    def create_turn_detection():
        """Create turn detection model"""
        # return MultilingualModel()
        from livekit.plugins.turn_detector.english import EnglishModel
        return EnglishModel()