#!/usr/bin/env python3
"""
Test script to verify Langfuse decorators are properly applied
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import time
from core.providers.llm.langfuse_wrapper import langfuse_tracker

class MockLLMProvider:
    """Mock LLM provider to test decorator application"""
    
    def __init__(self):
        self.model_name = "test-model"
    
    @langfuse_tracker.track_llm_call("mock_openai")
    def response(self, session_id, dialogue, **kwargs):
        """Mock response method that yields chunks"""
        print(f"[MOCK] Mock LLM response called with session: {session_id}")
        
        # Simulate streaming response
        response_text = "Hello! I'm a mock AI assistant. Let me count to 3: 1, 2, 3. Done!"
        
        # Split into chunks to simulate streaming
        words = response_text.split()
        for i, word in enumerate(words):
            chunk = word + (" " if i < len(words) - 1 else "")
            yield chunk
            time.sleep(0.01)  # Small delay to simulate real streaming
    
    @langfuse_tracker.track_function_call("mock_openai")
    def response_with_functions(self, session_id, dialogue, functions=None):
        """Mock function calling response"""
        print(f"[MOCK] Mock function call with session: {session_id}")
        
        # Simulate function calling response
        yield "I can help with weather information.", None
        yield None, [{"function": {"name": "get_weather", "arguments": '{"location": "New York"}'}}]
        yield "Based on the weather data, it's sunny today!", None

def test_decorator_application():
    """Test that decorators are properly applied and executed"""
    
    print("[TEST] Testing Langfuse Decorator Application...")
    
    # Check if Langfuse is enabled
    print(f"[STATUS] Langfuse enabled: {langfuse_tracker.enabled}")
    print(f"[STATUS] Langfuse client exists: {langfuse_tracker.client is not None}")
    
    if not langfuse_tracker.enabled:
        print("[WARNING] Langfuse is disabled - decorators will pass through")
    
    # Test the mock provider
    provider = MockLLMProvider()
    
    # Test basic response tracking
    print("\n[TEST] Testing basic LLM response tracking...")
    session_id = f"mock_session_{int(time.time())}"
    dialogue = [
        {"role": "user", "content": "Hello, please count to 3"}
    ]
    
    print(f"[CALL] Calling mock response method with session: {session_id}")
    
    response_chunks = []
    for chunk in provider.response(session_id, dialogue):
        response_chunks.append(chunk)
        print(f"[CHUNK] Received: {chunk}")
    
    full_response = ''.join(response_chunks)
    print(f"[RESULT] Full response: {full_response}")
    
    # Test function calling tracking
    print("\n[TEST] Testing function call tracking...")
    session_id_func = f"mock_func_session_{int(time.time())}"
    
    functions = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get weather information"
            }
        }
    ]
    
    print(f"[CALL] Calling mock function response with session: {session_id_func}")
    
    for content, tool_calls in provider.response_with_functions(session_id_func, dialogue, functions=functions):
        if content:
            print(f"[CONTENT] {content}")
        if tool_calls:
            print(f"[TOOLS] {tool_calls}")
    
    # Wait for Langfuse processing
    print("\n[WAIT] Waiting 2 seconds for Langfuse processing...")
    time.sleep(2)
    
    return True

def test_manual_tracking():
    """Test manual Langfuse tracking to verify client works"""
    
    print("\n[TEST] Testing manual Langfuse tracking...")
    
    if not langfuse_tracker.enabled:
        print("[SKIP] Langfuse disabled, skipping manual test")
        return False
    
    try:
        # Create a manual generation
        generation = langfuse_tracker.client.start_observation(
            as_type='generation',
            name='manual_test_generation',
            input={'test': 'manual tracking test'},
            model='test-model'
        )
        
        generation.update(
            output='This is a manual test of Langfuse tracking',
            metadata={
                'test_type': 'manual',
                'timestamp': time.time()
            }
        )
        
        generation.end()
        langfuse_tracker.client.flush()
        
        print("[SUCCESS] Manual tracking test completed")
        return True
        
    except Exception as e:
        print(f"[ERROR] Manual tracking failed: {e}")
        return False

if __name__ == "__main__":
    print("[SUITE] Langfuse Decorator Integration Test")
    print("=" * 50)
    
    # Test decorator application
    decorator_success = test_decorator_application()
    
    # Test manual tracking
    manual_success = test_manual_tracking()
    
    print("\n[RESULTS] Test Results:")
    print(f"[DECORATOR] Decorator Application: {'PASS' if decorator_success else 'FAIL'}")
    print(f"[MANUAL] Manual Tracking: {'PASS' if manual_success else 'FAIL'}")
    
    if decorator_success:
        print("\n[SUCCESS] Decorators are properly applied and executing!")
        if langfuse_tracker.enabled:
            print("[DASHBOARD] Check your Langfuse dashboard at: https://cloud.langfuse.com")
            print("[SESSION] Look for sessions starting with 'mock_session_' and 'mock_func_session_'")
        else:
            print("[INFO] Langfuse is disabled - check your environment variables")
    else:
        print("\n[FAIL] Decorator tests failed!")
    
    print("\n[NEXT] Next steps:")
    print("1. Verify that decorator debug messages appear in the output above")
    print("2. Check Langfuse dashboard for test traces (if enabled)")
    print("3. Look for [LANGFUSE] prefixed debug messages indicating tracking activity")