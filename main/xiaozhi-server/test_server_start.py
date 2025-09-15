#!/usr/bin/env python3
"""
Test script to verify server starts without errors after Langfuse fixes
"""

import sys
import os
import asyncio

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.langfuse_config import langfuse_config
from config.logger import setup_logging

logger = setup_logging()

def test_imports():
    """Test that all critical imports work"""
    print("=== TESTING IMPORTS ===")

    try:
        # Test Langfuse config
        from config.langfuse_config import langfuse_config
        print("[SUCCESS] Langfuse config imported")

        # Test Langfuse wrapper
        from core.providers.llm.langfuse_wrapper import langfuse_tracker
        print("[SUCCESS] Langfuse tracker imported")

        # Test ASR providers
        from core.providers.asr.fun_local import ASRProvider as FunASR
        print("[SUCCESS] FunASR provider imported")

        # Test TTS providers
        from core.providers.tts.edge import TTSProvider as EdgeTTS
        print("[SUCCESS] EdgeTTS provider imported")

        # Test LLM providers
        from core.providers.llm.openai.openai import LLMProvider as OpenAILLM
        print("[SUCCESS] OpenAI LLM provider imported")

        # Test connection handler
        from core.connection import ConnectionHandler
        print("[SUCCESS] ConnectionHandler imported")

        return True

    except Exception as e:
        print(f"[ERROR] Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_langfuse_integration():
    """Test Langfuse integration"""
    print("\n=== TESTING LANGFUSE INTEGRATION ===")

    enabled = langfuse_config.is_enabled()
    client = langfuse_config.get_client()

    print(f"Langfuse Enabled: {enabled}")
    print(f"Langfuse Client: {'Available' if client else 'Not available'}")

    if enabled:
        print("[SUCCESS] Langfuse is properly configured")
        return True
    else:
        print("[WARNING] Langfuse not enabled - check environment variables")
        return False

def test_connection_handler():
    """Test ConnectionHandler initialization"""
    print("\n=== TESTING CONNECTION HANDLER ===")

    try:
        from core.connection import ConnectionHandler

        # Mock config
        mock_config = {
            "selected_module": {
                "VAD": "SileroVAD",
                "ASR": "FunASR",
                "LLM": "ChatGLMLLM",
                "TTS": "EdgeTTS",
                "Memory": "nomem",
                "Intent": "function_call"
            },
            "server": {"ip": "0.0.0.0", "port": 8000}
        }

        # Try to create ConnectionHandler (this was failing before)
        handler = ConnectionHandler(
            mock_config,
            None,  # vad
            None,  # asr
            None,  # llm
            None,  # memory
            None,  # intent
            None   # server
        )

        print(f"[SUCCESS] ConnectionHandler created with session_id: {handler.session_id}")
        print(f"[SUCCESS] Logger initialized: {handler.logger is not None}")
        print(f"[SUCCESS] Langfuse client: {'Available' if handler.langfuse else 'Not available'}")

        return True

    except Exception as e:
        print(f"[ERROR] ConnectionHandler test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("XIAOZHI-SERVER LANGFUSE INTEGRATION TEST")
    print("=" * 50)

    results = []

    # Test imports
    results.append(test_imports())

    # Test Langfuse integration
    results.append(test_langfuse_integration())

    # Test ConnectionHandler
    results.append(test_connection_handler())

    # Summary
    print("\n=== TEST SUMMARY ===")

    if all(results):
        print("[SUCCESS] All tests passed!")
        print("\nThe server should now:")
        print("- Start without ConnectionHandler errors")
        print("- Track ASR operations via FunASR")
        print("- Track LLM operations via OpenAI/ChatGLM")
        print("- Track TTS operations via EdgeTTS")
        print("- Send traces to Langfuse dashboard")

        print("\nNext steps:")
        print("1. Start the server: python app.py")
        print("2. Connect ESP32 device and have a conversation")
        print("3. Check Langfuse dashboard for conversation traces")

        return True
    else:
        print("[ERROR] Some tests failed. Check errors above.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)