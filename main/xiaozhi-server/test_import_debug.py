#!/usr/bin/env python3
"""
Test import chain to see where the issue is
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_import_chain():
    """Test the complete import chain"""
    print("TESTING IMPORT CHAIN WITH DEBUG LOGGING")
    print("=" * 50)
    
    # Step 1: Test langfuse_config import
    print("1. Testing langfuse_config import...")
    try:
        from config.langfuse_config import langfuse_config
        print(f"   [OK] langfuse_config imported")
        print(f"   [INFO] Enabled: {langfuse_config.is_enabled()}")
    except Exception as e:
        print(f"   [ERROR] langfuse_config import failed: {e}")
        return False
    
    # Step 2: Test langfuse_wrapper import (should see debug logs)
    print("\n2. Testing langfuse_wrapper import...")
    try:
        # This should trigger the debug logs we added
        print("   About to import langfuse_wrapper...")
        from core.providers.llm.langfuse_wrapper import langfuse_tracker
        print(f"   [OK] langfuse_wrapper imported")
        print(f"   [INFO] Tracker enabled: {langfuse_tracker.enabled}")
    except Exception as e:
        print(f"   [ERROR] langfuse_wrapper import failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 3: Test OpenAI provider import (should see decorator application)
    print("\n3. Testing OpenAI provider import...")
    try:
        print("   About to import OpenAI provider...")
        from core.providers.llm.openai.openai import LLMProvider
        print(f"   [OK] OpenAI provider imported")
        
        # Check if methods have decorators
        provider = LLMProvider({"model_name": "test", "api_key": "test", "base_url": "test"})
        response_method = getattr(provider, 'response', None)
        if hasattr(response_method, '__wrapped__'):
            print(f"   [OK] response method has decorator!")
        else:
            print(f"   [ERROR] response method has NO decorator!")
            
    except Exception as e:
        print(f"   [ERROR] OpenAI provider import failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 4: Test create_instance (the actual method used by server)
    print("\n4. Testing create_instance (server method)...")
    try:
        from core.utils.llm import create_instance
        
        config = {
            "type": "openai",
            "api_key": "test_key",
            "model_name": "test-model",
            "base_url": "https://api.test.com/v1"
        }
        
        print("   About to call create_instance...")
        provider = create_instance("openai", config)
        print(f"   [OK] create_instance worked")
        print(f"   [INFO] Provider type: {type(provider)}")
        
        # Check decorators on the created instance
        response_method = getattr(provider, 'response', None)
        if hasattr(response_method, '__wrapped__'):
            print(f"   [OK] Created provider has decorated methods!")
        else:
            print(f"   [ERROR] Created provider has NO decorators!")
        
    except Exception as e:
        print(f"   [ERROR] create_instance failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 50)
    print("[INFO] Import chain test completed!")
    print("[ACTION] Look at the debug messages above to see:")
    print("- Did langfuse_wrapper show import messages?")
    print("- Did OpenAI provider show decorator application?") 
    print("- Do the final providers have __wrapped__ methods?")
    print("=" * 50)
    
    return True

if __name__ == "__main__":
    test_import_chain()