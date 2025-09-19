import livekit.plugins.groq as groq
import livekit.plugins.elevenlabs as elevenlabs
from livekit.plugins import silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from livekit.plugins.turn_detector.english import EnglishModel

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
            return elevenlabs.TTS(
                voice_id=tts_config['elevenlabs_voice_id'],
                model=tts_config['elevenlabs_model']
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
       # return MultilingualModel()
        return  EnglishModel()