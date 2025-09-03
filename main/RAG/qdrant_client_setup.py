import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()


class QdrantManager:
    def __init__(self):
        self.url = os.getenv("QDRANT_URL", "http://localhost:6333")
        self.api_key = os.getenv("QDRANT_API_KEY", None)
        self.collection_name = os.getenv("COLLECTION_NAME", "rag_collection")
        self.embedding_dimension = int(os.getenv("EMBEDDING_DIMENSION", "384"))
        
        self.client = self._initialize_client()
    
    def _initialize_client(self):
        try:
            if self.api_key:
                client = QdrantClient(
                    url=self.url,
                    api_key=self.api_key
                )
            else:
                client = QdrantClient(url=self.url)
            
            logger.info(f"Connected to Qdrant at {self.url}")
            return client
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            raise
    
    def create_collection(self, collection_name=None, vector_size=None, distance_metric=Distance.COSINE):
        collection_name = collection_name or self.collection_name
        vector_size = vector_size or self.embedding_dimension
        
        try:
            collections = self.client.get_collections().collections
            existing_collections = [col.name for col in collections]
            
            if collection_name in existing_collections:
                logger.info(f"Collection '{collection_name}' already exists")
                return False
            
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=distance_metric
                )
            )
            logger.info(f"Created collection '{collection_name}' with vector size {vector_size}")
            return True
        except Exception as e:
            logger.error(f"Failed to create collection: {e}")
            raise
    
    def ensure_collection_exists(self, collection_name=None, vector_size=None, distance_metric=Distance.COSINE):
        collection_name = collection_name or self.collection_name
        vector_size = vector_size or self.embedding_dimension
        
        try:
            collections = self.client.get_collections().collections
            existing_collections = [col.name for col in collections]
            
            if collection_name not in existing_collections:
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=vector_size,
                        distance=distance_metric
                    )
                )
                logger.info(f"Created collection '{collection_name}' with vector size {vector_size}")
                return True
            else:
                logger.info(f"Collection '{collection_name}' already exists")
                return False
        except Exception as e:
            logger.error(f"Failed to ensure collection exists: {e}")
            raise
    
    def delete_collection(self, collection_name=None):
        collection_name = collection_name or self.collection_name
        
        try:
            self.client.delete_collection(collection_name=collection_name)
            logger.info(f"Deleted collection '{collection_name}'")
            return True
        except Exception as e:
            logger.error(f"Failed to delete collection: {e}")
            return False
    
    def get_collection_info(self, collection_name=None):
        collection_name = collection_name or self.collection_name
        
        try:
            info = self.client.get_collection(collection_name=collection_name)
            return info
        except Exception as e:
            logger.error(f"Failed to get collection info: {e}")
            return None
    
    def upsert_points(self, points, collection_name=None):
        collection_name = collection_name or self.collection_name
        
        try:
            operation_info = self.client.upsert(
                collection_name=collection_name,
                points=points
            )
            logger.info(f"Upserted {len(points)} points to collection '{collection_name}'")
            return operation_info
        except Exception as e:
            logger.error(f"Failed to upsert points: {e}")
            raise
    
    def search(self, query_vector, collection_name=None, limit=5, score_threshold=None):
        collection_name = collection_name or self.collection_name
        
        try:
            search_result = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold
            )
            return search_result
        except Exception as e:
            logger.error(f"Failed to search: {e}")
            raise
    
    def get_points_count(self, collection_name=None):
        collection_name = collection_name or self.collection_name
        
        try:
            collection_info = self.get_collection_info(collection_name)
            if collection_info:
                return collection_info.points_count
            return 0
        except Exception as e:
            logger.error(f"Failed to get points count: {e}")
            return 0


if __name__ == "__main__":
    qdrant_manager = QdrantManager()
    
    qdrant_manager.create_collection()
    
    info = qdrant_manager.get_collection_info()
    if info:
        print(f"Collection info: {info}")