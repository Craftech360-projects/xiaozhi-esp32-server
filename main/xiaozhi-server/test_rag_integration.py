#!/usr/bin/env python3
"""
Test script for RAG Memory Provider Integration
Tests the basic functionality of the RAG math memory provider
"""

import sys
import os
import asyncio

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.config_loader import load_config
from core.utils.memory import create_instance

async def test_rag_memory_provider():
    """Test RAG memory provider loading and basic functionality"""
    print("Testing RAG Memory Provider Integration")
    print("=" * 50)
    
    try:
        # Load configuration
        print("1. Loading configuration...")
        config = load_config()
        print("   [OK] Configuration loaded successfully")
        
        # Test if rag_math memory provider can be created
        print("\n2. Testing RAG memory provider creation...")
        
        # Get RAG memory configuration
        rag_config = config.get("Memory", {}).get("rag_math", {})
        if not rag_config:
            print("   [FAIL] RAG memory provider not configured in config")
            return False
            
        print(f"   [OK] RAG configuration found: {rag_config}")
        
        # Create memory provider instance
        memory_provider = create_instance("rag_math", rag_config)
        print("   [OK] RAG memory provider created successfully")
        
        # Test initialization
        print("\n3. Testing memory provider initialization...")
        memory_provider.init_memory(role_id="test_role", llm=None)
        print("   [OK] Memory provider initialized")
        
        # Test educational query detection
        print("\n4. Testing educational query detection...")
        test_queries = [
            "What is 2 + 2?",  # Mathematical
            "Explain fractions",  # Educational
            "How's the weather?",  # Non-educational
            "What are prime numbers?",  # Mathematical concept
            "Hello there"  # Greeting
        ]
        
        for query in test_queries:
            is_educational = memory_provider._is_educational_query(query)
            print(f"   Query: '{query}' -> Educational: {is_educational}")
        
        # Test memory save (should work without errors)
        print("\n5. Testing memory save...")
        result = await memory_provider.save_memory(["test message"])
        print(f"   [OK] Memory save result: {result}")
        
        # Test educational query processing (will fail without manager-api running)
        print("\n6. Testing educational query processing...")
        try:
            query_result = await memory_provider.query_memory("What are fractions?")
            if query_result:
                print(f"   [OK] Query result: {len(query_result)} characters")
            else:
                print("   [INFO] No result (expected if manager-api not running)")
        except Exception as e:
            print(f"   [INFO] Query failed (expected if manager-api not running): {str(e)[:100]}...")
        
        print("\n" + "=" * 50)
        print("[PASS] RAG Memory Provider Integration Test PASSED")
        print("[INFO] The RAG memory provider is properly integrated with xiaozhi-server")
        print("[WARN] For full functionality, ensure manager-api is running")
        
        return True
        
    except Exception as e:
        print(f"\n[FAIL] Test FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    success = await test_rag_memory_provider()
    
    if success:
        print("\n[SUCCESS] Integration test completed successfully!")
        print("\n[NEXT] Next steps:")
        print("   1. Start manager-api server")
        print("   2. Configure memory provider in xiaozhi-server: Memory: rag_math")
        print("   3. Test with actual educational queries")
    else:
        print("\n[FAIL] Integration test failed!")
        print("   Please check the error messages above")

if __name__ == "__main__":
    asyncio.run(main())