import asyncio
import time
import json
import traceback
from typing import Optional, List
from config.logger import setup_logging
from core.providers.asr.deepgram import ASRProvider as DeepgramASR
from core.providers.llm.gemini_realtime.gemini_realtime import LLMProvider as GeminiRealtime

TAG = __name__
logger = setup_logging()


class GeminiRealtimeHandler:
    """
    Hybrid handler that combines:
    - Deepgram ASR for speech-to-text
    - Gemini Real-time for LLM and TTS
    - Xiaozhi's existing connection management
    """

    def __init__(self, conn, deepgram_config: dict, gemini_config: dict):
        self.conn = conn
        self.deepgram_asr = DeepgramASR(deepgram_config, delete_audio_file=True)
        self.gemini_llm = GeminiRealtime(gemini_config)
        
        # Audio processing
        self.audio_buffer = []
        self.is_processing = False
        self.last_activity_time = time.time()
        
        # Tasks
        self.audio_sender_task = None
        self.audio_receiver_task = None
        
        logger.bind(tag=TAG).info("GeminiRealtimeHandler initialized")

    async def start(self):
        """Start the real-time processing"""
        try:
            # Connect to Gemini
            success = await self.gemini_llm.connect()
            if not success:
                logger.bind(tag=TAG).error("Failed to connect to Gemini")
                return False
            
            # Start audio processing tasks
            self.audio_receiver_task = asyncio.create_task(self._audio_receiver_loop())
            
            logger.bind(tag=TAG).info("Gemini real-time handler started")
            return True
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"Error starting handler: {e}")
            return False

    async def stop(self):
        """Stop the real-time processing"""
        try:
            # Cancel tasks
            if self.audio_receiver_task:
                self.audio_receiver_task.cancel()
            
            # Disconnect from Gemini
            await self.gemini_llm.disconnect()
            
            logger.bind(tag=TAG).info("Gemini real-time handler stopped")
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"Error stopping handler: {e}")

    async def process_audio_chunk(self, audio_data: bytes, has_voice: bool):
        """Process incoming audio chunk from ESP32"""
        try:
            self.last_activity_time = time.time()
            
            # Add to buffer
            self.audio_buffer.append(audio_data)
            
            # If voice detected and we have enough audio, process it
            if has_voice and len(self.audio_buffer) > 10:  # ~600ms of audio
                await self._process_speech()
            
            # Keep buffer size manageable
            if len(self.audio_buffer) > 50:  # ~3 seconds
                self.audio_buffer = self.audio_buffer[-30:]  # Keep last 1.8 seconds
                
        except Exception as e:
            logger.bind(tag=TAG).error(f"Error processing audio chunk: {e}")

    async def _process_speech(self):
        """Process accumulated speech using Deepgram ASR"""
        if self.is_processing:
            return
            
        try:
            self.is_processing = True
            
            # Get audio buffer
            audio_chunks = self.audio_buffer.copy()
            self.audio_buffer.clear()
            
            if len(audio_chunks) < 5:  # Too short
                return
            
            logger.bind(tag=TAG).info(f"Processing speech with {len(audio_chunks)} audio chunks")
            
            # Use Deepgram for ASR
            start_time = time.time()
            transcript, _ = await self.deepgram_asr.speech_to_text(
                audio_chunks, 
                session_id=self.conn.session_id,
                audio_format="opus"  # or "pcm" depending on your setup
            )
            
            asr_time = time.time() - start_time
            
            if transcript and transcript.strip():
                logger.bind(tag=TAG).info(f"ASR result ({asr_time:.2f}s): {transcript}")
                
                # Send to Gemini for LLM processing and TTS
                await self._handle_transcript(transcript)
            else:
                logger.bind(tag=TAG).debug("No transcript received from Deepgram")
                
        except Exception as e:
            logger.bind(tag=TAG).error(f"Error in speech processing: {e}")
            traceback.print_exc()
        finally:
            self.is_processing = False

    async def _handle_transcript(self, transcript: str):
        """Handle transcript from Deepgram and get Gemini response"""
        try:
            # Send transcript to Gemini
            success = await self.gemini_llm.send_text_message(transcript)
            if not success:
                logger.bind(tag=TAG).error("Failed to send transcript to Gemini")
                return
            
            logger.bind(tag=TAG).info(f"Sent to Gemini: {transcript}")
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"Error handling transcript: {e}")

    async def _audio_receiver_loop(self):
        """Continuously receive audio from Gemini and send to ESP32"""
        try:
            while True:
                # Get audio response from Gemini
                audio_data = await self.gemini_llm.get_audio_response()
                
                if audio_data:
                    # Send audio to ESP32 client
                    await self._send_audio_to_client(audio_data)
                
                await asyncio.sleep(0.01)  # Small delay to prevent busy loop
                
        except asyncio.CancelledError:
            logger.bind(tag=TAG).info("Audio receiver loop cancelled")
        except Exception as e:
            logger.bind(tag=TAG).error(f"Error in audio receiver loop: {e}")

    async def _send_audio_to_client(self, audio_data: bytes):
        """Send audio data to ESP32 client"""
        try:
            if hasattr(self.conn, 'websocket') and self.conn.websocket:
                # Send as binary WebSocket message
                await self.conn.websocket.send(audio_data)
                logger.bind(tag=TAG).debug(f"Sent {len(audio_data)} bytes to client")
            else:
                logger.bind(tag=TAG).warning("No WebSocket connection available")
                
        except Exception as e:
            logger.bind(tag=TAG).error(f"Error sending audio to client: {e}")

    async def send_text_message(self, text: str):
        """Send text message to Gemini (for manual input)"""
        try:
            success = await self.gemini_llm.send_text_message(text)
            if success:
                logger.bind(tag=TAG).info(f"Manual text sent: {text}")
            return success
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"Error sending text message: {e}")
            return False

    def get_status(self) -> dict:
        """Get handler status"""
        return {
            "connected": self.gemini_llm.is_connected,
            "processing": self.is_processing,
            "buffer_size": len(self.audio_buffer),
            "last_activity": time.time() - self.last_activity_time
        }