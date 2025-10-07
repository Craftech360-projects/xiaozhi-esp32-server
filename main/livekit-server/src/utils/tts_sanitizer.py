"""
TTS Text Sanitizer
Cleans LLM-generated text to be more suitable for Text-to-Speech synthesis
"""

import re
import logging

logger = logging.getLogger(__name__)


class TTSSanitizer:
    """Sanitize text for better TTS output"""

    @staticmethod
    def sanitize(text: str) -> str:
        """
        Clean text for TTS by removing markdown formatting and improving readability

        Args:
            text: Raw text from LLM (may contain markdown)

        Returns:
            Cleaned text suitable for TTS
        """
        if not text:
            return text

        original_text = text

        # Remove bold markdown (**text** or __text__)
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
        text = re.sub(r'__(.+?)__', r'\1', text)

        # Remove italic markdown (*text* or _text_)
        text = re.sub(r'\*(.+?)\*', r'\1', text)
        text = re.sub(r'(?<!\w)_(.+?)_(?!\w)', r'\1', text)

        # Remove inline code (`code`)
        text = re.sub(r'`(.+?)`', r'\1', text)

        # Convert numbered lists (1. 2. 3.) to natural speech
        text = re.sub(r'^(\d+)\.\s+', r'\1. ', text, flags=re.MULTILINE)

        # Convert bullet points to natural pauses
        text = re.sub(r'^[-*]\s+', '', text, flags=re.MULTILINE)

        # Remove heading markers (##, ###)
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)

        # Clean up URLs (make them more pronounceable or remove)
        text = re.sub(r'https?://[^\s]+', '', text)

        # Convert parenthetical abbreviations to be more natural
        # e.g., "meters (m)" -> "meters"
        text = re.sub(r'\s*\(([a-zA-Z]{1,3})\)', '', text)

        # Clean up multiple spaces
        text = re.sub(r'\s+', ' ', text)

        # Clean up multiple newlines (keep max 2 for paragraph breaks)
        text = re.sub(r'\n{3,}', '\n\n', text)

        # Remove leading/trailing whitespace from each line
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)

        # Final cleanup
        text = text.strip()

        # Log if significant changes were made
        if len(original_text) - len(text) > 20:
            logger.debug(f"TTS sanitization removed {len(original_text) - len(text)} characters")

        return text

    @staticmethod
    def sanitize_for_child(text: str) -> str:
        """
        Additional sanitization for child-friendly TTS
        Makes text more conversational and age-appropriate

        Args:
            text: Pre-sanitized text

        Returns:
            Child-friendly text
        """
        text = TTSSanitizer.sanitize(text)

        # Replace formal "Source:" citations with friendlier versions
        text = re.sub(
            r'Source:\s*(.+?)(?:\n|$)',
            r"I found this in \1.",
            text,
            flags=re.IGNORECASE
        )

        # Make "For example:" more conversational
        text = re.sub(r'For example:', 'For example,', text)

        # Convert formal bullet introductions
        text = re.sub(r'(?:you learn about|topics include):\s*\n', r' ', text, flags=re.IGNORECASE)

        return text


def sanitize_for_tts(text: str, child_friendly: bool = True) -> str:
    """
    Convenience function to sanitize text for TTS

    Args:
        text: Raw text from LLM
        child_friendly: Whether to apply child-friendly transformations

    Returns:
        Sanitized text ready for TTS
    """
    if child_friendly:
        return TTSSanitizer.sanitize_for_child(text)
    return TTSSanitizer.sanitize(text)


# Test function for development
if __name__ == "__main__":
    test_text = """
**Standard Units** are agreed-upon units of measurement that everyone uses.

In **Chapter 5** of your Grade 6 Science textbook, you learn about:

1. **Length** - measured in meters (m), centimeters (cm), millimeters (mm)
2. **Mass** - measured in kilograms (kg), grams (g)
3. **Time** - measured in seconds (s), minutes (min), hours (h)

For example:
- Instead of saying "my hand is as long as a pencil", we say "my hand is 15 cm long"
- This way, everyone knows exactly how long it is!

**Source:** Grade 6 Science, Chapter 5, page 45
    """

    print("Original:")
    print(test_text)
    print("\n" + "="*80 + "\n")
    print("Sanitized:")
    print(sanitize_for_tts(test_text))
