"""
Knowledge Graph
Builds and manages a graph of concept relationships from educational content
"""

import logging
from typing import Dict, List, Optional, Set, Tuple
import json

logger = logging.getLogger(__name__)

try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False
    logger.warning("NetworkX not available. Install with: pip install networkx")


class KnowledgeGraph:
    """Graph of educational concepts and their relationships"""

    def __init__(self):
        if not NETWORKX_AVAILABLE:
            raise ImportError("NetworkX is required. Install with: pip install networkx")

        self.graph = nx.DiGraph()  # Directed graph for prerequisite relationships
        self.concept_index = {}  # Map concept names to section IDs

    def build_from_toc(self, expanded_toc: Dict, references: Dict[str, List[Dict]] = None):
        """
        Build knowledge graph from TOC and detected references

        Args:
            expanded_toc: Expanded TOC with metadata
            references: Dict mapping source_id to list of references

        Nodes: sections, activities, concepts
        Edges: references, prerequisites, related_to
        """

        logger.info("Building knowledge graph from TOC...")

        # Add all sections as nodes
        for section in expanded_toc.get('sections', []):
            self._add_section_node(section)

        # Add edges from references
        if references:
            self._add_reference_edges(references)

        # Add conceptual relationships
        self._add_concept_relationships(expanded_toc)

        logger.info(
            f"Knowledge graph built: {self.graph.number_of_nodes()} nodes, "
            f"{self.graph.number_of_edges()} edges"
        )

    def _add_section_node(self, section: Dict):
        """Add a section as a node in the graph"""

        section_id = section['id']

        # Node attributes
        node_attrs = {
            'title': section.get('title', ''),
            'type': section.get('type', 'teaching_text'),
            'content_priority': section.get('content_priority', 'medium'),
            'difficulty_level': section.get('difficulty_level', 'beginner'),
            'cognitive_level': section.get('cognitive_level', 'understand'),
            'key_concepts': section.get('key_concepts', []),
            'learning_objectives': section.get('learning_objectives', []),
        }

        self.graph.add_node(section_id, **node_attrs)

        # Index concepts
        for concept in section.get('key_concepts', []):
            if concept not in self.concept_index:
                self.concept_index[concept] = []
            self.concept_index[concept].append(section_id)

    def _add_reference_edges(self, references: Dict[str, List[Dict]]):
        """Add edges from detected references"""

        for source_id, ref_list in references.items():
            for ref in ref_list:
                target_id = ref.get('target_id')

                if not target_id:
                    continue

                # Add edge if both nodes exist
                if self.graph.has_node(source_id) and self.graph.has_node(target_id):
                    self.graph.add_edge(
                        source_id,
                        target_id,
                        relationship='references',
                        ref_type=ref['type'],
                        context=ref.get('context', '')[:100]  # Truncate context
                    )

    def _add_concept_relationships(self, expanded_toc: Dict):
        """Add edges between sections with related concepts"""

        sections = expanded_toc.get('sections', [])

        for i, section1 in enumerate(sections):
            section1_id = section1['id']
            concepts1 = set(section1.get('key_concepts', []))

            for section2 in sections[i+1:]:
                section2_id = section2['id']
                concepts2 = set(section2.get('key_concepts', []))

                # Check for shared concepts
                shared_concepts = concepts1.intersection(concepts2)

                if shared_concepts:
                    # Add bidirectional "related_to" edge
                    self.graph.add_edge(
                        section1_id,
                        section2_id,
                        relationship='related_to',
                        shared_concepts=list(shared_concepts)
                    )
                    self.graph.add_edge(
                        section2_id,
                        section1_id,
                        relationship='related_to',
                        shared_concepts=list(shared_concepts)
                    )

    def get_related_sections(
        self,
        section_id: str,
        depth: int = 2,
        relationship_types: Optional[List[str]] = None
    ) -> List[str]:
        """
        Get all related sections within depth hops

        Args:
            section_id: Starting section ID
            depth: Maximum graph distance
            relationship_types: Filter by relationship types (references, related_to, etc.)

        Returns:
            List of related section IDs
        """

        if section_id not in self.graph:
            logger.warning(f"Section {section_id} not found in graph")
            return []

        related = []
        visited = {section_id}
        queue = [(section_id, 0)]

        while queue:
            node, d = queue.pop(0)

            if d >= depth:
                continue

            # Get neighbors
            for neighbor in self.graph.neighbors(node):
                if neighbor in visited:
                    continue

                # Check relationship type filter
                if relationship_types:
                    edge_data = self.graph.get_edge_data(node, neighbor)
                    if edge_data and edge_data.get('relationship') not in relationship_types:
                        continue

                visited.add(neighbor)
                related.append(neighbor)
                queue.append((neighbor, d + 1))

        return related

    def find_prerequisite_path(self, start: str, end: str) -> List[str]:
        """
        Find learning path from start to end concept

        Args:
            start: Start section ID
            end: End section ID

        Returns:
            List of section IDs forming a path, or empty list if no path exists
        """

        if start not in self.graph or end not in self.graph:
            return []

        try:
            path = nx.shortest_path(self.graph, start, end)
            return path
        except nx.NetworkXNoPath:
            logger.debug(f"No path found from {start} to {end}")
            return []

    def get_prerequisites(self, section_id: str) -> List[str]:
        """
        Get prerequisite sections (incoming edges)

        Args:
            section_id: Section ID

        Returns:
            List of section IDs that are prerequisites
        """

        if section_id not in self.graph:
            return []

        # Get incoming edges (prerequisites)
        predecessors = list(self.graph.predecessors(section_id))

        return predecessors

    def get_dependent_sections(self, section_id: str) -> List[str]:
        """
        Get sections that depend on this section (outgoing edges)

        Args:
            section_id: Section ID

        Returns:
            List of section IDs that depend on this section
        """

        if section_id not in self.graph:
            return []

        # Get outgoing edges (dependents)
        successors = list(self.graph.successors(section_id))

        return successors

    def find_sections_by_concept(self, concept: str) -> List[str]:
        """
        Find all sections that cover a specific concept

        Args:
            concept: Concept name (e.g., "photosynthesis")

        Returns:
            List of section IDs covering this concept
        """

        # Case-insensitive search
        concept_lower = concept.lower()

        matching_sections = []

        for indexed_concept, section_ids in self.concept_index.items():
            if concept_lower in indexed_concept.lower():
                matching_sections.extend(section_ids)

        return list(set(matching_sections))  # Remove duplicates

    def get_concept_cluster(self, concept: str, max_depth: int = 2) -> List[str]:
        """
        Get cluster of related sections around a concept

        Args:
            concept: Concept name
            max_depth: Maximum graph distance

        Returns:
            List of section IDs in the concept cluster
        """

        # Find sections with this concept
        seed_sections = self.find_sections_by_concept(concept)

        if not seed_sections:
            return []

        # Get related sections for each seed
        cluster = set(seed_sections)

        for section_id in seed_sections:
            related = self.get_related_sections(section_id, depth=max_depth)
            cluster.update(related)

        return list(cluster)

    def get_learning_sequence(
        self,
        start_section: str,
        target_concepts: List[str]
    ) -> List[str]:
        """
        Generate a learning sequence to cover target concepts

        Args:
            start_section: Starting section ID
            target_concepts: List of concepts to learn

        Returns:
            Ordered list of section IDs forming a learning sequence
        """

        if start_section not in self.graph:
            return []

        # Find sections covering target concepts
        target_sections = []
        for concept in target_concepts:
            sections = self.find_sections_by_concept(concept)
            target_sections.extend(sections)

        target_sections = list(set(target_sections))  # Remove duplicates

        # Build learning sequence using shortest paths
        sequence = [start_section]
        current = start_section

        for target in target_sections:
            if target == current:
                continue

            path = self.find_prerequisite_path(current, target)

            if path:
                # Add path (excluding current which is already in sequence)
                sequence.extend(path[1:])
                current = target

        return sequence

    def get_section_centrality(self) -> Dict[str, float]:
        """
        Calculate centrality scores for sections

        Returns:
            Dict mapping section_id to centrality score
        """

        try:
            # Use PageRank as centrality measure
            centrality = nx.pagerank(self.graph)
            return centrality
        except Exception as e:
            logger.error(f"Failed to calculate centrality: {e}")
            return {}

    def get_most_important_sections(self, limit: int = 10) -> List[Tuple[str, float]]:
        """
        Get most important sections based on centrality

        Args:
            limit: Maximum number of sections to return

        Returns:
            List of (section_id, centrality_score) tuples, sorted by score
        """

        centrality = self.get_section_centrality()

        if not centrality:
            return []

        # Sort by centrality score
        sorted_sections = sorted(
            centrality.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return sorted_sections[:limit]

    def export_graph(self, filepath: str, format: str = 'json'):
        """
        Export graph to file

        Args:
            filepath: Output file path
            format: Export format ('json', 'gexf', 'graphml')
        """

        try:
            if format == 'json':
                # Export to JSON
                data = nx.node_link_data(self.graph)
                with open(filepath, 'w') as f:
                    json.dump(data, f, indent=2)

            elif format == 'gexf':
                nx.write_gexf(self.graph, filepath)

            elif format == 'graphml':
                nx.write_graphml(self.graph, filepath)

            else:
                logger.error(f"Unsupported export format: {format}")
                return

            logger.info(f"Graph exported to {filepath} ({format})")

        except Exception as e:
            logger.error(f"Failed to export graph: {e}")

    def import_graph(self, filepath: str, format: str = 'json'):
        """
        Import graph from file

        Args:
            filepath: Input file path
            format: Import format ('json', 'gexf', 'graphml')
        """

        try:
            if format == 'json':
                with open(filepath, 'r') as f:
                    data = json.load(f)
                self.graph = nx.node_link_graph(data)

            elif format == 'gexf':
                self.graph = nx.read_gexf(filepath)

            elif format == 'graphml':
                self.graph = nx.read_graphml(filepath)

            else:
                logger.error(f"Unsupported import format: {format}")
                return

            # Rebuild concept index
            self._rebuild_concept_index()

            logger.info(f"Graph imported from {filepath} ({format})")

        except Exception as e:
            logger.error(f"Failed to import graph: {e}")

    def _rebuild_concept_index(self):
        """Rebuild concept index from graph nodes"""

        self.concept_index = {}

        for node_id, node_data in self.graph.nodes(data=True):
            concepts = node_data.get('key_concepts', [])

            for concept in concepts:
                if concept not in self.concept_index:
                    self.concept_index[concept] = []
                self.concept_index[concept].append(node_id)

    def get_graph_statistics(self) -> Dict:
        """Get graph statistics"""

        stats = {
            'num_nodes': self.graph.number_of_nodes(),
            'num_edges': self.graph.number_of_edges(),
            'num_concepts': len(self.concept_index),
            'density': nx.density(self.graph),
            'is_connected': nx.is_weakly_connected(self.graph),
        }

        # Get component info
        if not nx.is_weakly_connected(self.graph):
            components = list(nx.weakly_connected_components(self.graph))
            stats['num_components'] = len(components)
            stats['largest_component_size'] = len(max(components, key=len))

        return stats

    def visualize_subgraph(
        self,
        section_ids: List[str],
        output_file: str = None
    ) -> str:
        """
        Create a visualization of a subgraph

        Args:
            section_ids: List of section IDs to include
            output_file: Optional output file for visualization

        Returns:
            DOT format string for visualization
        """

        # Create subgraph
        subgraph = self.graph.subgraph(section_ids)

        # Generate DOT format
        lines = ['digraph KnowledgeGraph {']
        lines.append('  rankdir=LR;')  # Left to right layout
        lines.append('  node [shape=box];')

        # Add nodes
        for node_id, node_data in subgraph.nodes(data=True):
            label = node_data.get('title', node_id)
            node_type = node_data.get('type', 'unknown')
            lines.append(f'  "{node_id}" [label="{label}" color="{self._get_color_for_type(node_type)}"];')

        # Add edges
        for source, target, edge_data in subgraph.edges(data=True):
            relationship = edge_data.get('relationship', 'references')
            lines.append(f'  "{source}" -> "{target}" [label="{relationship}"];')

        lines.append('}')

        dot_string = '\n'.join(lines)

        if output_file:
            with open(output_file, 'w') as f:
                f.write(dot_string)
            logger.info(f"Subgraph visualization saved to {output_file}")

        return dot_string

    def _get_color_for_type(self, node_type: str) -> str:
        """Get color for node type"""

        colors = {
            'teaching_text': 'blue',
            'activity': 'green',
            'example': 'orange',
            'practice': 'purple',
        }

        return colors.get(node_type, 'gray')
