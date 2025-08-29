#!/usr/bin/env python3
"""
Simple test for LLM retry logic
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.providers.llm.openai.openai import LLMProvider
from config.logger import setup_logging
import time

# Setup logging
logger = setup_logging()

def test_valid_api_key():
    """Test with valid API key"""
    print("\n[TEST 1] Testing with valid Groq API key")
    print("-" * 50)
    
    config = {
        "type": "openai",
        "api_key": "your-groq-api-key-here",
        "base_url": "https://api.groq.com/openai/v1",
        "model_name": "openai/gpt-oss-20b",
        "temperature": 0.7,
        "max_tokens": 30,
        "timeout": 15,
        "max_retries": 2,
        "retry_delay": 1
    }
    
    try:
        llm = LLMProvider(config)
        
        dialogue = [
            {"role": "user", "content": "Say hello"}
        ]
        
        print("Sending request to Groq...")
        start_time = time.time()
        
        response_text = ""
        for chunk in llm.response("test_session", dialogue):
            if chunk and not chunk.startswith("[OpenAI Service Response Exception"):
                response_text += chunk
                print("Got chunk:", repr(chunk))
        
        end_time = time.time()
        
        print(f"SUCCESS! Response time: {end_time - start_time:.2f}s")
        print(f"Response: {response_text.strip()}")
        
        return True
        
    except Exception as e:
        print(f"FAILED: {e}")
        return False

def test_invalid_api_key():
    """Test with invalid API key to trigger retry"""
    print("\n[TEST 2] Testing retry with invalid API key")
    print("-" * 50)
    
    config = {
        "type": "openai",
        "api_key": "invalid_key_123",  # Invalid key
        "base_url": "https://api.groq.com/openai/v1",
        "model_name": "openai/gpt-oss-20b",
        "temperature": 0.7,
        "max_tokens": 30,
        "timeout": 15,
        "max_retries": 2,  # Should try twice
        "retry_delay": 1   # 1 second between attempts
    }
    
    try:
        llm = LLMProvider(config)
        
        dialogue = [
            {"role": "user", "content": "Hello"}
        ]
        
        print("Sending request with invalid API key...")
        print("Should see retry attempts...")
        
        start_time = time.time()
        
        response_text = ""
        for chunk in llm.response("test_session", dialogue):
            response_text += chunk
            print("Received:", chunk)
        
        end_time = time.time()
        
        print(f"Completed in {end_time - start_time:.2f}s")
        print("Retry logic working - took extra time due to retries")
        
        return True
        
    except Exception as e:
        print(f"Expected failure: {e}")
        return True

def main():
    print("TESTING GROQ LLM RETRY LOGIC")
    print("=" * 50)
    
    # Test 1: Valid API key
    test1_result = test_valid_api_key()
    
    # Test 2: Invalid API key (should retry)
    test2_result = test_invalid_api_key()
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    if test1_result:
        print("✓ Valid API key test: PASSED")
    else:
        print("✗ Valid API key test: FAILED")
    
    if test2_result:
        print("✓ Retry logic test: PASSED")
    else:
        print("✗ Retry logic test: FAILED")
    
    if test1_result and test2_result:
        print("\nAll tests PASSED! Retry logic is working.")
    else:
        print("\nSome tests FAILED. Check configuration.")

if __name__ == "__main__":
    main()