#!/usr/bin/env python3
"""
Test script to verify full conversation flow with Langfuse tracking
This simulates ASR -> LLM -> TTS with proper tracking
"""

import asyncio
import sys
import os
import time

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.langfuse_config import langfuse_config
from core.providers.llm.langfuse_wrapper import langfuse_tracker
from config.logger import setup_logging

logger = setup_logging()
TAG = __name__

class MockConnection:
    """Mock connection object for testing"""
    def __init__(self):
        self.session_id = f"test_session_{int(time.time())}"
        self.audio_format = "opus"
        self.current_speaker = None
        self.logger = logger

async def test_full_conversation_flow():
    """Test complete conversation flow with Langfuse tracking"""

    print("\n=== FULL CONVERSATION FLOW TEST ===")

    # Create mock connection
    conn = MockConnection()
    print(f"Created test session: {conn.session_id}")

    try:
        # Step 1: Mock ASR (Speech-to-Text)
        @langfuse_tracker.track_stt("test_asr")
        async def mock_asr(opus_data, session_id, audio_format="opus"):
            """Mock ASR function"""
            await asyncio.sleep(0.2)  # Simulate processing time
            return "Hello, how can you help me today?", "test_audio.wav"

        print("\n1. Testing ASR with Langfuse tracking...")
        asr_result, audio_file = await mock_asr([b"mock_audio_data"], conn.session_id)
        print(f"   ASR Result: '{asr_result}'")

        # Step 2: Mock LLM (Language Model)
        @langfuse_tracker.track_llm_call("test_llm", "gpt-4o")
        def mock_llm(self, session_id, dialogue, **kwargs):
            """Mock LLM function that yields responses"""
            time.sleep(0.3)  # Simulate processing time
            responses = [
                "I'd be happy to help you today! ",
                "I can assist with various tasks like answering questions, ",
                "providing information, or helping with problem-solving. ",
                "What specific topic would you like to discuss?"
            ]
            for response in responses:
                yield response

        print("\n2. Testing LLM with Langfuse tracking...")
        dialogue = [
            {"role": "user", "content": asr_result}
        ]

        # Create a mock LLM instance
        class MockLLM:
            def __init__(self):
                self.model_name = "gpt-4o"

        llm_instance = MockLLM()
        llm_response = ""
        for chunk in mock_llm(llm_instance, conn.session_id, dialogue):
            llm_response += chunk

        print(f"   LLM Response: '{llm_response}'")

        # Step 3: Mock TTS (Text-to-Speech)
        @langfuse_tracker.track_tts("test_tts")
        async def mock_tts(text, voice_settings=None, **kwargs):
            """Mock TTS function"""
            await asyncio.sleep(0.1)  # Simulate processing time
            return b"mock_audio_data"  # Mock audio bytes

        print("\n3. Testing TTS with Langfuse tracking...")
        tts_result = await mock_tts(llm_response, voice_settings={"voice": "neural"})
        print(f"   TTS Result: Generated {len(tts_result)} bytes of audio")

        # Force flush all tracking data
        print("\n4. Flushing Langfuse data...")
        langfuse_tracker.client.flush()
        print("   Data flushed to Langfuse dashboard")

        return True

    except Exception as e:
        print(f"[ERROR] Conversation flow test failed: {e}")
        logger.bind(tag=TAG).error(f"Conversation flow test error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_streaming_llm_tracking():
    """Test streaming LLM response with Langfuse tracking"""

    print("\n=== STREAMING LLM TEST ===")

    try:
        # Mock streaming LLM with proper generator tracking
        @langfuse_tracker.track_llm_call("test_streaming_llm", "gpt-4o")
        def mock_streaming_llm(self, session_id, dialogue, **kwargs):
            """Mock streaming LLM function"""
            chunks = [
                "Here's a streaming response: ",
                "chunk 1, ",
                "chunk 2, ",
                "chunk 3, ",
                "final chunk."
            ]
            for chunk in chunks:
                time.sleep(0.05)  # Simulate streaming delay
                yield chunk

        # Create mock LLM instance
        class MockStreamingLLM:
            def __init__(self):
                self.model_name = "gpt-4o"

        llm_instance = MockStreamingLLM()
        dialogue = [{"role": "user", "content": "Test streaming"}]

        print("Testing streaming LLM response...")
        response = ""
        for chunk in mock_streaming_llm(llm_instance, "streaming_test", dialogue):
            response += chunk
            print(f"   Received chunk: '{chunk}'")

        print(f"Complete response: '{response}'")

        # Flush data
        langfuse_tracker.client.flush()

        return True

    except Exception as e:
        print(f"[ERROR] Streaming test failed: {e}")
        return False

async def main():
    """Main test function"""
    print("Starting Full Conversation Flow Test with Langfuse...")

    # Check Langfuse is enabled
    if not langfuse_config.is_enabled():
        print("[ERROR] Langfuse is not enabled. Please check environment variables.")
        return False

    print(f"Langfuse enabled: {langfuse_config.is_enabled()}")

    # Test full conversation flow
    flow_success = await test_full_conversation_flow()

    # Test streaming functionality
    streaming_success = await test_streaming_llm_tracking()

    if flow_success and streaming_success:
        print("\n[SUCCESS] All conversation flow tests passed!")
        print("\nWhat you should see in Langfuse dashboard:")
        print("- ASR (Speech-to-Text) traces with audio processing metrics")
        print("- LLM traces with input/output tokens and costs")
        print("- TTS (Text-to-Speech) traces with text processing")
        print("- Complete conversation traces linked by session_id")
        print("\nReal-time conversations will now be fully tracked in Langfuse!")
    else:
        print("\n[ERROR] Some tests failed. Check error messages above.")

    return flow_success and streaming_success

if __name__ == "__main__":
    asyncio.run(main())