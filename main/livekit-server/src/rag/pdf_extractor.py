"""
PDF Text Extraction for Educational Content
Extracts clean, structured text from textbook PDFs
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional
import re

logger = logging.getLogger(__name__)

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False
    logger.warning("pdfplumber not available. Install with: pip install pdfplumber")


class PDFExtractor:
    """Extract clean text from educational PDFs"""

    def __init__(self):
        if not PDFPLUMBER_AVAILABLE:
            raise ImportError("pdfplumber is required. Install with: pip install pdfplumber")

        self.min_text_length = 20
        self.image_caption_patterns = [
            r'^[A-Z][a-z\s]+$',  # Simple captions like "A Desert"
            r'^Figure \d+\.?\d*:?\s*',
            r'^Table \d+\.?\d*:?\s*',
            r'^Activity \d+\.?\d*:?\s*'
        ]

    def extract_from_pdf(self, pdf_path: str) -> Dict[str, any]:
        """
        Extract structured text from PDF

        Returns:
            {
                'full_text': str,
                'pages': List[Dict],
                'metadata': Dict
            }
        """
        try:
            pdf_path = Path(pdf_path)
            if not pdf_path.exists():
                raise FileNotFoundError(f"PDF not found: {pdf_path}")

            with pdfplumber.open(pdf_path) as pdf:
                pages_content = []
                full_text = []

                for page_num, page in enumerate(pdf.pages, start=1):
                    page_data = self._extract_page(page, page_num)
                    pages_content.append(page_data)
                    full_text.append(page_data['text'])

                return {
                    'full_text': '\n\n'.join(full_text),
                    'pages': pages_content,
                    'metadata': {
                        'filename': pdf_path.name,
                        'total_pages': len(pdf.pages),
                        'source': str(pdf_path)
                    }
                }

        except Exception as e:
            logger.error(f"Failed to extract from PDF {pdf_path}: {e}")
            raise

    def _extract_page(self, page, page_num: int) -> Dict:
        """Extract text and metadata from a single page"""

        raw_text = page.extract_text()

        if not raw_text:
            return {
                'page_number': page_num,
                'text': '',
                'has_content': False
            }

        cleaned_text = self._clean_text(raw_text)

        return {
            'page_number': page_num,
            'text': cleaned_text,
            'has_content': True,
            'has_heading': self._detect_heading(cleaned_text),
            'has_activity': self._detect_activity(cleaned_text),
            'image_captions': self._extract_image_captions(cleaned_text)
        }

    def _clean_text(self, text: str) -> str:
        """Clean extracted text"""

        # Fix reversed text if detected
        text = self._fix_reversed_text(text)

        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)

        # Remove page numbers at start/end
        text = re.sub(r'^\d+\s*', '', text)
        text = re.sub(r'\s*\d+$', '', text)

        # Remove "Reprint 2025-26" artifacts
        text = re.sub(r'Reprint\s+\d{4}-\d{2}', '', text)

        # Remove chapter footer artifacts
        text = re.sub(r'Chapter\s+\d+\.indd\s+\d+\s+\d+/\d+/\d+\s+\d+:\d+', '', text)

        return text.strip()

    def _detect_reversed_text(self, text: str) -> bool:
        """Detect if text is reversed (common PDF extraction issue)"""
        # Check for reversed common words at the start of text
        reversed_indicators = ['edarG', 'ecneicS', 'koobtxeT', 'ytisoiruC', 'dlroW']
        text_start = text[:200]  # Check first 200 chars
        return any(indicator in text_start for indicator in reversed_indicators)

    def _fix_reversed_text(self, text: str) -> str:
        """Fix reversed text by reversing each word"""
        if not self._detect_reversed_text(text):
            return text

        logger.info("Detected reversed text, fixing...")

        # Split into lines to preserve structure
        lines = text.split('\n')
        fixed_lines = []

        for line in lines:
            # Split line into words
            words = line.split()
            # Reverse each word
            fixed_words = [word[::-1] for word in words]
            # Join back
            fixed_lines.append(' '.join(fixed_words))

        return '\n'.join(fixed_lines)

    def _detect_heading(self, text: str) -> bool:
        """Detect if text contains a heading"""
        heading_patterns = [
            r'^Chapter\s+\d+',
            r'^\d+\.\d+\s+[A-Z]',  # 1.1 Heading
            r'^[A-Z][a-z]+\s+[A-Z][a-z]+\s+[A-Z][a-z]+',  # Title Case
        ]

        first_line = text.split('\n')[0] if '\n' in text else text[:100]
        return any(re.search(pattern, first_line) for pattern in heading_patterns)

    def _detect_activity(self, text: str) -> bool:
        """Detect if text contains an activity"""
        return bool(re.search(r'Activity\s+\d+\.?\d*:', text, re.IGNORECASE))

    def _extract_image_captions(self, text: str) -> List[str]:
        """Extract simple image captions (not verbose descriptions)"""
        captions = []

        # Look for simple patterns like "A Desert", "A mountainous region"
        simple_caption_pattern = r'A\s+[A-Z][a-z]+(?:\s+[a-z]+){0,3}'
        matches = re.findall(simple_caption_pattern, text)

        # Filter to keep only genuine captions (short, descriptive)
        for match in matches:
            if len(match.split()) <= 5:  # Max 5 words
                captions.append(match)

        return captions

    def extract_chapter_info(self, pdf_path: str) -> Dict:
        """Extract chapter number and title from PDF"""

        try:
            with pdfplumber.open(pdf_path) as pdf:
                first_page = pdf.pages[0]
                text = first_page.extract_text()

                # Try to find chapter number and title
                chapter_match = re.search(
                    r'Chapter\s+(\d+)\s*\n\s*(.+?)(?:\n|$)',
                    text,
                    re.MULTILINE
                )

                if chapter_match:
                    return {
                        'chapter_number': int(chapter_match.group(1)),
                        'chapter_title': chapter_match.group(2).strip()
                    }

                # Fallback: extract from filename
                filename = Path(pdf_path).stem
                filename_match = re.match(r'[Cc]hapter\s*(\d+)\s*(.+)', filename)
                if filename_match:
                    return {
                        'chapter_number': int(filename_match.group(1)),
                        'chapter_title': filename_match.group(2).strip()
                    }

                return {
                    'chapter_number': None,
                    'chapter_title': filename
                }

        except Exception as e:
            logger.error(f"Failed to extract chapter info: {e}")
            return {
                'chapter_number': None,
                'chapter_title': Path(pdf_path).stem
            }
