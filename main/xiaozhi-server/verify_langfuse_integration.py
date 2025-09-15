#!/usr/bin/env python3
"""
Verification script for Langfuse integration in xiaozhi-server
This checks that all components are properly integrated and ready for tracking
"""

import sys
import os

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.langfuse_config import langfuse_config
from core.providers.llm.langfuse_wrapper import langfuse_tracker

def check_langfuse_config():
    """Check Langfuse configuration"""
    print("=== LANGFUSE CONFIGURATION ===")

    enabled = langfuse_config.is_enabled()
    client = langfuse_config.get_client()

    print(f"Langfuse Enabled: {enabled}")
    print(f"Langfuse Client: {'Configured' if client else 'Not configured'}")

    if enabled:
        print("[SUCCESS] Langfuse is properly configured")
        return True
    else:
        print("[ERROR] Langfuse is not enabled")
        print("Please check your environment variables:")
        print("- LANGFUSE_SECRET_KEY")
        print("- LANGFUSE_PUBLIC_KEY")
        print("- LANGFUSE_HOST (optional, defaults to cloud.langfuse.com)")
        return False

def check_asr_integration():
    """Check ASR provider integration"""
    print("\n=== ASR INTEGRATION STATUS ===")

    asr_files = [
        "core/providers/asr/amazon_transcribe_realtime.py",
        "core/providers/asr/openai.py",
        "core/providers/asr/groq_whisper.py",
        "core/providers/asr/aliyun.py",
    ]

    integrated_count = 0
    total_count = len(asr_files)

    for asr_file in asr_files:
        if os.path.exists(asr_file):
            try:
                with open(asr_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    has_import = "langfuse_wrapper" in content
                    has_decorator = "@langfuse_tracker.track_stt" in content

                    if has_import and has_decorator:
                        print(f"[SUCCESS] {asr_file} - Fully integrated")
                        integrated_count += 1
                    elif has_import:
                        print(f"[PARTIAL] {asr_file} - Import found, decorator missing")
                    else:
                        print(f"[MISSING] {asr_file} - Not integrated")
            except Exception as e:
                print(f"[ERROR] {asr_file} - Could not read file: {e}")
        else:
            print(f"[NOT FOUND] {asr_file}")

    print(f"\nASR Integration Status: {integrated_count}/{total_count} providers integrated")
    return integrated_count > 0

def check_llm_integration():
    """Check LLM provider integration"""
    print("\n=== LLM INTEGRATION STATUS ===")

    llm_files = [
        "core/providers/llm/openai/openai.py",
        "core/providers/llm/gemini/gemini.py",
        "core/providers/llm/ollama/ollama.py",
        "core/providers/llm/fastgpt/fastgpt.py",
    ]

    integrated_count = 0

    for llm_file in llm_files:
        if os.path.exists(llm_file):
            try:
                with open(llm_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    has_import = "langfuse_wrapper" in content
                    has_decorator = "@langfuse_tracker.track_llm_call" in content

                    if has_import and has_decorator:
                        print(f"[SUCCESS] {llm_file} - Fully integrated")
                        integrated_count += 1
                    elif has_import:
                        print(f"[PARTIAL] {llm_file} - Import found, decorator missing")
                    else:
                        print(f"[MISSING] {llm_file} - Not integrated")
            except Exception as e:
                print(f"[ERROR] {llm_file} - Could not read file: {e}")
        else:
            print(f"[NOT FOUND] {llm_file}")

    print(f"\nLLM Integration Status: {integrated_count} providers integrated")
    return integrated_count > 0

def check_environment_variables():
    """Check required environment variables"""
    print("\n=== ENVIRONMENT VARIABLES ===")

    required_vars = ["LANGFUSE_SECRET_KEY", "LANGFUSE_PUBLIC_KEY"]
    optional_vars = ["LANGFUSE_HOST", "LANGFUSE_DEBUG"]

    all_set = True

    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"[SUCCESS] {var} - Set (length: {len(value)})")
        else:
            print(f"[ERROR] {var} - Not set")
            all_set = False

    for var in optional_vars:
        value = os.getenv(var)
        if value:
            print(f"[INFO] {var} - Set to: {value}")
        else:
            print(f"[INFO] {var} - Not set (using default)")

    return all_set

def main():
    """Main verification function"""
    print("XIAOZHI-SERVER LANGFUSE INTEGRATION VERIFICATION")
    print("=" * 50)

    # Check all components
    config_ok = check_langfuse_config()
    env_ok = check_environment_variables()
    asr_ok = check_asr_integration()
    llm_ok = check_llm_integration()

    # Summary
    print("\n=== VERIFICATION SUMMARY ===")

    if config_ok and env_ok and asr_ok and llm_ok:
        print("[SUCCESS] Langfuse integration is fully configured and ready!")
        print("\nYour real-time conversations will now be tracked with:")
        print("- ASR (Speech-to-Text) operations")
        print("- LLM (Language Model) requests and responses")
        print("- Token usage and cost tracking")
        print("- Session-based conversation flows")
        print("- Performance metrics (response times)")

        print("\nTo view your conversation traces:")
        print("1. Go to your Langfuse dashboard")
        print("2. Look for traces with your session IDs")
        print("3. Check the 'Generations' and 'Spans' sections")

        return True
    else:
        print("[ERROR] Langfuse integration has issues that need to be resolved:")

        if not config_ok or not env_ok:
            print("- Configuration/Environment variables need attention")
        if not asr_ok:
            print("- ASR provider integration needs attention")
        if not llm_ok:
            print("- LLM provider integration needs attention")

        print("\nPlease fix the issues above and run this script again.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)