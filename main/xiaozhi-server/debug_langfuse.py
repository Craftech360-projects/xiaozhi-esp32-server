#!/usr/bin/env python3
"""
Debug script to identify why Langfuse isn't working in production
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def debug_langfuse_issue():
    """Debug the exact issue with Langfuse tracking"""
    print("=" * 60)
    print("DEBUGGING LANGFUSE PRODUCTION ISSUE")
    print("=" * 60)
    
    # Check 1: Environment variables
    print("1. Checking Environment Variables...")
    secret_key = os.getenv('LANGFUSE_SECRET_KEY')
    public_key = os.getenv('LANGFUSE_PUBLIC_KEY')
    host = os.getenv('LANGFUSE_HOST', 'https://cloud.langfuse.com')
    
    if secret_key and public_key:
        print(f"   [OK] LANGFUSE_SECRET_KEY: {secret_key[:10]}...")
        print(f"   [OK] LANGFUSE_PUBLIC_KEY: {public_key[:10]}...")
        print(f"   [OK] LANGFUSE_HOST: {host}")
    else:
        print(f"   [ERROR] Missing keys - SECRET: {bool(secret_key)}, PUBLIC: {bool(public_key)}")
        return False
    
    # Check 2: Import langfuse_config
    print("\n2. Testing Langfuse Config...")
    try:
        from config.langfuse_config import langfuse_config
        client = langfuse_config.get_client()
        enabled = langfuse_config.is_enabled()
        
        print(f"   [INFO] Client initialized: {client is not None}")
        print(f"   [INFO] Tracking enabled: {enabled}")
        
        if client:
            # Try auth check
            try:
                result = client.auth_check()
                print(f"   [OK] Authentication successful: {result}")
            except Exception as e:
                print(f"   [WARNING] Auth check failed: {e}")
        else:
            print("   [ERROR] Client is None")
            return False
            
    except Exception as e:
        print(f"   [ERROR] Config import failed: {e}")
        return False
    
    # Check 3: Test langfuse_wrapper
    print("\n3. Testing Langfuse Wrapper...")
    try:
        from core.providers.llm.langfuse_wrapper import langfuse_tracker
        print(f"   [OK] Wrapper imported successfully")
        print(f"   [INFO] Tracker enabled: {langfuse_tracker.enabled}")
        print(f"   [INFO] Tracker client: {langfuse_tracker.client is not None}")
        
    except Exception as e:
        print(f"   [ERROR] Wrapper import failed: {e}")
        return False
    
    # Check 4: Test a simple tracking operation
    print("\n4. Testing Direct Tracking...")
    try:
        if client and enabled:
            # Create a simple trace directly
            trace = client.trace(name="debug_test", input={"test": "debug"})
            print(f"   [OK] Direct trace created: {trace.id}")
            
            # Create generation
            generation = trace.generation(
                name="debug_generation",
                input={"prompt": "test"},
                output="test response",
                model="debug-model"
            )
            print(f"   [OK] Direct generation created")
            
            # Flush
            client.flush()
            print(f"   [OK] Data flushed to Langfuse")
            
        else:
            print("   [SKIP] Client not available for direct test")
            
    except Exception as e:
        print(f"   [ERROR] Direct tracking failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Check 5: Test decorator mechanism
    print("\n5. Testing Decorator Mechanism...")
    try:
        from core.providers.llm.langfuse_wrapper import langfuse_tracker
        
        # Create a test function with decorator
        @langfuse_tracker.track_llm_call("debug_provider")
        def test_function(self, session_id, dialogue, **kwargs):
            return "test response"
        
        # Create mock self with model_name
        class MockSelf:
            def __init__(self):
                self.model_name = "debug-model"
        
        mock_self = MockSelf()
        
        # Call the decorated function
        result = test_function(mock_self, "debug_session", [{"role": "user", "content": "test"}])
        print(f"   [OK] Decorated function called successfully: {result}")
        
        # Flush again
        if client:
            client.flush()
            print(f"   [OK] Decorator data flushed")
        
    except Exception as e:
        print(f"   [ERROR] Decorator test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("[DEBUG COMPLETE] Check the results above for issues")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    debug_langfuse_issue()