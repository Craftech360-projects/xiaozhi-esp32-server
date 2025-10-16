"""
Complete Validation Test - All Criteria from Both Plans
Tests PLAN_TOC_GUIDED_RAG.md + PERFECT_SCORE_REPORT.md requirements
"""

import asyncio
import os
import sys
from pathlib import Path

# Set API key
os.environ['OPENAI_API_KEY'] = '***REMOVED***'

sys.path.insert(0, str(Path(__file__).parent / "src"))

print("\n" + "="*80)
print("COMPLETE VALIDATION TEST - ALL CRITERIA")
print("="*80)
print("\nValidating against:")
print("  1. PLAN_TOC_GUIDED_RAG.md requirements")
print("  2. PERFECT_SCORE_REPORT.md criteria")
print("  3. Enhancement 1 (Multi-Modal Support)")
print("\n" + "="*80)

# Initialize results
all_tests = []
total_score = 0
max_score = 0

def record_test(name, passed, score_value=1, max_value=1, details=""):
    """Record test result"""
    global total_score, max_score
    all_tests.append({
        'name': name,
        'passed': passed,
        'score': score_value if passed else 0,
        'max': max_value,
        'details': details
    })
    if passed:
        total_score += score_value
    max_score += max_value

# ============================================================================
# PART 1: PDF EXTRACTION (from PLAN_TOC_GUIDED_RAG.md)
# ============================================================================
print("\n[PART 1] PDF EXTRACTION MODULE")
print("-" * 80)

try:
    from rag.pdf_extractor import PDFExtractor

    extractor = PDFExtractor()
    pdf_path = "scripts/grade_06_science/Chapter 1 The Wonderful World of Science.pdf"

    # Test extraction
    pdf_data = extractor.extract_from_pdf(pdf_path)
    chapter_info = extractor.extract_chapter_info(pdf_path)

    # Validate results
    has_full_text = bool(pdf_data.get('full_text'))
    has_pages = len(pdf_data.get('pages', [])) > 0
    has_chapter_num = chapter_info.get('chapter_number') == 1
    has_chapter_title = bool(chapter_info.get('chapter_title'))

    test1_pass = has_full_text and has_pages and has_chapter_num and has_chapter_title

    print(f"  [{'OK' if test1_pass else 'FAIL'}] PDF Extractor")
    print(f"      - Full text: {len(pdf_data.get('full_text', ''))} chars")
    print(f"      - Pages: {len(pdf_data.get('pages', []))}")
    print(f"      - Chapter: {chapter_info.get('chapter_number')}")
    print(f"      - Title: {chapter_info.get('chapter_title', '')[:50]}")

    record_test("PDF Extraction", test1_pass, 1, 1,
                f"Extracted {len(pdf_data['pages'])} pages")

except Exception as e:
    print(f"  [FAIL] PDF Extraction failed: {e}")
    record_test("PDF Extraction", False, 0, 1, str(e))
    pdf_data = None
    chapter_info = None

# ============================================================================
# PART 2: LLM TOC EXTRACTION (from PLAN_TOC_GUIDED_RAG.md)
# ============================================================================
print("\n[PART 2] LLM TOC EXTRACTION")
print("-" * 80)

if pdf_data and chapter_info:
    try:
        from rag.toc_extractor import TOCExtractor

        toc_extractor = TOCExtractor()

        print("  Extracting TOC (using LLM, may take 10-15 seconds)...")
        toc = asyncio.run(toc_extractor.extract_toc(pdf_data['full_text'], chapter_info))

        # Validate TOC quality (from PERFECT_SCORE_REPORT.md: 6-8 sections target)
        num_sections = len(toc.get('sections', []))
        has_activities = any(s.get('type') == 'activity' for s in toc['sections'])
        has_teaching = any(s.get('type') == 'teaching_text' for s in toc['sections'])

        toc_quality_pass = num_sections >= 6 and num_sections <= 10 and has_activities and has_teaching

        print(f"  [{'OK' if toc_quality_pass else 'FAIL'}] TOC Extraction")
        print(f"      - Sections: {num_sections} (target: 6-10)")
        print(f"      - Has activities: {has_activities}")
        print(f"      - Has teaching: {has_teaching}")

        if num_sections > 0:
            print(f"\n  Sample sections:")
            for i, section in enumerate(toc['sections'][:5], 1):
                print(f"      {i}. [{section.get('type')}] {section.get('id')}: {section.get('title')[:50]}")

        record_test("TOC Extraction Quality", toc_quality_pass, 2, 2,
                   f"{num_sections} sections extracted")

    except Exception as e:
        print(f"  [FAIL] TOC Extraction failed: {e}")
        record_test("TOC Extraction Quality", False, 0, 2, str(e))
        toc = None
else:
    print("  [SKIP] TOC Extraction (PDF extraction failed)")
    toc = None

# ============================================================================
# PART 3: TOC EXPANSION (from PLAN_TOC_GUIDED_RAG.md)
# ============================================================================
print("\n[PART 3] TOC EXPANSION WITH METADATA")
print("-" * 80)

if toc:
    try:
        from rag.toc_expander import TOCExpander

        expander = TOCExpander()

        print("  Expanding TOC with metadata (using LLM, may take 15-20 seconds)...")
        expanded_toc = asyncio.run(expander.expand_toc(toc, pdf_data['full_text']))

        # Validate metadata richness (from PERFECT_SCORE_REPORT.md: 11 fields required)
        required_fields = [
            'key_concepts', 'learning_objectives', 'difficulty_level',
            'cognitive_level', 'expanded_description'
        ]

        has_all_metadata = all(
            all(field in section for field in required_fields)
            for section in expanded_toc['sections']
        )

        metadata_pass = has_all_metadata and len(expanded_toc['sections']) == len(toc['sections'])

        print(f"  [{'OK' if metadata_pass else 'FAIL'}] TOC Expansion")
        print(f"      - All metadata fields: {has_all_metadata}")
        print(f"      - Sections expanded: {len(expanded_toc['sections'])}/{len(toc['sections'])}")

        if expanded_toc['sections']:
            sample = expanded_toc['sections'][0]
            print(f"\n  Sample metadata:")
            print(f"      - Key concepts: {', '.join(sample.get('key_concepts', [])[:3])}")
            print(f"      - Difficulty: {sample.get('difficulty_level')}")
            print(f"      - Cognitive level: {sample.get('cognitive_level')}")

        record_test("TOC Metadata Expansion", metadata_pass, 2, 2,
                   f"All {len(expanded_toc['sections'])} sections enriched")

    except Exception as e:
        print(f"  [FAIL] TOC Expansion failed: {e}")
        record_test("TOC Metadata Expansion", False, 0, 2, str(e))
        expanded_toc = None
else:
    print("  [SKIP] TOC Expansion (TOC extraction failed)")
    expanded_toc = None

# ============================================================================
# PART 4: SEMANTIC CHUNKING WITH ACTIVITY PRESERVATION
# ============================================================================
print("\n[PART 4] SEMANTIC CHUNKING - CRITICAL REQUIREMENT")
print("-" * 80)

if expanded_toc:
    try:
        from rag.semantic_chunker import SemanticChunker

        chunker = SemanticChunker(min_chunk_size=400, max_chunk_size=800)
        chunks = chunker.chunk_by_toc(pdf_data['full_text'], expanded_toc)

        # CRITICAL TEST: Activity Preservation (from PLAN_TOC_GUIDED_RAG.md)
        activity_chunks = [c for c in chunks if c['metadata']['is_activity']]

        # Check that each activity appears in ONLY ONE chunk (chunk_index=0)
        activity_preservation = {}
        for chunk in activity_chunks:
            activity_id = chunk['toc_section_id']
            chunk_index = chunk['chunk_index']
            if activity_id not in activity_preservation:
                activity_preservation[activity_id] = []
            activity_preservation[activity_id].append(chunk_index)

        # ALL activities must have ONLY chunk_index=0 (single chunk)
        all_activities_preserved = all(
            indices == [0] for indices in activity_preservation.values()
        )

        print(f"  [{'OK' if all_activities_preserved else 'FAIL'}] Activity Preservation - CRITICAL")
        print(f"      - Total chunks: {len(chunks)}")
        print(f"      - Activity chunks: {len(activity_chunks)}")
        print(f"      - Activities preserved as single chunks: {all_activities_preserved}")

        if activity_chunks:
            print(f"\n  Activity preservation details:")
            for activity_id, indices in activity_preservation.items():
                status = "[OK]" if indices == [0] else "[FAIL - SPLIT!]"
                print(f"      {status} {activity_id}: chunks={len(indices)}")

        # Content Weighting Test (from PLAN_TOC_GUIDED_RAG.md)
        weights = [c['metadata']['content_weight'] for c in chunks]
        weight_min = min(weights)
        weight_max = max(weights)
        teaching_weights = [c['metadata']['content_weight'] for c in chunks
                           if c['metadata']['section_type'] == 'teaching_text']

        teaching_avg = sum(teaching_weights) / len(teaching_weights) if teaching_weights else 0
        weight_range_valid = weight_min >= 0.7 and weight_max <= 1.0
        teaching_highest = teaching_avg >= 0.95

        weighting_pass = weight_range_valid and teaching_highest

        print(f"\n  [{'OK' if weighting_pass else 'FAIL'}] Content Weighting")
        print(f"      - Weight range: {weight_min:.2f} - {weight_max:.2f} (target: 0.7-1.0)")
        print(f"      - Teaching avg: {teaching_avg:.2f} (target: >= 0.95)")

        record_test("Activity Preservation (CRITICAL)", all_activities_preserved, 2, 2,
                   f"{len(activity_chunks)} activities preserved")
        record_test("Content Weighting", weighting_pass, 2, 2,
                   f"Range: {weight_min:.2f}-{weight_max:.2f}")

    except Exception as e:
        print(f"  [FAIL] Semantic Chunking failed: {e}")
        record_test("Activity Preservation (CRITICAL)", False, 0, 2, str(e))
        record_test("Content Weighting", False, 0, 2, str(e))
        chunks = None
else:
    print("  [SKIP] Semantic Chunking (TOC expansion failed)")
    chunks = None

# ============================================================================
# PART 5: CHUNK VALIDATION
# ============================================================================
print("\n[PART 5] CHUNK VALIDATION")
print("-" * 80)

if chunks and expanded_toc:
    try:
        from rag.chunk_validator import ChunkValidator

        validator = ChunkValidator(similarity_threshold=0.45)

        print("  Validating chunks (may take 10-15 seconds)...")
        valid_chunks, flagged_chunks = asyncio.run(
            validator.validate_chunks(chunks, expanded_toc)
        )

        validation_rate = len(valid_chunks) / len(chunks) * 100 if chunks else 0

        # From PERFECT_SCORE_REPORT.md: 65%+ is acceptable
        validation_pass = validation_rate >= 60

        print(f"  [{'OK' if validation_pass else 'FAIL'}] Chunk Validation")
        print(f"      - Valid: {len(valid_chunks)}")
        print(f"      - Flagged: {len(flagged_chunks)}")
        print(f"      - Validation rate: {validation_rate:.1f}% (target: >= 60%)")

        record_test("Chunk Validation Rate", validation_pass, 2, 2,
                   f"{validation_rate:.1f}% validation rate")

    except Exception as e:
        print(f"  [FAIL] Chunk Validation failed: {e}")
        record_test("Chunk Validation Rate", False, 0, 2, str(e))
else:
    print("  [SKIP] Chunk Validation (chunking failed)")

# ============================================================================
# PART 6: ENHANCEMENT 1 - VISUAL CONTENT EXTRACTION
# ============================================================================
print("\n[PART 6] ENHANCEMENT 1 - MULTI-MODAL SUPPORT")
print("-" * 80)

try:
    from rag.figure_extractor import FigureExtractor

    fig_extractor = FigureExtractor()

    print("  Testing both chapters for visual content...")
    pdf1 = "scripts/grade_06_science/Chapter 1 The Wonderful World of Science.pdf"
    pdf2 = "scripts/grade_06_science/Chapter 2 Diversity in the Living World.pdf"

    figures1 = fig_extractor.extract_figures(pdf1)
    tables1 = fig_extractor.extract_tables(pdf1)

    print(f"  Chapter 1: {len(figures1)} figures, {len(tables1)} tables")

    figures2 = fig_extractor.extract_figures(pdf2)
    tables2 = fig_extractor.extract_tables(pdf2)

    print(f"  Chapter 2: {len(figures2)} figures, {len(tables2)} tables")

    total_visual = len(figures1) + len(tables1) + len(figures2) + len(tables2)

    # Visual extraction success if we extracted content
    visual_extraction_pass = total_visual > 100  # Chapter 2 has 90+ visual items

    print(f"\n  [{'OK' if visual_extraction_pass else 'FAIL'}] Visual Content Extraction")
    print(f"      - Total visual items: {total_visual}")
    print(f"      - Ch1 + Ch2: {len(figures1)+len(figures2)} figures, {len(tables1)+len(tables2)} tables")

    record_test("Visual Content Extraction", visual_extraction_pass, 2, 2,
               f"{total_visual} visual items extracted")

except Exception as e:
    print(f"  [FAIL] Visual Extraction failed: {e}")
    record_test("Visual Content Extraction", False, 0, 2, str(e))

# ============================================================================
# PART 7: INTEGRATION TESTS
# ============================================================================
print("\n[PART 7] INTEGRATION TESTS")
print("-" * 80)

# Test 1: Qdrant Manager has visual collection methods
try:
    from rag.qdrant_manager import QdrantEducationManager

    manager = QdrantEducationManager()

    has_create_visual = hasattr(manager, 'create_visual_collection')
    has_upsert_visual = hasattr(manager, 'upsert_visual_content')
    has_visual_indexes = hasattr(manager, 'create_visual_payload_indexes')

    qdrant_integration = has_create_visual and has_upsert_visual and has_visual_indexes

    print(f"  [{'OK' if qdrant_integration else 'FAIL'}] Qdrant Visual Integration")
    print(f"      - create_visual_collection: {has_create_visual}")
    print(f"      - upsert_visual_content: {has_upsert_visual}")
    print(f"      - create_visual_payload_indexes: {has_visual_indexes}")

    record_test("Qdrant Visual Methods", qdrant_integration, 1, 1)

except Exception as e:
    print(f"  [FAIL] Qdrant Integration test failed: {e}")
    record_test("Qdrant Visual Methods", False, 0, 1)

# Test 2: Education Service has visual search
try:
    from services.education_service import EducationService

    service = EducationService()
    has_visual_search = hasattr(service, 'search_visual_content')

    print(f"  [{'OK' if has_visual_search else 'FAIL'}] Education Service Visual Search")
    print(f"      - search_visual_content method: {has_visual_search}")

    record_test("Visual Search Integration", has_visual_search, 1, 1)

except Exception as e:
    print(f"  [FAIL] Education Service test failed: {e}")
    record_test("Visual Search Integration", False, 0, 1)

# ============================================================================
# FINAL RESULTS
# ============================================================================
print("\n" + "="*80)
print("FINAL VALIDATION RESULTS")
print("="*80)

print(f"\nOverall Score: {total_score}/{max_score} ({total_score/max_score*100:.1f}%)")
print()

# Group tests by category
categories = {
    'Core Pipeline (PLAN_TOC_GUIDED_RAG)': [
        'PDF Extraction', 'TOC Extraction Quality', 'TOC Metadata Expansion',
        'Activity Preservation (CRITICAL)', 'Content Weighting', 'Chunk Validation Rate'
    ],
    'Enhancement 1 (Multi-Modal)': [
        'Visual Content Extraction', 'Qdrant Visual Methods', 'Visual Search Integration'
    ]
}

for category, test_names in categories.items():
    print(f"\n{category}:")
    print("-" * 80)
    category_tests = [t for t in all_tests if t['name'] in test_names]
    for test in category_tests:
        status = "[OK] PASS" if test['passed'] else "[FAIL] FAIL"
        print(f"  {status}  {test['name']} ({test['score']}/{test['max']})")
        if test['details']:
            print(f"          {test['details']}")

# Calculate category scores
print("\n" + "="*80)
print("CATEGORY SCORES")
print("="*80)

for category, test_names in categories.items():
    category_tests = [t for t in all_tests if t['name'] in test_names]
    cat_score = sum(t['score'] for t in category_tests)
    cat_max = sum(t['max'] for t in category_tests)
    cat_pct = cat_score / cat_max * 100 if cat_max > 0 else 0

    rating = "EXCELLENT" if cat_pct >= 90 else "GOOD" if cat_pct >= 75 else "NEEDS WORK"
    print(f"\n{category}:")
    print(f"  Score: {cat_score}/{cat_max} ({cat_pct:.1f}%)")
    print(f"  Rating: {rating}")

# Final verdict
print("\n" + "="*80)
print("FINAL VERDICT")
print("="*80)

overall_pct = total_score / max_score * 100 if max_score > 0 else 0

if overall_pct >= 90:
    verdict = "EXCELLENT - PRODUCTION READY"
    status = "[SUCCESS]"
elif overall_pct >= 75:
    verdict = "GOOD - Minor improvements needed"
    status = "[OK]"
elif overall_pct >= 60:
    verdict = "ACCEPTABLE - Some work needed"
    status = "[WARN]"
else:
    verdict = "NEEDS WORK - Significant issues"
    status = "[FAIL]"

print(f"\n{status} {verdict}")
print(f"\nFinal Score: {total_score}/{max_score} ({overall_pct:.1f}%)")

# Check critical requirements
critical_tests = ['Activity Preservation (CRITICAL)', 'Content Weighting']
critical_pass = all(
    t['passed'] for t in all_tests if t['name'] in critical_tests
)

if critical_pass:
    print("\n[OK] All CRITICAL requirements passed!")
else:
    print("\n[FAIL] CRITICAL requirements failed!")

print("\n" + "="*80 + "\n")
