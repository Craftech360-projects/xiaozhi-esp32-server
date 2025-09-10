"""
Document Ingestion Service for Educational RAG System
Handles document processing, embedding generation, and vector storage
Integrates with existing educational RAG memory provider
"""

import asyncio
import os
from typing import List, Dict, Any, Optional
from pathlib import Path

# Core imports
from config.logger import setup_logging
from core.utils.enhanced_document_processor import EnhancedDocumentProcessor, DocumentChunk

# Vector database and embedding imports
try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models
    from qdrant_client.http.models import PointStruct, VectorParams, Filter, FieldCondition, MatchValue
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

TAG = __name__
logger = setup_logging()


class DocumentIngestionService:
    """Service for ingesting documents into the educational RAG system"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the document ingestion service"""
        self.config = config
        
        # Initialize document processor
        self.document_processor = EnhancedDocumentProcessor(
            chunk_size=config.get('chunk_size', 800),
            chunk_overlap=config.get('chunk_overlap', 100)
        )
        
        # Initialize vector database client
        self.qdrant_client = None
        self._initialize_vector_db()
        
        # Initialize embedding model
        self.embedding_model = None
        self._initialize_embedding_model()
        
        # Batch processing settings
        self.batch_size = config.get('batch_size', 50)
        
        logger.bind(tag=TAG).info("[DOC-INGESTION] Document ingestion service initialized")
    
    def _initialize_vector_db(self):
        """Initialize Qdrant vector database client"""
        try:
            if not QDRANT_AVAILABLE:
                logger.bind(tag=TAG).warning("[DOC-INGESTION] Qdrant not available, using fallback storage")
                return
            
            qdrant_url = self.config.get('qdrant_url')
            qdrant_api_key = self.config.get('qdrant_api_key')
            
            logger.bind(tag=TAG).info(f"[DOC-INGESTION] Qdrant URL: {qdrant_url}")
            logger.bind(tag=TAG).info(f"[DOC-INGESTION] Qdrant API key present: {bool(qdrant_api_key)}")
            
            if qdrant_url and qdrant_api_key:
                # Cloud Qdrant
                self.qdrant_client = QdrantClient(
                    url=qdrant_url,
                    api_key=qdrant_api_key,
                    timeout=30
                )
                logger.bind(tag=TAG).info("[DOC-INGESTION] Connected to Qdrant cloud instance")
            else:
                # Local Qdrant (fallback)
                logger.bind(tag=TAG).warning("[DOC-INGESTION] Qdrant URL or API key missing, trying local instance")
                self.qdrant_client = QdrantClient(host="localhost", port=6333)
                logger.bind(tag=TAG).info("[DOC-INGESTION] Connected to local Qdrant instance")
                
        except Exception as e:
            logger.bind(tag=TAG).error(f"[DOC-INGESTION] Failed to initialize Qdrant: {e}")
            self.qdrant_client = None
    
    def _initialize_embedding_model(self):
        """Initialize embedding model with fallbacks"""
        try:
            model_name = self.config.get('embedding_model', 'sentence-transformers/all-MiniLM-L6-v2')
            
            if SENTENCE_TRANSFORMERS_AVAILABLE:
                self.embedding_model = SentenceTransformer(model_name)
                logger.bind(tag=TAG).info(f"[DOC-INGESTION] Loaded embedding model: {model_name}")
            else:
                logger.bind(tag=TAG).warning("[DOC-INGESTION] SentenceTransformers not available, using fallback embeddings")
                self._initialize_fallback_embeddings()
                
        except Exception as e:
            logger.bind(tag=TAG).error(f"[DOC-INGESTION] Failed to load embedding model: {e}")
            self._initialize_fallback_embeddings()
    
    def _initialize_fallback_embeddings(self):
        """Initialize fallback embedding method using TF-IDF"""
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            import numpy as np
            
            class TfidfEmbedder:
                def __init__(self):
                    self.vectorizer = TfidfVectorizer(max_features=384, stop_words='english')
                    self.fitted = False
                
                def encode(self, texts):
                    if isinstance(texts, str):
                        texts = [texts]
                    
                    if not self.fitted:
                        # Fit with sample data
                        sample_texts = texts + ["sample educational text for fitting vectorizer"]
                        self.vectorizer.fit(sample_texts)
                        self.fitted = True
                    
                    vectors = self.vectorizer.transform(texts).toarray()
                    # Pad to 384 dimensions if needed
                    if vectors.shape[1] < 384:
                        padding = np.zeros((vectors.shape[0], 384 - vectors.shape[1]))
                        vectors = np.hstack([vectors, padding])
                    
                    return vectors if len(texts) > 1 else vectors[0]
            
            self.embedding_model = TfidfEmbedder()
            logger.bind(tag=TAG).info("[DOC-INGESTION] Using TF-IDF fallback embeddings")
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"[DOC-INGESTION] Failed to initialize fallback embeddings: {e}")
            self.embedding_model = None
    
    async def ingest_document(self, file_path: str, grade: str = "class-6", 
                            subject: str = "mathematics", document_name: Optional[str] = None) -> Dict[str, Any]:
        """Ingest a single document"""
        try:
            logger.bind(tag=TAG).info(f"[DOC-INGESTION] Starting ingestion of: {file_path}")
            
            # Process document into chunks
            chunks = self.document_processor.process_document(file_path, grade, subject, document_name)
            
            if not chunks:
                return {
                    'success': False,
                    'error': 'No content extracted from document',
                    'file_path': file_path
                }
            
            # Generate embeddings
            embeddings = await self._generate_embeddings_batch(chunks)
            
            # Store in vector database
            collection_name = self._get_collection_name(grade, subject)
            storage_result = await self._store_chunks_with_embeddings(chunks, embeddings, collection_name)
            
            if not storage_result['success']:
                return {
                    'success': False,
                    'error': storage_result['error'],
                    'file_path': file_path
                }
            
            # Generate statistics
            stats = self.document_processor.get_processing_stats(chunks)
            stats.update({
                'file_path': file_path,
                'document_name': document_name or Path(file_path).stem,
                'collection_name': collection_name,
                'embeddings_generated': len(embeddings),
                'storage_success': True
            })
            
            logger.bind(tag=TAG).info(f"[DOC-INGESTION] Successfully ingested {file_path}: {len(chunks)} chunks")
            
            return {
                'success': True,
                'statistics': stats
            }
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"[DOC-INGESTION] Error ingesting document {file_path}: {e}")
            return {
                'success': False,
                'error': str(e),
                'file_path': file_path
            }
    
    async def ingest_documents_batch(self, file_paths: List[str], grade: str = "class-6",
                                   subject: str = "mathematics") -> Dict[str, Any]:
        """Ingest multiple documents in batch"""
        try:
            logger.bind(tag=TAG).info(f"[DOC-INGESTION] Starting batch ingestion of {len(file_paths)} documents")
            
            results = {
                'total_documents': len(file_paths),
                'successful_ingestions': 0,
                'failed_ingestions': 0,
                'total_chunks': 0,
                'errors': [],
                'document_results': []
            }
            
            for file_path in file_paths:
                try:
                    result = await self.ingest_document(file_path, grade, subject)
                    results['document_results'].append(result)
                    
                    if result['success']:
                        results['successful_ingestions'] += 1
                        results['total_chunks'] += result['statistics']['total_chunks']
                    else:
                        results['failed_ingestions'] += 1
                        results['errors'].append({
                            'file_path': file_path,
                            'error': result.get('error', 'Unknown error')
                        })
                        
                except Exception as e:
                    results['failed_ingestions'] += 1
                    results['errors'].append({
                        'file_path': file_path,
                        'error': str(e)
                    })
                    logger.bind(tag=TAG).error(f"[DOC-INGESTION] Error in batch processing {file_path}: {e}")
            
            logger.bind(tag=TAG).info(f"[DOC-INGESTION] Batch ingestion completed: {results['successful_ingestions']}/{results['total_documents']} successful")
            
            return results
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"[DOC-INGESTION] Error in batch ingestion: {e}")
            return {
                'success': False,
                'error': str(e),
                'total_documents': len(file_paths),
                'successful_ingestions': 0,
                'failed_ingestions': len(file_paths)
            }
    
    async def _generate_embeddings_batch(self, chunks: List[DocumentChunk]) -> List[List[float]]:
        """Generate embeddings for chunks in batch"""
        try:
            if not self.embedding_model:
                logger.bind(tag=TAG).error("[DOC-INGESTION] No embedding model available")
                return []
            
            texts = [chunk.content for chunk in chunks]
            logger.bind(tag=TAG).debug(f"[DOC-INGESTION] Generating embeddings for {len(texts)} chunks")
            
            # Process in batches to avoid memory issues
            all_embeddings = []
            for i in range(0, len(texts), self.batch_size):
                batch_texts = texts[i:i + self.batch_size]
                
                if hasattr(self.embedding_model, 'encode'):
                    batch_embeddings = self.embedding_model.encode(batch_texts)
                    
                    # Ensure embeddings are in the correct format
                    if hasattr(batch_embeddings, 'tolist'):
                        batch_embeddings = batch_embeddings.tolist()
                    
                    # Handle single embedding case
                    if not isinstance(batch_embeddings[0], list):
                        batch_embeddings = [batch_embeddings]
                    
                    all_embeddings.extend(batch_embeddings)
                else:
                    logger.bind(tag=TAG).error("[DOC-INGESTION] Embedding model doesn't support encode method")
                    return []
            
            logger.bind(tag=TAG).info(f"[DOC-INGESTION] Generated {len(all_embeddings)} embeddings")
            return all_embeddings
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"[DOC-INGESTION] Error generating embeddings: {e}")
            return []
    
    async def _store_chunks_with_embeddings(self, chunks: List[DocumentChunk], 
                                          embeddings: List[List[float]], 
                                          collection_name: str) -> Dict[str, Any]:
        """Store chunks with embeddings in vector database"""
        try:
            if not self.qdrant_client:
                logger.bind(tag=TAG).warning("[DOC-INGESTION] No vector database available, skipping storage")
                return {'success': False, 'error': 'No vector database available'}
            
            if len(chunks) != len(embeddings):
                return {'success': False, 'error': 'Mismatch between chunks and embeddings count'}
            
            # Ensure collection exists
            await self._ensure_collection_exists(collection_name, len(embeddings[0]) if embeddings else 384)
            
            # Ensure payload indexes exist for filtering
            await self._ensure_payload_indexes(collection_name)
            
            # Prepare points for storage
            points = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                point_id = chunk.metadata.get('unique_id', f"{collection_name}_{i}")
                
                # Prepare payload (metadata) - ensure all values are JSON serializable
                payload = {}
                for key, value in chunk.metadata.items():
                    if value is not None:
                        # Convert sets to lists, handle other non-serializable types
                        if isinstance(value, set):
                            payload[key] = list(value)
                        elif isinstance(value, (str, int, float, bool, list, dict)):
                            payload[key] = value
                        else:
                            payload[key] = str(value)
                
                # Add content to payload
                payload['content'] = chunk.content
                
                # Ensure page_number is included from chunk object if not in metadata
                if 'page_number' not in payload and hasattr(chunk, 'page_number'):
                    payload['page_number'] = chunk.page_number
                
                point = PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload=payload
                )
                points.append(point)
            
            # Upload points in batches
            for i in range(0, len(points), self.batch_size):
                batch_points = points[i:i + self.batch_size]
                
                self.qdrant_client.upsert(
                    collection_name=collection_name,
                    points=batch_points
                )
                
                logger.bind(tag=TAG).debug(f"[DOC-INGESTION] Uploaded batch {i//self.batch_size + 1}/{(len(points) + self.batch_size - 1)//self.batch_size}")
            
            logger.bind(tag=TAG).info(f"[DOC-INGESTION] Successfully stored {len(points)} points in collection {collection_name}")
            
            return {
                'success': True,
                'points_stored': len(points),
                'collection_name': collection_name
            }
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"[DOC-INGESTION] Error storing chunks: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _ensure_collection_exists(self, collection_name: str, vector_size: int):
        """Ensure collection exists in vector database"""
        try:
            # Check if collection exists
            collections = self.qdrant_client.get_collections().collections
            existing_collections = [col.name for col in collections]
            
            if collection_name not in existing_collections:
                # Create collection
                self.qdrant_client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=vector_size,
                        distance=models.Distance.COSINE
                    )
                )
                logger.bind(tag=TAG).info(f"[DOC-INGESTION] Created collection: {collection_name}")
            else:
                logger.bind(tag=TAG).debug(f"[DOC-INGESTION] Collection already exists: {collection_name}")
                
        except Exception as e:
            logger.bind(tag=TAG).error(f"[DOC-INGESTION] Error ensuring collection exists: {e}")
            raise
    
    async def _collection_exists(self, collection_name: str) -> bool:
        """Check if a collection exists in the vector database"""
        try:
            if not self.qdrant_client:
                return False
            
            collections = self.qdrant_client.get_collections().collections
            existing_collections = [col.name for col in collections]
            
            return collection_name in existing_collections
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"[DOC-INGESTION] Error checking if collection exists: {e}")
            return False
    
    async def _ensure_payload_indexes(self, collection_name: str):
        """Ensure required payload indexes exist for filtering"""
        try:
            if not self.qdrant_client:
                return
            
            # Define the indexes we need for educational content filtering
            required_indexes = {
                'content_type': models.PayloadSchemaType.KEYWORD,
                'content_category': models.PayloadSchemaType.KEYWORD,
                'grade': models.PayloadSchemaType.KEYWORD, 
                'subject': models.PayloadSchemaType.KEYWORD,
                'document_name': models.PayloadSchemaType.KEYWORD,
                'difficulty_level': models.PayloadSchemaType.KEYWORD,
                'chapter_number': models.PayloadSchemaType.INTEGER,
                'page_number': models.PayloadSchemaType.INTEGER,
                'chunk_type': models.PayloadSchemaType.KEYWORD
            }
            
            logger.bind(tag=TAG).info(f"[DOC-INGESTION] Creating payload indexes for collection '{collection_name}'")
            
            for field_name, field_schema in required_indexes.items():
                try:
                    self.qdrant_client.create_payload_index(
                        collection_name=collection_name,
                        field_name=field_name,
                        field_schema=field_schema
                    )
                    
                    logger.bind(tag=TAG).debug(f"[DOC-INGESTION] Created index for '{field_name}'")
                    
                except Exception as index_error:
                    # Index might already exist, which is fine
                    if "already exists" in str(index_error).lower() or "index with field name" in str(index_error).lower():
                        logger.bind(tag=TAG).debug(f"[DOC-INGESTION] Index for '{field_name}' already exists")
                    else:
                        logger.bind(tag=TAG).warning(f"[DOC-INGESTION] Could not create index for '{field_name}': {index_error}")
            
            logger.bind(tag=TAG).info(f"[DOC-INGESTION] Payload indexes ensured for collection '{collection_name}'")
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"[DOC-INGESTION] Error ensuring payload indexes: {e}")
            # Don't raise - this is not critical enough to stop the ingestion process
    
    def _get_collection_name(self, grade: str, subject: str) -> str:
        """Generate collection name for grade and subject"""
        return f"{grade}-{subject}".lower().replace(" ", "-")
    
    async def get_collection_info(self, grade: str, subject: str) -> Dict[str, Any]:
        """Get information about a collection"""
        try:
            if not self.qdrant_client:
                return {'error': 'No vector database available'}
            
            collection_name = self._get_collection_name(grade, subject)
            
            # Get collection info
            collection_info = self.qdrant_client.get_collection(collection_name)
            
            return {
                'collection_name': collection_name,
                'points_count': collection_info.points_count,
                'vector_size': collection_info.config.params.vectors.size,
                'distance_metric': collection_info.config.params.vectors.distance.value,
                'status': collection_info.status.value
            }
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"[DOC-INGESTION] Error getting collection info: {e}")
            return {'error': str(e)}
    
    async def list_available_collections(self) -> List[Dict[str, Any]]:
        """List all available collections"""
        try:
            if not self.qdrant_client:
                return []
            
            collections = self.qdrant_client.get_collections().collections
            
            collection_list = []
            for collection in collections:
                collection_info = {
                    'name': collection.name,
                    'status': collection.status.value if hasattr(collection, 'status') else 'unknown'
                }
                
                # Try to get additional info
                try:
                    full_info = self.qdrant_client.get_collection(collection.name)
                    collection_info.update({
                        'points_count': full_info.points_count,
                        'vector_size': full_info.config.params.vectors.size
                    })
                except:
                    pass
                
                collection_list.append(collection_info)
            
            return collection_list
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"[DOC-INGESTION] Error listing collections: {e}")
            return []
    
    async def delete_collection(self, grade: str, subject: str) -> Dict[str, Any]:
        """Delete a collection"""
        try:
            if not self.qdrant_client:
                return {'success': False, 'error': 'No vector database available'}
            
            collection_name = self._get_collection_name(grade, subject)
            
            # Delete collection
            self.qdrant_client.delete_collection(collection_name)
            
            logger.bind(tag=TAG).info(f"[DOC-INGESTION] Deleted collection: {collection_name}")
            
            return {
                'success': True,
                'collection_name': collection_name,
                'message': f'Collection {collection_name} deleted successfully'
            }
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"[DOC-INGESTION] Error deleting collection: {e}")
            return {'success': False, 'error': str(e)}
    
    async def query_content_by_type(self, grade: str, subject: str, content_type: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Query content chunks by type from a specific collection
        
        Args:
            grade: Educational grade (e.g., "class-6")
            subject: Subject area (e.g., "mathematics", "english", "science")
            content_type: Type of content (e.g., "concept", "example", "exercise", "definition")
            limit: Maximum number of results to return
            
        Returns:
            List of content items with metadata
        """
        try:
            collection_name = f"{grade}-{subject}"
            logger.bind(tag=TAG).info(f"[DOC-INGESTION] Querying content type '{content_type}' from collection '{collection_name}'")
            
            # Check if collection exists
            if not await self._collection_exists(collection_name):
                logger.bind(tag=TAG).warning(f"[DOC-INGESTION] Collection {collection_name} does not exist")
                return []
            
            # Ensure payload indexes exist for filtering (for existing collections)
            await self._ensure_payload_indexes(collection_name)
            
            # Create filter for content type
            filter_condition = Filter(
                must=[
                    FieldCondition(
                        key="content_type",
                        match=MatchValue(value=content_type)
                    )
                ]
            )
            
            # Query with scroll for better performance with large results
            scroll_result = self.qdrant_client.scroll(
                collection_name=collection_name,
                scroll_filter=filter_condition,
                limit=limit,
                with_payload=True,
                with_vectors=False  # We don't need vectors for display
            )
            
            # Extract and format results
            content_items = []
            for point in scroll_result[0]:  # scroll_result is (points, next_page_offset)
                payload = point.payload
                
                # Extract relevant fields with proper null handling
                def safe_get(key, default=None):
                    """Safely get value, converting None/JSONNull to default"""
                    value = payload.get(key, default)
                    # Handle JSONNull or None values more robustly
                    if value is None:
                        return default
                    if str(value) == 'null' or str(value) == 'None':
                        return default
                    if hasattr(value, '__class__') and 'JSONNull' in str(value.__class__):
                        return default
                    # Check if the string representation indicates a null value
                    if str(type(value)).find('JSONNull') != -1:
                        return default
                    return value
                
                # Extract page number safely
                page_num = safe_get('page_number', 1)
                try:
                    page_num = int(page_num) if page_num else 1
                except (ValueError, TypeError):
                    page_num = 1
                
                # Extract chapter number safely  
                chapter_num = safe_get('chapter_number')
                try:
                    chapter_num = int(chapter_num) if chapter_num else None
                except (ValueError, TypeError):
                    chapter_num = None
                
                item = {
                    'id': str(point.id),
                    'content': safe_get('content', ''),
                    'content_type': safe_get('content_type', content_type),
                    'document_name': safe_get('document_name', 'Unknown'),
                    'page_number': page_num,
                    'chapter_number': chapter_num,
                    'difficulty_level': safe_get('difficulty_level', 'medium'),
                    'word_count': len(safe_get('content', '').split()) if safe_get('content') else 0,
                    'subject': safe_get('subject', subject),
                    'grade': safe_get('grade', grade),
                    'keywords': safe_get('keywords', []) or [],
                    'importance_score': safe_get('importance_score', 0.5),
                    'section_title': safe_get('section_title', ''),
                    'chunk_type': safe_get('chunk_type', 'text')
                }
                
                # Add title based on content type and metadata
                if payload.get('section_title'):
                    item['title'] = payload['section_title']
                else:
                    # Generate a meaningful title based on content type
                    doc_part = payload.get('document_name', 'Document').replace('.pdf', '')
                    page_part = f"Page {payload.get('page_number', '?')}"
                    item['title'] = f"{doc_part} - {page_part}"
                
                content_items.append(item)
            
            logger.bind(tag=TAG).info(f"[DOC-INGESTION] Found {len(content_items)} items of type '{content_type}' in collection '{collection_name}'")
            
            # Sort by page number and then by importance score if available
            content_items.sort(key=lambda x: (
                x.get('page_number', 0),
                -(x.get('importance_score', 0.5) or 0.5)
            ))
            
            return content_items
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"[DOC-INGESTION] Error querying content by type: {e}")
            return []


if __name__ == "__main__":
    # Test the document ingestion service
    async def test_service():
        config = {
            'qdrant_url': 'https://example.com',
            'qdrant_api_key': 'test-key',
            'embedding_model': 'sentence-transformers/all-MiniLM-L6-v2',
            'chunk_size': 800,
            'chunk_overlap': 100,
            'batch_size': 50
        }
        
        service = DocumentIngestionService(config)
        logger.info("Document ingestion service test initialized")
    
    asyncio.run(test_service())