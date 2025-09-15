#!/usr/bin/env python3
"""
Test script to verify complete conversation flow tracking with Langfuse
This script simulates STT -> LLM -> TTS flow and verifies proper tracing
"""

import sys
import os
import asyncio
import time
from unittest.mock import Mock

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.providers.llm.langfuse_wrapper import langfuse_tracker
from config.langfuse_config import langfuse_config

def test_langfuse_client():
    """Test if Langfuse client is properly initialized"""
    print("=== Testing Langfuse Client ===")

    client = langfuse_config.get_client()
    enabled = langfuse_config.is_enabled()

    print(f"Langfuse enabled: {enabled}")
    print(f"Client available: {client is not None}")

    if client:
        methods = [m for m in dir(client) if m in ['generation', 'event', 'span', 'trace']]
        print(f"API methods available: {methods}")

        # Test creating a simple trace
        try:
            trace = client.trace(
                name="test_trace",
                input={"test": "data"},
                metadata={"test_mode": True}
            )
            print(f"Test trace created successfully: {trace.id if hasattr(trace, 'id') else 'unknown'}")
            client.flush()
            return True
        except Exception as e:
            print(f"Failed to create test trace: {e}")
            return False
    else:
        print("No client available - check your .env configuration")
        return False

def simulate_stt_operation():
    """Simulate STT operation"""
    print("\n=== Simulating STT Operation ===")

    @langfuse_tracker.track_stt("test_stt")
    async def mock_stt(opus_data, session_id, audio_format="opus"):
        """Mock STT function"""
        await asyncio.sleep(0.1)  # Simulate processing time
        return "Hello, how are you today?"

    # Mock data
    mock_opus_data = [b"fake_audio_chunk_1", b"fake_audio_chunk_2"]
    session_id = "test_session_123"

    # Run the simulation
    result = asyncio.run(mock_stt(mock_opus_data, session_id))
    print(f"STT Result: {result}")
    return result, session_id

def simulate_llm_operation(stt_text, session_id):
    """Simulate LLM operation"""
    print("\n=== Simulating LLM Operation ===")

    @langfuse_tracker.track_llm_call("test_llm", "gpt-3.5-turbo")
    def mock_llm(self, session_id, dialogue):
        """Mock LLM function"""
        time.sleep(0.2)  # Simulate processing time
        for chunk in ["I'm", " doing", " great", ", thank", " you", "!"]:
            yield chunk

    # Create mock self object
    mock_self = Mock()
    mock_self.model_name = "gpt-3.5-turbo"

    # Mock dialogue
    dialogue = [
        {"role": "user", "content": stt_text}
    ]

    # Run the simulation
    result_chunks = []
    for chunk in mock_llm(mock_self, session_id, dialogue):
        result_chunks.append(chunk)

    llm_response = "".join(result_chunks)
    print(f"LLM Result: {llm_response}")
    return llm_response

def simulate_tts_operation(llm_text, session_id):
    """Simulate TTS operation"""
    print("\n=== Simulating TTS Operation ===")

    @langfuse_tracker.track_tts("test_tts")
    async def mock_tts(text, output_file):
        """Mock TTS function"""
        await asyncio.sleep(0.15)  # Simulate processing time
        return b"fake_audio_data"

    # Create mock TTS object with session info
    mock_tts_obj = Mock()
    mock_tts_obj._current_session_id = session_id
    mock_tts_obj.conn = Mock()
    mock_tts_obj.conn.session_id = session_id

    # Run the simulation
    result = asyncio.run(mock_tts(llm_text, None))
    print(f"TTS Result: Generated {len(result)} bytes of audio")
    return result

def simulate_complete_conversation_flow():
    """Simulate complete conversation flow"""
    print("\n" + "="*50)
    print("SIMULATING COMPLETE CONVERSATION FLOW")
    print("="*50)

    # Step 1: STT
    stt_result, session_id = simulate_stt_operation()

    # Step 2: LLM
    llm_result = simulate_llm_operation(stt_result, session_id)

    # Step 3: TTS
    tts_result = simulate_tts_operation(llm_result, session_id)

    # Flush to ensure all data is sent
    if langfuse_tracker.enabled and langfuse_tracker.client:
        langfuse_tracker.client.flush()
        print("\nFlushed Langfuse data")

    print("\n" + "="*50)
    print("CONVERSATION FLOW SIMULATION COMPLETE")
    print("="*50)

    return {
        "session_id": session_id,
        "stt_result": stt_result,
        "llm_result": llm_result,
        "tts_result": len(tts_result) if tts_result else 0
    }

def main():
    """Main test function"""
    print("Langfuse Conversation Flow Test")
    print("="*50)

    # Test 1: Basic client functionality
    client_works = test_langfuse_client()

    if not client_works:
        print("\n❌ Langfuse client test failed. Check your configuration.")
        return False

    # Test 2: Complete conversation flow
    try:
        result = simulate_complete_conversation_flow()

        print(f"\n✅ Conversation flow simulation completed:")
        print(f"   Session ID: {result['session_id']}")
        print(f"   STT Result: {result['stt_result']}")
        print(f"   LLM Result: {result['llm_result']}")
        print(f"   TTS Result: {result['tts_result']} bytes")

        print(f"\n✅ Check your Langfuse dashboard for session: {result['session_id']}")
        print("   You should see:")
        print("   1. A conversation trace with STT -> LLM -> TTS flow")
        print("   2. Proper input/output mapping")
        print("   3. Response times and costs for each step")

        return True

    except Exception as e:
        print(f"\n❌ Conversation flow simulation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n💥 Tests failed!")
        sys.exit(1)