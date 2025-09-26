#!/usr/bin/env python3
"""
Test script for volume control implementation
This script tests the DeviceControlService functionality
"""

import asyncio
import logging
import sys
import os

# Add the src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services.device_control_service import DeviceControlService

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("volume_test")

class MockContext:
    """Mock context for testing"""
    def __init__(self):
        self.room = MockRoom()

class MockRoom:
    """Mock room for testing"""
    def __init__(self):
        self.local_participant = MockParticipant()

class MockParticipant:
    """Mock participant for testing"""
    async def publish_data(self, data, topic=None, reliable=True):
        """Mock publish_data method"""
        import json
        try:
            message = json.loads(data.decode())
            print(f"[MOCK DATA CHANNEL] Topic: {topic}, Message: {message}")
            return True
        except Exception as e:
            print(f"[MOCK ERROR] Failed to decode data: {e}")
            return False

async def test_volume_control():
    """Test the volume control service"""

    print("Starting Volume Control Test")
    print("=" * 50)

    # Create device control service
    device_service = DeviceControlService()

    # Create mock context
    context = MockContext()
    device_service.set_context(context)

    print("Device control service initialized with mock context")
    print()

    # Test 1: Set volume to 50%
    print("Test 1: Set volume to 50%")
    result = await device_service.set_volume(50)
    print(f"Result: {result}")
    print()

    # Test 2: Volume up
    print("Test 2: Increase volume by 10%")
    result = await device_service.volume_up(10)
    print(f"Result: {result}")
    print()

    # Test 3: Volume down
    print("Test 3: Decrease volume by 5%")
    result = await device_service.volume_down(5)
    print(f"Result: {result}")
    print()

    # Test 4: Get volume
    print("Test 4: Get current volume")
    result = await device_service.get_volume()
    print(f"Result: {result}")
    print()

    # Test 5: Mute device
    print("Test 5: Mute device")
    result = await device_service.mute()
    print(f"Result: {result}")
    print()

    # Test 6: Unmute device
    print("Test 6: Unmute device to 60%")
    result = await device_service.unmute(60)
    print(f"Result: {result}")
    print()

    # Test 7: Invalid volume (should handle gracefully)
    print("Test 7: Set invalid volume (150%)")
    result = await device_service.set_volume(150)
    print(f"Result: {result}")
    print()

    # Test 8: Test volume cache
    print("Test 8: Test volume cache functionality")
    device_service.update_volume_cache(75)
    cached_volume = device_service.get_cached_volume()
    print(f"Cached volume: {cached_volume}%")
    print()

    print("Volume Control Test Complete!")
    print("=" * 50)

async def test_error_handling():
    """Test error handling without context"""

    print("Testing Error Handling (No Context)")
    print("=" * 30)

    # Create service without context
    device_service = DeviceControlService()

    try:
        result = await device_service.set_volume(50)
        print(f"Result: {result}")
    except Exception as e:
        print(f"Expected error caught: {e}")

    print()

if __name__ == "__main__":
    print("Volume Control Implementation Test")
    print("=====================================")
    print()

    async def main():
        await test_volume_control()
        await test_error_handling()

        print("All tests completed!")
        print()
        print("Integration Test Instructions:")
        print("1. Start the LiveKit server: python main.py")
        print("2. Connect a device via MQTT gateway")
        print("3. Use voice commands like:")
        print("   - 'Set volume to 70%'")
        print("   - 'Increase volume'")
        print("   - 'Decrease volume by 5'")
        print("   - 'What's the current volume?'")
        print("   - 'Mute the device'")
        print("   - 'Unmute'")

    # Run the test
    asyncio.run(main())