#!/usr/bin/env python3
"""
Force refresh the server imports and check status
"""

import sys
import os
import importlib

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def force_refresh_imports():
    """Force refresh all imports to pick up changes"""

    print("=== FORCING IMPORT REFRESH ===")

    try:
        # Clear import cache for key modules
        modules_to_refresh = [
            'core.providers.llm.langfuse_wrapper',
            'config.langfuse_config'
        ]

        for module_name in modules_to_refresh:
            if module_name in sys.modules:
                print(f"Refreshing: {module_name}")
                importlib.reload(sys.modules[module_name])

        # Now test the refreshed imports
        from config.langfuse_config import langfuse_config
        from core.providers.llm.langfuse_wrapper import langfuse_tracker

        print(f"✅ Langfuse enabled: {langfuse_config.is_enabled()}")

        client = langfuse_config.get_client()
        print(f"✅ Client has start_generation: {hasattr(client, 'start_generation')}")
        print(f"✅ Client has start_span: {hasattr(client, 'start_span')}")

        # Test the wrapper
        @langfuse_tracker.track_stt("test_refresh")
        async def test_stt_refresh():
            return "test result", None

        print("✅ STT tracker test: Ready")

        @langfuse_tracker.track_llm_call("test_refresh")
        def test_llm_refresh(self, session_id, dialogue):
            yield "test response"

        print("✅ LLM tracker test: Ready")

        @langfuse_tracker.track_tts("test_refresh")
        async def test_tts_refresh(text):
            return b"test audio"

        print("✅ TTS tracker test: Ready")

        print("\n🎯 ALL SYSTEMS READY!")
        print("\nNow restart your server:")
        print("1. Stop current server (Ctrl+C)")
        print("2. Run: python app.py")
        print("3. Test conversation with ESP32")

        return True

    except Exception as e:
        print(f"❌ Refresh failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_vad_sensitivity():
    """Check VAD configuration for voice detection issues"""

    print("\n=== VAD SENSITIVITY CHECK ===")

    try:
        import yaml

        with open("data/.config.yaml", "r") as f:
            config = yaml.safe_load(f)

        vad_config = config.get("VAD", {}).get("SileroVAD", {})
        threshold = vad_config.get("threshold", 0.5)
        threshold_low = vad_config.get("threshold_low", 0.2)
        min_volume = vad_config.get("min_volume", 0.01)

        print(f"Current VAD settings:")
        print(f"  Threshold: {threshold} (lower = more sensitive)")
        print(f"  Low threshold: {threshold_low}")
        print(f"  Min volume: {min_volume}")

        if threshold > 0.3:
            print("⚠️  VAD threshold might be too high")
            print("   Try lowering to 0.3 for better voice detection")
        else:
            print("✅ VAD sensitivity looks good")

        return True

    except Exception as e:
        print(f"❌ VAD check failed: {e}")
        return False

if __name__ == "__main__":
    print("XIAOZHI SERVER DIAGNOSTIC & REFRESH")
    print("=" * 45)

    refresh_ok = force_refresh_imports()
    vad_ok = check_vad_sensitivity()

    print(f"\n=== SUMMARY ===")
    print(f"Import refresh: {'✅ OK' if refresh_ok else '❌ FAILED'}")
    print(f"VAD check: {'✅ OK' if vad_ok else '❌ FAILED'}")

    if refresh_ok:
        print(f"\n🚀 READY TO RESTART SERVER!")
    else:
        print(f"\n⚠️  Fix import issues first")