#!/usr/bin/env python3
"""
Simple test script for XiaoZhi client
"""

import asyncio
from xiaozhi_client import XiaoZhiClient

async def test_client():
    """Test the XiaoZhi client with a simple conversation"""
    client = XiaoZhiClient(
        server_url="ws://127.0.0.1:8000/xiaozhi/v1",
        device_name="Test Client",
        enable_audio=True  # Enable audio playback
    )
    
    try:
        print("🔌 Connecting to XiaoZhi server...")
        if await client.connect():
            print("✅ Connected successfully!")
            
            # Start listening for responses
            listener_task = asyncio.create_task(client.listen_for_messages())
            
            # Test messages
            test_messages = [
                "你好小智",
                "今天天气怎么样？",
                "请将音量设置为80"
            ]
            
            for i, message in enumerate(test_messages, 1):
                print(f"\n📤 [{i}] Sending: {message}")
                await client.send_text_message(message)
                print("⏳ Waiting for response...")
                await asyncio.sleep(4)  # Wait for response
            
            print("\n✅ Test completed!")
            await asyncio.sleep(2)  # Final wait
            
            # Clean up
            listener_task.cancel()
            
        else:
            print("❌ Failed to connect to server")
            
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await client.disconnect()
        print("👋 Disconnected")

if __name__ == "__main__":
    print("🤖 XiaoZhi Client Test")
    print("=" * 30)
    asyncio.run(test_client())