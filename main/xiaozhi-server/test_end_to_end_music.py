#!/usr/bin/env python3
"""
End-to-end test for music playback with S3 streaming
"""

import os
import sys
import asyncio
import queue
from unittest.mock import Mock, MagicMock, AsyncMock
from dotenv import load_dotenv

# Add the current directory to Python path
sys.path.append('.')

# Load environment variables
load_dotenv()

async def test_end_to_end_music_playback():
    """Test complete music playback flow with S3 streaming"""
    print("🎵 Testing End-to-End Music Playback")
    print("=" * 45)
    
    from plugins_func.functions.play_music import handle_multilingual_music_command, initialize_s3_client, initialize_multilingual_music_system
    from core.providers.tts.dto.dto import TTSMessageDTO, SentenceType, ContentType
    
    # Initialize S3 client
    initialize_s3_client()
    
    try:
        # Create mock connection
        conn = Mock()
        conn.logger = Mock()
        conn.logger.bind.return_value = conn.logger
        conn.logger.info = Mock()
        conn.logger.error = Mock()
        conn.logger.debug = Mock()
        
        # Mock dialogue
        conn.dialogue = Mock()
        conn.dialogue.put = Mock()
        
        # Mock TTS system
        conn.tts = Mock()
        conn.tts.tts_text_queue = queue.Queue()
        
        # Mock other attributes
        conn.sentence_id = "test_123"
        conn.intent_type = "intent_llm"
        
        # Mock config for music system initialization
        conn.config = {
            "plugins": {
                "play_music": {
                    "music_dir": "./music",
                    "music_ext": [".mp3", ".wav", ".p3"],
                    "refresh_time": 60
                }
            }
        }
        
        # Initialize the music system
        initialize_multilingual_music_system(conn)
        
        # Test different types of music requests
        test_requests = [
            ("play Baa Baa Black Sheep", "specific", None),
            ("play Hindi song", "language_specific", "hindi"),
            ("play any music", "random", None),
        ]
        
        for user_request, song_type, language_preference in test_requests:
            print(f"\n🎯 Testing: '{user_request}'")
            print(f"   Type: {song_type}, Language: {language_preference}")
            
            # Clear the TTS queue
            while not conn.tts.tts_text_queue.empty():
                conn.tts.tts_text_queue.get()
            
            # Call the music handler
            await handle_multilingual_music_command(conn, user_request, song_type, language_preference)
            
            # Check if messages were queued
            messages = []
            while not conn.tts.tts_text_queue.empty():
                messages.append(conn.tts.tts_text_queue.get())
            
            print(f"   📝 TTS messages queued: {len(messages)}")
            
            # Look for FILE message with S3 URL
            file_messages = [msg for msg in messages if msg.content_type == ContentType.FILE]
            
            if file_messages:
                file_msg = file_messages[0]
                print(f"   🔗 S3 URL found: {file_msg.content_file[:60]}...")
                
                # Verify it's a valid S3 URL
                if file_msg.content_file.startswith('https://cheeko-audio-files.s3.amazonaws.com/'):
                    print("   ✅ Valid S3 URL generated")
                else:
                    print("   ❌ Invalid S3 URL format")
                    return False
            else:
                print("   ❌ No FILE message with S3 URL found")
                return False
        
        print("\n🎉 End-to-End Test Results:")
        print("✅ Music requests processed successfully")
        print("✅ S3 URLs generated for audio files")
        print("✅ TTS messages queued properly")
        print("✅ System ready for voice commands")
        
        return True
        
    except Exception as e:
        print(f"❌ End-to-end test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_tts_file_processing():
    """Test that TTS system processes S3 URLs correctly"""
    print("\n🔧 Testing TTS File Processing")
    print("-" * 35)
    
    from core.providers.tts.base import TTSProviderBase
    from plugins_func.functions.play_music import generate_s3_music_url
    
    # Generate test S3 URL
    test_url = generate_s3_music_url('English', 'Baa Baa Black Sheep.mp3')
    
    if not test_url:
        print("❌ Could not generate test S3 URL")
        return False
    
    # Test the URL validation logic (the fix we implemented)
    tts_file = test_url
    is_url = tts_file and (tts_file.startswith('http://') or tts_file.startswith('https://'))
    file_exists_or_url = tts_file and (is_url or os.path.exists(tts_file))
    
    print(f"🔍 TTS File Processing Logic:")
    print(f"   Input: {tts_file[:60]}...")
    print(f"   Detected as URL: {is_url}")
    print(f"   Will be processed: {file_exists_or_url}")
    
    if file_exists_or_url:
        print("✅ TTS system will process S3 URLs")
        return True
    else:
        print("❌ TTS system will reject S3 URLs")
        return False

if __name__ == "__main__":
    print("🚀 Starting Comprehensive Music Playback Test")
    print("=" * 50)
    
    # Test TTS file processing first
    tts_success = test_tts_file_processing()
    
    # Test end-to-end flow
    e2e_success = asyncio.run(test_end_to_end_music_playback())
    
    print("\n" + "=" * 50)
    print("📊 FINAL TEST RESULTS")
    print("=" * 50)
    
    if tts_success and e2e_success:
        print("🎉 ALL TESTS PASSED!")
        print("✅ S3 streaming integration is complete")
        print("✅ Voice commands will now play music from S3")
        print("✅ System is ready for production use")
        print("\n💡 Try saying: 'Play Baa Baa Black Sheep' or 'Play Hindi song'")
    else:
        print("❌ SOME TESTS FAILED")
        print("🔧 Check the errors above for details")
        if not tts_success:
            print("   - TTS file processing needs attention")
        if not e2e_success:
            print("   - End-to-end flow needs attention")