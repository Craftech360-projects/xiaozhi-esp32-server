#!/usr/bin/env python3
"""
Gemini Real-time WebSocket Client
Modified version of client.py that works with the Gemini real-time server
Supports: ESP32 → Deepgram ASR → Gemini LLM+TTS → ESP32 pipeline
"""

import json
import time
import uuid
import threading
import logging
import pyaudio
import keyboard
import asyncio
import websockets
import opuslib

from typing import Dict, Optional
from queue import Queue, Empty

# --- Configuration ---
SERVER_IP = "192.168.1.170"  # Update with your server's IP
WEBSOCKET_PORT = 8002  # Gemini real-time server port
WEBSOCKET_URL = f"ws://{SERVER_IP}:{WEBSOCKET_PORT}/xiaozhi/v1/"

# Audio configuration
SAMPLE_RATE = 16000
CHANNELS = 1
FRAME_DURATION_MS = 60  # 60ms frames like ESP32
SAMPLES_PER_FRAME = int(SAMPLE_RATE * FRAME_DURATION_MS / 1000)

# Buffer configuration
PLAYBACK_BUFFER_MIN_FRAMES = 3
PLAYBACK_BUFFER_START_FRAMES = 8
TTS_TIMEOUT_SECONDS = 30
BUFFER_TIMEOUT_SECONDS = 10

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger("GeminiRealtimeClient")

# Global variables
stop_threads = threading.Event()
start_recording_event = threading.Event()
stop_recording_event = threading.Event()


class GeminiRealtimeClient:
    """WebSocket client for Gemini real-time audio pipeline"""
    
    def __init__(self):
        self.websocket = None
        self.session_id = str(uuid.uuid4())
        self.device_mac = self._generate_unique_mac()
        
        # Audio components
        self.audio_playback_queue = Queue()
        self.playback_thread = None
        self.recording_thread = None
        self.websocket_thread = None
        
        # State tracking
        self.connected = False
        self.tts_active = False
        self.recording_active = False
        self.last_audio_received = 0
        self.session_active = True
        self.conversation_count = 0
        
        # Audio statistics
        self.total_audio_chunks_received = 0
        self.total_audio_chunks_sent = 0
        
        logger.info(f"Gemini Real-time Client initialized")
        logger.info(f"Device MAC: {self.device_mac}")
        logger.info(f"Session ID: {self.session_id}")

    def _generate_unique_mac(self) -> str:
        """Generate a unique MAC address for the client"""
        mac_bytes = [0x00, 0x16, 0x3E,  # OUI prefix
                     uuid.uuid4().bytes[0], 
                     uuid.uuid4().bytes[1], 
                     uuid.uuid4().bytes[2]]
        return '_'.join(f'{b:02x}' for b in mac_bytes)

    async def connect_websocket(self) -> bool:
        """Connect to the Gemini real-time WebSocket server"""
        try:
            logger.info(f"🔗 Connecting to Gemini real-time server: {WEBSOCKET_URL}")
            
            self.websocket = await websockets.connect(
                WEBSOCKET_URL,
                ping_interval=30,
                ping_timeout=10,
                close_timeout=10
            )
            
            self.connected = True
            logger.info("✅ WebSocket connected successfully")
            
            # Send hello message
            await self._send_hello()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to WebSocket: {e}")
            return False

    async def _send_hello(self):
        """Send hello message to establish session"""
        hello_message = {
            "type": "hello",
            "client_type": "python_client",
            "device_mac": self.device_mac,
            "session_id": self.session_id,
            "audio_format": "opus",
            "sample_rate": SAMPLE_RATE,
            "channels": CHANNELS,
            "frame_duration": FRAME_DURATION_MS,
            "timestamp": time.time()
        }
        
        await self.websocket.send(json.dumps(hello_message))
        logger.info("📤 Sent hello message")
        
        # Wait for hello response
        try:
            response = await asyncio.wait_for(self.websocket.recv(), timeout=10)
            hello_response = json.loads(response)
            
            logger.info("📥 Received hello response:")
            logger.info(f"   Session ID: {hello_response.get('session_id')}")
            logger.info(f"   Pipeline: {hello_response.get('capabilities', {}).get('pipeline')}")
            logger.info(f"   Gemini Real-time: {hello_response.get('capabilities', {}).get('gemini_realtime')}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to receive hello response: {e}")
            return False

    async def send_text_message(self, text: str):
        """Send text message to trigger Gemini response"""
        if not self.connected or not self.websocket:
            logger.error("❌ Not connected to WebSocket")
            return
        
        text_message = {
            "type": "text",
            "content": text,
            "session_id": self.session_id,
            "timestamp": time.time()
        }
        
        await self.websocket.send(json.dumps(text_message))
        logger.info(f"📤 Sent text message: {text}")

    async def send_audio_chunk(self, audio_data: bytes):
        """Send audio chunk to server"""
        if not self.connected or not self.websocket:
            return
        
        try:
            await self.websocket.send(audio_data)
            self.total_audio_chunks_sent += 1
            
        except Exception as e:
            logger.error(f"❌ Failed to send audio chunk: {e}")

    async def websocket_listener(self):
        """Listen for WebSocket messages from server"""
        logger.info("👂 WebSocket listener started")
        
        try:
            while self.connected and self.websocket:
                try:
                    message = await asyncio.wait_for(self.websocket.recv(), timeout=1.0)
                    
                    if isinstance(message, bytes):
                        # Audio response from Gemini
                        self.audio_playback_queue.put(message)
                        self.total_audio_chunks_received += 1
                        self.last_audio_received = time.time()
                        
                        if self.total_audio_chunks_received == 1:
                            logger.info("🔊 Started receiving audio from Gemini...")
                            self.tts_active = True
                        
                        if self.total_audio_chunks_received % 50 == 0:
                            logger.info(f"📥 Received {self.total_audio_chunks_received} audio chunks")
                    
                    elif isinstance(message, str):
                        # Text message from server
                        try:
                            msg = json.loads(message)
                            await self._handle_text_message(msg)
                        except json.JSONDecodeError:
                            logger.warning(f"📥 Non-JSON message: {message[:100]}...")
                
                except asyncio.TimeoutError:
                    continue
                except websockets.exceptions.ConnectionClosed:
                    logger.info("🔌 WebSocket connection closed")
                    break
                except Exception as e:
                    logger.error(f"❌ WebSocket listener error: {e}")
                    break
        
        except Exception as e:
            logger.error(f"❌ WebSocket listener failed: {e}")
        
        finally:
            self.connected = False
            logger.info("👂 WebSocket listener stopped")

    async def _handle_text_message(self, msg: dict):
        """Handle text messages from server"""
        msg_type = msg.get("type", "unknown")
        
        if msg_type == "hello_response":
            logger.info("✅ Received hello response")
        
        elif msg_type == "status":
            status = msg.get("data", {})
            logger.info(f"📊 Server status: {status}")
        
        elif msg_type == "error":
            error_msg = msg.get("message", "Unknown error")
            logger.error(f"❌ Server error: {error_msg}")
        
        else:
            logger.info(f"📥 Server message [{msg_type}]: {msg}")

    def _playback_thread(self):
        """Thread to play back audio from Gemini"""
        p = pyaudio.PyAudio()
        
        try:
            # Configure audio output for the format Gemini sends
            stream = p.open(
                format=pyaudio.paInt16,  # 16-bit PCM
                channels=CHANNELS,
                rate=24000,  # Gemini typically sends 24kHz audio
                output=True,
                frames_per_buffer=1024
            )
            
            logger.info("🔊 Audio playback thread started")
            is_playing = False
            buffer_timeout_start = time.time()
            
            while not stop_threads.is_set() and self.session_active:
                try:
                    # Jitter buffer logic
                    if not is_playing:
                        if self.audio_playback_queue.qsize() < PLAYBACK_BUFFER_START_FRAMES:
                            if time.time() - buffer_timeout_start > BUFFER_TIMEOUT_SECONDS:
                                logger.warning(f"⏰ Buffer timeout after {BUFFER_TIMEOUT_SECONDS}s")
                                buffer_timeout_start = time.time()
                            
                            time.sleep(0.05)
                            continue
                        else:
                            logger.info("✅ Buffer ready. Starting playback.")
                            is_playing = True
                    
                    # Check buffer level
                    if self.audio_playback_queue.qsize() < PLAYBACK_BUFFER_MIN_FRAMES:
                        is_playing = False
                        buffer_timeout_start = time.time()
                        logger.warning(f"‼️ Playback buffer low. Re-buffering...")
                        continue
                    
                    # Play audio chunk
                    audio_chunk = self.audio_playback_queue.get(timeout=1)
                    stream.write(audio_chunk)
                    
                except Empty:
                    is_playing = False
                    buffer_timeout_start = time.time()
                    continue
                except Exception as e:
                    logger.error(f"❌ Playback error: {e}")
                    break
        
        except Exception as e:
            logger.error(f"❌ Playback thread error: {e}")
        
        finally:
            try:
                stream.stop_stream()
                stream.close()
                p.terminate()
            except:
                pass
            logger.info("🔊 Playback thread finished")

    def _recording_thread(self):
        """Thread to record and send audio to server"""
        logger.info("🎤 Recording thread started")
        
        while not stop_threads.is_set() and self.session_active:
            # Wait for recording to be triggered
            if not start_recording_event.wait(timeout=1):
                continue
            
            if stop_threads.is_set():
                break
            
            logger.info("🔴 Recording activated")
            p = pyaudio.PyAudio()
            
            try:
                # Initialize Opus encoder
                encoder = opuslib.Encoder(SAMPLE_RATE, CHANNELS, opuslib.APPLICATION_VOIP)
                
                # Open microphone stream
                stream = p.open(
                    format=pyaudio.paInt16,
                    channels=CHANNELS,
                    rate=SAMPLE_RATE,
                    input=True,
                    frames_per_buffer=SAMPLES_PER_FRAME
                )
                
                logger.info("🎙️ Microphone stream opened. Recording...")
                self.recording_active = True
                
                packets_sent = 0
                last_log_time = time.time()
                
                # Recording loop
                while (not stop_threads.is_set() and 
                       not stop_recording_event.is_set() and 
                       self.session_active and 
                       self.connected):
                    
                    try:
                        # Read audio from microphone
                        pcm_data = stream.read(SAMPLES_PER_FRAME, exception_on_overflow=False)
                        
                        # Encode to Opus
                        opus_data = encoder.encode(pcm_data, SAMPLES_PER_FRAME)
                        
                        # Send to server via WebSocket
                        if self.websocket and opus_data:
                            asyncio.run_coroutine_threadsafe(
                                self.send_audio_chunk(opus_data),
                                self.websocket_loop
                            )
                            packets_sent += 1
                        
                        # Log progress
                        if time.time() - last_log_time >= 1.0:
                            logger.info(f"⬆️ Sent {packets_sent} audio packets in the last second")
                            packets_sent = 0
                            last_log_time = time.time()
                    
                    except Exception as e:
                        logger.error(f"❌ Recording error: {e}")
                        break
                
                self.recording_active = False
                logger.info("🎙️ Recording session ended")
                
            except Exception as e:
                logger.error(f"❌ Recording thread error: {e}")
            
            finally:
                try:
                    stream.stop_stream()
                    stream.close()
                    p.terminate()
                except:
                    pass
                
                start_recording_event.clear()
                
                if stop_recording_event.is_set():
                    logger.info("🛑 Recording stopped by signal")
        
        logger.info("🎤 Recording thread finished")

    def _monitor_spacebar(self):
        """Monitor spacebar for interrupting TTS"""
        logger.info("⌨️ Spacebar monitor started (press Space to interrupt)")
        
        while not stop_threads.is_set() and self.session_active:
            try:
                if keyboard.is_pressed('space'):
                    logger.info("🚫 Spacebar pressed - interrupting TTS")
                    
                    # Send control message to stop TTS
                    if self.websocket and self.connected:
                        control_msg = {
                            "type": "control",
                            "command": "stop_audio",
                            "session_id": self.session_id
                        }
                        
                        asyncio.run_coroutine_threadsafe(
                            self.websocket.send(json.dumps(control_msg)),
                            self.websocket_loop
                        )
                    
                    # Wait for key release
                    while keyboard.is_pressed('space') and not stop_threads.is_set():
                        time.sleep(0.01)
                
                time.sleep(0.01)
                
            except Exception as e:
                logger.error(f"❌ Spacebar monitor error: {e}")
                break
        
        logger.info("⌨️ Spacebar monitor stopped")

    async def start_conversation(self):
        """Start a conversation with Cheeko"""
        logger.info("🗣️ Starting conversation with Cheeko...")
        
        # Send initial message to trigger Cheeko's greeting
        await self.send_text_message("Hello Cheeko! I'm ready to chat with you!")
        
        # Start recording after a short delay
        await asyncio.sleep(2)
        start_recording_event.set()
        logger.info("🎤 Recording enabled - you can now speak!")

    async def keepalive_ping(self):
        """Send periodic ping frames to keep the WebSocket alive."""
        logger.info("🔄 Keepalive ping task started")
        while self.connected and self.websocket:
            try:
                await self.websocket.ping()
                logger.debug("🔄 Sent keepalive ping")
            except Exception as e:
                logger.error(f"❌ Keepalive ping error: {e}")
                break
            await asyncio.sleep(20)  # Ping every 20 seconds
        logger.info("🔄 Keepalive ping task stopped")

    async def run_async(self):
        """Main async run method"""
        try:
            # Connect to WebSocket
            if not await self.connect_websocket():
                return False

            # Store the event loop for other threads
            self.websocket_loop = asyncio.get_event_loop()

            # Start threads
            logger.info("🚀 Starting audio threads...")

            self.playback_thread = threading.Thread(target=self._playback_thread, daemon=True)
            self.recording_thread = threading.Thread(target=self._recording_thread, daemon=True)
            spacebar_thread = threading.Thread(target=self._monitor_spacebar, daemon=True)

            self.playback_thread.start()
            self.recording_thread.start()
            spacebar_thread.start()

            # Start WebSocket listener
            websocket_task = asyncio.create_task(self.websocket_listener())

            # Start keepalive ping task
            keepalive_task = asyncio.create_task(self.keepalive_ping())

            # Start conversation
            await self.start_conversation()

            logger.info("✅ Gemini real-time client running!")
            logger.info("🎤 Speak to Cheeko - your voice will be processed by Deepgram → Gemini")
            logger.info("🔊 Gemini's responses will be played back in real-time")
            logger.info("⌨️ Press Spacebar to interrupt TTS, Ctrl+C to exit")

            # Keep running
            try:
                await asyncio.gather(websocket_task, keepalive_task)
            except KeyboardInterrupt:
                logger.info("👋 Keyboard interrupt received")

            return True

        except Exception as e:
            logger.error(f"❌ Run error: {e}")
            return False

        finally:
            await self.cleanup()

    async def cleanup(self):
        """Clean up resources"""
        logger.info("🧹 Cleaning up...")
        
        stop_threads.set()
        self.session_active = False
        start_recording_event.set()  # Unblock waiting threads
        stop_recording_event.set()
        
        # Print statistics
        logger.info("📊 Session Statistics:")
        logger.info(f"   Audio chunks received: {self.total_audio_chunks_received}")
        logger.info(f"   Audio chunks sent: {self.total_audio_chunks_sent}")
        
        # Wait for threads
        if self.playback_thread and self.playback_thread.is_alive():
            self.playback_thread.join(timeout=2)
        
        if self.recording_thread and self.recording_thread.is_alive():
            self.recording_thread.join(timeout=2)
        
        # Close WebSocket
        if self.websocket:
            try:
                await self.websocket.close()
            except:
                pass
        
        self.connected = False
        logger.info("✅ Cleanup completed")

    def run(self):
        """Main run method (synchronous wrapper)"""
        try:
            asyncio.run(self.run_async())
        except KeyboardInterrupt:
            logger.info("👋 Interrupted by user")
        except Exception as e:
            logger.error(f"❌ Client error: {e}")


if __name__ == "__main__":
    print("🎯 Gemini Real-time WebSocket Client")
    print("=" * 60)
    print("Audio Pipeline: Microphone → Deepgram ASR → Gemini LLM+TTS → Speakers")
    print("Real-time streaming audio with Cheeko AI assistant")
    print("=" * 60)
    print(f"🔗 Connecting to: {WEBSOCKET_URL}")
    print("⌨️ Controls: Spacebar = Interrupt TTS, Ctrl+C = Exit")
    print("=" * 60)
    
    client = GeminiRealtimeClient()
    client.run()