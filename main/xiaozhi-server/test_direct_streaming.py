#!/usr/bin/env python3
"""
Test script to verify direct VAD-to-ASR streaming implementation.
This tests the direct streaming path from VAD to Google Speech v2 ASR.
"""

import asyncio
import sys
import os
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config.logger import setup_logging
from config.settings import load_config
from core.utils.modules_initialize import initialize_modules

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = setup_logging()

async def test_direct_streaming():
    """Test the direct streaming implementation"""
    print("\n" + "="*60)
    print("DIRECT VAD-TO-ASR STREAMING TEST")
    print("="*60)
    
    # Load configuration
    config = load_config()
    
    # Check selected modules
    selected_modules = config.get("selected_module", {})
    print(f"\nSelected Modules:")
    print(f"  VAD: {selected_modules.get('VAD', 'Not configured')}")
    print(f"  ASR: {selected_modules.get('ASR', 'Not configured')}")
    
    # Initialize modules
    print("\nInitializing modules...")
    modules = initialize_modules(
        logger,
        config,
        "VAD" in selected_modules,
        "ASR" in selected_modules,
        False,  # LLM
        False,  # TTS
        False,  # Memory
        False   # Intent
    )
    
    vad = modules.get("vad")
    asr = modules.get("asr")
    
    if not vad:
        print("❌ VAD module not initialized!")
        return
    
    if not asr:
        print("❌ ASR module not initialized!")
        return
    
    print(f"✅ VAD initialized: {type(vad).__name__}")
    print(f"✅ ASR initialized: {type(asr).__name__}")
    
    # Check ASR interface type
    from core.providers.asr.dto.dto import InterfaceType
    
    if hasattr(asr, 'interface_type'):
        print(f"\nASR Interface Type: {asr.interface_type}")
        
        if asr.interface_type == InterfaceType.STREAM:
            print("✅ ASR supports streaming interface")
            
            # Check for streaming methods
            has_start = hasattr(asr, 'start_streaming_session')
            has_stream = hasattr(asr, 'stream_audio_chunk')
            has_end = hasattr(asr, 'end_streaming_session')
            
            print(f"\nStreaming Methods:")
            print(f"  start_streaming_session: {'✅' if has_start else '❌'}")
            print(f"  stream_audio_chunk: {'✅' if has_stream else '❌'}")
            print(f"  end_streaming_session: {'✅' if has_end else '❌'}")
            
            if has_start and has_stream and has_end:
                print("\n✅ All streaming methods available!")
                print("\nDirect VAD-to-ASR streaming is properly configured!")
                
                # Create a mock connection object to test
                class MockConnection:
                    def __init__(self):
                        self.session_id = "test-session-123"
                        self.asr_provider = asr
                        self.asr_streaming_active = False
                        self.direct_streaming_mode = False
                        self.client_have_voice = False
                        self.asr_audio = []
                        self.audio_pre_buffer = []
                
                conn = MockConnection()
                print(f"\nTest Connection Created:")
                print(f"  Session ID: {conn.session_id}")
                print(f"  ASR Provider: {type(conn.asr_provider).__name__}")
                
                # Test starting a streaming session
                print("\nTesting streaming session start...")
                try:
                    success = await asr.start_streaming_session(conn, conn.session_id)
                    if success:
                        print("✅ Streaming session started successfully!")
                        conn.asr_streaming_active = True
                        conn.direct_streaming_mode = True
                    else:
                        print("⚠️ Failed to start streaming session")
                except Exception as e:
                    print(f"❌ Error starting streaming session: {e}")
                
                # Test ending the session
                if conn.asr_streaming_active:
                    print("\nTesting streaming session end...")
                    try:
                        final_transcript, file_path = await asr.end_streaming_session(conn, conn.session_id)
                        print(f"✅ Streaming session ended")
                        print(f"  Final transcript: '{final_transcript}' (empty is normal for test)")
                    except Exception as e:
                        print(f"❌ Error ending streaming session: {e}")
            else:
                print("\n❌ Missing required streaming methods!")
        else:
            print(f"❌ ASR interface type is {asr.interface_type}, not STREAM")
            print("   Direct streaming is disabled for non-streaming ASR providers")
    else:
        print("❌ ASR provider doesn't have interface_type attribute!")
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60 + "\n")

if __name__ == "__main__":
    asyncio.run(test_direct_streaming())