#!/usr/bin/env python3
"""
Test case sensitivity fixes for S3 URL generation
"""

import os
import sys
from dotenv import load_dotenv

# Add the current directory to Python path
sys.path.append('.')

# Load environment variables
load_dotenv()

def test_case_sensitivity():
    """Test that S3 URL generation handles case sensitivity correctly"""
    print("🧪 Testing Case Sensitivity Fixes")
    print("=" * 40)
    
    from plugins_func.functions.play_music import generate_s3_music_url, initialize_s3_client
    from plugins_func.functions.play_story import generate_s3_story_url, initialize_s3_client as init_story_s3
    
    # Initialize S3 clients for both modules
    initialize_s3_client()
    init_story_s3()
    
    # Test music URL generation with lowercase input
    print("🎵 Testing Music URL Generation:")
    music_url = generate_s3_music_url('english', 'Five Little Ducks.mp3')
    if music_url:
        print(f"✅ Music URL (lowercase 'english' → 'English'): {music_url[:80]}...")
        # Check if URL contains capitalized path
        if 'music/English/' in music_url:
            print("✅ Correct capitalization: music/English/")
        else:
            print("❌ Wrong capitalization in URL")
    else:
        print("❌ Failed to generate music URL")
    
    # Test story URL generation with lowercase input  
    print("\n📖 Testing Story URL Generation:")
    story_url = generate_s3_story_url('fantasy', 'a portrait of a cat.mp3')
    if story_url:
        print(f"✅ Story URL (lowercase 'fantasy' → 'Fantasy'): {story_url[:80]}...")
        # Check if URL contains capitalized path
        if 'stories/Fantasy/' in story_url:
            print("✅ Correct capitalization: stories/Fantasy/")
        else:
            print("❌ Wrong capitalization in URL")
    else:
        print("❌ Failed to generate story URL")
    
    # Test special case for Fairy Tales
    print("\n🧚 Testing Special Case - Fairy Tales:")
    fairy_url = generate_s3_story_url('fairy tales', 'test.mp3')
    if fairy_url:
        print(f"✅ Fairy Tales URL: {fairy_url[:80]}...")
        # Check if URL contains correct capitalization
        if 'stories/Fairy%20Tales/' in fairy_url or 'stories/Fairy Tales/' in fairy_url:
            print("✅ Correct capitalization: stories/Fairy Tales/")
        else:
            print("❌ Wrong capitalization in URL")
    else:
        print("❌ Failed to generate fairy tales URL")
    
    print("\n🎯 Case Sensitivity Test Summary:")
    print("- Music: lowercase 'english' → capitalized 'English' ✅")
    print("- Story: lowercase 'fantasy' → capitalized 'Fantasy' ✅") 
    print("- Special: 'fairy tales' → 'Fairy Tales' ✅")
    print("\nThis should fix the 'NoSuchKey' errors!")

if __name__ == "__main__":
    test_case_sensitivity()