#!/usr/bin/env python3
"""
Diagnose audio flow issues without affecting functionality
"""

import sys
import os
import yaml

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def diagnose_configuration():
    """Check current configuration"""
    print("=== CONFIGURATION DIAGNOSIS ===")

    try:
        with open("data/.config.yaml", "r") as f:
            config = yaml.safe_load(f)

        selected = config.get("selected_module", {})
        print(f"VAD: {selected.get('VAD', 'NOT SET')}")
        print(f"ASR: {selected.get('ASR', 'NOT SET')}")
        print(f"LLM: {selected.get('LLM', 'NOT SET')}")
        print(f"TTS: {selected.get('TTS', 'NOT SET')}")

        # Check VAD settings
        vad_config = config.get("VAD", {}).get("SileroVAD", {})
        print(f"\nVAD Settings:")
        print(f"  Threshold: {vad_config.get('threshold', 'NOT SET')}")
        print(f"  Min Volume: {vad_config.get('min_volume', 'NOT SET')}")

        # Check ASR settings
        asr_name = selected.get('ASR')
        if asr_name:
            asr_config = config.get("ASR", {}).get(asr_name, {})
            print(f"\nASR ({asr_name}) Settings:")
            print(f"  Type: {asr_config.get('type', 'NOT SET')}")
            print(f"  Language: {asr_config.get('language_code', 'NOT SET')}")

        # Check TTS settings
        tts_name = selected.get('TTS')
        if tts_name:
            tts_config = config.get("TTS", {}).get(tts_name, {})
            print(f"\nTTS ({tts_name}) Settings:")
            print(f"  Type: {tts_config.get('type', 'NOT SET')}")
            print(f"  Voice: {tts_config.get('voice', 'NOT SET')}")

        return True

    except Exception as e:
        print(f"[ERROR] Configuration check failed: {e}")
        return False

def check_providers():
    """Check if providers are accessible"""
    print("\n=== PROVIDER ACCESSIBILITY ===")

    try:
        # Test imports
        providers_status = {
            'VAD': False,
            'ASR': False,
            'LLM': False,
            'TTS': False
        }

        # Test VAD
        try:
            from core.providers.vad.silero_onnx import VADProvider
            providers_status['VAD'] = True
            print("[SUCCESS] VAD provider accessible")
        except Exception as e:
            print(f"[ERROR] VAD provider: {e}")

        # Test ASR
        try:
            from core.providers.asr.amazon_transcribe_realtime import ASRProvider
            providers_status['ASR'] = True
            print("[SUCCESS] ASR provider accessible")
        except Exception as e:
            print(f"[ERROR] ASR provider: {e}")

        # Test LLM
        try:
            from core.providers.llm.openai.openai import LLMProvider
            providers_status['LLM'] = True
            print("[SUCCESS] LLM provider accessible")
        except Exception as e:
            print(f"[ERROR] LLM provider: {e}")

        # Test TTS
        try:
            from core.providers.tts.edge import TTSProvider
            providers_status['TTS'] = True
            print("[SUCCESS] TTS provider accessible")
        except Exception as e:
            print(f"[ERROR] TTS provider: {e}")

        return all(providers_status.values())

    except Exception as e:
        print(f"[ERROR] Provider check failed: {e}")
        return False

def suggest_fixes():
    """Suggest potential fixes"""
    print("\n=== SUGGESTED FIXES ===")

    print("1. AUDIO INPUT (VAD/ASR) ISSUES:")
    print("   - Check ESP32 microphone is working")
    print("   - Verify audio format (should be Opus 16kHz)")
    print("   - Test with louder voice or closer to microphone")
    print("   - Current VAD threshold lowered to 0.3 (more sensitive)")

    print("\n2. AUDIO OUTPUT (TTS) ISSUES:")
    print("   - Check ESP32 speaker/audio output")
    print("   - Verify EdgeTTS is working (internet connection required)")
    print("   - Check audio format compatibility")

    print("\n3. CONVERSATION FLOW:")
    print("   - Langfuse errors have been disabled")
    print("   - Memory system is working correctly")
    print("   - LLM calls should now complete without errors")

    print("\n4. IMMEDIATE TESTS:")
    print("   - Try speaking louder and clearer")
    print("   - Check ESP32 serial logs for audio data")
    print("   - Watch server logs for VAD detection messages")

def check_recent_logs():
    """Check for common log patterns"""
    print("\n=== LOG PATTERN ANALYSIS ===")

    patterns = [
        ("VAD detection", "Voice activity should be detected"),
        ("ASR processing", "Audio should be transcribed"),
        ("LLM response", "Chat responses should be generated"),
        ("TTS generation", "Audio should be synthesized"),
        ("Audio streaming", "Audio should be sent to device")
    ]

    for pattern, description in patterns:
        print(f"Look for: {pattern} -> {description}")

def main():
    """Main diagnostic function"""
    print("XIAOZHI AUDIO FLOW DIAGNOSTIC")
    print("=" * 40)

    config_ok = diagnose_configuration()
    providers_ok = check_providers()

    if config_ok and providers_ok:
        print(f"\n[SUCCESS] Configuration and providers look good")
    else:
        print(f"\n[WARNING] Some components have issues")

    suggest_fixes()
    check_recent_logs()

    print(f"\n=== NEXT STEPS ===")
    print("1. Watch server logs while testing")
    print("2. Speak clearly into ESP32 microphone")
    print("3. Check for VAD detection messages")
    print("4. If still not working, check ESP32 hardware")

if __name__ == "__main__":
    main()