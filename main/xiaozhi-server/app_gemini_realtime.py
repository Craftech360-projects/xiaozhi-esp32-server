#!/usr/bin/env python3
"""
Xiaozhi WebSocket Server with Gemini Real-time Integration
Modified version of app.py that uses GeminiConnectionHandler for real-time audio processing
"""

import asyncio
import websockets
import json
import uuid
import traceback
from datetime import datetime
from config.logger import setup_logging
from config.settings import load_config
from core.connection_gemini import GeminiConnectionHandler
from core.utils.modules_initialize import initialize_modules

TAG = __name__
logger = setup_logging()


class GeminiRealtimeServer:
    """WebSocket server with Gemini real-time capabilities"""
    
    def __init__(self, config):
        self.config = config
        self.server_config = config.get("server", {})
        self.host = self.server_config.get("ip", "0.0.0.0")
        # Force port 8002 for Gemini real-time server to avoid conflict with standard server
        self.port = 8002
        
        # Initialize modules
        self.modules = initialize_modules(
            logger,
            config,
            "VAD" in config["selected_module"],
            "ASR" in config["selected_module"], 
            "LLM" in config["selected_module"],
            False,  # TTS not needed for Gemini real-time
            "Memory" in config["selected_module"],
            "Intent" in config["selected_module"],
        )
        
        # Active connections
        self.connections = {}
        
        logger.bind(tag=TAG).info(
            f"Gemini Real-time Server initialized - Host: {self.host}, Port: {self.port}"
        )

    async def handle_connection(self, websocket, path=None):
        """Handle new WebSocket connection with Gemini real-time capabilities"""
        session_id = str(uuid.uuid4())
        client_ip = websocket.remote_address[0] if websocket.remote_address else "unknown"
        
        logger.bind(tag=TAG).info(
            f"New connection - Session: {session_id}, IP: {client_ip}, Path: {path}"
        )
        
        try:
            # Create Gemini-enabled connection handler
            handler = GeminiConnectionHandler(self.config, self.modules, websocket, session_id)
            async with handler:
                # Store connection
                self.connections[session_id] = {
                    "handler": handler,
                    "websocket": websocket,
                    "client_ip": client_ip,
                    "connected_at": datetime.now(),
                    "path": path
                }
                
                logger.bind(tag=TAG).info(
                    f"Gemini real-time handler created for session: {session_id}"
                )
                
                # Handle messages
                await self.handle_messages(handler, websocket, session_id)
                
        except websockets.exceptions.ConnectionClosed:
            logger.bind(tag=TAG).info(f"Connection closed - Session: {session_id}")
        except Exception as e:
            logger.bind(tag=TAG).error(
                f"Error handling connection {session_id}: {e}"
            )
            traceback.print_exc()
        finally:
            # Clean up connection
            if session_id in self.connections:
                del self.connections[session_id]
            logger.bind(tag=TAG).info(f"Connection cleanup completed - Session: {session_id}")

    async def handle_messages(self, handler, websocket, session_id):
        """Handle incoming WebSocket messages"""
        try:
            async for message in websocket:
                try:
                    # Handle both text and binary messages
                    await handler.handle_message(message)
                    
                except json.JSONDecodeError as e:
                    logger.bind(tag=TAG).warning(
                        f"Invalid JSON from {session_id}: {e}"
                    )
                    await self.send_error(websocket, "Invalid JSON format")
                    
                except Exception as e:
                    logger.bind(tag=TAG).error(
                        f"Error processing message from {session_id}: {e}"
                    )
                    await self.send_error(websocket, "Message processing error")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.bind(tag=TAG).info(f"WebSocket connection closed - Session: {session_id}")
        except Exception as e:
            logger.bind(tag=TAG).error(f"Error in message handling for {session_id}: {e}")

    async def send_error(self, websocket, error_message):
        """Send error message to client"""
        try:
            error_response = {
                "type": "error",
                "message": error_message,
                "timestamp": datetime.now().isoformat()
            }
            await websocket.send(json.dumps(error_response))
        except Exception as e:
            logger.bind(tag=TAG).error(f"Failed to send error message: {e}")

    def get_server_status(self):
        """Get server status information"""
        return {
            "server_type": "gemini_realtime",
            "host": self.host,
            "port": self.port,
            "active_connections": len(self.connections),
            "connections": {
                session_id: {
                    "client_ip": conn["client_ip"],
                    "connected_at": conn["connected_at"].isoformat(),
                    "path": conn["path"]
                }
                for session_id, conn in self.connections.items()
            }
        }

    async def start_server(self):
        """Start the WebSocket server"""
        try:
            logger.bind(tag=TAG).info(
                f"Starting Gemini Real-time WebSocket server on {self.host}:{self.port}"
            )
            
            # Start WebSocket server
            async def connection_handler(websocket):
                # Extract path from websocket.path if needed
                path = getattr(websocket, 'path', '/xiaozhi/v1/')
                await self.handle_connection(websocket, path)
            
            server = await websockets.serve(
                connection_handler,
                self.host,
                self.port,
                ping_interval=30,
                ping_timeout=10,
                close_timeout=10
            )
            
            logger.bind(tag=TAG).info(
                f"🚀 Gemini Real-time Server started successfully!"
            )
            logger.bind(tag=TAG).info(
                f"📡 WebSocket endpoint: ws://{self.host}:{self.port}/xiaozhi/v1/"
            )
            logger.bind(tag=TAG).info(
                f"🎤 Audio pipeline: ESP32 → Deepgram ASR → Gemini LLM+TTS → ESP32"
            )
            
            # Keep server running
            await server.wait_closed()
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"Failed to start server: {e}")
            raise


async def main():
    """Main entry point"""
    try:
        # Load configuration
        config = load_config()
        
        # Check if Gemini real-time integration is enabled
        gemini_config = config.get("gemini_realtime_integration", {})
        if not gemini_config.get("enabled", False):
            logger.bind(tag=TAG).warning(
                "Gemini real-time integration is disabled in configuration"
            )
            logger.bind(tag=TAG).info(
                "To enable: set gemini_realtime_integration.enabled = true in config"
            )
            return
        
        # Validate API keys
        deepgram_key = gemini_config.get("deepgram_asr", {}).get("api_key")
        gemini_key = gemini_config.get("gemini_realtime", {}).get("api_key")
        
        if not deepgram_key or deepgram_key == "your-deepgram-api-key":
            logger.bind(tag=TAG).error("Deepgram API key not configured")
            return
            
        if not gemini_key or gemini_key == "your-gemini-api-key-here":
            logger.bind(tag=TAG).error("Gemini API key not configured")
            return
        
        logger.bind(tag=TAG).info("✅ API keys validated")
        logger.bind(tag=TAG).info("✅ Gemini real-time integration enabled")
        
        # Create and start server
        server = GeminiRealtimeServer(config)
        await server.start_server()
        
    except KeyboardInterrupt:
        logger.bind(tag=TAG).info("Server shutdown requested")
    except Exception as e:
        logger.bind(tag=TAG).error(f"Server error: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    print("🎯 Xiaozhi Gemini Real-time Server")
    print("=" * 50)
    print("Audio Pipeline: ESP32 → Deepgram ASR → Gemini LLM+TTS → ESP32")
    print("Real-time streaming audio with low latency")
    print("=" * 50)
    
    asyncio.run(main())