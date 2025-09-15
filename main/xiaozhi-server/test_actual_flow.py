#!/usr/bin/env python3
"""
Test the actual conversation flow that's happening based on logs
"""

import asyncio
import sys
import os

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_actual_providers():
    """Test the providers that are actually being used"""
    print("=== TESTING ACTUAL PROVIDER FLOW ===")

    try:
        # Test Langfuse first
        from config.langfuse_config import langfuse_config
        from core.providers.llm.langfuse_wrapper import langfuse_tracker

        print(f"Langfuse enabled: {langfuse_config.is_enabled()}")

        # Simulate the actual flow
        print("\n1. Testing ASR (AmazonTranscribeRealtime)...")

        # Test ASR tracking (the one that's actually being used)
        @langfuse_tracker.track_stt("amazon_transcribe_realtime")
        async def test_asr(opus_data, session_id, audio_format="opus"):
            """Test ASR tracking"""
            await asyncio.sleep(0.1)
            return "hello baby", "test_audio.wav"

        asr_result, audio_file = await test_asr([b"mock_audio"], "e317555d-deca-4b71-942d-854247528e51")
        print(f"   ASR result: {asr_result}")

        print("\n2. Testing LLM (GroqLLM via OpenAI provider)...")

        # Test LLM tracking
        @langfuse_tracker.track_llm_call("openai", "openai/gpt-oss-20b")
        def test_llm(self, session_id, dialogue, **kwargs):
            """Test LLM tracking"""
            responses = [
                "Hello there! ",
                "I'm Cheeko! ",
                "How are you doing today? ",
                "What fun things do you want to talk about?"
            ]
            for response in responses:
                yield response

        class MockLLM:
            def __init__(self):
                self.model_name = "openai/gpt-oss-20b"

        llm_instance = MockLLM()
        dialogue = [{"role": "user", "content": asr_result}]

        llm_response = ""
        for chunk in test_llm(llm_instance, "e317555d-deca-4b71-942d-854247528e51", dialogue):
            llm_response += chunk

        print(f"   LLM response: {llm_response}")

        print("\n3. Testing TTS (EdgeTTS)...")

        # Test TTS tracking
        @langfuse_tracker.track_tts("edge_tts")
        async def test_tts(text, output_file=None):
            """Test TTS tracking"""
            await asyncio.sleep(0.2)
            return b"mock_audio_data"

        tts_result = await test_tts(llm_response)
        print(f"   TTS result: Generated {len(tts_result)} bytes")

        print("\n4. Flushing Langfuse data...")
        langfuse_tracker.client.flush()
        print("   Data sent to Langfuse!")

        return True

    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_conversation_trace():
    """Test creating a full conversation trace"""
    print("\n=== TESTING FULL CONVERSATION TRACE ===")

    try:
        from config.langfuse_config import langfuse_config

        if not langfuse_config.is_enabled():
            print("Langfuse not enabled")
            return False

        client = langfuse_config.get_client()

        # Create a trace like the server does
        trace = client.trace(
            name="xiaozhi_conversation",
            session_id="e317555d-deca-4b71-942d-854247528e51",
            user_id="ESP32_Device",
            metadata={
                "device_id": "00:16:3e:ac:b5:38",
                "conversation_started": True,
                "input_text": "hello baby"
            }
        )

        print(f"Created trace: {trace.id}")

        # Add ASR span
        asr_span = trace.span(
            name="ASR_Processing",
            input={"audio_format": "opus", "session_id": "e317555d-deca-4b71-942d-854247528e51"},
            metadata={"provider": "amazon_transcribe_realtime"}
        )
        asr_span.update(output={"transcribed_text": "hello baby"})
        asr_span.end()

        # Add LLM generation
        llm_gen = trace.generation(
            name="LLM_Response",
            model="openai/gpt-oss-20b",
            input=[{"role": "user", "content": "hello baby"}],
            metadata={"provider": "groq", "session_id": "e317555d-deca-4b71-942d-854247528e51"}
        )
        llm_gen.update(output="Hello there! I'm Cheeko! How are you doing today?")
        llm_gen.end()

        # Add TTS span
        tts_span = trace.span(
            name="TTS_Processing",
            input={"text": "Hello there! I'm Cheeko! How are you doing today?"},
            metadata={"provider": "edge_tts", "voice": "en-US-AnaNeural"}
        )
        tts_span.update(output={"audio_generated": True, "bytes": 4096})
        tts_span.end()

        # End the trace
        trace.update(output={"conversation_complete": True, "total_exchanges": 1})

        # Flush data
        client.flush()

        print("Full conversation trace created and sent to Langfuse!")
        print(f"Check your dashboard for trace ID: {trace.id}")

        return True

    except Exception as e:
        print(f"[ERROR] Conversation trace test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    print("ACTUAL PROVIDER FLOW TEST")
    print("=" * 40)

    # Test provider flow
    flow_test = await test_actual_providers()

    # Test conversation trace
    trace_test = await test_conversation_trace()

    print("\n=== RESULTS ===")
    if flow_test and trace_test:
        print("[SUCCESS] All tests passed!")
        print("\nYour conversation should now appear in Langfuse dashboard with:")
        print("- ASR processing from Amazon Transcribe")
        print("- LLM responses from Groq (via OpenAI provider)")
        print("- TTS processing from EdgeTTS")
        print("- Complete conversation traces by session ID")

        print("\nIf you're still not seeing traces:")
        print("1. Check your Langfuse dashboard (cloud.langfuse.com)")
        print("2. Restart the server to pick up the new ASR tracking")
        print("3. Have a fresh conversation with your ESP32 device")

    else:
        print("[ERROR] Some tests failed")

    return flow_test and trace_test

if __name__ == "__main__":
    asyncio.run(main())