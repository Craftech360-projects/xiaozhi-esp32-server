"""
True Streaming S3 Audio Player for Xiaozhi Server
Streams audio directly from S3 URLs without downloading
"""

import os
import json
import boto3
import urllib.parse
from pathlib import Path
from botocore.exceptions import ClientError
import logging
import threading
import time

logger = logging.getLogger(__name__)

class StreamingS3AudioPlayer:
    def __init__(self, base_path=".", config_file="config.yaml"):
        self.base_path = Path(base_path)
        self.music_path = self.base_path / "music"
        self.stories_path = self.base_path / "stories"
        
        # Load AWS configuration
        self.bucket_name = "cheeko-audio-files"
        self.s3_client = None
        self._init_s3_client()
        
        # Audio player backends (try multiple options)
        self.player = None
        self.current_stream = None
        self._init_audio_backend()
    
    def _init_s3_client(self):
        """Initialize S3 client with credentials from environment variables"""
        try:
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
    
    def _init_audio_backend(self):
        """Initialize audio backend for streaming"""
        self.backend = None
        
        # Try VLC first (best for streaming)
        try:
            import vlc
            self.vlc_instance = vlc.Instance()
            self.vlc_player = self.vlc_instance.media_player_new()
            self.backend = "vlc"
            logger.info("VLC backend initialized for streaming")
            return
        except ImportError:
            logger.warning("VLC not available, trying pygame")
        
        # Try pygame as fallback
        try:
            import pygame
            pygame.mixer.init()
            self.backend = "pygame"
            logger.info("Pygame backend initialized")
            return
        except ImportError:
            logger.warning("Pygame not available")
        
        # Try Windows Media Player as last resort
        if os.name == 'nt':
            try:
                import winsound
                self.backend = "winsound"
                logger.info("Windows sound backend available")
                return
            except ImportError:
                pass
        
        logger.error("No suitable audio backend found for streaming")
    
    def generate_streaming_url(self, category_type, category, filename):
        """Generate streaming URL for audio file"""
        if not self.s3_client:
            return None
        
        try:
            # Use original filename for S3 key
            s3_key = f"{category_type}/{category}/{filename}"
            
            # Generate presigned URL with longer expiry for streaming
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': s3_key},
                ExpiresIn=7200  # 2 hours for streaming
            )
            logger.info(f"Generated streaming URL for {s3_key}")
            return url
            
        except ClientError as e:
            logger.error(f"Error generating streaming URL: {e}")
            return None
    
    def stream_audio_vlc(self, url):
        """Stream audio using VLC backend"""
        try:
            import vlc
            
            # Stop any current playback
            if hasattr(self, 'vlc_player'):
                self.vlc_player.stop()
            
            # Create media from URL
            media = self.vlc_instance.media_new(url)
            self.vlc_player.set_media(media)
            
            # Start streaming
            self.vlc_player.play()
            
            # Wait for playback to start
            time.sleep(0.5)
            
            # Check if playing
            state = self.vlc_player.get_state()
            if state == vlc.State.Playing:
                logger.info("VLC streaming started successfully")
                return True
            else:
                logger.error(f"VLC failed to start streaming, state: {state}")
                return False
                
        except Exception as e:
            logger.error(f"VLC streaming error: {e}")
            return False
    
    def stream_audio_pygame(self, url):
        """Stream audio using pygame backend"""
        try:
            import pygame
            import requests
            import io
            
            # Stop any current playback
            pygame.mixer.music.stop()
            
            # Stream the audio data
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            # Load audio data into pygame
            audio_data = io.BytesIO()
            for chunk in response.iter_content(chunk_size=8192):
                audio_data.write(chunk)
            
            audio_data.seek(0)
            pygame.mixer.music.load(audio_data)
            pygame.mixer.music.play()
            
            logger.info("Pygame streaming started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Pygame streaming error: {e}")
            return False
    
    def stream_audio_system(self, url):
        """Stream audio using system player (Windows)"""
        try:
            import subprocess
            import platform
            
            system = platform.system()
            
            if system == "Windows":
                # Use Windows Media Player
                subprocess.Popen([
                    "powershell", "-c", 
                    f"Add-Type -AssemblyName presentationCore; "
                    f"$mediaPlayer = New-Object system.windows.media.mediaplayer; "
                    f"$mediaPlayer.open('{url}'); "
                    f"$mediaPlayer.Play()"
                ], shell=True)
                
            elif system == "Darwin":  # macOS
                subprocess.Popen(["afplay", url])
                
            elif system == "Linux":
                # Try different players
                players = ["mpv", "vlc", "mplayer", "ffplay"]
                for player in players:
                    try:
                        subprocess.Popen([player, url])
                        break
                    except FileNotFoundError:
                        continue
            
            logger.info("System player streaming started")
            return True
            
        except Exception as e:
            logger.error(f"System player streaming error: {e}")
            return False
    
    def stream_audio(self, url):
        """Stream audio using the best available backend"""
        if not url:
            return False
        
        logger.info(f"Attempting to stream from: {url[:100]}...")
        
        # Try backends in order of preference
        if self.backend == "vlc":
            if self.stream_audio_vlc(url):
                return True
        
        if self.backend == "pygame":
            if self.stream_audio_pygame(url):
                return True
        
        # Fallback to system player
        if self.stream_audio_system(url):
            return True
        
        logger.error("All streaming backends failed")
        return False
    
    def stop_playback(self):
        """Stop current audio playback"""
        try:
            if self.backend == "vlc" and hasattr(self, 'vlc_player'):
                self.vlc_player.stop()
            elif self.backend == "pygame":
                import pygame
                pygame.mixer.music.stop()
            
            logger.info("Playback stopped")
        except Exception as e:
            logger.error(f"Error stopping playback: {e}")
    
    def play_music(self, language, song_query):
        """Stream music by language and song name/alternative"""
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
        
        # Generate streaming URL and play
        streaming_url = self.generate_streaming_url("music", language, song_info['filename'])
        if not streaming_url:
            return f"Failed to generate streaming URL for: {song_info['romanized']}"
        
        success = self.stream_audio(streaming_url)
        
        if success:
            return f"Streaming: {song_info['romanized']}"
        else:
            return f"Failed to stream: {song_info['romanized']}"
    
    def play_story(self, category, story_query):
        """Stream story by category and story name/alternative"""
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
        
        # Generate streaming URL and play
        streaming_url = self.generate_streaming_url("stories", category, story_info['filename'])
        if not streaming_url:
            return f"Failed to generate streaming URL for: {story_info['romanized']}"
        
        success = self.stream_audio(streaming_url)
        
        if success:
            return f"Streaming story: {story_info['romanized']}"
        else:
            return f"Failed to stream story: {story_info['romanized']}"
    
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
    
    def get_playback_status(self):
        """Get current playback status"""
        try:
            if self.backend == "vlc" and hasattr(self, 'vlc_player'):
                import vlc
                state = self.vlc_player.get_state()
                return {
                    'backend': 'vlc',
                    'playing': state == vlc.State.Playing,
                    'state': str(state)
                }
            elif self.backend == "pygame":
                import pygame
                return {
                    'backend': 'pygame',
                    'playing': pygame.mixer.music.get_busy(),
                    'state': 'playing' if pygame.mixer.music.get_busy() else 'stopped'
                }
        except Exception as e:
            logger.error(f"Error getting playback status: {e}")
        
        return {'backend': self.backend, 'playing': False, 'state': 'unknown'}


# Example usage
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    # Initialize streaming player
    player = StreamingS3AudioPlayer()
    
    print(f"Audio backend: {player.backend}")
    print("Available music languages:", player.list_available_music())
    print("Available story categories:", player.list_available_stories())
    
    # Test streaming (uncomment to test)
    # result = player.play_music("English", "baa baa black sheep")
    # print(result)
    
    # Check status
    # status = player.get_playback_status()
    # print(f"Playback status: {status}")