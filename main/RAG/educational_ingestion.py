import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from langchain_core.documents import Document
from dotenv import load_dotenv

from qdrant_client_setup import QdrantManager
from embedding_manager import EmbeddingManager
from educational_processor import EducationalTextbookProcessor
from educational_config import Grade, Subject, get_collection_name, get_subject_config, CURRICULUM

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()


class EducationalIngestionPipeline:
    def __init__(self, embedding_provider: str = "huggingface"):
        self.qdrant_manager = QdrantManager()
        self.embedding_manager = EmbeddingManager(provider=embedding_provider)
        self.textbook_processor = EducationalTextbookProcessor()
        
        # Educational-specific settings
        self.batch_size = int(os.getenv("EDU_BATCH_SIZE", "50"))
    
    def setup_subject_collection(self, grade: Grade, subject: Subject, recreate: bool = False) -> str:
        """Setup collection for a specific grade and subject"""
        collection_name = get_collection_name(grade, subject)
        
        if recreate:
            self.qdrant_manager.delete_collection(collection_name)
            self.qdrant_manager.create_collection(
                collection_name=collection_name,
                vector_size=self.embedding_manager.get_embedding_dimension()
            )
        else:
            self.qdrant_manager.ensure_collection_exists(
                collection_name=collection_name,
                vector_size=self.embedding_manager.get_embedding_dimension()
            )
        
        logger.info(f"Collection '{collection_name}' ready for {grade.value} {subject.value}")
        return collection_name
    
    def ingest_subject_textbooks(self, 
                               textbook_directory: str,
                               grade: Grade,
                               subject: Subject,
                               recreate_collection: bool = False) -> Dict[str, Any]:
        """Ingest all textbooks for a subject"""
        
        logger.info(f"Starting ingestion for {grade.value} {subject.value}")
        
        # Setup collection
        collection_name = self.setup_subject_collection(grade, subject, recreate_collection)
        
        # Process textbooks
        documents = self.textbook_processor.process_subject_directory(
            textbook_directory, grade, subject
        )
        
        if not documents:
            logger.warning(f"No documents processed from {textbook_directory}")
            return {
                "success": False,
                "error": "No documents processed",
                "collection_name": collection_name
            }
        
        # Generate embeddings
        logger.info(f"Generating embeddings for {len(documents)} documents...")
        embeddings = self.embedding_manager.batch_embed_documents(
            documents, 
            batch_size=self.batch_size
        )
        
        # Prepare points for Qdrant
        points = self._prepare_educational_points(documents, embeddings)
        
        # Upload to Qdrant
        logger.info(f"Uploading {len(points)} points to collection '{collection_name}'...")
        for i in range(0, len(points), self.batch_size):
            batch_points = points[i:i + self.batch_size]
            self.qdrant_manager.upsert_points(batch_points, collection_name)
            logger.info(f"Uploaded batch {i//self.batch_size + 1}/{(len(points) + self.batch_size - 1)//self.batch_size}")
        
        # Generate statistics
        stats = self._generate_ingestion_stats(documents, collection_name)
        
        logger.info(f"Successfully ingested {grade.value} {subject.value} textbooks")
        return stats
    
    def _prepare_educational_points(self, documents: List[Document], embeddings: List[List[float]]):
        """Prepare points with educational-specific metadata"""
        points = []
        
        for doc, embedding in zip(documents, embeddings):
            # Enhanced payload for educational content
            payload = {
                'text': doc.page_content,
                'grade': doc.metadata.get('grade'),
                'subject': doc.metadata.get('subject'),
                'chapter_number': doc.metadata.get('chapter_number'),
                'chapter_title': doc.metadata.get('chapter_title'),
                'page_number': doc.metadata.get('page_number'),
                'content_category': doc.metadata.get('content_category', 'concept'),
                'chunk_type': doc.metadata.get('chunk_type', 'concept'),
                'topics': doc.metadata.get('topics', []),
                'learning_objectives': doc.metadata.get('learning_objectives', []),
                'difficulty_level': doc.metadata.get('difficulty_level', 'medium'),
                'source': doc.metadata.get('source'),
                'file_name': doc.metadata.get('file_name')
            }
            
            # Generate unique ID for educational content (using UUID)
            import uuid
            point_id = str(uuid.uuid4())
            
            # Add readable identifier to payload for searching
            payload['readable_id'] = f"{doc.metadata.get('grade', 'unknown')}_{doc.metadata.get('subject', 'unknown')}_{doc.metadata.get('chapter_number', 0)}_{doc.metadata.get('page_number', 0)}_{doc.metadata.get('chunk_index', 0)}"
            
            from qdrant_client.models import PointStruct
            point = PointStruct(
                id=point_id,
                vector=embedding,
                payload=payload
            )
            points.append(point)
        
        return points
    
    def _generate_ingestion_stats(self, documents: List[Document], collection_name: str) -> Dict[str, Any]:
        """Generate comprehensive statistics for educational content"""
        stats = {
            'collection_name': collection_name,
            'total_documents': len(documents),
            'total_points_in_collection': self.qdrant_manager.get_points_count(collection_name)
        }
        
        # Analyze content types
        content_categories = {}
        chapters = set()
        pages = set()
        
        for doc in documents:
            # Content category analysis
            category = doc.metadata.get('content_category', 'unknown')
            content_categories[category] = content_categories.get(category, 0) + 1
            
            # Chapter and page analysis
            if doc.metadata.get('chapter_number'):
                chapters.add(doc.metadata['chapter_number'])
            if doc.metadata.get('page_number'):
                pages.add(doc.metadata['page_number'])
        
        stats.update({
            'content_categories': content_categories,
            'chapters_covered': sorted(list(chapters)),
            'total_chapters': len(chapters),
            'total_pages': len(pages),
            'embedding_dimension': self.embedding_manager.get_embedding_dimension()
        })
        
        return stats
    
    def ingest_single_chapter(self, 
                            pdf_path: str,
                            grade: Grade,
                            subject: Subject,
                            collection_name: Optional[str] = None) -> Dict[str, Any]:
        """Ingest a single chapter PDF"""
        
        if not collection_name:
            collection_name = get_collection_name(grade, subject)
            self.setup_subject_collection(grade, subject, recreate=False)
        
        logger.info(f"Processing single chapter: {pdf_path}")
        
        # Process the PDF
        documents = self.textbook_processor.process_textbook_pdf(pdf_path, grade, subject)
        
        if not documents:
            return {
                "success": False,
                "error": "No documents processed from PDF",
                "pdf_path": pdf_path
            }
        
        # Generate embeddings and upload
        embeddings = self.embedding_manager.batch_embed_documents(documents, self.batch_size)
        points = self._prepare_educational_points(documents, embeddings)
        
        # Upload in batches
        for i in range(0, len(points), self.batch_size):
            batch_points = points[i:i + self.batch_size]
            self.qdrant_manager.upsert_points(batch_points, collection_name)
        
        stats = self._generate_ingestion_stats(documents, collection_name)
        stats['pdf_path'] = pdf_path
        stats['success'] = True
        
        return stats
    
    def list_available_subjects(self) -> Dict[str, List[str]]:
        """List all configured subjects by grade"""
        subjects_by_grade = {}
        
        for (grade, subject) in CURRICULUM.keys():
            grade_key = grade.value
            if grade_key not in subjects_by_grade:
                subjects_by_grade[grade_key] = []
            subjects_by_grade[grade_key].append(subject.value)
        
        return subjects_by_grade
    
    def get_collection_overview(self, grade: Grade, subject: Subject) -> Dict[str, Any]:
        """Get overview of what's in a collection"""
        collection_name = get_collection_name(grade, subject)
        
        try:
            collection_info = self.qdrant_manager.get_collection_info(collection_name)
            if not collection_info:
                return {"error": f"Collection {collection_name} not found"}
            
            # Get sample points to analyze content
            sample_results = self.qdrant_manager.client.scroll(
                collection_name=collection_name,
                limit=100,
                with_payload=True
            )[0]
            
            overview = {
                'collection_name': collection_name,
                'total_points': collection_info.points_count,
                'vector_dimension': collection_info.config.params.vectors.size,
                'chapters': set(),
                'content_categories': {},
                'files': set()
            }
            
            for point in sample_results:
                payload = point.payload
                
                if payload.get('chapter_number'):
                    overview['chapters'].add(payload['chapter_number'])
                
                category = payload.get('content_category', 'unknown')
                overview['content_categories'][category] = overview['content_categories'].get(category, 0) + 1
                
                if payload.get('file_name'):
                    overview['files'].add(payload['file_name'])
            
            overview['chapters'] = sorted(list(overview['chapters']))
            overview['files'] = sorted(list(overview['files']))
            
            return overview
            
        except Exception as e:
            return {"error": str(e)}


if __name__ == "__main__":
    # Example usage
    pipeline = EducationalIngestionPipeline()
    
    # List available subjects
    subjects = pipeline.list_available_subjects()
    print("Available subjects:", subjects)
    
    # Ingest Class 6 Mathematics (modify path as needed)
    textbook_dir = "D:/cheekofinal/RAG/Class-6-mathematics"
    if Path(textbook_dir).exists():
        result = pipeline.ingest_subject_textbooks(
            textbook_dir,
            Grade.CLASS_6,
            Subject.MATHEMATICS,
            recreate_collection=True
        )
        print("Ingestion result:", result)
    else:
        print(f"Directory not found: {textbook_dir}")
    
    # Get collection overview
    overview = pipeline.get_collection_overview(Grade.CLASS_6, Subject.MATHEMATICS)
    print("Collection overview:", overview)