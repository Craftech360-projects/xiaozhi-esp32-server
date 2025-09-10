# src/vector_store_windows_safe.py
import chromadb
from chromadb.config import Settings
import numpy as np
from typing import List, Dict, Any
import logging
import os
import time
import tempfile

class VectorStore:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Use a Windows-safe database path
        self.db_path = self._get_safe_db_path()
        
        # Initialize ChromaDB with Windows-safe settings
        self.client = self._initialize_client()
        
        # Initialize embedding model
        self.embedding_model = self._initialize_embedding_model()
        
        # Get or create collection
        self.collection = self._get_collection()
        
    def _get_safe_db_path(self):
        """Get a Windows-safe database path"""
        # Use a unique temporary directory to avoid conflicts
        import tempfile
        temp_dir = tempfile.gettempdir()
        safe_path = os.path.join(temp_dir, "rag_chroma_db")
        
        # Ensure directory exists
        os.makedirs(safe_path, exist_ok=True)
        
        self.logger.info(f"Using database path: {safe_path}")
        return safe_path
    
    def _initialize_client(self):
        """Initialize ChromaDB client with retry logic"""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                client = chromadb.PersistentClient(
                    path=self.db_path,
                    settings=Settings(
                        anonymized_telemetry=False,
                        allow_reset=True
                    )
                )
                self.logger.info("✅ ChromaDB client initialized successfully")
                return client
                
            except Exception as e:
                self.logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    # Last attempt - use in-memory database
                    self.logger.info("Falling back to in-memory database")
                    return chromadb.Client()
                
                # Wait and retry
                time.sleep(1)
    
    def _initialize_embedding_model(self):
        """Initialize embedding model (TF-IDF fallback)"""
        try:
            # Simple, reliable TF-IDF embedder
            from sklearn.feature_extraction.text import TfidfVectorizer
            
            class SafeEmbedder:
                def __init__(self):
                    self.vectorizer = TfidfVectorizer(
                        max_features=384,
                        stop_words='english',
                        ngram_range=(1, 2)
                    )
                    self.fitted = False
                
                def encode(self, texts):
                    if isinstance(texts, str):
                        texts = [texts]
                    
                    if not self.fitted:
                        # Fit with the texts plus some sample data
                        fit_texts = texts + [
                            "sample document text",
                            "machine learning artificial intelligence",
                            "document processing analysis"
                        ]
                        self.vectorizer.fit(fit_texts)
                        self.fitted = True
                    
                    # Transform to vectors
                    vectors = self.vectorizer.transform(texts).toarray()
                    
                    # Ensure 384 dimensions
                    if vectors.shape[1] < 384:
                        padding = np.zeros((vectors.shape[0], 384 - vectors.shape[1]))
                        vectors = np.hstack([vectors, padding])
                    elif vectors.shape[1] > 384:
                        vectors = vectors[:, :384]
                    
                    return vectors if len(texts) > 1 else vectors[0]
            
            embedder = SafeEmbedder()
            self.logger.info("✅ Using TF-IDF embedder")
            return embedder
            
        except Exception as e:
            self.logger.error(f"Failed to initialize embedder: {e}")
            raise
    
    def _get_collection(self):
        """Get or create collection with safe naming"""
        try:
            collection_name = f"docs_{int(time.time())}"  # Unique name
            collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            self.logger.info(f"✅ Collection '{collection_name}' ready")
            return collection
            
        except Exception as e:
            self.logger.error(f"Collection creation failed: {e}")
            # Fallback: create with basic settings
            collection = self.client.create_collection(name="fallback_collection")
            return collection
    
    def add_documents(self, chunks: List, document_name: str):
        """Add document chunks to vector store"""
        try:
            documents = []
            embeddings = []
            metadatas = []
            ids = []
            
            # Process chunks in smaller batches
            for i, chunk in enumerate(chunks):
                # Generate embedding
                embedding = self.embedding_model.encode(chunk.content)
                
                # Create unique ID
                doc_id = f"{document_name}_{i}_{int(time.time())}"
                
                # Prepare metadata
                metadata = {
                    'document_name': document_name,
                    'chunk_type': getattr(chunk, 'chunk_type', 'text'),
                    'page_number': getattr(chunk, 'page_number', 1)
                }
                
                documents.append(chunk.content)
                embeddings.append(embedding.tolist() if hasattr(embedding, 'tolist') else list(embedding))
                metadatas.append(metadata)
                ids.append(doc_id)
            
            # Add to collection
            if documents:  # Only add if we have documents
                self.collection.add(
                    documents=documents,
                    embeddings=embeddings,
                    metadatas=metadatas,
                    ids=ids
                )
            
            self.logger.info(f"✅ Added {len(documents)} chunks from {document_name}")
            return {'success': True, 'count': len(documents)}
            
        except Exception as e:
            self.logger.error(f"Failed to add documents: {e}")
            return {'success': False, 'error': str(e)}
    
    def search(self, query: str, n_results: int = 5) -> Dict[str, Any]:
        """Search for relevant documents"""
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode(query)
            if hasattr(query_embedding, 'tolist'):
                query_embedding = query_embedding.tolist()
            
            # Search
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                include=['documents', 'metadatas', 'distances']
            )
            
            return {
                'documents': results['documents'][0] if results['documents'] else [],
                'metadatas': results['metadatas'][0] if results['metadatas'] else [],
                'distances': results['distances'][0] if results['distances'] else []
            }
            
        except Exception as e:
            self.logger.error(f"Search failed: {e}")
            return {'documents': [], 'metadatas': [], 'distances': []}
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        try:
            count = self.collection.count()
            return {
                'total_documents': count,
                'database_path': self.db_path,
                'embedding_model': 'TF-IDF'
            }
        except Exception as e:
            return {'error': str(e)}
