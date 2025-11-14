import livekit.plugins.groq as groq
import livekit.plugins.elevenlabs as elevenlabs
import livekit.plugins.deepgram as deepgram
import livekit.plugins.cartesia as cartesia
from livekit.plugins import openai, silero
from livekit.agents import stt, llm, tts
import os
import logging

# Import our custom providers
from .edge_tts_provider import EdgeTTS
from .piper_tts_provider import PiperTTS
from .fastwhisper_stt_provider import FastWhisperSTT
from .whisper_stt_provider import WhisperSTT
from .remote_whisper_stt_provider import RemoteWhisperSTT
from .remote_piper_tts_provider import RemotePiperTTS

logger = logging.getLogger(__name__)

# ========================================
# INSTANCE CACHING FOR HEAVY MODELS
# ========================================
# Cache STT instances to avoid reloading models (Whisper takes 19s to load!)
_whisper_stt_cache = {}
_fastwhisper_stt_cache = {}


class ProviderFactory:
    """Factory class for creating AI service providers"""

    @staticmethod
    def create_llm(config):
        """Create LLM provider with fallback based on configuration"""
        fallback_enabled = config.get('fallback_enabled', False)
        provider = config.get('llm_provider', 'groq').lower()

        if fallback_enabled:
            # Create primary and fallback LLM providers
            providers = []

            if provider == 'ollama':
                # Use official LiveKit Ollama integration via OpenAI plugin
                import httpx
                import openai as openai_sdk
                
                ollama_api = os.environ.get("OLLAMA_API_URL", "http://localhost:11434")
                ollama_model = config.get('llm_model', os.environ.get("OLLAMA_MODEL", "gemma2:2b"))
                ollama_timeout = int(os.environ.get("OLLAMA_TIMEOUT", "60"))  # Default 60s
                
                # Create custom client with timeout
                custom_client = openai_sdk.AsyncOpenAI(
                    base_url=f"{ollama_api}/v1",
                    api_key="ollama",  # Ollama doesn't need real API key
                    timeout=httpx.Timeout(timeout=ollama_timeout, connect=10.0)
                )
                
                # Speed optimization: Disable thinking mode, increase temperature for faster responses
                providers.append(openai.LLM(
                    model=ollama_model,
                    client=custom_client,
                    temperature=0.8,  # Higher temp = faster, more creative responses
                    # Note: reasoning_effort not supported by Ollama
                ))
            else:
                # Default to Groq
                providers.append(groq.LLM(model=config['llm_model']))

            # Add fallback
            providers.append(groq.LLM(model=config.get('fallback_llm_model', 'llama-3.1-8b-instant')))

            return llm.FallbackAdapter(providers)
        else:
            # Single provider
            if provider == 'ollama':
                # Use official LiveKit Ollama integration via OpenAI plugin
                import httpx
                import openai as openai_sdk
                
                ollama_api = os.environ.get("OLLAMA_API_URL", "http://localhost:11434")
                ollama_model = config.get('llm_model', os.environ.get("OLLAMA_MODEL", "gemma2:2b"))
                ollama_timeout = int(os.environ.get("OLLAMA_TIMEOUT", "60"))  # Default 60s
                
                # Create custom client with timeout
                custom_client = openai_sdk.AsyncOpenAI(
                    base_url=f"{ollama_api}/v1",
                    api_key="ollama",  # Ollama doesn't need real API key
                    timeout=httpx.Timeout(timeout=ollama_timeout, connect=10.0)
                )
                
                # Speed optimization: Disable thinking mode, increase temperature for faster responses
                return openai.LLM(
                    model=ollama_model,
                    client=custom_client,
                    temperature=0.8,  # Higher temp = faster, more creative responses
                    # Note: reasoning_effort not supported by Ollama
                )
            else:
                # Default to Groq provider
                return groq.LLM(model=config['llm_model'])

    @staticmethod
    def create_stt(config, vad=None):
        """Create Speech-to-Text provider with fallback based on configuration"""
        global _whisper_stt_cache, _fastwhisper_stt_cache
        
        fallback_enabled = config.get('fallback_enabled', False)
        provider = config.get('stt_provider', 'groq').lower()

        if fallback_enabled:
            # Create primary and fallback STT providers with StreamAdapter
            providers = []

            if provider == 'remote_whisper':
                # Use remote Whisper server
                remote_url = os.environ.get('REMOTE_WHISPER_URL', 'http://localhost:8000')
                providers.append(stt.StreamAdapter(
                    stt=RemoteWhisperSTT(
                        base_url=remote_url,
                        timeout=30.0,
                        language=config.get('stt_language', 'en')
                    ),
                    vad=vad
                ))
            elif provider == 'whisper':
                # Use cached Whisper instance to avoid reloading model (19s!)
                cache_key = f"{config.get('stt_model', 'base')}_{config.get('stt_language', 'en')}"
                
                if cache_key not in _whisper_stt_cache:
                    logger.info(f"🆕 [STT-CACHE] Creating new WhisperSTT instance: {cache_key}")
                    _whisper_stt_cache[cache_key] = WhisperSTT(
                        model=config.get('stt_model', 'base'),
                        language=config.get('stt_language', 'en')
                    )
                else:
                    logger.info(f"♻️ [STT-CACHE] Reusing cached WhisperSTT instance: {cache_key}")
                
                providers.append(stt.StreamAdapter(
                    stt=_whisper_stt_cache[cache_key],
                    vad=vad
                ))
            elif provider == 'fastwhisper':
                # Use cached FastWhisper instance to avoid reloading model
                cache_key = f"{config.get('stt_model', 'base')}_{config.get('stt_language', 'en')}"
                
                if cache_key not in _fastwhisper_stt_cache:
                    logger.info(f"🆕 [STT-CACHE] Creating new FastWhisperSTT instance: {cache_key}")
                    _fastwhisper_stt_cache[cache_key] = FastWhisperSTT(
                        model=config.get('stt_model', 'base'),
                        language=config.get('stt_language', 'en'),
                        vad_filter=False  # Disable internal VAD - using Silero VAD instead
                    )
                else:
                    logger.info(f"♻️ [STT-CACHE] Reusing cached FastWhisperSTT instance: {cache_key}")
                
                providers.append(stt.StreamAdapter(
                    stt=_fastwhisper_stt_cache[cache_key],
                    vad=vad
                ))
            elif provider == 'deepgram':
                api_key = os.getenv('DEEPGRAM_API_KEY')
                if not api_key:
                    raise ValueError("DEEPGRAM_API_KEY environment variable is not set")
                providers.append(stt.StreamAdapter(
                    stt=deepgram.STT(
                        api_key=api_key,
                        model=config.get('deepgram_model', 'nova-3'),
                        language=config['stt_language']
                    ),
                    vad=vad
                ))
            else:
                providers.append(stt.StreamAdapter(
                    stt=groq.STT(
                        model=config['stt_model'],
                        language=config['stt_language']
                    ),
                    vad=vad
                ))

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
            if provider == 'remote_whisper':
                # Use remote Whisper server
                remote_url = os.environ.get('REMOTE_WHISPER_URL', 'http://localhost:8000')
                return stt.StreamAdapter(
                    stt=RemoteWhisperSTT(
                        base_url=remote_url,
                        timeout=30.0,
                        language=config.get('stt_language', 'en')
                    ),
                    vad=vad
                )
            elif provider == 'whisper':
                # Use cached Whisper instance to avoid reloading model (19s!)
                cache_key = f"{config.get('stt_model', 'base')}_{config.get('stt_language', 'en')}"
                
                if cache_key not in _whisper_stt_cache:
                    logger.info(f"🆕 [STT-CACHE] Creating new WhisperSTT instance: {cache_key}")
                    _whisper_stt_cache[cache_key] = WhisperSTT(
                        model=config.get('stt_model', 'base'),
                        language=config.get('stt_language', 'en')
                    )
                else:
                    logger.info(f"♻️ [STT-CACHE] Reusing cached WhisperSTT instance: {cache_key}")
                
                return stt.StreamAdapter(
                    stt=_whisper_stt_cache[cache_key],
                    vad=vad
                )
            elif provider == 'fastwhisper':
                # Use cached FastWhisper instance to avoid reloading model
                cache_key = f"{config.get('stt_model', 'base')}_{config.get('stt_language', 'en')}"
                
                if cache_key not in _fastwhisper_stt_cache:
                    logger.info(f"🆕 [STT-CACHE] Creating new FastWhisperSTT instance: {cache_key}")
                    _fastwhisper_stt_cache[cache_key] = FastWhisperSTT(
                        model=config.get('stt_model', 'base'),
                        language=config.get('stt_language', 'en'),
                        vad_filter=False  # Disable internal VAD - using Silero VAD instead
                    )
                else:
                    logger.info(f"♻️ [STT-CACHE] Reusing cached FastWhisperSTT instance: {cache_key}")
                
                return stt.StreamAdapter(
                    stt=_fastwhisper_stt_cache[cache_key],
                    vad=vad
                )
            elif provider == 'deepgram':
                api_key = os.getenv('DEEPGRAM_API_KEY')
                if not api_key:
                    raise ValueError("DEEPGRAM_API_KEY environment variable is not set")
                return stt.StreamAdapter(
                    stt=deepgram.STT(
                        api_key=api_key,
                        model=config.get('deepgram_model', 'nova-3'),
                        language=config['stt_language']
                    ),
                    vad=vad
                )
            else:
                # Default to Groq with StreamAdapter and VAD
                return stt.StreamAdapter(
                    stt=groq.STT(
                        model=config['stt_model'],
                        language=config['stt_language']
                    ),
                    vad=vad
                )

    @staticmethod
    def create_tts(groq_config, tts_config):
        """Create Text-to-Speech provider with fallback based on configuration"""
        fallback_enabled = tts_config.get('fallback_enabled', False)

        if fallback_enabled:
            # Create primary and fallback TTS providers
            providers = []

            # Primary provider based on configuration
            primary_provider = tts_config.get('provider', 'edge').lower()
            if primary_provider == 'remote_piper':
                # Use remote Piper server
                remote_url = os.environ.get('REMOTE_PIPER_URL', 'http://localhost:8001')
                providers.append(RemotePiperTTS(
                    base_url=remote_url,
                    timeout=30.0,
                    sample_rate=tts_config.get('tts_sample_rate', 22050)
                ))
            elif primary_provider == 'piper':
                providers.append(PiperTTS(
                    voice=tts_config.get('piper_voice', 'en_US-amy-medium'),
                    model_path=tts_config.get('piper_model_path'),
                    sample_rate=tts_config.get('piper_sample_rate', 22050),
                    speaker=tts_config.get('piper_speaker'),
                    piper_binary=tts_config.get('piper_binary', 'piper')
                ))
            elif primary_provider == 'edge':
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
            # If primary is remote_piper, fall back to local Piper first (not Edge).
            if primary_provider == 'remote_piper':
                providers.append(PiperTTS(
                    voice=tts_config.get('piper_voice', 'en_US-amy-medium'),
                    model_path=tts_config.get('piper_model_path'),
                    sample_rate=tts_config.get('piper_sample_rate', 22050),
                    speaker=tts_config.get('piper_speaker'),
                    piper_binary=tts_config.get('piper_binary', 'piper')
                ))
            elif primary_provider != 'edge':
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

            if provider == 'remote_piper':
                # Use remote Piper server
                remote_url = os.environ.get('REMOTE_PIPER_URL', 'http://localhost:8001')
                return RemotePiperTTS(
                    base_url=remote_url,
                    timeout=30.0,
                    sample_rate=tts_config.get('tts_sample_rate', 22050)
                )
            elif provider == 'piper':
                return PiperTTS(
                    voice=tts_config.get('piper_voice', 'en_US-amy-medium'),
                    model_path=tts_config.get('piper_model_path'),
                    sample_rate=tts_config.get('piper_sample_rate', 22050),
                    speaker=tts_config.get('piper_speaker'),
                    piper_binary=tts_config.get('piper_binary', 'piper')
                )
            elif provider == 'elevenlabs':
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
        """Create Voice Activity Detection provider optimized for children"""
        # Try to use cached VAD first
        try:
            from ..utils.model_cache import model_cache
            cached_vad = model_cache.get_vad_model()
            if cached_vad:
                return cached_vad
        except Exception:
            pass  # Fall back to direct loading

        # Get VAD settings from environment or use defaults optimized for kids
        min_speech_duration = float(os.getenv('VAD_MIN_SPEECH_DURATION', '0.1'))
        min_silence_duration = float(os.getenv('VAD_MIN_SILENCE_DURATION', '0.5'))
        activation_threshold = float(os.getenv('VAD_ACTIVATION_THRESHOLD', '0.3'))
        max_buffered_speech = float(os.getenv('VAD_MAX_BUFFERED_SPEECH', '60.0'))
        prefix_padding = float(os.getenv('VAD_PREFIX_PADDING_DURATION', '0.3'))
        
        return silero.VAD.load(
            min_speech_duration=min_speech_duration,
            min_silence_duration=min_silence_duration,
            activation_threshold=activation_threshold,
            prefix_padding_duration=prefix_padding,
            sample_rate=16000,
            max_buffered_speech=max_buffered_speech,
        )

    @staticmethod
    def create_turn_detection():
        """Create turn detection model"""
       # return MultilingualModel()
       # return EnglishModel()
        return None  # Disabled to avoid HuggingFace download errors
