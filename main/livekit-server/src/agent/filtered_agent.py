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

    async def llm_output_filter(self, text: str, preserve_boundaries: bool = True) -> str:
        """
        Filter LLM output before it reaches TTS.

        Args:
            text: The text chunk to filter
            preserve_boundaries: If True, preserve leading/trailing spaces (for streaming)
        """
        if not self._filtering_enabled:
            return text

        try:
            filtered = self.text_filter.filter_for_tts(text, preserve_boundaries=preserve_boundaries)
            # Only log when significant filtering occurred (emojis removed, special chars cleaned)
            if text != filtered and len(text) - len(filtered) > 0:
                logger.debug(f"🔍 Filtered: '{text[:30]}...' -> '{filtered[:30]}...'")
            return filtered
        except Exception as e:
            logger.error(f"🔍 Error filtering LLM output: {e}")
            return text  # Return original if filtering fails

    async def tts_node(self, text: AsyncIterable[str], model_settings) -> AsyncIterable[rtc.AudioFrame]:
        """
        Enhanced TTS node with proper LLM response filtering and buffering.
        Buffers small chunks into complete phrases/sentences for natural pacing.
        """
        logger.info("🔊 TTS node with text buffering and filtering enabled")

        async def buffered_filtered_text_stream():
            """
            Buffer and filter text chunks before TTS.
            Accumulates chunks until we have complete sentences for more natural speech.
            """
            buffer = ""
            chunk_count = 0

            # Punctuation marks that indicate good breaking points
            breaking_punctuation = {'.', '!', '?', ':', '\n'}
            pause_punctuation = {',', ';'}

            async for text_chunk in text:
                if not text_chunk:
                    continue

                chunk_count += 1

                # Apply filtering with boundary preservation
                if self._filtering_enabled:
                    filtered_chunk = await self.llm_output_filter(text_chunk, preserve_boundaries=True)
                else:
                    filtered_chunk = text_chunk

                buffer += filtered_chunk

                # Check if we should flush the buffer
                should_flush = False

                # Flush on sentence-ending punctuation
                if any(punct in buffer for punct in breaking_punctuation):
                    should_flush = True

                # Also flush on commas/semicolons if buffer is getting long
                elif any(punct in buffer for punct in pause_punctuation) and len(buffer) > 50:
                    should_flush = True

                # Flush if buffer is too large (avoid excessive delays)
                elif len(buffer) > 100:
                    should_flush = True

                # Flush the buffer
                if should_flush and buffer.strip():
                    logger.debug(f"🔊 Buffered {chunk_count} chunks into phrase: '{buffer[:50]}...'")
                    yield buffer
                    buffer = ""
                    chunk_count = 0

            # Flush any remaining buffer at the end
            if buffer.strip():
                logger.debug(f"🔊 Final buffer flush ({chunk_count} chunks): '{buffer[:50]}...'")
                yield buffer

        # Use parent's TTS node with buffered and filtered text stream
        async for frame in super().tts_node(buffered_filtered_text_stream(), model_settings):
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
