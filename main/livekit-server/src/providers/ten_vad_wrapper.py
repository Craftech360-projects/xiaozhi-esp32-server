"""
TEN VAD Wrapper for LiveKit
Wraps TEN VAD to be compatible with LiveKit's VAD interface
"""

import asyncio
import logging
import time
from typing import AsyncIterator, Literal, Union
import numpy as np

from livekit import rtc
from livekit.agents import vad

logger = logging.getLogger(__name__)


class TENVAD(vad.VAD):
    """
    TEN Voice Activity Detection (VAD) wrapper for LiveKit.

    This class wraps the TEN VAD library to provide compatibility with LiveKit's VAD interface.
    TEN VAD offers superior precision and lower latency compared to Silero VAD.
    """

    @classmethod
    def load(
        cls,
        *,
        min_speech_duration: float = 0.05,
        min_silence_duration: float = 0.3,
        prefix_padding_duration: float = 0.5,
        max_buffered_speech: float = 60.0,
        activation_threshold: float = 0.5,
        sample_rate: Literal[8000, 16000] = 16000,
        hop_size: int = 160,  # TEN VAD specific: 160 samples = 10ms, 256 = 16ms
    ) -> "TENVAD":
        """
        Load and initialize the TEN VAD model.

        Args:
            min_speech_duration: Minimum duration of speech to start a new speech chunk (seconds)
            min_silence_duration: Wait this duration before ending speech (seconds)
            prefix_padding_duration: Duration of padding to add to beginning of speech (seconds)
            max_buffered_speech: Maximum duration of speech to keep in buffer (seconds)
            activation_threshold: Threshold to consider a frame as speech (0.0-1.0)
            sample_rate: Audio sample rate (8000 or 16000 Hz)
            hop_size: TEN VAD hop size in samples (160=10ms, 256=16ms)

        Returns:
            Initialized TENVAD instance
        """
        logger.info("[TEN VAD] Loading TEN VAD model...")

        try:
            from ten_vad import TenVad
        except ImportError:
            logger.error(
                "[TEN VAD] TEN VAD not installed. Install with: "
                "pip install -U git+https://github.com/TEN-framework/ten-vad.git"
            )
            raise

        # Initialize TEN VAD with hop_size and threshold
        ten_vad_model = TenVad(hop_size=hop_size, threshold=activation_threshold)
        logger.info(f"[TEN VAD] Model loaded successfully with hop_size={hop_size}, threshold={activation_threshold}")

        return cls(
            model=ten_vad_model,
            min_speech_duration=min_speech_duration,
            min_silence_duration=min_silence_duration,
            prefix_padding_duration=prefix_padding_duration,
            max_buffered_speech=max_buffered_speech,
            activation_threshold=activation_threshold,
            sample_rate=sample_rate,
            hop_size=hop_size,
        )

    def __init__(
        self,
        *,
        model,
        min_speech_duration: float,
        min_silence_duration: float,
        prefix_padding_duration: float,
        max_buffered_speech: float,
        activation_threshold: float,
        sample_rate: int,
        hop_size: int,
    ) -> None:
        # TEN VAD capabilities
        update_interval = hop_size / sample_rate  # e.g., 160/16000 = 0.01s = 10ms

        super().__init__(
            capabilities=vad.VADCapabilities(
                update_interval=update_interval,
            )
        )

        self._model = model
        self._min_speech_duration = min_speech_duration
        self._min_silence_duration = min_silence_duration
        self._prefix_padding_duration = prefix_padding_duration
        self._max_buffered_speech = max_buffered_speech
        self._activation_threshold = activation_threshold
        self._sample_rate = sample_rate
        self._hop_size = hop_size

        logger.info(
            f"[TEN VAD] Initialized with: "
            f"threshold={activation_threshold}, "
            f"min_speech={min_speech_duration}s, "
            f"min_silence={min_silence_duration}s, "
            f"sample_rate={sample_rate}Hz, "
            f"hop_size={hop_size} ({update_interval*1000:.1f}ms)"
        )

    def stream(self) -> "TENVADStream":
        """Create a new VAD stream for processing audio"""
        return TENVADStream(
            vad=self,
            model=self._model,
            min_speech_duration=self._min_speech_duration,
            min_silence_duration=self._min_silence_duration,
            prefix_padding_duration=self._prefix_padding_duration,
            max_buffered_speech=self._max_buffered_speech,
            activation_threshold=self._activation_threshold,
            sample_rate=self._sample_rate,
            hop_size=self._hop_size,
        )


class TENVADStream(vad.VADStream):
    """Stream for processing audio frames with TEN VAD"""

    def __init__(
        self,
        *,
        vad: TENVAD,
        model,
        min_speech_duration: float,
        min_silence_duration: float,
        prefix_padding_duration: float,
        max_buffered_speech: float,
        activation_threshold: float,
        sample_rate: int,
        hop_size: int,
    ) -> None:
        super().__init__(vad)

        self._model = model
        self._min_speech_duration = min_speech_duration
        self._min_silence_duration = min_silence_duration
        self._prefix_padding_duration = prefix_padding_duration
        self._max_buffered_speech = max_buffered_speech
        self._activation_threshold = activation_threshold
        self._sample_rate = sample_rate
        self._hop_size = hop_size

        # State tracking
        self._speech_started = False
        self._speech_buffer = []
        self._prefix_buffer = []
        self._silence_duration = 0.0
        self._speech_duration = 0.0

        # For resampling if needed
        self._audio_buffer = np.array([], dtype=np.int16)

        # Track resampling to log only once
        self._resampling_logged = False

    async def _main_task(self) -> None:
        """Main processing loop for audio frames"""
        try:
            async for item in self._input_ch:
                # Handle flush sentinel
                if isinstance(item, self._FlushSentinel):
                    await self._flush_speech()
                    continue

                # Process audio frame
                frame: rtc.AudioFrame = item
                inference_start = time.perf_counter()

                # Convert frame to numpy array
                audio_data = np.frombuffer(frame.data, dtype=np.int16)

                # Resample if needed (TEN VAD expects 16kHz)
                if frame.sample_rate != self._sample_rate:
                    audio_data = self._resample_audio(audio_data, frame.sample_rate, self._sample_rate)

                # Add to buffer for processing
                self._audio_buffer = np.concatenate([self._audio_buffer, audio_data])

                # Process in chunks of hop_size
                while len(self._audio_buffer) >= self._hop_size:
                    chunk = self._audio_buffer[:self._hop_size]
                    self._audio_buffer = self._audio_buffer[self._hop_size:]

                    # Run TEN VAD inference
                    # TEN VAD expects int16 audio data (not normalized)
                    # chunk is already int16 numpy array

                    # Validate chunk size
                    if len(chunk) != self._hop_size:
                        logger.warning(f"[TEN VAD] Chunk size mismatch: expected {self._hop_size}, got {len(chunk)}. Skipping.")
                        probability = 0.0
                        flags = 0
                    else:
                        # Get VAD prediction (TEN VAD returns probability and flags)
                        try:
                            # TEN VAD process method returns (probability, flags)
                            probability, flags = self._model.process(chunk)
                        except Exception as e:
                            logger.error(f"[TEN VAD] Prediction error: {e}")
                            logger.debug(f"[TEN VAD] Chunk shape: {chunk.shape}, dtype: {chunk.dtype}, hop_size: {self._hop_size}")
                            probability = 0.0
                            flags = 0

                    # Determine if speech is active
                    is_speech = probability >= self._activation_threshold

                    # Calculate frame duration
                    frame_duration = self._hop_size / self._sample_rate

                    # Update prefix buffer (for padding before speech)
                    self._prefix_buffer.append(chunk)
                    prefix_duration = len(self._prefix_buffer) * frame_duration
                    if prefix_duration > self._prefix_padding_duration:
                        self._prefix_buffer.pop(0)

                    # Process speech state
                    if is_speech:
                        # Accumulate speech
                        self._speech_buffer.append(chunk)
                        self._speech_duration += frame_duration
                        self._silence_duration = 0.0

                        # Check if we should start speech detection
                        if not self._speech_started and self._speech_duration >= self._min_speech_duration:
                            self._speech_started = True

                            # Add prefix padding at the START
                            self._speech_buffer = list(self._prefix_buffer) + self._speech_buffer

                            # Emit START_OF_SPEECH event
                            start_event = vad.VADEvent(
                                type=vad.VADEventType.START_OF_SPEECH,
                                samples_index=0,
                                timestamp=time.time(),
                                speech_duration=self._speech_duration,
                                silence_duration=0.0,
                                probability=probability,
                                inference_duration=time.perf_counter() - inference_start,
                            )
                            self._event_ch.send_nowait(start_event)
                            logger.info(f"[TEN VAD] START_OF_SPEECH (duration={self._speech_duration:.3f}s, threshold={self._min_speech_duration}s)")

                    else:
                        # Silence detected
                        if self._speech_started:
                            self._silence_duration += frame_duration
                            self._speech_buffer.append(chunk)  # Include trailing silence

                            # Check if silence duration exceeds threshold
                            if self._silence_duration >= self._min_silence_duration:
                                # End of speech
                                await self._emit_speech_chunk()
                        else:
                            # Not in speech yet - reset accumulated speech if any
                            if self._speech_duration > 0:
                                self._speech_duration = 0.0
                                self._speech_buffer = []

                    # Emit inference done event
                    inference_event = vad.VADEvent(
                        type=vad.VADEventType.INFERENCE_DONE,
                        samples_index=0,
                        timestamp=time.time(),
                        speech_duration=self._speech_duration,
                        silence_duration=self._silence_duration,
                        probability=probability,
                        inference_duration=time.perf_counter() - inference_start,
                    )
                    self._event_ch.send_nowait(inference_event)

            # End of input - flush remaining speech
            await self._flush_speech()

        except Exception as e:
            logger.error(f"[TEN VAD] Error in main task: {e}", exc_info=True)
            raise

    async def _emit_speech_chunk(self) -> None:
        """Emit a complete speech chunk"""
        if not self._speech_buffer:
            return

        # Concatenate all speech frames
        speech_array = np.concatenate(self._speech_buffer)

        # Convert back to int16
        speech_int16 = speech_array.astype(np.int16)

        # Create audio frame
        speech_frame = rtc.AudioFrame(
            data=speech_int16.tobytes(),
            sample_rate=self._sample_rate,
            num_channels=1,
            samples_per_channel=len(speech_int16),
        )

        # Emit END_OF_SPEECH event with the speech data
        end_event = vad.VADEvent(
            type=vad.VADEventType.END_OF_SPEECH,
            samples_index=0,
            timestamp=time.time(),
            speech_duration=self._speech_duration,
            silence_duration=self._silence_duration,
            frames=[speech_frame],
            probability=1.0,
            inference_duration=0.0,
        )
        self._event_ch.send_nowait(end_event)

        # Log detailed info about the speech chunk
        logger.info(
            f"[TEN VAD] 🎤 END_OF_SPEECH: duration={self._speech_duration:.2f}s, "
            f"samples={len(speech_int16)}, "
            f"sample_rate={self._sample_rate}Hz, "
            f"audio_size={len(speech_int16.tobytes())} bytes"
        )

        # Reset state
        self._speech_started = False
        self._speech_buffer = []
        self._speech_duration = 0.0
        self._silence_duration = 0.0

    async def _flush_speech(self) -> None:
        """Flush any remaining speech in the buffer"""
        if self._speech_started and self._speech_buffer:
            await self._emit_speech_chunk()

    def _resample_audio(self, audio: np.ndarray, from_rate: int, to_rate: int) -> np.ndarray:
        """Resample audio from one sample rate to another"""
        if from_rate == to_rate:
            return audio

        # Log resampling only once
        if not self._resampling_logged:
            logger.info(f"[TEN VAD] Resampling audio: {from_rate}Hz → {to_rate}Hz")
            self._resampling_logged = True

        try:
            # Try using scipy for better quality resampling
            from scipy import signal
            # Calculate number of output samples
            num_samples = int(len(audio) * to_rate / from_rate)
            # Use scipy's resample for high-quality resampling
            resampled = signal.resample(audio, num_samples).astype(np.int16)
            return resampled
        except ImportError:
            # Fallback to simple linear interpolation
            ratio = to_rate / from_rate
            new_length = int(len(audio) * ratio)
            indices = np.linspace(0, len(audio) - 1, new_length)
            resampled = np.interp(indices, np.arange(len(audio)), audio).astype(np.int16)
            return resampled
