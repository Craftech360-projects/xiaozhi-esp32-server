#!/usr/bin/env python3
"""
Test the music playback flow to verify timing of messages
"""

import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent / ".env")

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from services.music_service import MusicService
from services.unified_audio_player import UnifiedAudioPlayer
from agent.main_agent import Assistant

class MockSession:
    """Mock session for testing"""
    def __init__(self):
        self.messages = []
    
    async def say(self, text, allow_interruptions=True, **kwargs):
        """Mock say method that records messages"""
        print(f"🎤 TTS: {text}")
        self.messages.append(text)
        # Simulate TTS delay
        await asyncio.sleep(0.1)

class MockContext:
    """Mock context for testing"""
    def __init__(self):
        self.room = MockRoom()

class MockRoom:
    """Mock room for testing"""
    def __init__(self):
        self.local_participant = MockParticipant()

class MockParticipant:
    """Mock participant for testing"""
    async def publish_data(self, data, topic=None, reliable=False):
        """Mock data channel"""
        import json
        try:
            message = json.loads(data.decode())
            print(f"📡 Data Channel [{topic}]: {message}")
        except:
            print(f"📡 Data Channel [{topic}]: {data}")

async def test_music_flow():
    """Test the complete music playback flow"""
    print("🎵 Testing Music Playback Flow...")
    
    # Initialize services
    music_service = MusicService()
    audio_player = UnifiedAudioPlayer()
    assistant = Assistant()
    
    # Create mock session and context
    mock_session = MockSession()
    mock_context = MockContext()
    
    # Set up the audio player with mocks
    audio_player.set_session(mock_session)
    audio_player.set_context(mock_context)
    
    # Set up the assistant
    assistant.set_services(music_service, None, None, audio_player)
    
    # Initialize music service
    print("\n1. Initializing music service...")
    music_init = await music_service.initialize()
    if not music_init:
        print("❌ Music service initialization failed")
        return
    
    print("✅ Music service initialized")
    
    # Test music playback flow
    print("\n2. Testing music playback flow...")
    print("📝 Expected flow:")
    print("   1. Function called")
    print("   2. Music starts (no immediate TTS)")
    print("   3. Data channel message sent")
    print("   4. Music plays...")
    print("   5. Completion message via TTS")
    print("   6. Agent returns to listening")
    
    print("\n🎵 Calling play_music function...")
    
    # Call the play_music function
    result = await assistant.play_music(mock_context, song_name="baby shark")
    
    print(f"📤 Function returned: '{result}'")
    
    # Wait a bit to see if any async tasks complete
    print("\n⏳ Waiting for background tasks...")
    await asyncio.sleep(2)
    
    # Check what messages were sent
    print(f"\n📊 TTS Messages sent: {len(mock_session.messages)}")
    for i, msg in enumerate(mock_session.messages):
        print(f"   {i+1}. {msg}")
    
    print("\n✅ Music flow test completed!")
    
    print("\n🔧 Expected behavior:")
    print("   - Function returns empty string (no immediate TTS)")
    print("   - Data channel sends start notification")
    print("   - Music plays without TTS interference")
    print("   - Completion message sent after music ends")

if __name__ == "__main__":
    asyncio.run(test_music_flow())