"""MCP message handling and protocol utilities"""

import logging
import json
from typing import Dict, Any
from datetime import datetime
from .mcp_client import LiveKitMCPClient

logger = logging.getLogger("mcp_handler")


async def send_mcp_function_call(
    mcp_client: LiveKitMCPClient,
    function_name: str,
    arguments: Dict[str, Any] = None
) -> Dict:
    """
    Send an MCP function call using the provided client

    Args:
        mcp_client: The MCP client instance
        function_name: Name of the function to call
        arguments: Function arguments

    Returns:
        Dict with the message that was sent
    """
    if not mcp_client.is_ready():
        raise Exception("MCP client is not ready")

    return await mcp_client.send_function_call(function_name, arguments)


def format_mcp_message(message_type: str, data: Dict[str, Any]) -> Dict:
    """
    Format a message for MCP protocol

    Args:
        message_type: Type of message
        data: Message data

    Returns:
        Formatted MCP message
    """
    return {
        "type": message_type,
        **data,
        "timestamp": datetime.now().isoformat(),
        "request_id": f"req_{int(datetime.now().timestamp() * 1000)}"
    }


def create_function_call_message(function_name: str, arguments: Dict[str, Any] = None) -> Dict:
    """
    Create a function call message

    Args:
        function_name: Name of the function
        arguments: Function arguments

    Returns:
        Function call message dict
    """
    return format_mcp_message("function_call", {
        "function_call": {
            "name": function_name,
            "arguments": arguments or {}
        }
    })


def validate_function_call(function_name: str, arguments: Dict[str, Any] = None) -> bool:
    """
    Validate a function call

    Args:
        function_name: Name of the function
        arguments: Function arguments

    Returns:
        True if valid, False otherwise
    """
    if not function_name or not isinstance(function_name, str):
        logger.error("Invalid function name")
        return False

    if arguments is not None and not isinstance(arguments, dict):
        logger.error("Arguments must be a dictionary")
        return False

    return True


# Volume control specific handlers
async def handle_volume_set(mcp_client: LiveKitMCPClient, volume: int) -> Dict:
    """Handle set volume command"""
    if not validate_function_call("self_set_volume", {"volume": volume}):
        raise ValueError("Invalid volume set parameters")

    if not isinstance(volume, int) or volume < 0 or volume > 100:
        raise ValueError("Volume must be between 0 and 100")

    return await send_mcp_function_call(mcp_client, "self_set_volume", {"volume": volume})


async def handle_volume_adjust(mcp_client: LiveKitMCPClient, action: str, step: int = 10) -> Dict:
    """Handle volume up/down command"""
    function_name = "self_volume_up" if action.lower() in ["up", "increase"] else "self_volume_down"

    if not validate_function_call(function_name, {"step": step}):
        raise ValueError("Invalid volume adjust parameters")

    return await send_mcp_function_call(mcp_client, function_name, {"step": step})


async def handle_volume_get(mcp_client: LiveKitMCPClient) -> Dict:
    """Handle get volume command"""
    if not validate_function_call("self_get_volume"):
        raise ValueError("Invalid get volume parameters")

    return await send_mcp_function_call(mcp_client, "self_get_volume")


async def handle_volume_mute(mcp_client: LiveKitMCPClient, mute: bool = True) -> Dict:
    """Handle mute/unmute command"""
    function_name = "self_mute" if mute else "self_unmute"

    if not validate_function_call(function_name):
        raise ValueError("Invalid mute/unmute parameters")

    return await send_mcp_function_call(mcp_client, function_name)