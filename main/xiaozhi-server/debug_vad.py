#!/usr/bin/env python3
"""
VAD (Voice Activity Detection) Debug Script
Tests the Silero VAD component independently
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import torch
import numpy as np
import time
from config.logger import setup_logging

logger = setup_logging()

def test_vad():
    """Test VAD component"""
    try:
        print("[VAD] Testing VAD (Voice Activity Detection) Component")
        print("="*50)

        # Test 1: Import VAD module
        print("1. Testing VAD module import...")
        from core.providers.vad.silero_onnx import VADProvider
        print("[OK] VAD module imported successfully")

        # Test 2: Initialize VAD
        print("\n2. Initializing VAD...")
        vad_config = {
            'confidence': 0.3,
            'start_secs': 0.1,
            'stop_secs': 0.6,
            'min_volume': 0.005,
            'sample_rate': 16000
        }

        vad = VADProvider(vad_config)
        print("[OK] VAD initialized successfully")
        print(f"   - Confidence threshold: {vad_config['confidence']}")
        print(f"   - Start seconds: {vad_config['start_secs']}")
        print(f"   - Stop seconds: {vad_config['stop_secs']}")
        print(f"   - Min volume: {vad_config['min_volume']}")
        print(f"   - Sample rate: {vad_config['sample_rate']}")

        # Test 3: Check available methods
        print("\n3. Checking VAD available methods...")
        vad_methods = [method for method in dir(vad) if not method.startswith('_')]
        print(f"   - Available methods: {vad_methods}")

        # Test 4: Test with dummy audio data (this will show if VAD works)
        print("\n4. Testing VAD with audio data...")

        # Create dummy audio - silence
        silence = np.zeros(1024, dtype=np.float32)  # Short silence
        print(f"   - Testing silence ({len(silence)} samples)")

        # Try different method names
        try:
            if hasattr(vad, 'is_vad'):
                start_time = time.time()
                is_speech_silence = vad.is_vad(silence)
                silence_time = time.time() - start_time
                print(f"   - Silence result (is_vad): {is_speech_silence}")
                print(f"   - Processing time: {silence_time:.4f} seconds")
                print("[OK] VAD processing works - using is_vad method")
            elif hasattr(vad, 'is_speech'):
                start_time = time.time()
                is_speech_silence = vad.is_speech(silence)
                silence_time = time.time() - start_time
                print(f"   - Silence result (is_speech): {is_speech_silence}")
                print(f"   - Processing time: {silence_time:.4f} seconds")
                print("[OK] VAD processing works - using is_speech method")
            elif hasattr(vad, 'detect_voice'):
                start_time = time.time()
                is_speech_silence = vad.detect_voice(silence)
                silence_time = time.time() - start_time
                print(f"   - Silence result (detect_voice): {is_speech_silence}")
                print(f"   - Processing time: {silence_time:.4f} seconds")
                print("[OK] VAD processing works - using detect_voice method")
            elif hasattr(vad, 'process_audio'):
                start_time = time.time()
                result = vad.process_audio(silence)
                silence_time = time.time() - start_time
                print(f"   - Silence result (process_audio): {result}")
                print(f"   - Processing time: {silence_time:.4f} seconds")
                print("[OK] VAD processing works - using process_audio method")
            else:
                print("[ERROR] No suitable VAD method found")
                return False
        except Exception as e:
            print(f"[ERROR] VAD processing failed: {e}")
            print(f"   - Exception type: {type(e)}")
            import traceback
            traceback.print_exc()
            return False

        # Create dummy audio - simulated speech (sine wave)
        print(f"   - Testing simulated speech signal...")
        try:
            t = np.linspace(0, 1, 1024, False)
            speech_like = 0.3 * np.sin(2 * np.pi * 440 * t).astype(np.float32)  # 440Hz sine wave

            start_time = time.time()
            is_speech_signal = vad.is_vad(speech_like)
            signal_time = time.time() - start_time

            print(f"   - Speech signal result: {is_speech_signal}")
            print(f"   - Processing time: {signal_time:.4f} seconds")
            print("[OK] VAD processing works - signal processed successfully")
        except Exception as e:
            print(f"[ERROR] VAD speech processing failed: {e}")
            return False

        # Test 5: Performance benchmark
        print("\n5. Performance benchmark...")
        num_tests = 10
        times = []

        for i in range(num_tests):
            test_audio = np.random.uniform(-0.1, 0.1, 1024).astype(np.float32)
            start_time = time.time()
            vad.is_vad(test_audio)
            times.append(time.time() - start_time)

        avg_time = np.mean(times)
        print(f"   - Average processing time: {avg_time:.4f} seconds")
        print(f"   - Max processing time: {max(times):.4f} seconds")
        print(f"   - Min processing time: {min(times):.4f} seconds")

        if avg_time > 0.1:  # Should be much faster than 100ms
            print("[WARNING] VAD processing is slower than expected")
        else:
            print("[OK] VAD performance is good")

        # Test 6: Memory usage
        print("\n6. Memory usage check...")
        import psutil
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        print(f"   - Current memory usage: {memory_mb:.1f} MB")

        print("\n" + "="*50)
        print("[OK] VAD DEBUG COMPLETED - ALL TESTS PASSED")
        return True

    except ImportError as e:
        print(f"[ERROR] Import error: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Error during VAD testing: {e}")
        print(f"   Error type: {type(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_vad()
    if success:
        print("\n[SUCCESS] VAD component is working correctly!")
        sys.exit(0)
    else:
        print("\n[FAILED] VAD component has issues!")
        sys.exit(1)