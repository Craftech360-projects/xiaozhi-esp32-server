#!/usr/bin/env python3
"""
Test the new metadata-based chapter search
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

async def test_metadata_search():
    """Test metadata-based chapter search"""

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

    print("\n=== Testing Metadata-Based Chapter Search ===")

    # Test direct chapter search
    for chapter_num in [1, 2, 3, 4]:
        print(f"\n--- Testing Chapter {chapter_num} ---")

        try:
            result = await service.search_by_chapter(
                chapter_number=chapter_num,
                grade=6,
                subject="science"
            )

            if "error" in result:
                print(f"ERROR: {result['error']}")
                continue

            chapter_title = result.get('chapter_title', 'Unknown')
            answer = result.get('answer', 'No answer')
            confidence = result.get('confidence', 0.0)

            print(f"SUCCESS: Found Chapter {chapter_num}: {chapter_title}")
            print(f"Confidence: {confidence:.2f}")
            print(f"Answer length: {len(answer)} characters")
            print(f"Preview: {answer[:200]}...")

        except Exception as e:
            print(f"EXCEPTION: {e}")

    print("\n=== Testing Chapter Mapping ===")

    try:
        chapter_mapping = await service.get_chapter_mapping(6, "science")
        print(f"Found {len(chapter_mapping)} chapters:")
        for num, title in chapter_mapping.items():
            print(f"  Chapter {num}: {title}")

    except Exception as e:
        print(f"EXCEPTION in chapter mapping: {e}")

    print("\n=== Test Complete ===")

if __name__ == "__main__":
    asyncio.run(test_metadata_search())