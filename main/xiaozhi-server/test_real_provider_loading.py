#!/usr/bin/env python3
"""
Test real provider loading mechanism to find the production issue
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_real_provider_loading():
    """Test the actual provider loading mechanism used in production"""
    print("TESTING REAL PROVIDER LOADING MECHANISM")
    print("=" * 50)
    
    # Test 1: Test the actual create_instance function
    print("1. Testing core.utils.llm.create_instance...")
    try:
        from core.utils.llm import create_instance
        
        # Test with OpenAI provider (most likely to be used)
        config = {
            "model_name": "gpt-4o-mini",
            "api_key": "test_key"
        }
        
        provider = create_instance("openai", config)
        print(f"   [OK] OpenAI provider loaded: {type(provider)}")
        print(f"   [INFO] Model name: {provider.model_name}")
        
        # Check if the methods have decorators
        response_method = getattr(provider, 'response', None)
        response_with_functions_method = getattr(provider, 'response_with_functions', None)
        
        print(f"   [INFO] response method exists: {response_method is not None}")
        print(f"   [INFO] response_with_functions method exists: {response_with_functions_method is not None}")
        
        # Check for decorator wrapper indicators
        if hasattr(response_method, '__wrapped__'):
            print("   [OK] response method appears to be decorated (has __wrapped__)")
        else:
            print("   [WARNING] response method may not be decorated")
            
        if hasattr(response_with_functions_method, '__wrapped__'):
            print("   [OK] response_with_functions method appears to be decorated")
        else:
            print("   [WARNING] response_with_functions method may not be decorated")
        
    except Exception as e:
        print(f"   [ERROR] OpenAI provider loading failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 2: Test with other providers
    providers_to_test = ["ollama", "gemini", "xinference"]
    
    for provider_name in providers_to_test:
        print(f"\n2.{provider_name.upper()}. Testing {provider_name} provider...")
        try:
            config = {
                "model_name": f"{provider_name}-test-model",
                "api_key": "test_key" if provider_name != "ollama" else None
            }
            
            if provider_name == "gemini":
                config["api_key"] = "test_key"
            elif provider_name == "ollama":
                config = {"model_name": "llama3.2:3b", "base_url": "http://localhost:11434"}
            elif provider_name == "xinference":
                config = {"model_name": "qwen2.5-chat", "base_url": "http://localhost:9997"}
            
            provider = create_instance(provider_name, config)
            print(f"   [OK] {provider_name.capitalize()} provider loaded successfully")
            
            # Check for decorator
            response_method = getattr(provider, 'response', None)
            if hasattr(response_method, '__wrapped__'):
                print(f"   [OK] {provider_name} response method is decorated")
            else:
                print(f"   [WARNING] {provider_name} response method may not be decorated")
                
        except Exception as e:
            print(f"   [SKIP] {provider_name.capitalize()} provider loading failed (expected): {type(e).__name__}")
    
    # Test 3: Simulate actual method call with tracking
    print(f"\n3. Testing actual method call with tracking...")
    try:
        from core.utils.llm import create_instance
        from config.langfuse_config import langfuse_config
        
        # Create provider
        config = {"model_name": "gpt-4o-mini", "api_key": "test_key"}
        provider = create_instance("openai", config)
        
        # Mock dialogue
        dialogue = [{"role": "user", "content": "Hello, this is a production tracking test"}]
        
        # Check if Langfuse is enabled
        if langfuse_config.is_enabled():
            print(f"   [OK] Langfuse is enabled - calls should be tracked")
        else:
            print(f"   [WARNING] Langfuse is disabled - calls won't be tracked")
        
        # Note: We won't actually call the method since it would require real API keys
        print(f"   [INFO] Ready to track real provider calls in production")
        print(f"   [INFO] Provider type: {type(provider).__name__}")
        print(f"   [INFO] Provider model: {provider.model_name}")
        
    except Exception as e:
        print(f"   [ERROR] Production simulation failed: {e}")
    
    print("\n" + "=" * 50)
    print("[INFO] Provider loading test complete")
    print("[ACTION] If decorators are present, real conversations should be tracked")
    print("=" * 50)
    
    return True

if __name__ == "__main__":
    test_real_provider_loading()