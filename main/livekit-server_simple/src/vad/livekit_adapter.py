"""LiveKit VAD adapter for custom Silero ONNX implementation.

This module provides a wrapper that makes the custom Silero ONNX VAD
compatible with LiveKit's agent framework, allowing full control over
VAD parameters while maintaining LiveKit integration.
"""

import logging
import asyncio
from typing import Optional, AsyncIterator
from livekit import rtc
from livekit.agents import vad as livekit_vad
from .silero_onnx import SileroVADAnalyzer
from .vad_analyzer import VADParams, VADState

logger = logging.getLogger("livekit_vad_adapter")


class VADStream:
    """Async stream wrapper for VAD events.

    This class provides the async iteration interface that LiveKit expects,
    converting audio frames into VAD state events.
    """

    def __init__(self, analyzer: SileroVADAnalyzer, sample_rate: int, pre_padding_ms: int = 200):
        """Initialize the VAD stream.

        Args:
            analyzer: The underlying VAD analyzer
            sample_rate: Audio sample rate in Hz
            pre_padding_ms: Milliseconds of audio to include before speech detection
        """
        self._analyzer = analyzer
        self._sample_rate = sample_rate
        self._closed = False
        self._queue: asyncio.Queue = asyncio.Queue()
        self._last_state = VADState.QUIET
        self._collecting = False  # Currently collecting audio
        self._reached_speaking = False  # Did we reach SPEAKING state during collection?
        self._frame_buffer = []  # Buffer for audio frames during speech
        self._samples_index = 0  # Track total samples processed
        self._start_event_emitted = False  # Track if START_OF_SPEECH was emitted
        
        # Pre-padding buffer (circular buffer for recent frames)
        self._pre_padding_ms = pre_padding_ms
        frames_per_ms = sample_rate / 1000.0 / 20  # 20ms per frame typically
        self._pre_padding_frames = max(1, int(pre_padding_ms * frames_per_ms / 20))
        self._pre_buffer = []  # Circular buffer for pre-padding
        logger.info(f"🎙️ [VAD-INIT] Pre-padding: {pre_padding_ms}ms ({self._pre_padding_frames} frames)")

    def __aiter__(self) -> AsyncIterator:
        """Return self as async iterator."""
        return self

    async def __anext__(self):
        """Get next VAD event from the stream."""
        if self._closed:
            raise StopAsyncIteration

        # Wait for VAD events from push_frame
        try:
            event = await self._queue.get()
            if event is None:  # Sentinel value for stream end
                raise StopAsyncIteration
            return event
        except asyncio.CancelledError:
            raise StopAsyncIteration

    async def aclose(self):
        """Close the VAD stream asynchronously."""
        self._closed = True
        # Put sentinel value to unblock any waiting __anext__
        try:
            await asyncio.wait_for(self._queue.put(None), timeout=0.1)
        except asyncio.TimeoutError:
            pass
        logger.debug("VAD stream closed")

    def push_frame(self, frame: rtc.AudioFrame):
        """Process an audio frame through the VAD.

        Implements xiaozhi-server approach:
        1. Start collecting on ANY voice activity (STARTING)
        2. Continue collecting through SPEAKING and STOPPING
        3. Only emit START_OF_SPEECH once we confirm SPEAKING
        4. Only process if we reached SPEAKING state
        5. Discard if we never reached SPEAKING

        Args:
            frame: Audio frame from LiveKit
        """
        if self._closed:
            return

        # Update samples index
        self._samples_index += frame.samples_per_channel

        # Convert frame to bytes and analyze
        audio_data = frame.data.tobytes()
        vad_state = self._analyzer.analyze_audio(audio_data)

        # ALWAYS maintain pre-padding buffer (circular buffer)
        if not self._collecting:
            self._pre_buffer.append(frame)
            if len(self._pre_buffer) > self._pre_padding_frames:
                self._pre_buffer.pop(0)  # Remove oldest frame

        # START COLLECTING: First voice activity detected (STARTING state)
        if vad_state == VADState.STARTING and not self._collecting:
            self._collecting = True
            self._reached_speaking = False
            self._start_event_emitted = False
            
            # Initialize frame buffer with pre-padding + current frame
            self._frame_buffer = list(self._pre_buffer) + [frame]
            logger.info(f"📼 [VAD-COLLECT] Started collecting audio (STARTING detected) with {len(self._pre_buffer)} pre-padding frames")
        
        # BUFFER ALL FRAMES while collecting (STARTING, SPEAKING, STOPPING)
        elif self._collecting and vad_state in [VADState.STARTING, VADState.SPEAKING, VADState.STOPPING]:
            self._frame_buffer.append(frame)

        # TRACK SPEAKING STATE: Mark that we reached actual speech
        if vad_state == VADState.SPEAKING:
            if not self._reached_speaking:
                self._reached_speaking = True
                logger.info(f"✅ [VAD-COLLECT] Reached SPEAKING state ({len(self._frame_buffer)} frames buffered)")

            # EMIT START_OF_SPEECH only once when we confirm SPEAKING
            if not self._start_event_emitted:
                self._start_event_emitted = True
                event = livekit_vad.VADEvent(
                    type=livekit_vad.VADEventType.START_OF_SPEECH,
                    samples_index=self._samples_index,
                    timestamp=0,
                    speech_duration=0.0,
                    silence_duration=0.0,
                    frames=list(self._frame_buffer)  # Include all buffered frames
                )
                try:
                    self._queue.put_nowait(event)
                    logger.info(f"🎤 [VAD-EVENT] START_OF_SPEECH emitted ({len(self._frame_buffer)} frames, {len(self._frame_buffer) * 0.02:.2f}s)")
                except asyncio.QueueFull:
                    logger.warning("VAD event queue full, dropping START_OF_SPEECH event")

        # END COLLECTING: Reached proper silence (QUIET state)
        if vad_state == VADState.QUIET and self._collecting:
            self._collecting = False
            frames_to_send = list(self._frame_buffer)

            # CHECK: Did we reach SPEAKING state?
            if self._reached_speaking and len(frames_to_send) > 0:
                # PROCESS: We had real speech, emit END_OF_SPEECH
                event = livekit_vad.VADEvent(
                    type=livekit_vad.VADEventType.END_OF_SPEECH,
                    samples_index=self._samples_index,
                    timestamp=0,
                    speech_duration=len(frames_to_send) * 0.02,
                    silence_duration=0.0,
                    frames=frames_to_send
                )
                try:
                    self._queue.put_nowait(event)
                    logger.info(f"🔇 [VAD-EVENT] END_OF_SPEECH emitted ({len(frames_to_send)} frames, {len(frames_to_send) * 0.02:.2f}s) - Processing!")
                except asyncio.QueueFull:
                    logger.warning("VAD event queue full, dropping END_OF_SPEECH event")
            else:
                # DISCARD: Never reached SPEAKING state (false trigger)
                logger.info(f"🗑️ [VAD-DISCARD] Discarding {len(frames_to_send)} frames ({len(frames_to_send) * 0.02:.2f}s) - Never reached SPEAKING state")

            # Clear buffers after processing decision
            self._frame_buffer.clear()
            self._pre_buffer.clear()  # Clear pre-buffer for fresh start
            self._reached_speaking = False
            self._start_event_emitted = False

        # Log state transitions for debugging
        if vad_state != self._last_state:
            logger.info(f"🔄 [VAD-STATE] {self._last_state.name} → {vad_state.name}")
            self._last_state = vad_state


class LiveKitVAD:
    """LiveKit-compatible wrapper for custom Silero ONNX VAD.

    This adapter wraps the SileroVADAnalyzer to provide a LiveKit-compatible
    interface while offering full control over VAD parameters.
    """

    @classmethod
    def load(
        cls,
        *,
        model_path: str = "models/silero_vad.onnx",
        sample_rate: int = 16000,
        confidence: float = 0.5,
        start_secs: float = 0.2,
        stop_secs: float = 0.8,
        min_volume: float = 0.001,
    ):
        """Load the custom VAD with configurable parameters.

        Args:
            model_path: Path to the ONNX model file
            sample_rate: Audio sample rate (8000 or 16000 Hz)
            confidence: Confidence threshold for voice detection (0.0-1.0)
            start_secs: Delay before confirming voice start
            stop_secs: Delay before confirming voice end
            min_volume: Minimum RMS volume threshold

        Returns:
            LiveKitVAD instance configured with the specified parameters
        """
        logger.info(f"Loading custom Silero ONNX VAD from {model_path}")
        logger.info(f"VAD parameters: confidence={confidence}, start_secs={start_secs}, "
                   f"stop_secs={stop_secs}, min_volume={min_volume}")

        # Create VAD parameters
        params = VADParams(
            confidence=confidence,
            start_secs=start_secs,
            stop_secs=stop_secs,
            min_volume=min_volume
        )

        # Create analyzer with parameters
        analyzer = SileroVADAnalyzer(
            model_path=model_path,
            sample_rate=sample_rate,
            params=params
        )

        instance = cls()
        instance._analyzer = analyzer
        instance._sample_rate = sample_rate

        logger.info("✅ Custom Silero ONNX VAD loaded successfully")
        return instance

    def __init__(self):
        """Initialize the VAD adapter."""
        self._analyzer: Optional[SileroVADAnalyzer] = None
        self._sample_rate = 16000
        self._current_stream: Optional[VADStream] = None

    @property
    def analyzer(self) -> SileroVADAnalyzer:
        """Get the underlying VAD analyzer."""
        if self._analyzer is None:
            raise RuntimeError("VAD not initialized. Call load() first.")
        return self._analyzer

    @property
    def sample_rate(self) -> int:
        """Get the configured sample rate."""
        return self._sample_rate

    def stream(self, *, sample_rate: Optional[int] = None, pre_padding_ms: Optional[int] = None) -> VADStream:
        """Create a new VAD stream for processing audio.

        Args:
            sample_rate: Override sample rate for this stream
            pre_padding_ms: Milliseconds of audio to include before speech detection (uses config default if None)

        Returns:
            VADStream instance that can be used as an async iterator
        """
        if self._analyzer is None:
            raise RuntimeError("VAD not initialized. Call load() first.")

        # Close previous stream if exists
        if self._current_stream:
            asyncio.create_task(self._current_stream.aclose())

        # Get pre_padding_ms from config if not provided
        if pre_padding_ms is None:
            try:
                from ..config.config_loader import ConfigLoader
                vad_config = ConfigLoader.get_vad_config()
                pre_padding_ms = vad_config.get('pre_padding_ms', 200)
            except Exception:
                pre_padding_ms = 200  # Fallback default

        # Create new stream
        sr = sample_rate or self._sample_rate
        self._current_stream = VADStream(self._analyzer, sr, pre_padding_ms)
        logger.debug(f"Created new VAD stream with sample_rate={sr}, pre_padding={pre_padding_ms}ms")
        return self._current_stream

    def reset(self):
        """Reset the VAD analyzer state."""
        if self._analyzer:
            self._analyzer.reset()
            logger.debug("VAD state reset")

    def analyze_audio(self, audio_data: bytes) -> VADState:
        """Analyze audio data and return VAD state.

        Args:
            audio_data: Raw PCM audio bytes (16-bit signed)

        Returns:
            Current VAD state after processing
        """
        if self._analyzer is None:
            raise RuntimeError("VAD not initialized. Call load() first.")
        return self._analyzer.analyze_audio(audio_data)

    def voice_confidence(self, audio_data: bytes) -> float:
        """Calculate voice confidence for audio data.

        Args:
            audio_data: Raw PCM audio bytes (16-bit signed)

        Returns:
            Voice confidence score (0.0-1.0)
        """
        if self._analyzer is None:
            raise RuntimeError("VAD not initialized. Call load() first.")
        return self._analyzer.voice_confidence(audio_data)

    def __repr__(self) -> str:
        """String representation of the VAD instance."""
        if self._analyzer:
            params = self._analyzer.params
            return (f"LiveKitVAD(sample_rate={self._sample_rate}, "
                   f"confidence={params.confidence}, "
                   f"start_secs={params.start_secs}, "
                   f"stop_secs={params.stop_secs}, "
                   f"min_volume={params.min_volume})")
        return "LiveKitVAD(not initialized)"
