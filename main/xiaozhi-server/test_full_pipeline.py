#!/usr/bin/env python3
"""
Test script for the complete real-time pipeline:
ESP32 → Deepgram ASR → Gemini LLM+TTS → ESP32
"""

import asyncio
import websockets
import json
import time
import wave
import os
from pathlib import Path

# Mock audio data for testing
def create_mock_audio_chunks():
    """Create mock audio chunks to simulate ESP32 audio input"""
    # Create a simple sine wave as mock audio
    import numpy as np
    
    sample_rate = 16000
    duration = 3  # 3 seconds
    frequency = 440  # A4 note
    
    # Generate sine wave
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    audio_data = np.sin(2 * np.pi * frequency * t)
    
    # Convert to 16-bit PCM
    audio_data = (audio_data * 32767).astype(np.int16)
    
    # Split into chunks (60ms each, like ESP32)
    chunk_size = int(sample_rate * 0.06)  # 60ms chunks
    chunks = []
    
    for i in range(0, len(audio_data), chunk_size):
        chunk = audio_data[i:i + chunk_size]
        chunks.append(chunk.tobytes())
    
    return chunks


async def test_full_pipeline():
    """Test the complete real-time audio pipeline"""
    
    print("🚀 Testing Full Real-time Pipeline")
    print("=" * 60)
    print("Pipeline: ESP32 → Deepgram ASR → Gemini LLM+TTS → ESP32")
    print("=" * 60)
    
    # Server configuration
    server_host = "localhost"
    server_port = 8000
    websocket_url = f"ws://{server_host}:{server_port}/xiaozhi/v1/"
    
    try:
        print(f"🔗 Connecting to: {websocket_url}")
        
        # Connect to WebSocket server
        async with websockets.connect(websocket_url) as websocket:
            print("✅ Connected to Xiaozhi Gemini Real-time Server")
            
            # Send hello message
            hello_message = {
                "type": "hello",
                "client_type": "test_client",
                "audio_format": "pcm",
                "sample_rate": 16000,
                "timestamp": time.time()
            }
            
            await websocket.send(json.dumps(hello_message))
            print("📤 Sent hello message")
            
            # Wait for hello response
            response = await websocket.recv()
            hello_response = json.loads(response)
            
            print("📥 Received hello response:")
            print(f"   Session ID: {hello_response.get('session_id')}")
            print(f"   Pipeline: {hello_response.get('capabilities', {}).get('pipeline')}")
            print(f"   Gemini Real-time: {hello_response.get('capabilities', {}).get('gemini_realtime')}")
            
            # Test 1: Send text message
            print("\n🔤 Testing text message...")
            text_message = {
                "type": "text",
                "content": "Hello Cheeko! Can you tell me a short story about a friendly robot?"
            }
            
            await websocket.send(json.dumps(text_message))
            print("📤 Sent text message")
            
            # Listen for responses
            audio_chunks_received = 0
            start_time = time.time()
            
            print("👂 Listening for Gemini audio response...")
            
            try:
                while time.time() - start_time < 10:  # Listen for 10 seconds
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                        
                        if isinstance(response, bytes):
                            # Audio response from Gemini
                            audio_chunks_received += 1
                            if audio_chunks_received == 1:
                                print("🔊 Receiving audio response from Gemini...")
                            
                            if audio_chunks_received % 10 == 0:
                                print(f"   Received {audio_chunks_received} audio chunks...")
                                
                        elif isinstance(response, str):
                            # Text response
                            try:
                                msg = json.loads(response)
                                if msg.get("type") == "status":
                                    print(f"📊 Status: {msg.get('data', {})}")
                                elif msg.get("type") == "error":
                                    print(f"❌ Error: {msg.get('message')}")
                                else:
                                    print(f"📥 Message: {msg}")
                            except json.JSONDecodeError:
                                print(f"📥 Raw response: {response[:100]}...")
                                
                    except asyncio.TimeoutError:
                        continue
                        
            except Exception as e:
                print(f"⚠️  Response listening error: {e}")
            
            if audio_chunks_received > 0:
                print(f"✅ Received {audio_chunks_received} audio chunks from Gemini TTS")
                print("🎉 Full pipeline test successful!")
            else:
                print("⚠️  No audio chunks received - check Gemini configuration")
            
            # Test 2: Send mock audio (simulating ESP32)
            print(f"\n🎤 Testing audio input (simulating ESP32)...")
            
            # Create mock audio chunks
            audio_chunks = create_mock_audio_chunks()
            print(f"📤 Sending {len(audio_chunks)} audio chunks...")
            
            # Send audio chunks
            for i, chunk in enumerate(audio_chunks):
                await websocket.send(chunk)
                await asyncio.sleep(0.06)  # 60ms intervals like ESP32
                
                if (i + 1) % 10 == 0:
                    print(f"   Sent {i + 1}/{len(audio_chunks)} chunks...")
            
            print("✅ Audio chunks sent - waiting for processing...")
            
            # Listen for ASR + Gemini response
            audio_response_chunks = 0
            start_time = time.time()
            
            try:
                while time.time() - start_time < 15:  # Wait up to 15 seconds
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                        
                        if isinstance(response, bytes):
                            audio_response_chunks += 1
                            if audio_response_chunks == 1:
                                print("🔊 Receiving Gemini response to audio input...")
                                
                        elif isinstance(response, str):
                            try:
                                msg = json.loads(response)
                                print(f"📥 Server message: {msg}")
                            except json.JSONDecodeError:
                                pass
                                
                    except asyncio.TimeoutError:
                        continue
                        
            except Exception as e:
                print(f"⚠️  Audio response error: {e}")
            
            if audio_response_chunks > 0:
                print(f"✅ Received {audio_response_chunks} audio response chunks")
                print("🎉 Complete audio pipeline test successful!")
            else:
                print("⚠️  No audio response - check ASR and Gemini processing")
            
            # Send goodbye
            goodbye_message = {
                "type": "control",
                "command": "disconnect"
            }
            await websocket.send(json.dumps(goodbye_message))
            print("👋 Sent disconnect message")
            
    except websockets.exceptions.ConnectionRefused:
        print("❌ Connection refused - is the Gemini real-time server running?")
        print("   Start with: python app_gemini_realtime.py")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


async def check_server_status():
    """Check if the server is running"""
    try:
        server_host = "localhost"
        server_port = 8000
        websocket_url = f"ws://{server_host}:{server_port}/"
        
        async with websockets.connect(websocket_url) as websocket:
            return True
    except:
        return False


if __name__ == "__main__":
    print("🎯 Xiaozhi Full Pipeline Test")
    print("=" * 60)
    print("This test validates the complete real-time audio pipeline:")
    print("1. WebSocket connection to Gemini real-time server")
    print("2. Text message → Gemini LLM+TTS → Audio response")
    print("3. Audio input → Deepgram ASR → Gemini LLM+TTS → Audio response")
    print("=" * 60)
    
    async def main():
        # Check if server is running
        print("🔍 Checking server status...")
        server_running = await check_server_status()
        
        if not server_running:
            print("❌ Server not running")
            print("📋 To start the server:")
            print("   1. cd main/xiaozhi-server")
            print("   2. python app_gemini_realtime.py")
            print("   3. Then run this test again")
            return
        
        print("✅ Server is running")
        
        # Run the full pipeline test
        await test_full_pipeline()
    
    asyncio.run(main())