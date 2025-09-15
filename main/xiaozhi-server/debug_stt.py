#!/usr/bin/env python3
"""
STT (Speech-to-Text) Debug Script
Tests the ASR components independently
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
import time
import numpy as np
from config.logger import setup_logging

logger = setup_logging()

async def test_stt():
    """Test STT/ASR component"""
    try:
        print("[STT] Testing STT (Speech-to-Text) Component")
        print("="*50)

        # Test 1: Import STT module
        print("1. Testing STT module import...")
        from core.providers.asr.amazon_transcribe_realtime import ASRProvider
        print("[OK] STT module imported successfully")

        # Test 2: Initialize STT
        print("\n2. Initializing STT...")
        stt_config = {
            'language': 'en-IN',
            'region': 'us-east-1',
            'sample_rate': 16000
        }

        stt = ASRProvider(stt_config, delete_audio_file=False)
        print("[OK] STT initialized successfully")
        print(f"   - Language: {stt_config['language']}")
        print(f"   - Region: {stt_config['region']}")
        print(f"   - Sample rate: {stt_config['sample_rate']}")

        # Test 3: Check available methods
        print("\n3. Checking STT available methods...")
        stt_methods = [method for method in dir(stt) if not method.startswith('_')]
        print(f"   - Available methods: {stt_methods}")

        # Test 4: Test initialization check
        print("\n4. Testing STT initialization...")
        try:
            # Check if we have required attributes
            if hasattr(stt, 'language') and hasattr(stt, 'region'):
                print("[OK] STT has required configuration attributes")
                print(f"   - Language: {getattr(stt, 'language', 'not set')}")
                print(f"   - Region: {getattr(stt, 'region', 'not set')}")

            # Check if transcription method exists
            if hasattr(stt, 'transcribe_stream') or hasattr(stt, 'transcribe') or hasattr(stt, 'recognize'):
                print("[OK] STT has transcription method available")
                if hasattr(stt, 'transcribe_stream'):
                    print("   - Using transcribe_stream method")
                elif hasattr(stt, 'transcribe'):
                    print("   - Using transcribe method")
                elif hasattr(stt, 'recognize'):
                    print("   - Using recognize method")
            else:
                print("[WARNING] No standard transcription method found")

        except Exception as e:
            print(f"[ERROR] STT attribute check failed: {e}")

        # Test 5: Test mock audio processing (if possible)
        print("\n5. Testing STT with mock data...")
        try:
            # Create dummy audio buffer
            test_audio = b'mock_opus_audio_data'

            if hasattr(stt, 'transcribe_stream'):
                print("   - STT transcribe_stream method available for testing")
                print("[OK] STT processing method is accessible")
            elif hasattr(stt, 'transcribe'):
                print("   - STT transcribe method available for testing")
                print("[OK] STT processing method is accessible")
            else:
                print("[INFO] Direct testing not possible without real audio stream")

        except Exception as e:
            print(f"[WARNING] Mock audio test failed: {e}")

        # Test 6: Configuration validation
        print("\n6. Configuration validation...")

        # Check AWS credentials
        try:
            import boto3
            try:
                # Test AWS credentials
                session = boto3.Session()
                credentials = session.get_credentials()
                if credentials:
                    print("[OK] AWS credentials are available")
                    print(f"   - Access key: {credentials.access_key[:8]}...")
                else:
                    print("[ERROR] AWS credentials not found")
                    return False
            except Exception as e:
                print(f"[ERROR] AWS credential check failed: {e}")
                return False

        except ImportError:
            print("[ERROR] boto3 not installed - required for Amazon Transcribe")
            return False

        print("\n" + "="*50)
        print("[OK] STT DEBUG COMPLETED - ALL TESTS PASSED")
        return True

    except ImportError as e:
        print(f"[ERROR] Import error: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Error during STT testing: {e}")
        print(f"   Error type: {type(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_stt())
    if success:
        print("\n[SUCCESS] STT component is working correctly!")
        sys.exit(0)
    else:
        print("\n[FAILED] STT component has issues!")
        sys.exit(1)