"""
Local Whisper STT Provider for LiveKit
Uses openai-whisper for local speech-to-text
"""
import asyncio
import logging
import numpy as np
import tempfile
import os
from typing import Optional, Union
from livekit.agents import stt, utils
import soundfile as sf

logger = logging.getLogger(__name__)

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    logger.warning("openai-whisper not installed. Install with: pip install openai-whisper")


class WhisperSTT(stt.STT):
    """OpenAI Whisper STT implementation for local inference"""

    def __init__(
        self,
        *,
        model: str = "base",
        device: str = "cpu",
        language: str = "en",
    ):
        """
        Initialize Whisper STT provider

        Args:
            model: Model size ('tiny', 'base', 'small', 'medium', 'large')
            device: Device to use ('cpu', 'cuda')
            language: Language code (e.g., 'en', 'es', 'fr')
        """
        super().__init__(
            capabilities=stt.STTCapabilities(streaming=False, interim_results=False)
        )

        if not WHISPER_AVAILABLE:
            raise ImportError(
                "openai-whisper is not installed. "
                "Install with: pip install openai-whisper"
            )

        self._model_size = model
        self._device = device
        self._language = language if language else None
        self._model = None

        logger.info(
            f"Initialized WhisperSTT with model={model}, "
            f"device={device}, language={language}"
        )

    async def _ensure_model_loaded(self):
        """Lazy load the Whisper model"""
        if self._model is None:
            logger.info(f"Loading Whisper model: {self._model_size}")
            loop = asyncio.get_event_loop()

            try:
                # Load model in thread pool to avoid blocking
                self._model = await loop.run_in_executor(
                    None,
                    lambda: whisper.load_model(self._model_size, device=self._device)
                )
                logger.info(f"✅ Whisper model loaded successfully: {self._model_size}")
            except Exception as e:
                logger.error(f"❌ Failed to load Whisper model '{self._model_size}': {e}")
                logger.error(f"Available models: tiny, base, small, medium, large, tiny.en, base.en, small.en, medium.en")
                raise

    async def _recognize_impl(
        self,
        buffer: Union[utils.AudioBuffer, "rtc.AudioFrame"],
        *,
        language: Optional[str] = None,
        conn_options: Optional[any] = None,
    ) -> stt.SpeechEvent:
        """
        Implementation of speech recognition

        Args:
            buffer: Audio data to transcribe
            language: Override language (optional)
            conn_options: Connection options (ignored)

        Returns:
            SpeechEvent with transcription
        """
        await self._ensure_model_loaded()

        # Convert audio to numpy array
        audio_data = self._prepare_audio(buffer)

        # Run transcription in thread pool
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            self._transcribe_sync,
            audio_data,
            language or self._language,
        )

        # Extract text from result
        text = result.get("text", "").strip()

        # Create speech event
        return stt.SpeechEvent(
            type=stt.SpeechEventType.FINAL_TRANSCRIPT,
            alternatives=[
                stt.SpeechData(
                    text=text,
                    language=language or self._language or "en",
                    confidence=1.0,
                )
            ],
        )

    def _transcribe_sync(self, audio_data: np.ndarray, language: Optional[str]):
        """Synchronous transcription (run in thread pool)"""
        # Whisper expects audio at 16kHz
        result = self._model.transcribe(
            audio_data,
            language=language,
            fp16=False,  # Use FP32 for CPU
        )
        return result

    def _prepare_audio(self, buffer: Union[utils.AudioBuffer, "rtc.AudioFrame"]) -> np.ndarray:
        """Convert audio buffer to numpy array for Whisper"""
        try:
            # Check if it's an AudioBuffer
            if hasattr(buffer, '__class__') and buffer.__class__.__name__ == 'AudioBuffer':
                audio_data = buffer.data

                # Convert to numpy array
                if isinstance(audio_data, bytes):
                    audio_np = np.frombuffer(audio_data, dtype=np.int16)
                elif isinstance(audio_data, memoryview):
                    audio_np = np.frombuffer(bytes(audio_data), dtype=np.int16)
                else:
                    audio_np = np.array(audio_data, dtype=np.float32)

                # Normalize to float32 [-1, 1]
                if audio_np.dtype == np.int16:
                    audio_np = audio_np.astype(np.float32) / 32768.0

                return audio_np

            # Handle rtc.AudioFrame
            else:
                frame_data = buffer.data if hasattr(buffer, 'data') else buffer

                if isinstance(frame_data, memoryview):
                    audio_np = np.frombuffer(bytes(frame_data), dtype=np.int16)
                else:
                    audio_np = np.frombuffer(frame_data, dtype=np.int16)

                # Normalize to float32 [-1, 1]
                audio_np = audio_np.astype(np.float32) / 32768.0

                return audio_np

        except Exception as e:
            logger.error(f"Error preparing audio: {e}")
            return np.array([], dtype=np.float32)

    async def aclose(self):
        """Cleanup resources"""
        if self._model is not None:
            self._model = None
            logger.info("WhisperSTT closed")
