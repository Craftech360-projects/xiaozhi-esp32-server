"""FunASR Local Speech-to-Text Provider for LiveKit"""

import os
import time
import psutil
import asyncio
from typing import Optional
from funasr import AutoModel
from funasr.utils.postprocess_utils import rich_transcription_postprocess
from livekit import agents
from livekit.agents import stt
import logging

logger = logging.getLogger(__name__)

class FunASRSTT(stt.STT):
    """
    FunASR Local Inference Provider for LiveKit

    Provides multilingual speech-to-text using Alibaba's FunASR
    with local inference (no API calls required).

    Features:
    - Multilingual: Chinese, English, Japanese, Korean
    - Built-in VAD
    - ITN (Inverse Text Normalization)
    - Privacy-preserving (all processing local)
    - Zero API costs
    """

    def __init__(
        self,
        *,
        model_dir: str = "model_cache/funasr/iic/SenseVoiceSmall",
        language: str = "auto",
        use_itn: bool = True,
        max_single_segment_time: int = 30000,
        min_silence_duration: int = 800,
        speech_noise_thres: float = 0.6,
        device: str = "cpu",
    ):
        """
        Initialize FunASR STT provider

        Args:
            model_dir: Path to local model directory
            language: Language code ('auto', 'zh', 'en', 'ja', 'ko')
            use_itn: Enable Inverse Text Normalization
            max_single_segment_time: Max VAD segment duration (ms)
            min_silence_duration: Min silence to split segments (ms)
            speech_noise_thres: Speech/noise threshold (0.0-1.0)
            device: Compute device ('cpu' or 'cuda:0')
        """
        super().__init__(
            capabilities=stt.STTCapabilities(
                streaming=False,  # FunASR processes complete audio segments
                interim_results=False  # Only returns final transcripts
            )
        )

        self.model_dir = model_dir
        self.language = language
        self.use_itn = use_itn
        self.max_single_segment_time = max_single_segment_time
        self.min_silence_duration = min_silence_duration
        self.speech_noise_thres = speech_noise_thres
        self.device = device

        logger.info(f"FunASR provider initialized with language: {self.language}")

        # Memory check - require 2GB minimum
        self._check_memory()

        # Initialize model
        self.model = None
        self._initialize_model()

    def _check_memory(self):
        """Check system has sufficient memory"""
        min_mem_bytes = 2 * 1024 * 1024 * 1024  # 2GB
        total_mem = psutil.virtual_memory().total

        if total_mem < min_mem_bytes:
            raise RuntimeError(
                f"Insufficient memory for FunASR: "
                f"{total_mem / (1024**3):.2f}GB available, "
                f"minimum 2GB required"
            )

        logger.info(
            f"FunASR memory check passed: "
            f"{total_mem / (1024**3):.2f}GB available"
        )

    def _initialize_model(self):
        """Initialize FunASR model (uses cached model if available)"""
        try:
            logger.info(f"Loading FunASR model from {self.model_dir}")

            if not os.path.exists(self.model_dir):
                raise FileNotFoundError(
                    f"FunASR model not found at {self.model_dir}. "
                    f"Run: python scripts/download_funasr_model.py"
                )

            # Try to get cached model first
            # Build VAD kwargs with all parameters
            vad_kwargs = {
                "max_single_segment_time": self.max_single_segment_time,
                "min_silence_duration": self.min_silence_duration,
                "speech_noise_thres": self.speech_noise_thres,
            }

            try:
                from src.utils.model_cache import ModelCache

                config = {
                    'model_dir': self.model_dir,
                    'device': self.device,
                    'max_single_segment_time': self.max_single_segment_time,
                    'min_silence_duration': self.min_silence_duration,
                    'speech_noise_thres': self.speech_noise_thres,
                }

                model_cache = ModelCache()
                self.model = model_cache.get_funasr_model(config)
            except Exception as cache_error:
                # Fallback to direct loading if cache fails
                logger.warning(f"Model cache unavailable, loading directly: {cache_error}")

                self.model = AutoModel(
                    model=self.model_dir,
                    vad_kwargs=vad_kwargs,
                    disable_update=True,
                    hub="hf",
                    device=self.device
                )

            logger.info(
                f"FunASR model loaded successfully "
                f"(device={self.device}, language={self.language})"
            )

        except Exception as e:
            logger.error(f"Failed to load FunASR model: {e}")
            raise

    async def _recognize_impl(
        self,
        buffer: "agents.AudioFrame",
        *,
        language: Optional[str] = None,
        **kwargs  # Accept additional arguments like conn_options
    ) -> stt.SpeechEvent:
        """
        Recognize speech from audio frame (internal implementation)

        Args:
            buffer: Audio frame from LiveKit
            language: Optional language override
            **kwargs: Additional arguments from LiveKit (e.g., conn_options)

        Returns:
            SpeechEvent with transcription
        """
        try:
            start_time = time.time()

            # Convert AudioBuffer to PCM bytes
            audio_data = self._buffer_to_pcm(buffer)

            if len(audio_data) == 0:
                logger.warning("Empty audio buffer received")
                return self._empty_result()

            # Determine language to use
            lang_to_use = language or self.language
            logger.info(f"FunASR recognizing with language: {lang_to_use}")

            # Run inference in thread pool to avoid blocking event loop
            result = await asyncio.to_thread(
                self.model.generate,
                input=audio_data,
                cache={},
                language=lang_to_use,
                use_itn=self.use_itn,
                batch_size_s=60,
            )

            # Post-process
            text = rich_transcription_postprocess(result[0]["text"])

            elapsed = time.time() - start_time
            logger.info(
                f"FunASR transcription completed in {elapsed:.2f}s: "
                f"'{text}' (length={len(audio_data)} bytes, language={lang_to_use})"
            )

            # Return SpeechEvent
            return stt.SpeechEvent(
                type=stt.SpeechEventType.FINAL_TRANSCRIPT,
                alternatives=[
                    stt.SpeechData(
                        text=text,
                        language=lang_to_use,
                        confidence=1.0  # FunASR doesn't provide confidence
                    )
                ]
            )

        except Exception as e:
            logger.error(f"FunASR recognition error: {e}", exc_info=True)
            return self._empty_result()

    def _buffer_to_pcm(self, buffer: "agents.AudioFrame") -> bytes:
        """
        Convert LiveKit AudioFrame to PCM bytes

        FunASR expects:
        - Sample rate: 16kHz
        - Bit depth: 16-bit
        - Channels: Mono

        Args:
            buffer: LiveKit audio frame

        Returns:
            PCM audio bytes
        """
        # AudioFrame has a data attribute (numpy array)
        if not hasattr(buffer, 'data') or buffer.data is None:
            return b""

        # Convert numpy array to bytes
        # LiveKit AudioFrame.data is already in PCM format
        pcm_data = buffer.data.tobytes()

        return pcm_data

    def _empty_result(self) -> stt.SpeechEvent:
        """Return empty speech event"""
        return stt.SpeechEvent(
            type=stt.SpeechEventType.FINAL_TRANSCRIPT,
            alternatives=[
                stt.SpeechData(
                    text="",
                    language=self.language,
                    confidence=0.0
                )
            ]
        )
