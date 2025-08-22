import asyncio
import json
import time
import traceback
from typing import Optional, Dict, Any
from config.logger import setup_logging
from core.connection import ConnectionHandler
from core.handle.gemini_realtime_handle import GeminiRealtimeHandler

TAG = __name__
logger = setup_logging()


class GeminiConnectionHandler(ConnectionHandler):
    """
    Extended connection handler for Gemini Real-time integration
    Combines Xiaozhi's existing architecture with Gemini's real-time capabilities
    """

    def __init__(self, config: dict, modules: dict, websocket=None, session_id: str = None):
        # Extract modules
        _vad = modules.get("vad")
        _asr = modules.get("asr") 
        _llm = modules.get("llm")
        _memory = modules.get("memory")
        _intent = modules.get("intent")
        
        # Initialize base ConnectionHandler with proper parameters
        super().__init__(config, _vad, _asr, _llm, _memory, _intent)
        
        # Override session_id if provided
        if session_id:
            self.session_id = session_id
        
        # Set websocket
        self.websocket = websocket
        
        # Gemini-specific configuration
        self.gemini_config = config.get("gemini_realtime_integration", {}).get("gemini_realtime", {})
        self.deepgram_config = config.get("gemini_realtime_integration", {}).get("deepgram_asr", {})
        
        # Real-time handler
        self.gemini_handler = None
        # Check if Gemini real-time integration is enabled
        integration_config = config.get("gemini_realtime_integration", {})
        self.use_gemini_realtime = integration_config.get("enabled", False)
        
        # Audio processing
        self.audio_chunks_received = 0
        self.last_audio_time = time.time()
        
        logger.bind(tag=TAG).info(
            f"GeminiConnectionHandler initialized - Realtime: {self.use_gemini_realtime}"
        )



    async def _initialize_gemini_realtime(self):
        """Initialize Gemini real-time handler"""
        try:
            self.gemini_handler = GeminiRealtimeHandler(
                conn=self,
                deepgram_config=self.deepgram_config,
                gemini_config=self.gemini_config
            )
            
            success = await self.gemini_handler.start()
            if success:
                logger.bind(tag=TAG).info("Gemini real-time handler started successfully")
            else:
                logger.bind(tag=TAG).error("Failed to start Gemini real-time handler")
                self.gemini_handler = None
                
        except Exception as e:
            logger.bind(tag=TAG).error(f"Error initializing Gemini real-time: {e}")
            self.gemini_handler = None

    async def handle_message(self, message):
        """Handle incoming WebSocket messages"""
        try:
            # Handle text messages (JSON)
            if isinstance(message, str):
                await self._handle_text_message(message)
            
            # Handle binary messages (audio)
            elif isinstance(message, bytes):
                await self._handle_audio_message(message)
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"Error handling message: {e}")
            traceback.print_exc()

    async def _handle_text_message(self, message: str):
        """Handle text messages from client"""
        try:
            data = json.loads(message)
            message_type = data.get("type", "unknown")
            
            logger.bind(tag=TAG).info(f"Received text message: {message_type}")
            
            if message_type == "hello":
                await self._handle_hello_message(data)
            elif message_type == "text":
                await self._handle_manual_text(data.get("content", ""))
            elif message_type == "control":
                await self._handle_control_message(data)
            else:
                # Handle unknown message types
                logger.bind(tag=TAG).warning(f"Unknown message type: {message_type}")
                await self.send_error("Unknown message type")
                
        except json.JSONDecodeError:
            logger.bind(tag=TAG).warning(f"Invalid JSON message: {message[:100]}")
        except Exception as e:
            logger.bind(tag=TAG).error(f"Error handling text message: {e}")

    async def _handle_audio_message(self, audio_data: bytes):
        """Handle audio messages from ESP32"""
        try:
            self.audio_chunks_received += 1
            self.last_audio_time = time.time()
            
            # Log every 100th chunk to avoid spam
            if self.audio_chunks_received % 100 == 0:
                logger.bind(tag=TAG).debug(
                    f"Audio chunks received: {self.audio_chunks_received}"
                )
            
            # If using Gemini real-time, process with hybrid handler
            if self.gemini_handler:
                # Simple voice activity detection (you can enhance this)
                has_voice = len(audio_data) > 100  # Basic threshold
                await self.gemini_handler.process_audio_chunk(audio_data, has_voice)
            else:
                # Standard processing not available in Gemini mode
                logger.bind(tag=TAG).warning("Audio received but Gemini handler not available")
                
        except Exception as e:
            logger.bind(tag=TAG).error(f"Error handling audio message: {e}")

    async def _handle_hello_message(self, data: dict):
        """Handle hello/handshake message"""
        try:
            logger.bind(tag=TAG).info("Received hello message")
            
            # Send hello response with capabilities
            response = {
                "type": "hello_response",
                "session_id": self.session_id,
                "capabilities": {
                    "gemini_realtime": self.use_gemini_realtime,
                    "deepgram_asr": bool(self.deepgram_config),
                    "audio_format": "opus",
                    "sample_rate": 16000,
                    "pipeline": "ESP32 → Deepgram ASR → Gemini LLM+TTS → ESP32"
                },
                "status": "ready"
            }
            
            await self.send_json(response)
            logger.bind(tag=TAG).info("Sent hello response - Real-time pipeline active")
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"Error handling hello message: {e}")

    async def _handle_manual_text(self, text: str):
        """Handle manual text input"""
        try:
            if self.gemini_handler:
                success = await self.gemini_handler.send_text_message(text)
                if success:
                    logger.bind(tag=TAG).info(f"Manual text processed: {text}")
                else:
                    await self.send_error("Failed to process text message")
            else:
                # Fallback to standard processing
                await self.send_error("Gemini real-time not available")
                
        except Exception as e:
            logger.bind(tag=TAG).error(f"Error handling manual text: {e}")

    async def _handle_control_message(self, data: dict):
        """Handle control messages"""
        try:
            command = data.get("command", "")
            
            if command == "status":
                status = self._get_status()
                await self.send_json({"type": "status", "data": status})
            
            elif command == "stop_audio":
                if self.gemini_handler:
                    # Clear audio buffers
                    self.gemini_handler.audio_buffer.clear()
                    logger.bind(tag=TAG).info("Audio buffers cleared")
            
            else:
                logger.bind(tag=TAG).warning(f"Unknown control command: {command}")
                
        except Exception as e:
            logger.bind(tag=TAG).error(f"Error handling control message: {e}")

    async def send_json(self, data: dict):
        """Send JSON message to client"""
        try:
            message = json.dumps(data)
            await self.websocket.send(message)
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"Error sending JSON: {e}")

    async def send_error(self, error_message: str):
        """Send error message to client"""
        try:
            error_data = {
                "type": "error",
                "message": error_message,
                "timestamp": time.time()
            }
            await self.send_json(error_data)
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"Error sending error message: {e}")

    def _get_status(self) -> dict:
        """Get connection status"""
        base_status = {
            "session_id": self.session_id,
            "connected": True,
            "audio_chunks_received": self.audio_chunks_received,
            "last_audio_time": self.last_audio_time,
            "gemini_realtime_enabled": self.use_gemini_realtime
        }
        
        if self.gemini_handler:
            gemini_status = self.gemini_handler.get_status()
            base_status.update({"gemini": gemini_status})
        
        return base_status

    async def cleanup(self):
        """Cleanup resources"""
        try:
            # Stop Gemini handler
            if self.gemini_handler:
                await self.gemini_handler.stop()
                self.gemini_handler = None

            # Call parent close method (base class uses 'close', not 'cleanup')
            await super().close(self.websocket)

            logger.bind(tag=TAG).info("Connection cleanup completed")

        except Exception as e:
            logger.bind(tag=TAG).error(f"Error during cleanup: {e}")

    async def __aenter__(self):
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()
        
    async def initialize(self):
        """Initialize the connection handler"""
        try:
            # Call parent initialization if it exists
            if hasattr(super(), 'initialize'):
                await super().initialize()
            
            # Initialize Gemini real-time if enabled
            if self.use_gemini_realtime:
                await self._initialize_gemini_realtime()
            
            return True
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"Error initializing connection: {e}")
            return False