"""
Complete TOC-Guided RAG Pipeline with Multi-Modal Support (Enhancement 1)
Processes PDF textbooks with text + visual content (figures, tables)
"""

import asyncio
import os
import sys
import logging
from pathlib import Path
from typing import Dict, List

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
from rag.figure_extractor import FigureExtractor
from rag.visual_embeddings import VisualEmbeddingManager, VisualContentProcessor
from rag.embeddings import EmbeddingManager
from rag.qdrant_manager import QdrantEducationManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def process_textbook_with_visuals(
    pdf_path: str,
    collection_name: str = "grade_06_science",
    skip_existing: bool = False
) -> Dict:
    """
    Process textbook with complete TOC-guided pipeline + visual content

    Args:
        pdf_path: Path to PDF file
        collection_name: Qdrant collection name
        skip_existing: Skip if collection already has content

    Returns:
        Processing results with statistics
    """

    print("\n" + "="*80)
    print("TOC-GUIDED RAG PIPELINE WITH MULTI-MODAL SUPPORT")
    print("="*80)
    print(f"\nProcessing: {pdf_path}")
    print(f"Collection: {collection_name}")
    print("\n" + "="*80)

    # Initialize components
    print("\n[INIT] Initializing pipeline components...")

    pdf_extractor = PDFExtractor()
    toc_extractor = TOCExtractor()
    toc_expander = TOCExpander()
    chunker = SemanticChunker(min_chunk_size=400, max_chunk_size=800)
    validator = ChunkValidator(similarity_threshold=0.45)
    resolver = ReferenceResolver()
    knowledge_graph = KnowledgeGraph()

    # NEW: Visual content components
    figure_extractor = FigureExtractor()
    visual_manager = VisualEmbeddingManager()

    # Embedding and storage
    embedding_manager = EmbeddingManager()
    qdrant_manager = QdrantEducationManager()

    print("  [OK] All components initialized")

    # Initialize Qdrant collections
    print("\n[STEP 0] Setting up Qdrant collections...")

    existing_collections = await qdrant_manager.get_existing_collections()

    if collection_name not in existing_collections:
        # Create main collection
        await qdrant_manager.create_collection(collection_name, "science")
        print(f"  [OK] Created main collection: {collection_name}")
    else:
        print(f"  [OK] Collection {collection_name} already exists")

        if skip_existing:
            info = await qdrant_manager.get_collection_info(collection_name)
            if info and info.points_count > 0:
                print(f"  [SKIP] Collection already has {info.points_count} points, skipping...")
                return {"status": "skipped", "collection": collection_name}

    # NEW: Create visual collection
    visual_collection_name = f"{collection_name}_visual"
    await qdrant_manager.create_visual_collection(collection_name)
    print(f"  [OK] Visual collection ready: {visual_collection_name}")

    # Initialize embedding models
    print("\n[STEP 0.5] Loading embedding models...")
    await embedding_manager.initialize()
    print("  [OK] Text embedding model loaded (384-dim)")

    # NEW: Initialize CLIP model
    visual_manager.initialize()
    print("  [OK] CLIP visual model loaded (512-dim)")

    visual_processor = VisualContentProcessor(visual_manager)

    # Step 1: Extract PDF
    print(f"\n[STEP 1] Extracting PDF content...")
    pdf_data = pdf_extractor.extract_from_pdf(pdf_path)
    chapter_info = pdf_extractor.extract_chapter_info(pdf_path)

    print(f"  [OK] Extracted {len(pdf_data['pages'])} pages")
    print(f"  [OK] Chapter {chapter_info['chapter_number']}: {chapter_info['chapter_title']}")
    print(f"  [OK] Total text: {len(pdf_data['full_text'])} characters")

    # NEW: Step 1.5: Extract visual content
    print(f"\n[STEP 1.5] Extracting figures and tables...")

    figures = figure_extractor.extract_figures(pdf_path)
    tables = figure_extractor.extract_tables(pdf_path)

    print(f"  [OK] Extracted {len(figures)} figures")
    print(f"  [OK] Extracted {len(tables)} tables")

    if len(figures) + len(tables) > 0:
        print(f"\n  Visual Content Summary:")
        print(f"    - Total visual elements: {len(figures) + len(tables)}")

        # Sample first few
        if figures:
            print(f"\n    Sample Figures:")
            for fig in figures[:3]:
                print(f"      - {fig.get('figure_id')}: {fig.get('caption', 'No caption')[:60]}...")

        if tables:
            print(f"\n    Sample Tables:")
            for table in tables[:3]:
                print(f"      - {table.get('table_id')}: {table.get('caption', 'No caption')[:60]}...")

    # Step 2: Extract TOC
    print(f"\n[STEP 2] Extracting TOC structure...")
    toc = await toc_extractor.extract_toc(pdf_data['full_text'], chapter_info)

    print(f"  [OK] Extracted {len(toc['sections'])} TOC sections")

    print(f"\n  TOC Structure:")
    for i, section in enumerate(toc['sections'], 1):
        print(f"    {i}. [{section['type']}] {section['id']}: {section['title']}")

    # Step 3: Expand TOC with metadata
    print(f"\n[STEP 3] Expanding TOC with rich metadata...")
    expanded_toc = await toc_expander.expand_toc(toc, pdf_data['full_text'])

    print(f"  [OK] Expanded {len(expanded_toc['sections'])} sections with metadata")

    if expanded_toc['sections']:
        sample = expanded_toc['sections'][0]
        print(f"\n  Sample Metadata (Section {sample['id']}):")
        print(f"    - Key Concepts: {', '.join(sample.get('key_concepts', [])[:3])}")
        print(f"    - Difficulty: {sample.get('difficulty_level', 'N/A')}")
        print(f"    - Cognitive Level: {sample.get('cognitive_level', 'N/A')}")

    # Step 4: Create semantic chunks
    print(f"\n[STEP 4] Creating semantic chunks...")
    chunks = chunker.chunk_by_toc(pdf_data['full_text'], expanded_toc)

    print(f"  [OK] Created {len(chunks)} chunks")

    activity_chunks = [c for c in chunks if c['metadata']['is_activity']]
    teaching_chunks = [c for c in chunks if c['metadata']['section_type'] == 'teaching_text']

    print(f"  [OK] Activity chunks: {len(activity_chunks)}")
    print(f"  [OK] Teaching chunks: {len(teaching_chunks)}")

    # Step 5: Validate chunks
    print(f"\n[STEP 5] Validating chunks...")
    valid_chunks, flagged_chunks = await validator.validate_chunks(chunks, expanded_toc)

    validation_rate = len(valid_chunks) / len(chunks) * 100 if chunks else 0
    print(f"  [OK] Valid: {len(valid_chunks)}, Flagged: {len(flagged_chunks)}")
    print(f"  [OK] Validation rate: {validation_rate:.1f}%")

    # Step 6: Detect cross-references
    print(f"\n[STEP 6] Detecting cross-references...")
    references = resolver.detect_all_references_in_chunks(chunks)

    total_refs = sum(len(refs) for refs in references.values())
    print(f"  [OK] Detected {total_refs} references in {len(references)} chunks")

    # Count by type
    ref_types = {}
    for refs in references.values():
        for ref in refs:
            ref_type = ref['type']
            ref_types[ref_type] = ref_types.get(ref_type, 0) + 1

    if ref_types:
        print(f"\n  Reference breakdown:")
        for ref_type, count in sorted(ref_types.items(), key=lambda x: -x[1]):
            print(f"    - {ref_type}: {count}")

    # NEW: Step 6.5: Process visual content with embeddings
    print(f"\n[STEP 6.5] Generating visual embeddings...")

    processed_figures = await visual_processor.process_figures(figures)
    processed_tables = await visual_processor.process_tables(tables)

    visual_with_embeddings = [v for v in processed_figures + processed_tables if v.get('embedding')]

    print(f"  [OK] Generated {len(visual_with_embeddings)} visual embeddings")
    print(f"    - Figures: {len([v for v in processed_figures if v.get('embedding')])} / {len(figures)}")
    print(f"    - Tables: {len([v for v in processed_tables if v.get('embedding')])} / {len(tables)}")

    # Step 7: Generate text embeddings
    print(f"\n[STEP 7] Generating text embeddings...")

    chunks_with_embeddings = []
    batch_size = 32

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        texts = [chunk['content'] for chunk in batch]

        embeddings = await embedding_manager.embed_batch(texts)

        for chunk, embedding in zip(batch, embeddings):
            chunks_with_embeddings.append({
                "id": chunk['id'],
                "text_embedding": embedding,
                "payload": {
                    "content": chunk['content'],
                    "chapter_number": chunk['metadata']['chapter_number'],
                    "chapter": chunk['metadata']['chapter_title'],
                    "toc_section_id": chunk['metadata']['toc_section_id'],
                    "section_type": chunk['metadata']['section_type'],
                    "content_priority": chunk['metadata']['content_priority'],
                    "content_weight": chunk['metadata']['content_weight'],
                    "is_activity": chunk['metadata']['is_activity'],
                    "difficulty_level": chunk['metadata'].get('difficulty_level', 'beginner'),
                    "cognitive_level": chunk['metadata'].get('cognitive_level', 'understand'),
                    "key_concepts": chunk['metadata'].get('key_concepts', []),
                    "learning_objectives": chunk['metadata'].get('learning_objectives', []),
                    "page_number": chunk['metadata'].get('page_number', 0),
                }
            })

    print(f"  [OK] Generated {len(chunks_with_embeddings)} text embeddings")

    # NEW: Step 7.5: Store visual content in Qdrant
    print(f"\n[STEP 7.5] Storing visual content in Qdrant...")

    if visual_with_embeddings:
        success = await qdrant_manager.upsert_visual_content(
            visual_collection_name,
            visual_with_embeddings
        )

        if success:
            print(f"  [OK] Stored {len(visual_with_embeddings)} visual items")
        else:
            print(f"  [ERROR] Failed to store visual content")
    else:
        print(f"  [SKIP] No visual content to store")

    # Step 8: Store text content in Qdrant
    print(f"\n[STEP 8] Storing text content in Qdrant...")

    success = await qdrant_manager.upsert_content(
        collection_name,
        chunks_with_embeddings
    )

    if success:
        print(f"  [OK] Stored {len(chunks_with_embeddings)} text chunks")
    else:
        print(f"  [ERROR] Failed to store text content")

    # Step 9: Build knowledge graph
    print(f"\n[STEP 9] Building knowledge graph...")
    knowledge_graph.build_from_toc(expanded_toc, references)

    graph_stats = knowledge_graph.get_graph_statistics()
    print(f"  [OK] Graph built successfully")
    print(f"  [OK] Nodes: {graph_stats['num_nodes']}")
    print(f"  [OK] Edges: {graph_stats['num_edges']}")
    print(f"  [OK] Concepts: {graph_stats['num_concepts']}")
    print(f"  [OK] Density: {graph_stats['density']:.4f}")

    # Final summary
    print(f"\n" + "="*80)
    print("PROCESSING COMPLETE")
    print("="*80)

    print(f"\nText Content:")
    print(f"  - TOC sections: {len(expanded_toc['sections'])}")
    print(f"  - Chunks created: {len(chunks)}")
    print(f"  - Activities preserved: {len(activity_chunks)}")
    print(f"  - Cross-references: {total_refs}")
    print(f"  - Stored in: {collection_name}")

    print(f"\nVisual Content (NEW):")
    print(f"  - Figures extracted: {len(figures)}")
    print(f"  - Tables extracted: {len(tables)}")
    print(f"  - Visual embeddings: {len(visual_with_embeddings)}")
    print(f"  - Stored in: {visual_collection_name}")

    print(f"\nKnowledge Graph:")
    print(f"  - Nodes: {graph_stats['num_nodes']}")
    print(f"  - Edges: {graph_stats['num_edges']}")
    print(f"  - Concepts indexed: {graph_stats['num_concepts']}")

    print(f"\n" + "="*80 + "\n")

    return {
        "status": "success",
        "collection": collection_name,
        "visual_collection": visual_collection_name,
        "text_chunks": len(chunks),
        "visual_items": len(visual_with_embeddings),
        "figures": len(figures),
        "tables": len(tables),
        "toc_sections": len(expanded_toc['sections']),
        "activities": len(activity_chunks),
        "references": total_refs,
        "graph_stats": graph_stats
    }


async def main():
    """Process Grade 6 Science textbooks"""

    # Process Chapter 1
    result1 = await process_textbook_with_visuals(
        pdf_path="scripts/grade_06_science/Chapter 1 The Wonderful World of Science.pdf",
        collection_name="grade_06_science_ch1",
        skip_existing=False
    )

    # Process Chapter 2
    result2 = await process_textbook_with_visuals(
        pdf_path="scripts/grade_06_science/Chapter 2 Diversity in the Living World.pdf",
        collection_name="grade_06_science_ch2",
        skip_existing=False
    )

    print("\n" + "="*80)
    print("ALL CHAPTERS PROCESSED")
    print("="*80)

    print(f"\nChapter 1 Results:")
    print(f"  - Text chunks: {result1.get('text_chunks', 0)}")
    print(f"  - Visual items: {result1.get('visual_items', 0)}")
    print(f"  - Collection: {result1.get('collection', 'N/A')}")

    print(f"\nChapter 2 Results:")
    print(f"  - Text chunks: {result2.get('text_chunks', 0)}")
    print(f"  - Visual items: {result2.get('visual_items', 0)}")
    print(f"  - Collection: {result2.get('collection', 'N/A')}")

    print(f"\nCombined Statistics:")
    print(f"  - Total text chunks: {result1.get('text_chunks', 0) + result2.get('text_chunks', 0)}")
    print(f"  - Total visual items: {result1.get('visual_items', 0) + result2.get('visual_items', 0)}")
    print(f"  - Total figures: {result1.get('figures', 0) + result2.get('figures', 0)}")
    print(f"  - Total tables: {result1.get('tables', 0) + result2.get('tables', 0)}")

    print(f"\n" + "="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
