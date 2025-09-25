#!/usr/bin/env python3
"""
Test script to verify Chapter 1 content retrieval
"""

import asyncio
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env")

# Add the src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__)))

from src.services.education_service import EducationService

async def test_chapter1_queries():
    """Test Chapter 1 related queries"""

    # Initialize education service
    service = EducationService()
    success = await service.initialize()

    if not success:
        print("FAILED to initialize education service")
        return

    print("SUCCESS: Education service initialized")

    # Set Grade 6 Science context
    await service.set_student_context(6, "science")
    print("SUCCESS: Context set to Grade 6 Science")

    # Test queries
    test_queries = [
        "What is Chapter 1 about?",
        "Chapter 1",
        "The Wonderful World of Science",
        "what is science",
        "science introduction"
    ]

    print("\n=== Testing Chapter 1 Queries ===")

    for i, query in enumerate(test_queries, 1):
        print(f"\n--- Test {i}: {query} ---")

        try:
            result = await service.answer_question(
                question=query,
                grade=6,
                subject="science",
                include_examples=True
            )

            if "error" in result:
                print(f"ERROR: {result['error']}")
                continue

            answer = result.get('answer', 'No answer')
            confidence = result.get('confidence', 0.0)
            sources = result.get('sources', [])

            print(f"SUCCESS: Found answer (confidence: {confidence:.2f})")
            print(f"Answer length: {len(answer)} characters")
            print(f"Answer preview: {answer[:150]}...")

            if sources:
                source = sources[0]
                print(f"Source: {source.get('textbook', 'Unknown')} - {source.get('chapter', 'Unknown chapter')}")

        except Exception as e:
            print(f"EXCEPTION: {e}")

    print("\n=== Test Complete ===")

if __name__ == "__main__":
    asyncio.run(test_chapter1_queries())