import os
import asyncio
import base64
import io
import traceback
import logging
from datetime import datetime
from typing import Optional, Dict, Any, AsyncGenerator
from config.logger import setup_logging
from core.providers.llm.base import LLMProviderBase

try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

TAG = __name__
logger = setup_logging()


class LLMProvider(LLMProviderBase):
    """
    Gemini Real-time LLM Provider with Audio Capabilities
    Integrates with Xiaozhi's Deepgram ASR while using Gemini for LLM and TTS
    """

    def __init__(self, config: dict):
        super().__init__()
        
        if not GEMINI_AVAILABLE:
            raise ImportError("Google Gemini SDK not available. Install with: pip install google-genai")
        
        self.api_key = config.get("api_key")
        self.model = config.get("model", "models/gemini-2.5-flash-preview-native-audio-dialog")
        self.voice_name = config.get("voice_name", "Zephyr")
        self.media_resolution = config.get("media_resolution", "MEDIA_RESOLUTION_MEDIUM")
        self.enable_audio_output = config.get("enable_audio_output", True)
        
        # Initialize Gemini client
        self.client = genai.Client(
            http_options={"api_version": "v1beta"},
            api_key=self.api_key,
        )
        
        # Configure Gemini Live settings
        self.config = types.LiveConnectConfig(
            response_modalities=["AUDIO"] if self.enable_audio_output else ["TEXT"],
            media_resolution=self.media_resolution,
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=self.voice_name
                    )
                )
            ),
            context_window_compression=types.ContextWindowCompressionConfig(
                trigger_tokens=25600,
                sliding_window=types.SlidingWindow(target_tokens=12800),
            ),
        )
        
        # Session management
        self.session = None
        self.connection_manager = None
        self.audio_queue = None
        self.is_connected = False
        self.audio_receiver_task = None
        
        logger.bind(tag=TAG).info(
            f"Gemini Real-time LLM initialized - Model: {self.model}, Voice: {self.voice_name}"
        )

    async def connect(self):
        """Establish connection to Gemini Live API"""
        try:
            if self.is_connected:
                return True
                
            # Create the connection context manager
            self.connection_manager = self.client.aio.live.connect(
                model=self.model, 
                config=self.config
            )
            
            # Enter the context manager
            self.session = await self.connection_manager.__aenter__()
            
            self.audio_queue = asyncio.Queue()
            self.is_connected = True

            # Start audio receiver task
            self.audio_receiver_task = asyncio.create_task(self._receive_audio())
            
            logger.bind(tag=TAG).info("Connected to Gemini Live API")
            return True
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"Failed to connect to Gemini: {e}")
            return False

    async def disconnect(self):
        """Disconnect from Gemini Live API"""
        try:
            # Set disconnected flag first to stop loops
            self.is_connected = False

            # Cancel audio receiver task
            if self.audio_receiver_task and not self.audio_receiver_task.done():
                self.audio_receiver_task.cancel()
                try:
                    await self.audio_receiver_task
                except asyncio.CancelledError:
                    pass
                self.audio_receiver_task = None

            # Close session
            if self.session and hasattr(self, 'connection_manager'):
                # Exit the context manager properly
                await self.connection_manager.__aexit__(None, None, None)
                self.session = None
                self.connection_manager = None

            logger.bind(tag=TAG).info("Disconnected from Gemini Live API")

        except Exception as e:
            logger.bind(tag=TAG).error(f"Error disconnecting from Gemini: {e}")

    async def _receive_audio(self):
        """Receive audio responses from Gemini"""
        try:
            while self.is_connected and self.session:
                try:
                    turn = self.session.receive()
                    async for response in turn:
                        # Check if we're still connected before processing
                        if not self.is_connected:
                            break

                        if data := response.data:
                            await self.audio_queue.put(data)
                            logger.bind(tag=TAG).debug(f"Received audio data: {len(data)} bytes")

                        if text := response.text:
                            logger.bind(tag=TAG).info(f"Gemini response text: {text}")

                except asyncio.CancelledError:
                    logger.bind(tag=TAG).info("Audio receiver task cancelled")
                    break
                except Exception as turn_error:
                    logger.bind(tag=TAG).error(f"Error in receive turn: {turn_error}")
                    # Break the loop on connection errors
                    if "websocket" in str(turn_error).lower() or "connection" in str(turn_error).lower():
                        break
                    # For other errors, continue trying
                    await asyncio.sleep(1)

        except Exception as e:
            logger.bind(tag=TAG).error(f"Error receiving audio from Gemini: {e}")
        finally:
            logger.bind(tag=TAG).info("Audio receiver task ended")

    async def get_audio_response(self) -> Optional[bytes]:
        """Get next audio chunk from Gemini"""
        try:
            if not self.audio_queue:
                return None
                
            # Wait for audio with timeout
            audio_data = await asyncio.wait_for(self.audio_queue.get(), timeout=5.0)
            return audio_data
            
        except asyncio.TimeoutError:
            return None
        except Exception as e:
            logger.bind(tag=TAG).error(f"Error getting audio response: {e}")
            return None

    async def send_text_message(self, text: str, end_of_turn: bool = True) -> bool:
        """Send text message to Gemini"""
        try:
            if not self.is_connected or not self.session:
                await self.connect()
            
            await self.session.send(input=text, end_of_turn=end_of_turn)
            logger.bind(tag=TAG).info(f"Sent text to Gemini: {text[:100]}...")
            return True
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"Error sending text to Gemini: {e}")
            return False

    async def send_audio_chunk(self, audio_data: bytes) -> bool:
        """Send audio chunk to Gemini (for context, not ASR)"""
        try:
            if not self.is_connected or not self.session:
                await self.connect()
            
            audio_msg = {
                "data": audio_data,
                "mime_type": "audio/pcm"
            }
            
            await self.session.send(input=audio_msg)
            logger.bind(tag=TAG).debug(f"Sent audio chunk: {len(audio_data)} bytes")
            return True
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"Error sending audio to Gemini: {e}")
            return False

    # Required abstract method from base class
    def response(self, session_id, dialogue, **kwargs):
        """
        Standard LLM response method (required by base class)
        This is a synchronous wrapper around the async methods
        """
        try:
            # Extract the last user message
            user_message = ""
            for msg in reversed(dialogue):
                if msg.get("role") == "user":
                    user_message = msg.get("content", "")
                    break
            
            if not user_message:
                yield "No user message found"
                return
            
            # Run async method in sync context
            import asyncio
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Use the async text_chat method
            result = loop.run_until_complete(self.text_chat(dialogue, **kwargs))
            
            # Yield the result as a generator
            if result:
                yield result
            else:
                yield "No response received"
                
        except Exception as e:
            logger.bind(tag=TAG).error(f"Error in response method: {e}")
            yield f"Error: {str(e)}"

    def response_with_functions(self, session_id, dialogue, functions=None):
        """
        Function calling support (required by base class)
        For now, this just calls the regular response method
        """
        try:
            for text_chunk in self.response(session_id, dialogue):
                yield text_chunk, None  # No function calls for now
        except Exception as e:
            logger.bind(tag=TAG).error(f"Error in response_with_functions: {e}")
            yield f"Error: {str(e)}", None

    # Standard LLM interface methods
    async def text_chat(self, messages, **kwargs) -> str:
        """Standard text chat interface for compatibility"""
        try:
            # Extract the last user message
            user_message = ""
            for msg in reversed(messages):
                if msg.get("role") == "user":
                    user_message = msg.get("content", "")
                    break
            
            if not user_message:
                return "No user message found"
            
            # Connect if needed
            if not self.is_connected:
                await self.connect()
            
            # Send message
            await self.send_text_message(user_message)
            
            # For text-only mode, we need to collect the response
            # This is a simplified implementation
            response_text = ""
            try:
                turn = self.session.receive()
                async for response in turn:
                    if text := response.text:
                        response_text += text
                        
                return response_text or "No response received"
                
            except Exception as e:
                logger.bind(tag=TAG).error(f"Error receiving text response: {e}")
                return "Error receiving response"
                
        except Exception as e:
            logger.bind(tag=TAG).error(f"Error in text_chat: {e}")
            return f"Error: {str(e)}"

    async def stream_chat(self, messages, **kwargs) -> AsyncGenerator[str, None]:
        """Streaming chat interface"""
        try:
            # Extract the last user message
            user_message = ""
            for msg in reversed(messages):
                if msg.get("role") == "user":
                    user_message = msg.get("content", "")
                    break
            
            if not user_message:
                yield "No user message found"
                return
            
            # Connect if needed
            if not self.is_connected:
                await self.connect()
            
            # Send message
            await self.send_text_message(user_message)
            
            # Stream response
            turn = self.session.receive()
            async for response in turn:
                if text := response.text:
                    yield text
                    
        except Exception as e:
            logger.bind(tag=TAG).error(f"Error in stream_chat: {e}")
            yield f"Error: {str(e)}"

    def __del__(self):
        """Cleanup on destruction"""
        if self.is_connected:
            try:
                asyncio.create_task(self.disconnect())
            except:
                pass