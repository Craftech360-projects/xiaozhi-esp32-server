"""Voice Activity Detection (VAD) analyzer base classes and utilities.

This module provides the abstract base class for VAD analyzers and associated
data structures for voice activity detection in audio streams.

Adapted from xiaozhi-server for LiveKit integration.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional
from pydantic import BaseModel
import numpy as np
import logging
import wave
import os
from datetime import datetime

logger = logging.getLogger("vad_analyzer")

# Default VAD parameters
VAD_CONFIDENCE = 0.4
VAD_START_SECS = 0.2
VAD_STOP_SECS = 0.8
VAD_MIN_VOLUME = 0.001  # Very low default - essentially confidence-only detection


class VADState(Enum):
    """Voice Activity Detection states.

    States:
        QUIET: No voice activity detected
        STARTING: Voice activity beginning, transitioning from quiet
        SPEAKING: Active voice detected and confirmed
        STOPPING: Voice activity ending, transitioning to quiet
    """
    QUIET = 1
    STARTING = 2
    SPEAKING = 3
    STOPPING = 4


class VADParams(BaseModel):
    """Configuration parameters for Voice Activity Detection.

    Attributes:
        confidence: Minimum confidence threshold for voice detection (0.0-1.0)
        start_secs: Duration to wait before confirming voice start
        stop_secs: Duration to wait before confirming voice stop
        min_volume: Minimum audio volume threshold for voice detection
        save_audio: Whether to save collected audio as WAV files
        audio_save_dir: Directory to save audio files (default: "vad_audio_captures")
    """
    confidence: float = VAD_CONFIDENCE
    start_secs: float = VAD_START_SECS
    stop_secs: float = VAD_STOP_SECS
    min_volume: float = VAD_MIN_VOLUME
    save_audio: bool = True
    audio_save_dir: str = "vad_audio_captures"


def calculate_audio_volume(audio: bytes, sample_rate: int) -> float:
    """Calculate RMS volume of audio data.

    Args:
        audio: Raw audio bytes
        sample_rate: Audio sample rate in Hz

    Returns:
        RMS volume normalized to 0.0-1.0 range
    """
    audio_int16 = np.frombuffer(audio, dtype=np.int16)
    audio_float32 = audio_int16.astype(np.float32) / 32768.0
    rms = np.sqrt(np.mean(audio_float32 ** 2))
    return float(rms)


def exp_smoothing(current: float, previous: float, factor: float) -> float:
    """Apply exponential smoothing to a value.

    Args:
        current: Current value
        previous: Previous smoothed value
        factor: Smoothing factor (0.0-1.0)

    Returns:
        Smoothed value
    """
    return factor * current + (1 - factor) * previous


class VADAnalyzer(ABC):
    """Abstract base class for Voice Activity Detection analyzers.

    Provides the framework for implementing VAD analysis with configurable
    parameters, state management, and audio processing capabilities.
    """

    def __init__(self, *, sample_rate: Optional[int] = None, params: Optional[VADParams] = None):
        """Initialize the VAD analyzer.

        Args:
            sample_rate: Audio sample rate in Hz. If None, will be set later
            params: VAD parameters for detection configuration
        """
        self._init_sample_rate = sample_rate
        self._sample_rate = 0
        self._params = params or VADParams()
        self._num_channels = 1

        self._vad_buffer = b""

        # Volume exponential smoothing
        self._smoothing_factor = 0.2
        self._prev_volume = 0

        # Initialize VAD state variables
        self._vad_state = VADState.QUIET
        self._vad_starting_count = 0
        self._vad_stopping_count = 0
        self._vad_frames = 0
        self._vad_frames_num_bytes = 0
        self._vad_start_frames = 0
        self._vad_stop_frames = 0

        # Audio collection for triggered sessions
        self._audio_collection_active = False
        self._collected_audio_buffer = b""
        self._collection_start_time = None
        self._audio_file_counter = 0
        
        # Create audio save directory if needed
        if self._params.save_audio:
            self._ensure_audio_save_dir()

    @property
    def sample_rate(self) -> int:
        """Get the current sample rate."""
        return self._sample_rate

    @property
    def num_channels(self) -> int:
        """Get the number of audio channels."""
        return self._num_channels

    @property
    def params(self) -> VADParams:
        """Get the current VAD parameters."""
        return self._params

    @abstractmethod
    def num_frames_required(self) -> int:
        """Get the number of audio frames required for analysis."""
        pass

    @abstractmethod
    def voice_confidence(self, buffer: bytes) -> float:
        """Calculate voice activity confidence for the given audio buffer.

        Args:
            buffer: Audio buffer to analyze

        Returns:
            Voice confidence score between 0.0 and 1.0
        """
        pass

    def set_sample_rate(self, sample_rate: int):
        """Set the sample rate for audio processing.

        Args:
            sample_rate: Audio sample rate in Hz
        """
        self._sample_rate = self._init_sample_rate or sample_rate
        self.set_params(self._params)

    def set_params(self, params: VADParams):
        """Set VAD parameters and recalculate internal values.

        Args:
            params: VAD parameters for detection configuration
        """
        logger.debug(f"Setting VAD params to: {params}")
        self._params = params
        self._vad_frames = self.num_frames_required()
        self._vad_frames_num_bytes = self._vad_frames * self._num_channels * 2

        vad_frames_per_sec = self._vad_frames / self.sample_rate if self.sample_rate > 0 else 1

        self._vad_start_frames = round(self._params.start_secs / vad_frames_per_sec)
        self._vad_stop_frames = round(self._params.stop_secs / vad_frames_per_sec)
        self._vad_starting_count = 0
        self._vad_stopping_count = 0
        self._vad_state: VADState = VADState.QUIET
        
        # Create audio save directory if needed
        if self._params.save_audio:
            self._ensure_audio_save_dir()

    def _ensure_audio_save_dir(self):
        """Ensure the audio save directory exists."""
        try:
            if not os.path.exists(self._params.audio_save_dir):
                os.makedirs(self._params.audio_save_dir)
                logger.info(f"Created audio save directory: {self._params.audio_save_dir}")
        except Exception as e:
            logger.error(f"Failed to create audio save directory: {e}")

    def _start_audio_collection(self):
        """Start collecting audio frames."""
        if not self._audio_collection_active:
            self._audio_collection_active = True
            self._collected_audio_buffer = b""
            self._collection_start_time = datetime.now()
            self._reached_speaking_state = False  # Track if we actually reached SPEAKING
            logger.info("Started audio collection for VAD trigger")

    def _stop_audio_collection_and_save(self):
        """Stop collecting audio and save to WAV file."""
        if self._audio_collection_active and self._params.save_audio:
            self._audio_collection_active = False
            
            # Only save if we actually reached SPEAKING state and have meaningful audio
            if (len(self._collected_audio_buffer) > 0 and 
                hasattr(self, '_reached_speaking_state') and 
                self._reached_speaking_state):
                try:
                    # Generate filename with timestamp
                    timestamp = self._collection_start_time.strftime("%Y%m%d_%H%M%S")
                    self._audio_file_counter += 1
                    filename = f"vad_audio_{timestamp}_{self._audio_file_counter:03d}.wav"
                    filepath = os.path.join(self._params.audio_save_dir, filename)
                    
                    # SIMPLIFIED: Use 16kHz consistently throughout the pipeline
                    # ESP32 sends 16kHz audio, keep it at 16kHz to avoid conversion issues
                    # This ensures natural speech speed and eliminates sample rate confusion
                    effective_sample_rate = 16000  # Native ESP32 sample rate
                    
                    # Save original audio without trimming (as requested)
                    with wave.open(filepath, 'wb') as wav_file:
                        wav_file.setnchannels(self._num_channels)
                        wav_file.setsampwidth(2)  # 16-bit audio
                        wav_file.setframerate(effective_sample_rate)  # Use effective sample rate
                        wav_file.writeframes(self._collected_audio_buffer)
                    
                    duration = len(self._collected_audio_buffer) / (effective_sample_rate * self._num_channels * 2)
                    logger.info(f"Saved VAD audio: {filepath} (duration: {duration:.2f}s, size: {len(self._collected_audio_buffer)} bytes, rate: {effective_sample_rate}Hz)")
                    
                except Exception as e:
                    logger.error(f"Failed to save audio file: {e}")
            elif len(self._collected_audio_buffer) > 0:
                # Log that we're not saving because no real speech was detected
                duration = len(self._collected_audio_buffer) / (16000 * self._num_channels * 2)
                logger.info(f"Not saving VAD audio (no SPEAKING state reached): {duration:.2f}s, {len(self._collected_audio_buffer)} bytes")
            
            # DON'T clear the buffer immediately - let external systems access it first
            # self._collected_audio_buffer = b""  # Commented out

    def get_collected_audio(self) -> bytes:
        """Get the collected audio buffer (original, no trimming) and clear it."""
        if len(self._collected_audio_buffer) == 0:
            return b""
        
        # Return original audio without trimming (as requested)
        audio_data = self._collected_audio_buffer
        
        # Log for debugging
        duration = len(audio_data) / (16000 * self._num_channels * 2)
        logger.debug(f"🎯 [STT-AUDIO] Providing original audio: {duration:.2f}s, {len(audio_data)} bytes")
        
        # Clear the buffer after getting
        self._collected_audio_buffer = b""
        
        return audio_data

    def _collect_audio_frame(self, audio_data: bytes):
        """Collect audio frame if collection is active."""
        if self._audio_collection_active:
            # Debug: Log audio data size periodically
            if not hasattr(self, '_collect_debug_counter'):
                self._collect_debug_counter = 0
            self._collect_debug_counter += 1
            
            if self._collect_debug_counter % 50 == 0:  # Log every 50th collection
                logger.debug(f"🔍 [COLLECT-DEBUG] Collecting audio chunk: {len(audio_data)} bytes, "
                            f"Total buffer: {len(self._collected_audio_buffer)} bytes")
            
            self._collected_audio_buffer += audio_data


        


    def _get_smoothed_volume(self, audio: bytes) -> float:
        """Calculate smoothed audio volume using exponential smoothing."""
        volume = calculate_audio_volume(audio, self.sample_rate)
        return exp_smoothing(volume, self._prev_volume, self._smoothing_factor)

    def reset(self):
        """Reset the VAD analyzer to initial state."""
        self._vad_buffer = b""
        self._vad_state = VADState.QUIET
        self._vad_starting_count = 0
        self._vad_stopping_count = 0
        self._prev_volume = 0
        
        # Stop any active audio collection and save
        if self._audio_collection_active:
            self._stop_audio_collection_and_save()

    def analyze_audio(self, buffer: bytes) -> VADState:
        """Analyze audio buffer and return current VAD state.

        Processes incoming audio data, maintains internal state, and determines
        voice activity status based on confidence and volume thresholds.
        Collects all audio frames once VAD is triggered until proper completion.

        Args:
            buffer: Audio buffer to analyze

        Returns:
            Current VAD state after processing the buffer
        """
        # Always collect audio if collection is active (original behavior restored)
        if self._audio_collection_active:
            self._collect_audio_frame(buffer)

        self._vad_buffer += buffer

        num_required_bytes = self._vad_frames_num_bytes
        if len(self._vad_buffer) < num_required_bytes:
            return self._vad_state

        previous_state = self._vad_state

        while len(self._vad_buffer) >= num_required_bytes:
            audio_frames = self._vad_buffer[:num_required_bytes]
            self._vad_buffer = self._vad_buffer[num_required_bytes:]

            confidence = self.voice_confidence(audio_frames)

            volume = self._get_smoothed_volume(audio_frames)
            self._prev_volume = volume

            speaking = confidence >= self._params.confidence and volume >= self._params.min_volume

            # Debug logging for troubleshooting
            if not hasattr(self, '_debug_log_counter'):
                self._debug_log_counter = 0
            self._debug_log_counter += 1

            if self._debug_log_counter % 100 == 0:  # Reduced from 10 to 100
                collection_status = "COLLECTING" if self._audio_collection_active else "NOT_COLLECTING"
                logger.debug(f"VAD analysis: confidence={confidence:.3f} (threshold={self._params.confidence}), "
                           f"volume={volume:.4f} (threshold={self._params.min_volume}), "
                           f"speaking={speaking}, state={self._vad_state.name}, {collection_status}")

            if speaking:
                if self._vad_state == VADState.QUIET:
                    self._vad_state = VADState.STARTING
                    self._vad_starting_count = 1
                elif self._vad_state == VADState.STARTING:
                    self._vad_starting_count += 1
                elif self._vad_state == VADState.STOPPING:
                    self._vad_state = VADState.SPEAKING
                    self._vad_stopping_count = 0
            else:
                if self._vad_state == VADState.STARTING:
                    self._vad_state = VADState.QUIET
                    self._vad_starting_count = 0
                elif self._vad_state == VADState.SPEAKING:
                    self._vad_state = VADState.STOPPING
                    self._vad_stopping_count = 1
                elif self._vad_state == VADState.STOPPING:
                    self._vad_stopping_count += 1

        # Handle state transitions
        if (self._vad_state == VADState.STARTING and
            self._vad_starting_count >= self._vad_start_frames):
            self._vad_state = VADState.SPEAKING
            self._vad_starting_count = 0
            # Mark that we reached actual SPEAKING state
            if hasattr(self, '_reached_speaking_state'):
                self._reached_speaking_state = True

        if (self._vad_state == VADState.STOPPING and
            self._vad_stopping_count >= self._vad_stop_frames):
            self._vad_state = VADState.QUIET
            self._vad_stopping_count = 0

        # Audio collection logic: Only collect if save_audio is enabled
        # (When used with complete STT integration, this should be disabled)
        if self._params.save_audio:
            if previous_state == VADState.QUIET and self._vad_state == VADState.STARTING:
                # VAD just triggered - start collecting audio
                self._start_audio_collection()
            elif previous_state != VADState.QUIET and self._vad_state == VADState.QUIET:
                # VAD session ended - stop collecting and save audio
                self._stop_audio_collection_and_save()

        return self._vad_state
