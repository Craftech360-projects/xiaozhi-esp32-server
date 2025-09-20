import livekit.plugins.groq as groq
import livekit.plugins.elevenlabs as elevenlabs
import livekit.plugins.deepgram as deepgram
import livekit.plugins.openai as openai
from livekit.plugins import silero
try:
    from livekit.plugins import azure
except ImportError:
    azure = None
try:
    # Edge TTS is available as a standalone package
    import edge_tts
    HAS_EDGE_TTS = True
except ImportError:
    HAS_EDGE_TTS = False
# from livekit.plugins.turn_detector.multilingual import MultilingualModel
# from livekit.plugins.turn_detector.english import EnglishModel

class ProviderFactory:
    """Factory class for creating AI service providers"""

    @staticmethod
    def create_llm(config):
        """Create LLM provider based on configuration"""
        from ..config.config_loader import ConfigLoader
        api_keys = ConfigLoader.get_api_keys()
        return groq.LLM(model=config['llm_model'], api_key=api_keys.get('groq', ''))

    @staticmethod
    def create_stt(config):
        """Create Speech-to-Text provider based on configuration"""
        from ..config.config_loader import ConfigLoader
        api_keys = ConfigLoader.get_api_keys()
        provider = config.get('stt_provider', 'groq').lower()

        if provider == 'deepgram':
            return deepgram.STT(
                model=config.get('deepgram_model', 'nova-3'),
                language=config['stt_language'],
                api_key=api_keys.get('deepgram', '')
            )
        else:
            # Default to Groq
            return groq.STT(
                model=config['stt_model'],
                language=config['stt_language'],
                api_key=api_keys.get('groq', '')
            )

    @staticmethod
    def create_tts(groq_config, tts_config):
        """Create Text-to-Speech provider based on configuration"""
        provider = tts_config.get('provider', 'groq').lower()

        # Get API keys from config
        from ..config.config_loader import ConfigLoader
        api_keys = ConfigLoader.get_api_keys()

        if provider == 'elevenlabs':
            return elevenlabs.TTS(
                voice_id=tts_config['elevenlabs_voice_id'],
                model=tts_config['elevenlabs_model'],
                api_key=api_keys.get('elevenlabs', '')
            )
        elif provider == 'edge':
            # For Edge TTS, use ElevenLabs as it's available and working
            # TODO: Implement proper Edge TTS wrapper when OpenAI key is available
            print("Edge TTS requested - using ElevenLabs as alternative")
            try:
                # Get API keys from config
                from ..config.config_loader import ConfigLoader
                api_keys = ConfigLoader.get_api_keys()
                elevenlabs_key = api_keys.get('elevenlabs', '')

                if elevenlabs_key:
                    return elevenlabs.TTS(
                        voice_id="EXAVITQu4vr4xnSDxMaL",  # Default voice ID
                        model="eleven_turbo_v2_5",
                        api_key=elevenlabs_key
                    )
                else:
                    # If no ElevenLabs key, fall back to Groq with warning
                    print("Warning: No ElevenLabs key for Edge TTS alternative, using Groq")
                    return groq.TTS(
                        model=groq_config['tts_model'],
                        voice=groq_config['tts_voice'],
                        api_key=api_keys.get('groq', '')
                    )
            except Exception as e:
                print(f"Warning: Edge TTS alternative failed: {e}, using Groq")
                return groq.TTS(
                    model=groq_config['tts_model'],
                    voice=groq_config['tts_voice'],
                    api_key=api_keys.get('groq', '')
                )
        else:
            # Default to Groq
            return groq.TTS(
                model=groq_config['tts_model'],
                voice=groq_config['tts_voice'],
                api_key=api_keys.get('groq', '')
            )

    @staticmethod
    def create_vad():
        """Create Voice Activity Detection provider"""
        return silero.VAD.load()

    @staticmethod
    def create_turn_detection():
        """Create turn detection model"""
        # Turn detection disabled - models require special access
        return None