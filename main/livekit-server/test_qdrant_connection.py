#!/usr/bin/env python3
"""
Test Qdrant connection and check what data is available
"""

import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent / ".env")

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from qdrant_client import QdrantClient
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False

async def test_qdrant_connection():
    """Test connection to Qdrant and explore available data"""
    print("🔍 Testing Qdrant Connection...")
    
    if not QDRANT_AVAILABLE:
        print("❌ Qdrant client not installed. Install with: pip install qdrant-client")
        return
    
    # Get configuration from environment
    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    
    print(f"URL: {qdrant_url}")
    print(f"API Key: {qdrant_api_key[:20]}..." if qdrant_api_key else "No API Key")
    
    if not qdrant_url or not qdrant_api_key:
        print("❌ Qdrant configuration missing in .env file")
        return
    
    try:
        # Initialize client
        client = QdrantClient(
            url=qdrant_url,
            api_key=qdrant_api_key,
            timeout=10
        )
        
        print("✅ Qdrant client created")
        
        # Test connection
        collections = client.get_collections()
        print(f"✅ Connected to Qdrant! Found {len(collections.collections)} collections:")
        
        for collection in collections.collections:
            print(f"  - {collection.name}")
            
            # Get collection info
            try:
                info = client.get_collection(collection.name)
                print(f"    Points: {info.points_count}")
                print(f"    Vector size: {info.config.params.vectors.size}")
                
                # Sample some data
                if info.points_count > 0:
                    sample = client.scroll(
                        collection_name=collection.name,
                        limit=3,
                        with_payload=True
                    )
                    
                    print(f"    Sample data:")
                    for i, point in enumerate(sample[0][:2]):  # Show first 2 points
                        payload = point.payload
                        title = payload.get('title', 'No title')
                        language_or_category = payload.get('language') or payload.get('category', 'Unknown')
                        print(f"      {i+1}. '{title}' ({language_or_category})")
                        
                        # Show available fields
                        if i == 0:  # Only for first point
                            fields = list(payload.keys())
                            print(f"         Available fields: {fields}")
                            
            except Exception as e:
                print(f"    Error getting collection info: {e}")
        
        # Test search functionality
        print("\n🔍 Testing Search Functionality...")
        
        # Test music search
        music_collections = [c.name for c in collections.collections if 'music' in c.name.lower()]
        if music_collections:
            collection_name = music_collections[0]
            print(f"\nTesting music search in '{collection_name}':")
            
            # Get some sample data to test with
            sample = client.scroll(
                collection_name=collection_name,
                limit=5,
                with_payload=True
            )
            
            if sample[0]:
                # Test with a real song title
                test_song = sample[0][0].payload.get('title', 'baby shark')
                print(f"  Testing search for: '{test_song}'")
                
                # Try text-based search
                all_points = client.scroll(
                    collection_name=collection_name,
                    limit=100,
                    with_payload=True
                )
                
                matches = []
                for point in all_points[0]:
                    title = point.payload.get('title', '').lower()
                    if test_song.lower() in title:
                        matches.append(point.payload)
                
                print(f"  Found {len(matches)} matches")
                for match in matches[:3]:
                    title = match.get('title', 'No title')
                    language = match.get('language', 'Unknown')
                    print(f"    - '{title}' ({language})")
        
        # Test story search
        story_collections = [c.name for c in collections.collections if 'stor' in c.name.lower()]
        if story_collections:
            collection_name = story_collections[0]
            print(f"\nTesting story search in '{collection_name}':")
            
            # Get some sample data
            sample = client.scroll(
                collection_name=collection_name,
                limit=5,
                with_payload=True
            )
            
            if sample[0]:
                test_story = sample[0][0].payload.get('title', 'goldilocks')
                print(f"  Testing search for: '{test_story}'")
                
                # Try text-based search
                all_points = client.scroll(
                    collection_name=collection_name,
                    limit=100,
                    with_payload=True
                )
                
                matches = []
                for point in all_points[0]:
                    title = point.payload.get('title', '').lower()
                    if test_story.lower() in title:
                        matches.append(point.payload)
                
                print(f"  Found {len(matches)} matches")
                for match in matches[:3]:
                    title = match.get('title', 'No title')
                    category = match.get('category', 'Unknown')
                    print(f"    - '{title}' ({category})")
        
        print("\n✅ Qdrant connection test completed successfully!")
        
    except Exception as e:
        print(f"❌ Failed to connect to Qdrant: {e}")
        print("This could be due to:")
        print("  - Network connectivity issues")
        print("  - Invalid API key or URL")
        print("  - Qdrant service being down")

if __name__ == "__main__":
    asyncio.run(test_qdrant_connection())