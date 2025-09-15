#!/usr/bin/env python3
"""
Test the fixed Langfuse wrapper directly
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_fixed_wrapper():
    """Test the fixed wrapper directly"""
    print("TESTING FIXED LANGFUSE WRAPPER")
    print("=" * 40)
    
    try:
        from core.providers.llm.langfuse_wrapper import langfuse_tracker
        
        # Test 1: Direct wrapper method call
        print("1. Testing direct wrapper method...")
        
        input_data = {
            "messages": [
                {"role": "user", "content": "Hello, this is a wrapper test"}
            ]
        }
        output_data = "Hello! This is a test response from the fixed wrapper."
        
        langfuse_tracker._track_generation(
            input_data, 
            output_data, 
            "test_provider", 
            "test-model", 
            "test_session_123"
        )
        
        print("   [OK] Direct wrapper call successful")
        
        # Test 2: Test decorator on a mock function
        print("\n2. Testing decorator...")
        
        @langfuse_tracker.track_llm_call("test_decorator")
        def mock_llm_function(self, session_id, dialogue, **kwargs):
            return "Mock LLM response"
        
        class MockProvider:
            def __init__(self):
                self.model_name = "mock-model-v1"
        
        provider = MockProvider()
        result = mock_llm_function(provider, "test_session", [{"role": "user", "content": "test"}])
        
        print(f"   [OK] Decorator test successful: {result}")
        
        # Test 3: Test streaming decorator
        print("\n3. Testing streaming decorator...")
        
        @langfuse_tracker.track_llm_call("stream_test")
        def mock_streaming_function(self, session_id, dialogue, **kwargs):
            for chunk in ["Hello", " there", " from", " streaming!"]:
                yield chunk
        
        provider = MockProvider()
        provider.model_name = "streaming-model"
        
        full_response = ""
        for chunk in mock_streaming_function(provider, "stream_session", [{"role": "user", "content": "stream test"}]):
            full_response += chunk
        
        print(f"   [OK] Streaming test successful: '{full_response}'")
        
        print("\n" + "=" * 40)
        print("[SUCCESS] Fixed wrapper tests passed!")
        print("Check your Langfuse dashboard for:")
        print("- test_provider_generation")  
        print("- test_decorator_generation")
        print("- stream_test_streaming_generation")
        print("=" * 40)
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Wrapper test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_fixed_wrapper()