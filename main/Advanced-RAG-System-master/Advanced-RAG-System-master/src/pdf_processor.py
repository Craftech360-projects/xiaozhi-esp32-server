# src/pdf_processor.py
import fitz  # PyMuPDF
import pdfplumber
import pytesseract
from PIL import Image
import pandas as pd
import numpy as np
import io
import re
from typing import List, Dict, Any, Tuple
import logging
from dataclasses import dataclass

@dataclass
class DocumentChunk:
    content: str
    chunk_type: str  # 'text', 'table', 'image'
    page_number: int
    metadata: Dict[str, Any]
    
class PDFProcessor:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
    def extract_content(self, pdf_path: str) -> List[DocumentChunk]:
        """Extract all content types from PDF"""
        chunks = []
        
        # Process with PyMuPDF for images and basic text
        doc = fitz.open(pdf_path)
        
        # Process with pdfplumber for tables and structured text
        with pdfplumber.open(pdf_path) as pdf:
            for page_num in range(len(doc)):
                page_fitz = doc[page_num]
                page_plumber = pdf.pages[page_num]
                
                # Extract text chunks
                text_chunks = self._extract_text_chunks(page_plumber, page_num)
                chunks.extend(text_chunks)
                
                # Extract table chunks
                table_chunks = self._extract_table_chunks(page_plumber, page_num)
                chunks.extend(table_chunks)
                
                # Extract image chunks
                image_chunks = self._extract_image_chunks(page_fitz, page_num)
                chunks.extend(image_chunks)
        
        doc.close()
        return chunks
    
    def _extract_text_chunks(self, page, page_num: int) -> List[DocumentChunk]:
        """Extract and chunk text content"""
        text = page.extract_text()
        if not text:
            return []
            
        # Clean and normalize text
        text = self._clean_text(text)
        
        # Create chunks with overlap
        chunks = []
        words = text.split()
        
        for i in range(0, len(words), self.config.CHUNK_SIZE - self.config.CHUNK_OVERLAP):
            chunk_words = words[i:i + self.config.CHUNK_SIZE]
            chunk_text = ' '.join(chunk_words)
            
            if len(chunk_text.strip()) > 50:  # Only meaningful chunks
                chunks.append(DocumentChunk(
                    content=chunk_text,
                    chunk_type='text',
                    page_number=page_num + 1,
                    metadata={
                        'word_count': len(chunk_words),
                        'char_count': len(chunk_text),
                        'chunk_index': len(chunks)
                    }
                ))
        
        return chunks
    
    def _extract_table_chunks(self, page, page_num: int) -> List[DocumentChunk]:
        """Extract table content"""
        tables = page.extract_tables()
        chunks = []
        
        for table_idx, table in enumerate(tables):
            if not table:
                continue
                
            # Convert table to DataFrame for better processing
            df = pd.DataFrame(table[1:], columns=table[0] if table[0] else None)
            
            # Create structured text representation
            table_text = self._table_to_text(df)
            
            # Also create CSV representation
            csv_repr = df.to_csv(index=False)
            
            chunks.append(DocumentChunk(
                content=f"TABLE DATA:\n{table_text}\n\nCSV FORMAT:\n{csv_repr}",
                chunk_type='table',
                page_number=page_num + 1,
                metadata={
                    'table_index': table_idx,
                    'rows': len(df),
                    'columns': len(df.columns) if df.columns is not None else 0,
                    'table_shape': df.shape
                }
            ))
        
        return chunks
    
    def _extract_image_chunks(self, page, page_num: int) -> List[DocumentChunk]:
        """Extract and OCR image content"""
        chunks = []
        image_list = page.get_images()
        
        for img_idx, img in enumerate(image_list):
            try:
                # Extract image
                xref = img[0]
                pix = fitz.Pixmap(page.parent, xref)
                
                if pix.n - pix.alpha < 4:  # GRAY or RGB
                    img_data = pix.tobytes("png")
                    image = Image.open(io.BytesIO(img_data))
                    
                    # Resize if too large
                    if image.size[0] > self.config.MAX_IMAGE_SIZE[0] or image.size[1] > self.config.MAX_IMAGE_SIZE[1]:
                        image.thumbnail(self.config.MAX_IMAGE_SIZE, Image.Resampling.LANCZOS)
                    
                    # OCR the image
                    ocr_text = pytesseract.image_to_string(image)
                    
                    if len(ocr_text.strip()) > 20:  # Only if meaningful text found
                        chunks.append(DocumentChunk(
                            content=f"IMAGE CONTENT (OCR):\n{ocr_text}",
                            chunk_type='image',
                            page_number=page_num + 1,
                            metadata={
                                'image_index': img_idx,
                                'image_size': image.size,
                                'ocr_confidence': self._get_ocr_confidence(image)
                            }
                        ))
                
                pix = None
                
            except Exception as e:
                self.logger.warning(f"Could not process image {img_idx} on page {page_num}: {e}")
                continue
        
        return chunks
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep punctuation
        text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)\"\']+', '', text)
        return text.strip()
    
    def _table_to_text(self, df: pd.DataFrame) -> str:
        """Convert DataFrame to readable text"""
        return df.to_string(index=False, na_rep='')
    
    def _get_ocr_confidence(self, image: Image.Image) -> float:
        """Get OCR confidence score"""
        try:
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            return np.mean(confidences) if confidences else 0.0
        except:
            return 0.0
