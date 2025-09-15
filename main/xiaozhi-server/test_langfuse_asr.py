#!/usr/bin/env python3
"""
Test script to verify ASR Langfuse integration
"""

import asyncio
import sys
import os

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.langfuse_config import langfuse_config
from core.providers.llm.langfuse_wrapper import langfuse_tracker
from config.logger import setup_logging

logger = setup_logging()
TAG = __name__

async def test_langfuse_asr_integration():
    """Test ASR with Langfuse tracking"""

    # Check Langfuse configuration
    print("\n=== LANGFUSE CONFIG TEST ===")
    print(f"Langfuse enabled: {langfuse_config.is_enabled()}")
    print(f"Langfuse client: {langfuse_config.get_client()}")

    if not langfuse_config.is_enabled():
        print("[ERROR] Langfuse is not enabled. Check your environment variables.")
        print("Required: LANGFUSE_SECRET_KEY and LANGFUSE_PUBLIC_KEY")
        return False

    # Test STT tracking
    print("\n=== ASR TRACKING TEST ===")
    try:
        @langfuse_tracker.track_stt("test_asr")
        async def mock_speech_to_text(opus_data, session_id="test_session", audio_format="opus"):
            """Mock STT function for testing"""
            await asyncio.sleep(0.1)  # Simulate processing time
            return "Hello, this is a test transcription", "test_audio.wav"

        # Simulate ASR call
        result = await mock_speech_to_text([b"mock_audio_data"], "test_session_123")
        print(f"[SUCCESS] ASR tracking test successful: {result[0]}")

        # Force flush to ensure data is sent
        if langfuse_tracker.enabled:
            langfuse_tracker.client.flush()
            print("[SUCCESS] Langfuse data flushed to server")

        return True

    except Exception as e:
        print(f"[ERROR] ASR tracking test failed: {e}")
        logger.bind(tag=TAG).error(f"ASR tracking test error: {e}")
        return False

async def main():
    """Main test function"""
    print("Starting Langfuse ASR Integration Test...")

    success = await test_langfuse_asr_integration()

    if success:
        print("\n[SUCCESS] All tests passed! Langfuse ASR integration is working.")
        print("\nNext steps:")
        print("1. Check your Langfuse dashboard for the test trace")
        print("2. Start a real conversation to see ASR tracking in action")
    else:
        print("\n[ERROR] Tests failed. Check the configuration and error messages above.")

    return success

if __name__ == "__main__":
    asyncio.run(main())