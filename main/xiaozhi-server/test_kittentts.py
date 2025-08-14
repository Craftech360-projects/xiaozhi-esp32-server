#!/usr/bin/env python3
"""
Test script for KittenTTS integration with xiaozhi-server
"""

import os
import sys
import asyncio

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from core.providers.tts.kittentts import TTSProvider

def test_kittentts():
    """Test KittenTTS provider"""
    print("Testing KittenTTS integration...")
    
    # Test configuration
    config = {
        "model_name": "KittenML/kitten-tts-nano-0.1",
        "voice": "expr-voice-5-m",
        "speed": 1.0,
        "sample_rate": 24000,
        "format": "wav",
        "output_dir": "tmp/"
    }
    
    try:
        # Initialize TTS provider
        print("Initializing KittenTTS provider...")
        tts_provider = TTSProvider(config, delete_audio_file=False)
        
        # Test text
        test_text = "Hello! This is a test of KittenTTS integration with xiaozhi-server."
        
        # Test file generation
        print(f"Generating speech for: '{test_text}'")
        output_file = "tmp/kittentts_test.wav"
        
        # Ensure output directory exists
        os.makedirs("tmp", exist_ok=True)
        
        # Generate speech
        result = asyncio.run(tts_provider.text_to_speak(test_text, output_file))
        
        if os.path.exists(output_file):
            print(f"✅ Success! Audio file generated: {output_file}")
            file_size = os.path.getsize(output_file)
            print(f"   File size: {file_size} bytes")
        else:
            print("❌ Failed: Audio file not generated")
            
        # Test audio data generation (without file)
        print("Testing audio data generation...")
        audio_bytes = asyncio.run(tts_provider.text_to_speak(test_text, None))
        
        if audio_bytes:
            print(f"✅ Success! Audio data generated: {len(audio_bytes)} bytes")
        else:
            print("❌ Failed: Audio data not generated")
            
        print(f"Available voices: {tts_provider.available_voices}")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_kittentts()