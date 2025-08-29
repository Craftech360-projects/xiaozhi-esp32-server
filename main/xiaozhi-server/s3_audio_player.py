"""
S3 Audio Player for Xiaozhi Server
Streams audio files from AWS S3 bucket while keeping metadata local
"""

import os
import json
import boto3
import requests
import tempfile
import urllib.parse
from pathlib import Path
from pydub import AudioSegment
from pydub.playback import play
from botocore.exceptions import ClientError, NoCredentialsError
import logging

logger = logging.getLogger(__name__)

class S3AudioPlayer:
    def __init__(self, base_path=".", config_file="config.yaml"):
        self.base_path = Path(base_path)
        self.music_path = self.base_path / "music"
        self.stories_path = self.base_path / "stories"
        
        # Load AWS configuration
        self.bucket_name = "cheeko-audio-files"
        self.s3_client = None
        self._init_s3_client()
    
    def _init_s3_client(self):
        """Initialize S3 client with credentials from environment variables"""
        try:
            # Get credentials from environment variables (SECURE METHOD)
            aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
            aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
            aws_region = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
            
            if not aws_access_key or not aws_secret_key:
                logger.warning("AWS credentials not found in environment variables")
                return
            
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key,
                region_name=aws_region
            )
            logger.info("S3 client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {e}")
            self.s3_client = None
    
    def generate_s3_url(self, category_type, category, filename):
        """Generate S3 URL for audio file"""
        import urllib.parse
        
        # URL encode the filename to handle spaces and special characters
        encoded_filename = urllib.parse.quote(filename)
        s3_key = f"{category_type}/{category}/{encoded_filename}"
        
        # Try public URL first (simpler, works better with pydub on Windows)
        public_url = f"https://{self.bucket_name}.s3.amazonaws.com/{s3_key}"
        
        # Test if public URL is accessible
        try:
            import requests
            response = requests.head(public_url, timeout=5)
            if response.status_code == 200:
                logger.info(f"Using public URL: {public_url}")
                return public_url
        except:
            pass
        
        # Fallback to presigned URL if public access fails
        if self.s3_client:
            try:
                # Use original filename (not encoded) for S3 key in presigned URL
                original_s3_key = f"{category_type}/{category}/{filename}"
                url = self.s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': self.bucket_name, 'Key': original_s3_key},
                    ExpiresIn=3600  # 1 hour
                )
                logger.info(f"Using presigned URL")
                return url
            except ClientError as e:
                logger.error(f"Error generating presigned URL: {e}")
        
        # Final fallback
        return public_url
    
    def play_music(self, language, song_query):
        """Play music by language and song name/alternative"""
        metadata_file = self.music_path / language / "metadata.json"
        
        if not metadata_file.exists():
            return f"Language {language} not found"
        
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
        except Exception as e:
            logger.error(f"Error reading metadata: {e}")
            return f"Error reading music metadata for {language}"
        
        # Find song by name or alternative
        song_info = self._find_content(metadata, song_query)
        if not song_info:
            return f"Song '{song_query}' not found in {language}"
        
        # Generate S3 URL and play
        s3_url = self.generate_s3_url("music", language, song_info['filename'])
        success = self._play_audio_from_url(s3_url)
        
        if success:
            return f"Playing: {song_info['romanized']}"
        else:
            return f"Failed to play: {song_info['romanized']}"
    
    def play_story(self, category, story_query):
        """Play story by category and story name/alternative"""
        metadata_file = self.stories_path / category / "metadata.json"
        
        if not metadata_file.exists():
            return f"Story category {category} not found"
        
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
        except Exception as e:
            logger.error(f"Error reading metadata: {e}")
            return f"Error reading story metadata for {category}"
        
        story_info = self._find_content(metadata, story_query)
        if not story_info:
            return f"Story '{story_query}' not found in {category}"
        
        # Generate S3 URL and play
        s3_url = self.generate_s3_url("stories", category, story_info['filename'])
        success = self._play_audio_from_url(s3_url)
        
        if success:
            return f"Playing story: {story_info['romanized']}"
        else:
            return f"Failed to play story: {story_info['romanized']}"
    
    def _find_content(self, metadata, query):
        """Find content by name or alternatives using fuzzy matching"""
        query_lower = query.lower().strip()
        
        # First pass: exact matches
        for title, info in metadata.items():
            if query_lower == title.lower():
                return info
            if query_lower == info['romanized'].lower():
                return info
            for alt in info.get('alternatives', []):
                if query_lower == alt.lower():
                    return info
        
        # Second pass: partial matches
        for title, info in metadata.items():
            if query_lower in title.lower():
                return info
            if query_lower in info['romanized'].lower():
                return info
            for alt in info.get('alternatives', []):
                if query_lower in alt.lower():
                    return info
        
        return None
    
    def _play_audio_from_url(self, url):
        """Play audio from S3 URL using requests + pydub"""
        import requests
        import tempfile
        import os
        
        try:
            logger.info(f"Attempting to stream audio from: {url[:100]}...")
            
            # Download audio content to temporary file
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            # Create temporary file with proper extension
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
                for chunk in response.iter_content(chunk_size=8192):
                    temp_file.write(chunk)
                temp_file_path = temp_file.name
            
            # Play from temporary file
            audio = AudioSegment.from_file(temp_file_path)
            play(audio)
            
            # Clean up temporary file
            os.unlink(temp_file_path)
            
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error downloading audio: {e}")
            return False
        except Exception as e:
            logger.error(f"Error playing audio: {e}")
            # Clean up temp file if it exists
            try:
                if 'temp_file_path' in locals():
                    os.unlink(temp_file_path)
            except:
                pass
            return False
    
    def list_available_music(self):
        """List all available music languages"""
        languages = []
        if self.music_path.exists():
            for lang_dir in self.music_path.iterdir():
                if lang_dir.is_dir() and (lang_dir / "metadata.json").exists():
                    languages.append(lang_dir.name)
        return languages
    
    def list_available_stories(self):
        """List all available story categories"""
        categories = []
        if self.stories_path.exists():
            for cat_dir in self.stories_path.iterdir():
                if cat_dir.is_dir() and (cat_dir / "metadata.json").exists():
                    categories.append(cat_dir.name)
        return categories
    
    def get_songs_in_language(self, language):
        """Get all songs available in a specific language"""
        metadata_file = self.music_path / language / "metadata.json"
        if not metadata_file.exists():
            return []
        
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            return list(metadata.keys())
        except Exception as e:
            logger.error(f"Error reading metadata for {language}: {e}")
            return []
    
    def get_stories_in_category(self, category):
        """Get all stories available in a specific category"""
        metadata_file = self.stories_path / category / "metadata.json"
        if not metadata_file.exists():
            return []
        
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            return list(metadata.keys())
        except Exception as e:
            logger.error(f"Error reading metadata for {category}: {e}")
            return []


# Example usage and testing
if __name__ == "__main__":
    # Initialize player
    player = S3AudioPlayer()
    
    # Test listing available content
    print("Available music languages:", player.list_available_music())
    print("Available story categories:", player.list_available_stories())
    
    # Test playing music (uncomment to test)
    # result = player.play_music("Hindi", "bandar mama")
    # print(result)
    
    # Test playing story (uncomment to test)
    # result = player.play_story("Fantasy", "cat portrait")
    # print(result)