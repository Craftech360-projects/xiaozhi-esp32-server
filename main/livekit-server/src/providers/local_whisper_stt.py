"""
Local Whisper STT Provider for LiveKit
Uses faster-whisper for local speech-to-text
"""
import asyncio
import logging
import numpy as np
from typing import Optional, Union
from livekit.agents import stt, utils

logger = logging.getLogger(__name__)

try:
    from faster_whisper import WhisperModel
    FASTER_WHISPER_AVAILABLE = True
except ImportError:
    FASTER_WHISPER_AVAILABLE = False
    logger.warning("faster-whisper not installed. Install with: pip install faster-whisper")


class LocalWhisperSTT(stt.STT):
    """Local Whisper STT implementation using faster-whisper"""

    def __init__(
        self,
        *,
        model_size: str = "base",
        device: str = "cpu",
        compute_type: str = "int8",
        language: str = "en",
        beam_size: int = 5,
        vad_filter: bool = True,
    ):
        """
        Initialize Local Whisper STT provider

        Args:
            model_size: Model size ('tiny', 'base', 'small', 'medium', 'large', 'large-v2', 'large-v3')
            device: Device to use ('cpu', 'cuda', 'auto')
            compute_type: Compute type for quantization ('int8', 'int8_float16', 'float16', 'float32')
            language: Language code (e.g., 'en', 'es', 'fr')
            beam_size: Beam size for decoding
            vad_filter: Apply voice activity detection filter
        """
        super().__init__(
            capabilities=stt.STTCapabilities(streaming=False, interim_results=False)
        )

        if not FASTER_WHISPER_AVAILABLE:
            raise ImportError(
                "faster-whisper is not installed. "
                "Install with: pip install faster-whisper"
            )

        self._model_size = model_size
        self._device = device
        self._compute_type = compute_type
        self._language = language if language else None  # None for auto-detection
        self._beam_size = beam_size
        self._vad_filter = vad_filter
        self._model: Optional[WhisperModel] = None

        logger.info(
            f"Initialized LocalWhisperSTT with model={model_size}, "
            f"device={device}, compute_type={compute_type}, "
            f"language={language}"
        )

    async def _ensure_model_loaded(self):
        """Lazy load the Whisper model"""
        if self._model is None:
            logger.info(f"Loading Whisper model: {self._model_size}")
            loop = asyncio.get_event_loop()

            # Load model in thread pool to avoid blocking
            self._model = await loop.run_in_executor(
                None,
                lambda: WhisperModel(
                    self._model_size,
                    device=self._device,
                    compute_type=self._compute_type,
                )
            )

            logger.info(f"Whisper model loaded: {self._model_size}")

    async def recognize(
        self,
        *,
        buffer: Union[utils.AudioBuffer, "rtc.AudioFrame"],
        language: Optional[str] = None,
    ) -> stt.SpeechEvent:
        """
        Recognize speech from audio buffer

        Args:
            buffer: Audio data to transcribe
            language: Override language (optional)

        Returns:
            SpeechEvent with transcription
        """
        await self._ensure_model_loaded()

        # Convert audio to numpy array
        audio_data = self._prepare_audio(buffer)

        # Run transcription in thread pool
        loop = asyncio.get_event_loop()
        segments = await loop.run_in_executor(
            None,
            self._transcribe_sync,
            audio_data,
            language or self._language,
        )

        # Combine segments into full transcription
        text = " ".join([segment.text for segment in segments])

        # Create speech event
        return stt.SpeechEvent(
            type=stt.SpeechEventType.FINAL_TRANSCRIPT,
            alternatives=[
                stt.SpeechData(
                    text=text.strip(),
                    language=language or self._language or "en",
                    confidence=1.0,  # faster-whisper doesn't provide confidence per transcript
                )
            ],
        )

    def _transcribe_sync(self, audio_data: np.ndarray, language: Optional[str]):
        """Synchronous transcription (run in thread pool)"""
        segments, info = self._model.transcribe(
            audio_data,
            language=language,
            beam_size=self._beam_size,
            vad_filter=self._vad_filter,
        )

        # Convert generator to list
        return list(segments)

    def _prepare_audio(self, buffer: Union[utils.AudioBuffer, "rtc.AudioFrame"]) -> np.ndarray:
        """Convert audio buffer to numpy array for Whisper"""
        try:
            # Handle AudioBuffer
            if isinstance(buffer, utils.AudioBuffer):
                # Get raw audio data
                audio_data = buffer.data

                # Convert to numpy array
                if isinstance(audio_data, bytes):
                    # Assume 16-bit PCM
                    audio_np = np.frombuffer(audio_data, dtype=np.int16)
                else:
                    audio_np = np.array(audio_data, dtype=np.float32)

                # Normalize to float32 [-1, 1]
                if audio_np.dtype == np.int16:
                    audio_np = audio_np.astype(np.float32) / 32768.0

                return audio_np

            # Handle rtc.AudioFrame
            else:
                # Get frame data
                frame_data = buffer.data

                # Convert to numpy array
                audio_np = np.frombuffer(frame_data, dtype=np.int16)

                # Normalize to float32 [-1, 1]
                audio_np = audio_np.astype(np.float32) / 32768.0

                return audio_np

        except Exception as e:
            logger.error(f"Error preparing audio: {e}")
            # Return empty array as fallback
            return np.array([], dtype=np.float32)

    async def aclose(self):
        """Cleanup resources"""
        if self._model is not None:
            # faster-whisper models don't need explicit cleanup
            self._model = None
            logger.info("LocalWhisperSTT closed")


class LocalWhisperSTTStream(stt.SpeechStream):
    """
    Streaming wrapper for LocalWhisperSTT
    Note: Whisper is not truly streaming, but we can simulate it by
    buffering audio and transcribing chunks
    """

    def __init__(
        self,
        *,
        stt_instance: LocalWhisperSTT,
        language: Optional[str] = None,
        sample_rate: int = 16000,
        chunk_duration: float = 2.0,
    ):
        """
        Initialize streaming STT

        Args:
            stt_instance: LocalWhisperSTT instance
            language: Language code
            sample_rate: Audio sample rate
            chunk_duration: Duration of audio chunks to buffer (seconds)
        """
        super().__init__()
        self._stt = stt_instance
        self._language = language
        self._sample_rate = sample_rate
        self._chunk_duration = chunk_duration
        self._audio_buffer = []
        self._buffer_lock = asyncio.Lock()

    async def recognize(
        self,
        *,
        buffer: Union[utils.AudioBuffer, "rtc.AudioFrame"],
    ) -> stt.SpeechEvent:
        """Recognize speech from buffered audio"""
        return await self._stt.recognize(buffer=buffer, language=self._language)

    async def aclose(self):
        """Close stream"""
        self._audio_buffer.clear()
