#!/usr/bin/env python3
"""
Test script for NCERT Class 6 Science RAG system
Tests the indexed chapters and shows what topics are covered
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.providers.rag.simple_rag import SimpleRAGProvider
from config.logger import setup_logging

logger = setup_logging()

def test_rag_queries():
    """Test various science queries against the RAG system"""
    
    # Initialize RAG provider
    rag_config = {
        'db_path': './rag_db',
        'collection_name': 'textbooks'
    }
    rag = SimpleRAGProvider(rag_config)
    
    # Get collection info
    info = rag.get_collection_info()
    print(f"\n=== RAG Collection Info ===")
    print(f"Total documents: {info['count']}")
    print(f"Collection name: {info['name']}")
    
    # Test queries for Class 6 Science
    test_queries = [
        "What is photosynthesis?",
        "Explain the water cycle",
        "What are living and non-living things?",
        "Components of food",
        "Parts of a plant",
        "How do plants make their food?",
        "What is respiration in plants?",
        "Types of nutrients in food",
        "What are vitamins and minerals?",
        "Characteristics of living organisms"
    ]
    
    print(f"\n=== Testing Class 6 Science Queries ===\n")
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        print("-" * 50)
        
        # Search in RAG
        results = rag.search(query, k=3)
        
        if results:
            print(f"Found {len(results)} relevant chunks:")
            for i, result in enumerate(results):
                doc = result.get('document', '')
                metadata = result.get('metadata', {})
                score = result.get('score', 0)
                
                print(f"\nResult {i+1} (Score: {score:.3f}):")
                print(f"Source: {metadata.get('source', 'Unknown')}")
                print(f"Page: {metadata.get('page', 'N/A')}")
                print(f"Grade: {metadata.get('grade', 'N/A')}")
                print(f"Subject: {metadata.get('subject', 'N/A')}")
                print(f"Content preview: {doc[:200]}...")
        else:
            print("No results found")

def analyze_indexed_content():
    """Analyze what content has been indexed from Class 6 Science"""
    
    rag_config = {
        'db_path': './rag_db',
        'collection_name': 'textbooks'
    }
    rag = SimpleRAGProvider(rag_config)
    
    print("\n=== Analyzing Indexed Class 6 Science Content ===\n")
    
    # Get all documents from Class 6 Science
    # Note: This is a simplified approach - in real implementation, 
    # you'd query specifically for Class-6 Science documents
    
    # Sample topics that might be covered based on NCERT Class 6 Science curriculum
    expected_topics = [
        "Chapter 1: Components of Food",
        "Chapter 2: Sorting Materials into Groups",
        "Plant structure and functions",
        "Living and non-living things",
        "Food and nutrition",
        "Water cycle and rain",
        "Air and its properties",
        "Light and shadows",
        "Electricity and circuits",
        "Magnets and magnetism"
    ]
    
    print("Expected topics in NCERT Class 6 Science (Curiosity):")
    for topic in expected_topics:
        print(f"  - {topic}")
    
    # Search for each topic to verify coverage
    print("\n=== Verifying Topic Coverage ===\n")
    
    topic_keywords = [
        "food components nutrients",
        "materials sorting groups",
        "plant parts roots stem leaves",
        "living non-living organisms",
        "water cycle evaporation",
        "air oxygen breathing",
        "light shadow reflection",
        "electric circuit battery",
        "magnet magnetic poles"
    ]
    
    for keywords in topic_keywords:
        results = rag.search(keywords, k=1)
        if results:
            print(f"✓ Found content for: {keywords}")
            metadata = results[0].get('metadata', {})
            print(f"  Source: {metadata.get('source', 'Unknown')}, Page: {metadata.get('page', 'N/A')}")
        else:
            print(f"✗ No content found for: {keywords}")

def explain_rag_system():
    """Explain how the RAG system works"""
    
    explanation = """
=== How the RAG System Works ===

1. **Document Processing**:
   - PDF files are read page by page
   - Text is extracted from each page
   - Large pages are split into smaller chunks (500 characters with 50 char overlap)
   - Each chunk retains metadata (page number, source file, subject, grade)

2. **Embedding Creation**:
   - Each text chunk is converted to a vector embedding
   - Uses sentence-transformers model (all-MiniLM-L6-v2)
   - Creates 384-dimensional vectors representing semantic meaning

3. **Storage in ChromaDB**:
   - Chunks and their embeddings are stored in ChromaDB
   - Metadata is preserved for filtering and reference
   - Allows fast similarity search

4. **Query Processing**:
   - User question is converted to embedding using same model
   - Similarity search finds most relevant chunks
   - Returns top-k results with scores

5. **Integration with LLM**:
   - Retrieved chunks provide context to the LLM
   - LLM generates answer based on retrieved content
   - Includes page references for verification

Example Flow:
User asks: "What is photosynthesis?"
→ Question embedded → Search finds chunks about photosynthesis from Chapter 1
→ LLM uses these chunks to explain photosynthesis in student-friendly language
"""
    
    print(explanation)

def main():
    """Run all tests"""
    
    # Explain how RAG works
    explain_rag_system()
    
    # Test queries
    test_rag_queries()
    
    # Analyze indexed content
    analyze_indexed_content()
    
    print("\n=== Test Complete ===")
    print("\nTo use in xiaozhi:")
    print("1. Restart the xiaozhi-server")
    print("2. Ask questions about Class 6 Science topics")
    print("3. The system will search the indexed textbook and provide answers")

if __name__ == "__main__":
    main()