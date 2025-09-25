"""
Shared Component Manager for Educational Service
Manages expensive components that can be shared between clients
"""

import logging
import os
import asyncio
from typing import Optional, Dict, Any

from ..rag.qdrant_manager import QdrantEducationManager
from ..rag.embeddings import EmbeddingManager

logger = logging.getLogger(__name__)


class SharedEducationalComponents:
    """
    Singleton class to manage shared expensive components for educational services
    """
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SharedEducationalComponents, cls).__new__(cls)
            cls._instance.qdrant_manager = None
            cls._instance.embedding_manager = None
            cls._instance.ingestion_pipeline = None
        return cls._instance

    async def initialize(self) -> bool:
        """Initialize shared components"""
        if self._initialized:
            logger.info("Shared educational components already initialized")
            return True
            
        try:
            logger.info("Initializing shared educational components...")
            
            # Initialize Qdrant manager
            self.qdrant_manager = QdrantEducationManager()
            qdrant_success = await self.qdrant_manager.initialize_grade6_and_grade10_science()
            if not qdrant_success:
                logger.error("Failed to initialize shared Qdrant manager")
                return False

            # Initialize embedding manager with prewarmed models
            self.embedding_manager = EmbeddingManager()
            embedding_success = await self._initialize_embedding_models()
            if not embedding_success:
                logger.error("Failed to initialize shared embedding manager")
                return False

            # Initialize ingestion pipeline with shared components
            from ..education.textbook_ingestion import TextbookIngestionPipeline
            self.ingestion_pipeline = TextbookIngestionPipeline()
            self.ingestion_pipeline.qdrant_manager = self.qdrant_manager  # Reuse initialized manager
            self.ingestion_pipeline.embedding_manager = self.embedding_manager  # Reuse initialized manager
            self.ingestion_pipeline.is_initialized = True  # Skip duplicate initialization
            logger.info("Shared textbook ingestion pipeline configured (reusing components)")

            # Log collection statistics
            stats = await self.qdrant_manager.get_collection_stats()
            logger.info(f"Available collections: {stats['total_collections']}")
            logger.info(f"Total educational content points: {stats['total_points']}")

            self._initialized = True
            logger.info("✅ Shared educational components initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize shared educational components: {e}")
            return False

    async def _initialize_embedding_models(self) -> bool:
        """Initialize embedding models with prewarming of SentenceTransformers"""
        try:
            logger.info("Initializing embedding models with prewarming...")
            
            # Import the same libraries used in EmbeddingManager to check availability
            try:
                import openai
                openai_available = True
            except ImportError:
                openai_available = False

            try:
                from sentence_transformers import SentenceTransformer
                sentence_transformers_available = True
            except ImportError:
                sentence_transformers_available = False

            try:
                import torch
                import clip
                clip_available = True
            except ImportError:
                clip_available = False

            # Load OpenAI if available
            if openai_available and os.getenv("OPENAI_API_KEY"):
                logger.info("Using OpenAI embeddings for text")
                self.embedding_manager.text_model = "openai"
            elif sentence_transformers_available:
                # Preload the text embedding model (SentenceTransformer)
                logger.info("Prewarming SentenceTransformer for text embeddings: all-MiniLM-L6-v2")
                self.embedding_manager.text_model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("✅ Text embedding model prewarmed")
            else:
                logger.warning("No text embedding model available")

            # Preload the formula embedding model (SentenceTransformer)
            if sentence_transformers_available:
                logger.info("Prewarming SentenceTransformer for formula embeddings: all-mpnet-base-v2")
                self.embedding_manager.formula_model = SentenceTransformer('all-mpnet-base-v2')
                logger.info("✅ Formula embedding model prewarmed")
            else:
                logger.warning("No formula embedding model available")

            # Initialize visual embeddings (CLIP) if available
            if clip_available:
                logger.info("Loading CLIP for visual embeddings")
                device = "cuda" if torch.cuda.is_available() else "cpu"
                self.embedding_manager.clip_model, self.embedding_manager.clip_preprocess = clip.load("ViT-B/32", device=device)
                self.embedding_manager.visual_model = "clip"
            else:
                logger.warning("CLIP not available for visual embeddings")

            self.embedding_manager.is_initialized = True
            logger.info("Embedding models initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize embedding models: {e}")
            return False

    def get_shared_components(self) -> Dict[str, Any]:
        """Get shared components for use in a new EducationalService instance"""
        if not self._initialized:
            raise RuntimeError("Shared components not initialized")
        
        return {
            'qdrant_manager': self.qdrant_manager,
            'embedding_manager': self.embedding_manager,
            'ingestion_pipeline': self.ingestion_pipeline
        }

    @classmethod
    def is_initialized(cls) -> bool:
        """Check if shared components are initialized"""
        instance = cls._instance
        return instance._initialized if instance else False


# Global shared instance
shared_components = SharedEducationalComponents()


async def initialize_shared_components() -> bool:
    """Initialize shared educational components"""
    return await shared_components.initialize()


def get_shared_educational_components() -> Dict[str, Any]:
    """Get shared educational components"""
    return shared_components.get_shared_components()