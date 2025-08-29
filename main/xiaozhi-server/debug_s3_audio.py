"""
Debug script for S3 Audio streaming issues
"""

import os
import requests
from dotenv import load_dotenv
from s3_audio_player import S3AudioPlayer

load_dotenv()

def test_s3_access():
    """Test S3 bucket access and URL generation"""
    
    player = S3AudioPlayer()
    
    # Test URL generation
    test_filename = "Baa Baa Black Sheep.mp3"
    url = player.generate_s3_url("music", "English", test_filename)
    print(f"Generated URL: {url}")
    
    # Test direct HTTP access
    print("\n🔍 Testing direct HTTP access...")
    try:
        response = requests.head(url, timeout=10)
        print(f"HTTP Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type', 'Unknown')}")
        print(f"Content-Length: {response.headers.get('Content-Length', 'Unknown')} bytes")
        
        if response.status_code == 200:
            print("✅ URL is accessible!")
        else:
            print(f"❌ URL returned status {response.status_code}")
            
    except Exception as e:
        print(f"❌ HTTP request failed: {e}")
    
    # Test simple public URL
    print("\n🔍 Testing simple public URL...")
    simple_url = f"https://cheeko-audio-files.s3.amazonaws.com/music/English/Baa%20Baa%20Black%20Sheep.mp3"
    try:
        response = requests.head(simple_url, timeout=10)
        print(f"Simple URL Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Simple public URL works!")
            
            # Try downloading a small chunk
            print("\n📥 Testing download...")
            response = requests.get(simple_url, stream=True, timeout=10)
            chunk = next(response.iter_content(chunk_size=1024))
            print(f"✅ Downloaded {len(chunk)} bytes successfully")
            
    except Exception as e:
        print(f"❌ Simple URL test failed: {e}")

def test_temp_file_playback():
    """Test playing audio from temporary file"""
    print("\n🎵 Testing temporary file playback...")
    
    try:
        import tempfile
        from pydub import AudioSegment
        from pydub.playback import play
        
        # Download to temp file
        url = "https://cheeko-audio-files.s3.amazonaws.com/music/English/Baa%20Baa%20Black%20Sheep.mp3"
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
            for chunk in response.iter_content(chunk_size=8192):
                temp_file.write(chunk)
            temp_file_path = temp_file.name
        
        print(f"✅ Downloaded to: {temp_file_path}")
        print(f"File size: {os.path.getsize(temp_file_path)} bytes")
        
        # Try to load with pydub
        audio = AudioSegment.from_file(temp_file_path)
        print(f"✅ Audio loaded: {len(audio)}ms duration")
        
        print("🎵 Playing audio... (press Ctrl+C to stop)")
        play(audio)
        
        # Clean up
        os.unlink(temp_file_path)
        print("✅ Playback completed successfully!")
        
    except KeyboardInterrupt:
        print("\n⏹️ Playback stopped by user")
        try:
            os.unlink(temp_file_path)
        except:
            pass
    except Exception as e:
        print(f"❌ Temp file playback failed: {e}")
        try:
            os.unlink(temp_file_path)
        except:
            pass

if __name__ == "__main__":
    print("🔧 S3 Audio Debug Tool")
    print("=" * 50)
    
    test_s3_access()
    
    print("\n" + "=" * 50)
    user_input = input("Test audio playback? (y/n): ")
    if user_input.lower() == 'y':
        test_temp_file_playback()