"""
OpenAI Whisper STT Provider for LiveKit
Uses original OpenAI whisper library for local speech-to-text
"""
import asyncio
import logging
import numpy as np
from typing import Optional, Union
from livekit.agents import stt, utils

logger = logging.getLogger(__name__)

try:
    import whisper
    import torch
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    logger.warning("openai-whisper not installed. Install with: pip install openai-whisper")


class OpenAIWhisperSTT(stt.STT):
    """OpenAI Whisper STT implementation"""

    def __init__(
        self,
        *,
        model_size: str = "base",
        device: str = "cpu",
        language: str = "en",
    ):
        """
        Initialize OpenAI Whisper STT provider

        Args:
            model_size: Model size ('tiny', 'tiny.en', 'base', 'base.en', 'small', 'small.en', 'medium', 'large')
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

        self._model_size = model_size
        self._device = device
        self._language = language if language else None
        self._model: Optional[whisper.Whisper] = None

        logger.info(
            f"Initialized OpenAIWhisperSTT with model={model_size}, "
            f"device={device}, language={language}"
        )

    async def _ensure_model_loaded(self):
        """Lazy load the Whisper model"""
        if self._model is None:
            import os
            from pathlib import Path

            # Set custom download directory to model_cache folder
            model_cache_dir = Path(__file__).parent.parent.parent / "model_cache" / "whisper"
            model_cache_dir.mkdir(parents=True, exist_ok=True)

            # Set environment variable for whisper to use custom cache
            os.environ['XDG_CACHE_HOME'] = str(model_cache_dir.parent)

            logger.info(f"Loading OpenAI Whisper model: {self._model_size}")
            logger.info(f"Model cache directory: {model_cache_dir}")

            loop = asyncio.get_event_loop()

            # Load model in thread pool to avoid blocking
            # Whisper will download to XDG_CACHE_HOME/whisper/ if not present
            self._model = await loop.run_in_executor(
                None,
                lambda: whisper.load_model(
                    self._model_size,
                    device=self._device,
                    download_root=str(model_cache_dir)
                )
            )

            logger.info(f"OpenAI Whisper model loaded: {self._model_size}")

    async def _recognize_impl(
        self,
        buffer: Union[utils.AudioBuffer, "rtc.AudioFrame"],
        *,
        language: Optional[str] = None,
        conn_options: Optional[any] = None,
    ) -> stt.SpeechEvent:
        """
        Implementation of speech recognition (required by STT base class)

        Args:
            buffer: Audio data to transcribe
            language: Override language (optional)
            conn_options: Connection options (ignored for local Whisper)

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
        # Force English language for transcription
        # For .en models (tiny.en, base.en, etc), this is already enforced
        # For multilingual models, this ensures English-only transcription
        result = self._model.transcribe(
            audio_data,
            language="english",  # Force English transcription
            fp16=False,  # Use FP32 for CPU
            task="transcribe",  # Use 'transcribe' not 'translate'
        )
        return result

    def _prepare_audio(self, buffer: Union[utils.AudioBuffer, "rtc.AudioFrame"]) -> np.ndarray:
        """Convert audio buffer to numpy array for Whisper"""
        try:
            # Check if it's an AudioBuffer by checking for the class name
            if hasattr(buffer, '__class__') and buffer.__class__.__name__ == 'AudioBuffer':
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

            # Handle rtc.AudioFrame or any other buffer type
            else:
                # Get frame data
                frame_data = buffer.data if hasattr(buffer, 'data') else buffer

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
            # Clear model from memory
            del self._model
            self._model = None

            # Clear CUDA cache if using GPU
            if self._device == "cuda" and torch.cuda.is_available():
                torch.cuda.empty_cache()

            logger.info("OpenAIWhisperSTT closed")
