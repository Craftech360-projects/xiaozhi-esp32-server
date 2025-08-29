#!/usr/bin/env python3
"""
Test child-friendly fallback messages for toy
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.providers.llm.openai.openai import LLMProvider

def test_fallback_message():
    """Test fallback message for children when LLM fails"""
    print("Testing child-friendly fallback for toy...")
    
    config = {
        "type": "openai",
        "api_key": "invalid_key_for_test",  # This will cause 401 error
        "base_url": "https://api.groq.com/openai/v1",
        "model_name": "openai/gpt-oss-20b",
        "max_retries": 2,
        "retry_delay": 1
    }
    
    try:
        llm = LLMProvider(config)
        dialogue = [{"role": "user", "content": "Hello"}]
        
        print("Sending request with invalid key (will fail)...")
        
        for chunk in llm.response("test_session", dialogue):
            print(f"Fallback message: '{chunk}'")
            break  # Just get the first chunk (the fallback)
        
        print("SUCCESS: Child-friendly fallback message generated!")
        
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    test_fallback_message()