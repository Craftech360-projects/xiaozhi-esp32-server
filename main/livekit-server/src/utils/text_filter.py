import re
import unicodedata
import logging

logger = logging.getLogger("text_filter")

class TextFilter:
    """
    Text filtering utility to clean text before TTS synthesis.
    Removes emojis, special characters, and formatting while preserving
    essential punctuation for natural speech.
    """

    def __init__(self):
        # Compiled regex patterns for better performance
        self.emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags (iOS)
            "\U00002702-\U000027B0"  # dingbats
            "\U000024C2-\U0001F251"  # enclosed characters
            "\U0001F900-\U0001F9FF"  # supplemental symbols
            "\U0001FA70-\U0001FAFF"  # symbols and pictographs extended-a
            "]+",
            flags=re.UNICODE
        )

        # Pattern for special markdown/formatting characters (excluding & and @ for natural expressions)
        self.markdown_pattern = re.compile(r'[*_`~\[\]{}#|\\]')

        # Pattern for excessive punctuation (more than 3 consecutive)
        self.excessive_punct_pattern = re.compile(r'([.!?]){4,}')

        # Pattern for excessive spaces/newlines
        self.whitespace_pattern = re.compile(r'\s+')

        # Pattern for common TTS-unfriendly characters (preserve math symbols, common symbols, and Indic scripts)
        # Include math symbols: × (U+00D7), ÷ (U+00F7), √ (U+221A), ² (U+00B2), ³ (U+00B3), ± (U+00B1)
        # Preserve Unicode word characters (includes Devanagari, Arabic, Chinese, etc.) using \w with UNICODE flag
        # Only remove actual problematic characters like control chars, weird symbols, etc.
        self.special_chars_pattern = re.compile(r'[^\w\s.,!?;:()\'+\-*/=<>%$^&@°:×÷√²³±।॥]', re.UNICODE)

        # Keep these punctuation marks for natural speech rhythm and math
        self.speech_punctuation = {'.', ',', '!', '?', ';', ':', '(', ')', '-', "'", '+', '*', '/', '=', '<', '>', '%', '$', '^', '&', '@', '°', '×', '÷', '√', '²', '³', '±'}

    def filter_for_tts(self, text: str, preserve_boundaries: bool = False) -> str:
        """
        Main filtering method that cleans text for TTS synthesis.

        Args:
            text (str): Input text from LLM
            preserve_boundaries (bool): If True, preserve leading/trailing whitespace for streaming chunks

        Returns:
            str: Cleaned text suitable for TTS
        """
        if not text or not isinstance(text, str):
            return ""

        original_text = text

        try:
            # Check if text contains mathematical expressions (more precise)
            # Look for actual math patterns, not just isolated symbols
            import re as regex_mod
            math_patterns = [
                r'\d+\s*[\+\-\*/=^×÷]\s*\d+',     # Numbers with operators: 2+2, 10*5, 12×1, 2÷2
                r'\w+\s*[\+\-\*/=^×÷]\s*\w+',     # Variables with operators: x+y, a=b, x×y
                r'\d+\s*[\+\-\*/=^×÷]\s*\w+',     # Mixed: 2+x, 3×y
                r'\w+\s*[\+\-\*/=^×÷]\s*\d+',     # Mixed: x+2, y×3
                r'calculate|computation|solve|equation|formula|result\s*=|answer\s*=|math|mathematics|times?\s+table',  # Math keywords
                r'\([^)]*[\+\-\*/=^×÷][^)]*\)',   # Math in parentheses: (x+y), (a+b)
                r'\w+\s*=\s*\w+[\+\-\*/^×÷]\w+',  # Equations: E=mc^2, a=b+c
                r'[\w\d]+\^[\w\d]+',            # Exponents: 2^3, x^2, E^2
                r'\(\s*[\w\d]+\s*,\s*[\w\d]+\s*\)',  # Coordinates: (x,y), (10,20)
                r'[\w\d]+\s*[\+\-\*/=×÷]\s*[\w\d]+\s*[\+\-\*/=×÷]\s*[\w\d]+',  # Complex: 1+2+3, a×b÷c
            ]
            has_math_context = any(regex_mod.search(pattern, text.lower()) for pattern in math_patterns)

            # Step 1: Remove emojis
            text = self.emoji_pattern.sub(' ', text)

            # Step 2: Handle markdown formatting (be smart about * in math context)
            if has_math_context:
                # Only remove non-math markdown characters, preserve & and @
                text = re.sub(r'[_`~\[\]{}#|\\]', '', text)
            else:
                # Remove all markdown including * but preserve & and @ for natural expressions
                text = re.sub(r'[*_`~\[\]{}#|\\]', '', text)

            # Step 3: Handle excessive punctuation (keep rhythm but reduce noise)
            text = self.excessive_punct_pattern.sub(r'\1\1\1', text)  # Max 3 consecutive

            # Step 4: Remove problematic special characters but keep speech punctuation and math
            text = self.special_chars_pattern.sub('', text)

            # Step 5: Clean up whitespace (collapse multiple spaces/newlines to single space)
            text = self.whitespace_pattern.sub(' ', text)

            # Step 6: Remove leading/trailing whitespace (only for complete text, not streaming chunks)
            if not preserve_boundaries:
                text = text.strip()

                # Step 7: Ensure sentence ending if text is substantial (only for complete text)
                if len(text) > 10 and not text.endswith(('.', '!', '?')):
                    text += '.'

            # Log filtering if significant changes were made
            if len(original_text) - len(text) > 5:
                logger.debug(f"TTS Filter: '{original_text[:50]}...' -> '{text[:50]}...'")

            return text

        except Exception as e:
            logger.error(f"Error filtering text for TTS: {e}")
            # Return a basic cleaned version as fallback
            if preserve_boundaries:
                return re.sub(r'[^\w\s.,!?;:()\'+\-*/=<>%$×÷√²³±।॥]', '', original_text, flags=re.UNICODE)
            else:
                return re.sub(r'[^\w\s.,!?;:()\'+\-*/=<>%$×÷√²³±।॥]', '', original_text, flags=re.UNICODE).strip()

    def remove_unicode_categories(self, text: str, categories_to_remove: list = None) -> str:
        """
        Remove characters from specific Unicode categories.

        Args:
            text (str): Input text
            categories_to_remove (list): Unicode categories to remove (e.g., ['So', 'Sm'])
                                       So = Other Symbols, Sm = Math Symbols

        Returns:
            str: Text with specified Unicode categories removed
        """
        if categories_to_remove is None:
            categories_to_remove = ['So', 'Sm', 'Sk']  # Symbols, Math, Modifier symbols

        filtered_chars = []
        for char in text:
            category = unicodedata.category(char)
            if category not in categories_to_remove:
                filtered_chars.append(char)

        return ''.join(filtered_chars)

    def normalize_for_speech(self, text: str) -> str:
        """
        Additional normalization for natural speech synthesis.
        Intelligently converts symbols to speech-friendly forms while preserving math context.

        Args:
            text (str): Input text

        Returns:
            str: Normalized text for speech
        """
        # Only convert symbols when they're clearly not part of math expressions

        # Check if text seems to contain mathematical expressions (using same logic as main filter)
        import re as regex_mod
        math_patterns = [
            r'\d+\s*[\+\-\*/=^×÷]\s*\d+',
            r'\w+\s*[\+\-\*/=^×÷]\s*\w+',
            r'calculate|computation|solve|equation|formula|result\s*=|answer\s*=|math|mathematics|times?\s+table',
            r'\([^)]*[\+\-\*/=^×÷][^)]*\)',
            r'[\w\d]+\^[\w\d]+',
        ]
        has_math_context = any(regex_mod.search(pattern, text.lower()) for pattern in math_patterns)

        # Check for email patterns to preserve @
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        has_email = regex_mod.search(email_pattern, text)

        if not has_math_context:
            # Safe to convert symbols to speech forms, but preserve @ in emails
            replacements = {
                ' & ': ' and ',
                ' + ': ' plus ',
                ' = ': ' equals ',
                ' % ': ' percent ',
                ' $ ': ' dollars ',
                ' # ': ' number ',
            }

            # Only convert @ if not in email context
            if not has_email:
                replacements[' @ '] = ' at '

            for old, new in replacements.items():
                text = text.replace(old, new)
        else:
            # Preserve math symbols but convert non-math ones, still preserve @ in emails
            replacements = {
                ' & ': ' and ',
                ' # ': ' number ',
            }

            # Only convert @ if not in email context
            if not has_email:
                replacements[' @ '] = ' at '

            for old, new in replacements.items():
                text = text.replace(old, new)

        return text

    def is_safe_for_tts(self, text: str) -> bool:
        """
        Check if text is safe and suitable for TTS without filtering.

        Args:
            text (str): Input text

        Returns:
            bool: True if text is already TTS-safe
        """
        if not text:
            return True

        # Check for emojis
        if self.emoji_pattern.search(text):
            return False

        # Check for excessive special characters
        special_char_count = len(self.special_chars_pattern.findall(text))
        total_chars = len(text)

        # If more than 10% special characters, consider it unsafe
        if total_chars > 0 and (special_char_count / total_chars) > 0.1:
            return False

        return True


# Global instance for easy access
text_filter = TextFilter()
