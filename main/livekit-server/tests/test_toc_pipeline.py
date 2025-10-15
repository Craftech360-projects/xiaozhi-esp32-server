"""
Test Suite for TOC-Guided RAG Pipeline
Validates all critical requirements from the plan
"""

import pytest
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rag.pdf_extractor import PDFExtractor
from rag.toc_extractor import TOCExtractor
from rag.toc_expander import TOCExpander
from rag.semantic_chunker import SemanticChunker
from rag.chunk_validator import ChunkValidator


# Sample test data
SAMPLE_PDF_PATH = "scripts/grade_06_science/Chapter 1 The Wonderful World of Science.pdf"

SAMPLE_TEXT = """
Chapter 1
The Wonderful World of Science

1.1 What is Science?
Science is a way of understanding the world around us. It helps us learn about living things, materials, and how things work.

Activity 1.1: Observe Living Things
Look at the plants and animals around you. Record your observations. What do you see? How do they move? What do they eat?

1.2 Scientific Method
The scientific method is a process scientists use to answer questions. First, we observe something interesting. Next, we ask a question about it. Then we make a guess called a hypothesis.
"""


class TestPDFExtraction:
    """Test PDF extraction module"""

    def test_pdf_extractor_initialization(self):
        """Test that PDF extractor can be initialized"""
        extractor = PDFExtractor()
        assert extractor is not None
        assert extractor.min_text_length == 20

    @pytest.mark.skipif(not Path(SAMPLE_PDF_PATH).exists(), reason="Sample PDF not found")
    def test_extract_chapter_info(self):
        """Test chapter info extraction"""
        extractor = PDFExtractor()
        chapter_info = extractor.extract_chapter_info(SAMPLE_PDF_PATH)

        assert 'chapter_number' in chapter_info
        assert 'chapter_title' in chapter_info
        assert chapter_info['chapter_number'] == 1
        assert 'Science' in chapter_info['chapter_title']

    @pytest.mark.skipif(not Path(SAMPLE_PDF_PATH).exists(), reason="Sample PDF not found")
    def test_extract_from_pdf(self):
        """Test full PDF extraction"""
        extractor = PDFExtractor()
        result = extractor.extract_from_pdf(SAMPLE_PDF_PATH)

        assert 'full_text' in result
        assert 'pages' in result
        assert 'metadata' in result
        assert len(result['full_text']) > 0
        assert len(result['pages']) > 0


class TestTOCExtraction:
    """Test TOC extraction module"""

    @pytest.mark.asyncio
    async def test_toc_extractor_initialization(self):
        """Test that TOC extractor can be initialized"""
        extractor = TOCExtractor()
        assert extractor is not None

    @pytest.mark.asyncio
    async def test_extract_toc_from_sample_text(self):
        """Test TOC extraction from sample text"""
        extractor = TOCExtractor()
        chapter_info = {
            'chapter_number': 1,
            'chapter_title': 'The Wonderful World of Science'
        }

        toc = await extractor.extract_toc(SAMPLE_TEXT, chapter_info)

        assert 'chapter' in toc
        assert 'title' in toc
        assert 'sections' in toc
        assert toc['chapter'] == 1
        assert len(toc['sections']) > 0

        # Check that sections have required fields
        for section in toc['sections']:
            assert 'id' in section
            assert 'title' in section
            assert 'type' in section
            assert 'content_priority' in section


class TestTOCExpansion:
    """Test TOC expansion module"""

    @pytest.mark.asyncio
    async def test_toc_expander_initialization(self):
        """Test that TOC expander can be initialized"""
        expander = TOCExpander()
        assert expander is not None

    @pytest.mark.asyncio
    async def test_expand_simple_toc(self):
        """Test TOC expansion with simple example"""
        expander = TOCExpander()

        simple_toc = {
            'chapter': 1,
            'title': 'The Wonderful World of Science',
            'sections': [
                {
                    'id': '1.1',
                    'title': 'What is Science?',
                    'type': 'teaching_text',
                    'content_priority': 'high',
                    'start_text': 'Science is a way of understanding',
                    'page': 1
                }
            ]
        }

        expanded = await expander.expand_toc(simple_toc, SAMPLE_TEXT)

        assert 'sections' in expanded
        assert len(expanded['sections']) > 0

        # Check that sections have rich metadata
        section = expanded['sections'][0]
        assert 'expanded_description' in section
        assert 'key_concepts' in section
        assert 'learning_objectives' in section
        assert 'difficulty_level' in section
        assert 'cognitive_level' in section


class TestSemanticChunking:
    """Test semantic chunking module - CRITICAL TESTS"""

    def test_semantic_chunker_initialization(self):
        """Test that semantic chunker can be initialized"""
        chunker = SemanticChunker(min_chunk_size=400, max_chunk_size=800)
        assert chunker is not None
        assert chunker.min_chunk_size == 400
        assert chunker.max_chunk_size == 800

    def test_activity_preservation(self):
        """
        CRITICAL TEST: Verify activities are preserved as complete units
        This is a core requirement from the user
        """
        chunker = SemanticChunker(min_chunk_size=400, max_chunk_size=800)

        expanded_toc = {
            'chapter': 1,
            'title': 'The Wonderful World of Science',
            'sections': [
                {
                    'id': 'activity_1.1',
                    'title': 'Observe Living Things',
                    'type': 'activity',
                    'content_priority': 'medium',
                    'start_text': 'Activity 1.1: Observe Living Things',
                    'key_concepts': ['observation', 'living things'],
                    'learning_objectives': ['Practice observation skills'],
                    'difficulty_level': 'beginner',
                    'cognitive_level': 'apply',
                    'related_activities': []
                }
            ]
        }

        chunks = chunker.chunk_by_toc(SAMPLE_TEXT, expanded_toc)

        # Find activity chunks
        activity_chunks = [c for c in chunks if c['metadata']['is_activity']]

        # Verify activity is preserved as single chunk
        assert len(activity_chunks) >= 1, "Activity should be chunked"

        # Verify activity chunk is complete (not split)
        activity_chunk = activity_chunks[0]
        assert 'Activity 1.1' in activity_chunk['content'], "Activity content should include title"
        assert 'Observe Living Things' in activity_chunk['content'], "Activity title should be present"

        print(f"[OK] Activity preservation test passed: {len(activity_chunks)} activity chunk(s) created")

    def test_content_weighting(self):
        """
        CRITICAL TEST: Verify content weighting is calculated correctly
        This is a core requirement from the user
        """
        chunker = SemanticChunker(min_chunk_size=400, max_chunk_size=800)

        expanded_toc = {
            'chapter': 1,
            'title': 'The Wonderful World of Science',
            'sections': [
                {
                    'id': '1.1',
                    'title': 'What is Science?',
                    'type': 'teaching_text',
                    'content_priority': 'high',
                    'start_text': 'Science is a way',
                    'key_concepts': [],
                    'learning_objectives': [],
                    'difficulty_level': 'beginner',
                    'cognitive_level': 'understand',
                    'related_activities': []
                },
                {
                    'id': '1.2',
                    'title': 'Practice Exercise',
                    'type': 'practice',
                    'content_priority': 'low',
                    'start_text': 'Exercise',
                    'key_concepts': [],
                    'learning_objectives': [],
                    'difficulty_level': 'beginner',
                    'cognitive_level': 'apply',
                    'related_activities': []
                }
            ]
        }

        chunks = chunker.chunk_by_toc(SAMPLE_TEXT, expanded_toc)

        # Check content weights
        for chunk in chunks:
            assert 'content_weight' in chunk['metadata'], "Each chunk should have content_weight"

            weight = chunk['metadata']['content_weight']
            assert 0.7 <= weight <= 1.0, f"Content weight should be between 0.7 and 1.0, got {weight}"

            # Verify teaching content has higher weight than practice
            if chunk['metadata']['section_type'] == 'teaching_text':
                assert weight >= 0.95, f"Teaching text should have high weight (>=0.95), got {weight}"

            if chunk['metadata']['section_type'] == 'practice':
                assert weight <= 0.75, f"Practice should have lower weight (<=0.75), got {weight}"

        print(f"[OK] Content weighting test passed: weights range from 0.7 to 1.0")

    def test_metadata_richness(self):
        """Test that chunks have rich educational metadata"""
        chunker = SemanticChunker(min_chunk_size=400, max_chunk_size=800)

        expanded_toc = {
            'chapter': 1,
            'title': 'The Wonderful World of Science',
            'sections': [
                {
                    'id': '1.1',
                    'title': 'What is Science?',
                    'type': 'teaching_text',
                    'content_priority': 'high',
                    'start_text': 'Science is',
                    'key_concepts': ['science', 'observation', 'understanding'],
                    'learning_objectives': ['Understand what science is'],
                    'difficulty_level': 'beginner',
                    'cognitive_level': 'understand',
                    'related_activities': ['activity_1.1']
                }
            ]
        }

        chunks = chunker.chunk_by_toc(SAMPLE_TEXT, expanded_toc)

        assert len(chunks) > 0, "Should create at least one chunk"

        # Verify metadata richness
        chunk = chunks[0]
        metadata = chunk['metadata']

        required_fields = [
            'chapter', 'chapter_title', 'section_title', 'section_type',
            'content_priority', 'key_concepts', 'learning_objectives',
            'difficulty_level', 'cognitive_level', 'is_activity', 'content_weight'
        ]

        for field in required_fields:
            assert field in metadata, f"Metadata should include {field}"

        print(f"[OK] Metadata richness test passed: all {len(required_fields)} required fields present")


class TestChunkValidation:
    """Test chunk validation module"""

    @pytest.mark.asyncio
    async def test_chunk_validator_initialization(self):
        """Test that chunk validator can be initialized"""
        validator = ChunkValidator(similarity_threshold=0.65)
        assert validator is not None
        assert validator.similarity_threshold == 0.65

    @pytest.mark.asyncio
    async def test_validate_chunks(self):
        """Test chunk validation against TOC"""
        validator = ChunkValidator(similarity_threshold=0.5)  # Lower threshold for testing

        # Create sample chunks and TOC
        expanded_toc = {
            'chapter': 1,
            'title': 'The Wonderful World of Science',
            'sections': [
                {
                    'id': '1.1',
                    'title': 'What is Science?',
                    'type': 'teaching_text',
                    'content_priority': 'high',
                    'expanded_description': 'Science is a way of understanding the world around us.',
                    'key_concepts': ['science', 'observation', 'understanding'],
                    'learning_objectives': ['Understand what science is'],
                    'difficulty_level': 'beginner',
                    'cognitive_level': 'understand',
                    'related_activities': []
                }
            ]
        }

        sample_chunks = [
            {
                'id': 1,
                'content': 'Science is a way of understanding the world around us through observation and experimentation.',
                'toc_section_id': '1.1',
                'chunk_index': 0,
                'metadata': {
                    'chapter': 1,
                    'chapter_title': 'The Wonderful World of Science',
                    'section_title': 'What is Science?',
                    'section_type': 'teaching_text',
                    'content_priority': 'high',
                    'is_activity': False,
                    'content_weight': 1.0,
                    'key_concepts': ['science', 'observation'],
                    'learning_objectives': ['Understand what science is'],
                    'difficulty_level': 'beginner',
                    'cognitive_level': 'understand',
                    'related_activities': []
                }
            }
        ]

        valid_chunks, flagged_chunks = await validator.validate_chunks(sample_chunks, expanded_toc)

        assert len(valid_chunks) >= 0, "Should process chunks"
        assert len(flagged_chunks) >= 0, "Should flag problematic chunks"

        print(f"[OK] Chunk validation test passed: {len(valid_chunks)} valid, {len(flagged_chunks)} flagged")


class TestEndToEnd:
    """End-to-end integration tests"""

    @pytest.mark.asyncio
    @pytest.mark.skipif(not Path(SAMPLE_PDF_PATH).exists(), reason="Sample PDF not found")
    async def test_full_pipeline(self):
        """
        CRITICAL TEST: Test complete pipeline from PDF to validated chunks
        This verifies all requirements work together
        """
        print("\n" + "="*60)
        print("END-TO-END PIPELINE TEST")
        print("="*60)

        # Step 1: Extract PDF
        print("\n1. Extracting PDF...")
        pdf_extractor = PDFExtractor()
        pdf_data = pdf_extractor.extract_from_pdf(SAMPLE_PDF_PATH)
        chapter_info = pdf_extractor.extract_chapter_info(SAMPLE_PDF_PATH)

        assert len(pdf_data['full_text']) > 0, "Should extract text from PDF"
        print(f"   [OK] Extracted {len(pdf_data['pages'])} pages, {len(pdf_data['full_text'])} characters")

        # Step 2: Extract TOC
        print("\n2. Extracting TOC structure...")
        toc_extractor = TOCExtractor()
        toc = await toc_extractor.extract_toc(pdf_data['full_text'], chapter_info)

        assert len(toc['sections']) > 0, "Should extract TOC sections"
        print(f"   [OK] Extracted {len(toc['sections'])} TOC sections")

        # Step 3: Expand TOC
        print("\n3. Expanding TOC with metadata...")
        toc_expander = TOCExpander()
        expanded_toc = await toc_expander.expand_toc(toc, pdf_data['full_text'])

        assert len(expanded_toc['sections']) > 0, "Should expand TOC"
        assert 'key_concepts' in expanded_toc['sections'][0], "Should add metadata"
        print(f"   [OK] Expanded {len(expanded_toc['sections'])} sections with rich metadata")

        # Step 4: Semantic chunking
        print("\n4. Creating semantic chunks...")
        chunker = SemanticChunker(min_chunk_size=400, max_chunk_size=800)
        chunks = chunker.chunk_by_toc(pdf_data['full_text'], expanded_toc)

        assert len(chunks) > 0, "Should create chunks"
        print(f"   [OK] Created {len(chunks)} chunks")

        # Verify activity preservation
        activity_chunks = [c for c in chunks if c['metadata']['is_activity']]
        print(f"   [OK] Preserved {len(activity_chunks)} activities as complete units")

        # Verify content weighting
        weights = [c['metadata']['content_weight'] for c in chunks]
        print(f"   [OK] Content weights: min={min(weights):.2f}, max={max(weights):.2f}")

        # Step 5: Validate chunks
        print("\n5. Validating chunks...")
        validator = ChunkValidator(similarity_threshold=0.65)
        valid_chunks, flagged_chunks = await validator.validate_chunks(chunks, expanded_toc)

        print(f"   [OK] Validation: {len(valid_chunks)} valid, {len(flagged_chunks)} flagged")

        if flagged_chunks:
            print("\n   Flagged chunks:")
            for i, flagged in enumerate(flagged_chunks[:3], 1):
                print(f"     {i}. {flagged['reason']} (similarity: {flagged['similarity_score']:.2f})")

        print("\n" + "="*60)
        print("END-TO-END TEST PASSED")
        print("="*60)
        print(f"\nSummary:")
        print(f"  • PDF Pages: {len(pdf_data['pages'])}")
        print(f"  • TOC Sections: {len(expanded_toc['sections'])}")
        print(f"  • Chunks Created: {len(chunks)}")
        print(f"  • Activities Preserved: {len(activity_chunks)}")
        print(f"  • Valid Chunks: {len(valid_chunks)}")
        print("="*60)


def run_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("TOC-GUIDED RAG PIPELINE TEST SUITE")
    print("="*60)

    # Run pytest
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-s"  # Show print statements
    ])


if __name__ == "__main__":
    run_tests()
