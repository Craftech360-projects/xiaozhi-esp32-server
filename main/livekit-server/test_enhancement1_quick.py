"""
Quick Test for Enhancement 1 - Multi-Modal Support
Tests visual extraction and embedding generation
"""

import os
import sys
from pathlib import Path

# Set API key
os.environ['OPENAI_API_KEY'] = '***REMOVED***'

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

print("\n" + "="*80)
print("ENHANCEMENT 1 - QUICK TEST")
print("="*80)

# Test 1: Figure Extractor
print("\n[TEST 1] Testing FigureExtractor...")
try:
    from rag.figure_extractor import FigureExtractor

    extractor = FigureExtractor()
    print("  [OK] FigureExtractor initialized")

    # Test with Chapter 1 (smaller, faster)
    pdf_path = "scripts/grade_06_science/Chapter 1 The Wonderful World of Science.pdf"

    print(f"\n  Extracting from: {Path(pdf_path).name}")
    print("  (This may take 10-15 seconds...)")

    # Extract figures
    figures = extractor.extract_figures(pdf_path)
    print(f"\n  [OK] Extracted {len(figures)} figures")

    if figures:
        sample = figures[0]
        print(f"\n  Sample Figure:")
        print(f"    ID: {sample.get('figure_id')}")
        print(f"    Page: {sample.get('page')}")
        print(f"    Caption: {sample.get('caption', 'No caption')[:60]}")
        print(f"    Has image data: {sample.get('image_data') is not None}")

    # Extract tables
    print("\n  Extracting tables...")
    tables = extractor.extract_tables(pdf_path)
    print(f"  [OK] Extracted {len(tables)} tables")

    if tables:
        sample = tables[0]
        print(f"\n  Sample Table:")
        print(f"    ID: {sample.get('table_id')}")
        print(f"    Page: {sample.get('page')}")
        print(f"    Caption: {sample.get('caption', 'No caption')[:60]}")
        print(f"    Rows: {sample.get('row_count')}, Columns: {sample.get('column_count')}")

    test1_passed = True

except Exception as e:
    print(f"  [FAIL] Error: {e}")
    test1_passed = False

# Test 2: Visual Embedding Manager
print("\n[TEST 2] Testing VisualEmbeddingManager...")
try:
    from rag.visual_embeddings import VisualEmbeddingManager

    visual_manager = VisualEmbeddingManager()
    print("  [OK] VisualEmbeddingManager created")

    print("  Initializing CLIP model (this may take 30-60 seconds on first run)...")
    success = visual_manager.initialize()

    if success:
        print("  [OK] CLIP model initialized")
        print(f"  Model: {visual_manager.model_name}")
        print(f"  Device: {visual_manager.device}")
        print(f"  Embedding dim: {visual_manager.get_embedding_dim()}")
        test2_passed = True
    else:
        print("  [FAIL] CLIP initialization failed")
        test2_passed = False

except Exception as e:
    print(f"  [FAIL] Error: {e}")
    test2_passed = False

# Test 3: Visual Content Processing
print("\n[TEST 3] Testing Visual Content Processing...")
test3_passed = False

if test1_passed and test2_passed and len(tables) > 0:
    try:
        from rag.visual_embeddings import VisualContentProcessor
        import asyncio

        processor = VisualContentProcessor(visual_manager)
        print("  [OK] VisualContentProcessor created")

        # Process one table (faster than figures with images)
        print(f"\n  Processing {min(2, len(tables))} table(s)...")

        async def process_test():
            processed = await processor.process_tables(tables[:2])
            return processed

        processed_tables = asyncio.run(process_test())

        print(f"  [OK] Processed {len(processed_tables)} tables")

        if processed_tables:
            sample = processed_tables[0]
            embedding = sample.get('embedding')
            print(f"\n  Sample Processed Table:")
            print(f"    ID: {sample.get('table_id')}")
            print(f"    Type: {sample.get('type')}")
            print(f"    Has embedding: {embedding is not None}")
            if embedding:
                print(f"    Embedding dim: {len(embedding)}")
                print(f"    Embedding sample: [{embedding[0]:.4f}, {embedding[1]:.4f}, ..., {embedding[-1]:.4f}]")

        test3_passed = True

    except Exception as e:
        print(f"  [FAIL] Error: {e}")
        import traceback
        traceback.print_exc()

# Test 4: Qdrant Visual Collection
print("\n[TEST 4] Testing Qdrant Visual Collections...")
try:
    from rag.qdrant_manager import QdrantEducationManager
    import asyncio

    manager = QdrantEducationManager()
    print("  [OK] QdrantEducationManager created")

    async def test_visual_collection():
        # Check existing collections
        collections = await manager.get_existing_collections()
        print(f"  Existing collections: {len(collections)}")

        # Test creating visual collection
        test_collection = "test_visual_collection"
        if test_collection in collections:
            print(f"  Test collection already exists, skipping creation")
        else:
            success = await manager.create_visual_collection("test")
            if success:
                print(f"  [OK] Created visual collection: {test_collection}")
            else:
                print(f"  [FAIL] Failed to create visual collection")
                return False

        return True

    test4_passed = asyncio.run(test_visual_collection())

except Exception as e:
    print(f"  [FAIL] Error: {e}")
    test4_passed = False

# Test 5: Education Service Visual Search
print("\n[TEST 5] Testing Education Service Visual Search...")
try:
    from services.education_service import EducationService

    service = EducationService()
    print("  [OK] EducationService created")

    # Check if search_visual_content method exists
    if hasattr(service, 'search_visual_content'):
        print("  [OK] search_visual_content() method exists")
        test5_passed = True
    else:
        print("  [FAIL] search_visual_content() method not found")
        test5_passed = False

except Exception as e:
    print(f"  [FAIL] Error: {e}")
    test5_passed = False

# Final Summary
print("\n" + "="*80)
print("TEST SUMMARY")
print("="*80)

tests = [
    ("Visual Extraction (FigureExtractor)", test1_passed),
    ("CLIP Model (VisualEmbeddingManager)", test2_passed),
    ("Visual Processing (VisualContentProcessor)", test3_passed),
    ("Qdrant Visual Collections", test4_passed),
    ("Education Service Integration", test5_passed),
]

passed = sum(1 for _, result in tests if result)
total = len(tests)

print(f"\nTests Passed: {passed}/{total}")
print()

for test_name, result in tests:
    status = "[OK] PASS" if result else "[FAIL] FAIL"
    print(f"  {status}  {test_name}")

if passed == total:
    print(f"\n[SUCCESS] All tests passed! Enhancement 1 is working correctly.")
    print("\nComponents Ready:")
    if test1_passed:
        print(f"  - Visual extraction: {len(figures)} figures, {len(tables)} tables from Chapter 1")
    if test2_passed:
        print(f"  - CLIP embeddings: 512-dimensional vectors")
    if test3_passed:
        print(f"  - Visual processing: Ready for batch processing")
    if test4_passed:
        print(f"  - Qdrant storage: Visual collections ready")
    if test5_passed:
        print(f"  - Education service: Visual search integrated")
else:
    print(f"\n[WARN] {total - passed} test(s) failed. Review errors above.")

print("\n" + "="*80 + "\n")
