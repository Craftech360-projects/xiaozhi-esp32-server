"""
Chunk Validator
Validates that chunks match their assigned TOC sections using vector similarity
"""

import logging
import numpy as np
from typing import Dict, List, Tuple
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class ChunkValidator:
    """Validate chunks match their assigned TOC sections"""

    def __init__(self, similarity_threshold: float = 0.50):
        self.similarity_threshold = similarity_threshold
        self.embedding_model = None

    def _load_embedding_model(self):
        """Lazy load embedding model"""
        if self.embedding_model is None:
            logger.info("Loading embedding model for validation...")
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

    async def validate_chunks(
        self,
        chunks: List[Dict],
        expanded_toc: Dict
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        Validate chunks against TOC sections

        Returns:
            (valid_chunks, flagged_chunks)

        Validation checks:
        - Chunk content matches TOC section description
        - Similarity score above threshold
        - Content type consistency
        """

        self._load_embedding_model()

        # Build TOC section embeddings
        toc_sections_map = {}
        toc_embeddings = {}

        for section in expanded_toc['sections']:
            section_id = section['id']
            toc_sections_map[section_id] = section

            # Create section description for embedding
            section_desc = self._build_section_description(section)
            section_embedding = self.embedding_model.encode(
                section_desc,
                convert_to_numpy=True
            )
            toc_embeddings[section_id] = section_embedding

        # Validate each chunk
        valid_chunks = []
        flagged_chunks = []

        for chunk in chunks:
            validation_result = self._validate_chunk(
                chunk,
                toc_sections_map,
                toc_embeddings
            )

            if validation_result['is_valid']:
                valid_chunks.append(chunk)
            else:
                flagged_chunks.append({
                    'chunk': chunk,
                    'reason': validation_result['reason'],
                    'similarity_score': validation_result['similarity_score']
                })

        logger.info(
            f"Validation complete: {len(valid_chunks)} valid, "
            f"{len(flagged_chunks)} flagged"
        )

        return valid_chunks, flagged_chunks

    def _validate_chunk(
        self,
        chunk: Dict,
        toc_sections_map: Dict,
        toc_embeddings: Dict
    ) -> Dict:
        """Validate a single chunk"""

        toc_section_id = chunk['toc_section_id']

        if toc_section_id not in toc_sections_map:
            return {
                'is_valid': False,
                'reason': f'TOC section {toc_section_id} not found',
                'similarity_score': 0.0
            }

        # Get chunk embedding
        chunk_embedding = self.embedding_model.encode(
            chunk['content'],
            convert_to_numpy=True
        )

        # Calculate similarity with assigned TOC section
        section_embedding = toc_embeddings[toc_section_id]
        similarity = self._cosine_similarity(chunk_embedding, section_embedding)

        # Check similarity threshold
        if similarity < self.similarity_threshold:
            return {
                'is_valid': False,
                'reason': f'Low similarity ({similarity:.2f}) with TOC section',
                'similarity_score': similarity
            }

        # Validate content type consistency
        chunk_type = chunk['metadata']['section_type']
        toc_type = toc_sections_map[toc_section_id]['type']

        if chunk_type != toc_type:
            return {
                'is_valid': False,
                'reason': f'Content type mismatch: chunk={chunk_type}, toc={toc_type}',
                'similarity_score': similarity
            }

        return {
            'is_valid': True,
            'reason': 'Valid',
            'similarity_score': similarity
        }

    def _build_section_description(self, section: Dict) -> str:
        """Build section description for embedding"""

        parts = [
            section['title'],
            section.get('expanded_description', ''),
            ' '.join(section.get('key_concepts', [])),
            ' '.join(section.get('learning_objectives', []))
        ]

        description = ' '.join(p for p in parts if p)
        return description

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""

        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        similarity = dot_product / (norm1 * norm2)
        return float(similarity)

    def generate_validation_report(self, flagged_chunks: List[Dict]) -> str:
        """Generate human-readable validation report"""

        if not flagged_chunks:
            return "All chunks passed validation!"

        report_lines = [
            f"\n{'='*60}",
            "CHUNK VALIDATION REPORT",
            f"{'='*60}",
            f"\nTotal flagged chunks: {len(flagged_chunks)}\n"
        ]

        for i, flagged in enumerate(flagged_chunks, 1):
            chunk = flagged['chunk']
            reason = flagged['reason']
            similarity = flagged['similarity_score']

            report_lines.extend([
                f"\n{i}. Chunk ID: {chunk['id']}",
                f"   TOC Section: {chunk['toc_section_id']}",
                f"   Section Title: {chunk['metadata']['section_title']}",
                f"   Reason: {reason}",
                f"   Similarity Score: {similarity:.2f}",
                f"   Content Preview: {chunk['content'][:100]}..."
            ])

        report_lines.append(f"\n{'='*60}\n")

        return '\n'.join(report_lines)
