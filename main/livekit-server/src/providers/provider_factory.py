import livekit.plugins.groq as groq
import livekit.plugins.elevenlabs as elevenlabs
import livekit.plugins.deepgram as deepgram
from livekit.plugins import openai, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from livekit.plugins.turn_detector.english import EnglishModel
from livekit.agents import stt, llm, tts

# Import our custom providers
from .edge_tts_provider import EdgeTTS
from .local_whisper_stt import LocalWhisperSTT
from .openai_whisper_stt import OpenAIWhisperSTT
from .coqui_tts_provider import CoquiTTS

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
                providers.append(openai.LLM.with_ollama(
                    model=config.get('llm_model', 'llama3.1:8b'),
                    base_url=config.get('ollama_url', 'http://localhost:11434') + '/v1',
                    temperature=config.get('llm_temperature', 0.7),
                ))
            else:
                providers.append(groq.LLM(model=config['llm_model']))

            # Add fallback
            fallback_provider = config.get('fallback_llm_provider', provider).lower()
            if fallback_provider == 'ollama':
                providers.append(openai.LLM.with_ollama(
                    model=config.get('fallback_llm_model', 'llama3.1:8b'),
                    base_url=config.get('ollama_url', 'http://localhost:11434') + '/v1',
                ))
            else:
                providers.append(groq.LLM(model=config.get('fallback_llm_model', 'llama-3.1-8b-instant')))

            return llm.FallbackAdapter(providers)
        else:
            # Single provider
            if provider == 'ollama':
                from openai import AsyncOpenAI
                import httpx

                # Create custom HTTP client with extended timeout
                http_client = httpx.AsyncClient(timeout=120.0)

                # Create OpenAI client with custom http_client
                oai_client = AsyncOpenAI(
                    base_url=config.get('ollama_url', 'http://localhost:11434') + '/v1',
                    api_key="ollama",  # Ollama doesn't need real API key
                    http_client=http_client,
                )

                return openai.LLM(
                    model=config.get('llm_model', 'llama3.1:8b'),
                    temperature=config.get('llm_temperature', 0.7),
                    client=oai_client,
                )
            else:
                # Default to Groq
                return groq.LLM(model=config['llm_model'])

    @staticmethod
    def create_stt(config, vad=None):
        """Create Speech-to-Text provider with fallback based on configuration"""
        fallback_enabled = config.get('fallback_enabled', False)
        provider = config.get('stt_provider', 'groq').lower()

        if fallback_enabled:
            # Create primary and fallback STT providers with StreamAdapter
            providers = []

            if provider == 'local_whisper':
                providers.append(stt.StreamAdapter(
                    stt=LocalWhisperSTT(
                        model_size=config.get('whisper_model', 'base'),
                        device=config.get('whisper_device', 'cpu'),
                        language=config['stt_language'],
                    ),
                    vad=vad
                ))
            elif provider == 'deepgram':
                providers.append(stt.StreamAdapter(
                    stt=deepgram.STT(
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

            # Add fallback
            fallback_provider = config.get('fallback_stt_provider', 'groq').lower()
            if fallback_provider == 'local_whisper':
                providers.append(stt.StreamAdapter(
                    stt=LocalWhisperSTT(
                        model_size=config.get('whisper_model', 'base'),
                        device=config.get('whisper_device', 'cpu'),
                        language=config['stt_language'],
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

            return stt.FallbackAdapter(providers)
        else:
            # Single provider with StreamAdapter and VAD
            if provider == 'local_whisper':
                return stt.StreamAdapter(
                    stt=LocalWhisperSTT(
                        model_size=config.get('whisper_model', 'base'),
                        device=config.get('whisper_device', 'cpu'),
                        compute_type=config.get('whisper_compute_type', 'int8'),
                        language=config['stt_language'],
                    ),
                    vad=vad
                )
            elif provider == 'openai_whisper':
                return stt.StreamAdapter(
                    stt=OpenAIWhisperSTT(
                        model_size=config.get('whisper_model', 'base'),
                        device=config.get('whisper_device', 'cpu'),
                        language=config['stt_language'],
                    ),
                    vad=vad
                )
            elif provider == 'deepgram':
                return stt.StreamAdapter(
                    stt=deepgram.STT(
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
            if primary_provider == 'edge':
                providers.append(EdgeTTS(
                    voice=tts_config.get('edge_voice', 'en-US-AvaNeural'),
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
            else:
                providers.append(groq.TTS(
                    model=groq_config['tts_model'],
                    voice=groq_config['tts_voice']
                ))

            # Fallback providers (in order of preference)
            if primary_provider != 'edge':
                providers.append(EdgeTTS(
                    voice=tts_config.get('edge_voice', 'en-US-AvaNeural'),
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

            if provider == 'piper':
                from .piper_tts_provider import PiperTTS
                return PiperTTS(
                    voice=tts_config.get('piper_voice', 'en_US-lessac-medium'),
                    sample_rate=tts_config.get('piper_sample_rate', 22050),
                )
            elif provider == 'pyttsx3':
                from .pyttsx3_tts_provider import Pyttsx3TTS
                return Pyttsx3TTS(
                    rate=tts_config.get('pyttsx3_rate', 150),
                    volume=tts_config.get('pyttsx3_volume', 1.0),
                    voice_index=tts_config.get('pyttsx3_voice', 0),
                    sample_rate=24000,
                )
            elif provider == 'coqui':
                return CoquiTTS(
                    model_name=tts_config.get('coqui_model', 'tts_models/en/ljspeech/tacotron2-DDC'),
                    use_gpu=tts_config.get('coqui_use_gpu', False),
                    sample_rate=tts_config.get('coqui_sample_rate', 24000),
                    speaker=tts_config.get('coqui_speaker'),
                    language=tts_config.get('coqui_language'),
                )
            elif provider == 'elevenlabs':
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
        """Create Voice Activity Detection provider using cache"""
        # Try to use cached VAD first
        try:
            from ..utils.model_cache import model_cache
            cached_vad = model_cache.get_vad_model()
            if cached_vad:
                return cached_vad
        except Exception:
            pass  # Fall back to direct loading

        # Fallback to direct loading
        return silero.VAD.load()

    @staticmethod
    def create_turn_detection():
        """Create turn detection model"""
       # return MultilingualModel()
       # return EnglishModel()
        return None  # Disabled to avoid HuggingFace download errors