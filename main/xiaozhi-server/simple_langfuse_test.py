#!/usr/bin/env python3
"""
Simple test to isolate the exact Langfuse issue
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_simple_langfuse():
    """Simple test to isolate the issue"""
    print("SIMPLE LANGFUSE TEST")
    print("=" * 40)
    
    # Test 1: Direct Langfuse client test
    print("1. Testing Direct Langfuse Client...")
    try:
        from langfuse import Langfuse
        
        client = Langfuse(
            secret_key=os.getenv('LANGFUSE_SECRET_KEY'),
            public_key=os.getenv('LANGFUSE_PUBLIC_KEY'),
            host=os.getenv('LANGFUSE_HOST', 'https://cloud.langfuse.com')
        )
        
        # Test auth
        auth_result = client.auth_check()
        print(f"   [OK] Auth successful: {auth_result}")
        
        # Test v3+ API directly
        generation = client.start_observation(
            as_type='generation',
            name="simple_test_generation", 
            input={"prompt": "Hello, this is a simple test"},
            model="test-model"
        )
        print(f"   [OK] Generation started: {generation.id}")
        
        # Update with output
        generation.update(output="Hello! This is a test response.")
        generation.end()
        
        # Flush
        client.flush()
        print(f"   [OK] Generation completed and flushed")
        
        return True
        
    except Exception as e:
        print(f"   [ERROR] Direct client test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_simple_langfuse()
    if success:
        print("\n[SUCCESS] Check your Langfuse dashboard - you should see a 'simple_test_generation' trace!")
        print("Dashboard: https://cloud.langfuse.com")
    else:
        print("\n[FAILED] Basic Langfuse test failed")