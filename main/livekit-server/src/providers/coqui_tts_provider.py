"""
Coqui TTS Provider for LiveKit
Provides fully local text-to-speech using Coqui TTS
"""
import asyncio
import io
import logging
import wave
import numpy as np
from typing import Optional
from livekit.agents import tts

logger = logging.getLogger(__name__)

try:
    from TTS.api import TTS as CoquiTTSAPI
    COQUI_TTS_AVAILABLE = True
except ImportError:
    COQUI_TTS_AVAILABLE = False
    logger.warning("Coqui TTS not installed. Install with: pip install TTS")


class CoquiTTS(tts.TTS):
    """Coqui TTS implementation for local text-to-speech"""

    def __init__(
        self,
        *,
        model_name: str = "tts_models/en/ljspeech/tacotron2-DDC",
        use_gpu: bool = False,
        sample_rate: int = 24000,
        speaker: Optional[str] = None,
        language: Optional[str] = None,
    ):
        """
        Initialize Coqui TTS provider

        Args:
            model_name: TTS model name from Coqui TTS
                Examples:
                - tts_models/en/ljspeech/tacotron2-DDC
                - tts_models/en/ljspeech/fast_pitch
                - tts_models/en/vctk/vits
                - tts_models/multilingual/multi-dataset/your_tts
            use_gpu: Use GPU for inference (requires CUDA)
            sample_rate: Output audio sample rate
            speaker: Speaker name for multi-speaker models
            language: Language code for multilingual models
        """
        super().__init__(
            capabilities=tts.TTSCapabilities(streaming=False),
            sample_rate=sample_rate,
            num_channels=1,
        )

        if not COQUI_TTS_AVAILABLE:
            raise ImportError(
                "Coqui TTS is not installed. "
                "Install with: pip install TTS"
            )

        self._model_name = model_name
        self._use_gpu = use_gpu
        self._sample_rate = sample_rate
        self._speaker = speaker
        self._language = language
        self._tts: Optional[CoquiTTSAPI] = None

        logger.info(
            f"Initialized CoquiTTS with model={model_name}, "
            f"use_gpu={use_gpu}, sample_rate={sample_rate}"
        )

    async def _ensure_model_loaded(self):
        """Lazy load the TTS model"""
        if self._tts is None:
            logger.info(f"Loading Coqui TTS model: {self._model_name}")
            loop = asyncio.get_event_loop()

            # Load model in thread pool to avoid blocking
            self._tts = await loop.run_in_executor(
                None,
                lambda: CoquiTTSAPI(
                    model_name=self._model_name,
                    gpu=self._use_gpu,
                )
            )

            logger.info(f"Coqui TTS model loaded: {self._model_name}")

    def synthesize(self, text: str, *, conn_options: Optional[any] = None) -> "ChunkedStream":
        """
        Synthesize text to speech

        Args:
            text: Text to synthesize
            conn_options: Connection options (passed to stream)

        Returns:
            ChunkedStream with audio data
        """
        return CoquiTTSStream(
            tts_instance=self,
            text=text,
            sample_rate=self._sample_rate,
            speaker=self._speaker,
            language=self._language,
            conn_options=conn_options,
        )

    async def _synthesize_audio(self, text: str) -> bytes:
        """
        Internal method to synthesize audio

        Args:
            text: Text to synthesize

        Returns:
            Audio data as bytes (WAV format)
        """
        await self._ensure_model_loaded()

        logger.debug(f"Synthesizing text: {text[:50]}...")

        # Run synthesis in thread pool
        loop = asyncio.get_event_loop()
        audio_data = await loop.run_in_executor(
            None,
            self._synthesize_sync,
            text,
        )

        return audio_data

    def _synthesize_sync(self, text: str) -> bytes:
        """
        Synchronous synthesis (run in thread pool)

        Returns audio as WAV bytes
        """
        try:
            # Build synthesis arguments
            tts_kwargs = {}

            if self._speaker:
                tts_kwargs['speaker'] = self._speaker

            if self._language:
                tts_kwargs['language'] = self._language

            # Synthesize to file path (Coqui TTS outputs to file)
            # We'll use a BytesIO buffer instead
            output_buffer = io.BytesIO()

            # Generate audio (returns numpy array)
            wav_data = self._tts.tts(text=text, **tts_kwargs)

            # Convert numpy array to WAV bytes
            wav_bytes = self._numpy_to_wav(wav_data, self._sample_rate)

            return wav_bytes

        except Exception as e:
            logger.error(f"Error synthesizing audio: {e}")
            # Return silence as fallback
            return self._generate_silence(1.0)

    def _numpy_to_wav(self, audio_np: np.ndarray, sample_rate: int) -> bytes:
        """
        Convert numpy array to WAV bytes

        Args:
            audio_np: Audio data as numpy array
            sample_rate: Sample rate

        Returns:
            WAV file as bytes
        """
        # Ensure audio is in correct format
        if audio_np.dtype != np.int16:
            # Normalize to [-1, 1] if needed
            if audio_np.max() > 1.0 or audio_np.min() < -1.0:
                audio_np = audio_np / np.max(np.abs(audio_np))

            # Convert to int16
            audio_np = (audio_np * 32767).astype(np.int16)

        # Create WAV file in memory
        wav_buffer = io.BytesIO()

        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_np.tobytes())

        return wav_buffer.getvalue()

    def _generate_silence(self, duration: float) -> bytes:
        """Generate silent audio"""
        num_samples = int(duration * self._sample_rate)
        silence = np.zeros(num_samples, dtype=np.int16)

        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(self._sample_rate)
            wav_file.writeframes(silence.tobytes())

        return wav_buffer.getvalue()

    async def aclose(self):
        """Cleanup resources"""
        if self._tts is not None:
            # Coqui TTS doesn't need explicit cleanup
            self._tts = None
            logger.info("CoquiTTS closed")


class CoquiTTSStream(tts.ChunkedStream):
    """Audio stream for Coqui TTS output"""

    def __init__(
        self,
        *,
        tts_instance: CoquiTTS,
        text: str,
        sample_rate: int,
        speaker: Optional[str] = None,
        language: Optional[str] = None,
        conn_options: Optional[any] = None,
    ):
        """
        Initialize TTS stream

        Args:
            tts_instance: CoquiTTS instance
            text: Text to synthesize
            sample_rate: Audio sample rate
            speaker: Speaker name
            language: Language code
            conn_options: Connection options (passed to ChunkedStream)
        """
        super().__init__(
            tts=tts_instance,
            input_text=text,
            conn_options=conn_options,
        )
        self._tts = tts_instance
        self._text = text
        self._sample_rate = sample_rate
        self._speaker = speaker
        self._language = language
        self._audio_data: Optional[bytes] = None
        self._sent = False

    async def _run(self, output_emitter):
        """Main synthesis task - required by ChunkedStream abstract class"""
        try:
            # Synthesize audio
            self._audio_data = await self._tts._synthesize_audio(self._text)

            # Emit the audio chunk using the output_emitter
            output_emitter(
                tts.SynthesizedAudio(
                    request_id="",
                    segment_id="",
                    frame=self._audio_data,
                )
            )
        except Exception as e:
            logger.error(f"Error in CoquiTTS synthesis: {e}")

    async def aclose(self):
        """Close stream"""
        await super().aclose()
        self._audio_data = None
