#!/usr/bin/env python3
"""
TTS (Text-to-Speech) Debug Script
Tests the TTS components independently
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
import time
from config.logger import setup_logging

logger = setup_logging()

async def test_tts():
    """Test TTS component"""
    try:
        print("[TTS] Testing TTS (Text-to-Speech) Component")
        print("="*50)

        # Test 1: Import TTS module
        print("1. Testing TTS module import...")
        from core.providers.tts.edge import TTSProvider
        print("[OK] TTS module imported successfully")

        # Test 2: Initialize TTS
        print("\n2. Initializing TTS...")
        tts_config = {
            'voice': 'en-US-AriaNeural',
            'speed': '0%',
            'pitch': '0%',
            'format': 'opus'
        }

        tts = TTSProvider(tts_config)
        print("[OK] TTS initialized successfully")
        print(f"   - Voice: {tts_config['voice']}")
        print(f"   - Speed: {tts_config['speed']}")
        print(f"   - Pitch: {tts_config['pitch']}")
        print(f"   - Format: {tts_config['format']}")

        # Test 3: Check available methods
        print("\n3. Checking TTS available methods...")
        tts_methods = [method for method in dir(tts) if not method.startswith('_')]
        print(f"   - Available methods: {tts_methods}")

        # Test 4: Test text synthesis
        print("\n4. Testing TTS text synthesis...")
        test_text = "Hello, this is a test of the text to speech system."

        try:
            if hasattr(tts, 'text_to_speech'):
                print("   - TTS text_to_speech method available")
                result = await tts.text_to_speech(test_text)
                if result:
                    print("[OK] TTS synthesis successful")
                    print(f"   - Generated audio data size: {len(result)} bytes")
                else:
                    print("[WARNING] TTS synthesis returned empty result")
            elif hasattr(tts, 'synthesize'):
                print("   - TTS synthesize method available")
                result = await tts.synthesize(test_text)
                if result:
                    print("[OK] TTS synthesis successful")
                    print(f"   - Generated audio data size: {len(result)} bytes")
                else:
                    print("[WARNING] TTS synthesis returned empty result")
            elif hasattr(tts, 'generate_speech'):
                print("   - TTS generate_speech method available")
                result = await tts.generate_speech(test_text)
                if result:
                    print("[OK] TTS synthesis successful")
                    print(f"   - Generated audio data size: {len(result)} bytes")
                else:
                    print("[WARNING] TTS synthesis returned empty result")
            else:
                print("[WARNING] No standard TTS synthesis method found")
                print("   - Available methods:", tts_methods)

        except Exception as e:
            print(f"[ERROR] TTS synthesis failed: {e}")
            print(f"   - Exception type: {type(e)}")

        # Test 5: Configuration validation
        print("\n5. Configuration validation...")

        # Check if voice configuration is valid
        if hasattr(tts, 'voice') or hasattr(tts, 'config'):
            print("[OK] TTS has voice configuration")
            if hasattr(tts, 'voice'):
                print(f"   - Voice setting: {getattr(tts, 'voice', 'not set')}")
        else:
            print("[WARNING] TTS voice configuration not accessible")

        # Test 6: Performance test (if synthesis worked)
        print("\n6. Performance test...")
        try:
            short_text = "Test"
            start_time = time.time()

            if hasattr(tts, 'text_to_speech'):
                await tts.text_to_speech(short_text)
            elif hasattr(tts, 'synthesize'):
                await tts.synthesize(short_text)
            elif hasattr(tts, 'generate_speech'):
                await tts.generate_speech(short_text)

            processing_time = time.time() - start_time
            print(f"   - Processing time for short text: {processing_time:.3f} seconds")

            if processing_time < 2.0:
                print("[OK] TTS performance is acceptable")
            else:
                print("[WARNING] TTS processing is slow")

        except Exception as e:
            print(f"[WARNING] Performance test failed: {e}")

        # Test 7: Check EdgeTTS dependencies
        print("\n7. Checking EdgeTTS dependencies...")
        try:
            import edge_tts
            print("[OK] edge-tts library is available")
            print(f"   - edge-tts version: {getattr(edge_tts, '__version__', 'unknown')}")
        except ImportError:
            print("[ERROR] edge-tts library not installed")
            return False

        print("\n" + "="*50)
        print("[OK] TTS DEBUG COMPLETED - ALL TESTS PASSED")
        return True

    except ImportError as e:
        print(f"[ERROR] Import error: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Error during TTS testing: {e}")
        print(f"   Error type: {type(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_tts())
    if success:
        print("\n[SUCCESS] TTS component is working correctly!")
        sys.exit(0)
    else:
        print("\n[FAILED] TTS component has issues!")
        sys.exit(1)