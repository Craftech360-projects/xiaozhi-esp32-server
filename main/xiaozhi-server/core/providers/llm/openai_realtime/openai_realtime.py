"""
OpenAI Realtime API Provider
Implements GPT-4o Realtime API for low-latency speech-to-speech conversations
"""

import json
import asyncio
import base64
import struct
import threading
import queue
from typing import Optional, Dict, Any, Generator, List
import websockets
import numpy as np
from scipy import signal
from config.logger import setup_logging
from core.providers.llm.base import LLMProviderBase
from core.providers.asr.base import ASRProviderBase
from core.utils.opus_encoder_utils import OpusEncoderUtils

TAG = __name__
logger = setup_logging()


class OpenAIRealtimeProvider(LLMProviderBase):
    """
    OpenAI Realtime API provider for direct speech-to-speech conversations.
    This provider bypasses traditional ASR->LLM->TTS pipeline for lower latency.
    """
    
    def __init__(self, config=None, api_key=None, model=None, **kwargs):
        # Handle both direct parameters and config dict
        if config:
            self.api_key = config.get("api_key", api_key)
            self.model = config.get("model", model or "gpt-4o-realtime-preview")
            self.voice = config.get("voice", "alloy")
        else:
            self.api_key = api_key
            self.model = model or "gpt-4o-realtime-preview"
            self.voice = "alloy"
        self.base_url = "wss://api.openai.com/v1/realtime"
        
        # Audio configuration
        self.input_sample_rate = 16000  # ESP32 sends 16kHz
        self.output_sample_rate = 24000  # OpenAI expects 24kHz
        
        # Initialize Opus encoder for response audio
        self.opus_encoder = OpusEncoderUtils(
            sample_rate=16000,  # Output to ESP32 at 16kHz
            channels=1,         # Mono
            frame_size_ms=60    # 60ms frames
        )
        
        # Connection state
        self.ws = None
        self.connected = False
        self.session_id = None
        
        # Audio queues
        self.audio_input_queue = queue.Queue()
        self.audio_output_queue = queue.Queue()
        
        # Response tracking
        self.current_response_id = None
        self.response_audio_buffer = bytearray()
        
        # Event loop for async operations
        self.loop = None
        self.ws_thread = None
        
        logger.bind(tag=TAG).info(f"Initialized OpenAI Realtime provider with model: {model}")
    
    async def connect(self):
        """Establish WebSocket connection to OpenAI Realtime API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "OpenAI-Beta": "realtime=v1"
            }
            
            url = f"{self.base_url}?model={self.model}"
            # Fix: Use additional_headers instead of extra_headers for newer websockets versions
            try:
                self.ws = await websockets.connect(url, additional_headers=headers)
            except TypeError:
                # Fallback for older websockets versions
                self.ws = await websockets.connect(url, extra_headers=headers)
            
            self.connected = True
            
            logger.bind(tag=TAG).info("Connected to OpenAI Realtime API")
            
            # Start listening for messages
            await self._listen_loop()
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"Failed to connect to OpenAI Realtime API: {e}")
            self.connected = False
            raise
    
    async def _listen_loop(self):
        """Listen for messages from OpenAI WebSocket"""
        try:
            async for message in self.ws:
                await self._handle_message(json.loads(message))
        except websockets.exceptions.ConnectionClosed:
            logger.bind(tag=TAG).warning("OpenAI Realtime WebSocket connection closed")
            self.connected = False
        except Exception as e:
            logger.bind(tag=TAG).error(f"Error in listen loop: {e}")
            self.connected = False
    
    async def _handle_message(self, message: Dict[str, Any]):
        """Handle incoming messages from OpenAI"""
        event_type = message.get("type")
        
        if event_type == "session.created":
            self.session_id = message.get("session", {}).get("id")
            logger.bind(tag=TAG).info(f"Session created: {self.session_id}")
            
            # Configure session for optimal settings
            await self._configure_session()
            
        elif event_type == "input_audio_buffer.speech_started":
            # User started speaking
            logger.bind(tag=TAG).info("🎤 User speech detected - started recording")
            
        elif event_type == "input_audio_buffer.speech_stopped":
            # User stopped speaking
            logger.bind(tag=TAG).info("🔇 User speech stopped - processing audio")
            
        elif event_type == "conversation.item.input_audio_transcription.completed":
            # Input audio transcription completed (if enabled)
            transcript = message.get("transcript", "")
            if transcript:
                logger.bind(tag=TAG).info(f"🗣️  User said: {transcript}")
            
        elif event_type == "response.audio.delta":
            # Audio chunk received - buffer chunks for proper Opus encoding
            audio_data = base64.b64decode(message.get("delta", ""))
            logger.bind(tag=TAG).info(f"🎵 Received audio delta: {len(audio_data)} bytes")
            
            if audio_data:
                self.response_audio_buffer.extend(audio_data)
                logger.bind(tag=TAG).info(f"🔊 Audio buffer size: {len(self.response_audio_buffer)} bytes")
                
                # Check if we have enough data for Opus encoding (60ms frames to match client expectations)
                min_samples = 1440  # 60ms at 24kHz (24000 * 0.06 = 1440 samples)
                if len(self.response_audio_buffer) >= min_samples * 2:  # * 2 for 16-bit samples
                    # Extract a chunk for encoding
                    chunk_size = min_samples * 2
                    chunk_data = bytes(self.response_audio_buffer[:chunk_size])
                    self.response_audio_buffer = self.response_audio_buffer[chunk_size:]
                    logger.bind(tag=TAG).info(f"📦 Processing audio chunk: {len(chunk_data)} bytes")
                    
                    # Convert PCM16 24kHz chunk to Opus packets for ESP32
                    opus_packets = self._convert_pcm_to_opus_packets(chunk_data)
                    if opus_packets:
                        # Send each packet individually for proper streaming
                        for packet in opus_packets:
                            logger.bind(tag=TAG).info(f"🎧 Queuing Opus packet: {len(packet)} bytes")
                            self.audio_output_queue.put(packet)
                    else:
                        logger.bind(tag=TAG).warning("⚠️ No Opus packets generated from PCM data")
            
        elif event_type == "response.audio.done":
            # Audio response complete - send any remaining buffered data
            if self.response_audio_buffer:
                # Process any leftover audio in buffer with end_of_stream=True
                final_packets = self._convert_pcm_to_opus_final_packets(self.response_audio_buffer)
                if final_packets:
                    for packet in final_packets:
                        self.audio_output_queue.put(packet)
                self.response_audio_buffer = bytearray()
            
            # Reset encoder state for next conversation
            self.opus_encoder.reset_state()
            
            # Signal end of audio stream by putting a None marker
            self.audio_output_queue.put(None)
            
        elif event_type == "response.text.delta":
            # Text transcript of response (for logging)
            text = message.get("delta", "")
            if text:
                if not hasattr(self, 'current_response_text'):
                    self.current_response_text = ""
                self.current_response_text += text
                logger.bind(tag=TAG).debug(f"Response text delta: {text}")
        
        elif event_type == "response.text.done":
            # Complete text response received - log it
            if hasattr(self, 'current_response_text') and self.current_response_text:
                logger.bind(tag=TAG).info(f"🤖 LLM Response: {self.current_response_text}")
                self.current_response_text = ""
            
        elif event_type == "error":
            error = message.get("error", {})
            logger.bind(tag=TAG).error(f"OpenAI error: {error}")
    
    async def _configure_session(self):
        """Configure the session with optimal settings"""
        config = {
            "type": "session.update",
            "session": {
                "modalities": ["text", "audio"],
                "instructions": "You are Cheeko, a friendly, curious, and playful AI friend for children aged 4+. You talk in short, clear, and fun sentences. Always end with a fun follow-up question and keep the child talking and smiling!",
                "voice": self.voice,  # Use configured voice
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16",
                "input_audio_transcription": {
                    "model": "whisper-1"  # Enable input transcription for logging
                },
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.5,
                    "prefix_padding_ms": 300,
                    "silence_duration_ms": 500
                },
                "temperature": 0.8,
                "max_response_output_tokens": 4096
            }
        }
        
        await self.ws.send(json.dumps(config))
        logger.bind(tag=TAG).info("Session configured")
    
    def send_audio(self, audio_data: bytes):
        """
        Send audio data to OpenAI Realtime API
        Converts from Opus 16kHz to PCM16 24kHz
        """
        if not self.connected:
            logger.bind(tag=TAG).warning("Not connected to OpenAI Realtime API")
            return
        
        # Convert Opus to PCM16 and resample
        pcm_data = self._convert_opus_to_pcm(audio_data)
        
        if pcm_data:
            # Send audio immediately using async task
            asyncio.run_coroutine_threadsafe(
                self._send_audio_chunk(pcm_data),
                self.loop
            )
    
    async def _send_audio_chunk(self, pcm_data: bytes):
        """Send PCM audio chunk to OpenAI"""
        message = {
            "type": "input_audio_buffer.append",
            "audio": base64.b64encode(pcm_data).decode("utf-8")
        }
        
        await self.ws.send(json.dumps(message))
    
    async def _commit_audio(self):
        """Commit audio buffer to trigger processing"""
        message = {
            "type": "input_audio_buffer.commit"
        }
        await self.ws.send(json.dumps(message))
        logger.bind(tag=TAG).debug("Committed audio buffer for processing")
    
    def commit_and_respond(self):
        """Commit audio buffer and trigger response generation"""
        if not self.connected:
            return
            
        # Schedule commit and response in async loop
        asyncio.run_coroutine_threadsafe(
            self._commit_and_respond_async(),
            self.loop
        )
    
    async def _commit_and_respond_async(self):
        """Async method to commit audio and trigger response"""
        # Commit the audio buffer
        await self._commit_audio()
        
        # Trigger response generation
        response_message = {
            "type": "response.create"
        }
        await self.ws.send(json.dumps(response_message))
        logger.bind(tag=TAG).info("Triggered OpenAI response generation")
    
    def _convert_opus_to_pcm(self, opus_data: bytes) -> bytes:
        """
        Convert Opus audio to PCM16 format and resample from 16kHz to 24kHz
        Uses existing ASR decoder utility
        """
        try:
            # Decode Opus to PCM using existing utility
            pcm_frames = ASRProviderBase.decode_opus([opus_data])
            
            if not pcm_frames:
                return b""
            
            # Combine all PCM frames
            pcm_16khz = b''.join(pcm_frames)
            
            # Resample from 16kHz to 24kHz
            samples = np.frombuffer(pcm_16khz, dtype=np.int16)
            num_samples = int(len(samples) * 24000 / 16000)
            resampled = signal.resample(samples, num_samples)
            resampled_int16 = np.clip(resampled, -32768, 32767).astype(np.int16)
            
            return resampled_int16.tobytes()
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"Error converting Opus to PCM: {e}")
            return b""
    
    def _convert_pcm_to_opus(self, pcm_data: bytes) -> bytes:
        """
        Convert PCM16 24kHz audio to Opus 16kHz for ESP32
        Uses existing Opus encoder utility
        """
        try:
            # Resample from 24kHz to 16kHz first
            samples = np.frombuffer(pcm_data, dtype=np.int16)
            num_samples = int(len(samples) * 16000 / 24000)
            resampled = signal.resample(samples, num_samples)
            resampled_int16 = np.clip(resampled, -32768, 32767).astype(np.int16)
            pcm_16khz = resampled_int16.tobytes()
            
            # Encode to Opus using existing utility (do not end stream for individual chunks)
            opus_packets = self.opus_encoder.encode_pcm_to_opus(pcm_16khz, end_of_stream=False)
            
            if opus_packets:
                # Debug: Log packet information
                total_size = sum(len(packet) for packet in opus_packets)
                logger.bind(tag=TAG).debug(f"PCM input: {len(pcm_16khz)} bytes, Generated {len(opus_packets)} Opus packets, total: {total_size} bytes")
                
                # Return concatenated Opus packets
                return b''.join(opus_packets)
            else:
                return b""
                
        except Exception as e:
            logger.bind(tag=TAG).error(f"Error converting PCM to Opus: {e}")
            return b""
    
    def _convert_pcm_to_opus_packets(self, pcm_data: bytes) -> list:
        """
        Convert PCM16 24kHz audio to individual Opus packets for ESP32
        Returns list of individual Opus packets instead of concatenated bytes
        """
        try:
            # Resample from 24kHz to 16kHz first
            samples = np.frombuffer(pcm_data, dtype=np.int16)
            num_samples = int(len(samples) * 16000 / 24000)
            resampled = signal.resample(samples, num_samples)
            resampled_int16 = np.clip(resampled, -32768, 32767).astype(np.int16)
            pcm_16khz = resampled_int16.tobytes()
            
            # Encode to Opus using existing utility (returns list of packets)
            opus_packets = self.opus_encoder.encode_pcm_to_opus(pcm_16khz, end_of_stream=False)
            
            if opus_packets:
                # Debug: Log packet information
                total_size = sum(len(packet) for packet in opus_packets)
                logger.bind(tag=TAG).debug(f"PCM input: {len(pcm_16khz)} bytes, Generated {len(opus_packets)} Opus packets, total: {total_size} bytes")
                
                # Return individual packets
                return opus_packets
            else:
                return []
                
        except Exception as e:
            logger.bind(tag=TAG).error(f"Error converting PCM to Opus packets: {e}")
            return []
    
    def _convert_pcm_to_opus_final(self, pcm_data: bytes) -> bytes:
        """
        Convert final PCM16 24kHz audio chunk to Opus 16kHz for ESP32 with end_of_stream=True
        Uses existing Opus encoder utility
        """
        try:
            # Resample from 24kHz to 16kHz first
            samples = np.frombuffer(pcm_data, dtype=np.int16)
            num_samples = int(len(samples) * 16000 / 24000)
            resampled = signal.resample(samples, num_samples)
            resampled_int16 = np.clip(resampled, -32768, 32767).astype(np.int16)
            pcm_16khz = resampled_int16.tobytes()
            
            # Encode to Opus with end_of_stream=True for final chunk
            opus_packets = self.opus_encoder.encode_pcm_to_opus(pcm_16khz, end_of_stream=True)
            
            if opus_packets:
                # Return concatenated Opus packets
                return b''.join(opus_packets)
            else:
                return b""
                
        except Exception as e:
            logger.bind(tag=TAG).error(f"Error converting final PCM to Opus: {e}")
            return b""
    
    def _convert_pcm_to_opus_final_packets(self, pcm_data: bytes) -> list:
        """
        Convert final PCM16 24kHz audio chunk to individual Opus packets with end_of_stream=True
        Returns list of individual Opus packets
        """
        try:
            # Resample from 24kHz to 16kHz first
            samples = np.frombuffer(pcm_data, dtype=np.int16)
            num_samples = int(len(samples) * 16000 / 24000)
            resampled = signal.resample(samples, num_samples)
            resampled_int16 = np.clip(resampled, -32768, 32767).astype(np.int16)
            pcm_16khz = resampled_int16.tobytes()
            
            # Encode to Opus with end_of_stream=True for final chunk
            opus_packets = self.opus_encoder.encode_pcm_to_opus(pcm_16khz, end_of_stream=True)
            
            if opus_packets:
                logger.bind(tag=TAG).debug(f"Generated {len(opus_packets)} final Opus packets")
                return opus_packets
            else:
                return []
                
        except Exception as e:
            logger.bind(tag=TAG).error(f"Error converting final PCM to Opus packets: {e}")
            return []
    
    def response(self, session_id: str, dialogue: list) -> Generator[str, None, None]:
        """
        Standard LLM response interface (text mode fallback)
        For Realtime API, this sends text instead of audio
        """
        if not self.connected:
            yield "OpenAI Realtime API not connected"
            return
        
        # Send text message
        asyncio.run(self._send_text_message(dialogue[-1].get("content", "")))
        
        # Wait for and yield text response
        # This is a simplified implementation
        yield "Response from Realtime API"
    
    async def _send_text_message(self, text: str):
        """Send text message to OpenAI Realtime API"""
        # Reset encoder state for new conversation
        self.opus_encoder.reset_state()
        
        message = {
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": "user",
                "content": [{
                    "type": "input_text",
                    "text": text
                }]
            }
        }
        
        await self.ws.send(json.dumps(message))
        
        # Trigger response
        response_message = {
            "type": "response.create"
        }
        await self.ws.send(json.dumps(response_message))
    
    async def disconnect(self):
        """Disconnect from OpenAI Realtime API"""
        if self.ws:
            await self.ws.close()
            self.connected = False
            logger.bind(tag=TAG).info("Disconnected from OpenAI Realtime API")
    
    def start_async_loop(self):
        """Start async event loop in separate thread"""
        def run_loop():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_until_complete(self.connect())
        
        self.ws_thread = threading.Thread(target=run_loop)
        self.ws_thread.start()
    
    def stop(self):
        """Stop the provider and clean up"""
        if self.loop:
            asyncio.run_coroutine_threadsafe(self.disconnect(), self.loop)
        if self.ws_thread:
            self.ws_thread.join(timeout=5)