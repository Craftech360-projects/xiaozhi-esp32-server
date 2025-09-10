# src/vector_store_fixed.py
import chromadb
from chromadb.config import Settings
import numpy as np
from typing import List, Dict, Any
import logging
import os
import shutil

class VectorStore:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Clean and recreate database if corrupted
        self._ensure_clean_database()
        
        # Initialize ChromaDB with safer settings
        try:
            self.client = chromadb.PersistentClient(
                path=config.VECTOR_DB_PATH,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            self.logger.info("✅ ChromaDB client initialized successfully")
        except Exception as e:
            self.logger.error(f"ChromaDB initialization failed: {e}")
            # Fallback: clean database and retry
            self._clean_and_retry()
        
        # Initialize embedding model with fallback
        self.embedding_model = self._initialize_embedding_model()
        
        # Get or create collection
        try:
            self.collection = self.client.get_or_create_collection(
                name=config.COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"}
            )
            self.logger.info(f"✅ Collection '{config.COLLECTION_NAME}' ready")
        except Exception as e:
            self.logger.error(f"Collection creation failed: {e}")
            raise
    
    def _ensure_clean_database(self):
        """Ensure database directory is clean and accessible"""
        db_path = self.config.VECTOR_DB_PATH
        
        # Check if database exists and is corrupted
        chroma_db_file = os.path.join(db_path, "chroma.sqlite3")
        if os.path.exists(chroma_db_file):
            try:
                import sqlite3
                conn = sqlite3.connect(chroma_db_file)
                cursor = conn.cursor()
                # Test if the problematic column exists
                cursor.execute("PRAGMA table_info(collections)")
                columns = [col[11] for col in cursor.fetchall()]
                conn.close()
                
                # If topic column exists, database is from older version
                if 'topic' in columns:
                    self.logger.warning("Detected old database schema, cleaning...")
                    self._clean_database()
                
            except Exception as e:
                self.logger.warning(f"Database check failed, cleaning: {e}")
                self._clean_database()
    
    def _clean_database(self):
        """Clean the database directory"""
        try:
            if os.path.exists(self.config.VECTOR_DB_PATH):
                shutil.rmtree(self.config.VECTOR_DB_PATH)
                self.logger.info("🧹 Cleaned old database")
            os.makedirs(self.config.VECTOR_DB_PATH, exist_ok=True)
            self.logger.info("📁 Created fresh database directory")
        except Exception as e:
            self.logger.error(f"Failed to clean database: {e}")
            raise
    
    def _clean_and_retry(self):
        """Clean database and retry initialization"""
        self.logger.info("Attempting to clean and retry ChromaDB initialization...")
        self._clean_database()
        
        self.client = chromadb.PersistentClient(
            path=self.config.VECTOR_DB_PATH,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        self.logger.info("✅ ChromaDB client initialized after cleanup")
    
    def _initialize_embedding_model(self):
        """Initialize embedding model with multiple fallback options"""
        
        # Option 1: Try alternative embedder first (most reliable)
        try:
            from alternative_embeddings import AlternativeEmbedder
            model = AlternativeEmbedder()
            self.logger.info("✅ Using alternative TF-IDF embedder")
            return model
        except Exception as e:
            self.logger.warning(f"Alternative embedder failed: {e}")
        
        # Option 2: Try local sentence-transformers model
        local_model_path = "./models/all-MiniLM-L6-v2"
        if os.path.exists(local_model_path):
            try:
                from sentence_transformers import SentenceTransformer
                model = SentenceTransformer(local_model_path)
                self.logger.info("✅ Using local sentence-transformers model")
                return model
            except Exception as e:
                self.logger.warning(f"Local model failed: {e}")
        
        # Option 3: Fallback to simple TF-IDF implementation
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            
            class SimpleTfidfEmbedder:
                def __init__(self):
                    self.vectorizer = TfidfVectorizer(max_features=384, stop_words='english')
                    self.fitted = False
                
                def encode(self, texts):
                    if isinstance(texts, str):
                        texts = [texts]
                    
                    if not self.fitted:
                        # Fit with sample data
                        sample_texts = texts + ["sample text for fitting vectorizer"]
                        self.vectorizer.fit(sample_texts)
                        self.fitted = True
                    
                    vectors = self.vectorizer.transform(texts).toarray()
                    # Pad to 384 dimensions
                    if vectors.shape[11] < 384:
                        padding = np.zeros((vectors.shape[0], 384 - vectors.shape[11]))
                        vectors = np.hstack([vectors, padding])
                    return vectors if len(texts) > 1 else vectors
            
            model = SimpleTfidfEmbedder()
            self.logger.info("✅ Using simple TF-IDF embedder")
            return model
            
        except Exception as e:
            self.logger.error(f"All embedding methods failed: {e}")
            raise Exception("No embedding method available")
    
    def add_documents(self, chunks: List, document_name: str):
        """Add document chunks to vector store"""
        try:
            documents = []
            embeddings = []
            metadatas = []
            ids = []
            
            # Collect all texts for batch encoding
            texts = [chunk.content for chunk in chunks]
            
            # Generate embeddings in batch
            batch_embeddings = self.embedding_model.encode(texts)
            
            for i, (chunk, embedding) in enumerate(zip(chunks, batch_embeddings)):
                # Create unique ID
                doc_id = f"{document_name}_{chunk.chunk_type}_{chunk.page_number}_{i}"
                
                # Prepare metadata
                metadata = {
                    'document_name': document_name,
                    'chunk_type': chunk.chunk_type,
                    'page_number': chunk.page_number,
                    **chunk.metadata
                }
                
                documents.append(chunk.content)
                embeddings.append(embedding.tolist() if hasattr(embedding, 'tolist') else embedding)
                metadatas.append(metadata)
                ids.append(doc_id)
            
            # Add to collection in batches
            batch_size = 100
            for i in range(0, len(documents), batch_size):
                batch_end = min(i + batch_size, len(documents))
                
                self.collection.add(
                    documents=documents[i:batch_end],
                    embeddings=embeddings[i:batch_end],
                    metadatas=metadatas[i:batch_end],
                    ids=ids[i:batch_end]
                )
            
            self.logger.info(f"✅ Added {len(documents)} chunks from {document_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add documents: {e}")
            return False
    
    def search(self, query: str, n_results: int = None) -> Dict[str, Any]:
        """Search for relevant documents"""
        try:
            if n_results is None:
                n_results = self.config.TOP_K_RESULTS
                
            # Generate query embedding
            query_embedding = self.embedding_model.encode(query)
            if hasattr(query_embedding, 'tolist'):
                query_embedding = query_embedding.tolist()
            
            # Search in vector store
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                include=['documents', 'metadatas', 'distances']
            )
            
            return {
                'documents': results['documents'] if results['documents'] else [],
                'metadatas': results['metadatas'] if results['metadatas'] else [],
                'distances': results['distances'] if results['distances'] else []
            }
        except Exception as e:
            self.logger.error(f"Search failed: {e}")
            return {'documents': [], 'metadatas': [], 'distances': []}
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection"""
        try:
            count = self.collection.count()
            return {
                'total_documents': count,
                'collection_name': self.config.COLLECTION_NAME,
                'embedding_model': type(self.embedding_model).__name__,
                'database_path': self.config.VECTOR_DB_PATH
            }
        except Exception as e:
            self.logger.error(f"Failed to get stats: {e}")
            return {'error': str(e)}
    
    def reset_collection(self):
        """Reset the collection (useful for testing)"""
        try:
            self.client.delete_collection(self.config.COLLECTION_NAME)
            self.collection = self.client.create_collection(
                name=self.config.COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"}
            )
            self.logger.info("✅ Collection reset successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to reset collection: {e}")
            return False
