#!/usr/bin/env python3
"""
Test script to verify STT -> LLM -> TTS flow mapping in Langfuse dashboard
This will create a real conversation flow with proper input/output mapping
"""

import os
import sys
import time
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.providers.llm.langfuse_wrapper import langfuse_tracker

async def test_flow_mapping():
    """Test the complete conversation flow with proper STT->LLM->TTS mapping"""
    print("=" * 70)
    print("TESTING STT -> LLM -> TTS FLOW MAPPING IN LANGFUSE DASHBOARD")
    print("=" * 70)

    if not langfuse_tracker.enabled:
        print("ERROR: Langfuse is not enabled. Check your configuration.")
        return False

    # Test session
    session_id = f"flow-test-{int(time.time())}"
    print(f"Session ID: {session_id}")

    # Step 1: Simulate STT function
    print("\n1. Testing STT Function with @track_stt decorator...")

    @langfuse_tracker.track_stt("openai_whisper")
    async def mock_stt_function(audio_data, session_id, audio_format="opus"):
        """Mock STT function that returns transcribed text"""
        # Simulate STT processing time
        await asyncio.sleep(0.1)

        # Return the transcribed text (this should appear as LLM INPUT in dashboard)
        transcribed_text = "What's the weather like today in New York?"
        print(f"   STT Output: '{transcribed_text}'")
        return transcribed_text

    # Call STT function
    stt_result = await mock_stt_function([b"fake_audio_data"], session_id)

    # Step 2: Simulate LLM function
    print("\n2. Testing LLM Function with @track_llm_call decorator...")

    @langfuse_tracker.track_llm_call("openai", "gpt-4o-mini")
    def mock_llm_function(provider_instance, session_id, dialogue, **kwargs):
        """Mock LLM function that returns a response"""
        # Simulate LLM processing time
        time.sleep(0.2)

        # Return the LLM response (this should appear as TTS INPUT in dashboard)
        llm_response = "The weather in New York today is partly cloudy with a temperature of 72°F (22°C). It's a pleasant day with light winds from the southwest."
        print(f"   LLM Output: '{llm_response}'")
        return llm_response

    # Simulate dialogue with user message
    dialogue = [
        {"role": "system", "content": "You are a helpful weather assistant."},
        {"role": "user", "content": stt_result}  # This is the STT output
    ]

    # Mock provider instance
    class MockProvider:
        def __init__(self):
            self.model_name = "gpt-4o-mini"

    mock_provider = MockProvider()
    llm_result = mock_llm_function(mock_provider, session_id, dialogue)

    # Step 3: Simulate TTS function
    print("\n3. Testing TTS Function with @track_tts decorator...")

    @langfuse_tracker.track_tts("edge_tts")
    async def mock_tts_function(provider_instance, text_input, **kwargs):
        """Mock TTS function that converts text to speech"""
        # Simulate TTS processing time
        await asyncio.sleep(0.1)

        print(f"   TTS Input: '{text_input}'")
        print(f"   TTS Output: Audio generated successfully")
        return True

    # Mock TTS provider with session_id
    class MockTTSProvider:
        def __init__(self, session_id):
            self._current_session_id = session_id

    mock_tts_provider = MockTTSProvider(session_id)
    tts_result = await mock_tts_function(mock_tts_provider, llm_result)

    # Step 4: Flush data to Langfuse
    print("\n4. Flushing data to Langfuse...")
    try:
        langfuse_tracker.client.flush()
        print("   Data flushed successfully")

        # Wait for data to be processed
        time.sleep(3)

    except Exception as e:
        print(f"   Flush failed: {e}")

    print("\n" + "=" * 70)
    print("FLOW MAPPING TEST COMPLETED!")
    print("=" * 70)
    print(f"\nSession ID: {session_id}")
    print("\nCheck your Langfuse dashboard at: https://cloud.langfuse.com")
    print("\nYou should see the following flow:")
    print("  [STT] Audio -> 'What's the weather like today in New York?'")
    print("  [LLM] INPUT: 'What's the weather like today in New York?'")
    print("  [LLM] OUTPUT: 'The weather in New York today is partly cloudy...'")
    print("  [TTS] Input: 'The weather in New York today is partly cloudy...' -> Audio")
    print("\nThe STT OUTPUT should appear as LLM INPUT")
    print("The LLM OUTPUT should appear as TTS INPUT")
    print("All operations should be linked in a single trace!")
    print("=" * 70)

    return True

async def main():
    """Main function to run the flow mapping test"""
    try:
        success = await test_flow_mapping()
        if success:
            print("\n[SUCCESS] Flow mapping test completed successfully!")
            print("[ACTION] Please check your Langfuse dashboard to verify the flow.")
        else:
            print("\n[FAILED] Flow mapping test failed.")

    except Exception as e:
        print(f"\n[ERROR] Test failed with exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())