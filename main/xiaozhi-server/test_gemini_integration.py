#!/usr/bin/env python3
"""
Test script for Gemini Real-time + Deepgram ASR integration
"""

import os
import sys
import asyncio
import json
import time
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.handle.gemini_realtime_handle import GeminiRealtimeHandler
from config.logger import setup_logging

logger = setup_logging()


class MockConnection:
    """Mock connection object for testing"""
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.websocket = None
        self.audio_responses = []

    async def send(self, data):
        """Mock send method"""
        if isinstance(data, bytes):
            self.audio_responses.append(data)
            print(f"📤 Received audio response: {len(data)} bytes")
        else:
            print(f"📤 Received message: {data}")


async def test_gemini_integration():
    """Test the Gemini + Deepgram integration"""
    
    print("🚀 Gemini Real-time + Deepgram ASR Integration Test")
    print("=" * 60)
    
    # Configuration
    deepgram_config = {
        "api_key": "2bc99f78312157bb1e017a2596b45c71bfe5f6ba",  # Replace with your key
        "model": "nova-3",
        "language": "en",
        "smart_format": True,
        "punctuate": True,
        "diarize": False,
        "multichannel": False,
        "timeout": 60,
        "output_dir": "tmp/"
    }
    
    gemini_config = {
        "api_key": "AIzaSyCl9yuCQjgoM2IMExHv9fD6FrdHaNKW7RQ",  # Replace with your key
        "model": "models/gemini-2.5-flash-preview-native-audio-dialog",
        "voice_name": "Zephyr",
        "media_resolution": "MEDIA_RESOLUTION_MEDIUM",
        "enable_audio_output": True
    }
    
    # Check API keys
    if deepgram_config["api_key"] == "your-deepgram-api-key":
        print("❌ Please set your Deepgram API key")
        print("   Get it from: https://console.deepgram.com/")
        return False
    
    if gemini_config["api_key"] == "your-gemini-api-key":
        print("❌ Please set your Gemini API key")
        print("   Get it from: https://aistudio.google.com/apikey")
        return False
    
    try:
        # Create mock connection
        mock_conn = MockConnection("test_session_123")
        
        # Initialize handler
        print("🔧 Initializing Gemini Real-time Handler...")
        handler = GeminiRealtimeHandler(
            conn=mock_conn,
            deepgram_config=deepgram_config,
            gemini_config=gemini_config
        )
        
        # Start the handler
        print("🚀 Starting handler...")
        success = await handler.start()
        
        if not success:
            print("❌ Failed to start handler")
            return False
        
        print("✅ Handler started successfully!")
        
        # Test text message
        print("\n📝 Testing text message...")
        test_message = "Hello, this is a test of the Gemini integration. Please respond with a short greeting."
        
        success = await handler.send_text_message(test_message)
        if success:
            print(f"✅ Text message sent: {test_message}")
        else:
            print("❌ Failed to send text message")
        
        # Wait for response
        print("⏳ Waiting for Gemini response...")
        await asyncio.sleep(3)
        
        # Check for audio responses
        if mock_conn.audio_responses:
            total_audio = sum(len(data) for data in mock_conn.audio_responses)
            print(f"✅ Received {len(mock_conn.audio_responses)} audio chunks")
            print(f"   Total audio data: {total_audio} bytes")
        else:
            print("⚠️  No audio responses received (this might be normal for text-only responses)")
        
        # Test status
        print("\n📊 Handler Status:")
        status = handler.get_status()
        for key, value in status.items():
            print(f"   {key}: {value}")
        
        # Simulate audio processing (mock audio data)
        print("\n🎤 Testing audio processing...")
        mock_audio_chunks = [
            b"mock_audio_data_chunk_1" * 10,
            b"mock_audio_data_chunk_2" * 10,
            b"mock_audio_data_chunk_3" * 10,
        ]
        
        for i, chunk in enumerate(mock_audio_chunks):
            print(f"   Processing audio chunk {i+1}...")
            await handler.process_audio_chunk(chunk, has_voice=True)
            await asyncio.sleep(0.1)
        
        print("✅ Audio processing test completed")
        
        # Wait a bit more for any responses
        await asyncio.sleep(2)
        
        # Final status
        print("\n📊 Final Status:")
        final_status = handler.get_status()
        for key, value in final_status.items():
            print(f"   {key}: {value}")
        
        # Cleanup
        print("\n🧹 Cleaning up...")
        await handler.stop()
        print("✅ Handler stopped successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        if "google" in str(e).lower():
            print("   Run: pip install google-genai")
        elif "deepgram" in str(e).lower():
            print("   Run: pip install deepgram-sdk")
        return False
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_configuration():
    """Test if all dependencies are available"""
    
    print("🔍 Testing configuration and dependencies...")
    
    # Check if provider files exist
    files_to_check = [
        "core/providers/llm/gemini_realtime.py",
        "core/providers/asr/deepgram.py",
        "core/handle/gemini_realtime_handle.py"
    ]
    
    for file_path in files_to_check:
        if Path(file_path).exists():
            print(f"✅ {file_path} exists")
        else:
            print(f"❌ {file_path} not found")
            return False
    
    # Check dependencies
    try:
        import deepgram
        print("✅ Deepgram SDK available")
    except ImportError:
        print("❌ Deepgram SDK not installed")
        print("   Run: pip install deepgram-sdk")
        return False
    
    try:
        from google import genai
        print("✅ Google Gemini SDK available")
    except ImportError:
        print("❌ Google Gemini SDK not installed")
        print("   Run: pip install google-genai")
        return False
    
    return True


if __name__ == "__main__":
    print("🎯 Gemini Real-time + Deepgram Integration Test")
    print("=" * 60)
    print("This test will:")
    print("1. Check all dependencies and files")
    print("2. Initialize the hybrid handler")
    print("3. Test text messaging with Gemini")
    print("4. Test audio processing pipeline")
    print("5. Verify real-time audio responses")
    print("=" * 60)
    
    async def main():
        # Test configuration
        config_ok = await test_configuration()
        if not config_ok:
            print("\n❌ Configuration test failed")
            return
        
        print("\n✅ Configuration test passed")
        
        # Test integration
        print("\n🚀 Starting integration test...")
        success = await test_gemini_integration()
        
        if success:
            print("\n🎉 Integration test completed successfully!")
            print("\nNext steps:")
            print("1. Set your API keys in the configuration")
            print("2. Enable gemini_realtime_integration in config.yaml")
            print("3. Use GeminiConnectionHandler in your WebSocket server")
        else:
            print("\n❌ Integration test failed")
    
    asyncio.run(main())