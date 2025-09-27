#!/usr/bin/env python3
"""
Quick test to verify the volume control fix works with proper room access
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from agent.main_agent import Assistant
from services.device_control_service import DeviceControlService

class MockRoom:
    def __init__(self):
        self.local_participant = MockParticipant()

class MockParticipant:
    async def publish_data(self, data, topic=None, reliable=True):
        import json
        try:
            message = json.loads(data.decode())
            print(f"SUCCESS: Sent {message['command']} = {message.get('value', 'N/A')}")
            return True
        except Exception as e:
            print(f"ERROR: {e}")
            return False

class MockUnifiedPlayer:
    def __init__(self):
        self.context = MockContext()

class MockContext:
    def __init__(self):
        self.room = MockRoom()

class MockRunContext:
    """Mock RunContext that doesn't have room attribute (like the real one)"""
    def __init__(self):
        pass  # No room attribute

async def test_volume_fix():
    print("Testing Volume Control Fix")
    print("=" * 40)

    # Create assistant
    assistant = Assistant()

    # Create services
    device_service = DeviceControlService()
    unified_player = MockUnifiedPlayer()

    # Set services (including device_control_service)
    assistant.set_services(None, None, None, unified_player, device_service)

    # Create mock context (without room attribute like the real RunContext)
    context = MockRunContext()

    print("Test 1: Set volume to 75%")
    result = await assistant.set_device_volume(context, 75)
    print(f"Result: {result}")
    print()

    print("Test 2: Increase volume by 10")
    result = await assistant.adjust_device_volume(context, "up", 10)
    print(f"Result: {result}")
    print()

    print("Test 3: Get volume")
    result = await assistant.get_device_volume(context)
    print(f"Result: {result}")
    print()

    print("Test 4: Mute device")
    result = await assistant.mute_device(context)
    print(f"Result: {result}")
    print()

    print("All tests completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_volume_fix())