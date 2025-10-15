"""
Reference Resolver
Detects and resolves cross-references in educational content
"""

import re
import logging
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class ReferenceResolver:
    """Detect and resolve references between educational content"""

    def __init__(self):
        # Reference patterns for detection
        self.reference_patterns = {
            'activity': [
                r'[Aa]ctivity\s+(\d+\.?\d*)',
                r'[Aa]ctivity\s+([A-Z])',
                r'[Ee]xercise\s+(\d+\.?\d*)',
            ],
            'section': [
                r'[Ss]ection\s+(\d+\.\d+)',
                r'[Ss]ec\.\s+(\d+\.\d+)',
                r'in\s+section\s+(\d+\.\d+)',
            ],
            'chapter': [
                r'[Cc]hapter\s+(\d+)',
                r'[Cc]h\.\s+(\d+)',
                r'in\s+chapter\s+(\d+)',
            ],
            'figure': [
                r'[Ff]igure\s+(\d+\.?\d*)',
                r'[Ff]ig\.\s+(\d+\.?\d*)',
                r'see\s+figure\s+(\d+\.?\d*)',
            ],
            'table': [
                r'[Tt]able\s+(\d+\.?\d*)',
                r'[Tt]ab\.\s+(\d+\.?\d*)',
                r'see\s+table\s+(\d+\.?\d*)',
            ],
            'page': [
                r'[Pp]age\s+(\d+)',
                r'on\s+page\s+(\d+)',
            ],
            'implicit': [
                r'as\s+(?:we\s+)?(?:saw|discussed|learned|mentioned)\s+(?:earlier|before|previously|above)',
                r'(?:recall|remember)\s+(?:that|from)',
                r'(?:refer|referring)\s+(?:back\s+)?to',
                r'as\s+(?:noted|stated|explained)\s+(?:earlier|before|previously|above)',
            ]
        }

    def detect_references(self, text: str, chapter_num: int, source_id: str = None) -> List[Dict]:
        """
        Detect all references in text

        Args:
            text: Content text to analyze
            chapter_num: Current chapter number
            source_id: ID of source chunk/section

        Returns:
            List of detected references with context
        """

        references = []

        # Detect explicit references (Activity, Section, Figure, etc.)
        for ref_type, patterns in self.reference_patterns.items():
            if ref_type == 'implicit':
                # Handle implicit references separately
                continue

            for pattern in patterns:
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    ref_id = match.group(1)
                    context = self._extract_context(text, match.start(), match.end())

                    reference = {
                        'type': ref_type,
                        'target_id': self._normalize_reference_id(ref_type, ref_id, chapter_num),
                        'reference_text': match.group(0),
                        'context': context,
                        'position': match.start(),
                        'source_id': source_id,
                        'chapter': chapter_num
                    }

                    references.append(reference)

        # Detect implicit references
        implicit_refs = self._detect_implicit_references(text, source_id)
        references.extend(implicit_refs)

        return references

    def _normalize_reference_id(self, ref_type: str, ref_id: str, chapter_num: int) -> str:
        """Normalize reference ID to standard format"""

        if ref_type == 'activity':
            # Convert "1.1" or "1" to "activity_1.1" or "activity_1"
            if '.' not in ref_id:
                ref_id = f"{chapter_num}.{ref_id}"
            return f"activity_{ref_id}"

        elif ref_type == 'section':
            # Section ID is already in format "1.1"
            return ref_id

        elif ref_type == 'chapter':
            # Chapter ID is just the number
            return f"chapter_{ref_id}"

        elif ref_type == 'figure':
            # Convert to "fig_1.1" or "fig_1_1"
            return f"fig_{ref_id.replace('.', '_')}"

        elif ref_type == 'table':
            # Convert to "table_1.1" or "table_1_1"
            return f"table_{ref_id.replace('.', '_')}"

        elif ref_type == 'page':
            # Page reference
            return f"page_{ref_id}"

        return ref_id

    def _extract_context(self, text: str, start: int, end: int, window: int = 100) -> str:
        """Extract context around reference"""

        context_start = max(0, start - window)
        context_end = min(len(text), end + window)
        context = text[context_start:context_end]

        # Clean up context
        context = ' '.join(context.split())  # Normalize whitespace

        return context

    def _detect_implicit_references(self, text: str, source_id: str = None) -> List[Dict]:
        """Detect implicit references (as discussed earlier, etc.)"""

        implicit_refs = []

        for pattern in self.reference_patterns['implicit']:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                context = self._extract_context(text, match.start(), match.end(), window=150)

                reference = {
                    'type': 'implicit',
                    'target_id': None,  # Unknown target
                    'reference_text': match.group(0),
                    'context': context,
                    'position': match.start(),
                    'source_id': source_id,
                    'requires_resolution': True
                }

                implicit_refs.append(reference)

        return implicit_refs

    async def resolve_reference(
        self,
        reference: Dict,
        qdrant_client,
        collection_name: str
    ) -> Optional[Dict]:
        """
        Resolve reference to actual content

        Args:
            reference: Reference dict from detect_references()
            qdrant_client: Qdrant client instance
            collection_name: Collection to search

        Returns:
            Referenced content or None if not found
        """

        if not reference.get('target_id'):
            logger.warning("Cannot resolve reference without target_id")
            return None

        try:
            from qdrant_client.models import Filter, FieldCondition, MatchValue

            ref_type = reference['type']
            target_id = reference['target_id']

            # Build filter based on reference type
            if ref_type == 'activity':
                # Search for activity by toc_section_id
                filter_condition = Filter(
                    must=[
                        FieldCondition(
                            key="toc_section_id",
                            match=MatchValue(value=target_id)
                        ),
                        FieldCondition(
                            key="is_activity",
                            match=MatchValue(value=True)
                        )
                    ]
                )

            elif ref_type == 'section':
                # Search by section ID
                filter_condition = Filter(
                    must=[
                        FieldCondition(
                            key="toc_section_id",
                            match=MatchValue(value=target_id)
                        )
                    ]
                )

            elif ref_type in ['figure', 'table']:
                # Search in visual collection
                visual_collection = f"{collection_name}_visual"
                filter_condition = Filter(
                    must=[
                        FieldCondition(
                            key=f"{ref_type}_id",
                            match=MatchValue(value=target_id)
                        )
                    ]
                )
                collection_name = visual_collection

            else:
                logger.warning(f"Unsupported reference type for resolution: {ref_type}")
                return None

            # Search Qdrant
            search_results = qdrant_client.scroll(
                collection_name=collection_name,
                scroll_filter=filter_condition,
                limit=1,
                with_payload=True
            )

            points = search_results[0]

            if points:
                point = points[0]
                return {
                    'id': str(point.id),
                    'content': point.payload.get('content', ''),
                    'metadata': point.payload,
                    'reference': reference
                }

            return None

        except Exception as e:
            logger.error(f"Failed to resolve reference: {e}")
            return None

    def detect_all_references_in_chunks(self, chunks: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Detect references in all chunks

        Args:
            chunks: List of content chunks

        Returns:
            Dict mapping chunk_id to list of references
        """

        all_references = {}

        for chunk in chunks:
            chunk_id = chunk['id']
            content = chunk['content']
            chapter = chunk['metadata'].get('chapter_number', 1)

            references = self.detect_references(content, chapter, source_id=chunk_id)

            if references:
                all_references[chunk_id] = references

        logger.info(
            f"Detected {sum(len(refs) for refs in all_references.values())} "
            f"references across {len(all_references)} chunks"
        )

        return all_references

    def build_reference_map(self, all_references: Dict[str, List[Dict]]) -> Dict[str, List[str]]:
        """
        Build a map of content relationships

        Args:
            all_references: Output from detect_all_references_in_chunks()

        Returns:
            Dict mapping target_id to list of source_ids that reference it
        """

        reference_map = {}

        for source_id, references in all_references.items():
            for reference in references:
                target_id = reference.get('target_id')

                if not target_id:
                    continue

                if target_id not in reference_map:
                    reference_map[target_id] = []

                reference_map[target_id].append(source_id)

        logger.info(
            f"Built reference map with {len(reference_map)} targets "
            f"referenced by {sum(len(sources) for sources in reference_map.values())} sources"
        )

        return reference_map

    def get_referring_chunks(
        self,
        target_id: str,
        all_references: Dict[str, List[Dict]]
    ) -> List[Dict]:
        """
        Get all chunks that refer to a target

        Args:
            target_id: Target section/activity/figure ID
            all_references: Output from detect_all_references_in_chunks()

        Returns:
            List of references to the target
        """

        referring_chunks = []

        for source_id, references in all_references.items():
            for reference in references:
                if reference.get('target_id') == target_id:
                    referring_chunks.append({
                        'source_id': source_id,
                        'reference': reference
                    })

        return referring_chunks

    def generate_reference_report(self, all_references: Dict[str, List[Dict]]) -> str:
        """Generate human-readable reference report"""

        if not all_references:
            return "No references detected."

        lines = [
            "\n" + "="*60,
            "CROSS-REFERENCE ANALYSIS REPORT",
            "="*60,
            f"\nTotal chunks with references: {len(all_references)}",
            f"Total references detected: {sum(len(refs) for refs in all_references.values())}",
            "\n" + "-"*60,
            "REFERENCE BREAKDOWN BY TYPE",
            "-"*60
        ]

        # Count by type
        type_counts = {}
        for references in all_references.values():
            for ref in references:
                ref_type = ref['type']
                type_counts[ref_type] = type_counts.get(ref_type, 0) + 1

        for ref_type, count in sorted(type_counts.items(), key=lambda x: -x[1]):
            lines.append(f"  {ref_type.capitalize()}: {count}")

        lines.extend([
            "\n" + "-"*60,
            "SAMPLE REFERENCES",
            "-"*60
        ])

        # Show sample references
        sample_count = 0
        for source_id, references in list(all_references.items())[:5]:
            for ref in references[:2]:  # Max 2 per chunk
                lines.extend([
                    f"\nSource: {source_id}",
                    f"Type: {ref['type']}",
                    f"Target: {ref.get('target_id', 'Unknown')}",
                    f"Text: \"{ref['reference_text']}\"",
                    f"Context: {ref['context'][:100]}..."
                ])
                sample_count += 1
                if sample_count >= 10:
                    break
            if sample_count >= 10:
                break

        lines.append("\n" + "="*60 + "\n")

        return '\n'.join(lines)
