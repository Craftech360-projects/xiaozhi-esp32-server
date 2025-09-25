#!/usr/bin/env python3
"""
Test Activity queries to ensure they work with chapter context
"""

import asyncio
import sys
import os
import logging
from unittest.mock import MagicMock
from dotenv import load_dotenv

# Configure logging to see the agent logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv(".env")

# Add the src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__)))

from src.agent.educational_agent import EducationalAssistant
from livekit.agents import RunContext

async def test_activity_queries():
    """Test activity queries that should use chapter context"""

    # Create educational assistant
    assistant = EducationalAssistant()

    # Initialize education service
    init_success = await assistant.initialize_education_service()

    if not init_success:
        print("FAILED to initialize education service")
        return

    print("SUCCESS: Education service initialized")

    # Create a mock context
    mock_context = MagicMock(spec=RunContext)

    # Test activity queries
    test_queries = [
        "What is Activity 1.1?",
        "Tell me about Activity 1.1",
        "What is Activity 1.1 in chapter 1?",
        "What is the Activity 1.1 in this chapter?",  # This was the original failing query
        "Activity 1.1"
    ]

    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Testing: '{query}'")
        print(f"{'='*60}")

        try:
            # Call the search_textbook tool function directly
            response = await assistant.search_textbook(
                context=mock_context,
                question=query,
                grade=6,
                subject="science"
            )

            print(f"Response length: {len(response)} characters")
            if len(response) > 200:
                print(f"Response preview: {response[:200]}...")
                # Check if it mentions chapter 1 content
                if "wonderful world" in response.lower() or "chapter 1" in response.lower():
                    print("SUCCESS: Response contains Chapter 1 content!")
                elif "activity" in response.lower():
                    print("INFO: Response mentions activities")
                else:
                    print("WARNING: Response may not be from correct chapter")
            else:
                print(f"Short response: {response}")

        except Exception as e:
            print(f"EXCEPTION: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_activity_queries())