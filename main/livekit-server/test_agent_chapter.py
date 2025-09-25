#!/usr/bin/env python3
"""
Test script to verify the agent can answer chapter-related queries
"""

import asyncio
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env")

# Add the src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__)))

from src.agent.educational_agent import EducationalAssistant

async def test_agent_chapter_queries():
    """Test the agent's ability to handle chapter queries"""

    # Create educational assistant
    assistant = EducationalAssistant()

    # Initialize education service
    init_success = await assistant.initialize_education_service()

    if not init_success:
        print("FAILED to initialize education service")
        return

    print("SUCCESS: Education service initialized")

    # Test different chapter query formats
    test_queries = [
        "What is chapter 1 about?",
        "Tell me about chapter 1",
        "Give me a brief about chapter 2",
        "What does chapter 3 cover?",
        "Chapter 4",
        "Explain chapter 5 to me",
        "Tell me chapter 1"
    ]

    print("\n=== Testing Agent Chapter Query Handling ===")

    for query in test_queries:
        print(f"\n--- Query: '{query}' ---")

        try:
            # Call the underlying implementation directly
            # This simulates what would happen when the agent processes the query
            response = await assistant._search_textbook_internal(
                question=query,
                grade=6,  # Pre-set to Grade 6
                subject="science"  # Pre-set to Science
            )

            # Check response quality
            if response and len(response) > 100:
                print(f"SUCCESS: Got response with {len(response)} characters")
                # Show first 200 chars of response
                print(f"Response preview: {response[:200]}...")
            else:
                print(f"WARNING: Short response ({len(response) if response else 0} chars)")
                if response:
                    print(f"Full response: {response}")

        except Exception as e:
            print(f"EXCEPTION: {e}")

    print("\n=== Test Complete ===")

if __name__ == "__main__":
    asyncio.run(test_agent_chapter_queries())