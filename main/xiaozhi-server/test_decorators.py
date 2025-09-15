#!/usr/bin/env python3
"""
Test script to verify Langfuse decorators work correctly.
This simulates actual function calls like those in your providers.
"""

import os
import sys
import time
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.providers.llm.langfuse_wrapper import langfuse_tracker

class MockLLMProvider:
    def __init__(self):
        self.model_name = "gpt-4o-mini"

    @langfuse_tracker.track_llm_call("openai")
    def response(self, session_id, dialogue, **kwargs):
        """Mock LLM response function"""
        time.sleep(0.1)  # Simulate processing time
        return "This is a mock response from the LLM provider."

class MockSTTProvider:
    @langfuse_tracker.track_stt("openai_whisper")
    async def speech_to_text(self, opus_data, session_id, audio_format="opus"):
        """Mock STT function"""
        time.sleep(0.1)  # Simulate processing time
        return "This is a mock transcription", "mock_file.wav"

class MockTTSProvider:
    @langfuse_tracker.track_tts("ttson")
    async def text_to_speak(self, text, output_file):
        """Mock TTS function"""
        time.sleep(0.1)  # Simulate processing time
        return True

async def test_decorators():
    """Test all decorators with mock functions"""
    print("Testing Langfuse decorators with mock functions...")
    
    # Test LLM decorator
    print("1. Testing LLM decorator...")
    llm = MockLLMProvider()
    result = llm.response(
        "test_session_123", 
        [{"role": "user", "content": "Hello, test!"}],
        temperature=0.7,
        max_tokens=100
    )
    print(f"   LLM result: {result}")
    
    # Test STT decorator  
    print("2. Testing STT decorator...")
    stt = MockSTTProvider()
    result = await stt.speech_to_text(
        [b"mock_audio_data"], 
        session_id="test_session_123",
        audio_format="opus"
    )
    print(f"   STT result: {result}")
    
    # Test TTS decorator
    print("3. Testing TTS decorator...")
    tts = MockTTSProvider()
    result = await tts.text_to_speak(
        "Hello, this is a test message for TTS",
        "output.mp3"
    )
    print(f"   TTS result: {result}")
    
    # Flush data
    print("4. Flushing data...")
    if langfuse_tracker.enabled:
        langfuse_tracker.client.flush()
        print("   Data flushed successfully")
    
    print("\n[SUCCESS] All decorators tested successfully!")
    print("[ACTION] Check your Langfuse dashboard for new traces with mock data.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_decorators())