#!/usr/bin/env python3
"""
Test script for Deepgram ASR integration with microphone input or a local file.
This version is self-contained and uses a specific Deepgram API URL.
"""

import os
import sys
import asyncio
import wave
import time
from pathlib import Path

# --- Dependency Installation ---
try:
    import aiohttp
except ImportError:
    print("❌ aiohttp not installed. Installing...")
    os.system(f"{sys.executable} -m pip install aiohttp")
    import aiohttp

try:
    import pyaudio
except ImportError:
    print("❌ PyAudio not installed. Installing...")
    os.system(f"{sys.executable} -m pip install pyaudio")
    import pyaudio

# --- Self-Contained ASRProvider Class ---

class ASRProvider:
    """
    A self-contained provider to interact with the Deepgram API using a specific URL.
    """
    def __init__(self, config, delete_audio_file=False):
        # The URL is now hardcoded as per the request.
        # Config values like model, language, etc., are for display purposes.
        self.url = 'https://api.deepgram.com/v1/listen?model=nova-3&smart_format=true'
        self.config = config
        self.api_key = config.get("api_key")
        # The delete_audio_file and output_dir are no longer used by this provider
        # as it doesn't handle file saving, but we keep the signature for compatibility.

    async def speech_to_text(self, pcm_data=None, session_id=None, audio_format=None, audio_file=None):
        """
        Transcribes audio by sending it to the configured Deepgram URL.
        It prioritizes the audio_file path if provided.
        """
        if not self.api_key:
            raise ValueError("Deepgram API key is not configured.")

        audio_data = None
        if audio_file and os.path.exists(audio_file):
            with open(audio_file, 'rb') as f:
                audio_data = f.read()
        elif pcm_data:
            # This path is less preferred now; sending a file is more robust.
            audio_data = b''.join(pcm_data)
        
        if not audio_data:
            print("❌ No audio data provided to transcribe.")
            return None, None

        headers = {
            'Authorization': f'Token {self.api_key}',
            'Content-Type': 'audio/wav' # Assuming WAV format for simplicity
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(self.url, headers=headers, data=audio_data) as response:
                    if response.status == 200:
                        result = await response.json()
                        transcript = result.get('results', {}).get('channels', [{}])[0].get('alternatives', [{}])[0].get('transcript', '')
                        return transcript, audio_file
                    else:
                        error_text = await response.text()
                        print(f"❌ Deepgram API Error (Status {response.status}): {error_text}")
                        return None, audio_file
            except aiohttp.ClientError as e:
                print(f"❌ Network or connection error: {e}")
                return None, audio_file


def record_audio_from_mic(duration=5, sample_rate=16000, chunk_size=1024):
    """Record audio from microphone for a specified duration."""
    
    print(f"🎤 Recording audio from microphone for {duration} seconds...")
    print("   Speak now!")
    
    audio = pyaudio.PyAudio()
    
    try:
        stream = audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=sample_rate,
            input=True,
            frames_per_buffer=chunk_size
        )
        
        frames = []
        for i in range(0, int(sample_rate / chunk_size * duration)):
            data = stream.read(chunk_size)
            frames.append(data)
            elapsed = (i + 1) * chunk_size / sample_rate
            remaining = duration - elapsed
            if int(elapsed) != int(elapsed - chunk_size / sample_rate):
                print(f"   Recording... {remaining:.1f}s remaining")
        
        print("✅ Recording completed!")
        
        stream.stop_stream()
        stream.close()
        
        test_file = "recorded_audio.wav"
        with wave.open(test_file, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(b''.join(frames))
        
        print(f"💾 Temporary audio saved to: {test_file}")
        
        return test_file
        
    except Exception as e:
        print(f"❌ Error recording audio: {e}")
        return None
        
    finally:
        audio.terminate()


async def test_deepgram_asr_with_mic(asr_provider):
    """Test Deepgram ASR with microphone input."""
    
    audio_file = None
    try:
        print("\n" + "="*50)
        print("🎙️  MICROPHONE TEST")
        print("="*50)
        
        audio_file = record_audio_from_mic(duration=5)
        
        if audio_file is None:
            print("❌ Failed to record audio from microphone")
            return False
        
        print("\n🔄 Processing audio with Deepgram...")
        start_time = time.time()
        
        result_text, _ = await asr_provider.speech_to_text(audio_file=audio_file)
        
        processing_time = time.time() - start_time
        
        print("\n" + "="*50)
        print("📝 TRANSCRIPTION RESULTS")
        print("="*50)
        
        if result_text is not None and result_text.strip():
            print(f"✅ Transcription successful!")
            print(f"⏱️  Processing time: {processing_time:.2f} seconds")
            print(f"📄 Result: '{result_text}'")
            return True
        else:
            print("❌ Transcription failed - no text detected")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        print(f"   Full error: {traceback.format_exc()}")
        return False
    finally:
        if audio_file and os.path.exists(audio_file):
            try:
                os.remove(audio_file)
                print(f"\n🗑️  Temporary recording file '{audio_file}' deleted.")
            except Exception as e:
                print(f"\n⚠️  Could not delete temporary file '{audio_file}': {e}")


async def test_deepgram_asr_with_local_file(asr_provider, file_path):
    """Test Deepgram ASR with a local audio file."""
    
    print("\n" + "="*50)
    print("📁 LOCAL FILE TEST")
    print("="*50)
    print(f"   File: {file_path}")

    try:
        print("\n🔄 Processing audio with Deepgram...")
        start_time = time.time()
        
        result_text, _ = await asr_provider.speech_to_text(audio_file=file_path)
        
        processing_time = time.time() - start_time
        
        print("\n" + "="*50)
        print("📝 TRANSCRIPTION RESULTS")
        print("="*50)
        
        if result_text is not None and result_text.strip():
            print(f"✅ Transcription successful!")
            print(f"⏱️  Processing time: {processing_time:.2f} seconds")
            print(f"📄 Result: '{result_text}'")
            return True
        else:
            print("❌ Transcription failed - no text detected")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        print(f"   Full error: {traceback.format_exc()}")
        return False


def check_microphone():
    """Check if any microphone input devices are available."""
    try:
        audio = pyaudio.PyAudio()
        input_devices = []
        for i in range(audio.get_device_count()):
            device_info = audio.get_device_info_by_index(i)
            if device_info['maxInputChannels'] > 0:
                input_devices.append(device_info['name'])
        
        audio.terminate()
        
        if input_devices:
            print(f"✅ Found {len(input_devices)} input device(s)")
            return True
        else:
            print("❌ No microphone devices found")
            return False
            
    except Exception as e:
        print(f"⚠️  Could not check for microphone: {e}")
        return True


if __name__ == "__main__":
    print("🚀 Deepgram ASR Test Script")
    print("=" * 50)
    
    async def main():
        # Configuration for the Deepgram ASR provider
        # Note: model and smart_format are now controlled by the URL in the ASRProvider class
        config = {
            "api_key": "2bc99f78312157bb1e017a2596b45c71bfe5f6ba",  # Replace with your actual API key
            "model": "nova-3",
            "language": "en",
            "smart_format": True,
        }
        
        if config["api_key"] == "your-deepgram-api-key":
            print("❌ Please set your Deepgram API key in the config")
            return

        print("\nChoose a test mode:")
        print("  1: Record audio from microphone")
        print("  2: Transcribe a local audio file")
        choice = input("Enter your choice (1 or 2): ")

        asr_provider = ASRProvider(config)

        if choice == '1':
            if check_microphone():
                input("Press Enter to start recording...")
                await test_deepgram_asr_with_mic(asr_provider)
        elif choice == '2':
            file_path = input("Enter the path to your local audio file: ")
            if not os.path.exists(file_path):
                print(f"❌ Error: File not found at '{file_path}'")
                return
            await test_deepgram_asr_with_local_file(asr_provider, file_path)
        else:
            print("❌ Invalid choice.")

    asyncio.run(main())
