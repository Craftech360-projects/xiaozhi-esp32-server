"""
Test script for S3 Audio Player
Run this to test the S3 streaming functionality
"""

import os
from dotenv import load_dotenv
from s3_audio_player import S3AudioPlayer

# Load environment variables from .env file
load_dotenv()

def test_s3_audio_player():
    """Test the S3 audio player functionality"""
    
    # Check if AWS credentials are set
    if not os.getenv('AWS_ACCESS_KEY_ID'):
        print("❌ AWS_ACCESS_KEY_ID not found in environment variables")
        print("Please create a .env file with your AWS credentials")
        return
    
    if not os.getenv('AWS_SECRET_ACCESS_KEY'):
        print("❌ AWS_SECRET_ACCESS_KEY not found in environment variables")
        print("Please create a .env file with your AWS credentials")
        return
    
    print("✅ AWS credentials found in environment")
    
    # Initialize the player
    player = S3AudioPlayer()
    
    # Test listing available content
    print("\n📁 Available Music Languages:")
    music_langs = player.list_available_music()
    for lang in music_langs:
        print(f"  - {lang}")
    
    print("\n📚 Available Story Categories:")
    story_cats = player.list_available_stories()
    for cat in story_cats:
        print(f"  - {cat}")
    
    # Test getting songs in a language (if Hindi exists)
    if "Hindi" in music_langs:
        print(f"\n🎵 Songs in Hindi:")
        hindi_songs = player.get_songs_in_language("Hindi")
        for song in hindi_songs[:5]:  # Show first 5
            print(f"  - {song}")
    
    # Test getting stories in a category (if Fantasy exists)
    if "Fantasy" in story_cats:
        print(f"\n📖 Stories in Fantasy:")
        fantasy_stories = player.get_stories_in_category("Fantasy")
        for story in fantasy_stories[:5]:  # Show first 5
            print(f"  - {story}")
    
    print("\n🎯 To test actual playback, uncomment the lines below:")
    print("# result = player.play_music('Hindi', 'bandar mama')")
    print("# print(result)")
    
    #Uncomment these lines to test actual playback
    if music_langs:
        test_lang = music_langs[0]
        songs = player.get_songs_in_language(test_lang)
        if songs:
            print(f"\n🎵 Testing playback of first song in {test_lang}...")
            result = player.play_music(test_lang, songs[0])
            print(f"Result: {result}")

if __name__ == "__main__":
    test_s3_audio_player()