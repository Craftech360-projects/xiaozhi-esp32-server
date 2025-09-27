#!/usr/bin/env python3
"""
Test script to verify the updated message format matches xiaozhi-server format
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
            print(f"SUCCESS: Message format sent via data channel:")
            print(f"Topic: {topic}")
            print(f"Message: {json.dumps(message, indent=2)}")
            print(f"Expected xiaozhi-server format: ✓ type, ✓ action, ✓ session_id")

            # Verify the format matches xiaozhi-server pattern
            if message.get('type') == 'device_control' and 'action' in message and 'session_id' in message:
                print("✅ Format is compatible with xiaozhi-server!")
            else:
                print("❌ Format does NOT match xiaozhi-server pattern")
            print("-" * 60)
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
        pass

async def test_xiaozhi_format():
    print("Testing Volume Control - xiaozhi-server Compatible Format")
    print("=" * 70)

    # Create assistant
    assistant = Assistant()

    # Create services
    device_service = DeviceControlService()
    unified_player = MockUnifiedPlayer()

    # Set services
    assistant.set_services(None, None, None, unified_player, device_service)

    # Create mock context
    context = MockRunContext()

    print("Test 1: Set volume to 75% - xiaozhi format")
    result = await assistant.set_device_volume(context, 75)
    print(f"Result: {result}")
    print()

    print("Test 2: Volume up by 15% - xiaozhi format")
    result = await assistant.adjust_device_volume(context, "up", 15)
    print(f"Result: {result}")
    print()

    print("Test 3: Volume down by 5% - xiaozhi format")
    result = await assistant.adjust_device_volume(context, "down", 5)
    print(f"Result: {result}")
    print()

    print("Test 4: Get volume - xiaozhi format")
    result = await assistant.get_device_volume(context)
    print(f"Result: {result}")
    print()

    print("Expected xiaozhi-server message format for devices:")
    print(json.dumps({
        "type": "device_control",
        "action": "set_volume",
        "volume": 75,
        "session_id": "session_id"
    }, indent=2))
    print()

    print("✅ All tests completed! The format should now be compatible with xiaozhi-server.")

if __name__ == "__main__":
    import json
    asyncio.run(test_xiaozhi_format())