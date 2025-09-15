#!/usr/bin/env python3
"""
Test to verify correct Langfuse API usage
"""

import sys
import os

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.langfuse_config import langfuse_config

def test_langfuse_api():
    """Test the correct Langfuse API"""
    print("=== TESTING LANGFUSE API ===")

    if not langfuse_config.is_enabled():
        print("Langfuse not enabled")
        return False

    client = langfuse_config.get_client()
    print(f"Client type: {type(client)}")
    print(f"Client methods: {[method for method in dir(client) if not method.startswith('_')]}")

    try:
        # Test creating a trace
        trace = client.trace(
            name="test_trace",
            session_id="test_session",
            metadata={"test": True}
        )
        print(f"✅ Trace created: {trace}")

        # Test creating a generation within the trace
        generation = trace.generation(
            name="test_generation",
            input={"test": "input"},
            model="test-model",
            metadata={"test": True}
        )
        print(f"✅ Generation created: {generation}")

        # Update generation
        generation.update(output="test output")
        generation.end()

        # Test creating a span within the trace
        span = trace.span(
            name="test_span",
            input={"test": "span input"},
            metadata={"test": True}
        )
        print(f"✅ Span created: {span}")

        # Update span
        span.update(output={"test": "span output"})
        span.end()

        # Flush data
        client.flush()
        print("✅ Data flushed successfully")

        return True

    except Exception as e:
        print(f"❌ API test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_langfuse_api()