#!/usr/bin/env python3
"""
Final test of real conversation tracking
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_real_tracking():
    """Test actual LLM provider with decorators"""
    print("FINAL REAL TRACKING TEST")
    print("=" * 40)
    
    try:
        # Import the actual provider used by the server
        from core.utils.llm import create_instance
        
        # Use the actual configuration from server
        config = {
            "type": "openai",
            "api_key": "test_key",
            "model_name": "openai/gpt-oss-20b",  # User's actual model
            "base_url": "https://api.groq.com/openai/v1"  # User's actual URL
        }
        
        print("1. Creating provider instance...")
        provider = create_instance("openai", config)
        print(f"   Provider created: {type(provider)}")
        
        print("2. Checking if methods are decorated...")
        response_method = getattr(provider, 'response', None)
        if hasattr(response_method, '__wrapped__'):
            print("   [SUCCESS] response method has decorator!")
        else:
            print("   [ERROR] response method has NO decorator!")
            
        function_method = getattr(provider, 'response_with_functions', None)
        if hasattr(function_method, '__wrapped__'):
            print("   [SUCCESS] response_with_functions method has decorator!")
        else:
            print("   [ERROR] response_with_functions method has NO decorator!")
        
        print("3. Testing decorator invocation...")
        # Create test dialogue
        test_dialogue = [
            {"role": "user", "content": "Hello, this is a test conversation"}
        ]
        
        test_session = "test_real_tracking_123"
        
        print(f"   About to call provider.response with session: {test_session}")
        print("   WATCH FOR DECORATOR DEBUG MESSAGES BELOW:")
        print("   " + "-" * 50)
        
        try:
            # This should trigger the decorator and create a trace
            response_gen = provider.response(test_session, test_dialogue)
            
            # Consume a few chunks to simulate real usage
            chunks = []
            chunk_count = 0
            for chunk in response_gen:
                chunks.append(chunk)
                chunk_count += 1
                if chunk_count >= 3:  # Just get first 3 chunks
                    break
                    
            print(f"   Response chunks received: {chunk_count}")
            print(f"   Sample content: {chunks[0][:50] if chunks else 'No content'}")
            
        except Exception as e:
            # Expected to fail due to fake API key, but decorator should still fire
            print(f"   [EXPECTED] API call failed (fake key): {e}")
            print("   This is normal - we just want to see decorator messages!")
        
        print("   " + "-" * 50)
        print("4. RESULTS:")
        print("   If you saw messages like:")
        print("   '[LANGFUSE] DECORATOR CALLED! Provider: openai, Function: response'")
        print("   '[LANGFUSE] TRACKING: session=test_real_tracking_123'")
        print("   Then tracking is WORKING!")
        
        print("\n5. Next steps:")
        print("   - Start your server: python app.py")
        print("   - Have a real conversation with your toy")
        print("   - Check https://cloud.langfuse.com for traces")
        
    except Exception as e:
        print(f"Error in real tracking test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_real_tracking()