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
                    base_url=config.get(
                        'ollama_url', 'http://localhost:11434') + '/v1',
                    temperature=config.get('llm_temperature', 0.7),
                ))
            else:
                providers.append(groq.LLM(model=config['llm_model']))

            # Add fallback
            fallback_provider = config.get(
                'fallback_llm_provider', provider).lower()
            if fallback_provider == 'ollama':
                providers.append(openai.LLM.with_ollama(
                    model=config.get('fallback_llm_model', 'llama3.1:8b'),
                    base_url=config.get(
                        'ollama_url', 'http://localhost:11434') + '/v1',
                ))
            else:
                providers.append(groq.LLM(model=config.get(
                    'fallback_llm_model', 'llama-3.1-8b-instant')))

            return llm.FallbackAdapter(providers)
        else:
            # Single provider
            if provider == 'ollama':
                return openai.LLM.with_ollama(
                    model=config.get('llm_model', 'llama3.1:8b'),
                    base_url=config.get(
                        'ollama_url', 'http://localhost:11434') + '/v1',
                    temperature=config.get('llm_temperature', 0.7),
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
                import os
                api_key = os.getenv('DEEPGRAM_API_KEY')
                if not api_key:
                    raise ValueError("DEEPGRAM_API_KEY environment variable is not set")

                # Configure Deepgram with language and endpointing settings
                deepgram_lang = config.get('deepgram_language')
                endpointing_ms = config.get('deepgram_endpointing_ms', 25)

                providers.append(stt.StreamAdapter(
                    stt=deepgram.STT(
                        api_key=api_key,
                        model=config.get('deepgram_model', 'nova-3'),
                        language=deepgram_lang if deepgram_lang else 'en-US',
                        endpointing_ms=endpointing_ms
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
            fallback_provider = config.get(
                'fallback_stt_provider', 'groq').lower()
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
                        compute_type=config.get(
                            'whisper_compute_type', 'int8'),
                        language=config['stt_language'],
                    ),
                    vad=vad
                )
            elif provider == 'deepgram':
                import os
                api_key = os.getenv('DEEPGRAM_API_KEY')
                if not api_key:
                    raise ValueError("DEEPGRAM_API_KEY environment variable is not set")

                # Configure Deepgram with language and endpointing settings
                deepgram_lang = config.get('deepgram_language')
                endpointing_ms = config.get('deepgram_endpointing_ms', 25)

                return stt.StreamAdapter(
                    stt=deepgram.STT(
                        api_key=api_key,
                        model=config.get('deepgram_model', 'nova-3'),
                        language=deepgram_lang if deepgram_lang else 'en-US',
                        endpointing_ms=endpointing_ms
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

            if provider == 'coqui':
                return CoquiTTS(
                    model_name=tts_config.get(
                        'coqui_model', 'tts_models/en/ljspeech/tacotron2-DDC'),
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

        # Child-friendly VAD settings - lower thresholds for softer, higher-pitched voices
        # Children's voices are typically higher-pitched (200-300 Hz) and softer than adults
        return silero.VAD.load(
            min_speech_duration=0.05,      # Quick detection - keep default
            min_silence_duration=0.4,      # Reduced from 0.55s - children pause less
            activation_threshold=0.3,      # CRITICAL: Lowered from 0.5 for children's voices
            sample_rate=16000,
            max_buffered_speech=60.0
        )

    @staticmethod
    def create_turn_detection():
        """Create turn detection model"""
       # return MultilingualModel()
       # return EnglishModel()
        return None  # Disabled to avoid HuggingFace download errors
