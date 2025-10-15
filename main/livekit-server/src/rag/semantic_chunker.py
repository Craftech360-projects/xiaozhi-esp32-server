"""
Semantic Chunking based on TOC Structure
PRESERVES: Activities as complete units, context around definitions
"""

import logging
import re
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class SemanticChunker:
    """Chunk text based on TOC structure with content preservation"""

    def __init__(self, min_chunk_size: int = 400, max_chunk_size: int = 800):
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size

    def chunk_by_toc(self, full_text: str, expanded_toc: Dict) -> List[Dict]:
        """
        Chunk text guided by TOC structure

        GUARANTEES:
        - Activities are kept as single chunks (no splitting)
        - Key definitions preserved with context
        - Teaching content gets high priority
        """

        all_chunks = []
        chunk_id = 1

        for section in expanded_toc['sections']:
            section_content = self._extract_section_content(
                full_text,
                section,
                expanded_toc['sections']
            )

            if not section_content or len(section_content.strip()) < 50:
                logger.warning(f"Section {section['id']} has insufficient content")
                continue

            # CRITICAL: Activities are NOT split
            if section['type'] == 'activity':
                logger.info(f"Preserving activity {section['id']} as complete unit")
                section_chunks = [section_content]  # Single chunk
            else:
                # Regular content: chunk by semantic boundaries
                section_chunks = self._chunk_section_content(
                    section_content,
                    preserve_definitions=True
                )

            # Create chunk objects with rich metadata
            for i, chunk_text in enumerate(section_chunks):
                chunk = {
                    'id': chunk_id,
                    'content': chunk_text.strip(),
                    'toc_section_id': section['id'],
                    'chunk_index': i,
                    'metadata': {
                        # From TOC
                        'chapter': expanded_toc['chapter'],
                        'chapter_title': expanded_toc['title'],
                        'section_title': section['title'],
                        'section_type': section['type'],
                        'content_priority': section['content_priority'],

                        # Learning metadata
                        'key_concepts': section.get('key_concepts', []),
                        'learning_objectives': section.get('learning_objectives', []),
                        'difficulty_level': section.get('difficulty_level', 'beginner'),
                        'cognitive_level': section.get('cognitive_level', 'understand'),
                        'related_activities': section.get('related_activities', []),

                        # Standard fields
                        'chapter_number': expanded_toc['chapter'],
                        'subject': 'science',
                        'content_type': section['type'],
                        'is_activity': section['type'] == 'activity',

                        # Weighting score for retrieval
                        'content_weight': self._calculate_content_weight(section)
                    }
                }

                all_chunks.append(chunk)
                chunk_id += 1

        logger.info(f"Created {len(all_chunks)} chunks from {len(expanded_toc['sections'])} sections")
        return all_chunks

    def _calculate_content_weight(self, section: Dict) -> float:
        """
        Calculate content weight for retrieval boosting

        HIGH priority teaching_text: 1.0
        MEDIUM priority examples: 0.85
        LOW priority practice: 0.7
        """

        priority_weights = {
            'high': 1.0,
            'medium': 0.85,
            'low': 0.7
        }

        type_weights = {
            'teaching_text': 1.0,
            'activity': 0.95,
            'example': 0.85,
            'practice': 0.75
        }

        priority = section.get('content_priority', 'medium')
        section_type = section.get('type', 'teaching_text')

        # Combine priority and type weights
        weight = priority_weights.get(priority, 0.85) * type_weights.get(section_type, 0.85)

        return round(weight, 2)

    def _extract_section_content(self, full_text: str, section: Dict, all_sections: List[Dict]) -> str:
        """Extract content for a specific section with fuzzy matching"""

        section_title = section['title']
        section_id = section['id']
        start_text = section.get('start_text', '')

        # Try multiple strategies to find section start
        start_idx = -1

        # Strategy 1: Try exact start_text match
        if start_text and len(start_text.strip()) > 10:
            start_idx = full_text.find(start_text[:50])  # Use first 50 chars

        # Strategy 2: Try section ID pattern (1.1, activity_1.1, etc.)
        if start_idx == -1:
            # Try patterns like "1.1 ", "Activity 1.1", "1.1:"
            id_clean = section_id.replace('activity_', '')
            patterns = [
                fr'\b{re.escape(id_clean)}\s',
                fr'Activity\s+{re.escape(id_clean)}',
                fr'{re.escape(id_clean)}:',
                fr'{re.escape(id_clean)}\.'
            ]
            for pattern in patterns:
                match = re.search(pattern, full_text, re.IGNORECASE)
                if match:
                    start_idx = match.start()
                    break

        # Strategy 3: Try title match (case-insensitive, fuzzy)
        if start_idx == -1:
            # Try exact title
            title_pattern = re.escape(section_title)
            match = re.search(title_pattern, full_text, re.IGNORECASE)
            if match:
                start_idx = match.start()
            else:
                # Try first 3 words of title
                title_words = section_title.split()[:3]
                if len(title_words) >= 2:
                    partial_title = ' '.join(title_words)
                    match = re.search(re.escape(partial_title), full_text, re.IGNORECASE)
                    if match:
                        start_idx = match.start()

        # Strategy 4: If still not found, divide content equally
        if start_idx == -1:
            logger.warning(f"Could not find start of section {section['id']}, using fallback")
            current_idx = all_sections.index(section)
            section_size = len(full_text) // len(all_sections)
            start_idx = current_idx * section_size
            end_idx = min(start_idx + section_size, len(full_text))
            return full_text[start_idx:end_idx]

        # Find section end
        current_idx = all_sections.index(section)
        if current_idx < len(all_sections) - 1:
            next_section = all_sections[current_idx + 1]
            next_start_text = next_section.get('start_text', '')
            next_id = next_section['id'].replace('activity_', '')

            # Try to find next section start
            end_idx = -1

            if next_start_text:
                end_idx = full_text.find(next_start_text[:50], start_idx + 100)

            if end_idx == -1:
                # Try next section ID patterns
                patterns = [
                    fr'\b{re.escape(next_id)}\s',
                    fr'Activity\s+{re.escape(next_id)}',
                    fr'{re.escape(next_id)}:'
                ]
                for pattern in patterns:
                    match = re.search(pattern, full_text[start_idx + 100:], re.IGNORECASE)
                    if match:
                        end_idx = start_idx + 100 + match.start()
                        break

            if end_idx == -1:
                # Use reasonable max section size
                end_idx = min(start_idx + 2000, len(full_text))
        else:
            end_idx = len(full_text)

        content = full_text[start_idx:end_idx]

        # Log what we found
        logger.info(f"Section {section_id}: extracted {len(content)} chars")

        return content

    def _chunk_section_content(self, content: str, preserve_definitions: bool = True) -> List[str]:
        """
        Chunk section content preserving context around definitions

        If preserve_definitions=True:
        - Keep definition sentences with surrounding context
        - Don't split definitions across chunks
        """

        chunks = []

        # Detect definition sentences
        definition_sentences = []
        if preserve_definitions:
            definition_sentences = self._detect_definitions(content)

        # Split by paragraphs
        paragraphs = re.split(r'\n\s*\n|\n{2,}', content)

        current_chunk = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # Check if this paragraph contains a definition
            has_definition = any(defn in para for defn in definition_sentences)

            # If adding this paragraph exceeds max size
            if len(current_chunk) + len(para) + 1 > self.max_chunk_size:
                # If current chunk has definition, DON'T split
                if has_definition and current_chunk:
                    # Save current chunk first
                    if len(current_chunk) >= self.min_chunk_size:
                        chunks.append(current_chunk)
                    # Start new chunk with definition paragraph
                    current_chunk = para
                elif len(current_chunk) >= self.min_chunk_size:
                    chunks.append(current_chunk)
                    current_chunk = para
                else:
                    # Current chunk too small, split by sentences
                    sentences = self._split_into_sentences(para)
                    for sent in sentences:
                        if len(current_chunk) + len(sent) + 1 <= self.max_chunk_size:
                            current_chunk += " " + sent if current_chunk else sent
                        else:
                            if current_chunk:
                                chunks.append(current_chunk)
                            current_chunk = sent
            else:
                current_chunk += "\n\n" + para if current_chunk else para

        # Add final chunk
        if current_chunk and len(current_chunk) >= self.min_chunk_size:
            chunks.append(current_chunk)
        elif current_chunk and chunks:
            chunks[-1] += "\n\n" + current_chunk
        elif current_chunk:
            chunks.append(current_chunk)

        return chunks

    def _detect_definitions(self, text: str) -> List[str]:
        """Detect definition sentences in text"""

        definition_patterns = [
            r'[A-Z][a-z]+\s+is\s+(?:a|an|the)\s+[a-z]+',  # "Science is a way..."
            r'[A-Z][a-z]+\s+refers\s+to',
            r'[A-Z][a-z]+\s+means',
            r'We\s+(?:define|call)\s+[a-z]+\s+as',
            r'The\s+definition\s+of'
        ]

        sentences = self._split_into_sentences(text)
        definitions = []

        for sentence in sentences:
            if any(re.search(pattern, sentence) for pattern in definition_patterns):
                definitions.append(sentence)

        return definitions

    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
