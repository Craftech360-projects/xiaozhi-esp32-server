import os
import logging
from typing import List, Optional, Union
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from sentence_transformers import SentenceTransformer
from fastembed import TextEmbedding
from dotenv import load_dotenv
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()


class EmbeddingManager:
    def __init__(self, provider: str = "huggingface"):
        self.provider = provider
        self.model_name = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        self.embedding_dimension = int(os.getenv("EMBEDDING_DIMENSION", "384"))
        self.embeddings = self._initialize_embeddings()
    
    def _initialize_embeddings(self):
        if self.provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                logger.warning("OpenAI API key not found, falling back to HuggingFace")
                self.provider = "huggingface"
            else:
                logger.info("Using OpenAI embeddings")
                return OpenAIEmbeddings(openai_api_key=api_key)
        
        if self.provider == "fastembed":
            logger.info(f"Using FastEmbed with model: {self.model_name}")
            return TextEmbedding(model_name=self.model_name)
        
        logger.info(f"Using HuggingFace embeddings with model: {self.model_name}")
        return HuggingFaceEmbeddings(
            model_name=self.model_name,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
    
    def embed_text(self, text: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        try:
            if isinstance(text, str):
                text = [text]
            
            if self.provider == "fastembed":
                embeddings = list(self.embeddings.embed(text))
                if len(text) == 1:
                    return embeddings[0].tolist()
                return [emb.tolist() for emb in embeddings]
            else:
                embeddings = self.embeddings.embed_documents(text)
                if len(text) == 1:
                    return embeddings[0]
                return embeddings
        except Exception as e:
            logger.error(f"Failed to embed text: {e}")
            raise
    
    def embed_documents(self, documents: List[Document]) -> List[List[float]]:
        try:
            texts = [doc.page_content for doc in documents]
            embeddings = self.embed_text(texts)
            logger.info(f"Generated embeddings for {len(documents)} documents")
            return embeddings
        except Exception as e:
            logger.error(f"Failed to embed documents: {e}")
            raise
    
    def embed_query(self, query: str) -> List[float]:
        try:
            if self.provider == "fastembed":
                embedding = list(self.embeddings.embed([query]))[0]
                return embedding.tolist()
            else:
                embedding = self.embeddings.embed_query(query)
                return embedding
        except Exception as e:
            logger.error(f"Failed to embed query: {e}")
            raise
    
    def get_embedding_dimension(self) -> int:
        if self.provider == "openai":
            return 1536
        elif self.provider == "fastembed":
            if "all-MiniLM-L6-v2" in self.model_name:
                return 384
            elif "all-mpnet-base-v2" in self.model_name:
                return 768
            else:
                return self.embedding_dimension
        else:
            return self.embedding_dimension
    
    def compute_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        cosine_similarity = np.dot(vec1, vec2) / (norm1 * norm2)
        return float(cosine_similarity)
    
    def batch_embed_documents(self, documents: List[Document], batch_size: int = 32) -> List[List[float]]:
        all_embeddings = []
        
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            batch_embeddings = self.embed_documents(batch)
            all_embeddings.extend(batch_embeddings)
            logger.info(f"Processed batch {i//batch_size + 1}/{(len(documents) + batch_size - 1)//batch_size}")
        
        return all_embeddings


class MultiModalEmbeddingManager(EmbeddingManager):
    def __init__(self):
        super().__init__()
        self.text_model = self.model_name
        self.image_model = "Qdrant/clip-ViT-B-32-vision"
    
    def embed_image(self, image_path: str) -> List[float]:
        logger.warning("Image embedding not implemented in this version")
        return [0.0] * 512
    
    def embed_multimodal(self, text: str, image_path: Optional[str] = None) -> dict:
        result = {
            "text_embedding": self.embed_query(text)
        }
        
        if image_path:
            result["image_embedding"] = self.embed_image(image_path)
        
        return result


if __name__ == "__main__":
    embedding_manager = EmbeddingManager()
    
    sample_text = "This is a sample text for embedding"
    embedding = embedding_manager.embed_query(sample_text)
    print(f"Embedding dimension: {len(embedding)}")
    
    sample_docs = [
        Document(page_content="Document 1 content", metadata={"id": 1}),
        Document(page_content="Document 2 content", metadata={"id": 2})
    ]
    doc_embeddings = embedding_manager.embed_documents(sample_docs)
    print(f"Generated {len(doc_embeddings)} document embeddings")