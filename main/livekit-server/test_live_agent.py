#!/usr/bin/env python3
"""
Test the live agent with chapter queries
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

async def test_live_agent():
    """Test the agent with actual chapter queries"""

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

    # Test chapter queries
    test_queries = [
        "What is chapter 1 about?",
        "Tell me about chapter 1",
        "Chapter 1 of Grade 6 Science",
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

            print(f"\nResponse length: {len(response)} characters")
            print(f"Response preview: {response[:300]}...")

        except Exception as e:
            print(f"EXCEPTION: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_live_agent())