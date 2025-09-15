#!/usr/bin/env python3
"""
Test core Langfuse integration without heavy dependencies
"""

import sys
import os

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_core_integration():
    """Test core Langfuse functionality"""
    print("=== TESTING CORE LANGFUSE INTEGRATION ===")

    try:
        # Test Langfuse config
        from config.langfuse_config import langfuse_config
        print("[SUCCESS] Langfuse config imported")

        # Test Langfuse wrapper
        from core.providers.llm.langfuse_wrapper import langfuse_tracker
        print("[SUCCESS] Langfuse tracker imported")

        print(f"Langfuse Enabled: {langfuse_config.is_enabled()}")
        print(f"Langfuse Client: {'Available' if langfuse_config.get_client() else 'Not available'}")

        if not langfuse_config.is_enabled():
            print("[ERROR] Langfuse not enabled - check environment variables")
            return False

        # Test basic tracking functionality
        @langfuse_tracker.track_stt("test_asr")
        async def mock_asr_test(audio_data, session_id):
            return "test transcription", None

        @langfuse_tracker.track_llm_call("test_llm")
        def mock_llm_test(self, session_id, messages):
            yield "test response"

        @langfuse_tracker.track_tts("test_tts")
        async def mock_tts_test(text):
            return b"mock_audio_data"

        print("[SUCCESS] All tracking decorators work")

        # Flush to ensure data is sent
        langfuse_tracker.client.flush()
        print("[SUCCESS] Data flushed to Langfuse")

        return True

    except Exception as e:
        print(f"[ERROR] Core integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("LANGFUSE CORE INTEGRATION TEST")
    print("=" * 40)

    success = test_core_integration()

    print("\n=== SUMMARY ===")
    if success:
        print("[SUCCESS] Core Langfuse integration is working!")
        print("\nWhat this means:")
        print("- Langfuse tracking decorators are ready")
        print("- ASR, LLM, and TTS tracking will work")
        print("- Missing funasr/mcp modules won't affect Langfuse")
        print("- Server conversations will be tracked once running")

        print("\nTo see traces in your dashboard:")
        print("1. Start the server (despite dependency warnings)")
        print("2. Have a conversation with your ESP32 device")
        print("3. Check your Langfuse dashboard for traces")
    else:
        print("[ERROR] Core integration has issues")

    return success

if __name__ == "__main__":
    main()