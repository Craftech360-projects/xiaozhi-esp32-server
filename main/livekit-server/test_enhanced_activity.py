#!/usr/bin/env python3
"""
Test Enhanced Activity and Chapter Detection
"""

import asyncio
import sys
import os
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv(".env")

# Add the src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__)))

from src.services.education_service import EducationService

async def test_enhanced_activity_detection():
    """Test the enhanced chapter + activity detection system"""

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

    # Test various query types
    test_queries = [
        # Chapter + Activity queries (should use metadata search for activity)
        "in chapter 1, what is activity 1?",
        "What is Activity 1.1 in chapter 1?",
        "Tell me about activity 2 in chapter 1",
        "Chapter 2 activity 1",
        "In chapter 3, explain activity 1.2",

        # Chapter-only queries (should use metadata search for chapter)
        "What is chapter 1 about?",
        "Tell me about chapter 2",

        # Activity-only queries (should use semantic search)
        "What is activity 1.1?",
        "Tell me about activity 2",

        # General queries (should use semantic search)
        "What are living things?",
        "How do magnets work?"
    ]

    print("\n=== Testing Enhanced Detection System ===\n")

    for query in test_queries:
        print(f"--- Query: '{query}' ---")

        try:
            result = await service.answer_question(
                question=query,
                grade=6,
                subject="science"
            )

            if "error" not in result:
                answer = result.get('answer', '')
                confidence = result.get('confidence', 0.0)
                activity_number = result.get('activity_number')
                chapter_number = result.get('chapter_number')

                print(f"SUCCESS: Got answer with confidence {confidence:.2f}")
                print(f"Answer length: {len(answer)} characters")

                # Determine search type based on result
                if activity_number and chapter_number:
                    print(f"SEARCH TYPE: ✅ Chapter + Activity Metadata Search (Ch.{chapter_number} Act.{activity_number})")
                elif chapter_number and not activity_number:
                    print(f"SEARCH TYPE: ✅ Chapter Metadata Search (Ch.{chapter_number})")
                else:
                    print("SEARCH TYPE: 🔍 Semantic Search")

                if answer:
                    print(f"Preview: {answer[:200]}...")

            else:
                print(f"ERROR: {result.get('error', 'Unknown error')}")

        except Exception as e:
            print(f"EXCEPTION: {e}")

        print()  # Empty line for readability

    print("=== Test Summary ===")
    print("The enhanced system should now:")
    print("1. Use Activity + Chapter metadata search for 'in chapter X, activity Y' queries")
    print("2. Use Chapter metadata search for 'chapter X' queries")
    print("3. Fall back to semantic search for general queries")
    print("4. Provide more specific activity-focused answers")

if __name__ == "__main__":
    asyncio.run(test_enhanced_activity_detection())