import os
import logging
from typing import List, Optional, Dict, Any
from pathlib import Path
import uuid
from qdrant_client.models import PointStruct
from langchain_core.documents import Document
from dotenv import load_dotenv

from qdrant_client_setup import QdrantManager
from document_loader import DocumentLoaderManager
from text_processor import TextProcessor
from embedding_manager import EmbeddingManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()


class IngestionPipeline:
    def __init__(self, 
                 collection_name: Optional[str] = None,
                 embedding_provider: str = "huggingface",
                 recreate_collection: bool = False):
        
        self.qdrant_manager = QdrantManager()
        self.document_loader = DocumentLoaderManager()
        self.text_processor = TextProcessor()
        self.embedding_manager = EmbeddingManager(provider=embedding_provider)
        
        self.collection_name = collection_name or os.getenv("COLLECTION_NAME", "rag_collection")
        
        if recreate_collection:
            self.qdrant_manager.delete_collection(self.collection_name)
            self.qdrant_manager.create_collection(
                collection_name=self.collection_name,
                vector_size=self.embedding_manager.get_embedding_dimension()
            )
        else:
            self.qdrant_manager.ensure_collection_exists(
                collection_name=self.collection_name,
                vector_size=self.embedding_manager.get_embedding_dimension()
            )
    
    def prepare_points(self, documents: List[Document], embeddings: List[List[float]]) -> List[PointStruct]:
        points = []
        
        for doc, embedding in zip(documents, embeddings):
            point_id = str(uuid.uuid4())
            
            payload = {
                "text": doc.page_content,
                "metadata": doc.metadata,
                "source": doc.metadata.get("source", "unknown"),
                "chunk_id": doc.metadata.get("chunk_id", 0),
                "chunk_size": len(doc.page_content)
            }
            
            point = PointStruct(
                id=point_id,
                vector=embedding,
                payload=payload
            )
            points.append(point)
        
        return points
    
    def ingest_documents(self, 
                        documents: List[Document],
                        batch_size: int = 100,
                        split_method: str = "recursive",
                        clean_text: bool = True) -> Dict[str, Any]:
        
        processed_documents = self.text_processor.process_documents(
            documents,
            split_method=split_method,
            clean=clean_text
        )
        
        processed_documents = self.text_processor.deduplicate_documents(processed_documents)
        
        logger.info(f"Generating embeddings for {len(processed_documents)} document chunks...")
        embeddings = self.embedding_manager.batch_embed_documents(
            processed_documents,
            batch_size=batch_size
        )
        
        points = self.prepare_points(processed_documents, embeddings)
        
        logger.info(f"Uploading {len(points)} points to Qdrant collection '{self.collection_name}'...")
        for i in range(0, len(points), batch_size):
            batch_points = points[i:i + batch_size]
            self.qdrant_manager.upsert_points(batch_points, self.collection_name)
            logger.info(f"Uploaded batch {i//batch_size + 1}/{(len(points) + batch_size - 1)//batch_size}")
        
        result = {
            "collection_name": self.collection_name,
            "documents_processed": len(documents),
            "chunks_created": len(processed_documents),
            "points_uploaded": len(points),
            "embedding_dimension": self.embedding_manager.get_embedding_dimension(),
            "total_points_in_collection": self.qdrant_manager.get_points_count(self.collection_name)
        }
        
        return result
    
    def ingest_from_file(self, file_path: str, **kwargs) -> Dict[str, Any]:
        logger.info(f"Loading document from {file_path}")
        
        path = Path(file_path)
        if path.suffix == '.pdf':
            documents = self.document_loader.load_pdf_file(file_path)
        elif path.suffix == '.txt':
            documents = self.document_loader.load_text_file(file_path)
        elif path.suffix == '.csv':
            documents = self.document_loader.load_csv_file(file_path)
        elif path.suffix == '.json':
            documents = self.document_loader.load_json_file(file_path)
        else:
            documents = self.document_loader.load_unstructured(file_path)
        
        if not documents:
            logger.error(f"No documents loaded from {file_path}")
            return {"error": "No documents loaded"}
        
        return self.ingest_documents(documents, **kwargs)
    
    def ingest_from_directory(self, 
                            directory_path: str,
                            glob_pattern: str = "**/*.txt",
                            **kwargs) -> Dict[str, Any]:
        logger.info(f"Loading documents from directory {directory_path}")
        
        documents = self.document_loader.load_directory(
            directory_path,
            glob_pattern=glob_pattern
        )
        
        if not documents:
            logger.error(f"No documents loaded from {directory_path}")
            return {"error": "No documents loaded"}
        
        return self.ingest_documents(documents, **kwargs)
    
    def ingest_from_s3(self,
                      bucket: str,
                      prefix: str = "",
                      **kwargs) -> Dict[str, Any]:
        logger.info(f"Loading documents from S3 bucket {bucket}/{prefix}")
        
        documents = self.document_loader.load_from_s3(bucket, prefix)
        
        if not documents:
            logger.error(f"No documents loaded from S3")
            return {"error": "No documents loaded"}
        
        return self.ingest_documents(documents, **kwargs)
    
    def ingest_from_multiple_files(self,
                                 file_paths: List[str],
                                 **kwargs) -> Dict[str, Any]:
        logger.info(f"Loading documents from {len(file_paths)} files")
        
        documents = self.document_loader.load_multiple_files(file_paths)
        
        if not documents:
            logger.error("No documents loaded from files")
            return {"error": "No documents loaded"}
        
        return self.ingest_documents(documents, **kwargs)


if __name__ == "__main__":
    pipeline = IngestionPipeline(recreate_collection=True)
    
    sample_docs = [
        Document(
            page_content="Qdrant is a vector database optimized for storing and searching high-dimensional vectors.",
            metadata={"source": "qdrant_docs.txt", "type": "documentation"}
        ),
        Document(
            page_content="LangChain is a framework for developing applications powered by language models.",
            metadata={"source": "langchain_docs.txt", "type": "documentation"}
        ),
        Document(
            page_content="RAG (Retrieval-Augmented Generation) combines retrieval and generation for better AI responses.",
            metadata={"source": "rag_overview.txt", "type": "concepts"}
        )
    ]
    
    result = pipeline.ingest_documents(sample_docs)
    print(f"Ingestion result: {result}")