"""LiveKit MCP tool executor"""

import logging
from typing import Dict, Any, Optional
from .mcp_client import LiveKitMCPClient
from .mcp_handler import (
    handle_volume_set,
    handle_volume_adjust,
    handle_volume_get,
    handle_volume_mute,
)

logger = logging.getLogger("mcp_executor")


class LiveKitMCPExecutor:
    """Executor for MCP tools via LiveKit data channel"""

    def __init__(self):
        self.mcp_client = LiveKitMCPClient()
        self._volume_cache: Optional[int] = None

    def set_context(self, context, audio_player=None, unified_audio_player=None):
        """Set the agent context for MCP communication"""
        self.mcp_client.set_context(context, audio_player, unified_audio_player)

    def is_ready(self) -> bool:
        """Check if the executor is ready"""
        return self.mcp_client.is_ready()

    # Volume Control Methods
    async def set_volume(self, volume: int) -> str:
        """
        Set device volume to a specific level

        Args:
            volume: Volume level (0-100)

        Returns:
            Status message for user feedback
        """
        try:
            # Validate volume level
            if not isinstance(volume, int) or volume < 0 or volume > 100:
                return "Volume level must be between 0 and 100."

            await handle_volume_set(self.mcp_client, volume)
            self._volume_cache = volume

            # Return appropriate response based on level
            if volume == 0:
                return "Volume set to mute."
            elif volume <= 30:
                return f"Volume set to {volume}% (low)."
            elif volume <= 70:
                return f"Volume set to {volume}% (medium)."
            else:
                return f"Volume set to {volume}% (high)."

        except Exception as e:
            logger.error(f"Error setting volume: {e}")
            return "Sorry, I couldn't adjust the volume right now."

    async def adjust_volume(self, action: str, step: int = 10) -> str:
        """
        Adjust device volume up or down

        Args:
            action: 'up'/'increase' or 'down'/'decrease'
            step: Volume adjustment step (default 10)

        Returns:
            Status message for user feedback
        """
        try:
            # Validate action
            if action.lower() not in ["up", "increase", "down", "decrease"]:
                return "Please specify 'up' or 'down' to adjust the volume."

            # Validate step
            if not isinstance(step, int) or step < 1 or step > 50:
                return "Step must be between 1 and 50."

            await handle_volume_adjust(self.mcp_client, action, step)

            # Calculate estimated new volume if we have cached value
            if self._volume_cache is not None:
                if action.lower() in ["up", "increase"]:
                    new_level = min(100, self._volume_cache + step)
                    self._volume_cache = new_level
                    return f"Volume increased to {new_level}%."
                else:
                    new_level = max(0, self._volume_cache - step)
                    self._volume_cache = new_level
                    if new_level == 0:
                        return "Volume muted."
                    else:
                        return f"Volume decreased to {new_level}%."
            else:
                action_word = "increased" if action.lower() in ["up", "increase"] else "decreased"
                return f"Volume {action_word} by {step}%."

        except Exception as e:
            logger.error(f"Error adjusting volume: {e}")
            return "Sorry, I couldn't adjust the volume right now."

    async def get_volume(self) -> str:
        """
        Get current device volume level

        Returns:
            Current volume status message
        """
        try:
            await handle_volume_get(self.mcp_client)

            # Return cached volume if available, otherwise indicate we're checking
            if self._volume_cache is not None:
                return f"Current volume is {self._volume_cache}%."
            else:
                return "Checking current volume level..."

        except Exception as e:
            logger.error(f"Error getting volume: {e}")
            return "Sorry, I couldn't check the volume right now."

    async def mute_device(self) -> str:
        """
        Mute the device (set volume to 0)

        Returns:
            Status message for user feedback
        """
        try:
            await handle_volume_mute(self.mcp_client, mute=True)
            self._volume_cache = 0
            return "Device muted."

        except Exception as e:
            logger.error(f"Error muting device: {e}")
            return "Sorry, I couldn't mute the device right now."

    async def unmute_device(self, level: int = 50) -> str:
        """
        Unmute the device and set volume to specified level

        Args:
            level: Volume level to restore (default 50)

        Returns:
            Status message for user feedback
        """
        try:
            # Validate level
            if not isinstance(level, int) or level < 1 or level > 100:
                level = 50  # Default to 50 if invalid

            await handle_volume_mute(self.mcp_client, mute=False)
            self._volume_cache = level
            return f"Device unmuted and volume set to {level}%."

        except Exception as e:
            logger.error(f"Error unmuting device: {e}")
            return "Sorry, I couldn't unmute the device right now."

    # Cache Management
    def update_volume_cache(self, level: int):
        """
        Update the cached volume level

        Args:
            level: Current volume level from device
        """
        if isinstance(level, int) and 0 <= level <= 100:
            self._volume_cache = level
            logger.info(f"Updated volume cache: {level}%")

    def get_cached_volume(self) -> Optional[int]:
        """
        Get the cached volume level

        Returns:
            Cached volume level or None if not available
        """
        return self._volume_cache

    # Generic Tool Execution
    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> str:
        """
        Execute a generic MCP tool

        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments

        Returns:
            Execution result message
        """
        try:
            await self.mcp_client.send_function_call(tool_name, arguments)
            return f"Tool '{tool_name}' executed successfully."

        except Exception as e:
            logger.error(f"Error executing tool '{tool_name}': {e}")
            return f"Sorry, I couldn't execute the tool '{tool_name}' right now."