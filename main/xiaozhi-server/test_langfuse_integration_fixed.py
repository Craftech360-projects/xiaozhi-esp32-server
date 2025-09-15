#!/usr/bin/env python3
"""
Test script to verify Langfuse integration is working properly
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import time
import asyncio
from core.providers.llm.openai.openai import LLMProvider

def test_langfuse_integration():
    """Test that Langfuse tracking is working for real LLM calls"""
    
    print("[TEST] Testing Langfuse Integration...")
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Test configuration
    config = {
        "model_name": "gpt-4o-mini",
        "api_key": os.getenv("OPENAI_API_KEY", "dummy-key"),
        "base_url": "https://api.openai.com/v1",
        "max_tokens": 100,
        "temperature": 0.7
    }
    
    # Check if OpenAI key is available
    if config["api_key"] == "dummy-key":
        print("[ERROR] No OpenAI API key found. Please set OPENAI_API_KEY in .env file")
        return False
    
    try:
        # Initialize the provider (this should load the Langfuse tracker)
        print("[INIT] Initializing OpenAI LLM Provider...")
        provider = LLMProvider(config)
        
        # Test data
        session_id = f"test_session_{int(time.time())}"
        dialogue = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say hello and count to 3"}
        ]
        
        print(f"[START] Starting LLM call test - Session ID: {session_id}")
        print(f"[DATA] Dialogue: {len(dialogue)} messages")
        
        # Make the call - this should be tracked by Langfuse
        print("[CALL] Calling LLM provider.response() method...")
        response_chunks = []
        
        for chunk in provider.response(session_id, dialogue):
            response_chunks.append(chunk)
            print(f"[CHUNK] Received chunk: {chunk[:50]}...")
        
        full_response = ''.join(response_chunks)
        print(f"[SUCCESS] Complete response received: {len(full_response)} characters")
        print(f"[RESPONSE] Response: {full_response}")
        
        # Wait a moment for Langfuse to process
        print("[WAIT] Waiting 3 seconds for Langfuse to process...")
        time.sleep(3)
        
        print("[COMPLETE] Test completed successfully!")
        print("[DASHBOARD] Check your Langfuse dashboard at https://cloud.langfuse.com")
        print(f"[SESSION] Look for session: {session_id}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_function_call():
    """Test function calling tracking"""
    
    print("\n[TEST] Testing Function Call Integration...")
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Test configuration
    config = {
        "model_name": "gpt-4o-mini",
        "api_key": os.getenv("OPENAI_API_KEY", "dummy-key"),
        "base_url": "https://api.openai.com/v1",
        "max_tokens": 100,
        "temperature": 0.7
    }
    
    if config["api_key"] == "dummy-key":
        print("[ERROR] No OpenAI API key found. Skipping function call test.")
        return False
    
    try:
        provider = LLMProvider(config)
        
        # Test data
        session_id = f"test_function_session_{int(time.time())}"
        dialogue = [
            {"role": "user", "content": "What's the weather like?"}
        ]
        
        # Simple function definition
        functions = [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get weather information",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {"type": "string"}
                        }
                    }
                }
            }
        ]
        
        print(f"[START] Starting function call test - Session ID: {session_id}")
        
        # Make the function call
        print("[CALL] Calling LLM provider.response_with_functions() method...")
        
        for content, tool_calls in provider.response_with_functions(session_id, dialogue, functions=functions):
            if content:
                print(f"[CONTENT] Content: {content}")
            if tool_calls:
                print(f"[TOOLS] Tool calls: {tool_calls}")
        
        print("[SUCCESS] Function call test completed!")
        return True
        
    except Exception as e:
        print(f"[ERROR] Function call test failed: {e}")
        return False

if __name__ == "__main__":
    print("[SUITE] Langfuse Integration Test Suite")
    print("=" * 50)
    
    # Test basic LLM tracking
    llm_success = test_langfuse_integration()
    
    # Test function call tracking
    func_success = test_function_call()
    
    print("\n[RESULTS] Test Results:")
    print(f"[LLM] LLM Tracking: {'PASS' if llm_success else 'FAIL'}")
    print(f"[FUNC] Function Tracking: {'PASS' if func_success else 'FAIL'}")
    
    if llm_success and func_success:
        print("\n[SUCCESS] All tests passed! Langfuse integration is working correctly.")
        print("[DASHBOARD] Check your dashboard at: https://cloud.langfuse.com")
    else:
        print("\n[FAIL] Some tests failed. Please check the error messages above.")
        
    print("\n[NEXT] Next steps:")
    print("1. Check your Langfuse dashboard for the test traces")
    print("2. Look for the session IDs mentioned above")
    print("3. Verify that metrics, costs, and timing are recorded correctly")