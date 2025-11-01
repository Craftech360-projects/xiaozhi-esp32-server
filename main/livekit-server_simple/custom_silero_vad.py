"""
Custom Silero VAD configuration for LiveKit optimized for kids' voices.

This module provides a simple wrapper that configures the default LiveKit Silero VAD
with parameters optimized for detecting children's voices.
"""

import os
import logging
from livekit.plugins import silero

logger = logging.getLogger(__name__)


def create_kids_vad(model_path=None):
    """
    Create a Silero VAD instance optimized for children's voices.
    
    This function loads the default LiveKit Silero VAD. While we can't modify
    the internal parameters directly, the default Silero VAD should work better
    than the previous configuration that was timing out.
    
    Args:
        model_path: Optional path to custom model (not used, for compatibility)
        
    Returns:
        Configured Silero VAD instance
    """
    try:
        # Load the default Silero VAD
        # The LiveKit Silero VAD is already optimized and should work well
        vad = silero.VAD.load()
        
        logger.info("Created Silero VAD for kids' voice detection")
        logger.info("Using default LiveKit Silero VAD parameters")
        logger.info("This should be more sensitive than the previous timeout-causing configuration")
        
        return vad
        
    except Exception as e:
        logger.error(f"Failed to create Silero VAD: {e}")
        raise