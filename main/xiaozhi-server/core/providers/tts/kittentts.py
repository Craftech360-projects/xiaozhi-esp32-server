import os
import asyncio
import threading
import numpy as np
import soundfile as sf
from core.providers.tts.base import TTSProviderBase
from core.utils.kittentts_model import KittenTTS
from config.logger import setup_logging

TAG = __name__
logger = setup_logging()

class TTSProvider(TTSProviderBase):
    def __init__(self, config, delete_audio_file):
        super().__init__(config, delete_audio_file)
        
        # KittenTTS configuration
        self.model_name = config.get("model_name", "KittenML/kitten-tts-nano-0.1")
        self.voice = config.get("voice", "expr-voice-5-m")
        self.speed = float(config.get("speed", 1.0))
        self.sample_rate = int(config.get("sample_rate", 24000))
        self.audio_file_type = config.get("format", "wav")
        
        # Available voices
        self.available_voices = [
            'expr-voice-2-m', 'expr-voice-2-f', 'expr-voice-3-m', 'expr-voice-3-f',
            'expr-voice-4-m', 'expr-voice-4-f', 'expr-voice-5-m', 'expr-voice-5-f'
        ]
        
        # Validate voice
        if self.voice not in self.available_voices:
            logger.bind(tag=TAG).warning(f"Voice '{self.voice}' not available. Using default 'expr-voice-5-m'")
            self.voice = "expr-voice-3-f"
        
        # Initialize KittenTTS model synchronously at startup
        self.model = None
        self._initialize_model()
        logger.bind(tag=TAG).info("KittenTTS provider ready for use")
    
    def _initialize_model(self):
        """Initialize the KittenTTS model"""
        try:
            # Check for required dependencies
            try:
                import onnxruntime
                import soundfile
                import phonemizer
                import huggingface_hub
            except ImportError as e:
                raise Exception(f"Missing KittenTTS dependency: {e}. Please run: python install_kittentts.py")
            
            self.model = KittenTTS(self.model_name)
            logger.bind(tag=TAG).info(f"KittenTTS model initialized successfully with voice: {self.voice}")
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"Failed to initialize KittenTTS model: {e}")
            raise Exception(f"KittenTTS initialization failed: {e}")
    

    
    async def text_to_speak(self, text, output_file):
        """Convert text to speech using KittenTTS"""
        try:
            if not self.model:
                raise Exception("KittenTTS model not initialized")
            
            # Log which voice is being used for debugging
            logger.bind(tag=TAG).info(f"🎭 KittenTTS generating audio with voice: {self.voice}, speed: {self.speed}, text: '{text[:50]}...'")
            
            # Generate audio using KittenTTS
            audio_data = self.model.generate(text, voice=self.voice, speed=self.speed)
            
            if output_file:
                # Save to file
                sf.write(output_file, audio_data, self.sample_rate)
                logger.bind(tag=TAG).debug(f"Audio saved to {output_file}")
            else:
                # Return audio bytes
                # Convert numpy array to wav bytes
                import io
                buffer = io.BytesIO()
                sf.write(buffer, audio_data, self.sample_rate, format='WAV')
                audio_bytes = buffer.getvalue()
                buffer.close()
                return audio_bytes
                
        except Exception as e:
            error_msg = f"KittenTTS synthesis failed: {e}"
            logger.bind(tag=TAG).error(error_msg)
            raise Exception(error_msg)