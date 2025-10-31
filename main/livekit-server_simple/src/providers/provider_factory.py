import livekit.plugins.groq as groq
import livekit.plugins.elevenlabs as elevenlabs
import livekit.plugins.deepgram as deepgram
import livekit.plugins.cartesia as cartesia
from livekit.plugins import openai
from livekit.agents import stt, llm, tts

# Import our custom providers
from .edge_tts_provider import EdgeTTS
from ..vad import LiveKitVAD


class ProviderFactory:
    """Factory class for creating AI service providers"""

    @staticmethod
    def create_llm(config):
        """Create LLM provider with fallback based on configuration"""
        fallback_enabled = config.get('fallback_enabled', False)

        if fallback_enabled:
            # Create primary and fallback LLM providers (both Groq)
            providers = [
                groq.LLM(model=config['llm_model']),
                groq.LLM(model=config.get('fallback_llm_model', 'llama-3.1-8b-instant'))
            ]
            return llm.FallbackAdapter(providers)
        else:
            # Single Groq provider
            return groq.LLM(model=config['llm_model'])

    @staticmethod
    def create_stt(config, vad=None):
        """Create Speech-to-Text provider with fallback based on configuration"""
        import logging
        logger = logging.getLogger("provider_factory")
        
        fallback_enabled = config.get('fallback_enabled', False)
        provider = config.get('stt_provider', 'groq').lower()

        if fallback_enabled:
            # Create primary and fallback STT providers with StreamAdapter
            providers = []

            if provider == 'deepgram':
                import os
                logger.info(f"🎤 Creating Deepgram STT provider")
                api_key = os.getenv('DEEPGRAM_API_KEY')
                if not api_key:
                    logger.error("❌ DEEPGRAM_API_KEY environment variable is not set")
                    raise ValueError("DEEPGRAM_API_KEY environment variable is not set")
                logger.info(f"🎤 Deepgram API key found, creating STT with model: {config.get('deepgram_model', 'nova-3')}")
                providers.append(stt.StreamAdapter(
                    stt=deepgram.STT(
                        api_key=api_key,
                        model=config.get('deepgram_model', 'nova-3'),
                        language=config['stt_language']
                    ),
                    vad=vad
                ))
                logger.info(f"🎤 Deepgram StreamAdapter created successfully")
            else:
                logger.info(f"🎤 Creating Groq STT (fallback path) with model: {config['stt_model']}")
                providers.append(stt.StreamAdapter(
                    stt=groq.STT(
                        model=config['stt_model'],
                        language=config['stt_language']
                    ),
                    vad=vad
                ))
                logger.info(f"🎤 Groq STT StreamAdapter (fallback) created successfully")

            # Add fallback (always Groq)
            providers.append(stt.StreamAdapter(
                stt=groq.STT(
                    model=config['stt_model'],
                    language=config['stt_language']
                ),
                vad=vad
            ))

            return stt.FallbackAdapter(providers)
        else:
            # Single provider with StreamAdapter and VAD
            if provider == 'deepgram':
                import os
                logger.info(f"🎤 Creating single Deepgram STT provider")
                api_key = os.getenv('DEEPGRAM_API_KEY')
                if not api_key:
                    logger.error("❌ DEEPGRAM_API_KEY environment variable is not set")
                    raise ValueError("DEEPGRAM_API_KEY environment variable is not set")
                logger.info(f"🎤 Deepgram API key found, creating STT with model: {config.get('deepgram_model', 'nova-3')}")
                
                deepgram_stt = deepgram.STT(
                    api_key=api_key,
                    model=config.get('deepgram_model', 'nova-3'),
                    language=config['stt_language']
                )
                logger.info(f"🎤 Deepgram STT created successfully")
                
                # Use the original STT without wrapper for now
                wrapped_stt = deepgram_stt
                
                # Create StreamAdapter with detailed logging
                logger.info(f"🎤 Creating StreamAdapter with Deepgram STT and custom VAD")
                logger.info(f"🎤 STT type: {type(wrapped_stt)}, VAD type: {type(vad)}")
                
                stream_adapter = stt.StreamAdapter(
                    stt=wrapped_stt,
                    vad=vad
                )
                logger.info(f"🎤 Deepgram StreamAdapter created successfully")
                
                # Test if the StreamAdapter has the expected methods
                logger.info(f"🎤 StreamAdapter methods: {[m for m in dir(stream_adapter) if not m.startswith('_')]}")
                
                return stream_adapter
            else:
                # Default to Groq with StreamAdapter and VAD
                logger.info(f"🎤 Creating Groq STT with model: {config['stt_model']}, language: {config['stt_language']}")
                logger.info(f"🎤 VAD provided: {vad is not None}, VAD type: {type(vad) if vad else 'None'}")
                
                groq_stt = groq.STT(
                    model=config['stt_model'],
                    language=config['stt_language']
                )
                logger.info(f"🎤 Groq STT created successfully")
                
                stream_adapter = stt.StreamAdapter(
                    stt=groq_stt,
                    vad=vad
                )
                logger.info(f"🎤 StreamAdapter created successfully with VAD")
                return stream_adapter

    @staticmethod
    def create_tts(groq_config, tts_config):
        """Create Text-to-Speech provider with fallback based on configuration"""
        fallback_enabled = tts_config.get('fallback_enabled', False)

        if fallback_enabled:
            # Create primary and fallback TTS providers
            providers = []

            # Primary provider based on configuration
            primary_provider = tts_config.get('provider', 'edge').lower()
            if primary_provider == 'edge':
                providers.append(EdgeTTS(
                    voice=tts_config.get('edge_voice', 'en-US-AnaNeural'),
                    rate=tts_config.get('edge_rate', '+0%'),
                    volume=tts_config.get('edge_volume', '+0%'),
                    pitch=tts_config.get('edge_pitch', '+0Hz'),
                    sample_rate=tts_config.get('edge_sample_rate', 24000),
                    channels=tts_config.get('edge_channels', 1)
                ))
            elif primary_provider == 'elevenlabs':
                providers.append(elevenlabs.TTS(
                    voice_id=tts_config['elevenlabs_voice_id'],
                    model=tts_config['elevenlabs_model']
                ))
            elif primary_provider == 'cartesia':
                providers.append(cartesia.TTS(
                    model=tts_config.get('cartesia_model', 'sonic-english'),
                    voice=tts_config.get('cartesia_voice', '9626c31c-bec5-4cca-baa8-f8ba9e84c8bc'),
                    language=tts_config.get('cartesia_language', 'en')
                ))
            else:
                # Primary Groq TTS - use tts_config if available
                model = tts_config.get('model', groq_config['tts_model'])
                voice = tts_config.get('voice', groq_config['tts_voice'])
                providers.append(groq.TTS(
                    model=model,
                    voice=voice
                ))

            # Fallback providers (in order of preference)
            if primary_provider != 'edge':
                providers.append(EdgeTTS(
                    voice=tts_config.get('edge_voice', 'en-US-AnaNeural'),
                    rate=tts_config.get('edge_rate', '+0%'),
                    volume=tts_config.get('edge_volume', '+0%'),
                    pitch=tts_config.get('edge_pitch', '+0Hz'),
                    sample_rate=tts_config.get('edge_sample_rate', 24000),
                    channels=tts_config.get('edge_channels', 1)
                ))

            if primary_provider != 'groq':
                providers.append(groq.TTS(
                    model=groq_config['tts_model'],
                    voice=groq_config['tts_voice']
                ))

            return tts.FallbackAdapter(providers)
        else:
            # Single provider (current behavior)
            provider = tts_config.get('provider', 'groq').lower()

            if provider == 'elevenlabs':
                return elevenlabs.TTS(
                    voice_id=tts_config['elevenlabs_voice_id'],
                    model=tts_config['elevenlabs_model']
                )
            elif provider == 'edge':
                return EdgeTTS(
                    voice=tts_config.get('edge_voice', 'en-US-AnaNeural'),
                    rate=tts_config.get('edge_rate', '+0%'),
                    volume=tts_config.get('edge_volume', '+0%'),
                    pitch=tts_config.get('edge_pitch', '+0Hz'),
                    sample_rate=tts_config.get('edge_sample_rate', 24000),
                    channels=tts_config.get('edge_channels', 1)
                )
            elif provider == 'cartesia':
                return cartesia.TTS(
                    model=tts_config.get('cartesia_model', 'sonic-english'),
                    voice=tts_config.get('cartesia_voice', '9626c31c-bec5-4cca-baa8-f8ba9e84c8bc'),
                    language=tts_config.get('cartesia_language', 'en')
                )
            else:
                # Default to Groq - use tts_config if available, otherwise fall back to groq_config
                model = tts_config.get('model', groq_config['tts_model'])
                voice = tts_config.get('voice', groq_config['tts_voice'])
                return groq.TTS(
                    model=model,
                    voice=voice
                )

    @staticmethod
    def create_vad():
        """Create Voice Activity Detection provider with custom Silero ONNX implementation"""
        # Try to use cached VAD first
        try:
            from ..utils.model_cache import model_cache
            cached_vad = model_cache.get_vad_model()
            if cached_vad:
                return cached_vad
        except Exception:
            pass  # Fall back to direct loading

        # Load custom VAD with optimized parameters including pre-padding
        # Using ONNX implementation for better performance
        from ..config.config_loader import ConfigLoader
        vad_config = ConfigLoader.get_vad_config()

        return LiveKitVAD.load(
            model_path=vad_config.get('model_path', 'models/silero_vad.onnx'),
            sample_rate=vad_config.get('sample_rate', 16000),
            confidence=vad_config.get('confidence', 0.5),
            start_secs=vad_config.get('start_secs', 0.2),
            stop_secs=vad_config.get('stop_secs', 0.8),
            min_volume=vad_config.get('min_volume', 0.001)
        )

    @staticmethod
    def create_turn_detection():
        """Create turn detection model"""
       # return MultilingualModel()
       # return EnglishModel()
        return None  # Disabled to avoid HuggingFace download errors
