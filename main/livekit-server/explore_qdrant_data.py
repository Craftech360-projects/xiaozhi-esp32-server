#!/usr/bin/env python3
"""
Explore Qdrant data structure to understand available languages and content
"""

import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv
from collections import defaultdict

# Load environment variables
load_dotenv(Path(__file__).parent / ".env")

try:
    from qdrant_client import QdrantClient
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False

async def explore_qdrant_data():
    """Explore what data is available in Qdrant"""
    print("🔍 Exploring Qdrant Data Structure...")
    
    if not QDRANT_AVAILABLE:
        print("❌ Qdrant client not installed")
        return
    
    # Get configuration
    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    
    try:
        client = QdrantClient(
            url=qdrant_url,
            api_key=qdrant_api_key,
            timeout=10
        )
        
        # Explore music collection
        print("\n🎵 MUSIC COLLECTION ANALYSIS")
        print("=" * 50)
        
        music_points = client.scroll(
            collection_name="xiaozhi_music",
            limit=1000,  # Get all points
            with_payload=True
        )
        
        languages = defaultdict(list)
        all_titles = []
        
        for point in music_points[0]:
            payload = point.payload
            title = payload.get('title', 'Unknown')
            language = payload.get('language', 'Unknown')
            filename = payload.get('filename', 'Unknown')
            
            languages[language].append(title)
            all_titles.append(title)
        
        print(f"Total music tracks: {len(all_titles)}")
        print(f"Languages found: {len(languages)}")
        
        for language, titles in languages.items():
            print(f"\n📁 {language} ({len(titles)} tracks):")
            for title in titles[:5]:  # Show first 5
                print(f"  - {title}")
            if len(titles) > 5:
                print(f"  ... and {len(titles) - 5} more")
        
        # Explore story collection
        print("\n\n📚 STORY COLLECTION ANALYSIS")
        print("=" * 50)
        
        story_points = client.scroll(
            collection_name="xiaozhi_stories",
            limit=1000,  # Get all points
            with_payload=True
        )
        
        categories = defaultdict(list)
        all_story_titles = []
        
        for point in story_points[0]:
            payload = point.payload
            title = payload.get('title', 'Unknown')
            category = payload.get('category', 'Unknown')
            filename = payload.get('filename', 'Unknown')
            
            categories[category].append(title)
            all_story_titles.append(title)
        
        print(f"Total stories: {len(all_story_titles)}")
        print(f"Categories found: {len(categories)}")
        
        for category, titles in categories.items():
            print(f"\n📁 {category} ({len(titles)} stories):")
            for title in titles[:5]:  # Show first 5
                print(f"  - {title}")
            if len(titles) > 5:
                print(f"  ... and {len(titles) - 5} more")
        
        # Test search with misspellings
        print("\n\n🔍 TESTING SEARCH WITH MISSPELLINGS")
        print("=" * 50)
        
        # Test music search
        print("\n🎵 Music Search Tests:")
        
        # Find a common song to test with
        test_songs = []
        for point in music_points[0][:10]:
            title = point.payload.get('title', '')
            if any(word in title.lower() for word in ['baby', 'shark', 'twinkle', 'song']):
                test_songs.append(title)
        
        if test_songs:
            original_title = test_songs[0]
            print(f"Original: '{original_title}'")
            
            # Create misspelled versions
            misspelled_queries = [
                original_title.replace('a', ''),  # Missing letter
                original_title.replace('baby', 'bby'),  # Missing letters
                original_title.replace('shark', 'shrak'),  # Transposed letters
                original_title.split()[0] if ' ' in original_title else original_title[:4]  # Partial
            ]
            
            for query in misspelled_queries:
                if query and query != original_title:
                    matches = []
                    for point in music_points[0]:
                        title = point.payload.get('title', '').lower()
                        if query.lower() in title or any(word in title for word in query.lower().split()):
                            matches.append(point.payload.get('title'))
                    
                    print(f"Query: '{query}' -> {len(matches)} matches")
                    if matches:
                        print(f"  Best match: '{matches[0]}'")
        
        # Test story search
        print("\n📚 Story Search Tests:")
        
        # Find a common story to test with
        test_stories = []
        for point in story_points[0][:10]:
            title = point.payload.get('title', '')
            if any(word in title.lower() for word in ['goldilocks', 'three', 'bears', 'little']):
                test_stories.append(title)
        
        if test_stories:
            original_title = test_stories[0]
            print(f"Original: '{original_title}'")
            
            # Test partial matches
            partial_queries = [
                'goldilocks',
                'three bears',
                'goldilock',  # Missing s
                'bears'
            ]
            
            for query in partial_queries:
                matches = []
                for point in story_points[0]:
                    title = point.payload.get('title', '').lower()
                    if query.lower() in title or any(word in title for word in query.lower().split()):
                        matches.append(point.payload.get('title'))
                
                print(f"Query: '{query}' -> {len(matches)} matches")
                if matches:
                    print(f"  Best match: '{matches[0]}'")
        
        print("\n✅ Data exploration completed!")
        
    except Exception as e:
        print(f"❌ Error exploring data: {e}")

if __name__ == "__main__":
    asyncio.run(explore_qdrant_data())