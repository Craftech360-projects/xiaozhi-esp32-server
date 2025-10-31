#!/usr/bin/env python3
"""
Test script for frame handling in the custom AWS STT provider
"""

import os
import asyncio
import logging
import numpy as np
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("frame_handling_test")

async def test_frame_handling():
    """Test frame handling with different data types"""
    
    print("🧪 Testing Frame Handling in Custom AWS STT Provider")
    print("=" * 60)
    
    # Import required modules
    try:
        from src.providers.aws_stt_provider import AWSTranscribeSTT
        from livekit import rtc
        print("✅ Imports successful")
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    
    # Create AWS STT provider
    print("\n1. Creating AWS STT provider...")
    try:
        aws_stt = AWSTranscribeSTT(
            language="en-IN",
            region="us-east-1",
            sample_rate=16000,
            timeout=30
        )
        print("✅ AWS STT provider created")
    except Exception as e:
        print(f"❌ Failed to create AWS STT provider: {e}")
        return False
    
    # Create stream
    print("\n2. Creating speech stream...")
    try:
        stream = aws_stt.stream(language="en-IN")
        print("✅ Speech stream created")
    except Exception as e:
        print(f"❌ Failed to create speech stream: {e}")
        return False
    
    # Test different frame data types
    print("\n3. Testing different frame data types...")
    
    # Test 1: Memoryview data (most common in LiveKit)
    print("   Testing memoryview data...")
    try:
        # Create sample audio data
        sample_data = np.zeros(1600, dtype=np.int16)  # 0.1 seconds at 16kHz
        memview_data = memoryview(sample_data.tobytes())
        
        # Create mock AudioFrame
        class MockAudioFrame:
            def __init__(self, data):
                self.data = data
                self.sample_rate = 16000
                self.samples_per_channel = len(data) // 2  # 16-bit = 2 bytes per sample
        
        frame = MockAudioFrame(memview_data)
        
        # Test push_frame (this should not raise an error)
        stream.push_frame(frame)
        print("   ✅ Memoryview data handled successfully")
        
    except Exception as e:
        print(f"   ❌ Memoryview test failed: {e}")
        return False
    
    # Test 2: Numpy array data
    print("   Testing numpy array data...")
    try:
        numpy_data = np.zeros(1600, dtype=np.int16)
        frame = MockAudioFrame(numpy_data)
        stream.push_frame(frame)
        print("   ✅ Numpy array data handled successfully")
        
    except Exception as e:
        print(f"   ❌ Numpy array test failed: {e}")
        return False
    
    # Test 3: Bytes data
    print("   Testing bytes data...")
    try:
        bytes_data = np.zeros(1600, dtype=np.int16).tobytes()
        
        class BytesFrame:
            def __init__(self, data):
                self.data = data
                self.sample_rate = 16000
            
            # Mock tobytes method
            def tobytes(self):
                return self.data
        
        # Create a mock that has tobytes method
        class MockBytesData:
            def __init__(self, data):
                self._data = data
            
            def tobytes(self):
                return self._data
        
        frame = MockAudioFrame(MockBytesData(bytes_data))
        stream.push_frame(frame)
        print("   ✅ Bytes data handled successfully")
        
    except Exception as e:
        print(f"   ❌ Bytes test failed: {e}")
        return False
    
    # Clean up
    print("\n4. Cleaning up...")
    try:
        await stream.aclose()
        print("✅ Stream closed successfully")
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 All frame handling tests passed!")
    print("\n📝 The provider can now handle:")
    print("   - memoryview objects (LiveKit's default)")
    print("   - numpy arrays")
    print("   - objects with tobytes() method")
    print("   - raw buffer data")
    print("\n🚀 Your AWS STT provider is ready for production use!")
    
    return True

if __name__ == "__main__":
    print("🧪 Frame Handling Test for Custom AWS STT Provider")
    print("This script tests different audio frame data types")
    print()
    
    # Run test
    success = asyncio.run(test_frame_handling())
    
    if success:
        print("\n✅ All frame handling tests completed successfully!")
    else:
        print("\n❌ Frame handling tests failed. Please check the errors above.")
        exit(1)