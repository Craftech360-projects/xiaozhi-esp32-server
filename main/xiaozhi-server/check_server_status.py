#!/usr/bin/env python3
"""
Check server status and configuration
"""

import sys
import os

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_server_status():
    """Check current server configuration and status"""

    print("=== SERVER STATUS CHECK ===")

    try:
        # Check Langfuse integration
        from config.langfuse_config import langfuse_config
        from core.providers.llm.langfuse_wrapper import langfuse_tracker

        print(f"[SUCCESS] Langfuse enabled: {langfuse_config.is_enabled()}")
        print(f"[SUCCESS] Langfuse wrapper loaded: {langfuse_tracker.enabled}")

        # Check current configuration
        from config.config_loader import get_config
        config = get_config()

        print(f"[INFO] Current ASR provider: {config['selected_module']['ASR']}")
        print(f"[INFO] Current LLM provider: {config['selected_module']['LLM']}")
        print(f"[INFO] Current TTS provider: {config['selected_module']['TTS']}")

        # Check provider integrations
        integrations = {
            'ASR': False,
            'LLM': False,
            'TTS': False
        }

        # Check ASR integration
        asr_provider = config['selected_module']['ASR']
        if asr_provider == "AmazonTranscribeStreaming":
            # Check if amazon_transcribe_realtime.py has Langfuse
            try:
                with open("core/providers/asr/amazon_transcribe_realtime.py", "r") as f:
                    content = f.read()
                    if "@langfuse_tracker.track_stt" in content:
                        integrations['ASR'] = True
            except:
                pass

        # Check LLM integration
        llm_provider = config['selected_module']['LLM']
        if llm_provider == "GroqLLM":
            # OpenAI provider should have Langfuse
            try:
                with open("core/providers/llm/openai/openai.py", "r") as f:
                    content = f.read()
                    if "@langfuse_tracker.track_llm_call" in content:
                        integrations['LLM'] = True
            except:
                pass

        # Check TTS integration
        tts_provider = config['selected_module']['TTS']
        if tts_provider == "EdgeTTS":
            try:
                with open("core/providers/tts/edge.py", "r") as f:
                    content = f.read()
                    if "@langfuse_tracker.track_tts" in content:
                        integrations['TTS'] = True
            except:
                pass

        # Report integration status
        for provider, integrated in integrations.items():
            status = "[SUCCESS]" if integrated else "[MISSING]"
            print(f"{status} {provider} Langfuse integration: {integrated}")

        # Check if server needs restart
        print(f"\n=== ACTION REQUIRED ===")
        if all(integrations.values()):
            print("[SUCCESS] All integrations are in place")
            print("[INFO] If you're still seeing errors, restart the server:")
            print("       1. Stop current server (Ctrl+C)")
            print("       2. Run: python app.py")
            print("       3. Try conversation with ESP32 device")
        else:
            print("[ERROR] Some integrations are missing - check the files above")

        return True

    except Exception as e:
        print(f"[ERROR] Status check failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    check_server_status()