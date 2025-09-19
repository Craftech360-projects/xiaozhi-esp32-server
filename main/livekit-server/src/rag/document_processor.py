"""
Advanced Textbook Processor with OCR, Table Extraction, and Multi-modal Content Handling
Supports PDF parsing with layout preservation, image processing, and intelligent chunking
"""

import logging
import os
import io
import re
import uuid
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from pathlib import Path

# PDF processing
try:
    import fitz  # PyMuPDF
    import pdfplumber
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

# OCR and image processing
try:
    import pytesseract
    from PIL import Image
    import cv2
    import numpy as np
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

# Table extraction
try:
    import camelot
    import tabula
    TABLE_EXTRACTION_AVAILABLE = True
except ImportError:
    TABLE_EXTRACTION_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class ContentChunk:
    """Structured representation of a content chunk"""
    id: str
    content: str
    content_type: str  # text|table|formula|diagram|example|exercise
    page_number: int
    section_title: str
    section_level: int
    bbox: Optional[Tuple[float, float, float, float]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ExtractedFigure:
    """Structured representation of an extracted figure"""
    index: int
    caption: str
    ocr_text: str
    description: str
    diagram_type: str
    bbox: Tuple[float, float, float, float]
    confidence: float
    image_data: Optional[bytes] = None


@dataclass
class ExtractedTable:
    """Structured representation of an extracted table"""
    index: int
    headers: List[str]
    rows: List[List[str]]
    markdown: str
    caption: str
    summary: str
    bbox: Tuple[float, float, float, float]
    table_type: str  # data|comparison|formula


@dataclass
class ExtractedFormula:
    """Structured representation of a mathematical formula"""
    latex: str
    mathml: str
    text_description: str
    variables: List[str]
    formula_type: str
    bbox: Tuple[float, float, float, float]


class TextbookProcessor:
    """Advanced processor for educational textbooks with multi-modal content extraction"""

    def __init__(self):
        self.check_dependencies()

        # OCR configuration
        self.ocr_config = r'--oem 3 --psm 6'

        # Pattern matching for educational content
        self.header_patterns = [
            r'^Chapter\s+\d+',
            r'^Section\s+\d+(\.\d+)*',
            r'^Unit\s+\d+',
            r'^\d+\.\d+',
            r'^[A-Z][A-Z\s]+$'  # ALL CAPS headers
        ]

        self.formula_patterns = [
            r'\$.*?\$',  # LaTeX inline math
            r'\\\[.*?\\\]',  # LaTeX display math
            r'\\begin\{equation\}.*?\\end\{equation\}',  # LaTeX equations
        ]

        self.example_patterns = [
            r'Example\s+\d+',
            r'Problem\s+\d+',
            r'Exercise\s+\d+',
            r'Solution:?',
            r'Answer:?'
        ]

    def check_dependencies(self):
        """Check if required dependencies are available"""
        if not PDF_AVAILABLE:
            logger.warning("PDF processing libraries not available. Install PyMuPDF and pdfplumber.")

        if not OCR_AVAILABLE:
            logger.warning("OCR libraries not available. Install pytesseract, PIL, opencv-python.")

        if not TABLE_EXTRACTION_AVAILABLE:
            logger.warning("Table extraction libraries not available. Install camelot-py and tabula-py.")

    async def process_textbook(
        self,
        pdf_path: str,
        grade: int,
        subject: str,
        textbook_name: str,
        author: str = "",
        isbn: str = ""
    ) -> List[ContentChunk]:
        """Process entire textbook and return structured chunks"""

        if not PDF_AVAILABLE:
            raise RuntimeError("PDF processing libraries not available")

        logger.info(f"Processing textbook: {textbook_name} (Grade {grade}, Subject: {subject})")

        try:
            # Extract content using PyMuPDF for layout preservation
            document = fitz.open(pdf_path)
            all_chunks = []

            for page_num in range(len(document)):
                page = document[page_num]
                logger.info(f"Processing page {page_num + 1}/{len(document)}")

                # Extract page data
                page_data = await self.extract_page_content(page, page_num + 1)

                # Create intelligent chunks
                chunks = self.create_semantic_chunks(
                    page_data, grade, subject, textbook_name, author, isbn
                )
                all_chunks.extend(chunks)

            document.close()
            logger.info(f"Successfully processed {len(all_chunks)} chunks from {textbook_name}")
            return all_chunks

        except Exception as e:
            logger.error(f"Failed to process textbook {pdf_path}: {e}")
            raise

    async def extract_page_content(self, page: fitz.Page, page_number: int) -> Dict[str, Any]:
        """Extract all content types from a single page"""

        page_data = {
            "page_number": page_number,
            "full_text": "",
            "sections": [],
            "figures": [],
            "tables": [],
            "formulas": [],
            "margin_notes": [],
            "bbox": page.rect
        }

        try:
            # Extract text with layout preservation
            page_data["sections"] = self.extract_sections_with_hierarchy(page)
            page_data["full_text"] = page.get_text()

            # Extract figures/images
            if OCR_AVAILABLE:
                page_data["figures"] = await self.extract_figures(page)

            # Extract tables
            if TABLE_EXTRACTION_AVAILABLE:
                page_data["tables"] = await self.extract_tables(page, page_number)

            # Extract mathematical formulas
            page_data["formulas"] = self.extract_formulas(page)

            # Extract margin notes and annotations
            page_data["margin_notes"] = self.extract_margin_notes(page)

            return page_data

        except Exception as e:
            logger.error(f"Failed to extract content from page {page_number}: {e}")
            return page_data

    def extract_sections_with_hierarchy(self, page: fitz.Page) -> List[Dict[str, Any]]:
        """Extract text sections while preserving hierarchical structure"""

        sections = []
        current_section = None

        try:
            # Get text blocks with formatting information
            blocks = page.get_text("dict")["blocks"]

            for block in blocks:
                if "lines" not in block:
                    continue

                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"].strip()
                        if not text:
                            continue

                        # Detect headers by font size and formatting
                        is_header, header_level = self.detect_header(span, text)

                        if is_header:
                            # Save previous section
                            if current_section:
                                sections.append(current_section)

                            # Start new section
                            current_section = {
                                "title": text,
                                "level": header_level,
                                "content": [],
                                "bbox": span["bbox"],
                                "font_size": span["size"],
                                "font_flags": span["flags"]
                            }
                        elif current_section:
                            # Add content to current section
                            current_section["content"].append({
                                "text": text,
                                "bbox": span["bbox"],
                                "font_size": span["size"],
                                "font_flags": span["flags"],
                                "type": self.classify_text_type(text)
                            })

            # Add final section
            if current_section:
                sections.append(current_section)

            return sections

        except Exception as e:
            logger.error(f"Failed to extract sections: {e}")
            return []

    def detect_header(self, span: Dict, text: str) -> Tuple[bool, int]:
        """Detect if text is a header and determine its level"""

        # Check pattern matching
        for pattern in self.header_patterns:
            if re.match(pattern, text, re.IGNORECASE):
                level = self.determine_header_level(text)
                return True, level

        # Check font size (larger fonts are likely headers)
        font_size = span.get("size", 12)
        if font_size > 14:
            return True, 1
        elif font_size > 12:
            return True, 2

        # Check font flags (bold, italic)
        flags = span.get("flags", 0)
        if flags & 2**4:  # Bold flag
            return True, 3

        return False, 0

    def determine_header_level(self, text: str) -> int:
        """Determine header level based on text patterns"""

        if re.match(r'^Chapter\s+\d+', text, re.IGNORECASE):
            return 1
        elif re.match(r'^Section\s+\d+', text, re.IGNORECASE):
            return 2
        elif re.match(r'^\d+\.\d+', text):
            return 3
        elif text.isupper() and len(text) > 3:
            return 2
        else:
            return 4

    def classify_text_type(self, text: str) -> str:
        """Classify text content type"""

        # Check for examples and exercises
        for pattern in self.example_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return "example"

        # Check for definitions
        if re.search(r'Definition:?|Define[sd]?', text, re.IGNORECASE):
            return "definition"

        # Check for formulas
        for pattern in self.formula_patterns:
            if re.search(pattern, text):
                return "formula"

        # Check for questions
        if text.strip().endswith('?'):
            return "question"

        return "text"

    async def extract_figures(self, page: fitz.Page) -> List[ExtractedFigure]:
        """Extract and process figures/diagrams from page"""

        figures = []

        try:
            image_list = page.get_images()

            for img_index, img in enumerate(image_list):
                try:
                    # Extract image
                    xref = img[0]
                    pix = fitz.Pixmap(page.parent, xref)

                    if pix.n - pix.alpha < 4:  # GRAY or RGB
                        # Convert to PIL Image
                        img_data = pix.tobytes("png")

                        ocr_text = ""
                        avg_confidence = 0

                        if OCR_AVAILABLE:
                            try:
                                pil_image = Image.open(io.BytesIO(img_data))

                                # Perform OCR
                                ocr_text = pytesseract.image_to_string(
                                    pil_image, config=self.ocr_config
                                ).strip()

                                # Get OCR confidence
                                ocr_data = pytesseract.image_to_data(
                                    pil_image, output_type=pytesseract.Output.DICT
                                )
                                confidences = [int(conf) for conf in ocr_data['conf'] if int(conf) > 0]
                                avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                            except Exception as ocr_error:
                                logger.warning(f"OCR failed for image {img_index}: {ocr_error}")
                                ocr_text = ""
                                avg_confidence = 0
                        else:
                            logger.debug(f"OCR not available, skipping text extraction for image {img_index}")

                        # Find caption
                        caption = self.find_image_caption(page, img)

                        # Generate description (placeholder - could use vision models)
                        description = self.generate_image_description(pil_image, caption, ocr_text)

                        # Classify diagram type
                        diagram_type = self.classify_diagram_type(ocr_text, caption, description)

                        figure = ExtractedFigure(
                            index=img_index,
                            caption=caption,
                            ocr_text=ocr_text,
                            description=description,
                            diagram_type=diagram_type,
                            bbox=page.get_image_bbox(img),
                            confidence=avg_confidence,
                            image_data=img_data
                        )
                        figures.append(figure)

                    pix = None  # Free memory

                except Exception as e:
                    logger.warning(f"Failed to process image {img_index}: {e}")
                    continue

            return figures

        except Exception as e:
            logger.error(f"Failed to extract figures: {e}")
            return []

    async def extract_tables(self, page: fitz.Page, page_number: int) -> List[ExtractedTable]:
        """Extract tables using multiple methods"""

        tables = []

        try:
            # Method 1: Use camelot for better table detection
            pdf_path = page.parent.name
            if pdf_path and TABLE_EXTRACTION_AVAILABLE:
                try:
                    camelot_tables = camelot.read_pdf(
                        pdf_path,
                        pages=str(page_number),
                        flavor='lattice'  # Good for tables with lines
                    )

                    for i, table in enumerate(camelot_tables):
                        if table.parsing_report['accuracy'] > 80:  # Only high-confidence tables
                            extracted_table = ExtractedTable(
                                index=i,
                                headers=table.df.columns.tolist(),
                                rows=table.df.values.tolist(),
                                markdown=table.df.to_markdown(index=False),
                                caption=self.find_table_caption(page, table._bbox),
                                summary=self.summarize_table(table.df),
                                bbox=table._bbox,
                                table_type=self.classify_table_type(table.df)
                            )
                            tables.append(extracted_table)

                except Exception as e:
                    logger.warning(f"Camelot table extraction failed: {e}")

            # Method 2: Fallback to basic table detection
            if not tables:
                tables.extend(self.extract_tables_basic(page))

            return tables

        except Exception as e:
            logger.error(f"Failed to extract tables: {e}")
            return []

    def extract_tables_basic(self, page: fitz.Page) -> List[ExtractedTable]:
        """Basic table extraction using text patterns"""

        tables = []

        try:
            text = page.get_text()
            lines = text.split('\n')

            # Look for table-like patterns
            table_lines = []
            for line in lines:
                # Simple heuristic: lines with multiple separated values
                if len(line.split()) > 3 and ('|' in line or '\t' in line or '  ' in line):
                    table_lines.append(line)

            if len(table_lines) > 2:  # At least header + 2 rows
                # Basic table parsing
                headers = table_lines[0].split()
                rows = [line.split() for line in table_lines[1:]]

                table = ExtractedTable(
                    index=0,
                    headers=headers,
                    rows=rows,
                    markdown=self.convert_to_markdown(headers, rows),
                    caption="",
                    summary=f"Table with {len(headers)} columns and {len(rows)} rows",
                    bbox=(0, 0, page.rect.width, page.rect.height),
                    table_type="data"
                )
                tables.append(table)

            return tables

        except Exception as e:
            logger.error(f"Basic table extraction failed: {e}")
            return []

    def convert_to_markdown(self, headers: List[str], rows: List[List[str]]) -> str:
        """Convert table data to markdown format"""

        if not headers or not rows:
            return ""

        # Create header row
        markdown = "| " + " | ".join(headers) + " |\n"
        markdown += "| " + " | ".join(["---"] * len(headers)) + " |\n"

        # Add data rows
        for row in rows:
            # Pad row to match header length
            padded_row = row + [""] * (len(headers) - len(row))
            markdown += "| " + " | ".join(padded_row[:len(headers)]) + " |\n"

        return markdown

    def extract_formulas(self, page: fitz.Page) -> List[ExtractedFormula]:
        """Extract mathematical formulas from page"""

        formulas = []

        try:
            text = page.get_text()

            # Look for LaTeX patterns
            for pattern in self.formula_patterns:
                matches = re.finditer(pattern, text, re.DOTALL)
                for match in matches:
                    formula_text = match.group()

                    formula = ExtractedFormula(
                        latex=formula_text,
                        mathml="",  # Could convert LaTeX to MathML
                        text_description=self.describe_formula(formula_text),
                        variables=self.extract_variables_from_formula(formula_text),
                        formula_type=self.classify_formula_type(formula_text),
                        bbox=(0, 0, 0, 0)  # Would need more sophisticated detection
                    )
                    formulas.append(formula)

            return formulas

        except Exception as e:
            logger.error(f"Failed to extract formulas: {e}")
            return []

    def extract_margin_notes(self, page: fitz.Page) -> List[str]:
        """Extract margin notes and annotations"""

        margin_notes = []

        try:
            # Get annotations
            for annot in page.annots():
                if annot.type[1] in ['Text', 'Note', 'Highlight']:
                    content = annot.info.get('content', '')
                    if content.strip():
                        margin_notes.append(content.strip())

            return margin_notes

        except Exception as e:
            logger.error(f"Failed to extract margin notes: {e}")
            return []

    def create_semantic_chunks(
        self,
        page_data: Dict[str, Any],
        grade: int,
        subject: str,
        textbook_name: str,
        author: str,
        isbn: str
    ) -> List[ContentChunk]:
        """Create intelligent chunks with preserved context and relationships"""

        chunks = []

        try:
            for section in page_data["sections"]:
                # Process section content
                section_text = self.combine_section_content(section)

                if not section_text.strip():
                    continue

                # Create chunks with semantic boundaries
                section_chunks = self.chunk_section_intelligently(section_text)

                for i, chunk_text in enumerate(section_chunks):
                    # Find references in this chunk
                    figure_refs = self.find_content_references(chunk_text, page_data["figures"], "figure")
                    table_refs = self.find_content_references(chunk_text, page_data["tables"], "table")
                    formula_refs = self.find_content_references(chunk_text, page_data["formulas"], "formula")

                    # Create chunk with metadata
                    chunk = ContentChunk(
                        id=str(uuid.uuid4()),
                        content=chunk_text,
                        content_type=self.classify_chunk_type(chunk_text),
                        page_number=page_data["page_number"],
                        section_title=section["title"],
                        section_level=section["level"],
                        bbox=section.get("bbox"),
                        metadata={
                            # Basic info
                            "textbook_name": textbook_name,
                            "textbook_author": author,
                            "isbn": isbn,
                            "grade": grade,
                            "subject": subject,

                            # Content organization
                            "chapter": self.extract_chapter_info(section["title"]),
                            "section": section["title"],
                            "section_number": section["level"],

                            # Context preservation
                            "preceding_content": section_chunks[i-1] if i > 0 else "",
                            "following_content": section_chunks[i+1] if i < len(section_chunks)-1 else "",
                            "full_page_text": page_data["full_text"],

                            # References
                            "figure_refs": figure_refs,
                            "table_refs": table_refs,
                            "formula_refs": formula_refs,

                            # Educational metadata
                            "topic": self.extract_topics(chunk_text, subject),
                            "keywords": self.extract_keywords(chunk_text, subject),
                            "difficulty_level": self.assess_difficulty(chunk_text, grade),
                            "cognitive_level": self.classify_cognitive_level(chunk_text),
                            "concepts": self.extract_concepts(chunk_text, subject),

                            # Quality metrics
                            "extraction_confidence": 1.0,
                            "verified": False,
                            "last_updated": "2024-01-01T00:00:00Z"
                        }
                    )
                    chunks.append(chunk)

            # Add figure chunks
            chunks.extend(self.create_figure_chunks(page_data["figures"], page_data, textbook_name, author, isbn, grade, subject))

            # Add table chunks
            chunks.extend(self.create_table_chunks(page_data["tables"], page_data, textbook_name, author, isbn, grade, subject))

            return chunks

        except Exception as e:
            logger.error(f"Failed to create semantic chunks: {e}")
            return []

    def chunk_section_intelligently(self, text: str, target_size: int = 400) -> List[str]:
        """Create chunks with semantic boundaries"""

        sentences = self.split_into_sentences(text)
        chunks = []
        current_chunk = []
        current_size = 0

        for sentence in sentences:
            sentence_size = len(sentence.split())

            # Check if adding this sentence exceeds target size
            if current_size + sentence_size > target_size and current_chunk:
                # Check for natural break points
                if self.is_natural_break(sentence):
                    chunks.append(' '.join(current_chunk))
                    current_chunk = [sentence]
                    current_size = sentence_size
                else:
                    current_chunk.append(sentence)
                    current_size += sentence_size
            else:
                current_chunk.append(sentence)
                current_size += sentence_size

        # Add final chunk
        if current_chunk:
            chunks.append(' '.join(current_chunk))

        return chunks

    def split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences with educational content awareness"""

        # Simple sentence splitting with some educational context awareness
        sentences = re.split(r'[.!?]+', text)

        cleaned_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and len(sentence) > 10:  # Filter out very short fragments
                cleaned_sentences.append(sentence)

        return cleaned_sentences

    def is_natural_break(self, sentence: str) -> bool:
        """Check if sentence represents a natural breaking point"""

        break_indicators = [
            r'^However,',
            r'^Therefore,',
            r'^In addition,',
            r'^Furthermore,',
            r'^Example\s+\d+',
            r'^Problem\s+\d+',
            r'^Solution:?',
            r'^Note:?'
        ]

        for pattern in break_indicators:
            if re.match(pattern, sentence, re.IGNORECASE):
                return True

        return False

    # Helper methods for content analysis
    def combine_section_content(self, section: Dict) -> str:
        """Combine section content items into coherent text"""
        texts = [item["text"] for item in section.get("content", [])]
        return " ".join(texts)

    def classify_chunk_type(self, text: str) -> str:
        """Classify the type of content chunk"""
        text_lower = text.lower()

        if any(word in text_lower for word in ["example", "problem", "exercise"]):
            return "example"
        elif any(word in text_lower for word in ["definition", "define"]):
            return "definition"
        elif any(word in text_lower for word in ["theorem", "proof", "lemma"]):
            return "theorem"
        elif "?" in text:
            return "question"
        else:
            return "text"

    def extract_chapter_info(self, title: str) -> str:
        """Extract chapter information from section title"""
        chapter_match = re.search(r'Chapter\s+(\d+)', title, re.IGNORECASE)
        if chapter_match:
            return f"Chapter {chapter_match.group(1)}"
        return ""

    def extract_topics(self, text: str, subject: str) -> List[str]:
        """Extract topic keywords based on subject"""
        # This would be enhanced with subject-specific topic extraction
        words = re.findall(r'\b[A-Z][a-z]+\b', text)
        return list(set(words))[:10]  # Limit to 10 topics

    def extract_keywords(self, text: str, subject: str) -> List[str]:
        """Extract important keywords from text"""
        # Simple keyword extraction - could be enhanced with NLP
        words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
        return list(set(words))[:15]  # Limit to 15 keywords

    def assess_difficulty(self, text: str, grade: int) -> str:
        """Assess difficulty level based on text complexity and grade"""
        # Simple heuristic based on sentence length and vocabulary
        avg_sentence_length = len(text.split()) / max(1, text.count('.'))

        if avg_sentence_length < 10:
            return "beginner"
        elif avg_sentence_length < 20:
            return "intermediate"
        else:
            return "advanced"

    def classify_cognitive_level(self, text: str) -> str:
        """Classify cognitive level based on Bloom's taxonomy"""
        text_lower = text.lower()

        if any(word in text_lower for word in ["analyze", "compare", "contrast", "examine"]):
            return "analyze"
        elif any(word in text_lower for word in ["apply", "use", "solve", "demonstrate"]):
            return "apply"
        elif any(word in text_lower for word in ["explain", "describe", "interpret"]):
            return "understand"
        else:
            return "remember"

    def extract_concepts(self, text: str, subject: str) -> List[str]:
        """Extract key concepts based on subject domain"""
        # Subject-specific concept extraction would be implemented here
        return []

    # Helper methods for content references
    def find_content_references(self, text: str, content_items: List, content_type: str) -> List[str]:
        """Find references to figures, tables, or formulas in text"""
        references = []

        if content_type == "figure":
            patterns = [r'Figure\s+(\d+)', r'Fig\.\s+(\d+)', r'figure\s+(\d+)']
        elif content_type == "table":
            patterns = [r'Table\s+(\d+)', r'table\s+(\d+)']
        elif content_type == "formula":
            patterns = [r'Equation\s+(\d+)', r'equation\s+(\d+)', r'Formula\s+(\d+)']
        else:
            return references

        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            references.extend(matches)

        return list(set(references))

    # Additional helper methods would be implemented here for:
    # - find_image_caption()
    # - generate_image_description()
    # - classify_diagram_type()
    # - find_table_caption()
    # - summarize_table()
    # - classify_table_type()
    # - describe_formula()
    # - extract_variables_from_formula()
    # - classify_formula_type()
    # - create_figure_chunks()
    # - create_table_chunks()

    def find_image_caption(self, page: fitz.Page, img: Any) -> str:
        """Find caption text near image"""
        # Placeholder implementation
        return ""

    def generate_image_description(self, image: Image.Image, caption: str, ocr_text: str) -> str:
        """Generate description of image content"""
        # Placeholder - could use vision models like CLIP or GPT-4V
        return f"Image with caption: {caption}. OCR text: {ocr_text[:100]}..."

    def classify_diagram_type(self, ocr_text: str, caption: str, description: str) -> str:
        """Classify type of diagram"""
        combined_text = f"{ocr_text} {caption} {description}".lower()

        if any(word in combined_text for word in ["graph", "chart", "plot"]):
            return "graph"
        elif any(word in combined_text for word in ["diagram", "flowchart", "flow"]):
            return "diagram"
        elif any(word in combined_text for word in ["illustration", "drawing"]):
            return "illustration"
        else:
            return "image"

    def find_table_caption(self, page: fitz.Page, bbox: Tuple) -> str:
        """Find caption for table"""
        # Placeholder implementation
        return ""

    def summarize_table(self, df) -> str:
        """Create summary of table content"""
        if hasattr(df, 'shape'):
            return f"Table with {df.shape[0]} rows and {df.shape[1]} columns"
        return "Data table"

    def classify_table_type(self, df) -> str:
        """Classify type of table"""
        # Simple classification based on content
        return "data"

    def describe_formula(self, latex: str) -> str:
        """Convert LaTeX formula to text description"""
        # Placeholder - could use specialized math-to-text conversion
        return f"Mathematical formula: {latex}"

    def extract_variables_from_formula(self, latex: str) -> List[str]:
        """Extract variable names from LaTeX formula"""
        # Simple regex to find single letter variables
        variables = re.findall(r'\b[a-zA-Z]\b', latex)
        return list(set(variables))

    def classify_formula_type(self, latex: str) -> str:
        """Classify type of mathematical formula"""
        if any(op in latex for op in ["\\frac", "\\int", "\\sum"]):
            return "calculus"
        elif any(op in latex for op in ["\\sqrt", "^2", "^3"]):
            return "algebraic"
        else:
            return "arithmetic"

    def create_figure_chunks(self, figures: List[ExtractedFigure], page_data: Dict, *args) -> List[ContentChunk]:
        """Create chunks for figure content"""
        chunks = []
        for figure in figures:
            chunk = ContentChunk(
                id=str(uuid.uuid4()),
                content=f"{figure.description} {figure.ocr_text}",
                content_type="diagram",
                page_number=page_data["page_number"],
                section_title=f"Figure {figure.index}",
                section_level=5,
                bbox=figure.bbox,
                metadata={
                    "content_type": "diagram",
                    "diagram_type": figure.diagram_type,
                    "ocr_text": figure.ocr_text,
                    "caption": figure.caption,
                    "ocr_confidence": figure.confidence
                }
            )
            chunks.append(chunk)
        return chunks

    def create_table_chunks(self, tables: List[ExtractedTable], page_data: Dict, *args) -> List[ContentChunk]:
        """Create chunks for table content"""
        chunks = []
        for table in tables:
            chunk = ContentChunk(
                id=str(uuid.uuid4()),
                content=f"{table.summary} {table.markdown}",
                content_type="table",
                page_number=page_data["page_number"],
                section_title=f"Table {table.index}",
                section_level=5,
                bbox=table.bbox,
                metadata={
                    "content_type": "table",
                    "table_markdown": table.markdown,
                    "table_caption": table.caption,
                    "table_summary": table.summary,
                    "table_type": table.table_type
                }
            )
            chunks.append(chunk)
        return chunks