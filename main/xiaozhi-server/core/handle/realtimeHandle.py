"""
Handler for OpenAI Realtime API integration
Manages bidirectional audio streaming between ESP32 and OpenAI
"""

import asyncio
import json
import queue
import threading
import time
from typing import Optional
from config.logger import setup_logging
from core.providers.llm.openai_realtime import OpenAIRealtimeProvider

TAG = __name__
logger = setup_logging()


class RealtimeHandler:
    """
    Handles real-time audio streaming between ESP32 device and OpenAI Realtime API
    Bypasses traditional ASR->LLM->TTS pipeline for lower latency
    """
    
    def __init__(self, config: dict, websocket, device_id: str, session_id: str = None, connection=None):
        self.config = config
        self.websocket = websocket
        self.device_id = device_id
        self.session_id = session_id or f"realtime_{int(time.time())}"
        self.connection = connection  # Reference to ConnectionHandler for state management
        
        # Get OpenAI configuration
        openai_config = config.get("openai_realtime", {})
        self.api_key = openai_config.get("api_key")
        self.model = openai_config.get("model", "gpt-4o-realtime-preview")
        self.enabled = openai_config.get("enabled", False)
        
        # Initialize provider
        self.provider = None
        if self.enabled and self.api_key:
            self.provider = OpenAIRealtimeProvider(
                api_key=self.api_key,
                model=self.model
            )
        
        # Audio processing state
        self.is_active = False
        self.audio_thread = None
        self.stop_event = threading.Event()
        self.event_loop = None  # Store reference to main event loop
        self.is_speaking = False  # Track if we're currently sending audio
        self.last_audio_time = None  # Track last audio packet time
        self.audio_timeout = 2.0  # Seconds to wait before considering audio stream ended
        
        logger.bind(tag=TAG).info(
            f"Realtime handler initialized for device {device_id}, enabled: {self.enabled}"
        )
    
    async def start(self):
        """Start the Realtime API connection and audio streaming"""
        if not self.provider:
            logger.bind(tag=TAG).warning("Realtime API not configured or disabled")
            return False
        
        try:
            # Store reference to current event loop
            self.event_loop = asyncio.get_event_loop()
            
            # Start the provider's async loop
            self.provider.start_async_loop()
            
            # Wait for connection
            await asyncio.sleep(2)  # Give time for connection
            
            if self.provider.connected:
                self.is_active = True
                
                # Start audio processing thread
                self.audio_thread = threading.Thread(target=self._process_audio)
                self.audio_thread.start()
                
                logger.bind(tag=TAG).info("Realtime API handler started successfully")
                return True
            else:
                logger.bind(tag=TAG).error("Failed to connect to Realtime API")
                return False
                
        except Exception as e:
            logger.bind(tag=TAG).error(f"Error starting Realtime handler: {e}")
            return False
    
    async def handle_audio_input(self, audio_data: bytes):
        """
        Handle incoming audio from ESP32
        
        Args:
            audio_data: Opus encoded audio from ESP32
        """
        if not self.is_active or not self.provider:
            return
        
        try:
            # Check if we're not currently speaking (ready to receive input)
            if not self.connection or not self.connection.client_is_speaking:
                # Send audio to OpenAI Realtime API
                self.provider.send_audio(audio_data)
                logger.bind(tag=TAG).debug(f"Sent audio chunk to OpenAI: {len(audio_data)} bytes")
                
                # Track if we've been receiving audio
                if not hasattr(self, 'receiving_audio'):
                    self.receiving_audio = False
                    self.last_audio_received = None
                
                # If this is empty audio (silence detected), commit buffer
                if len(audio_data) == 0 or audio_data == b'':
                    if self.receiving_audio:
                        logger.bind(tag=TAG).info("Silence detected - committing audio buffer")
                        self.provider.commit_and_respond()
                        self.receiving_audio = False
                else:
                    self.receiving_audio = True
                    self.last_audio_received = time.time()
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"Error handling audio input: {e}")
    
    def _process_audio(self):
        """Background thread to process audio output from OpenAI"""
        while not self.stop_event.is_set():
            try:
                # Check for audio from OpenAI (with timeout)
                audio_data = self.provider.audio_output_queue.get(timeout=0.1)
                
                # Handle end of stream marker
                if audio_data is None:
                    if self.is_speaking:
                        # Send TTS stop message
                        stop_future = asyncio.run_coroutine_threadsafe(
                            self._send_tts_message("stop"),
                            self.event_loop
                        )
                        try:
                            stop_future.result(timeout=1.0)
                            self.is_speaking = False
                            self.last_audio_time = None
                            # Clear server speaking status to allow recording
                            if self.connection:
                                self.connection.clearSpeakStatus()
                            logger.bind(tag=TAG).info("Audio stream completed - sent TTS stop and cleared speaking status")
                        except asyncio.TimeoutError:
                            logger.bind(tag=TAG).warning("TTS stop message timed out")
                    continue
                
                if audio_data and self.event_loop:
                    # Send TTS start message on first audio chunk
                    if not self.is_speaking:
                        start_future = asyncio.run_coroutine_threadsafe(
                            self._send_tts_message("start"),
                            self.event_loop
                        )
                        try:
                            start_future.result(timeout=1.0)
                            self.is_speaking = True
                            # Set server speaking status to pause recording
                            if self.connection:
                                self.connection.client_is_speaking = True
                                logger.bind(tag=TAG).debug("Set client_is_speaking = True")
                        except asyncio.TimeoutError:
                            logger.bind(tag=TAG).warning("TTS start message timed out")
                    
                    # Update last audio time
                    self.last_audio_time = time.time()
                    
                    # Send audio back to ESP32 using stored event loop
                    future = asyncio.run_coroutine_threadsafe(
                        self._send_audio_to_device(audio_data),
                        self.event_loop
                    )
                    # Wait for completion to avoid the "never awaited" warning
                    try:
                        future.result(timeout=1.0)
                    except asyncio.TimeoutError:
                        logger.bind(tag=TAG).warning("Audio send operation timed out")
                
                # Check for audio timeout (stream ended)
                elif self.is_speaking and self.last_audio_time:
                    if time.time() - self.last_audio_time > self.audio_timeout:
                        # Send TTS stop message
                        stop_future = asyncio.run_coroutine_threadsafe(
                            self._send_tts_message("stop"),
                            self.event_loop
                        )
                        try:
                            stop_future.result(timeout=1.0)
                            self.is_speaking = False
                            self.last_audio_time = None
                            # Clear server speaking status to allow recording
                            if self.connection:
                                self.connection.clearSpeakStatus()
                            logger.bind(tag=TAG).info("Audio stream ended - sent TTS stop and cleared speaking status")
                        except asyncio.TimeoutError:
                            logger.bind(tag=TAG).warning("TTS stop message timed out")
                    
            except queue.Empty:
                continue
            except Exception as e:
                logger.bind(tag=TAG).error(f"Error processing audio output: {e}")
    
    async def _send_audio_to_device(self, audio_data: bytes):
        """
        Send audio data back to ESP32 device
        
        Args:
            audio_data: Opus encoded audio for ESP32
        """
        try:
            # Check if audio data is too large for UDP transmission
            max_udp_payload = 1400  # Safe UDP payload size (typical MTU is 1500)
            
            if len(audio_data) <= max_udp_payload:
                # Small packet, send directly like traditional pipeline
                await self.websocket.send(audio_data)
                logger.bind(tag=TAG).debug(f"Sent audio packet: {len(audio_data)} bytes")
            else:
                # Large chunk from Realtime API - split into smaller Opus-compatible packets
                # This shouldn't happen often, but handle it gracefully
                logger.bind(tag=TAG).warning(f"Large audio chunk received: {len(audio_data)} bytes, splitting")
                
                # Split into smaller chunks (simulate multiple Opus packets)
                packet_size = 960  # Typical Opus packet size for 60ms at 16kHz
                for i in range(0, len(audio_data), packet_size):
                    packet = audio_data[i:i + packet_size]
                    await self.websocket.send(packet)
                    # Add timing delay similar to traditional pipeline (60ms frames)
                    await asyncio.sleep(0.06)
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"Error sending audio to device: {e}")
    
    async def _send_tts_message(self, state, text=None):
        """Send TTS status message to match traditional pipeline"""
        try:
            message = {"type": "tts", "state": state, "session_id": self.session_id}
            if text is not None:
                message["text"] = text
            
            await self.websocket.send(json.dumps(message))
            logger.bind(tag=TAG).debug(f"Sent TTS message: {state}")
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"Error sending TTS message: {e}")
    
    async def handle_text_input(self, text: str):
        """
        Handle text input (fallback mode or text commands)
        
        Args:
            text: User text input
        """
        if not self.is_active or not self.provider:
            return
        
        try:
            # Send text to OpenAI Realtime API
            await self.provider._send_text_message(text)
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"Error handling text input: {e}")
    
    async def stop(self):
        """Stop the Realtime API handler and clean up"""
        self.is_active = False
        self.stop_event.set()
        
        # Wait for audio thread to finish
        if self.audio_thread:
            self.audio_thread.join(timeout=2)
        
        # Stop the provider
        if self.provider:
            self.provider.stop()
        
        logger.bind(tag=TAG).info("Realtime handler stopped")
    
    def is_enabled(self) -> bool:
        """Check if Realtime API is enabled and configured"""
        return self.enabled and self.api_key is not None