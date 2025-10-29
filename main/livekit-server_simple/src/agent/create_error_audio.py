#!/usr/bin/env python3
"""
Script to create a simple error message audio file for fallback scenarios
This creates a basic audio file that can be used when TTS fails
"""

import os
import pathlib
import logging

logger = logging.getLogger(__name__)

def create_error_audio():
    """Create a simple error audio file using text-to-speech"""
    try:
        # Try to use system TTS to create a basic error message
        error_message = "I'm having technical difficulties. Please try again."
        audio_path = os.path.join(pathlib.Path(__file__).parent.absolute(), "error_message.ogg")
        
        # Check if file already exists
        if os.path.exists(audio_path):
            logger.info(f"Error audio file already exists: {audio_path}")
            return audio_path
        
        # Try different methods to create audio file
        methods = [
            _create_with_pyttsx3,
            _create_with_gtts,
            _create_silence_file
        ]
        
        for method in methods:
            try:
                if method(error_message, audio_path):
                    logger.info(f"Created error audio file: {audio_path}")
                    return audio_path
            except Exception as e:
                logger.warning(f"Method {method.__name__} failed: {e}")
                continue
        
        logger.warning("Could not create error audio file with any method")
        return None
        
    except Exception as e:
        logger.error(f"Failed to create error audio: {e}")
        return None

def _create_with_pyttsx3(message: str, output_path: str) -> bool:
    """Try to create audio using pyttsx3"""
    try:
        import pyttsx3
        import tempfile
        import subprocess
        
        engine = pyttsx3.init()
        
        # Create temporary wav file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_wav:
            temp_wav_path = temp_wav.name
        
        engine.save_to_file(message, temp_wav_path)
        engine.runAndWait()
        
        # Convert to ogg using ffmpeg if available
        try:
            subprocess.run([
                'ffmpeg', '-i', temp_wav_path, '-c:a', 'libvorbis', 
                '-q:a', '4', output_path, '-y'
            ], check=True, capture_output=True)
            os.unlink(temp_wav_path)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            # ffmpeg not available, just rename wav to ogg
            os.rename(temp_wav_path, output_path.replace('.ogg', '.wav'))
            return True
            
    except ImportError:
        return False

def _create_with_gtts(message: str, output_path: str) -> bool:
    """Try to create audio using Google Text-to-Speech"""
    try:
        from gtts import gTTS
        import tempfile
        import subprocess
        
        tts = gTTS(text=message, lang='en', slow=False)
        
        # Create temporary mp3 file
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_mp3:
            temp_mp3_path = temp_mp3.name
        
        tts.save(temp_mp3_path)
        
        # Convert to ogg using ffmpeg if available
        try:
            subprocess.run([
                'ffmpeg', '-i', temp_mp3_path, '-c:a', 'libvorbis',
                '-q:a', '4', output_path, '-y'
            ], check=True, capture_output=True)
            os.unlink(temp_mp3_path)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            # ffmpeg not available, just rename mp3 to ogg
            os.rename(temp_mp3_path, output_path.replace('.ogg', '.mp3'))
            return True
            
    except ImportError:
        return False

def _create_silence_file(message: str, output_path: str) -> bool:
    """Create a silent audio file as last resort"""
    try:
        import subprocess
        
        # Create 3 seconds of silence
        subprocess.run([
            'ffmpeg', '-f', 'lavfi', '-i', 'anullsrc=channel_layout=stereo:sample_rate=48000',
            '-t', '3', '-c:a', 'libvorbis', output_path, '-y'
        ], check=True, capture_output=True)
        
        logger.info("Created silent audio file as fallback")
        return True
        
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    create_error_audio()