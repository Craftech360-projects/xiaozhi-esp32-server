"""
Visual Embeddings Manager
Generates embeddings for images, figures, and diagrams using CLIP
"""

import logging
from typing import List, Dict, Optional
import numpy as np

logger = logging.getLogger(__name__)

try:
    from transformers import CLIPProcessor, CLIPModel
    import torch
    from PIL import Image
    import io
    CLIP_AVAILABLE = True
except ImportError:
    CLIP_AVAILABLE = False
    logger.warning("CLIP dependencies not available. Install with: pip install transformers torch Pillow")


class VisualEmbeddingManager:
    """Generate embeddings for visual content using CLIP (multimodal)"""

    def __init__(self, model_name: str = "openai/clip-vit-base-patch32"):
        """
        Initialize CLIP model for visual embeddings

        Args:
            model_name: HuggingFace model name for CLIP
        """

        if not CLIP_AVAILABLE:
            raise ImportError(
                "CLIP dependencies required. Install with: pip install transformers torch Pillow"
            )

        self.model_name = model_name
        self.model = None
        self.processor = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        logger.info(f"Initializing Visual Embedding Manager with {model_name} on {self.device}")

    def initialize(self) -> bool:
        """Load CLIP model and processor"""

        try:
            logger.info(f"Loading CLIP model: {self.model_name}")

            self.model = CLIPModel.from_pretrained(self.model_name)
            self.processor = CLIPProcessor.from_pretrained(self.model_name)

            # Move model to device
            self.model = self.model.to(self.device)
            self.model.eval()  # Set to evaluation mode

            logger.info("CLIP model loaded successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to load CLIP model: {e}")
            return False

    async def embed_image(
        self,
        image_data: bytes,
        caption: str = "",
        combine_with_text: bool = True
    ) -> List[float]:
        """
        Generate multimodal embedding for image + caption

        Args:
            image_data: Image bytes
            caption: Text caption/description
            combine_with_text: Whether to combine image and text embeddings

        Returns:
            Embedding vector (512-dim for CLIP-base)
        """

        if not self.model or not self.processor:
            logger.error("CLIP model not initialized")
            return []

        try:
            # Load image from bytes
            image = Image.open(io.BytesIO(image_data))

            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')

            if combine_with_text and caption:
                # Generate combined multimodal embedding
                embedding = self._generate_multimodal_embedding(image, caption)
            else:
                # Generate image-only embedding
                embedding = self._generate_image_embedding(image)

            return embedding.tolist()

        except Exception as e:
            logger.error(f"Failed to generate visual embedding: {e}")
            return []

    def _generate_image_embedding(self, image: Image.Image) -> np.ndarray:
        """Generate image-only embedding"""

        with torch.no_grad():
            # Process image
            inputs = self.processor(images=image, return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            # Get image features
            image_features = self.model.get_image_features(**inputs)

            # Normalize
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)

            # Convert to numpy
            embedding = image_features.cpu().numpy().flatten()

            return embedding

    def _generate_multimodal_embedding(self, image: Image.Image, text: str) -> np.ndarray:
        """Generate combined image + text embedding"""

        with torch.no_grad():
            # Process both image and text (truncate text to max 77 tokens)
            inputs = self.processor(
                text=[text],
                images=image,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=77  # CLIP's maximum token length
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            # Get image and text features
            image_features = self.model.get_image_features(pixel_values=inputs['pixel_values'])
            text_features = self.model.get_text_features(
                input_ids=inputs['input_ids'],
                attention_mask=inputs['attention_mask']
            )

            # Normalize
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            text_features = text_features / text_features.norm(dim=-1, keepdim=True)

            # Combine features (weighted average)
            combined_features = (image_features * 0.6 + text_features * 0.4)

            # Normalize combined features
            combined_features = combined_features / combined_features.norm(dim=-1, keepdim=True)

            # Convert to numpy
            embedding = combined_features.cpu().numpy().flatten()

            return embedding

    async def embed_table(self, table_data: List[List], caption: str = "") -> List[float]:
        """
        Generate embedding for table data

        Args:
            table_data: Table rows as list of lists
            caption: Table caption/description

        Returns:
            Embedding vector (512-dim)
        """

        if not self.model or not self.processor:
            logger.error("CLIP model not initialized")
            return []

        try:
            # Convert table to text representation
            table_text = self._table_to_text(table_data, caption)

            # Generate text embedding
            embedding = self._generate_text_embedding(table_text)

            return embedding.tolist()

        except Exception as e:
            logger.error(f"Failed to generate table embedding: {e}")
            return []

    def _table_to_text(self, table_data: List[List], caption: str) -> str:
        """Convert table data to text representation"""

        text_parts = []

        if caption:
            text_parts.append(caption)

        # Add table content
        for row in table_data:
            row_text = " | ".join(str(cell) for cell in row if cell)
            if row_text:
                text_parts.append(row_text)

        return ". ".join(text_parts)

    def _generate_text_embedding(self, text: str) -> np.ndarray:
        """Generate text-only embedding"""

        with torch.no_grad():
            # Process text (truncate to max 77 tokens)
            inputs = self.processor(
                text=[text],
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=77  # CLIP's maximum token length
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            # Get text features
            text_features = self.model.get_text_features(
                input_ids=inputs['input_ids'],
                attention_mask=inputs['attention_mask']
            )

            # Normalize
            text_features = text_features / text_features.norm(dim=-1, keepdim=True)

            # Convert to numpy
            embedding = text_features.cpu().numpy().flatten()

            return embedding

    async def search_visual_content(
        self,
        query: str,
        qdrant_client,
        collection_name: str,
        limit: int = 5
    ) -> List[Dict]:
        """
        Search for relevant visual content using text query

        Args:
            query: Text query (e.g., "show me diagram of photosynthesis")
            qdrant_client: Qdrant client instance
            collection_name: Collection containing visual content
            limit: Number of results to return

        Returns:
            List of visual content matches
        """

        if not self.model or not self.processor:
            logger.error("CLIP model not initialized")
            return []

        try:
            # Generate text embedding for query
            query_embedding = self._generate_text_embedding(query)

            # Search in Qdrant
            search_results = qdrant_client.search(
                collection_name=collection_name,
                query_vector=query_embedding.tolist(),
                limit=limit,
                with_payload=True
            )

            # Convert to dict format
            results = []
            for result in search_results:
                results.append({
                    'id': result.id,
                    'score': result.score,
                    'type': result.payload.get('type', 'unknown'),
                    'caption': result.payload.get('caption', ''),
                    'page': result.payload.get('page', 0),
                    'figure_id': result.payload.get('figure_id') or result.payload.get('table_id'),
                    'nearby_text': result.payload.get('nearby_text', ''),
                    'metadata': result.payload
                })

            return results

        except Exception as e:
            logger.error(f"Failed to search visual content: {e}")
            return []

    def get_embedding_dim(self) -> int:
        """Get embedding dimension (512 for CLIP-base)"""
        return 512

    def is_initialized(self) -> bool:
        """Check if model is initialized"""
        return self.model is not None and self.processor is not None


class VisualContentProcessor:
    """Process and prepare visual content for storage"""

    def __init__(self, visual_embedding_manager: VisualEmbeddingManager):
        self.embedding_manager = visual_embedding_manager

    async def process_figures(self, figures: List[Dict]) -> List[Dict]:
        """
        Process figures and generate embeddings

        Args:
            figures: List of figure dicts from FigureExtractor

        Returns:
            List of processed figures with embeddings
        """

        processed_figures = []

        for figure in figures:
            try:
                # Generate embedding (if image_data available)
                embedding = None
                if figure.get('image_data'):
                    embedding = await self.embedding_manager.embed_image(
                        figure['image_data'],
                        figure.get('caption', ''),
                        combine_with_text=True
                    )
                else:
                    # Use caption-only embedding
                    caption_text = f"{figure.get('caption', '')} {figure.get('nearby_text', '')}"
                    if caption_text.strip():
                        embedding = self.embedding_manager._generate_text_embedding(caption_text)
                        if embedding is not None:
                            embedding = embedding.tolist()

                processed_figure = {
                    **figure,
                    'embedding': embedding,
                    'type': 'figure',
                    'has_image_data': figure.get('image_data') is not None
                }

                processed_figures.append(processed_figure)

            except Exception as e:
                logger.error(f"Failed to process figure {figure.get('figure_id')}: {e}")
                continue

        return processed_figures

    async def process_tables(self, tables: List[Dict]) -> List[Dict]:
        """
        Process tables and generate embeddings

        Args:
            tables: List of table dicts from FigureExtractor

        Returns:
            List of processed tables with embeddings
        """

        processed_tables = []

        for table in tables:
            try:
                # Generate table embedding
                embedding = await self.embedding_manager.embed_table(
                    table.get('data', []),
                    table.get('caption', '')
                )

                processed_table = {
                    **table,
                    'embedding': embedding,
                    'type': 'table'
                }

                processed_tables.append(processed_table)

            except Exception as e:
                logger.error(f"Failed to process table {table.get('table_id')}: {e}")
                continue

        return processed_tables
