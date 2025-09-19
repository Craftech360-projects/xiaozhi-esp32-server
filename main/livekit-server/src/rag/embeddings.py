"""
Embedding Manager for Educational Content
Handles text, visual, and formula embeddings with caching
"""

import logging
import os
import hashlib
import pickle
from typing import List, Dict, Optional, Any, Union, Tuple
from pathlib import Path
import asyncio

# OpenAI for text embeddings
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Sentence Transformers for specialized embeddings
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

# CLIP for visual embeddings
try:
    import torch
    import clip
    CLIP_AVAILABLE = True
except ImportError:
    CLIP_AVAILABLE = False

logger = logging.getLogger(__name__)


class EmbeddingManager:
    """Manages different types of embeddings for educational content"""

    def __init__(self, cache_dir: str = "embeddings_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

        # Initialize OpenAI
        if OPENAI_AVAILABLE:
            openai.api_key = os.getenv("OPENAI_API_KEY")

        # Initialize embedding models
        self.text_model = None
        self.visual_model = None
        self.formula_model = None
        self.clip_model = None
        self.clip_preprocess = None

        self.is_initialized = False

    async def initialize(self) -> bool:
        """Initialize all embedding models"""
        try:
            logger.info("Initializing embedding models...")

            # Initialize text embeddings (OpenAI or Sentence Transformers)
            if OPENAI_AVAILABLE and os.getenv("OPENAI_API_KEY"):
                logger.info("Using OpenAI embeddings for text")
                self.text_model = "openai"
            elif SENTENCE_TRANSFORMERS_AVAILABLE:
                logger.info("Loading Sentence Transformers for text embeddings")
                self.text_model = SentenceTransformer('all-MiniLM-L6-v2')
            else:
                logger.warning("No text embedding model available")

            # Initialize visual embeddings (CLIP)
            if CLIP_AVAILABLE:
                logger.info("Loading CLIP for visual embeddings")
                device = "cuda" if torch.cuda.is_available() else "cpu"
                self.clip_model, self.clip_preprocess = clip.load("ViT-B/32", device=device)
                self.visual_model = "clip"
            else:
                logger.warning("CLIP not available for visual embeddings")

            # Initialize formula embeddings (specialized model)
            if SENTENCE_TRANSFORMERS_AVAILABLE:
                logger.info("Loading specialized model for formula embeddings")
                self.formula_model = SentenceTransformer('all-mpnet-base-v2')
            else:
                logger.warning("No formula embedding model available")

            self.is_initialized = True
            logger.info("Embedding models initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize embedding models: {e}")
            return False

    async def get_text_embedding(self, text: str, use_cache: bool = True) -> Optional[List[float]]:
        """Generate text embedding"""
        if not text.strip():
            return None

        # Check cache first
        if use_cache:
            cached_embedding = self._get_cached_embedding(text, "text")
            if cached_embedding is not None:
                return cached_embedding

        try:
            embedding = None

            if self.text_model == "openai" and OPENAI_AVAILABLE:
                # Use OpenAI embeddings
                response = await asyncio.to_thread(
                    openai.embeddings.create,
                    input=text,
                    model="text-embedding-3-small"
                )
                embedding = response.data[0].embedding

            elif isinstance(self.text_model, SentenceTransformer):
                # Use Sentence Transformers
                embedding = await asyncio.to_thread(
                    self.text_model.encode,
                    text,
                    convert_to_tensor=False,
                    normalize_embeddings=True
                )
                embedding = embedding.tolist()

            # Cache the result
            if embedding and use_cache:
                self._cache_embedding(text, "text", embedding)

            return embedding

        except Exception as e:
            logger.error(f"Failed to generate text embedding: {e}")
            return None

    async def get_visual_embedding(self, image_data: bytes, use_cache: bool = True) -> Optional[List[float]]:
        """Generate visual embedding for images"""
        if not image_data:
            return None

        # Check cache first
        if use_cache:
            cached_embedding = self._get_cached_embedding(image_data, "visual")
            if cached_embedding is not None:
                return cached_embedding

        try:
            if not CLIP_AVAILABLE or self.clip_model is None:
                logger.warning("CLIP not available for visual embeddings")
                return None

            # Process image with CLIP
            from PIL import Image
            import io

            image = Image.open(io.BytesIO(image_data))
            image_tensor = self.clip_preprocess(image).unsqueeze(0)

            with torch.no_grad():
                embedding = self.clip_model.encode_image(image_tensor)
                embedding = embedding.cpu().numpy().flatten().tolist()

            # Cache the result
            if embedding and use_cache:
                self._cache_embedding(image_data, "visual", embedding)

            return embedding

        except Exception as e:
            logger.error(f"Failed to generate visual embedding: {e}")
            return None

    async def get_formula_embedding(self, formula_text: str, use_cache: bool = True) -> Optional[List[float]]:
        """Generate embedding for mathematical formulas"""
        if not formula_text.strip():
            return None

        # Check cache first
        if use_cache:
            cached_embedding = self._get_cached_embedding(formula_text, "formula")
            if cached_embedding is not None:
                return cached_embedding

        try:
            if self.formula_model is None:
                # Fallback to text embedding
                return await self.get_text_embedding(formula_text, use_cache)

            # Use specialized model for formulas
            embedding = await asyncio.to_thread(
                self.formula_model.encode,
                formula_text,
                convert_to_tensor=False,
                normalize_embeddings=True
            )
            embedding = embedding.tolist()

            # Cache the result
            if embedding and use_cache:
                self._cache_embedding(formula_text, "formula", embedding)

            return embedding

        except Exception as e:
            logger.error(f"Failed to generate formula embedding: {e}")
            return None

    async def get_contextual_embedding(self, content: str, context: str, use_cache: bool = True) -> Optional[List[float]]:
        """Generate embedding with additional context"""
        combined_text = f"{context}\n\n{content}"
        return await self.get_text_embedding(combined_text, use_cache)

    async def get_multi_modal_embedding(
        self,
        text: str,
        formula: Optional[str] = None,
        image_data: Optional[bytes] = None
    ) -> Dict[str, Optional[List[float]]]:
        """Generate embeddings for multiple modalities"""
        embeddings = {}

        # Text embedding
        embeddings["text"] = await self.get_text_embedding(text)

        # Formula embedding
        if formula:
            embeddings["formula"] = await self.get_formula_embedding(formula)

        # Visual embedding
        if image_data:
            embeddings["visual"] = await self.get_visual_embedding(image_data)

        return embeddings

    async def batch_text_embeddings(self, texts: List[str], use_cache: bool = True) -> List[Optional[List[float]]]:
        """Generate embeddings for multiple texts efficiently"""
        if not texts:
            return []

        try:
            # Check cache for all texts first
            embeddings = []
            uncached_texts = []
            uncached_indices = []

            for i, text in enumerate(texts):
                if use_cache:
                    cached = self._get_cached_embedding(text, "text")
                    if cached is not None:
                        embeddings.append(cached)
                        continue

                embeddings.append(None)  # Placeholder
                uncached_texts.append(text)
                uncached_indices.append(i)

            # Generate embeddings for uncached texts
            if uncached_texts:
                if self.text_model == "openai" and OPENAI_AVAILABLE:
                    # Batch OpenAI embeddings
                    response = await asyncio.to_thread(
                        openai.embeddings.create,
                        input=uncached_texts,
                        model="text-embedding-3-small"
                    )
                    new_embeddings = [item.embedding for item in response.data]

                elif isinstance(self.text_model, SentenceTransformer):
                    # Batch Sentence Transformers
                    new_embeddings = await asyncio.to_thread(
                        self.text_model.encode,
                        uncached_texts,
                        convert_to_tensor=False,
                        normalize_embeddings=True,
                        batch_size=32
                    )
                    new_embeddings = [emb.tolist() for emb in new_embeddings]

                else:
                    new_embeddings = [None] * len(uncached_texts)

                # Fill in the embeddings and cache them
                for i, (text, embedding) in enumerate(zip(uncached_texts, new_embeddings)):
                    original_index = uncached_indices[i]
                    embeddings[original_index] = embedding

                    if embedding and use_cache:
                        self._cache_embedding(text, "text", embedding)

            return embeddings

        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            return [None] * len(texts)

    def _get_cache_key(self, content: Union[str, bytes], embedding_type: str) -> str:
        """Generate cache key for content"""
        if isinstance(content, str):
            content_bytes = content.encode('utf-8')
        else:
            content_bytes = content

        hash_object = hashlib.md5(content_bytes)
        content_hash = hash_object.hexdigest()
        return f"{embedding_type}_{content_hash}"

    def _get_cached_embedding(self, content: Union[str, bytes], embedding_type: str) -> Optional[List[float]]:
        """Retrieve embedding from cache"""
        cache_key = self._get_cache_key(content, embedding_type)
        cache_file = self.cache_dir / f"{cache_key}.pkl"

        try:
            if cache_file.exists():
                with open(cache_file, 'rb') as f:
                    return pickle.load(f)
        except Exception as e:
            logger.warning(f"Failed to load cached embedding: {e}")

        return None

    def _cache_embedding(self, content: Union[str, bytes], embedding_type: str, embedding: List[float]) -> None:
        """Store embedding in cache"""
        cache_key = self._get_cache_key(content, embedding_type)
        cache_file = self.cache_dir / f"{cache_key}.pkl"

        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(embedding, f)
        except Exception as e:
            logger.warning(f"Failed to cache embedding: {e}")

    def clear_cache(self) -> None:
        """Clear embedding cache"""
        try:
            for cache_file in self.cache_dir.glob("*.pkl"):
                cache_file.unlink()
            logger.info("Embedding cache cleared")
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")

    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        stats = {"text": 0, "visual": 0, "formula": 0, "total": 0}

        try:
            for cache_file in self.cache_dir.glob("*.pkl"):
                embedding_type = cache_file.stem.split("_")[0]
                if embedding_type in stats:
                    stats[embedding_type] += 1
                stats["total"] += 1
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")

        return stats

    async def embed_content_chunk(self, chunk_data: Dict[str, Any]) -> Dict[str, Optional[List[float]]]:
        """Generate all relevant embeddings for a content chunk"""
        embeddings = {}

        # Main text embedding
        content = chunk_data.get("content", "")
        if content:
            embeddings["text"] = await self.get_text_embedding(content)

        # Contextual embedding (with surrounding content)
        context = ""
        if chunk_data.get("preceding_content"):
            context += chunk_data["preceding_content"] + "\n"
        if chunk_data.get("following_content"):
            context += "\n" + chunk_data["following_content"]

        if context.strip():
            embeddings["context"] = await self.get_contextual_embedding(content, context)

        # Formula embedding if present
        if chunk_data.get("formula_latex"):
            embeddings["formula"] = await self.get_formula_embedding(chunk_data["formula_latex"])

        # Visual embedding if present
        if chunk_data.get("image_data"):
            embeddings["visual"] = await self.get_visual_embedding(chunk_data["image_data"])

        return embeddings

    def get_embedding_dimensions(self) -> Dict[str, int]:
        """Get dimensions for different embedding types"""
        return {
            "text": 1536 if self.text_model == "openai" else 384,  # OpenAI vs Sentence Transformers
            "visual": 512,  # CLIP
            "formula": 768   # MPNet
        }

    async def similarity_search(
        self,
        query_embedding: List[float],
        candidate_embeddings: List[List[float]],
        top_k: int = 10
    ) -> List[Tuple[int, float]]:
        """Compute similarity scores and return top candidates"""
        try:
            import numpy as np
            from sklearn.metrics.pairwise import cosine_similarity

            query_array = np.array(query_embedding).reshape(1, -1)
            candidates_array = np.array(candidate_embeddings)

            # Compute cosine similarity
            similarities = cosine_similarity(query_array, candidates_array)[0]

            # Get top k indices and scores
            top_indices = np.argsort(similarities)[-top_k:][::-1]
            top_scores = similarities[top_indices]

            return [(int(idx), float(score)) for idx, score in zip(top_indices, top_scores)]

        except Exception as e:
            logger.error(f"Failed to compute similarities: {e}")
            return []