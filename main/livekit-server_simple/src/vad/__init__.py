"""Custom VAD module for LiveKit integration.

This module provides a production-ready Voice Activity Detection implementation
using the Silero VAD ONNX model, adapted from xiaozhi-server.
"""

from .vad_analyzer import VADAnalyzer, VADParams, VADState, calculate_audio_volume, exp_smoothing
from .silero_onnx import SileroOnnxModel, SileroVADAnalyzer
from .livekit_adapter import LiveKitVAD, VADStream

__all__ = [
    "VADAnalyzer",
    "VADParams",
    "VADState",
    "SileroOnnxModel",
    "SileroVADAnalyzer",
    "LiveKitVAD",
    "VADStream",
    "calculate_audio_volume",
    "exp_smoothing",
]
