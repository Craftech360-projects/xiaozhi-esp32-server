#!/usr/bin/env python3
"""
XiaoZhi WebSocket Client
A Python client for connecting to the XiaoZhi voice assistant server
"""

import asyncio
import websockets
import json
import uuid
import logging
from typing import Optional, Dict, Any
import argparse
import io
import wave
import threading
import tempfile
import os
try:
    import pyaudio
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    print("⚠️  PyAudio not available. Audio playback disabled. Install with: pip install pyaudio")

try:
    import opuslib
    OPUS_AVAILABLE = True
except ImportError:
    OPUS_AVAILABLE = False
    print("⚠️  OpusLib not available. Opus decoding disabled. Install with: pip install opuslib")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class XiaoZhiClient:
    def __init__(self, server_url: str, device_id: str = None, device_name: str = "Python Client", enable_audio: bool = True):
        self.server_url = server_url
        self.device_id = device_id or self._generate_device_id()
        self.device_name = device_name
        self.websocket = None
        self.session_id = None
        self.connected = False
        self.enable_audio = enable_audio and AUDIO_AVAILABLE
        self.audio_buffer = []
        self.is_playing_audio = False
        self.audio_chunks = []
        
        # Audio settings (matching server config)
        self.audio_format = pyaudio.paInt16 if AUDIO_AVAILABLE else None
        self.channels = 1
        self.sample_rate = 16000
        self.chunk_size = 1024
        
        # Opus decoder
        self.opus_decoder = None
        if OPUS_AVAILABLE:
            try:
                self.opus_decoder = opuslib.Decoder(self.sample_rate, self.channels)
                logger.info("🎵 Opus decoder initialized")
            except Exception as e:
                logger.warning(f"Opus decoder initialization failed: {e}")
        
        if self.enable_audio:
            try:
                self.audio = pyaudio.PyAudio()
                logger.info("🔊 Audio system initialized")
            except Exception as e:
                logger.warning(f"Audio initialization failed: {e}")
                self.enable_audio = False
        
    def _generate_device_id(self) -> str:
        """Generate a random device ID in MAC address format"""
        import random
        mac = [random.randint(0x00, 0xff) for _ in range(6)]
        return ':'.join(f'{x:02X}' for x in mac)
    
    async def connect(self, token: str = "your-token1") -> bool:
        """Connect to the XiaoZhi server"""
        try:
            # Add device info to URL parameters
            url_with_params = f"{self.server_url}?device-id={self.device_id}&client-id=python_client"
            
            logger.info(f"Connecting to {url_with_params}")
            # Connect without extra_headers for compatibility
            self.websocket = await websockets.connect(url_with_params)
            
            # Send hello message
            hello_message = {
                "type": "hello",
                "device_id": self.device_id,
                "device_name": self.device_name,
                "device_mac": self.device_id,
                "token": token,
                "features": {
                    "mcp": True
                }
            }
            
            await self.send_message(hello_message)
            logger.info("Hello message sent")
            
            # Wait for hello response
            response = await self.websocket.recv()
            response_data = json.loads(response)
            
            if response_data.get("type") == "hello" and response_data.get("session_id"):
                self.session_id = response_data.get("session_id")
                self.connected = True
                logger.info(f"Connected successfully! Session ID: {self.session_id}")
                logger.info(f"Server audio params: {response_data.get('audio_params', {})}")
                return True
            else:
                logger.error(f"Hello handshake failed: {response_data}")
                return False
                
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False
    
    async def send_message(self, message: Dict[Any, Any]):
        """Send a message to the server"""
        if self.websocket:
            await self.websocket.send(json.dumps(message))
    
    async def send_text_message(self, text: str):
        """Send a text message for processing"""
        if not self.connected:
            logger.error("Not connected to server")
            return
        
        # Send text message using the correct format (listen with detect state)
        text_message = {
            "type": "listen",
            "mode": "manual",
            "state": "detect",
            "text": text
        }
        await self.send_message(text_message)
        logger.info(f"Sent text: {text}")
    
    async def send_mcp_response(self, mcp_data: Dict[Any, Any]):
        """Send MCP response (for tool interactions)"""
        if not self.connected:
            logger.error("Not connected to server")
            return
            
        mcp_message = {
            "session_id": self.session_id or "",
            "type": "mcp",
            "payload": mcp_data
        }
        await self.send_message(mcp_message)
        logger.info(f"Sent MCP response: {mcp_data.get('method', 'unknown')}")
    
    async def handle_mcp_request(self, payload: Dict[Any, Any]):
        """Handle MCP requests from server"""
        method = payload.get("method")
        msg_id = payload.get("id")
        
        if method == "tools/list":
            # Respond with available tools
            tools_response = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "tools": [
                        {
                            "name": "self.get_device_status",
                            "description": "Get current device status including volume, brightness, etc.",
                            "inputSchema": {"type": "object", "properties": {}}
                        },
                        {
                            "name": "self.audio_speaker.set_volume",
                            "description": "Set audio speaker volume (0-100)",
                            "inputSchema": {
                                "type": "object",
                                "properties": {"volume": {"type": "integer", "minimum": 0, "maximum": 100}},
                                "required": ["volume"]
                            }
                        },
                        {
                            "name": "self.screen.set_brightness",
                            "description": "Set screen brightness (0-100)",
                            "inputSchema": {
                                "type": "object",
                                "properties": {"brightness": {"type": "integer", "minimum": 0, "maximum": 100}},
                                "required": ["brightness"]
                            }
                        }
                    ]
                }
            }
            await self.send_mcp_response(tools_response)
            
        elif method == "tools/call":
            # Handle tool calls
            tool_name = payload.get("params", {}).get("name")
            arguments = payload.get("params", {}).get("arguments", {})
            
            logger.info(f"Tool call: {tool_name} with args: {arguments}")
            
            # Simulate tool execution
            result = self._execute_tool(tool_name, arguments)
            
            tool_response = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": [{"type": "text", "text": str(result)}],
                    "isError": False
                }
            }
            await self.send_mcp_response(tool_response)
    
    def _execute_tool(self, tool_name: str, arguments: Dict[Any, Any]) -> str:
        """Simulate tool execution"""
        if tool_name == "self.get_device_status":
            return json.dumps({
                "volume": 75,
                "brightness": 80,
                "battery": 85,
                "wifi_connected": True,
                "status": "online"
            })
        elif tool_name == "self.audio_speaker.set_volume":
            volume = arguments.get("volume", 50)
            logger.info(f"Setting volume to {volume}")
            return f"Volume set to {volume}%"
        elif tool_name == "self.screen.set_brightness":
            brightness = arguments.get("brightness", 50)
            logger.info(f"Setting brightness to {brightness}")
            return f"Brightness set to {brightness}%"
        else:
            return f"Tool {tool_name} executed successfully"
    
    def save_audio_chunk(self, audio_data: bytes):
        """Save audio chunk to file for debugging"""
        try:
            # Save raw audio data to temp file for inspection
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.raw')
            temp_file.write(audio_data)
            temp_file.close()
            logger.info(f"💾 Saved audio chunk to: {temp_file.name}")
        except Exception as e:
            logger.error(f"Failed to save audio chunk: {e}")
    
    def save_complete_audio(self):
        """Save all received audio chunks as one file"""
        if not self.audio_chunks:
            return
            
        try:
            # Save all chunks combined
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.raw')
            for chunk in self.audio_chunks:
                temp_file.write(chunk)
            temp_file.close()
            
            total_size = sum(len(chunk) for chunk in self.audio_chunks)
            logger.info(f"💾 Saved complete audio ({total_size} bytes, {len(self.audio_chunks)} chunks) to: {temp_file.name}")
            
            # Also try to save as WAV if we think it's PCM
            try:
                wav_file = temp_file.name.replace('.raw', '.wav')
                with wave.open(wav_file, 'wb') as wf:
                    wf.setnchannels(self.channels)
                    wf.setsampwidth(2)  # 16-bit
                    wf.setframerate(self.sample_rate)
                    for chunk in self.audio_chunks:
                        wf.writeframes(chunk)
                logger.info(f"💾 Also saved as WAV: {wav_file}")
            except Exception as e:
                logger.debug(f"WAV save failed: {e}")
                
        except Exception as e:
            logger.error(f"Failed to save complete audio: {e}")

    def play_audio_chunk(self, audio_data: bytes):
        """Play audio chunk with improved error handling"""
        if not self.enable_audio:
            return
        
        # Save chunk for debugging (limit to prevent memory issues)
        if len(self.audio_chunks) < 1000:  # Limit memory usage
            self.audio_chunks.append(audio_data)
        
        def play_audio():
            stream = None
            try:
                # Method 1: Try to decode as Opus if available
                if self.opus_decoder and OPUS_AVAILABLE:
                    try:
                        # Decode Opus to PCM
                        pcm_data = self.opus_decoder.decode(audio_data, frame_size=960)  # 60ms at 16kHz
                        
                        # Create audio stream with error handling
                        stream = self.audio.open(
                            format=self.audio_format,
                            channels=self.channels,
                            rate=self.sample_rate,
                            output=True,
                            frames_per_buffer=self.chunk_size
                        )
                        
                        # Play decoded PCM data
                        if pcm_data and len(pcm_data) > 0:
                            stream.write(pcm_data)
                        
                        logger.debug("🔊 Played Opus audio chunk")
                        return
                        
                    except Exception as e:
                        logger.debug(f"Opus decode failed: {e}")
                    finally:
                        if stream:
                            try:
                                stream.stop_stream()
                                stream.close()
                            except:
                                pass
                
                # Method 2: Skip raw PCM fallback to avoid crashes
                logger.debug("Skipping raw PCM playback")
                
            except Exception as e:
                logger.error(f"Audio playback error: {e}")
            finally:
                if stream:
                    try:
                        stream.stop_stream()
                        stream.close()
                    except:
                        pass
        
        # Play audio in separate thread to avoid blocking
        try:
            audio_thread = threading.Thread(target=play_audio)
            audio_thread.daemon = True
            audio_thread.start()
        except Exception as e:
            logger.error(f"Failed to start audio thread: {e}")

    async def listen_for_messages(self):
        """Listen for incoming messages from server"""
        try:
            async for message in self.websocket:
                try:
                    # Check if message is binary (audio data)
                    if isinstance(message, bytes):
                        logger.info(f"🎵 Received audio chunk: {len(message)} bytes")
                        if self.enable_audio:
                            self.play_audio_chunk(message)
                        continue
                    
                    # Try to parse as JSON
                    data = json.loads(message)
                    await self.handle_message(data)
                except json.JSONDecodeError:
                    logger.warning(f"Received non-JSON message (length: {len(message)})")
                except Exception as e:
                    logger.error(f"Error handling message: {e}")
        except websockets.exceptions.ConnectionClosed:
            logger.info("Connection closed by server")
            self.connected = False
        except Exception as e:
            logger.error(f"Error in message listener: {e}")
            self.connected = False
    
    async def handle_message(self, data: Dict[Any, Any]):
        """Handle incoming messages"""
        msg_type = data.get("type")
        
        if msg_type == "hello":
            logger.info(f"Received hello response: {data}")
        elif msg_type == "mcp":
            payload = data.get("payload", {})
            await self.handle_mcp_request(payload)
        elif msg_type == "stt":
            # Speech-to-text result
            text_content = data.get("text", "")
            logger.info(f"🎤 STT Result: {text_content}")
        elif msg_type == "tts":
            # Text-to-speech status
            state = data.get("state", "")
            text_content = data.get("text", "")
            if state == "sentence_start" and text_content:
                logger.info(f"🔊 TTS Response: {text_content}")
                # Clear previous audio chunks for new sentence
                self.audio_chunks = []
            elif state == "end":
                logger.info(f"🔊 TTS Complete - received {len(self.audio_chunks)} audio chunks")
                # Optionally save complete audio
                self.save_complete_audio()
            else:
                logger.info(f"🔊 TTS State: {state}")
        elif msg_type == "text":
            text_content = data.get("text", "")
            logger.info(f"💬 Text Response: {text_content}")
        elif msg_type == "audio":
            logger.info("🎵 Received audio response")
        elif msg_type == "emotion":
            emotion = data.get("emotion", "")
            logger.info(f"😊 Emotion: {emotion}")
        else:
            logger.info(f"📨 Unknown message type '{msg_type}': {data}")
    
    async def disconnect(self):
        """Disconnect from server"""
        self.connected = False
        
        if self.websocket:
            try:
                await self.websocket.close()
                logger.info("Disconnected from server")
            except Exception as e:
                logger.warning(f"WebSocket close error: {e}")
        
        # Clean up audio resources
        if self.enable_audio and hasattr(self, 'audio'):
            try:
                # Give time for audio threads to finish
                await asyncio.sleep(0.1)
                self.audio.terminate()
                logger.info("🔊 Audio system terminated")
            except Exception as e:
                logger.warning(f"Audio cleanup error: {e}")
        
        # Clear audio chunks to free memory
        self.audio_chunks.clear()

async def main():
    parser = argparse.ArgumentParser(description='XiaoZhi WebSocket Client')
    parser.add_argument('--server', default='ws://127.0.0.1:8000/xiaozhi/v1', 
                       help='WebSocket server URL')
    parser.add_argument('--token', default='your-token1', 
                       help='Authentication token')
    parser.add_argument('--device-name', default='Python Client', 
                       help='Device name')
    parser.add_argument('--no-audio', action='store_true',
                       help='Disable audio playback')
    
    args = parser.parse_args()
    
    client = XiaoZhiClient(args.server, device_name=args.device_name, enable_audio=not args.no_audio)
    
    try:
        # Connect to server
        if await client.connect(args.token):
            logger.info("Connected successfully!")
            
            # Start message listener in background
            listener_task = asyncio.create_task(client.listen_for_messages())
            
            # Interactive mode
            print("\n=== XiaoZhi Client Connected ===")
            print("Commands:")
            print("  /text <message>  - Send text message")
            print("  /status         - Get device status")
            print("  /volume <0-100> - Set volume")
            print("  /brightness <0-100> - Set brightness")
            print("  /quit           - Disconnect and exit")
            print("=====================================\n")
            
            while client.connected:
                try:
                    user_input = input("> ").strip()
                    
                    if user_input.startswith('/quit'):
                        break
                    elif user_input.startswith('/text '):
                        message = user_input[6:]
                        await client.send_text_message(message)
                    elif user_input.startswith('/status'):
                        await client.send_text_message("请告诉我设备当前状态")
                    elif user_input.startswith('/volume '):
                        try:
                            volume = int(user_input[8:])
                            await client.send_text_message(f"请将音量设置为{volume}")
                        except ValueError:
                            print("Invalid volume value")
                    elif user_input.startswith('/brightness '):
                        try:
                            brightness = int(user_input[12:])
                            await client.send_text_message(f"请将屏幕亮度设置为{brightness}")
                        except ValueError:
                            print("Invalid brightness value")
                    elif user_input:
                        await client.send_text_message(user_input)
                        
                except KeyboardInterrupt:
                    break
                except EOFError:
                    break
            
            # Cancel listener task
            listener_task.cancel()
            
        else:
            logger.error("Failed to connect to server")
            
    except Exception as e:
        logger.error(f"Client error: {e}")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())