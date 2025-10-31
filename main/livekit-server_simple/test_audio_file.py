#!/usr/bin/env python3
"""
Audio File Testing Script for STT Providers
Tests audio file transcription with AWS STT and Groq fallback
"""

import os
import asyncio
import logging
import time
import wave
import numpy as np
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv(".env")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("audio_test")

async def test_audio_file(audio_file_path: str):
    """Test audio file with STT providers"""
    
    print("🎵 Audio File STT Testing")
    print("=" * 50)
    print(f"📁 Audio file: {audio_file_path}")
    
    # Check if file exists
    if not os.path.exists(audio_file_path):
        print(f"❌ Audio file not found: {audio_file_path}")
        return False
    
    # Get file info
    try:
        with wave.open(audio_file_path, 'rb') as wav_file:
            frames = wav_file.getnframes()
            sample_rate = wav_file.getframerate()
            channels = wav_file.getnchannels()
            duration = frames / sample_rate
            
        print(f"📊 Audio info:")
        print(f"   Duration: {duration:.2f} seconds")
        print(f"   Sample rate: {sample_rate} Hz")
        print(f"   Channels: {channels}")
        print(f"   Frames: {frames}")
        
    except Exception as e:
        print(f"❌ Error reading audio file: {e}")
        return False
    
    # Test 1: Test with Groq STT (current working provider)
    print(f"\n🧪 Test 1: Groq STT (Current Working Provider)")
    print("-" * 45)
    
    try:
        groq_result = await test_with_groq_stt(audio_file_path)
        if groq_result:
            print(f"✅ Groq STT Result: \"{groq_result}\"")
        else:
            print(f"❌ Groq STT failed")
    except Exception as e:
        print(f"❌ Groq STT error: {e}")
    
    # Test 2: Test with AWS STT (if credentials work)
    print(f"\n🧪 Test 2: AWS Transcribe STT")
    print("-" * 30)
    
    try:
        aws_result = await test_with_aws_stt(audio_file_path)
        if aws_result:
            print(f"✅ AWS STT Result: \"{aws_result}\"")
        else:
            print(f"❌ AWS STT failed")
    except Exception as e:
        print(f"❌ AWS STT error: {e}")
    
    # Test 3: Test with Provider Factory (integrated system)
    print(f"\n🧪 Test 3: Provider Factory (Integrated System)")
    print("-" * 48)
    
    try:
        factory_result = await test_with_provider_factory(audio_file_path)
        if factory_result:
            print(f"✅ Provider Factory Result: \"{factory_result}\"")
        else:
            print(f"❌ Provider Factory failed")
    except Exception as e:
        print(f"❌ Provider Factory error: {e}")
    
    return True

async def test_with_groq_stt(audio_file_path: str):
    """Test with Groq STT directly"""
    try:
        import livekit.plugins.groq as groq
        from livekit.agents import utils
        
        # Create Groq STT
        groq_stt = groq.STT(
            model="whisper-large-v3-turbo",
            language="en"  # Using 'en' for compatibility
        )
        
        # Load and convert audio
        audio_buffer = await load_audio_file(audio_file_path)
        
        # Recognize speech
        start_time = time.time()
        result = await groq_stt.recognize(audio_buffer)
        elapsed_time = time.time() - start_time
        
        print(f"   Processing time: {elapsed_time:.2f}s")
        
        if result and result.alternatives:
            return result.alternatives[0].text
        else:
            return None
            
    except Exception as e:
        logger.error(f"Groq STT test error: {e}")
        return None

async def test_with_aws_stt(audio_file_path: str):
    """Test with AWS STT directly"""
    try:
        # Test AWS credentials first
        import boto3
        from botocore.exceptions import ClientError
        
        aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
        aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        aws_region = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
        
        if not aws_access_key_id or not aws_secret_access_key:
            print("   ⚠️ AWS credentials not found in environment")
            return None
        
        # Test credentials
        session = boto3.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=aws_region
        )
        
        sts_client = session.client('sts')
        identity = sts_client.get_caller_identity()
        print(f"   ✅ AWS credentials valid - Account: {identity.get('Account')}")
        
        # Test Transcribe service
        transcribe_client = session.client('transcribe')
        transcribe_client.list_transcription_jobs(MaxResults=1)
        print(f"   ✅ AWS Transcribe service accessible")
        
        # Use our custom AWS STT provider
        from src.providers.aws_stt_provider import AWSTranscribeSTT
        
        aws_stt = AWSTranscribeSTT(
            language="en-IN",  # Indian English
            region=aws_region,
            sample_rate=16000,
            timeout=30
        )
        
        # Load and convert audio
        audio_buffer = await load_audio_file(audio_file_path)
        
        # Recognize speech
        start_time = time.time()
        result = await aws_stt._recognize_impl(audio_buffer)
        elapsed_time = time.time() - start_time
        
        print(f"   Processing time: {elapsed_time:.2f}s")
        
        if result and result.alternatives:
            return result.alternatives[0].text
        else:
            return None
            
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'InvalidClientTokenId':
            print("   ❌ Invalid AWS credentials")
        elif error_code == 'SubscriptionRequiredException':
            print("   ❌ AWS Transcribe service not enabled")
        else:
            print(f"   ❌ AWS error: {error_code}")
        return None
    except Exception as e:
        logger.error(f"AWS STT test error: {e}")
        return None

async def test_with_provider_factory(audio_file_path: str):
    """Test with the integrated provider factory system"""
    try:
        from src.providers.provider_factory import ProviderFactory
        from src.config.config_loader import ConfigLoader
        
        # Load configuration
        config = ConfigLoader.get_groq_config()
        print(f"   📋 Config: STT Provider = {config.get('stt_provider')}")
        print(f"   📋 Config: STT Language = {config.get('stt_language')}")
        
        # Create VAD (required for STT)
        vad = ProviderFactory.create_vad()
        print(f"   ✅ VAD created: {type(vad)}")
        
        # Create STT provider
        stt_provider = ProviderFactory.create_stt(config, vad)
        print(f"   ✅ STT provider created: {type(stt_provider)}")
        
        # Load and convert audio
        audio_buffer = await load_audio_file(audio_file_path)
        
        # Recognize speech
        start_time = time.time()
        result = await stt_provider.recognize(audio_buffer)
        elapsed_time = time.time() - start_time
        
        print(f"   Processing time: {elapsed_time:.2f}s")
        
        if result and result.alternatives:
            return result.alternatives[0].text
        else:
            return None
            
    except Exception as e:
        logger.error(f"Provider factory test error: {e}")
        return None

async def load_audio_file(audio_file_path: str):
    """Load audio file and convert to AudioBuffer format"""
    try:
        from livekit.agents import utils
        import soundfile as sf
        
        # Read audio file
        audio_data, sample_rate = sf.read(audio_file_path)
        
        # Convert to mono if stereo
        if len(audio_data.shape) > 1:
            audio_data = np.mean(audio_data, axis=1)
        
        # Convert to int16
        if audio_data.dtype != np.int16:
            audio_data = (audio_data * 32767).astype(np.int16)
        
        # Create AudioBuffer
        audio_buffer = utils.AudioBuffer(
            data=audio_data.tobytes(),
            sample_rate=sample_rate,
            num_channels=1,
            samples_per_channel=len(audio_data)
        )
        
        return audio_buffer
        
    except ImportError:
        # Fallback without soundfile
        print("   ⚠️ soundfile not available, using wave module")
        return await load_audio_file_wave(audio_file_path)
    except Exception as e:
        logger.error(f"Error loading audio file: {e}")
        return None

async def load_audio_file_wave(audio_file_path: str):
    """Load audio file using wave module (fallback)"""
    try:
        from livekit.agents import utils
        
        with wave.open(audio_file_path, 'rb') as wav_file:
            frames = wav_file.readframes(-1)
            sample_rate = wav_file.getframerate()
            channels = wav_file.getnchannels()
            
        # Convert to numpy array
        audio_data = np.frombuffer(frames, dtype=np.int16)
        
        # Convert to mono if stereo
        if channels > 1:
            audio_data = audio_data.reshape(-1, channels)
            audio_data = np.mean(audio_data, axis=1).astype(np.int16)
        
        # Create AudioBuffer
        audio_buffer = utils.AudioBuffer(
            data=audio_data.tobytes(),
            sample_rate=sample_rate,
            num_channels=1,
            samples_per_channel=len(audio_data)
        )
        
        return audio_buffer
        
    except Exception as e:
        logger.error(f"Error loading audio file with wave: {e}")
        return None

def show_audio_analysis(audio_file_path: str):
    """Show detailed audio analysis"""
    try:
        print(f"\n📊 Detailed Audio Analysis")
        print("-" * 30)
        
        with wave.open(audio_file_path, 'rb') as wav_file:
            frames = wav_file.readframes(-1)
            sample_rate = wav_file.getframerate()
            channels = wav_file.getnchannels()
            sample_width = wav_file.getsampwidth()
            duration = len(frames) / (sample_rate * channels * sample_width)
            
        # Convert to numpy for analysis
        if sample_width == 2:
            audio_data = np.frombuffer(frames, dtype=np.int16)
        else:
            audio_data = np.frombuffer(frames, dtype=np.uint8)
        
        # Basic statistics
        print(f"📈 Audio Statistics:")
        print(f"   File size: {len(frames)} bytes")
        print(f"   Duration: {duration:.2f} seconds")
        print(f"   Sample rate: {sample_rate} Hz")
        print(f"   Channels: {channels}")
        print(f"   Sample width: {sample_width} bytes")
        print(f"   Max amplitude: {np.max(np.abs(audio_data))}")
        print(f"   RMS level: {np.sqrt(np.mean(audio_data**2)):.2f}")
        
        # Check if audio has content
        rms_threshold = 100  # Minimum RMS for speech
        if np.sqrt(np.mean(audio_data**2)) > rms_threshold:
            print(f"✅ Audio appears to contain speech content")
        else:
            print(f"⚠️ Audio might be too quiet or empty")
            
    except Exception as e:
        print(f"❌ Error analyzing audio: {e}")

if __name__ == "__main__":
    # Audio file path
    audio_file = "hita3.wav"
    
    print("🎵 LiveKit STT Audio File Tester")
    print("This script tests audio file transcription with different STT providers")
    print()
    
    # Show audio analysis first
    if os.path.exists(audio_file):
        show_audio_analysis(audio_file)
    
    # Run the test
    try:
        success = asyncio.run(test_audio_file(audio_file))
        
        if success:
            print(f"\n🎉 Audio testing completed!")
            print(f"📝 Results show which STT providers are working with your audio file.")
        else:
            print(f"\n❌ Audio testing failed.")
            
    except KeyboardInterrupt:
        print(f"\n👋 Testing cancelled by user")
    except Exception as e:
        print(f"\n❌ Testing failed: {e}")
        import traceback
        traceback.print_exc()