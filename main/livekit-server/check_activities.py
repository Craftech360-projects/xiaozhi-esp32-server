#!/usr/bin/env python3
"""
Check what activity content exists in the chapters
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

async def check_activity_content():
    """Check what activity content exists in Chapter 1"""
    service = EducationService()
    await service.initialize()

    from qdrant_client.models import Filter, FieldCondition, MatchValue

    # Get all Chapter 1 content
    search_result = await asyncio.to_thread(
        service.qdrant_manager.client.scroll,
        collection_name='grade_06_science',
        scroll_filter=Filter(
            must=[FieldCondition(key='chapter_number', match=MatchValue(value=1))]
        ),
        limit=50,
        with_payload=True,
        with_vectors=False
    )

    points = search_result[0]
    print(f'Found {len(points)} chunks in Chapter 1')

    # Search for structured content patterns
    patterns_to_check = [
        'activity',
        'exercise',
        'question',
        'task',
        'experiment',
        'do you know',
        'try this',
        'observe',
        'investigation'
    ]

    print('\n--- Searching for structured content patterns ---')
    for pattern in patterns_to_check:
        matches = []
        for i, point in enumerate(points):
            content = point.payload.get('content', '').lower()
            if pattern in content:
                # Get a snippet around the match
                pos = content.find(pattern)
                start = max(0, pos - 50)
                end = min(len(content), pos + 150)
                snippet = content[start:end].replace('\n', ' ')
                matches.append(f'Chunk {i+1}: ...{snippet}...')

        print(f'\n{pattern.upper()}: Found {len(matches)} matches')
        for match in matches[:2]:  # Show first 2 matches
            print(f'  {match}')

    print('\n--- Sample content from first few chunks ---')
    for i in range(min(3, len(points))):
        content = points[i].payload.get('content', '')
        print(f'\nChunk {i+1} content (first 200 chars):')
        print(f'"{content[:200]}..."')

if __name__ == "__main__":
    asyncio.run(check_activity_content())