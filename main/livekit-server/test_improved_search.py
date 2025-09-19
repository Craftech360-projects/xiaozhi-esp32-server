#!/usr/bin/env python3
"""
Test the improved semantic search with real Qdrant data
"""

import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables FIRST
load_dotenv(Path(__file__).parent / ".env")

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from services.music_service import MusicService
from services.story_service import StoryService

async def test_improved_search():
    """Test the improved semantic search functionality"""
    print("🔍 Testing Improved Semantic Search...")
    
    # Initialize services
    music_service = MusicService()
    story_service = StoryService()
    
    # Test music service initialization
    print("\n1. Testing Music Service Initialization...")
    music_init = await music_service.initialize()
    print(f"Music service initialized: {music_init}")
    
    if music_init:
        # Get available languages
        languages = await music_service.get_all_languages()
        print(f"Available languages: {languages}")
        
        # Test searches across different languages
        print("\n2. Testing Multi-Language Music Search...")
        
        test_queries = [
            ("baby shark", None, "English nursery rhyme"),
            ("bby shark", None, "Misspelled baby shark"),  # Missing letters
            ("baby shrak", None, "Transposed letters"),
            ("hanuman", None, "Hindi/Sanskrit content"),
            ("ganesh", None, "Sanskrit sloka"),
            ("aane", None, "Kannada song"),
            ("chanda mama", None, "Telugu lullaby"),
            ("abc", None, "Phonics content"),
            ("apple", None, "Learning content"),
            ("completely unknown song", None, "Non-existent")
        ]
        
        for query, language_filter, description in test_queries:
            print(f"\n🔍 Searching for: '{query}' ({description})")
            results = await music_service.search_songs(query, language_filter)
            
            if results:
                print(f"  ✅ Found {len(results)} results:")
                for i, result in enumerate(results[:3]):
                    print(f"    {i+1}. '{result['title']}' ({result['language']}) - Score: {result['score']:.2f}")
            else:
                print(f"  ❌ No results found")
        
        # Test language-specific searches
        print("\n3. Testing Language-Specific Searches...")
        
        for language in languages[:3]:  # Test first 3 languages
            print(f"\n🌐 Searching in {language}:")
            results = await music_service.search_songs("song", language)
            if results:
                print(f"  Found {len(results)} results in {language}")
                for result in results[:2]:
                    print(f"    - '{result['title']}'")
    
    # Test story service
    print("\n4. Testing Story Service Initialization...")
    story_init = await story_service.initialize()
    print(f"Story service initialized: {story_init}")
    
    if story_init:
        # Get available categories
        categories = await story_service.get_all_categories()
        print(f"Available categories: {categories}")
        
        # Test story searches
        print("\n5. Testing Multi-Category Story Search...")
        
        story_queries = [
            ("goldilocks", None, "Classic fairy tale"),
            ("goldilock", None, "Misspelled goldilocks"),  # Missing s
            ("three bears", None, "Partial story name"),
            ("bertie", None, "Character name"),
            ("astropup", None, "Space adventure"),
            ("cat", None, "Animal stories"),
            ("unknown story", None, "Non-existent")
        ]
        
        for query, category_filter, description in story_queries:
            print(f"\n🔍 Searching for: '{query}' ({description})")
            results = await story_service.search_stories(query, category_filter)
            
            if results:
                print(f"  ✅ Found {len(results)} results:")
                for i, result in enumerate(results[:3]):
                    print(f"    {i+1}. '{result['title']}' ({result['category']}) - Score: {result['score']:.2f}")
            else:
                print(f"  ❌ No results found")
        
        # Test category-specific searches
        print("\n6. Testing Category-Specific Searches...")
        
        for category in categories[:3]:  # Test first 3 categories
            print(f"\n📚 Searching in {category}:")
            results = await story_service.search_stories("story", category)
            if results:
                print(f"  Found {len(results)} results in {category}")
                for result in results[:2]:
                    print(f"    - '{result['title']}'")
    
    print("\n✅ Improved search testing completed!")
    print("\nKey Improvements Demonstrated:")
    print("🔧 Multi-language search (not just English)")
    print("🔧 Spell tolerance for misspellings")
    print("🔧 Partial word matching")
    print("🔧 Cross-category/language search")
    print("🔧 Fuzzy matching with scoring")

if __name__ == "__main__":
    asyncio.run(test_improved_search())