#!/usr/bin/env python3
"""
Test WebSocket conversation to trigger Langfuse logging
"""

import asyncio
import websockets
import json

async def test_conversation():
    """Test a simple conversation to trigger Langfuse logs"""
    
    uri = "ws://192.168.1.77:8000/toy/v1/"
    
    try:
        print(f"[TEST] Connecting to {uri}...")
        
        # Connect with headers similar to what the device would send
        headers = {
            "device-id": "test-device-123",
            "client-id": "test-client-123"
        }
        
        async with websockets.connect(uri, extra_headers=headers) as websocket:
            print("[SUCCESS] Connected to WebSocket!")
            
            # Send a message to trigger LLM conversation (using correct format)
            test_message = {
                "type": "listen",
                "state": "detect",
                "text": "Hello, how are you today?"
            }
            
            print(f"[SEND] Sending message: {test_message}")
            await websocket.send(json.dumps(test_message))
            
            # Wait for responses
            print("[WAIT] Waiting for responses...")
            
            timeout_counter = 0
            while timeout_counter < 10:  # Wait up to 10 seconds
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    print(f"[RECV] {response}")
                except asyncio.TimeoutError:
                    timeout_counter += 1
                    print(f"[TIMEOUT] Waiting... ({timeout_counter}/10)")
                    continue
                
                # If we get a response, reset timeout
                timeout_counter = 0
            
            print("[COMPLETE] Test conversation finished")
            
    except Exception as e:
        print(f"[ERROR] Connection failed: {e}")
        print("[INFO] Make sure the server is running and accessible")

if __name__ == "__main__":
    print("[TEST] WebSocket Conversation Test")
    print("=" * 40)
    print("This will trigger conversation logs including Langfuse tracking")
    print()
    
    asyncio.run(test_conversation())
    
    print()
    print("[INFO] Check server logs for:")
    print("  [WEBSOCKET] NEW CONNECTION")
    print("  [CONNECTION] STARTING HANDLER") 
    print("  [CONVERSATION] STARTED")
    print("  [LLM] SENDING TO LLM")
    print("  [LLM] CHAT STARTED")
    print("  [INFO] OpenAI LLM response call")
    print("  [INFO] Langfuse generation started")
    print("  [CONNECTION] CLOSED")