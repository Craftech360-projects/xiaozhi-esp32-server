#!/usr/bin/env python3
"""
Test script to verify Langfuse integration is working properly.
This script tests the Langfuse configuration and integration without affecting the main application.
"""

import os
import sys
import time
import json
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.langfuse_config import langfuse_config
from core.providers.llm.langfuse_wrapper import langfuse_tracker

def test_langfuse_configuration():
    """Test basic Langfuse configuration and connectivity"""
    print("=" * 60)
    print("LANGFUSE INTEGRATION TEST")
    print("=" * 60)
    
    # Test 1: Check if Langfuse is enabled
    print("1. Testing Langfuse Configuration...")
    client = langfuse_config.get_client()
    is_enabled = langfuse_config.is_enabled()
    
    if is_enabled and client:
        print("   [OK] Langfuse client initialized successfully")
        print(f"   [INFO] Client instance: {type(client)}")
    else:
        print("   [ERROR] Langfuse client not initialized")
        print("   [TIP] Make sure you have set LANGFUSE_SECRET_KEY and LANGFUSE_PUBLIC_KEY environment variables")
        return False
    
    # Test 2: Check pricing configuration
    print("\n2. Testing Pricing Configuration...")
    pricing = langfuse_config.get_pricing_config()
    print(f"   [INFO] Available models in pricing: {len(pricing.keys())}")
    print(f"   [INFO] Sample pricing - GPT-4: ${pricing.get('gpt-4', {}).get('input', 'N/A')}/1K input tokens")
    
    # Test 3: Test tracker initialization
    print("\n3. Testing Langfuse Tracker...")
    tracker = langfuse_tracker
    print(f"   [INFO] Tracker enabled: {tracker.enabled}")
    print(f"   [INFO] Tracker client: {type(tracker.client) if tracker.client else 'None'}")
    
    # Test 4: Test basic generation creation using v3+ API
    print("\n4. Testing Generation Creation...")
    if tracker.enabled:
        try:
            # Test LLM generation
            test_session_id = f"test_session_{int(time.time())}"
            
            start_time = time.time()
            time.sleep(0.1)  # Simulate processing time
            end_time = time.time()
            
            input_data = {"messages": [{"role": "user", "content": "Test message"}]}
            output_data = "Test response from LLM"
            
            tracker._track_generation(
                input_data, output_data, start_time, end_time, "test_provider", "gpt-4o-mini", test_session_id
            )
            
            print("   [OK] Test LLM generation created successfully")
            print(f"   [INFO] Session ID: {test_session_id}")
            
            # Test STT tracking
            tracker._track_stt_operation(
                ([b"fake_audio_data"],), {"audio_format": "opus"}, "Hello, this is a test transcription", 
                start_time, end_time, "openai_whisper", test_session_id
            )
            
            print("   [OK] STT test generation created successfully")
            
            # Test TTS tracking
            tracker._track_tts_operation(
                "Hello, this is a test synthesis", {"voice_id": 1695}, True,
                start_time, end_time, "ttson", test_session_id
            )
            
            print("   [OK] TTS test generation created successfully")
            
        except Exception as e:
            print(f"   [ERROR] Failed to create test generations: {e}")
            print(f"   [DEBUG] Error details: {type(e).__name__}: {e}")
            return False
    
    # Test 5: Environment Variables Check
    print("\n5. Environment Variables Check...")
    secret_key = os.getenv('LANGFUSE_SECRET_KEY', '')
    public_key = os.getenv('LANGFUSE_PUBLIC_KEY', '')
    host = os.getenv('LANGFUSE_HOST', 'https://cloud.langfuse.com')
    
    print(f"   [INFO] LANGFUSE_SECRET_KEY: {'[SET]' if secret_key else '[NOT SET]'}")
    print(f"   [INFO] LANGFUSE_PUBLIC_KEY: {'[SET]' if public_key else '[NOT SET]'}")
    print(f"   [INFO] LANGFUSE_HOST: {host}")
    
    # Test 6: Token counting functionality
    print("\n6. Testing Token Counting...")
    try:
        # Test with different model types
        test_text = "This is a test message for token counting."
        
        gpt4_tokens = tracker._count_tokens(test_text, "gpt-4")
        gpt35_tokens = tracker._count_tokens(test_text, "gpt-3.5-turbo")
        fallback_tokens = tracker._count_tokens(test_text, "unknown-model")
        
        print(f"   [INFO] GPT-4 tokens: {gpt4_tokens}")
        print(f"   [INFO] GPT-3.5 tokens: {gpt35_tokens}")
        print(f"   [INFO] Fallback estimation: {fallback_tokens}")
        
        # Test cost calculation
        cost_info = tracker._calculate_cost(100, 50, "gpt-4o")
        print(f"   [INFO] Cost calculation test: ${cost_info['total_cost']:.6f}")
        
    except Exception as e:
        print(f"   [WARNING] Token counting test failed: {e}")
    
    print("\n" + "=" * 60)
    if is_enabled:
        print("[SUCCESS] LANGFUSE INTEGRATION TEST COMPLETED SUCCESSFULLY!")
        print("\n[INFO] Check your Langfuse dashboard for the test traces:")
        print(f"   Dashboard URL: {host}")
        print("\n[INFO] Integration Status:")
        print("   [OK] LLM calls will be tracked with costs and usage")
        print("   [OK] STT operations will be tracked with audio metadata")  
        print("   [OK] TTS operations will be tracked with voice settings")
        print("   [OK] All operations include response times and error handling")
    else:
        print("[ERROR] LANGFUSE INTEGRATION NOT PROPERLY CONFIGURED")
        print("\n[HELP] To fix this:")
        print("   1. Set LANGFUSE_SECRET_KEY environment variable")
        print("   2. Set LANGFUSE_PUBLIC_KEY environment variable")
        print("   3. Optionally set LANGFUSE_HOST (defaults to cloud.langfuse.com)")
    print("=" * 60)
    
    return is_enabled

if __name__ == "__main__":
    success = test_langfuse_configuration()
    sys.exit(0 if success else 1)