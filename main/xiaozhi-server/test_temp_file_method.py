"""
Test the temporary file download method for S3 audio streaming
"""

import os
from dotenv import load_dotenv
from s3_audio_player import S3AudioPlayer

load_dotenv()

def test_temp_file_streaming():
    """Test the S3 audio player with temporary file method"""
    
    print("🎵 Testing S3 Audio Player with Temp File Method")
    print("=" * 55)
    
    # Initialize player
    player = S3AudioPlayer()
    
    # List available content
    print("\n📁 Available Music Languages:")
    music_langs = player.list_available_music()
    for lang in music_langs:
        print(f"  - {lang}")
    
    if not music_langs:
        print("❌ No music languages found. Check your metadata.json files.")
        return
    
    # Test with English if available
    if "English" in music_langs:
        print(f"\n🎵 Songs in English:")
        english_songs = player.get_songs_in_language("English")
        for i, song in enumerate(english_songs[:5], 1):
            print(f"  {i}. {song}")
        
        if english_songs:
            print(f"\n🎯 Testing playback of: {english_songs[0]}")
            print("This should download the file temporarily and play it...")
            
            # Test the actual playback
            result = player.play_music("English", english_songs[0])
            print(f"Result: {result}")
    
    # Test stories if available
    print("\n📚 Available Story Categories:")
    story_cats = player.list_available_stories()
    for cat in story_cats:
        print(f"  - {cat}")
    
    if story_cats:
        test_cat = story_cats[0]
        stories = player.get_stories_in_category(test_cat)
        if stories:
            print(f"\n📖 Testing story playback: {stories[0]}")
            result = player.play_story(test_cat, stories[0])
            print(f"Result: {result}")

def test_manual_temp_download():
    """Manually test the temporary file download and playback"""
    import requests
    import tempfile
    from pydub import AudioSegment
    from pydub.playback import play
    
    print("\n🔧 Manual Temp File Test")
    print("-" * 30)
    
    # Use a working presigned URL
    import boto3
    s3_client = boto3.client(
        's3',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
    )
    
    bucket_name = 'cheeko-audio-files'
    test_key = 'music/English/Baa Baa Black Sheep.mp3'
    
    try:
        # Generate presigned URL
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': test_key},
            ExpiresIn=3600
        )
        print(f"✅ Generated presigned URL")
        
        # Download to temp file
        print("📥 Downloading to temporary file...")
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
            for chunk in response.iter_content(chunk_size=8192):
                temp_file.write(chunk)
            temp_file_path = temp_file.name
        
        print(f"✅ Downloaded to: {temp_file_path}")
        print(f"File size: {os.path.getsize(temp_file_path)} bytes")
        
        # Load with pydub
        print("🎵 Loading with pydub...")
        audio = AudioSegment.from_file(temp_file_path)
        print(f"✅ Audio loaded: {len(audio)}ms duration, {audio.frame_rate}Hz")
        
        # Play audio
        print("🔊 Playing audio... (Press Ctrl+C to stop)")
        play(audio)
        
        # Clean up
        os.unlink(temp_file_path)
        print("✅ Playback completed and temp file cleaned up!")
        
        return True
        
    except KeyboardInterrupt:
        print("\n⏹️ Playback stopped by user")
        try:
            os.unlink(temp_file_path)
        except:
            pass
        return True
    except Exception as e:
        print(f"❌ Manual test failed: {e}")
        try:
            os.unlink(temp_file_path)
        except:
            pass
        return False

if __name__ == "__main__":
    # Test the S3AudioPlayer
    test_temp_file_streaming()
    
    print("\n" + "=" * 55)
    user_input = input("Run manual temp file test? (y/n): ")
    if user_input.lower() == 'y':
        success = test_manual_temp_download()
        if success:
            print("\n🎉 S3 audio streaming is working perfectly!")
        else:
            print("\n❌ There's still an issue with the temp file method.")