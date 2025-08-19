#!/usr/bin/env python3
"""
Test script to search for Extrinsic Semiconductor in physics textbooks
"""

import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.providers.rag.simple_rag import SimpleRAGProvider
from plugins_func.functions.search_textbook import search_textbook
from config.logger import setup_logging

logger = setup_logging()


def test_extrinsic_semiconductor():
    """Test searching for Extrinsic Semiconductor"""
    
    print("=== Testing Search for 'Extrinsic Semiconductor' ===\n")
    
    # Initialize RAG provider
    print("1. Initializing RAG provider...")
    rag_config = {
        'db_path': './rag_db',
        'collection_name': 'textbooks'
    }
    rag = SimpleRAGProvider(rag_config)
    
    # Get collection info
    info = rag.get_collection_info()
    print(f"✓ Collection loaded with {info['count']} documents\n")
    
    # Test direct RAG search
    print("2. Direct RAG search for 'Extrinsic Semiconductor'...")
    query = "what is Extrinsic Semiconductor"
    
    results = rag.search(query, top_k=5)
    
    if results['documents']:
        print(f"✓ Found {len(results['documents'])} relevant results:\n")
        
        for i, (doc, metadata) in enumerate(zip(results['documents'], results['metadatas'])):
            print(f"Result {i+1}:")
            print(f"  Source: {metadata.get('source', 'Unknown')}")
            print(f"  Page: {metadata.get('page', 'Unknown')}")
            print(f"  Content preview:")
            print(f"  {'-' * 60}")
            # Show more content for better understanding
            print(f"  {doc[:500]}...")
            print(f"  {'-' * 60}\n")
    else:
        print("✗ No results found\n")
    
    # Test through plugin
    print("3. Testing through search_textbook plugin...")
    response = search_textbook(query, subject="Physics", grade="Class-12")
    
    print(f"✓ Plugin response type: {response.action}")
    print(f"\nPlugin formatted response preview:")
    print("=" * 70)
    print(response.result[:1000] if response.result else "No result")
    print("=" * 70)
    
    # Try variations of the query
    print("\n4. Testing query variations...")
    variations = [
        "Extrinsic Semiconductor",
        "extrinsic semiconductor definition",
        "p-type n-type semiconductor",
        "doped semiconductor"
    ]
    
    for var_query in variations:
        print(f"\n  Searching for: '{var_query}'")
        var_results = rag.search(var_query, top_k=2)
        
        if var_results['documents']:
            print(f"  ✓ Found {len(var_results['documents'])} results")
            # Show first result
            if var_results['documents']:
                metadata = var_results['metadatas'][0]
                print(f"    - Page {metadata.get('page', '?')} from {metadata.get('source', 'Unknown')}")
                print(f"    - Preview: {var_results['documents'][0][:200]}...")
        else:
            print(f"  ✗ No results found")


if __name__ == "__main__":
    print("Starting Extrinsic Semiconductor search test...\n")
    
    try:
        test_extrinsic_semiconductor()
        print("\n✅ Test complete!")
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()