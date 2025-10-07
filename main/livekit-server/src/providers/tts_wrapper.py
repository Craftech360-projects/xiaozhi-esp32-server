"""
TTS Wrapper with automatic text sanitization
Wraps any TTS provider and cleans text before synthesis
"""

import logging
from typing import Any
from ..utils.tts_sanitizer import sanitize_for_tts

logger = logging.getLogger(__name__)


def wrap_tts_with_sanitizer(tts_instance: Any, child_friendly: bool = True) -> Any:
    """
    Wrap a TTS instance to automatically sanitize text before synthesis

    Args:
        tts_instance: The TTS provider instance (Groq TTS, ElevenLabs TTS, etc.)
        child_friendly: Whether to apply child-friendly text transformations

    Returns:
        The same TTS instance with wrapped methods
    """
    # Store the original synthesize method
    original_synthesize = tts_instance.synthesize

    # Create a wrapper function that sanitizes text
    def sanitized_synthesize(text: str, **kwargs):
        """Sanitize text before passing to TTS"""
        sanitized_text = sanitize_for_tts(text, child_friendly=child_friendly)

        # Log if significant changes were made
        if len(text) != len(sanitized_text):
            removed_chars = len(text) - len(sanitized_text)
            logger.debug(f"TTS: Sanitized {removed_chars} chars")
            if removed_chars > 50:
                logger.debug(f"Original: {text[:150]}...")
                logger.debug(f"Sanitized: {sanitized_text[:150]}...")

        # Call the original synthesize with cleaned text
        return original_synthesize(sanitized_text, **kwargs)

    # Replace the synthesize method with our wrapper
    tts_instance.synthesize = sanitized_synthesize

    logger.info(f"TTS sanitization wrapper applied to {type(tts_instance).__name__}")

    return tts_instance


class SanitizedTTSWrapper:
    """
    Simple wrapper that delegates to the underlying TTS but sanitizes text first
    """

    def __init__(self, wrapped_tts: Any, child_friendly: bool = True):
        self._tts = wrapped_tts
        self._child_friendly = child_friendly
        self._original_synthesize = wrapped_tts.synthesize
        logger.info(f"Created SanitizedTTSWrapper around {type(wrapped_tts).__name__}")

    def synthesize(self, text: str, **kwargs):
        """Synthesize with sanitized text"""
        sanitized_text = sanitize_for_tts(text, child_friendly=self._child_friendly)

        # Log if significant changes were made
        if len(text) != len(sanitized_text):
            removed_chars = len(text) - len(sanitized_text)
            logger.debug(f"TTS: Sanitized {removed_chars} chars")

        return self._original_synthesize(sanitized_text, **kwargs)

    def __getattr__(self, name):
        """Delegate all other attributes to the wrapped TTS"""
        return getattr(self._tts, name)
