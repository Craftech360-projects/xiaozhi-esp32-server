import os
import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from pypdf import PdfReader
from langchain_core.documents import Document
from dotenv import load_dotenv

from educational_config import Grade, Subject, get_collection_name, get_chapter_metadata, get_chapter_by_title
from text_processor import TextProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()


class EducationalTextbookProcessor:
    def __init__(self):
        self.text_processor = TextProcessor()
        
        # Educational text processing parameters
        self.chunk_size = int(os.getenv("EDU_CHUNK_SIZE", "800"))  # Smaller chunks for better comprehension
        self.chunk_overlap = int(os.getenv("EDU_CHUNK_OVERLAP", "150"))
        
        # Patterns for detecting educational content
        self.chapter_patterns = [
            r'^Chapter\s+(\d+)\.?\s*(.+?)$',
            r'^(\d+)\.?\s+(.+?)$',
            r'^\s*CHAPTER\s+(\d+)\.?\s*(.+?)$'
        ]
        
        self.section_patterns = [
            r'^\d+\.\d+\s+(.+?)$',
            r'^[A-Z]\.\s+(.+?)$',
            r'^\d+\)\s+(.+?)$'
        ]
        
        self.exercise_patterns = [
            r'Exercise\s+\d+(\.\d+)?',
            r'Practice\s+Problems?',
            r'Questions?',
            r'Try\s+These?',
            r'Activities?'
        ]
    
    def detect_chapter_from_filename(self, filename: str) -> Optional[Tuple[int, str]]:
        """Extract chapter number and title from filename"""
        filename = Path(filename).stem
        
        # Try different patterns
        patterns = [
            r'[Cc]hapter[-_\s]*(\d+)[-_\s]*(.+)',
            r'(\d+)[-_\s]*(.+)',
            r'Ch[-_\s]*(\d+)[-_\s]*(.+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filename)
            if match:
                try:
                    chapter_num = int(match.group(1))
                    chapter_title = re.sub(r'[-_]', ' ', match.group(2)).strip()
                    return chapter_num, chapter_title
                except ValueError:
                    continue
        
        return None
    
    def extract_text_with_structure(self, pdf_path: str) -> Dict[str, Any]:
        """Extract text from PDF while preserving educational structure"""
        try:
            reader = PdfReader(pdf_path)
            content = {
                'full_text': '',
                'pages': [],
                'sections': [],
                'exercises': [],
                'chapter_info': None
            }
            
            # Try to detect chapter from filename
            chapter_info = self.detect_chapter_from_filename(pdf_path)
            if chapter_info:
                content['chapter_info'] = {
                    'number': chapter_info[0],
                    'title': chapter_info[1]
                }
            
            for page_num, page in enumerate(reader.pages):
                text = page.extract_text()
                
                # Clean the text
                text = self._clean_educational_text(text)
                
                content['pages'].append({
                    'page_number': page_num + 1,
                    'text': text
                })
                
                content['full_text'] += f"\n\nPage {page_num + 1}:\n{text}"
                
                # Identify sections and exercises
                sections = self._identify_sections(text)
                exercises = self._identify_exercises(text)
                
                content['sections'].extend(sections)
                content['exercises'].extend(exercises)
            
            return content
            
        except Exception as e:
            logger.error(f"Failed to extract text from {pdf_path}: {e}")
            return {'full_text': '', 'pages': [], 'sections': [], 'exercises': []}
    
    def _clean_educational_text(self, text: str) -> str:
        """Clean text specifically for educational content"""
        # Remove page numbers and headers/footers
        text = re.sub(r'\n\d+\s*\n', '\n', text)
        text = re.sub(r'\nPage \d+.*?\n', '\n', text)
        
        # Fix common PDF extraction issues
        text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)  # Add space between words
        text = re.sub(r'\s+', ' ', text)  # Multiple spaces to single
        text = re.sub(r'([.!?])\s*([A-Z])', r'\1 \2', text)  # Space after sentences
        
        # Clean mathematical expressions (preserve them better)
        text = re.sub(r'(\d)\s+([+\-×÷=])\s+(\d)', r'\1 \2 \3', text)
        
        return text.strip()
    
    def _identify_sections(self, text: str) -> List[Dict[str, str]]:
        """Identify sections within the text"""
        sections = []
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            for pattern in self.section_patterns:
                if re.match(pattern, line):
                    sections.append({
                        'title': line,
                        'line_number': i + 1,
                        'type': 'section'
                    })
                    break
        
        return sections
    
    def _identify_exercises(self, text: str) -> List[Dict[str, str]]:
        """Identify exercises and practice problems"""
        exercises = []
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            for pattern in self.exercise_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    exercises.append({
                        'title': line,
                        'line_number': i + 1,
                        'type': 'exercise'
                    })
                    break
        
        return exercises
    
    def process_textbook_pdf(self, pdf_path: str, grade: Grade, subject: Subject) -> List[Document]:
        """Process a textbook PDF into structured documents"""
        logger.info(f"Processing textbook: {pdf_path}")
        
        # Extract structured content
        content = self.extract_text_with_structure(pdf_path)
        
        if not content['full_text']:
            logger.warning(f"No text extracted from {pdf_path}")
            return []
        
        # Determine chapter information
        chapter_info = content.get('chapter_info')
        if not chapter_info:
            # Try to extract from content
            for line in content['full_text'].split('\n')[:10]:  # Check first 10 lines
                for pattern in self.chapter_patterns:
                    match = re.search(pattern, line.strip())
                    if match:
                        try:
                            chapter_info = {
                                'number': int(match.group(1)),
                                'title': match.group(2).strip()
                            }
                            break
                        except ValueError:
                            continue
                if chapter_info:
                    break
        
        # Get chapter metadata
        chapter_metadata = {}
        if chapter_info:
            chapter_metadata = get_chapter_metadata(grade, subject, chapter_info['number'])
            if not chapter_metadata:
                chapter_metadata = {
                    'grade': grade.value,
                    'subject': subject.value,
                    'chapter_number': chapter_info['number'],
                    'chapter_title': chapter_info['title'],
                    'topics': [],
                    'learning_objectives': [],
                    'difficulty_level': 'medium'
                }
        
        # Create base metadata
        base_metadata = {
            'source': pdf_path,
            'file_name': Path(pdf_path).name,
            'content_type': 'textbook',
            'educational_level': grade.value,
            'subject': subject.value,
            **chapter_metadata
        }
        
        # Split text into educationally meaningful chunks
        documents = []
        
        # Process by pages for better context
        for page_info in content['pages']:
            page_text = page_info['text']
            if not page_text.strip():
                continue
            
            # Create document for the page
            page_doc = Document(
                page_content=page_text,
                metadata={
                    **base_metadata,
                    'page_number': page_info['page_number'],
                    'chunk_type': 'page'
                }
            )
            
            # Split page into smaller chunks for better retrieval
            page_chunks = self.text_processor.process_documents(
                [page_doc],
                split_method="recursive",
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap
            )
            
            # Add chunk-specific metadata
            for i, chunk in enumerate(page_chunks):
                chunk.metadata.update({
                    'chunk_type': 'concept',
                    'chunk_index': i,
                    'page_chunk_id': f"p{page_info['page_number']}_c{i}"
                })
                
                # Try to identify the type of content in the chunk
                chunk_type = self._classify_chunk_content(chunk.page_content)
                chunk.metadata['content_category'] = chunk_type
                
            documents.extend(page_chunks)
        
        # Add special documents for exercises
        for exercise in content['exercises']:
            if exercise['title']:
                exercise_doc = Document(
                    page_content=f"Exercise: {exercise['title']}",
                    metadata={
                        **base_metadata,
                        'content_category': 'exercise',
                        'chunk_type': 'exercise_header',
                        'exercise_title': exercise['title']
                    }
                )
                documents.append(exercise_doc)
        
        logger.info(f"Created {len(documents)} educational documents from {pdf_path}")
        return documents
    
    def _classify_chunk_content(self, text: str) -> str:
        """Classify the type of educational content"""
        text_lower = text.lower()
        
        # Check for different types of educational content
        if any(keyword in text_lower for keyword in ['example', 'solve', 'solution', 'answer']):
            return 'example'
        elif any(keyword in text_lower for keyword in ['definition', 'define', 'meaning', 'what is']):
            return 'definition'
        elif any(keyword in text_lower for keyword in ['formula', 'rule', 'property', 'theorem']):
            return 'formula'
        elif any(keyword in text_lower for keyword in ['exercise', 'practice', 'question', 'problem']):
            return 'exercise'
        elif any(keyword in text_lower for keyword in ['remember', 'note', 'important', 'tip']):
            return 'note'
        else:
            return 'concept'
    
    def process_subject_directory(self, directory_path: str, grade: Grade, subject: Subject) -> List[Document]:
        """Process all PDFs in a subject directory"""
        directory = Path(directory_path)
        if not directory.exists():
            logger.error(f"Directory does not exist: {directory_path}")
            return []
        
        all_documents = []
        pdf_files = list(directory.glob("*.pdf"))
        
        logger.info(f"Found {len(pdf_files)} PDF files in {directory_path}")
        
        for pdf_file in sorted(pdf_files):  # Sort to maintain chapter order
            documents = self.process_textbook_pdf(str(pdf_file), grade, subject)
            all_documents.extend(documents)
        
        logger.info(f"Processed {len(all_documents)} total documents from {directory_path}")
        return all_documents


if __name__ == "__main__":
    # Example usage
    processor = EducationalTextbookProcessor()
    
    # Process Class 6 Science directory
    docs = processor.process_subject_directory(
        "D:/cheekofinal/RAG/Class-6-science",
        Grade.CLASS_6,
        Subject.SCIENCE
    )
    
    print(f"Processed {len(docs)} documents")
    
    # Show sample document
    if docs:
        sample_doc = docs[0]
        print("\nSample document:")
        print(f"Content: {sample_doc.page_content[:200]}...")
        print(f"Metadata: {sample_doc.metadata}")