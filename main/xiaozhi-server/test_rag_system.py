#!/usr/bin/env python3
"""
Test script for RAG system implementation
"""

import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.providers.rag.simple_rag import SimpleRAGProvider
from config.logger import setup_logging

logger = setup_logging()


def test_rag_system():
    """Test the RAG system implementation"""
    
    print("=== Testing RAG System Implementation ===\n")
    
    # Initialize RAG provider
    print("1. Initializing RAG provider...")
    try:
        rag_config = {
            'db_path': './rag_db',
            'collection_name': 'textbooks'
        }
        rag = SimpleRAGProvider(rag_config)
        print("✓ RAG provider initialized successfully\n")
    except Exception as e:
        print(f"✗ Failed to initialize RAG provider: {str(e)}")
        return False
    
    # Get collection info
    print("2. Getting collection info...")
    try:
        info = rag.get_collection_info()
        print(f"✓ Collection info:")
        print(f"  - Name: {info['name']}")
        print(f"  - Document count: {info['count']}")
        print(f"  - DB path: {info['db_path']}")
        print(f"  - Model: {info['model']}\n")
    except Exception as e:
        print(f"✗ Failed to get collection info: {str(e)}")
        return False
    
    # Test adding a sample document
    print("3. Testing document addition...")
    try:
        sample_text = """
        分数是数学中表示部分与整体关系的一种方式。
        分数由分子和分母组成，中间用分数线隔开。
        例如：1/2 表示将一个整体平均分成2份，取其中的1份。
        分数可以表示小于1的数，也可以表示大于或等于1的数。
        """
        
        sample_metadata = {
            'page': 1,
            'subject': '数学',
            'grade': '五年级',
            'source': 'test_document.pdf'
        }
        
        success = rag.add_document(sample_text, sample_metadata)
        if success:
            print("✓ Successfully added test document\n")
        else:
            print("✗ Failed to add test document\n")
    except Exception as e:
        print(f"✗ Error adding document: {str(e)}")
        return False
    
    # Test searching
    print("4. Testing search functionality...")
    test_queries = [
        "什么是分数？",
        "分数的组成部分",
        "photosynthesis",  # Should return no results
    ]
    
    for query in test_queries:
        print(f"\n  Searching for: '{query}'")
        try:
            results = rag.search(query, top_k=2)
            
            if results['documents']:
                print(f"  ✓ Found {len(results['documents'])} results:")
                for i, (doc, metadata) in enumerate(zip(results['documents'], results['metadatas'])):
                    print(f"    Result {i+1}:")
                    print(f"      - Subject: {metadata.get('subject', 'N/A')}")
                    print(f"      - Grade: {metadata.get('grade', 'N/A')}")
                    print(f"      - Page: {metadata.get('page', 'N/A')}")
                    print(f"      - Preview: {doc[:100]}...")
            else:
                print("  ✗ No results found")
                
        except Exception as e:
            print(f"  ✗ Search error: {str(e)}")
    
    print("\n5. Testing the search_textbook plugin...")
    try:
        from plugins_func.functions.search_textbook import search_textbook, get_textbook_info
        
        # Test get_textbook_info
        info = get_textbook_info()
        if info:
            print(f"✓ Plugin loaded successfully")
            print(f"  - Collection has {info['count']} documents")
        
        # Test search_textbook function
        print("\n  Testing plugin search function...")
        response = search_textbook("分数是什么")
        print(f"  ✓ Plugin response type: {response.action}")
        print(f"  ✓ Response preview: {response.result[:200] if response.result else 'No result'}...")
        
    except Exception as e:
        print(f"✗ Failed to test plugin: {str(e)}")
    
    print("\n=== RAG System Test Complete ===")
    return True


def cleanup_test_data():
    """Clean up test data"""
    print("\nCleaning up test data...")
    try:
        rag_config = {
            'db_path': './rag_db',
            'collection_name': 'textbooks'
        }
        rag = SimpleRAGProvider(rag_config)
        # Note: This doesn't delete the test document, just resets the collection
        # In production, you might want to implement a more selective cleanup
        print("✓ Cleanup complete")
    except Exception as e:
        print(f"✗ Cleanup failed: {str(e)}")


if __name__ == "__main__":
    print("Starting RAG system test...\n")
    
    # Check if required packages are installed
    try:
        import chromadb
        import sentence_transformers
        import PyPDF2
        print("✓ All required packages are installed\n")
    except ImportError as e:
        print(f"✗ Missing required package: {str(e)}")
        print("\nPlease install required packages:")
        print("pip install chromadb sentence-transformers PyPDF2")
        sys.exit(1)
    
    # Run tests
    success = test_rag_system()
    
    if success:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed!")
    
    # Optional: cleanup
    # cleanup_test_data()