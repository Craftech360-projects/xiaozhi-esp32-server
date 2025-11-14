#!/usr/bin/env python3
"""
Test script for remote Whisper and Piper services
"""
import requests
import json
import sys
import io
import wave
import struct

def test_whisper_health(base_url="http://192.168.1.114:8000"):
    """Test Whisper server health endpoint"""
    print(f"\n🔍 Testing Whisper Health at {base_url}/health")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Whisper Server: {data}")
            return True
        else:
            print(f"❌ Whisper Health Check Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Whisper Connection Error: {e}")
        return False

def test_piper_health(base_url="http://192.168.1.114:8001"):
    """Test Piper server health endpoint"""
    print(f"\n🔍 Testing Piper Health at {base_url}/health")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Piper Server: {data}")
            return True
        else:
            print(f"❌ Piper Health Check Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Piper Connection Error: {e}")
        return False

def create_test_audio():
    """Create a simple test audio file (1 second of silence)"""
    print("\n🎵 Creating test audio file...")
    sample_rate = 16000
    duration = 1  # seconds
    
    # Create WAV file in memory
    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        
        # Generate 1 second of silence
        for _ in range(sample_rate * duration):
            wav_file.writeframes(struct.pack('<h', 0))
    
    buffer.seek(0)
    print("✅ Test audio created (1 second of silence)")
    return buffer.getvalue()

def test_whisper_transcribe(base_url="http://192.168.1.114:8000"):
    """Test Whisper transcription with test audio"""
    print(f"\n🎤 Testing Whisper Transcription at {base_url}/transcribe")
    try:
        audio_data = create_test_audio()
        
        files = {
            'audio': ('test.wav', audio_data, 'audio/wav')
        }
        data = {
            'language': 'en'
        }
        
        response = requests.post(
            f"{base_url}/transcribe",
            files=files,
            data=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Transcription Result: {result}")
            return True
        else:
            print(f"❌ Transcription Failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Transcription Error: {e}")
        return False

def test_piper_synthesize(base_url="http://192.168.1.114:8001"):
    """Test Piper TTS synthesis"""
    print(f"\n🔊 Testing Piper Synthesis at {base_url}/synthesize")
    try:
        payload = {
            "text": "Hello, this is a test of the remote Piper server."
        }
        
        response = requests.post(
            f"{base_url}/synthesize",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            audio_size = len(response.content)
            print(f"✅ Synthesis Successful: Received {audio_size} bytes of audio")
            
            # Save to file for verification
            with open('test_piper_output.wav', 'wb') as f:
                f.write(response.content)
            print(f"   Audio saved to: test_piper_output.wav")
            return True
        else:
            print(f"❌ Synthesis Failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Synthesis Error: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 Remote Services Test Suite")
    print("=" * 60)
    
    results = {
        "Whisper Health": test_whisper_health(),
        "Piper Health": test_piper_health(),
        "Whisper Transcription": test_whisper_transcribe(),
        "Piper Synthesis": test_piper_synthesize()
    }
    
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:.<40} {status}")
    
    print("=" * 60)
    
    all_passed = all(results.values())
    if all_passed:
        print("\n🎉 All tests passed! Remote services are working correctly.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
