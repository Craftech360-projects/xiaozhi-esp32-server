#!/usr/bin/env python3
"""
Example of using Cartesia TTS directly in LiveKit Agent
Shows both the AgentSession approach and direct TTS usage
"""

import asyncio
import os
from dotenv import load_dotenv
from livekit.agents import AgentSession, inference
from livekit.plugins import cartesia

# Load environment variables
load_dotenv(".env")

async def cartesia_direct_example():
    """Example of using Cartesia TTS directly"""
    print("🎵 Testing Cartesia TTS directly...")
    
    # Create Cartesia TTS instance
    tts = cartesia.TTS(
        model="sonic-english",  # or "sonic-multilingual"
        voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc",  # Child-friendly voice
        language="en"
    )
    
    # Test synthesis
    text = "Hello! I'm Cheeko, your friendly AI companion. Ready for some fun adventures?"
    
    try:
        # Synthesize speech
        audio_stream = tts.synthesize(text)
        
        # Process audio frames
        frame_count = 0
        async for audio_frame in audio_stream:
            frame_count += 1
            print(f"📡 Received audio frame {frame_count}: {len(audio_frame.data)} samples")
            
            # In real usage, you'd send this to LiveKit room
            # await room.local_participant.publish_track(audio_track)
            
        print(f"✅ Cartesia TTS completed - {frame_count} frames generated")
        
    except Exception as e:
        print(f"❌ Cartesia TTS error: {e}")

def create_cartesia_agent_session():
    """Example of using Cartesia in AgentSession (your approach)"""
    print("🤖 Creating AgentSession with Cartesia TTS...")
    
    # Method 1: Using inference.TTS (your approach)
    session = AgentSession(
        tts=inference.TTS(
            model="cartesia/sonic-english",  # Note the cartesia/ prefix
            voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc",
            language="en"
        ),
        # ... other components (stt, llm, vad, etc.)
    )
    
    print("✅ AgentSession created with Cartesia TTS")
    return session

def cartesia_voice_options():
    """Show available Cartesia voice options"""
    print("🎭 Cartesia Voice Options for Kids:")
    
    voices = {
        "Child-friendly voices": {
            "9626c31c-bec5-4cca-baa8-f8ba9e84c8bc": "Young, energetic voice (recommended for Cheeko)",
            "a0e99841-438c-4a64-b679-ae501e7d6091": "Friendly, warm voice",
            "2ee87190-8f84-4925-97da-e52547f9462c": "Playful, animated voice"
        },
        "Adult voices (backup)": {
            "79a125e8-cd45-4c13-8a67-188112f4dd22": "Clear, professional female",
            "87748186-23bb-4158-a1eb-332911b0b708": "Warm, storytelling voice"
        }
    }
    
    for category, voice_list in voices.items():
        print(f"\n{category}:")
        for voice_id, description in voice_list.items():
            print(f"  {voice_id}: {description}")

def cartesia_model_options():
    """Show available Cartesia model options"""
    print("🧠 Cartesia Model Options:")
    
    models = {
        "sonic-english": "Optimized for English, fastest performance",
        "sonic-multilingual": "Supports multiple languages, slightly slower"
    }
    
    for model, description in models.items():
        print(f"  {model}: {description}")

async def main():
    """Main example function"""
    print("🚀 Cartesia TTS Examples for LiveKit")
    print("=" * 50)
    
    # Show configuration options
    cartesia_model_options()
    print()
    cartesia_voice_options()
    print()
    
    # Test direct usage
    await cartesia_direct_example()
    print()
    
    # Show AgentSession approach
    session = create_cartesia_agent_session()
    print()
    
    print("🎯 Integration Tips:")
    print("1. Use 'sonic-english' for best performance with English")
    print("2. Child voice ID '9626c31c-bec5-4cca-baa8-f8ba9e84c8bc' works great for Cheeko")
    print("3. Cartesia has very low latency (~200ms) compared to other TTS providers")
    print("4. Set CARTESIA_API_KEY in your .env file")
    print("5. Your current .env is already configured for Cartesia!")

if __name__ == "__main__":
    asyncio.run(main())