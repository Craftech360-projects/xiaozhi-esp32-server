"""
Figure and Table Extractor
Extracts visual elements (figures, tables, diagrams) from PDFs with context
"""

import logging
import io
from typing import Dict, List, Tuple, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    import pdfplumber
    from PIL import Image
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False
    logger.warning("pdfplumber or PIL not available. Install with: pip install pdfplumber Pillow")


class FigureExtractor:
    """Extract figures, tables, and diagrams from educational PDFs"""

    def __init__(self):
        if not PDFPLUMBER_AVAILABLE:
            raise ImportError("pdfplumber and PIL are required. Install with: pip install pdfplumber Pillow")

        self.min_figure_size = (100, 100)  # Minimum width, height in pixels
        self.max_figures_per_page = 10  # Limit figures per page

    def extract_figures(self, pdf_path: str) -> List[Dict]:
        """
        Extract all figures with context from PDF

        Returns:
            [
                {
                    'figure_id': 'fig_1_2',
                    'page': 2,
                    'caption': 'Diagram of scientific method',
                    'image_data': bytes,
                    'bounding_box': (x0, y0, x1, y1),
                    'nearby_text': 'Context from surrounding text...',
                    'image_size': (width, height)
                }
            ]
        """

        if not PDFPLUMBER_AVAILABLE:
            logger.error("Cannot extract figures: pdfplumber not available")
            return []

        figures = []

        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, start=1):
                    page_figures = self._extract_figures_from_page(page, page_num)
                    figures.extend(page_figures)

            logger.info(f"Extracted {len(figures)} figures from {pdf_path}")
            return figures

        except Exception as e:
            logger.error(f"Failed to extract figures from {pdf_path}: {e}")
            return []

    def extract_tables(self, pdf_path: str) -> List[Dict]:
        """
        Extract tables with structured data from PDF

        Returns:
            [
                {
                    'table_id': 'table_1_1',
                    'page': 3,
                    'caption': 'Properties of materials',
                    'data': [[row1], [row2], ...],
                    'headers': ['Material', 'Property', 'Use'],
                    'nearby_text': 'Context from surrounding text...'
                }
            ]
        """

        if not PDFPLUMBER_AVAILABLE:
            logger.error("Cannot extract tables: pdfplumber not available")
            return []

        tables = []

        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, start=1):
                    page_tables = self._extract_tables_from_page(page, page_num)
                    tables.extend(page_tables)

            logger.info(f"Extracted {len(tables)} tables from {pdf_path}")
            return tables

        except Exception as e:
            logger.error(f"Failed to extract tables from {pdf_path}: {e}")
            return []

    def _extract_figures_from_page(self, page, page_num: int) -> List[Dict]:
        """Extract figures from a single page"""

        figures = []

        try:
            # Get images from page
            images = page.images

            if not images:
                return []

            # Get full page text for context
            page_text = page.extract_text() or ""

            # Process each image
            for img_index, img in enumerate(images[:self.max_figures_per_page]):
                try:
                    # Get image properties
                    bbox = (img['x0'], img['top'], img['x1'], img['bottom'])
                    width = img['width']
                    height = img['height']

                    # Skip very small images (likely logos, icons, etc.)
                    if width < self.min_figure_size[0] or height < self.min_figure_size[1]:
                        continue

                    # Try to extract image data
                    try:
                        # pdfplumber doesn't directly provide image bytes,
                        # but we can reference the image location
                        image_data = None  # Placeholder - actual extraction would require PyMuPDF

                        # Detect caption
                        caption = self._detect_caption_near_image(page_text, bbox, page_num, img_index)

                        # Get surrounding text context
                        nearby_text = self._extract_nearby_text(page_text, bbox)

                        # Generate figure ID
                        figure_id = self._generate_figure_id(caption, page_num, img_index)

                        figures.append({
                            'figure_id': figure_id,
                            'page': page_num,
                            'caption': caption,
                            'image_data': image_data,  # None for now - would need PyMuPDF
                            'bounding_box': bbox,
                            'nearby_text': nearby_text,
                            'image_size': (width, height)
                        })

                    except Exception as e:
                        logger.warning(f"Failed to extract image {img_index} from page {page_num}: {e}")
                        continue

                except Exception as e:
                    logger.warning(f"Failed to process image {img_index} on page {page_num}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Failed to extract figures from page {page_num}: {e}")

        return figures

    def _extract_tables_from_page(self, page, page_num: int) -> List[Dict]:
        """Extract tables from a single page"""

        tables = []

        try:
            # Get tables from page
            page_tables = page.extract_tables()

            if not page_tables:
                return []

            # Get full page text for context
            page_text = page.extract_text() or ""

            # Process each table
            for table_index, table_data in enumerate(page_tables):
                try:
                    if not table_data or len(table_data) < 2:  # Need at least header + 1 row
                        continue

                    # Extract headers (first row)
                    headers = table_data[0]

                    # Extract data rows
                    data_rows = table_data[1:]

                    # Detect caption
                    caption = self._detect_table_caption(page_text, table_data, page_num, table_index)

                    # Get surrounding text context
                    nearby_text = self._extract_table_context(page_text, table_data)

                    # Generate table ID
                    table_id = self._generate_table_id(caption, page_num, table_index)

                    tables.append({
                        'table_id': table_id,
                        'page': page_num,
                        'caption': caption,
                        'data': data_rows,
                        'headers': headers,
                        'nearby_text': nearby_text,
                        'row_count': len(data_rows),
                        'column_count': len(headers) if headers else 0
                    })

                except Exception as e:
                    logger.warning(f"Failed to extract table {table_index} from page {page_num}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Failed to extract tables from page {page_num}: {e}")

        return tables

    def _detect_caption_near_image(
        self,
        page_text: str,
        bbox: Tuple[float, float, float, float],
        page_num: int,
        img_index: int
    ) -> str:
        """Detect caption text near an image"""

        import re

        # Look for figure captions in text
        caption_patterns = [
            r'[Ff]ig(?:ure|\.)?\s*(\d+[\.\d]*)[:\s]+(.+?)(?:\n|$)',
            r'[Ii]mage\s*(\d+[\.\d]*)[:\s]+(.+?)(?:\n|$)',
            r'[Dd]iagram\s*(\d+[\.\d]*)[:\s]+(.+?)(?:\n|$)',
        ]

        for pattern in caption_patterns:
            matches = re.findall(pattern, page_text)
            if matches and img_index < len(matches):
                fig_num, caption_text = matches[img_index]
                return caption_text.strip()

        # Fallback: generic caption
        return f"Figure {page_num}.{img_index + 1}"

    def _detect_table_caption(
        self,
        page_text: str,
        table_data: List[List],
        page_num: int,
        table_index: int
    ) -> str:
        """Detect caption text near a table"""

        import re

        # Look for table captions in text
        caption_patterns = [
            r'[Tt]able\s*(\d+[\.\d]*)[:\s]+(.+?)(?:\n|$)',
            r'[Tt]ab\.\s*(\d+[\.\d]*)[:\s]+(.+?)(?:\n|$)',
        ]

        for pattern in caption_patterns:
            matches = re.findall(pattern, page_text)
            if matches and table_index < len(matches):
                table_num, caption_text = matches[table_index]
                return caption_text.strip()

        # Try to use first row as caption if it's descriptive
        if table_data and table_data[0]:
            first_row_text = ' '.join(str(cell) for cell in table_data[0] if cell)
            if len(first_row_text) > 20 and len(first_row_text) < 100:
                return first_row_text

        # Fallback: generic caption
        return f"Table {page_num}.{table_index + 1}"

    def _extract_nearby_text(
        self,
        page_text: str,
        bbox: Tuple[float, float, float, float],
        context_window: int = 200
    ) -> str:
        """Extract text near an image for context"""

        # Simple approach: extract text before and after figure caption
        # More sophisticated approach would use bbox coordinates

        # For now, return a snippet of page text
        if len(page_text) > context_window * 2:
            return page_text[:context_window] + "..."
        return page_text

    def _extract_table_context(
        self,
        page_text: str,
        table_data: List[List],
        context_window: int = 150
    ) -> str:
        """Extract text context around a table"""

        # Simple approach: extract surrounding text
        # More sophisticated approach would identify table location in text

        # For now, return a snippet
        if len(page_text) > context_window * 2:
            return page_text[:context_window] + "..."
        return page_text

    def _generate_figure_id(self, caption: str, page_num: int, index: int) -> str:
        """Generate unique figure ID"""

        import re

        # Try to extract figure number from caption
        match = re.search(r'[Ff]ig(?:ure|\.)?\s*(\d+[\.\d]*)', caption)
        if match:
            fig_num = match.group(1).replace('.', '_')
            return f"fig_{fig_num}"

        # Fallback to page-based ID
        return f"fig_{page_num}_{index + 1}"

    def _generate_table_id(self, caption: str, page_num: int, index: int) -> str:
        """Generate unique table ID"""

        import re

        # Try to extract table number from caption
        match = re.search(r'[Tt]able\s*(\d+[\.\d]*)', caption)
        if match:
            table_num = match.group(1).replace('.', '_')
            return f"table_{table_num}"

        # Fallback to page-based ID
        return f"table_{page_num}_{index + 1}"

    def extract_all_visual_content(self, pdf_path: str) -> Dict[str, List[Dict]]:
        """
        Extract both figures and tables from PDF

        Returns:
            {
                'figures': [...],
                'tables': [...]
            }
        """

        logger.info(f"Extracting all visual content from {pdf_path}")

        figures = self.extract_figures(pdf_path)
        tables = self.extract_tables(pdf_path)

        return {
            'figures': figures,
            'tables': tables,
            'total_visual_elements': len(figures) + len(tables)
        }
