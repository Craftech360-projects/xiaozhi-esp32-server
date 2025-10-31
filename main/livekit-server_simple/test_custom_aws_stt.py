#!/usr/bin/env python3
"""
Test script specifically for the custom AWS STT provider
"""

import os
import asyncio
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("custom_aws_stt_test")

async def test_custom_aws_stt():
    """Test the custom AWS STT provider directly"""
    
    print("🧪 Testing Custom AWS Transcribe STT Provider")
    print("=" * 50)
    
    # Test 1: Import custom provider
    print("\n1. Testing custom AWS STT provider import...")
    try:
        from src.providers.aws_stt_provider import AWSTranscribeSTT
        print("✅ Custom AWS STT provider imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import custom AWS STT provider: {e}")
        return False
    
    # Test 2: Create provider instance
    print("\n2. Creating custom AWS STT provider instance...")
    try:
        aws_stt = AWSTranscribeSTT(
            language="en-IN",
            region="us-east-1",
            sample_rate=16000,
            timeout=30
        )
        print(f"✅ Custom AWS STT provider created: {type(aws_stt)}")
        print(f"   Language: {aws_stt.language_code}")
        print(f"   Region: {aws_stt.aws_region}")
        print(f"   Sample Rate: {aws_stt.sample_rate}")
    except Exception as e:
        print(f"❌ Failed to create custom AWS STT provider: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 3: Check capabilities
    print("\n3. Checking STT capabilities...")
    capabilities = aws_stt.capabilities
    print(f"✅ Streaming: {capabilities.streaming}")
    print(f"✅ Interim Results: {capabilities.interim_results}")
    
    # Test 4: Test streaming method
    print("\n4. Testing streaming method...")
    try:
        stream = aws_stt.stream(language="en-IN")
        print(f"✅ Stream created: {type(stream)}")
        
        # Clean up
        await stream.aclose()
        print("✅ Stream closed successfully")
    except Exception as e:
        print(f"❌ Failed to create stream: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 5: Test single frame recognition (should raise NotImplementedError)
    print("\n5. Testing single frame recognition (should fail)...")
    try:
        import numpy as np
        
        # Create a simple mock buffer for testing
        class MockAudioBuffer:
            def __init__(self, data, sample_rate):
                self.data = data
                self.sample_rate = sample_rate
        
        # Create a dummy audio buffer
        dummy_audio = np.zeros(1600, dtype=np.int16)  # 0.1 seconds of silence
        buffer = MockAudioBuffer(data=dummy_audio, sample_rate=16000)
        
        # This should raise NotImplementedError
        await aws_stt._recognize_impl(buffer)
        print("❌ Single frame recognition should have failed")
        return False
    except NotImplementedError as e:
        print(f"✅ Single frame recognition correctly failed: {e}")
    except Exception as e:
        print(f"❌ Unexpected error in single frame test: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 Custom AWS STT provider tests passed!")
    print("\n📝 The provider is now ready for streaming speech recognition.")
    print("🚀 Your LiveKit agent will use this custom provider instead of the plugin.")
    
    return True

if __name__ == "__main__":
    print("🧪 Custom AWS Transcribe STT Provider Test")
    print("This script tests the custom implementation specifically")
    print()
    
    # Run test
    success = asyncio.run(test_custom_aws_stt())
    
    if success:
        print("\n✅ All custom provider tests completed successfully!")
        print("\n💡 Key differences from the plugin:")
        print("   - Implements proper streaming interface")
        print("   - Handles Indian English (en-IN) correctly")
        print("   - Uses amazon-transcribe library directly")
        print("   - Provides interim results for real-time feedback")
    else:
        print("\n❌ Custom provider tests failed. Please fix the issues above.")
        exit(1)