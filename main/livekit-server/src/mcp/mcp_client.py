"""LiveKit MCP client for device communication"""

import logging
import json
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger("mcp_client")


class LiveKitMCPClient:
    """MCP client for LiveKit data channel communication"""

    def __init__(self):
        self.context = None
        self.is_connected = False
        self.audio_player = None
        self.unified_audio_player = None

    def set_context(self, context, audio_player=None, unified_audio_player=None):
        """Set the agent context for sending data channel messages"""
        self.context = context
        self.audio_player = audio_player
        self.unified_audio_player = unified_audio_player
        self.is_connected = True

    async def send_message(self, message_type: str, data: Dict[str, Any], topic: str = "mcp_function_call") -> Dict:
        """
        Send a message via LiveKit data channel

        Args:
            message_type: Type of message (e.g., 'function_call')
            data: Message data
            topic: LiveKit data channel topic

        Returns:
            Dict with the message that was sent
        """
        if not self.context:
            logger.error("MCP client context not available")
            raise Exception("MCP client not properly initialized")

        # Get room using the same pattern as working adjust_device_volume function
        room = None
        if hasattr(self.context, 'room'):
            room = self.context.room
            logger.info("Found room directly in context")
        elif self.unified_audio_player and hasattr(self.unified_audio_player, 'context') and self.unified_audio_player.context:
            room = self.unified_audio_player.context.room
            logger.info("Found room via unified_audio_player.context")
        elif self.audio_player and hasattr(self.audio_player, 'context') and self.audio_player.context:
            room = self.audio_player.context.room
            logger.info("Found room via audio_player.context")

        if not room:
            logger.error("Cannot access room for MCP communication")
            logger.error(f"Context type: {type(self.context)}")
            logger.error(f"Available context attributes: {[attr for attr in dir(self.context) if not attr.startswith('_')]}")
            raise Exception("MCP client cannot access room")

        message = {
            "type": message_type,
            **data,
            "timestamp": datetime.now().isoformat(),
            "request_id": f"req_{int(datetime.now().timestamp() * 1000)}"
        }

        try:
            await room.local_participant.publish_data(
                json.dumps(message).encode(),
                topic=topic,
                reliable=True
            )
            logger.info(f"Sent MCP message: {message_type} to topic: {topic}")
            return message

        except Exception as e:
            logger.error(f"Failed to send MCP message: {e}")
            raise

    async def send_function_call(self, function_name: str, arguments: Dict = None) -> Dict:
        """
        Send a function call message

        Args:
            function_name: The function name (e.g., 'self_set_volume')
            arguments: The function arguments dictionary

        Returns:
            Dict with the message that was sent
        """
        data = {
            "function_call": {
                "name": function_name,
                "arguments": arguments or {}
            }
        }

        return await self.send_message("function_call", data)

    def is_ready(self) -> bool:
        """Check if the MCP client is ready for communication"""
        return self.is_connected and self.context is not None

    def disconnect(self):
        """Disconnect the MCP client"""
        self.context = None
        self.is_connected = False
        logger.info("MCP client disconnected")