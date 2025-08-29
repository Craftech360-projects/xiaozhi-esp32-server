"""
Test the true streaming S3 audio player
"""

import os
import time
from dotenv import load_dotenv
from streaming_audio_player import StreamingS3AudioPlayer

load_dotenv()

def test_streaming_backends():
    """Test which streaming backends are available"""
    print("🎵 Testing Streaming Audio Backends")
    print("=" * 40)
    
    # Test VLC
    try:
        import vlc
        print("✅ VLC available - Best for streaming")
        vlc_version = vlc.libvlc_get_version().decode('utf-8')
        print(f"   Version: {vlc_version}")
    except ImportError:
        print("❌ VLC not available")
        print("   Install with: pip install python-vlc")
        print("   Or download VLC media player")
    
    # Test pygame
    try:
        import pygame
        print("✅ Pygame available - Good for streaming")
        print(f"   Version: {pygame.version.ver}")
    except ImportError:
        print("❌ Pygame not available")
        print("   Install with: pip install pygame")
    
    # Test system capabilities
    import platform
    system = platform.system()
    print(f"✅ System: {system} - Can use system player as fallback")

def test_streaming_player():
    """Test the streaming S3 audio player"""
    print("\n🎵 Testing Streaming S3 Audio Player")
    print("=" * 45)
    
    # Initialize player
    player = StreamingS3AudioPlayer()
    print(f"Audio backend: {player.backend}")
    
    if not player.backend:
        print("❌ No audio backend available!")
        print("Install VLC or pygame for streaming support")
        return
    
    # List available content
    music_langs = player.list_available_music()
    story_cats = player.list_available_stories()
    
    print(f"\nAvailable music languages: {music_langs}")
    print(f"Available story categories: {story_cats}")
    
    if not music_langs:
        print("❌ No music metadata found")
        return
    
    # Test music streaming
    test_lang = music_langs[0]
    print(f"\n🎵 Testing music streaming in {test_lang}...")
    
    # Get first song
    songs = []
    metadata_file = player.music_path / test_lang / "metadata.json"
    if metadata_file.exists():
        import json
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        songs = list(metadata.keys())
    
    if songs:
        test_song = songs[0]
        print(f"Streaming: {test_song}")
        
        result = player.play_music(test_lang, test_song)
        print(f"Result: {result}")
        
        # Check playback status
        time.sleep(2)  # Wait for streaming to start
        status = player.get_playback_status()
        print(f"Playback status: {status}")
        
        if status.get('playing'):
            print("✅ Streaming is working!")
            print("Let it play for 10 seconds...")
            time.sleep(10)
            
            # Stop playback
            player.stop_playback()
            print("⏹️ Stopped playback")
        else:
            print("❌ Streaming failed to start")
    
    # Test story streaming if available
    if story_cats:
        print(f"\n📚 Testing story streaming in {story_cats[0]}...")
        
        stories = []
        metadata_file = player.stories_path / story_cats[0] / "metadata.json"
        if metadata_file.exists():
            import json
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            stories = list(metadata.keys())
        
        if stories:
            test_story = stories[0]
            print(f"Streaming story: {test_story}")
            
            result = player.play_story(story_cats[0], test_story)
            print(f"Result: {result}")
            
            time.sleep(3)
            status = player.get_playback_status()
            print(f"Story playback status: {status}")
            
            if status.get('playing'):
                print("✅ Story streaming is working!")
                time.sleep(5)
                player.stop_playback()
            else:
                print("❌ Story streaming failed")

def interactive_test():
    """Interactive streaming test"""
    print("\n🎮 Interactive Streaming Test")
    print("=" * 35)
    
    player = StreamingS3AudioPlayer()
    
    if not player.backend:
        print("❌ No audio backend available for interactive test")
        return
    
    while True:
        print("\nCommands:")
        print("1. Play music: music <language> <song>")
        print("2. Play story: story <category> <story>")
        print("3. Stop: stop")
        print("4. Status: status")
        print("5. List: list")
        print("6. Quit: quit")
        
        command = input("\nEnter command: ").strip().lower()
        
        if command == "quit":
            player.stop_playback()
            break
        elif command == "stop":
            player.stop_playback()
            print("⏹️ Stopped playback")
        elif command == "status":
            status = player.get_playback_status()
            print(f"Status: {status}")
        elif command == "list":
            print(f"Music: {player.list_available_music()}")
            print(f"Stories: {player.list_available_stories()}")
        elif command.startswith("music "):
            parts = command.split(" ", 2)
            if len(parts) >= 3:
                result = player.play_music(parts[1], parts[2])
                print(result)
            else:
                print("Usage: music <language> <song>")
        elif command.startswith("story "):
            parts = command.split(" ", 2)
            if len(parts) >= 3:
                result = player.play_story(parts[1], parts[2])
                print(result)
            else:
                print("Usage: story <category> <story>")
        else:
            print("Unknown command")

if __name__ == "__main__":
    test_streaming_backends()
    test_streaming_player()
    
    print("\n" + "=" * 50)
    user_input = input("Run interactive test? (y/n): ")
    if user_input.lower() == 'y':
        interactive_test()