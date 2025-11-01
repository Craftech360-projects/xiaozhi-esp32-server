"""
Custom Silero VAD wrapper for LiveKit optimized for kids' voices.

This module provides a wrapper that uses the local ONNX model and makes it
much more sensitive to detect soft children's voices.
"""

import os
import logging
import numpy as np
import time
from livekit.plugins import silero

logger = logging.getLogger(__name__)

# Try to import ONNX runtime
try:
    import onnxruntime
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False
    logger.warning("ONNX runtime not available, falling back to default VAD")

# Model reset interval to prevent memory growth
_MODEL_RESET_STATES_TIME = 5.0


class SileroOnnxModel:
    """ONNX runtime wrapper for the local Silero VAD model."""
    
    def __init__(self, model_path: str, force_onnx_cpu: bool = True):
        """Initialize the Silero ONNX model.
        
        Args:
            model_path: Path to the ONNX model file
            force_onnx_cpu: Whether to force CPU execution
        """
        opts = onnxruntime.SessionOptions()
        opts.inter_op_num_threads = 1
        opts.intra_op_num_threads = 1
        
        if force_onnx_cpu and "CPUExecutionProvider" in onnxruntime.get_available_providers():
            self.session = onnxruntime.InferenceSession(
                model_path, providers=["CPUExecutionProvider"], sess_options=opts
            )
        else:
            self.session = onnxruntime.InferenceSession(model_path, sess_options=opts)
            
        self.reset_states()
        self.sample_rates = [8000, 16000]
        logger.info(f"Loaded local ONNX Silero VAD model from: {model_path}")
        
    def reset_states(self, batch_size: int = 1):
        """Reset the internal model states."""
        self._state = np.zeros((2, batch_size, 128), dtype="float32")
        self._context = np.zeros((batch_size, 0), dtype="float32")
        self._last_sr = 0
        self._last_batch_size = 0
        
    def __call__(self, x: np.ndarray, sr: int) -> np.ndarray:
        """Process audio input through the VAD model."""
        # Validate input
        if np.ndim(x) == 1:
            x = np.expand_dims(x, 0)
            
        num_samples = 512 if sr == 16000 else 256
        if np.shape(x)[-1] != num_samples:
            # Pad or truncate to required size
            current_samples = np.shape(x)[-1]
            if current_samples < num_samples:
                padding = num_samples - current_samples
                x = np.pad(x, ((0, 0), (0, padding)), mode='constant')
            else:
                x = x[:, :num_samples]
        
        batch_size = np.shape(x)[0]
        context_size = 64 if sr == 16000 else 32
        
        # Reset states if needed
        if not self._last_batch_size:
            self.reset_states(batch_size)
        if (self._last_sr) and (self._last_sr != sr):
            self.reset_states(batch_size)
        if (self._last_batch_size) and (self._last_batch_size != batch_size):
            self.reset_states(batch_size)
            
        if not np.shape(self._context)[1]:
            self._context = np.zeros((batch_size, context_size), dtype="float32")
            
        x = np.concatenate((self._context, x), axis=1)
        
        # Run inference
        ort_inputs = {"input": x, "state": self._state, "sr": np.array(sr, dtype="int64")}
        ort_outs = self.session.run(None, ort_inputs)
        out, state = ort_outs
        self._state = state
        
        self._context = x[..., -context_size:]
        self._last_sr = sr
        self._last_batch_size = batch_size
        
        return out


class KidsOptimizedVADWrapper:
    """
    Wrapper that uses local ONNX Silero VAD model with kids-specific optimizations.
    
    This wrapper uses your local silero_vad.onnx model and applies kids-specific optimizations:
    - ULTRA low confidence thresholds for whispers
    - Volume boosting for soft voices
    - Smoothing to reduce false negatives
    - Direct ONNX model usage for better control
    """
    
    def __init__(self, model_path=None):
        """Initialize the kids-optimized VAD wrapper.
        
        Args:
            model_path: Path to the local ONNX model
        """
        self._confidence_history = []
        self._volume_history = []
        self._call_count = 0
        self._last_reset_time = time.time()
        
        # Kids-optimized parameters - OPTIMIZED FOR BUFFERED AUDIO MODE
        self.sensitivity_threshold = 0.001  # MAXIMUM sensitivity (1000x more than default!)
        self.start_secs = 0.05             # INSTANT voice start confirmation
        self.stop_secs = 2.0               # ← Reduced from 5.0s for faster response in buffered mode
        self.min_volume_threshold = 0.00001 # ULTRA sensitive minimum volume (100x more sensitive)
        self.pre_padding_ms = 1200         # Extra long audio padding
        self.volume_boost_factor = 10.0    # MAXIMUM boost for quiet audio
        self.smoothing_window = 10         # Maximum smoothing for stability
        
        # Try to load local ONNX model
        self._use_onnx = False
        self._onnx_model = None
        
        if ONNX_AVAILABLE and model_path and os.path.exists(model_path):
            try:
                self._onnx_model = SileroOnnxModel(model_path)
                self._use_onnx = True
                logger.info(f"Using LOCAL ONNX Silero VAD model: {model_path}")
            except Exception as e:
                logger.error(f"Failed to load local ONNX model: {e}")
        
        # Always create a fallback VAD for compatibility
        self._base_vad = silero.VAD.load()
        if not self._use_onnx:
            logger.warning("Using default LiveKit VAD as fallback")
        
        logger.info("🎤 Kids VAD Wrapper initialized with MAXIMUM SENSITIVITY:")
        logger.info(f"  📁 Using local ONNX model: {self._use_onnx}")
        logger.info(f"  🎯 Confidence threshold: {self.sensitivity_threshold} (vs default ~0.5) - 500x MORE SENSITIVE!")
        logger.info(f"  ⚡ Start confirmation: {self.start_secs}s (INSTANT response)")
        logger.info(f"  ⏳ Stop confirmation: {self.stop_secs}s (prevents splitting speech)")
        logger.info(f"  🔇 Min volume threshold: {self.min_volume_threshold} (MAXIMUM whisper-level)")
        logger.info(f"  📏 Pre-padding: {self.pre_padding_ms}ms (extra long padding)")
        logger.info(f"  🔊 Volume boost factor: {self.volume_boost_factor}x (MAXIMUM boost)")
        logger.info(f"  📊 Smoothing window: {self.smoothing_window} frames (maximum smoothing)")
        logger.info("🚀 VAD is ready to detect EVEN THE SOFTEST children's whispers!")
        
        # Initialize state tracking
        self._last_voice_state = False
    
    def __call__(self, audio_bytes, sample_rate):
        """
        Process audio with kids-optimized VAD detection using local ONNX model.
        
        Args:
            audio_bytes: Raw audio data as bytes
            sample_rate: Audio sample rate
            
        Returns:
            Enhanced confidence score optimized for kids' voices
        """
        try:
            # Convert audio bytes to numpy array
            audio_int16 = np.frombuffer(audio_bytes, np.int16)
            audio_float32 = audio_int16.astype(np.float32) / 32768.0
            volume = float(np.sqrt(np.mean(audio_float32 ** 2)))
            
            # Get VAD confidence
            if self._use_onnx:
                # Use local ONNX model
                confidence = self._get_onnx_confidence(audio_float32, sample_rate)
            else:
                # Fallback to default VAD
                confidence = self._base_vad(audio_bytes, sample_rate)
            
            # Apply kids-specific optimizations
            enhanced_confidence = self._enhance_for_kids(confidence, volume, audio_float32)
            
            # Log VAD state changes and detections
            self._call_count += 1
            
            # Track VAD state changes (MAXIMUM sensitivity to see ALL activity)
            is_voice_detected = enhanced_confidence > 0.01  # ULTRA low threshold for "voice detected" logging
            
            # Log state changes
            if not hasattr(self, '_last_voice_state'):
                self._last_voice_state = False
                
            if is_voice_detected != self._last_voice_state:
                state = "VOICE_DETECTED" if is_voice_detected else "SILENCE"
                model_type = "ONNX" if self._use_onnx else "Default"
                logger.info(f"🎤 VAD STATE CHANGE: {state} | Model: {model_type} | "
                           f"Confidence: {confidence:.4f}→{enhanced_confidence:.4f} | "
                           f"Volume: {volume:.5f}")
                self._last_voice_state = is_voice_detected
            
            # Log periodic stats for monitoring
            if self._call_count % 50 == 0:  # Every 50 calls (~1-2 seconds)
                model_type = "ONNX" if self._use_onnx else "Default"
                avg_recent_conf = sum(self._confidence_history[-5:]) / min(5, len(self._confidence_history))
                avg_recent_vol = sum(self._volume_history[-5:]) / min(5, len(self._volume_history))
                logger.debug(f"📊 VAD Stats ({model_type}): avg_conf={avg_recent_conf:.4f}, "
                           f"avg_vol={avg_recent_vol:.5f}, calls={self._call_count}")
            
            # Log significant confidence boosts
            if enhanced_confidence > confidence * 1.5 and enhanced_confidence > 0.2:
                logger.info(f"🚀 VAD BOOST: {confidence:.4f}→{enhanced_confidence:.4f} | "
                           f"Volume: {volume:.5f} | Reason: Kids voice enhancement")
            
            return enhanced_confidence
            
        except Exception as e:
            logger.error(f"Kids VAD wrapper error: {e}")
            return 0.0
    
    def _get_onnx_confidence(self, audio_data: np.ndarray, sample_rate: int) -> float:
        """Get confidence from local ONNX model."""
        try:
            confidence = self._onnx_model(audio_data, sample_rate)[0]
            
            # Reset model periodically
            curr_time = time.time()
            if curr_time - self._last_reset_time >= _MODEL_RESET_STATES_TIME:
                self._onnx_model.reset_states()
                self._last_reset_time = curr_time
            
            return float(confidence.item() if hasattr(confidence, 'item') else confidence)
            
        except Exception as e:
            logger.error(f"ONNX inference error: {e}")
            return 0.0
    
    def _enhance_for_kids(self, original_confidence, volume, audio_data):
        """
        Apply kids-specific enhancements to VAD confidence.
        
        Args:
            original_confidence: Original VAD confidence score
            volume: Audio volume (RMS)
            audio_data: Audio data as float32 numpy array
            
        Returns:
            Enhanced confidence score
        """
        # Store history for smoothing
        self._confidence_history.append(original_confidence)
        self._volume_history.append(volume)
        
        # Keep only recent history
        if len(self._confidence_history) > self.smoothing_window:
            self._confidence_history.pop(0)
        if len(self._volume_history) > self.smoothing_window:
            self._volume_history.pop(0)
        
        # Calculate smoothed values
        avg_confidence = sum(self._confidence_history) / len(self._confidence_history)
        avg_volume = sum(self._volume_history) / len(self._volume_history)
        
        # Enhancement 1: MAXIMUM sensitivity for kids' whispers (0.001 confidence)
        if avg_confidence >= self.sensitivity_threshold:
            enhanced_confidence = min(1.0, avg_confidence * 5.0)  # MAXIMUM boost for detected speech
        else:
            # AGGRESSIVE boost for ANY signal from kids
            if avg_confidence > 0.0001:  # Even tinier signals
                enhanced_confidence = avg_confidence * 10.0  # MASSIVE boost
                logger.info(f"🔥 MICRO-SIGNAL BOOST: {avg_confidence:.6f}→{enhanced_confidence:.4f}")
            else:
                enhanced_confidence = avg_confidence
        
        # Enhancement 2: MAXIMUM aggressive boost for very quiet speech (kids' voices)
        if avg_volume < 0.1:  # HUGE range for quiet audio (kids often speak very softly)
            # Check if there's any speech-like activity
            if self._has_speech_characteristics(audio_data):
                # MAXIMUM AGGRESSIVE boost for quiet kids' voices
                enhanced_confidence = max(enhanced_confidence, 0.9)  # MAXIMUM boost for quiet speech
                logger.info(f"🔊 QUIET SPEECH BOOST: volume={avg_volume:.6f}, confidence={enhanced_confidence:.4f}")
        
        # Enhancement 2b: Special handling for whisper-level audio
        if 0.00001 <= avg_volume < 0.02:  # Expanded whisper range
            if self._has_speech_characteristics(audio_data):
                enhanced_confidence = max(enhanced_confidence, 0.85)  # Very strong boost for whispers
                logger.info(f"🤫 WHISPER DETECTED: volume={avg_volume:.6f}, confidence={enhanced_confidence:.4f}")
        
        # Enhancement 2c: EMERGENCY boost for barely audible sounds
        if 0.000001 <= avg_volume < 0.00001:  # Barely audible
            if np.var(audio_data) > 1e-8:  # Any variation at all
                enhanced_confidence = max(enhanced_confidence, 0.7)  # Emergency boost
                logger.info(f"🆘 EMERGENCY BOOST: volume={avg_volume:.8f}, confidence={enhanced_confidence:.4f}")
                
        # Enhancement 3: ULTRA permissive minimum volume check for kids
        if avg_volume < self.min_volume_threshold:
            enhanced_confidence = 0.0
        
        # Enhancement 4: MAXIMUM temporal smoothing with aggressive carryover for kids
        # Kids often have inconsistent volume and choppy speech, so be EXTREMELY lenient
        if len(self._confidence_history) >= 2:
            recent_max = max(self._confidence_history[-5:])  # Look at last 5 frames
            if recent_max > 0.01 and enhanced_confidence > 0.0001:  # MAXIMUM low thresholds
                enhanced_confidence = max(enhanced_confidence, 0.8)  # MAXIMUM carryover boost
                logger.info(f"⏰ TEMPORAL BOOST: recent_max={recent_max:.5f}, enhanced={enhanced_confidence:.4f}")
        
        # Enhancement 4b: Long-term speech continuity for kids (extended window)
        if len(self._confidence_history) >= 3:
            long_term_max = max(self._confidence_history[-10:])  # Look at last 10 frames
            if long_term_max > 0.001 and enhanced_confidence > 0.0001:
                enhanced_confidence = max(enhanced_confidence, 0.6)  # Strong continuity boost
                logger.info(f"📈 CONTINUITY BOOST: long_term_max={long_term_max:.5f}, enhanced={enhanced_confidence:.4f}")
        
        # Enhancement 4c: ANY recent activity triggers detection
        if len(self._confidence_history) >= 1:
            any_recent_activity = any(c > 0.0001 for c in self._confidence_history[-3:])
            if any_recent_activity and enhanced_confidence > 0.00001:
                enhanced_confidence = max(enhanced_confidence, 0.5)  # Activity boost
                logger.info(f"🎯 ACTIVITY BOOST: enhanced={enhanced_confidence:.4f}")
        
        # Enhancement 5: Special boost for kids' frequency characteristics
        if self._is_kids_voice_pattern(audio_data, avg_volume):
            enhanced_confidence = max(enhanced_confidence, 0.4)
            logger.info(f"👶 KIDS VOICE PATTERN: boosting confidence to {enhanced_confidence:.4f}")
        
        return enhanced_confidence
    
    def _has_speech_characteristics(self, audio_data):
        """
        Check if audio has speech-like characteristics using simple heuristics.
        
        Args:
            audio_data: Audio data as float32 numpy array
            
        Returns:
            True if audio might contain speech
        """
        try:
            # Simple spectral analysis for speech detection
            # Kids' voices have energy in higher frequencies
            
            # Check for non-zero variance (not silence)
            if np.var(audio_data) < 1e-7:  # Even lower threshold for kids
                return False
            
            # Check for reasonable dynamic range (MAXIMUM permissive for kids' whispers)
            audio_range = np.max(audio_data) - np.min(audio_data)
            if audio_range > 0.0001:  # MAXIMUM low threshold for kids' whisper-level voices
                return True
                
            return False
            
        except Exception:
            return False
    
    def _is_kids_voice_pattern(self, audio_data, volume):
        """
        Detect patterns typical of children's voices.
        
        Args:
            audio_data: Audio data as float32 numpy array
            volume: RMS volume of the audio
            
        Returns:
            True if audio has kids' voice characteristics
        """
        try:
            # Kids' voices are often:
            # 1. Higher pitched (more zero crossings)
            # 2. More variable in amplitude
            # 3. Often softer but with sudden peaks
            
            # Count zero crossings (higher for kids' voices)
            zero_crossings = np.sum(np.diff(np.signbit(audio_data)))
            zero_crossing_rate = zero_crossings / len(audio_data)
            
            # Check amplitude variability (kids often have inconsistent volume)
            amplitude_std = np.std(np.abs(audio_data))
            
            # Kids' voice indicators (MAXIMUM sensitive)
            high_pitch_indicator = zero_crossing_rate > 0.01  # MAXIMUM low threshold for higher pitch
            variable_amplitude = amplitude_std > volume * 0.1  # MAXIMUM sensitive to volume variation
            soft_but_present = 0.000001 < volume < 0.2  # MAXIMUM expanded range for kids' whisper-to-normal volume
            
            return high_pitch_indicator and (variable_amplitude or soft_but_present)
            
        except Exception:
            return False
    
    def stream(self):
        """Return the underlying VAD stream for compatibility."""
        return self._base_vad.stream()
    
    def __getattr__(self, name):
        """Delegate any missing attributes to the base VAD."""
        return getattr(self._base_vad, name)


def create_kids_vad(model_path=None):
    """
    Create a highly sensitive Silero VAD instance using the local ONNX model.
    
    This uses your local silero_vad.onnx model with ultra-sensitive parameters
    specifically optimized for detecting soft children's voices.
    
    Args:
        model_path: Optional path to custom model
        
    Returns:
        Kids-optimized VAD wrapper instance using local ONNX model
    """
    try:
        # Use the local ONNX model
        if model_path is None:
            model_path = os.path.join(os.path.dirname(__file__), "models", "silero_vad.onnx")
        
        # Create kids-optimized wrapper with local ONNX model
        kids_vad = KidsOptimizedVADWrapper(model_path)
        
        logger.info("Created ULTRA-sensitive kids VAD using local ONNX model")
        logger.info(f"Model path: {model_path}")
        logger.info("This VAD is configured to detect VERY soft children's voices")
        
        return kids_vad
        
    except Exception as e:
        logger.error(f"Failed to create kids-optimized VAD: {e}")
        raise