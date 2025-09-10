"""
Enhanced Document Processor for Educational RAG System
Combines features from both sample projects:
- Multi-format PDF processing (text, tables, images with OCR)
- Educational content classification and metadata extraction
- Smart chunking with content-aware strategies
- Integration with xiaozhi-server logging system
"""

import os
import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
import uuid

# Import core dependencies
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from config.logger import setup_logging

# PDF processing imports with fallbacks
try:
    import fitz  # PyMuPDF
    FITZ_AVAILABLE = True
except ImportError:
    FITZ_AVAILABLE = False

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

try:
    import pytesseract
    from PIL import Image
    import pandas as pd
    import numpy as np
    import io
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

TAG = __name__
logger = setup_logging()


@dataclass
class DocumentChunk:
    """Enhanced document chunk with comprehensive metadata"""
    content: str
    chunk_type: str  # 'text', 'table', 'image', 'concept', 'example', 'exercise'
    page_number: int
    metadata: Dict[str, Any]
    embedding_vector: Optional[List[float]] = None


class EnhancedDocumentProcessor:
    """Enhanced document processor combining educational focus with multi-format support"""
    
    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 100):
        """Initialize the enhanced document processor"""
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", ", ", " ", ""]
        )
        
        # Configuration
        self.max_image_size = (800, 600)
        self.min_chunk_length = 50
        
        # Check dependencies
        self._check_dependencies()
        
        logger.bind(tag=TAG).info(f"[ENHANCED-DOC-PROC] Initialized with chunk_size={chunk_size}, chunk_overlap={chunk_overlap}")
    
    def _check_dependencies(self):
        """Check and log available dependencies"""
        deps = {
            'PyMuPDF (fitz)': FITZ_AVAILABLE,
            'pdfplumber': PDFPLUMBER_AVAILABLE,
            'OCR (pytesseract/PIL)': OCR_AVAILABLE
        }
        
        for dep, available in deps.items():
            status = "✅ Available" if available else "❌ Missing"
            logger.bind(tag=TAG).info(f"[ENHANCED-DOC-PROC] {dep}: {status}")
        
        if not FITZ_AVAILABLE and not PDFPLUMBER_AVAILABLE:
            logger.bind(tag=TAG).warning("[ENHANCED-DOC-PROC] No PDF processing libraries available - falling back to basic text processing")
    
    def process_document(self, file_path: str, grade: str = "class-6", 
                        subject: str = "mathematics", document_name: Optional[str] = None) -> List[DocumentChunk]:
        """Process a document file with enhanced multi-format extraction"""
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                logger.bind(tag=TAG).error(f"[ENHANCED-DOC-PROC] File not found: {file_path}")
                return []
            
            doc_name = document_name or file_path.stem
            file_ext = file_path.suffix.lower()
            
            logger.bind(tag=TAG).info(f"[ENHANCED-DOC-PROC] Processing {file_ext} document: {doc_name}")
            
            if file_ext == '.pdf':
                return self._process_pdf_advanced(str(file_path), grade, subject, doc_name)
            elif file_ext in ['.txt', '.md']:
                return self._process_text_file(str(file_path), grade, subject, doc_name)
            else:
                logger.bind(tag=TAG).warning(f"[ENHANCED-DOC-PROC] Unsupported file format: {file_ext}")
                return []
                
        except Exception as e:
            logger.bind(tag=TAG).error(f"[ENHANCED-DOC-PROC] Error processing document {file_path}: {e}")
            return []
    
    def _process_pdf_advanced(self, pdf_path: str, grade: str, subject: str, doc_name: str) -> List[DocumentChunk]:
        """Advanced PDF processing with multi-format content extraction"""
        chunks = []
        
        # Try advanced processing first
        if FITZ_AVAILABLE and PDFPLUMBER_AVAILABLE:
            chunks = self._extract_multiformat_content(pdf_path, grade, subject, doc_name)
        
        # Fallback to basic processing
        if not chunks:
            chunks = self._process_pdf_basic(pdf_path, grade, subject, doc_name)
        
        logger.bind(tag=TAG).info(f"[ENHANCED-DOC-PROC] Processed PDF into {len(chunks)} chunks")
        return chunks
    
    def _extract_multiformat_content(self, pdf_path: str, grade: str, subject: str, doc_name: str) -> List[DocumentChunk]:
        """Extract text, tables, and images from PDF"""
        chunks = []
        
        try:
            # Open with both libraries
            doc = fitz.open(pdf_path)
            
            with pdfplumber.open(pdf_path) as pdf:
                for page_num in range(len(doc)):
                    page_fitz = doc[page_num]
                    page_plumber = pdf.pages[page_num]
                    
                    logger.bind(tag=TAG).debug(f"[ENHANCED-DOC-PROC] Processing page {page_num + 1}")
                    
                    # Extract text chunks
                    text_chunks = self._extract_text_chunks_advanced(page_plumber, page_num + 1, grade, subject, doc_name)
                    chunks.extend(text_chunks)
                    
                    # Extract table chunks
                    if hasattr(page_plumber, 'extract_tables'):
                        table_chunks = self._extract_table_chunks(page_plumber, page_num + 1, grade, subject, doc_name)
                        chunks.extend(table_chunks)
                    
                    # Extract image chunks (if OCR available)
                    if OCR_AVAILABLE:
                        image_chunks = self._extract_image_chunks_with_ocr(page_fitz, page_num + 1, grade, subject, doc_name)
                        chunks.extend(image_chunks)
            
            doc.close()
            return chunks
            
        except Exception as e:
            logger.bind(tag=TAG).warning(f"[ENHANCED-DOC-PROC] Advanced PDF processing failed: {e}")
            return []
    
    def _extract_text_chunks_advanced(self, page, page_num: int, grade: str, subject: str, doc_name: str) -> List[DocumentChunk]:
        """Extract and intelligently chunk text content"""
        try:
            text = page.extract_text()
            if not text or len(text.strip()) < self.min_chunk_length:
                return []
            
            # Preprocess text
            processed_text = self._preprocess_educational_content(text)
            
            # Extract chapter information
            chapter_info = self._extract_chapter_info(processed_text, page_num)
            
            # Create text chunks
            text_chunks = self.text_splitter.split_text(processed_text)
            
            chunks = []
            for i, chunk_text in enumerate(text_chunks):
                if len(chunk_text.strip()) < self.min_chunk_length:
                    continue
                
                # Classify content type
                content_category = self._classify_educational_content(chunk_text)
                
                # Create comprehensive metadata
                metadata = self._create_comprehensive_metadata(
                    chunk_text, page_num, i, grade, subject, doc_name, 
                    chapter_info, content_category, 'text'
                )
                
                chunk = DocumentChunk(
                    content=chunk_text,
                    chunk_type='text',
                    page_number=page_num,
                    metadata=metadata
                )
                chunks.append(chunk)
            
            return chunks
            
        except Exception as e:
            logger.bind(tag=TAG).warning(f"[ENHANCED-DOC-PROC] Text extraction failed for page {page_num}: {e}")
            return []
    
    def _process_pdf_basic(self, pdf_path: str, grade: str, subject: str, doc_name: str) -> List[DocumentChunk]:
        """Basic PDF processing fallback using PyPDF"""
        try:
            from langchain_community.document_loaders import PyPDFLoader
            
            loader = PyPDFLoader(pdf_path)
            documents = loader.load()
            
            if not documents:
                return []
            
            chunks = []
            for page_num, doc in enumerate(documents, 1):
                processed_content = self._preprocess_educational_content(doc.page_content)
                
                if len(processed_content.strip()) < self.min_chunk_length:
                    continue
                
                chapter_info = self._extract_chapter_info(processed_content, page_num)
                text_chunks = self.text_splitter.split_text(processed_content)
                
                for i, chunk_text in enumerate(text_chunks):
                    if len(chunk_text.strip()) < self.min_chunk_length:
                        continue
                    
                    content_category = self._classify_educational_content(chunk_text)
                    
                    metadata = self._create_comprehensive_metadata(
                        chunk_text, page_num, i, grade, subject, doc_name,
                        chapter_info, content_category, 'text'
                    )
                    
                    chunk = DocumentChunk(
                        content=chunk_text,
                        chunk_type='text',
                        page_number=page_num,
                        metadata=metadata
                    )
                    chunks.append(chunk)
            
            return chunks
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"[ENHANCED-DOC-PROC] Basic PDF processing failed: {e}")
            return []
    
    def _process_text_file(self, text_path: str, grade: str, subject: str, doc_name: str) -> List[DocumentChunk]:
        """Process plain text files"""
        try:
            with open(text_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if len(content.strip()) < self.min_chunk_length:
                return []
            
            processed_content = self._preprocess_educational_content(content)
            chapter_info = self._extract_chapter_info(processed_content, 1)
            text_chunks = self.text_splitter.split_text(processed_content)
            
            chunks = []
            for i, chunk_text in enumerate(text_chunks):
                if len(chunk_text.strip()) < self.min_chunk_length:
                    continue
                
                content_category = self._classify_educational_content(chunk_text)
                
                metadata = self._create_comprehensive_metadata(
                    chunk_text, 1, i, grade, subject, doc_name,
                    chapter_info, content_category, 'text'
                )
                
                chunk = DocumentChunk(
                    content=chunk_text,
                    chunk_type='text',
                    page_number=1,
                    metadata=metadata
                )
                chunks.append(chunk)
            
            return chunks
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"[ENHANCED-DOC-PROC] Text file processing failed: {e}")
            return []
    
    def _preprocess_educational_content(self, content: str) -> str:
        """Preprocess educational content for better chunking"""
        # Remove excessive whitespace
        content = re.sub(r'\s+', ' ', content)
        
        # Remove page headers/footers patterns
        content = re.sub(r'^\d+\s*$', '', content, flags=re.MULTILINE)
        content = re.sub(r'^Page \d+.*$', '', content, flags=re.MULTILINE)
        
        # Normalize mathematical expressions
        content = re.sub(r'(\d+)\s*[×x]\s*(\d+)', r'\1 × \2', content)
        content = re.sub(r'(\d+)\s*[÷/]\s*(\d+)', r'\1 ÷ \2', content)
        content = re.sub(r'(\d+)\s*\+\s*(\d+)', r'\1 + \2', content)
        content = re.sub(r'(\d+)\s*-\s*(\d+)', r'\1 - \2', content)
        
        return content.strip()
    
    def _extract_chapter_info(self, content: str, page_num: int) -> Dict[str, Any]:
        """Extract chapter information from content"""
        chapter_info = {
            'chapter_number': None,
            'chapter_title': None,
            'topics': [],
            'learning_objectives': [],
            'difficulty_level': 'medium'
        }
        
        # Extract chapter number and title
        chapter_patterns = [
            r'Chapter\s+(\d+)[\s:]*(.+?)(?:\n|$)',
            r'CHAPTER\s+(\d+)[\s:]*(.+?)(?:\n|$)',
            r'(\d+)\.?\s+([A-Z][^.]+?)(?:\n|$)'
        ]
        
        for pattern in chapter_patterns:
            match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
            if match:
                chapter_info['chapter_number'] = int(match.group(1))
                chapter_info['chapter_title'] = match.group(2).strip()
                break
        
        # Determine difficulty level based on content complexity
        if any(word in content.lower() for word in ['advanced', 'complex', 'difficult']):
            chapter_info['difficulty_level'] = 'hard'
        elif any(word in content.lower() for word in ['basic', 'simple', 'introduction']):
            chapter_info['difficulty_level'] = 'easy'
        
        return chapter_info
    
    def _classify_educational_content(self, text: str) -> str:
        """Classify educational content type"""
        text_lower = text.lower()
        
        # Check for different content types
        if any(word in text_lower for word in ['definition', 'is defined', 'means', 'refers to']):
            return 'definition'
        elif any(word in text_lower for word in ['example', 'for instance', 'consider', 'suppose']):
            return 'example'
        elif any(word in text_lower for word in ['exercise', 'problem', 'solve', 'calculate', 'find']):
            return 'exercise'
        elif any(word in text_lower for word in ['formula', 'equation', 'rule', 'method']):
            return 'formula'
        elif any(word in text_lower for word in ['table', 'data', 'chart']):
            return 'table'
        elif any(word in text_lower for word in ['remember', 'note', 'important', 'key point']):
            return 'key_concept'
        else:
            return 'concept'
    
    def _extract_table_chunks(self, page, page_num: int, grade: str, subject: str, doc_name: str) -> List[DocumentChunk]:
        """Extract and process table content from PDF pages"""
        chunks = []
        try:
            tables = page.extract_tables()
            if not tables:
                return chunks
            
            for table_idx, table in enumerate(tables):
                if not table or len(table) < 2:  # Skip empty or single-row tables
                    continue
                
                # Convert table to formatted text
                table_text = self._format_table_as_text(table)
                
                if len(table_text.strip()) < self.min_chunk_length:
                    continue
                
                # Create metadata for table
                chapter_info = self._extract_chapter_info("", page_num)
                metadata = self._create_comprehensive_metadata(
                    table_text, page_num, table_idx, grade, subject, doc_name,
                    chapter_info, 'table', 'table'
                )
                
                # Add table-specific metadata
                metadata['table_rows'] = len(table)
                metadata['table_columns'] = len(table[0]) if table else 0
                
                chunk = DocumentChunk(
                    content=table_text,
                    chunk_type='table',
                    page_number=page_num,
                    metadata=metadata
                )
                chunks.append(chunk)
                
                logger.bind(tag=TAG).debug(f"[ENHANCED-DOC-PROC] Extracted table from page {page_num} with {len(table)} rows")
        
        except Exception as e:
            logger.bind(tag=TAG).warning(f"[ENHANCED-DOC-PROC] Table extraction failed on page {page_num}: {e}")
        
        return chunks
    
    def _format_table_as_text(self, table: List[List[str]]) -> str:
        """Format table data as structured text"""
        if not table:
            return ""
        
        # Clean and format table data
        formatted_rows = []
        for row in table:
            cleaned_row = [str(cell).strip() if cell else "" for cell in row]
            if any(cleaned_row):  # Skip empty rows
                formatted_rows.append(" | ".join(cleaned_row))
        
        return "\n".join(formatted_rows)
    
    def _extract_image_chunks_with_ocr(self, page, page_num: int, grade: str, subject: str, doc_name: str) -> List[DocumentChunk]:
        """Extract and process images with OCR"""
        chunks = []
        
        if not OCR_AVAILABLE:
            return chunks
        
        try:
            image_list = page.get_images()
            
            for img_idx, img in enumerate(image_list):
                try:
                    # Extract image
                    xref = img[0]
                    pix = fitz.Pixmap(page.parent, xref)
                    
                    # Convert to PIL Image
                    img_data = pix.tobytes("png")
                    image = Image.open(io.BytesIO(img_data))
                    
                    # Resize if too large
                    if image.size[0] > self.max_image_size[0] or image.size[1] > self.max_image_size[1]:
                        image.thumbnail(self.max_image_size, Image.Resampling.LANCZOS)
                    
                    # Perform OCR
                    ocr_text = pytesseract.image_to_string(image)
                    
                    if len(ocr_text.strip()) < self.min_chunk_length:
                        continue
                    
                    # Process OCR text
                    processed_text = self._preprocess_educational_content(ocr_text)
                    
                    # Create metadata
                    chapter_info = self._extract_chapter_info(processed_text, page_num)
                    metadata = self._create_comprehensive_metadata(
                        processed_text, page_num, img_idx, grade, subject, doc_name,
                        chapter_info, 'image', 'image'
                    )
                    
                    chunk = DocumentChunk(
                        content=processed_text,
                        chunk_type='image',
                        page_number=page_num,
                        metadata=metadata
                    )
                    chunks.append(chunk)
                    
                    logger.bind(tag=TAG).debug(f"[ENHANCED-DOC-PROC] Extracted text from image on page {page_num}")
                    
                except Exception as e:
                    logger.bind(tag=TAG).debug(f"[ENHANCED-DOC-PROC] Failed to process image {img_idx} on page {page_num}: {e}")
                    continue
        
        except Exception as e:
            logger.bind(tag=TAG).warning(f"[ENHANCED-DOC-PROC] Image extraction failed on page {page_num}: {e}")
        
        return chunks
    
    def _create_comprehensive_metadata(self, content: str, page_num: int, chunk_idx: int,
                                     grade: str, subject: str, doc_name: str,
                                     chapter_info: Dict[str, Any], content_category: str,
                                     chunk_type: str) -> Dict[str, Any]:
        """Create comprehensive metadata for educational content"""
        return {
            'unique_id': f"{doc_name}_{page_num}_{chunk_idx}",
            'grade': grade,
            'subject': subject,
            'document_name': doc_name,
            'page_number': page_num,
            'chunk_index': chunk_idx,
            'chunk_type': chunk_type,
            'content_category': content_category,
            'content_type': content_category,  # Add content_type for consistency
            'chapter_number': chapter_info.get('chapter_number'),
            'chapter_title': chapter_info.get('chapter_title'),
            'topics': chapter_info.get('topics', []),
            'learning_objectives': chapter_info.get('learning_objectives', []),
            'difficulty_level': chapter_info.get('difficulty_level', 'medium'),
            'text_length': len(content),
            'word_count': len(content.split()),
            'has_examples': 'example' in content.lower(),
            'has_exercises': any(word in content.lower() for word in ['exercise', 'problem', 'solve']),
            'has_mathematical_content': any(char in content for char in ['×', '÷', '+', '-', '=', '%', '²', '³']),
            'unique_id': str(uuid.uuid4()),
            'source': doc_name,
            'file_name': doc_name
        }
    
    def batch_process_documents(self, file_paths: List[str], grade: str = "class-6", 
                              subject: str = "mathematics") -> List[DocumentChunk]:
        """Process multiple documents in batch"""
        all_chunks = []
        
        for file_path in file_paths:
            try:
                chunks = self.process_document(file_path, grade, subject)
                all_chunks.extend(chunks)
                logger.bind(tag=TAG).info(f"[ENHANCED-DOC-PROC] Processed {file_path}: {len(chunks)} chunks")
            except Exception as e:
                logger.bind(tag=TAG).warning(f"[ENHANCED-DOC-PROC] Failed to process {file_path}: {e}")
                continue
        
        logger.bind(tag=TAG).info(f"[ENHANCED-DOC-PROC] Batch processed {len(file_paths)} documents into {len(all_chunks)} total chunks")
        return all_chunks
    
    def get_processing_stats(self, chunks: List[DocumentChunk]) -> Dict[str, Any]:
        """Get processing statistics"""
        if not chunks:
            return {'total_chunks': 0}
        
        stats = {
            'total_chunks': len(chunks),
            'chunk_types': {},
            'content_categories': {},
            'pages_processed': set(),
            'subjects': set(),
            'grades': set()
        }
        
        for chunk in chunks:
            # Count chunk types
            chunk_type = chunk.chunk_type
            stats['chunk_types'][chunk_type] = stats['chunk_types'].get(chunk_type, 0) + 1
            
            # Count content categories
            category = chunk.metadata.get('content_category', 'unknown')
            stats['content_categories'][category] = stats['content_categories'].get(category, 0) + 1
            
            # Collect metadata
            stats['pages_processed'].add(chunk.metadata.get('page_number'))
            stats['subjects'].add(chunk.metadata.get('subject'))
            stats['grades'].add(chunk.metadata.get('grade'))
        
        # Convert sets to lists for JSON serialization
        stats['pages_processed'] = sorted(list(stats['pages_processed']))
        stats['subjects'] = list(stats['subjects'])
        stats['grades'] = list(stats['grades'])
        
        return stats


if __name__ == "__main__":
    # Test the enhanced document processor
    processor = EnhancedDocumentProcessor()
    logger.info("Enhanced document processor initialized successfully")