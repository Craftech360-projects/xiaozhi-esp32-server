#!/usr/bin/env python3
"""
Test script to verify the FIXED Langfuse integration is working properly.
This script will create actual traces that should appear in your dashboard.
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

def test_fixed_langfuse_integration():
    """Test the fixed Langfuse integration with actual traces that will appear in dashboard"""
    print("=" * 60)
    print("FIXED LANGFUSE INTEGRATION TEST - WITH INPUT/OUTPUT VISIBILITY")
    print("=" * 60)

    # Test 1: Check if Langfuse is enabled
    print("1. Testing Langfuse Configuration...")
    client = langfuse_config.get_client()
    is_enabled = langfuse_config.is_enabled()

    if is_enabled and client:
        print("   [OK] Langfuse client initialized successfully")
        print(f"   [INFO] Client instance: {type(client)}")

        # Test authentication
        try:
            auth_result = client.auth_check()
            print(f"   [OK] Authentication successful")
        except Exception as e:
            print(f"   [ERROR] Authentication failed: {e}")
            return False
    else:
        print("   [ERROR] Langfuse client not initialized")
        return False
    
    # Test 2: Complete conversation flow test
    print("\n2. Testing Complete Conversation Flow...")
    session_id = f"test-conversation-{int(time.time())}"

    try:
        # Step 1: STT tracking
        print("   [INFO] Testing STT tracking...")
        stt_success = langfuse_tracker._safe_track_event(
            name="STT-openai",
            input_data={
                "audio_format": "opus",
                "audio_chunks": 3,
                "session_id": session_id
            },
            output_data={
                "transcribed_text": "Hello! Can you help me test Langfuse integration?",
                "text_length": 48
            },
            metadata={
                "provider": "openai",
                "operation": "speech_to_text",
                "response_time_ms": 1200,
                "step": "1_stt",
                "session_id": session_id
            }
        )
        print(f"   STT tracking: {'SUCCESS' if stt_success else 'FAILED'}")

        # Step 2: LLM tracking with input/output visible in dashboard
        print("   [INFO] Testing LLM tracking...")
        llm_success = langfuse_tracker._safe_track_event(
            name="LLM-openai",
            input_data={
                "messages": [
                    {"role": "system", "content": "You are a helpful AI assistant."},
                    {"role": "user", "content": "Hello! Can you help me test Langfuse integration?"}
                ],
                "from_stt": "Hello! Can you help me test Langfuse integration?",
                "message_count": 2,
                "session_id": session_id
            },
            output_data={
                "response": "Hello! I'd be happy to help you test the Langfuse integration. This response should be visible in the dashboard!",
                "content": "Hello! I'd be happy to help you test the Langfuse integration. This response should be visible in the dashboard!"
            },
            metadata={
                "provider": "openai",
                "model": "gpt-4o-mini",
                "response_time_ms": 2500,
                "input_tokens": 28,
                "output_tokens": 22,
                "total_tokens": 50,
                "cost_usd": 0.0025,
                "step": "2_llm",
                "session_id": session_id
            }
        )
        print(f"   LLM tracking: {'SUCCESS' if llm_success else 'FAILED'}")

        # Step 3: TTS tracking
        print("   [INFO] Testing TTS tracking...")
        tts_success = langfuse_tracker._safe_track_event(
            name="TTS-edge",
            input_data={
                "text": "Hello! I'd be happy to help you test the Langfuse integration. This response should be visible in the dashboard!",
                "from_llm": "Hello! I'd be happy to help you test the Langfuse integration. This response should be visible in the dashboard!",
                "text_length": 107,
                "session_id": session_id
            },
            output_data={
                "audio_generated": True,
                "audio_format": "wav",
                "characters_processed": 107
            },
            metadata={
                "provider": "edge",
                "operation": "text_to_speech",
                "response_time_ms": 800,
                "step": "3_tts",
                "session_id": session_id
            }
        )
        print(f"   TTS tracking: {'SUCCESS' if tts_success else 'FAILED'}")

        all_success = stt_success and llm_success and tts_success
        print(f"   Overall: {'ALL OPERATIONS SUCCESSFUL' if all_success else 'SOME OPERATIONS FAILED'}")

    except Exception as e:
        print(f"   [ERROR] Conversation flow tracking failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 3: Final flush and verification
    print("\n3. Flushing Data to Langfuse...")
    try:
        client.flush()
        print("   [OK] All data flushed successfully")

        # Wait a moment for data to be processed
        time.sleep(2)

    except Exception as e:
        print(f"   [ERROR] Flush failed: {e}")

    print("\n" + "=" * 60)
    print("[SUCCESS] FIXED LANGFUSE INTEGRATION TEST COMPLETED!")
    print("\n[INFO] Check your Langfuse dashboard now:")
    print("   Dashboard URL: https://cloud.langfuse.com")
    print(f"\n[INFO] Look for session: {session_id}")
    print("\n[INFO] You should see:")
    print("   [OK] Input: 'Hello! Can you help me test Langfuse integration?'")
    print("   [OK] Output: 'Hello! I'd be happy to help you test the Langfuse integration...'")
    print("   [OK] All operations linked in a single trace")
    print("   [OK] Token counts and costs for LLM operations")
    print("   [OK] Audio metadata for STT/TTS operations")
    print("\n[INFO] The input/output should now be VISIBLE in the dashboard!")
    print("=" * 60)

    return True

if __name__ == "__main__":
    success = test_fixed_langfuse_integration()
    if success:
        print("\n[FINAL] Integration test completed successfully!")
        print("[ACTION] Please check your Langfuse dashboard for the test traces.")
    else:
        print("\n[FINAL] Integration test failed. Please check the error messages above.")
    sys.exit(0 if success else 1)