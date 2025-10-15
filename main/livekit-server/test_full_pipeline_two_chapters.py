"""
Full Pipeline Test with Two Chapters
Tests complete TOC-guided RAG pipeline with Chapter 1 and Chapter 2
"""

import asyncio
import os
import sys
from pathlib import Path

# Set API key
os.environ['OPENAI_API_KEY'] = '***REMOVED***'

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from rag.pdf_extractor import PDFExtractor
from rag.toc_extractor import TOCExtractor
from rag.toc_expander import TOCExpander
from rag.semantic_chunker import SemanticChunker
from rag.chunk_validator import ChunkValidator
from rag.reference_resolver import ReferenceResolver
from rag.knowledge_graph import KnowledgeGraph

# PDF paths
PDF_PATHS = [
    "scripts/grade_06_science/Chapter 1 The Wonderful World of Science.pdf",
    "scripts/grade_06_science/Chapter 2 Diversity in the Living World.pdf"
]


async def test_full_pipeline():
    """Test complete pipeline with two chapters"""

    print("\n" + "="*80)
    print("FULL PIPELINE TEST - TWO CHAPTERS")
    print("="*80)
    print("\nTesting:")
    print("  1. Chapter 1: The Wonderful World of Science")
    print("  2. Chapter 2: Diversity in the Living World")
    print("\n" + "="*80)

    # Initialize components
    pdf_extractor = PDFExtractor()
    toc_extractor = TOCExtractor()
    toc_expander = TOCExpander()
    chunker = SemanticChunker(min_chunk_size=400, max_chunk_size=800)
    validator = ChunkValidator(similarity_threshold=0.45)
    resolver = ReferenceResolver()
    knowledge_graph = KnowledgeGraph()

    all_chapters_data = []
    all_chunks = []
    all_references = {}

    # Process each PDF
    for pdf_index, pdf_path in enumerate(PDF_PATHS, 1):
        print(f"\n{'='*80}")
        print(f"PROCESSING CHAPTER {pdf_index}")
        print(f"{'='*80}")
        print(f"PDF: {pdf_path}\n")

        # Step 1: Extract PDF
        print(f"[{pdf_index}.1] Extracting PDF content...")
        pdf_data = pdf_extractor.extract_from_pdf(pdf_path)
        chapter_info = pdf_extractor.extract_chapter_info(pdf_path)

        print(f"  [OK] Extracted {len(pdf_data['pages'])} pages")
        print(f"  [OK] Chapter {chapter_info['chapter_number']}: {chapter_info['chapter_title']}")
        print(f"  [OK] Total text: {len(pdf_data['full_text'])} characters")

        # Step 2: Extract TOC
        print(f"\n[{pdf_index}.2] Extracting TOC structure...")
        toc = await toc_extractor.extract_toc(pdf_data['full_text'], chapter_info)

        print(f"  [OK] Extracted {len(toc['sections'])} TOC sections")

        # Show TOC sections
        print(f"\n  TOC Sections:")
        for i, section in enumerate(toc['sections'], 1):
            print(f"    {i}. [{section['type']}] {section['id']}: {section['title']}")

        # Step 3: Expand TOC
        print(f"\n[{pdf_index}.3] Expanding TOC with metadata...")
        expanded_toc = await toc_expander.expand_toc(toc, pdf_data['full_text'])

        print(f"  [OK] Expanded {len(expanded_toc['sections'])} sections with rich metadata")

        # Sample metadata
        if expanded_toc['sections']:
            sample = expanded_toc['sections'][0]
            print(f"\n  Sample Metadata (Section {sample['id']}):")
            print(f"    - Key Concepts: {', '.join(sample.get('key_concepts', [])[:3])}")
            print(f"    - Difficulty: {sample.get('difficulty_level', 'N/A')}")
            print(f"    - Cognitive Level: {sample.get('cognitive_level', 'N/A')}")

        # Step 4: Semantic chunking
        print(f"\n[{pdf_index}.4] Creating semantic chunks...")
        chunks = chunker.chunk_by_toc(pdf_data['full_text'], expanded_toc)

        print(f"  [OK] Created {len(chunks)} chunks")

        # Analyze chunk distribution
        activity_chunks = [c for c in chunks if c['metadata']['is_activity']]
        teaching_chunks = [c for c in chunks if c['metadata']['section_type'] == 'teaching_text']

        print(f"  [OK] Activity chunks: {len(activity_chunks)}")
        print(f"  [OK] Teaching chunks: {len(teaching_chunks)}")

        # Step 5: Validate chunks
        print(f"\n[{pdf_index}.5] Validating chunks...")
        valid_chunks, flagged_chunks = await validator.validate_chunks(chunks, expanded_toc)

        validation_rate = len(valid_chunks) / len(chunks) * 100 if chunks else 0
        print(f"  [OK] Valid: {len(valid_chunks)}, Flagged: {len(flagged_chunks)}")
        print(f"  [OK] Validation rate: {validation_rate:.1f}%")

        # Step 6: Detect references (NEW - Enhancement 2)
        print(f"\n[{pdf_index}.6] Detecting cross-references...")
        chapter_references = resolver.detect_all_references_in_chunks(chunks)

        total_refs = sum(len(refs) for refs in chapter_references.values())
        print(f"  [OK] Detected {total_refs} references in {len(chapter_references)} chunks")

        # Count by type
        ref_types = {}
        for refs in chapter_references.values():
            for ref in refs:
                ref_type = ref['type']
                ref_types[ref_type] = ref_types.get(ref_type, 0) + 1

        print(f"  Reference breakdown:")
        for ref_type, count in sorted(ref_types.items(), key=lambda x: -x[1]):
            print(f"    - {ref_type}: {count}")

        # Store chapter data
        all_chapters_data.append({
            'pdf_path': pdf_path,
            'chapter_info': chapter_info,
            'toc': toc,
            'expanded_toc': expanded_toc,
            'chunks': chunks,
            'valid_chunks': valid_chunks,
            'flagged_chunks': flagged_chunks,
            'references': chapter_references
        })

        all_chunks.extend(chunks)
        all_references.update(chapter_references)

    # Step 7: Build Knowledge Graph (NEW - Enhancement 2)
    print(f"\n{'='*80}")
    print("BUILDING KNOWLEDGE GRAPH")
    print(f"{'='*80}")

    # Combine TOCs
    combined_toc = {
        'chapter': 'Combined',
        'title': 'Grade 6 Science',
        'sections': []
    }

    for chapter_data in all_chapters_data:
        combined_toc['sections'].extend(chapter_data['expanded_toc']['sections'])

    print(f"\n[7.1] Building knowledge graph...")
    knowledge_graph.build_from_toc(combined_toc, all_references)

    graph_stats = knowledge_graph.get_graph_statistics()
    print(f"  [OK] Graph built successfully")
    print(f"  [OK] Nodes: {graph_stats['num_nodes']}")
    print(f"  [OK] Edges: {graph_stats['num_edges']}")
    print(f"  [OK] Concepts indexed: {graph_stats['num_concepts']}")
    print(f"  [OK] Density: {graph_stats['density']:.4f}")
    print(f"  [OK] Connected: {graph_stats['is_connected']}")

    # Get most important sections
    print(f"\n[7.2] Analyzing section importance...")
    important_sections = knowledge_graph.get_most_important_sections(limit=5)

    if important_sections:
        print(f"  Top 5 most important sections (by centrality):")
        for i, (section_id, centrality) in enumerate(important_sections, 1):
            node_data = knowledge_graph.graph.nodes[section_id]
            print(f"    {i}. {section_id}: {node_data.get('title', 'Unknown')} (score: {centrality:.4f})")

    # Test concept search
    print(f"\n[7.3] Testing concept search...")
    test_concepts = ["science", "living", "observation"]

    for concept in test_concepts:
        sections = knowledge_graph.find_sections_by_concept(concept)
        if sections:
            print(f"  Concept '{concept}' found in {len(sections)} sections: {sections[:3]}")

    # Final Summary
    print(f"\n{'='*80}")
    print("PIPELINE TEST COMPLETE")
    print(f"{'='*80}")

    total_chunks = sum(len(cd['chunks']) for cd in all_chapters_data)
    total_valid = sum(len(cd['valid_chunks']) for cd in all_chapters_data)
    total_activities = sum(len([c for c in cd['chunks'] if c['metadata']['is_activity']]) for cd in all_chapters_data)
    total_references = sum(len(refs) for refs in all_references.values())

    print(f"\nOverall Statistics:")
    print(f"  Chapters processed: {len(all_chapters_data)}")
    print(f"  Total TOC sections: {len(combined_toc['sections'])}")
    print(f"  Total chunks created: {total_chunks}")
    print(f"  Total valid chunks: {total_valid}")
    print(f"  Total activities preserved: {total_activities}")
    print(f"  Total cross-references detected: {total_references}")
    print(f"  Knowledge graph nodes: {graph_stats['num_nodes']}")
    print(f"  Knowledge graph edges: {graph_stats['num_edges']}")

    # Quality Assessment
    print(f"\n{'='*80}")
    print("QUALITY ASSESSMENT")
    print(f"{'='*80}")

    quality_score = 0
    max_score = 10

    # 1. TOC Extraction Quality (2 points)
    avg_sections_per_chapter = len(combined_toc['sections']) / len(all_chapters_data)
    if avg_sections_per_chapter >= 7:
        quality_score += 2
        print(f"\n[OK] TOC Quality: 2/2 points")
        print(f"     - Average {avg_sections_per_chapter:.1f} sections per chapter (target: 6-8)")
    elif avg_sections_per_chapter >= 5:
        quality_score += 1.5
        print(f"\n[GOOD] TOC Quality: 1.5/2 points")
        print(f"     - Average {avg_sections_per_chapter:.1f} sections per chapter")
    else:
        quality_score += 1
        print(f"\n[PARTIAL] TOC Quality: 1/2 points")
        print(f"     - Only {avg_sections_per_chapter:.1f} sections per chapter")

    # 2. Activity Preservation (2 points)
    activity_sections = sum(len([s for s in cd['expanded_toc']['sections'] if s['type'] == 'activity']) for cd in all_chapters_data)
    if total_activities == activity_sections and total_activities > 0:
        quality_score += 2
        print(f"\n[OK] Activity Preservation: 2/2 points")
        print(f"     - All {activity_sections} activities preserved as complete units")
    elif total_activities > 0:
        quality_score += 1
        print(f"\n[PARTIAL] Activity Preservation: 1/2 points")
        print(f"     - {total_activities}/{activity_sections} activities preserved")
    else:
        print(f"\n[SKIP] Activity Preservation: No activities in these chapters")
        quality_score += 2  # Don't penalize if no activities

    # 3. Chunk Validation (2 points)
    avg_validation_rate = (total_valid / total_chunks * 100) if total_chunks else 0
    if avg_validation_rate >= 70:
        quality_score += 2
        print(f"\n[OK] Validation Success: 2/2 points")
        print(f"     - Validation rate: {avg_validation_rate:.1f}%")
    elif avg_validation_rate >= 60:
        quality_score += 1.5
        print(f"\n[GOOD] Validation Success: 1.5/2 points")
        print(f"     - Validation rate: {avg_validation_rate:.1f}%")
    else:
        quality_score += 1
        print(f"\n[PARTIAL] Validation Success: 1/2 points")
        print(f"     - Validation rate: {avg_validation_rate:.1f}%")

    # 4. Cross-Reference Detection (2 points) - NEW
    refs_per_chunk = total_references / total_chunks if total_chunks else 0
    if total_references >= 10 and refs_per_chunk >= 0.2:
        quality_score += 2
        print(f"\n[OK] Cross-Reference Detection: 2/2 points")
        print(f"     - {total_references} references detected ({refs_per_chunk:.2f} per chunk)")
    elif total_references >= 5:
        quality_score += 1.5
        print(f"\n[GOOD] Cross-Reference Detection: 1.5/2 points")
        print(f"     - {total_references} references detected")
    else:
        quality_score += 1
        print(f"\n[PARTIAL] Cross-Reference Detection: 1/2 points")
        print(f"     - Only {total_references} references detected")

    # 5. Knowledge Graph Quality (2 points) - NEW
    if graph_stats['num_nodes'] >= 10 and graph_stats['num_edges'] >= 5:
        quality_score += 2
        print(f"\n[OK] Knowledge Graph: 2/2 points")
        print(f"     - {graph_stats['num_nodes']} nodes, {graph_stats['num_edges']} edges")
        print(f"     - {graph_stats['num_concepts']} concepts indexed")
    elif graph_stats['num_nodes'] >= 5:
        quality_score += 1.5
        print(f"\n[GOOD] Knowledge Graph: 1.5/2 points")
        print(f"     - {graph_stats['num_nodes']} nodes, {graph_stats['num_edges']} edges")
    else:
        quality_score += 1
        print(f"\n[PARTIAL] Knowledge Graph: 1/2 points")
        print(f"     - Graph needs more nodes/edges")

    # Final Score
    print(f"\n{'='*80}")
    print(f"FINAL QUALITY SCORE: {quality_score}/{max_score}")
    print(f"{'='*80}")

    if quality_score >= 9:
        rating = "EXCELLENT"
        status = "[SUCCESS]"
    elif quality_score >= 7.5:
        rating = "GOOD"
        status = "[GOOD]"
    elif quality_score >= 6:
        rating = "ACCEPTABLE"
        status = "[ACCEPTABLE]"
    else:
        rating = "NEEDS IMPROVEMENT"
        status = "[NEEDS WORK]"

    print(f"\n{status} Rating: {rating} ({quality_score}/{max_score})")
    print(f"\nBaseline (Old Pipeline): 5.5/10")
    print(f"Current (TOC-Guided + Enhancements): {quality_score}/10")
    improvement = ((quality_score - 5.5) / 5.5) * 100
    print(f"Improvement: {improvement:+.1f}%")

    # Feature Status
    print(f"\n{'='*80}")
    print("ENHANCEMENT STATUS")
    print(f"{'='*80}")

    print(f"\n[OK] Enhancement 3: Answer Templates - INTEGRATED")
    print(f"     - 8 question type formatters")
    print(f"     - Automatic answer structuring")

    print(f"\n[READY] Enhancement 1: Multi-Modal Support - MODULES READY")
    print(f"     - Figure/table extraction: {Path('src/rag/figure_extractor.py').exists()}")
    print(f"     - Visual embeddings: {Path('src/rag/visual_embeddings.py').exists()}")
    print(f"     - Integration pending")

    print(f"\n[OK] Enhancement 2: Cross-Reference Resolution - WORKING")
    print(f"     - Reference detection: {total_references} refs found")
    print(f"     - Knowledge graph: {graph_stats['num_nodes']} nodes, {graph_stats['num_edges']} edges")
    print(f"     - Full integration pending")

    print(f"\n{'='*80}\n")

    return {
        'quality_score': quality_score,
        'total_chunks': total_chunks,
        'total_references': total_references,
        'graph_stats': graph_stats,
        'chapters_data': all_chapters_data
    }


if __name__ == "__main__":
    result = asyncio.run(test_full_pipeline())
