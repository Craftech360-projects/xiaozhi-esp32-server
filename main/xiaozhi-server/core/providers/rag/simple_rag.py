import os
import hashlib
from typing import List, Dict, Any
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from .base import RAGProviderBase, logger

TAG = __name__


class SimpleRAGProvider(RAGProviderBase):
    """Simple RAG provider using ChromaDB and Sentence Transformers"""
    
    def __init__(self, config: dict = None):
        super().__init__(config)
        
        # Get configuration
        self.db_path = config.get('db_path', './rag_db') if config else './rag_db'
        self.collection_name = config.get('collection_name', 'textbooks') if config else 'textbooks'
        self.model_name = config.get('model_name', 'paraphrase-multilingual-MiniLM-L12-v2') if config else 'paraphrase-multilingual-MiniLM-L12-v2'
        
        try:
            # Initialize ChromaDB client with persistent storage
            self.client = chromadb.PersistentClient(
                path=self.db_path,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "Textbook content for educational Q&A"}
            )
            
            # Initialize sentence transformer model
            logger.bind(tag=TAG).info(f"Loading embedding model: {self.model_name}")
            self.embedding_model = SentenceTransformer(self.model_name)
            
            logger.bind(tag=TAG).info(f"Successfully initialized SimpleRAGProvider with collection: {self.collection_name}")
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"Failed to initialize SimpleRAGProvider: {str(e)}")
            raise
    
    def _generate_id(self, text: str, metadata: Dict[str, Any]) -> str:
        """Generate a unique ID for a document"""
        content = f"{text}_{metadata.get('page', 0)}_{metadata.get('source', '')}"
        return f"doc_{hashlib.md5(content.encode()).hexdigest()[:16]}"
    
    def add_document(self, text: str, metadata: Dict[str, Any]) -> bool:
        """Add a single document to the RAG database"""
        try:
            # Skip empty or very short texts
            if not text or len(text.strip()) < 10:
                return True
            
            # Generate embedding
            embedding = self.embedding_model.encode([text])
            
            # Generate unique ID
            doc_id = self._generate_id(text, metadata)
            
            # Add to collection
            self.collection.add(
                documents=[text],
                embeddings=embedding.tolist(),
                metadatas=[metadata],
                ids=[doc_id]
            )
            
            logger.bind(tag=TAG).debug(f"Added document with ID: {doc_id}")
            return True
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"Failed to add document: {str(e)}")
            return False
    
    def add_documents(self, texts: List[str], metadatas: List[Dict[str, Any]]) -> bool:
        """Add multiple documents to the RAG database"""
        try:
            # Filter out empty texts
            valid_docs = [(text, meta) for text, meta in zip(texts, metadatas) 
                         if text and len(text.strip()) >= 10]
            
            if not valid_docs:
                return True
            
            texts, metadatas = zip(*valid_docs)
            texts = list(texts)
            metadatas = list(metadatas)
            
            # Generate embeddings
            embeddings = self.embedding_model.encode(texts)
            
            # Generate unique IDs
            ids = [self._generate_id(text, meta) for text, meta in zip(texts, metadatas)]
            
            # Add to collection
            self.collection.add(
                documents=texts,
                embeddings=embeddings.tolist(),
                metadatas=metadatas,
                ids=ids
            )
            
            logger.bind(tag=TAG).info(f"Added {len(texts)} documents to collection")
            return True
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"Failed to add documents: {str(e)}")
            return False
    
    def search(self, query: str, top_k: int = 5, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Search for relevant documents"""
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query])
            
            # Prepare where clause for filtering
            where_clause = None
            if filters:
                # ChromaDB requires specific format for multiple filters
                conditions = []
                for key, value in filters.items():
                    if value is not None:
                        conditions.append({key: {"$eq": value}})
                
                if len(conditions) == 1:
                    where_clause = conditions[0]
                elif len(conditions) > 1:
                    where_clause = {"$and": conditions}
                else:
                    where_clause = None
            
            # Search in collection
            results = self.collection.query(
                query_embeddings=query_embedding.tolist(),
                n_results=min(top_k, self.collection.count()),
                where=where_clause
            )
            
            logger.bind(tag=TAG).debug(f"Search query: '{query}' returned {len(results['documents'][0])} results")
            
            return {
                'documents': results['documents'][0] if results['documents'] else [],
                'metadatas': results['metadatas'][0] if results['metadatas'] else [],
                'distances': results['distances'][0] if results['distances'] else [],
                'ids': results['ids'][0] if results['ids'] else []
            }
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"Search failed: {str(e)}")
            return {
                'documents': [],
                'metadatas': [],
                'distances': [],
                'ids': []
            }
    
    def delete_collection(self, collection_name: str = None) -> bool:
        """Delete a collection or reset the current collection"""
        try:
            if collection_name and collection_name != self.collection_name:
                self.client.delete_collection(name=collection_name)
                logger.bind(tag=TAG).info(f"Deleted collection: {collection_name}")
            else:
                # Reset current collection
                self.collection = self.client.get_or_create_collection(
                    name=self.collection_name,
                    metadata={"description": "Textbook content for educational Q&A"}
                )
                logger.bind(tag=TAG).info(f"Reset collection: {self.collection_name}")
            
            return True
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"Failed to delete collection: {str(e)}")
            return False
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the current collection"""
        try:
            count = self.collection.count()
            
            return {
                'name': self.collection_name,
                'count': count,
                'db_path': self.db_path,
                'model': self.model_name,
                'metadata': self.collection.metadata
            }
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"Failed to get collection info: {str(e)}")
            return {
                'name': self.collection_name,
                'count': 0,
                'error': str(e)
            }