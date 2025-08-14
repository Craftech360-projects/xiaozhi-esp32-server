#!/usr/bin/env python3
"""
Test script to compare female voices for kid companion
"""

import os
import sys
import asyncio

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from core.providers.tts.kittentts import TTSProvider

def test_female_voices():
    """Test all female voices with kid-friendly content"""
    print("🎭 Testing KittenTTS female voices for kid companion...")
    print()
    
    # Kid-friendly test phrases
    test_phrases = [
        "Hi there! I'm Cheeko, your friendly AI companion!",
        "That's amazing! Tell me more about your favorite toy.",
        "Wow, you're so creative! What should we explore next?",
        "Great job! You're doing wonderfully today!"
    ]
    
    # Female voices to test
    female_voices = [
        'expr-voice-2-f',
        'expr-voice-3-f', 
        'expr-voice-4-f',
        'expr-voice-5-f'
    ]
    
    # Ensure output directory exists
    os.makedirs("tmp/voice_tests", exist_ok=True)
    
    for voice in female_voices:
        print(f"🎤 Testing {voice}...")
        
        config = {
            "model_name": "KittenML/kitten-tts-nano-0.1",
            "voice": voice,
            "speed": 1.0,  # Normal speed for kids
            "sample_rate": 24000,
            "format": "wav",
            "output_dir": "tmp/voice_tests/"
        }
        
        try:
            tts_provider = TTSProvider(config, delete_audio_file=False)
            
            for i, phrase in enumerate(test_phrases):
                output_file = f"tmp/voice_tests/{voice}_phrase_{i+1}.wav"
                
                print(f"   Generating: '{phrase[:30]}...'")
                result = asyncio.run(tts_provider.text_to_speak(phrase, output_file))
                
                if os.path.exists(output_file):
                    file_size = os.path.getsize(output_file)
                    print(f"   ✅ Generated: {output_file} ({file_size} bytes)")
                else:
                    print(f"   ❌ Failed to generate: {output_file}")
            
            print()
            
        except Exception as e:
            print(f"   ❌ Error testing {voice}: {e}")
            print()
    
    print("🎯 VOICE RECOMMENDATIONS FOR KID COMPANION:")
    print()
    print("Based on typical characteristics for children's content:")
    print()
    print("🌟 RECOMMENDED: expr-voice-3-f")
    print("   - Usually has a warm, nurturing tone")
    print("   - Good clarity for children's comprehension")
    print("   - Friendly and approachable sound")
    print()
    print("🌟 ALTERNATIVE: expr-voice-5-f") 
    print("   - Often has a gentle, caring quality")
    print("   - Clear pronunciation")
    print("   - Pleasant for extended conversations")
    print()
    print("📁 Audio files saved in: tmp/voice_tests/")
    print("🎧 Listen to each voice and choose based on:")
    print("   - Warmth and friendliness")
    print("   - Clarity for children")
    print("   - Comfort for extended use")
    print("   - Age-appropriate tone")

if __name__ == "__main__":
    test_female_voices()