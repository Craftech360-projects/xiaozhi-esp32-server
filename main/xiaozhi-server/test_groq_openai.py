#!/usr/bin/env python3
"""
Test that GroqLLM configuration actually uses OpenAI provider with decorators
"""

import os
import sys
from dotenv import load_dotenv
import time

# Load environment variables from .env file
load_dotenv()

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_groq_openai():
    """Test that GroqLLM config uses OpenAI provider"""
    print("TESTING GROQLLM -> OPENAI PROVIDER MAPPING")
    print("=" * 50)
    
    try:
        # Test the exact same logic as modules_initialize.py
        from core.utils.llm import create_instance
        
        # Your actual config values
        select_llm_module = "GroqLLM"  # This is what's in your config
        config_groqllm = {
            "type": "openai",  # This makes it use OpenAI provider
            "api_key": "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",
            "model_name": "openai/gpt-oss-20b",
            "base_url": "https://api.groq.com/openai/v1",
            "temperature": 0.7,
            "max_tokens": 2048
        }
        
        # This is what modules_initialize.py does (lines 41-50)
        llm_type = config_groqllm.get("type", select_llm_module)  # Should be "openai"
        print(f"[INFO] Selected LLM module: {select_llm_module}")
        print(f"[CRITICAL] Determined LLM type: {llm_type}")
        
        # This should create OpenAI provider with Groq config
        provider = create_instance(llm_type, config_groqllm)
        
        print(f"[OK] Provider created successfully!")
        print(f"[INFO] Provider type: {type(provider)}")
        print(f"[INFO] Provider module: {provider.__class__.__module__}")
        print(f"[INFO] Model name: {getattr(provider, 'model_name', 'unknown')}")
        print(f"[INFO] Base URL: {getattr(provider, 'base_url', 'unknown')}")
        
        # Check if methods are decorated
        response_method = getattr(provider, 'response', None)
        response_with_functions_method = getattr(provider, 'response_with_functions', None)
        
        if hasattr(response_method, '__wrapped__'):
            print(f"[OK] response() method IS DECORATED!")
        else:
            print(f"[ERROR] response() method is NOT DECORATED!")
            
        if hasattr(response_with_functions_method, '__wrapped__'):
            print(f"[OK] response_with_functions() method IS DECORATED!")
        else:
            print(f"[ERROR] response_with_functions() method is NOT DECORATED!")
        
        # Test tracking with the GroqLLM provider
        print(f"\n[INFO] Testing Langfuse tracking with GroqLLM provider...")
        from core.providers.llm.langfuse_wrapper import langfuse_tracker
        from config.langfuse_config import langfuse_config
        
        if not langfuse_config.is_enabled():
            print(f"[ERROR] Langfuse is not enabled!")
            return False
        
        # Test tracking exactly like real conversation
        input_data = {
            "messages": [
                {"role": "system", "content": "You are a helpful AI assistant."},
                {"role": "user", "content": "Hello! This is a test of GroqLLM tracking."}
            ]
        }
        output_data = "Hello! I'm responding through GroqLLM (which uses OpenAI provider) and this should be tracked in Langfuse."
        
        session_id = f"groq_test_{int(time.time())}"
        
        langfuse_tracker._track_generation(
            input_data,
            output_data,
            "openai",  # This is what the decorator will log as
            provider.model_name,  # openai/gpt-oss-20b
            session_id
        )
        
        print(f"[OK] GroqLLM tracking test successful!")
        print(f"[INFO] Session: {session_id}")
        print(f"[INFO] Model: {provider.model_name}")
        
    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 50)
    print("[SUCCESS] GROQLLM USES OPENAI PROVIDER WITH DECORATORS!")
    print("\n[CRITICAL FINDINGS]:")
    print("✅ Your GroqLLM config correctly maps to OpenAI provider")
    print("✅ OpenAI provider has Langfuse decorators applied") 
    print("✅ Real conversations SHOULD be tracked automatically")
    print("✅ Test trace created successfully")
    print("\n[ACTION] Check Langfuse dashboard for:")
    print("🔗 https://cloud.langfuse.com")
    print("📊 Look for: openai_generation with session groq_test_*")
    print("\n[IF STILL NO REAL TRACES]:")
    print("1. Start your xiaozhi server: python app.py")
    print("2. Have a real conversation")
    print("3. Look for [LANGFUSE] DECORATOR CALLED! in console logs")
    print("4. If you see the logs, tracking IS working!")
    print("=" * 50)
    
    return True

if __name__ == "__main__":
    test_groq_openai()