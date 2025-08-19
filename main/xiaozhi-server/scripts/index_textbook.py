#!/usr/bin/env python3
"""
Script to index textbooks into the RAG system
Usage: python index_textbook.py <pdf_path> <subject> <grade>
Example: python index_textbook.py ./textbooks/math_grade5.pdf "数学" "五年级"
"""

import os
import sys
import argparse
from pathlib import Path

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import PyPDF2
from core.providers.rag.simple_rag import SimpleRAGProvider
from config.logger import setup_logging

logger = setup_logging()


def extract_text_from_pdf(pdf_path: str) -> list:
    """Extract text from PDF file, returning list of (page_num, text) tuples"""
    pages_text = []
    
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            total_pages = len(pdf_reader.pages)
            
            logger.info(f"Processing PDF with {total_pages} pages")
            
            for page_num in range(total_pages):
                try:
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text()
                    
                    if text and text.strip():
                        pages_text.append((page_num + 1, text))
                        logger.debug(f"Extracted text from page {page_num + 1}")
                    else:
                        logger.warning(f"No text found on page {page_num + 1}")
                        
                except Exception as e:
                    logger.error(f"Error extracting page {page_num + 1}: {str(e)}")
                    continue
                    
    except Exception as e:
        logger.error(f"Error reading PDF file: {str(e)}")
        raise
        
    return pages_text


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list:
    """
    Split text into chunks with overlap
    
    Args:
        text: Text to split
        chunk_size: Approximate size of each chunk in characters
        overlap: Number of characters to overlap between chunks
        
    Returns:
        List of text chunks
    """
    # Split by paragraphs first
    paragraphs = text.split('\n\n')
    
    chunks = []
    current_chunk = ""
    
    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        
        if not paragraph:
            continue
            
        # If adding this paragraph would exceed chunk size
        if len(current_chunk) + len(paragraph) > chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
            
            # Start new chunk with overlap from previous chunk
            if len(current_chunk) > overlap:
                overlap_text = current_chunk[-overlap:]
                current_chunk = overlap_text + " " + paragraph
            else:
                current_chunk = paragraph
        else:
            # Add paragraph to current chunk
            if current_chunk:
                current_chunk += "\n\n" + paragraph
            else:
                current_chunk = paragraph
    
    # Add the last chunk
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks


def index_textbook(pdf_path: str, subject: str, grade: str, chunk_size: int = 500):
    """
    Index a textbook PDF into the RAG system
    
    Args:
        pdf_path: Path to the PDF file
        subject: Subject of the textbook (e.g., "数学", "语文")
        grade: Grade level (e.g., "五年级", "六年级")
        chunk_size: Size of text chunks
    """
    # Initialize RAG provider
    rag_config = {
        'db_path': './rag_db',
        'collection_name': 'textbooks'
    }
    rag = SimpleRAGProvider(rag_config)
    
    # Get collection info before indexing
    info_before = rag.get_collection_info()
    logger.info(f"Collection before indexing: {info_before['count']} documents")
    
    # Extract text from PDF
    logger.info(f"Extracting text from: {pdf_path}")
    pages_text = extract_text_from_pdf(pdf_path)
    
    if not pages_text:
        logger.error("No text extracted from PDF")
        return
    
    # Process each page
    all_chunks = []
    all_metadata = []
    
    for page_num, page_text in pages_text:
        # Chunk the page text
        chunks = chunk_text(page_text, chunk_size=chunk_size)
        
        # Create metadata for each chunk
        for i, chunk in enumerate(chunks):
            if len(chunk.strip()) < 50:  # Skip very small chunks
                continue
                
            metadata = {
                'page': page_num,
                'chunk_index': i,
                'subject': subject,
                'grade': grade,
                'source': os.path.basename(pdf_path),
                'full_path': os.path.abspath(pdf_path)
            }
            
            all_chunks.append(chunk)
            all_metadata.append(metadata)
    
    # Index all chunks at once
    logger.info(f"Indexing {len(all_chunks)} chunks into RAG system")
    success = rag.add_documents(all_chunks, all_metadata)
    
    if success:
        # Get collection info after indexing
        info_after = rag.get_collection_info()
        logger.info(f"Successfully indexed {len(all_chunks)} chunks")
        logger.info(f"Collection after indexing: {info_after['count']} documents")
        logger.info(f"Textbook '{os.path.basename(pdf_path)}' has been indexed successfully!")
    else:
        logger.error("Failed to index documents")


def main():
    parser = argparse.ArgumentParser(description='Index a textbook PDF into the RAG system')
    parser.add_argument('pdf_path', help='Path to the PDF file')
    parser.add_argument('subject', help='Subject of the textbook (e.g., 数学, 语文, 英语)')
    parser.add_argument('grade', help='Grade level (e.g., 五年级, 六年级)')
    parser.add_argument('--chunk-size', type=int, default=500, 
                       help='Size of text chunks (default: 500 characters)')
    parser.add_argument('--reset', action='store_true',
                       help='Reset the collection before indexing')
    
    args = parser.parse_args()
    
    # Validate PDF path
    if not os.path.exists(args.pdf_path):
        logger.error(f"PDF file not found: {args.pdf_path}")
        sys.exit(1)
    
    if not args.pdf_path.lower().endswith('.pdf'):
        logger.error("File must be a PDF")
        sys.exit(1)
    
    # Reset collection if requested
    if args.reset:
        logger.info("Resetting collection...")
        rag = SimpleRAGProvider({'db_path': './rag_db'})
        rag.delete_collection()
    
    # Index the textbook
    try:
        index_textbook(args.pdf_path, args.subject, args.grade, args.chunk_size)
    except Exception as e:
        logger.error(f"Indexing failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()