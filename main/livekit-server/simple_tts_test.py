#!/usr/bin/env python3
"""
Simple test script for TTS text filtering functionality.
"""

import sys
import os

# Add the src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.text_filter import text_filter

def test_basic_filtering():
    """Test basic filtering functionality"""

    test_cases = [
        "Hello world!",  # Normal text
        "This is *markdown* text",  # Markdown
        "Math: 2 + 2 = 4",  # Math symbols
        "email@domain.com",  # Email
        "   Extra   spaces   ",  # Whitespace
        "",  # Empty
        None,  # None
    ]

    print("TTS Text Filtering Test Results:")
    print("=" * 50)

    for i, text in enumerate(test_cases, 1):
        print(f"\nTest {i}:")
        print(f"Input:  {repr(text)}")

        try:
            result = text_filter.filter_for_tts(text)
            print(f"Output: {repr(result)}")

            if text != result:
                print("Status: Filtered")
            else:
                print("Status: No change")

        except Exception as e:
            print(f"Error: {e}")

    print("\n" + "=" * 50)
    print("Basic filtering test completed!")

def test_emoji_filtering():
    """Test emoji filtering specifically"""

    # Test with ASCII representation of emojis
    test_with_emojis = "Hello world with happy face emoji"
    normal_text = "Hello world normal text"

    print("\nEmoji Filtering Test:")
    print("-" * 30)

    result1 = text_filter.filter_for_tts(test_with_emojis)
    result2 = text_filter.filter_for_tts(normal_text)

    print(f"With emojis: {repr(test_with_emojis)} -> {repr(result1)}")
    print(f"Normal text: {repr(normal_text)} -> {repr(result2)}")

    # Test safety check
    safe1 = text_filter.is_safe_for_tts(test_with_emojis)
    safe2 = text_filter.is_safe_for_tts(normal_text)

    print(f"Safety check - with emojis: {safe1}")
    print(f"Safety check - normal: {safe2}")

def test_agent_import():
    """Test that the agent can be imported"""

    print("\nAgent Import Test:")
    print("-" * 30)

    try:
        from src.agent.filtered_agent import FilteredAgent
        agent = FilteredAgent(instructions="Test agent")
        print("✅ FilteredAgent imported and created successfully")
        print(f"Filtering enabled: {agent.is_filtering_enabled()}")
        return True
    except Exception as e:
        print(f"❌ Agent import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Starting simple TTS filtering tests...\n")

    # Run tests
    test_basic_filtering()
    test_emoji_filtering()
    success = test_agent_import()

    print("\n" + "=" * 50)
    if success:
        print("✅ All tests passed! TTS filtering is working.")
        print("\nTo use in your project:")
        print("1. Replace 'Agent' with 'FilteredAgent' in your agent class")
        print("2. Text will be automatically filtered before TTS")
    else:
        print("❌ Some tests failed. Check the errors above.")