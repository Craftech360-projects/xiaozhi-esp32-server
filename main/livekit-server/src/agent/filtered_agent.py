import logging
from typing import AsyncIterable
from livekit.agents import Agent
from livekit import rtc
from ..utils.text_filter import text_filter

logger = logging.getLogger("filtered_agent")


class FilteredAgent(Agent):
    """
    Custom Agent that implements LLM response filtering.

    This agent intercepts LLM responses and filters them before TTS synthesis.
    """

    def __init__(self, *, instructions: str = "", tts_provider=None, **kwargs):
        """Initialize the FilteredAgent with text filtering capabilities."""
        super().__init__(instructions=instructions, **kwargs)
        self.text_filter = text_filter
        self._filtering_enabled = True  # Enable filtering at LLM output level
        self._tts_provider = tts_provider
        logger.info("FilteredAgent initialized with LLM response filtering (ENABLED)")

    async def llm_output_filter(self, text: str) -> str:
        """Filter LLM output before it reaches TTS"""
        if not self._filtering_enabled:
            return text

        try:
            filtered = self.text_filter.filter_for_tts(text)
            if text != filtered:
                logger.info(f"🔍 LLM Filter applied: '{text[:50]}...' -> '{filtered[:50]}...'")
            else:
                logger.info(f"🔍 No filtering needed for: '{text[:50]}...'")
            return filtered
        except Exception as e:
            logger.error(f"🔍 Error filtering LLM output: {e}")
            return text  # Return original if filtering fails

    async def tts_node(self, text: AsyncIterable[str], model_settings) -> AsyncIterable[rtc.AudioFrame]:
        """
        Enhanced TTS node with proper LLM response filtering.
        Applies filtering to text stream before passing to session TTS.
        """
        logger.info("🔊 TTS node with LLM response filtering enabled")

        async def filtered_text_stream():
            """Filter the text stream from LLM before TTS"""
            async for text_chunk in text:
                if text_chunk and self._filtering_enabled:
                    # Apply filtering to each text chunk
                    filtered_chunk = await self.llm_output_filter(text_chunk)
                    yield filtered_chunk
                else:
                    yield text_chunk

        # Use parent's TTS node with filtered text stream
        async for frame in super().tts_node(filtered_text_stream(), model_settings):
            yield frame

    def enable_filtering(self, enabled: bool = True):
        """Enable or disable text filtering."""
        self._filtering_enabled = enabled
        if enabled:
            logger.info("TTS text filtering enabled")
        else:
            logger.info("TTS text filtering disabled")

    def is_filtering_enabled(self) -> bool:
        """Check if text filtering is currently enabled."""
        return getattr(self, '_filtering_enabled', True)