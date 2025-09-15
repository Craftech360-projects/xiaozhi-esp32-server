#!/usr/bin/env python3
"""
Test script for the fixed Langfuse integration
"""

import sys
import os
import asyncio
import time
from unittest.mock import Mock

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.providers.llm.langfuse_wrapper_fixed import langfuse_tracker

def test_api_compatibility():
    """Test that all the API methods we're using actually exist"""
    print("=== Testing Langfuse API Compatibility ===")

    if not langfuse_tracker.enabled:
        print("❌ Langfuse is disabled - check your configuration")
        return False

    client = langfuse_tracker.client

    # Test required methods exist
    required_methods = ['create_trace_id', 'start_span', 'start_generation', 'flush']

    for method in required_methods:
        if hasattr(client, method):
            print(f"✅ {method} - available")
        else:
            print(f"❌ {method} - missing")
            return False

    # Test creating a trace ID
    try:
        trace_id = client.create_trace_id()
        print(f"✅ create_trace_id() works: {trace_id}")
    except Exception as e:
        print(f"❌ create_trace_id() failed: {e}")
        return False

    # Test creating a span
    try:
        span = client.start_span(
            name="test_span",
            trace_id=trace_id,
            input={"test": "data"},
            output={"result": "success"},
            metadata={"test_mode": True}
        )
        span.end()
        print("✅ start_span() works")
    except Exception as e:
        print(f"❌ start_span() failed: {e}")
        return False

    # Test creating a generation
    try:
        gen = client.start_generation(
            name="test_generation",
            trace_id=trace_id,
            input={"prompt": "Hello"},
            output={"response": "Hi there!"},
            model="test-model",
            metadata={"test_mode": True}
        )
        gen.end()
        print("✅ start_generation() works")
    except Exception as e:
        print(f"❌ start_generation() failed: {e}")
        return False

    # Test flush
    try:
        client.flush()
        print("✅ flush() works")
    except Exception as e:
        print(f"❌ flush() failed: {e}")
        return False

    return True

def test_conversation_flow():
    """Test the complete conversation flow tracking"""
    print("\n=== Testing Conversation Flow ===")

    session_id = "test_session_12345"

    # Step 1: STT
    print("Testing STT tracking...")

    @langfuse_tracker.track_stt("test_stt")
    async def mock_stt(opus_data, session_id, audio_format="opus"):
        await asyncio.sleep(0.05)  # Simulate processing
        return "Hello, how are you today?"

    stt_result = asyncio.run(mock_stt([b"fake_audio"], session_id))
    print(f"STT Result: {stt_result}")

    # Step 2: LLM
    print("Testing LLM tracking...")

    @langfuse_tracker.track_llm_call("test_llm", "gpt-3.5-turbo")
    def mock_llm(self, session_id, dialogue):
        time.sleep(0.1)  # Simulate processing
        for chunk in ["I'm", " doing", " great", ", thanks", "!"]:
            yield chunk

    mock_self = Mock()
    mock_self.model_name = "gpt-3.5-turbo"

    dialogue = [{"role": "user", "content": stt_result}]

    llm_chunks = []
    for chunk in mock_llm(mock_self, session_id, dialogue):
        llm_chunks.append(chunk)

    llm_result = "".join(llm_chunks)
    print(f"LLM Result: {llm_result}")

    # Step 3: TTS
    print("Testing TTS tracking...")

    @langfuse_tracker.track_tts("test_tts")
    async def mock_tts(text, output_file):
        await asyncio.sleep(0.08)  # Simulate processing
        return b"fake_audio_output"

    # Create mock TTS object with session info
    mock_tts_obj = Mock()
    mock_tts_obj._current_session_id = session_id

    tts_result = asyncio.run(mock_tts(llm_result, None))
    print(f"TTS Result: {len(tts_result)} bytes generated")

    # Flush all data
    langfuse_tracker.client.flush()

    print("✅ Complete conversation flow tested")

    return {
        "session_id": session_id,
        "stt": stt_result,
        "llm": llm_result,
        "tts": len(tts_result)
    }

def main():
    """Main test function"""
    print("Langfuse Fixed Integration Test")
    print("="*50)

    # Test 1: API compatibility
    if not test_api_compatibility():
        print("\n❌ API compatibility test failed")
        return False

    # Test 2: Conversation flow
    try:
        result = test_conversation_flow()

        print(f"\n✅ All tests passed!")
        print(f"Session tracked: {result['session_id']}")
        print(f"STT: {result['stt']}")
        print(f"LLM: {result['llm']}")
        print(f"TTS: {result['tts']} bytes")

        print(f"\n🎯 Check your Langfuse dashboard for trace: {result['session_id']}")
        print("Expected structure:")
        print("  📊 Conversation Trace")
        print("  ├── 🎤 STT-test_stt (audio → text)")
        print("  ├── 🤖 LLM-test_llm-STREAM (text → response)")
        print("  └── 🔊 TTS-test_tts (text → audio)")
        print("  ")
        print("  Each step should show:")
        print("  • Proper input/output mapping")
        print("  • Response times")
        print("  • Token usage and costs (for LLM)")

        return True

    except Exception as e:
        print(f"\n❌ Conversation flow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 All tests passed! The fixed Langfuse integration is working.")
        sys.exit(0)
    else:
        print("\n💥 Tests failed!")
        sys.exit(1)