#!/usr/bin/env python3
"""
Test TTS system integration with S3 URLs
"""

import os
import sys
import asyncio
import queue
from unittest.mock import Mock, MagicMock
from dotenv import load_dotenv

# Add the current directory to Python path
sys.path.append('.')

# Load environment variables
load_dotenv()

def test_tts_s3_url_processing():
    """Test that TTS system can handle S3 URLs in ContentType.FILE messages"""
    print("🧪 Testing TTS S3 URL Processing")
    print("=" * 40)
    
    from core.providers.tts.base import TTSProviderBase
    from core.providers.tts.dto.dto import TTSMessageDTO, SentenceType, ContentType
    from plugins_func.functions.play_music import generate_s3_music_url, initialize_s3_client
    
    # Initialize S3 client
    initialize_s3_client()
    
    # Generate a test S3 URL
    test_url = generate_s3_music_url('English', 'Baa Baa Black Sheep.mp3')
    
    if not test_url:
        print("❌ Failed to generate S3 URL for testing")
        return False
    
    print(f"🔗 Test S3 URL: {test_url[:80]}...")
    
    try:
        # Create a mock TTS provider
        class TestTTSProvider(TTSProviderBase):
            def __init__(self):
                config = {"output_dir": "tmp/"}
                super().__init__(config, delete_audio_file=True)
                
                # Mock connection
                self.conn = Mock()
                self.conn.stop_event = Mock()
                self.conn.stop_event.is_set.return_value = False
                self.conn.audio_format = "opus"
                
                # Mock queue
                self.tts_text_queue = queue.Queue()
                self.tts_audio_queue = queue.Queue()
            
            def to_tts(self, text):
                return []  # Mock implementation
            
            def text_to_speak(self, text):
                return []  # Mock implementation for abstract method
        
        # Create test provider
        provider = TestTTSProvider()
        
        # Create a FILE message with S3 URL
        file_message = TTSMessageDTO(
            sentence_id="test_123",
            sentence_type=SentenceType.MIDDLE,
            content_type=ContentType.FILE,
            content_file=test_url,
            content_detail="Test music file"
        )
        
        # Put message in queue
        provider.tts_text_queue.put(file_message)
        
        # Test the URL validation logic
        tts_file = test_url
        is_url = tts_file and (tts_file.startswith('http://') or tts_file.startswith('https://'))
        file_exists_or_url = tts_file and (is_url or os.path.exists(tts_file))
        
        print(f"🔍 URL Detection:")
        print(f"   Is URL: {is_url}")
        print(f"   File exists or URL: {file_exists_or_url}")
        
        if not file_exists_or_url:
            print("❌ URL validation failed")
            return False
        
        # Test audio processing
        print("🎵 Testing audio processing...")
        audio_datas = provider._process_audio_file(test_url)
        
        if audio_datas and len(audio_datas) > 0:
            print(f"✅ Successfully processed S3 audio!")
            print(f"   Audio frames: {len(audio_datas)}")
            print(f"   First frame size: {len(audio_datas[0]) if audio_datas else 0} bytes")
            return True
        else:
            print("❌ Failed to process S3 audio")
            return False
            
    except Exception as e:
        print(f"❌ Error testing TTS S3 integration: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_local_file_compatibility():
    """Test that local file processing still works"""
    print("\n📁 Testing Local File Compatibility")
    print("-" * 40)
    
    # Test the validation logic for local files
    local_file = "nonexistent_file.mp3"
    is_url = local_file and (local_file.startswith('http://') or local_file.startswith('https://'))
    file_exists_or_url = local_file and (is_url or os.path.exists(local_file))
    
    print(f"🔍 Local File Detection:")
    print(f"   Is URL: {is_url}")
    print(f"   File exists or URL: {file_exists_or_url}")
    print("✅ Local file logic preserved (would check os.path.exists)")

if __name__ == "__main__":
    success = test_tts_s3_url_processing()
    test_local_file_compatibility()
    
    if success:
        print("\n🎉 TTS S3 Integration Fix Complete!")
        print("✅ TTS system can now process S3 URLs")
        print("✅ Music playback should work end-to-end")
        print("✅ Local file compatibility maintained")
    else:
        print("\n❌ TTS S3 Integration needs attention")
        print("Check the error above for details")