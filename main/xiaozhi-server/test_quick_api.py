#!/usr/bin/env python3
"""
Quick test of the correct Langfuse API
"""

import sys
import os

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.langfuse_config import langfuse_config
from core.providers.llm.langfuse_wrapper import langfuse_tracker

def test_quick_api():
    """Test the corrected API"""
    print("Testing corrected Langfuse API...")

    try:
        # Test the fixed LLM tracking
        @langfuse_tracker.track_llm_call("test_provider", "test-model")
        def test_llm(self, session_id, dialogue, **kwargs):
            """Test LLM function"""
            yield "Hello "
            yield "world!"

        class MockLLM:
            def __init__(self):
                self.model_name = "test-model"

        llm_instance = MockLLM()
        result = ""
        for chunk in test_llm(llm_instance, "test_session", [{"role": "user", "content": "test"}]):
            result += chunk

        print(f"Result: {result}")

        # Flush data
        langfuse_config.get_client().flush()
        print("Success! API is working.")
        return True

    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_quick_api()