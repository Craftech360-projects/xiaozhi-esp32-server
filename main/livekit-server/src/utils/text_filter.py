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

        # Pattern for common TTS-unfriendly characters (preserve math symbols and common symbols)
        # Include math symbols: × (U+00D7), ÷ (U+00F7), √ (U+221A), ² (U+00B2), ³ (U+00B3), ± (U+00B1)
        # Note: Unicode quotes/dashes are normalized to ASCII in filter_for_tts() before this pattern is applied
        # IMPORTANT: Hyphen must be escaped or at end to avoid being interpreted as range
        self.special_chars_pattern = re.compile(r'[^\w\s.,!?;:()\'"+=<>%$^&@°:×÷√²³±*/\-]', re.UNICODE)

        # Keep these punctuation marks for natural speech rhythm and math
        self.speech_punctuation = {'.', ',', '!', '?', ';', ':', '(', ')', '-', "'", '+', '*', '/', '=', '<', '>', '%', '$', '^', '&', '@', '°', '×', '÷', '√', '²', '³', '±'}

    def _contains_markdown_table(self, text: str) -> bool:
        """
        Detect if text contains markdown table formatting

        Args:
            text: Input text to check

        Returns:
            bool: True if markdown table detected
        """
        # Check for table indicators:
        # 1. Multiple pipe characters (|) on same line
        # 2. Separator rows (---|---|---)
        # 3. Multiple lines with pipes
        lines = text.split('\n')

        pipe_lines = 0
        has_separator = False

        for line in lines:
            pipe_count = line.count('|')

            # Line with multiple pipes (table row)
            if pipe_count >= 2:
                pipe_lines += 1

            # Separator row: |---|---|---| or | --- | --- |
            if re.search(r'\|[\s\-]+\|[\s\-]+\|', line):
                has_separator = True

        # Table detected if: multiple pipe lines OR separator row exists
        return pipe_lines >= 2 or has_separator

    def _strip_table_formatting(self, text: str) -> str:
        """
        Remove markdown table formatting and convert to narrative text

        Args:
            text: Text containing markdown table

        Returns:
            str: Text with table formatting removed, better for voice
        """
        lines = text.split('\n')
        cleaned_lines = []

        for line in lines:
            # Skip separator rows (---|---|---)
            if re.match(r'^\s*\|?[\s\-|]+\|?\s*$', line):
                continue

            # If line has pipes, it's a table row
            if '|' in line:
                # Remove pipes and clean up
                cells = [cell.strip() for cell in line.split('|') if cell.strip()]

                # Skip empty rows
                if not cells:
                    continue

                # Join cells with "and" or commas for natural speech
                if len(cells) == 1:
                    cleaned_lines.append(cells[0])
                elif len(cells) == 2:
                    cleaned_lines.append(f"{cells[0]} and {cells[1]}")
                else:
                    # For multiplication tables, format nicely
                    # Check if it's numbers (multiplication table row)
                    # Allow digits, multiply symbols (×, *, x), and common math symbols (=, -, +)
                    def is_table_cell(cell):
                        cleaned = cell.replace(' ', '').replace('-', '').replace('×', '').replace('*', '').replace('=', '').replace('+', '')
                        return cleaned.isdigit() or cell.strip() in ['×', 'x', '*', '=', '+', '-']

                    if all(is_table_cell(cell) for cell in cells if cell):
                        # Join with "then" for sequential numbers
                        cleaned_lines.append(", then ".join(cells))
                    else:
                        cleaned_lines.append(", ".join(cells))
            else:
                # Regular line, keep as is
                if line.strip():
                    cleaned_lines.append(line.strip())

        return '. '.join(cleaned_lines)

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
            # Step 0: Detect and handle markdown tables (BEFORE normalization)
            # Tables are terrible for TTS - convert to narrative or warn
            if self._contains_markdown_table(text):
                logger.warning("🚫 Markdown table detected in TTS output - tables are not suitable for voice!")
                text = self._strip_table_formatting(text)

            # Step 1: Normalize Unicode typography characters to ASCII equivalents
            # This must happen BEFORE other filtering to prevent word merging
            unicode_replacements = {
                # Curly quotes to straight quotes
                '\u2018': "'",  # ' (left single quotation mark)
                '\u2019': "'",  # ' (right single quotation mark)
                '\u201A': "'",  # ‚ (single low-9 quotation mark)
                '\u201B': "'",  # ‛ (single high-reversed-9 quotation mark)
                '\u201C': '"',  # " (left double quotation mark)
                '\u201D': '"',  # " (right double quotation mark)
                '\u201E': '"',  # „ (double low-9 quotation mark)
                '\u201F': '"',  # ‟ (double high-reversed-9 quotation mark)
                # Dashes to regular hyphen
                '\u2010': '-',  # ‐ (hyphen)
                '\u2011': '-',  # ‑ (non-breaking hyphen)
                '\u2012': '-',  # ‒ (figure dash)
                '\u2013': '-',  # – (en dash)
                '\u2014': '-',  # — (em dash)
                '\u2015': '-',  # ― (horizontal bar)
                # Spaces
                '\u00A0': ' ',  # non-breaking space
                '\u2007': ' ',  # figure space
                '\u202F': ' ',  # narrow no-break space
            }

            for unicode_char, ascii_char in unicode_replacements.items():
                text = text.replace(unicode_char, ascii_char)

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

            # Step 1.5: Convert math operators to speech-friendly words for TTS
            # This ensures TTS pronounces "5-2" as "5 minus 2" instead of "5 2"
            if has_math_context:
                # Convert operators to words, but only when surrounded by numbers
                # This preserves hyphenated words like "twenty-five"
                text = regex_mod.sub(r'(\d+)\s*-\s*(\d+)', r'\1 minus \2', text)
                text = regex_mod.sub(r'(\d+)\s*\+\s*(\d+)', r'\1 plus \2', text)
                text = regex_mod.sub(r'(\d+)\s*\*\s*(\d+)', r'\1 times \2', text)
                text = regex_mod.sub(r'(\d+)\s*×\s*(\d+)', r'\1 times \2', text)
                text = regex_mod.sub(r'(\d+)\s*/\s*(\d+)', r'\1 divided by \2', text)
                text = regex_mod.sub(r'(\d+)\s*÷\s*(\d+)', r'\1 divided by \2', text)
                logger.debug(f"🧮 Converted math operators to words for TTS: '{text[:50]}...')")

            # Step 2: Remove emojis
            text = self.emoji_pattern.sub(' ', text)

            # Step 3: Handle markdown formatting (be smart about * and - in math context)
            # IMPORTANT: Replace with space to prevent word merging!
            if has_math_context:
                # Only remove non-math markdown characters, preserve & and @ and - (minus sign)
                # CRITICAL: Preserve minus sign (-) for math expressions like "5-2"
                text = re.sub(r'[_`~\[\]{}#|\\]', ' ', text)
            else:
                # Remove all markdown including * but preserve & and @ for natural expressions
                # Also preserve - in non-math context as it could be hyphenated words
                text = re.sub(r'[*_`~\[\]{}#|\\]', ' ', text)

            # Step 4: Handle excessive punctuation (keep rhythm but reduce noise)
            text = self.excessive_punct_pattern.sub(r'\1\1\1', text)  # Max 3 consecutive

            # Step 5: Remove problematic special characters but keep speech punctuation and math
            # IMPORTANT: Replace with space to prevent word merging!
            text = self.special_chars_pattern.sub(' ', text)

            # Step 6: Clean up whitespace (collapse multiple spaces/newlines to single space)
            text = self.whitespace_pattern.sub(' ', text)

            # Step 7: Remove leading/trailing whitespace (only for complete text, not streaming chunks)
            if not preserve_boundaries:
                text = text.strip()

                # Step 8: Ensure sentence ending if text is substantial (only for complete text)
                if len(text) > 10 and not text.endswith(('.', '!', '?')):
                    text += '.'

            # Log filtering if significant changes were made
            if len(original_text) - len(text) > 5:
                logger.debug(f"TTS Filter: '{original_text[:50]}...' -> '{text[:50]}...'")

            return text

        except Exception as e:
            logger.error(f"Error filtering text for TTS: {e}")
            # Return a basic cleaned version as fallback
            # First normalize Unicode to ASCII
            unicode_replacements = {
                '\u2018': "'", '\u2019': "'", '\u201A': "'", '\u201B': "'",
                '\u201C': '"', '\u201D': '"', '\u201E': '"', '\u201F': '"',
                '\u2010': '-', '\u2011': '-', '\u2012': '-', '\u2013': '-', '\u2014': '-', '\u2015': '-',
                '\u00A0': ' ', '\u2007': ' ', '\u202F': ' ',
            }
            cleaned = original_text
            for unicode_char, ascii_char in unicode_replacements.items():
                cleaned = cleaned.replace(unicode_char, ascii_char)

            # IMPORTANT: Replace removed chars with space to prevent word merging
            # IMPORTANT: Hyphen must be escaped (\-) to avoid range interpretation
            cleaned = re.sub(r'[^\w\s.,!?;:()\'"+=<>%$×÷√²³±*/\-]', ' ', cleaned)
            cleaned = re.sub(r'\s+', ' ', cleaned)  # Collapse multiple spaces
            if preserve_boundaries:
                return cleaned
            else:
                return cleaned.strip()

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
