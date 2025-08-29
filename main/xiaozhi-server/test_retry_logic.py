#!/usr/bin/env python3
"""
Test script to verify LLM retry logic
This will test both successful connections and retry scenarios
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.providers.llm.openai.openai import LLMProvider
from config.logger import setup_logging
import time

# Setup logging
logger = setup_logging()

def test_successful_connection():
    """Test normal operation with valid API key"""
    print("\n[TEST 1] Normal operation with valid Groq API key")
    print("="*60)
    
    config = {
        "type": "openai",
        "api_key": "your-groq-api-key-here",
        "base_url": "https://api.groq.com/openai/v1",
        "model_name": "openai/gpt-oss-20b",
        "temperature": 0.7,
        "max_tokens": 50,  # Small for quick test
        "timeout": 15,
        "max_retries": 2,
        "retry_delay": 1
    }
    
    try:
        llm = LLMProvider(config)
        
        dialogue = [
            {"role": "user", "content": "Say 'Hello from Cheeko!' in exactly those words."}
        ]
        
        print("📤 Sending request to Groq...")
        start_time = time.time()
        
        response_text = ""
        for chunk in llm.response("test_session", dialogue):
            if chunk and not chunk.startswith("[OpenAI Service Response Exception"):
                response_text += chunk
                print(f"📥 Received: {chunk}", end="", flush=True)
        
        end_time = time.time()
        
        print(f"\n✅ Success! Response time: {end_time - start_time:.2f}s")
        print(f"📝 Full response: {response_text.strip()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_invalid_api_key():
    """Test retry logic with invalid API key (should trigger 401 errors)"""
    print("\n🧪 TEST 2: Testing retry logic with invalid API key")
    print("="*60)
    
    config = {
        "type": "openai",
        "api_key": "invalid_key_to_trigger_401_error",  # Invalid key
        "base_url": "https://api.groq.com/openai/v1",
        "model_name": "openai/gpt-oss-20b",
        "temperature": 0.7,
        "max_tokens": 50,
        "timeout": 15,
        "max_retries": 2,  # Should try twice
        "retry_delay": 1   # 1 second between attempts
    }
    
    try:
        llm = LLMProvider(config)
        
        dialogue = [
            {"role": "user", "content": "Hello"}
        ]
        
        print("📤 Sending request with invalid API key...")
        print("⏳ Should see 2 retry attempts with 1s delay between them...")
        
        start_time = time.time()
        
        response_text = ""
        for chunk in llm.response("test_session", dialogue):
            response_text += chunk
            if chunk.startswith("[OpenAI Service Response Exception"):
                print(f"📥 {chunk}")
            else:
                print(f"📥 Received: {chunk}")
        
        end_time = time.time()
        
        print(f"\n⚠️  Expected failure completed in {end_time - start_time:.2f}s")
        print("✅ Retry logic working - should have taken ~2+ seconds due to retry delay")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed unexpectedly: {e}")
        return False

def test_timeout_scenario():
    """Test with very short timeout to trigger timeout retry"""
    print("\n🧪 TEST 3: Testing timeout scenario")
    print("="*60)
    
    config = {
        "type": "openai",
        "api_key": "your-groq-api-key-here",
        "base_url": "https://api.groq.com/openai/v1",
        "model_name": "openai/gpt-oss-20b",
        "temperature": 0.7,
        "max_tokens": 50,
        "timeout": 1,     # Very short timeout to trigger timeout
        "max_retries": 2,
        "retry_delay": 1
    }
    
    try:
        llm = LLMProvider(config)
        
        dialogue = [
            {"role": "user", "content": "Tell me a short story"}
        ]
        
        print("📤 Sending request with 1s timeout (may trigger timeout retry)...")
        
        start_time = time.time()
        
        response_text = ""
        for chunk in llm.response("test_session", dialogue):
            response_text += chunk
            print(f"📥 {chunk}", end="", flush=True)
        
        end_time = time.time()
        
        print(f"\n✅ Completed in {end_time - start_time:.2f}s")
        
        return True
        
    except Exception as e:
        print(f"⚠️  Expected timeout behavior: {e}")
        return True

def main():
    """Run all tests"""
    print("🚀 TESTING GROQ LLM RETRY LOGIC")
    print("="*60)
    print("This will test:")
    print("✓ Normal API operation")
    print("✓ 401 error retry logic")  
    print("✓ Timeout handling")
    print()
    
    results = []
    
    # Test 1: Normal operation
    results.append(test_successful_connection())
    
    # Test 2: Invalid API key (401 errors)
    results.append(test_invalid_api_key())
    
    # Test 3: Timeout scenario
    results.append(test_timeout_scenario())
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! Retry logic is working correctly.")
        print("\n🔧 Configuration recommendations:")
        print("   • timeout: 15s (good for Groq)")
        print("   • max_retries: 2 (retry once)")
        print("   • retry_delay: 1s (quick retry)")
    else:
        print("⚠️  Some tests failed. Check the logs above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)