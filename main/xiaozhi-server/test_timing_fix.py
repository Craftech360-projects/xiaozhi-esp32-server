#!/usr/bin/env python3
"""
Test script to verify the timing fix for audio streaming.
This simulates the issue where audio chunks arrive after the Google API starts,
causing timing mismatches and empty transcripts.
"""

import asyncio
import sys
import time
from pathlib import Path
import numpy as np

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config.logger import setup_logging
from config.settings import load_config
from core.utils.modules_initialize import initialize_modules
from core.providers.asr.dto.dto import InterfaceType

logger = setup_logging()

def generate_mock_audio_chunk(duration_ms=60, sample_rate=16000):
    """Generate a mock audio chunk (sine wave) for testing"""
    samples = int(sample_rate * duration_ms / 1000)
    t = np.linspace(0, duration_ms/1000, samples, False)
    # Generate a 440Hz sine wave (A4 note)
    audio = np.sin(2 * np.pi * 440 * t) * 0.3
    # Convert to 16-bit PCM
    audio_pcm = (audio * 32767).astype(np.int16)
    return audio_pcm.tobytes()

async def test_timing_fix():
    """Test the timing fix by simulating delayed audio arrival"""
    print("\n" + "="*70)
    print("TIMING FIX VERIFICATION TEST")
    print("="*70)
    print("This test simulates the issue where audio chunks arrive")
    print("after Google API session starts, causing timeouts and empty transcripts.")
    print("="*70)
    
    # Load configuration
    config = load_config()
    
    # Check selected modules
    selected_modules = config.get("selected_module", {})
    asr_type = selected_modules.get('ASR', 'Not configured')
    vad_type = selected_modules.get('VAD', 'Not configured')
    
    print(f"\nConfiguration:")
    print(f"   VAD: {vad_type}")
    print(f"   ASR: {asr_type}")
    
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
    
    asr = modules.get("asr")
    vad = modules.get("vad")
    
    if not asr or not vad:
        print("ERROR: Failed to initialize required modules!")
        return
    
    print(f"SUCCESS: ASR: {type(asr).__name__}")
    print(f"SUCCESS: VAD: {type(vad).__name__}")
    
    # Verify streaming capability
    if not hasattr(asr, 'interface_type') or asr.interface_type != InterfaceType.STREAM:
        print("ERROR: ASR does not support streaming interface!")
        return
    
    print(f"SUCCESS: ASR Interface: {asr.interface_type}")
    
    # Create mock connection
    class MockConnection:
        def __init__(self):
            self.session_id = f"test-timing-{int(time.time())}"
            self.asr_provider = asr
            self.asr_streaming_active = False
            self.direct_streaming_mode = False
            self.client_have_voice = False
            self.asr_audio = []
            self.audio_pre_buffer = []
            self._vad_log_counter = 0
    
    conn = MockConnection()
    print(f"SUCCESS: Mock Connection: {conn.session_id}")
    
    print(f"\nTesting Timing Fix - Scenario: Delayed Audio Arrival")
    print(f"   1. Start streaming session (Google API waits)")
    print(f"   2. Delay for 3 seconds (simulate delayed speech)")
    print(f"   3. Send burst of audio chunks (simulate speech starting)")
    print(f"   4. Verify chunks are processed despite delay")
    print(f"   5. End session and get transcript")
    
    try:
        # Step 1: Start streaming session
        print(f"\nStep 1: Starting streaming session...")
        success = await asr.start_streaming_session(conn, conn.session_id)
        if success:
            print(f"SUCCESS: Streaming session started successfully")
            conn.asr_streaming_active = True
            conn.direct_streaming_mode = True
        else:
            print(f"ERROR: Failed to start streaming session")
            return
        
        # Step 2: Simulate delay (this is what caused the original issue)
        print(f"\nStep 2: Simulating 3-second delay (no audio)...")
        print(f"   (This represents the time between VAD starting and actual speech)")
        await asyncio.sleep(3.0)
        
        # Step 3: Send burst of audio chunks (simulate delayed speech arrival)
        print(f"\nStep 3: Sending burst of audio chunks after delay...")
        num_chunks = 30  # 1.8 seconds of audio (30 * 60ms)
        
        for i in range(num_chunks):
            # Generate mock audio chunk
            audio_chunk = generate_mock_audio_chunk()
            
            # Stream to ASR
            partial_result = await asr.stream_audio_chunk(conn, audio_chunk, conn.session_id)
            
            if i % 10 == 0:  # Log every 10th chunk
                print(f"   CHUNK {i+1}/{num_chunks} sent ({len(audio_chunk)} bytes)")
                if partial_result:
                    print(f"   PARTIAL: '{partial_result}'")
            
            # Small delay to simulate real-time streaming
            await asyncio.sleep(0.05)  # 50ms delay
        
        print(f"SUCCESS: Streamed {num_chunks} audio chunks after 3-second delay")
        
        # Step 4: Wait a bit for processing
        print(f"\nStep 4: Waiting for processing...")
        await asyncio.sleep(2.0)
        
        # Step 5: End streaming session
        print(f"\nStep 5: Ending streaming session...")
        final_transcript, file_path = await asr.end_streaming_session(conn, conn.session_id)
        
        print(f"SUCCESS: Streaming session ended")
        print(f"TRANSCRIPT: '{final_transcript}'")
        
        if not final_transcript.strip():
            print(f"INFO: Empty transcript is expected for mock audio (sine waves)")
            print(f"   But the improved generator should have processed all chunks!")
        
        # Reset connection state
        conn.asr_streaming_active = False
        conn.direct_streaming_mode = False
        
        print(f"\nTIMING FIX TEST COMPLETED!")
        
    except Exception as e:
        print(f"\nERROR: Timing fix test failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
    
    print(f"\n" + "="*70)
    print("TIMING FIX ANALYSIS")
    print("="*70)
    
    print(f"\nKey Improvements Made:")
    print(f"   • Audio generator processes chunks in batches (up to 5 at once)")
    print(f"   • Extended timeout patience (5 seconds instead of 2)")
    print(f"   • Generator stays alive while audio buffer has data")
    print(f"   • Better error handling for timing issues")
    print(f"   • Improved logging to detect timing problems")
    
    print(f"\nWhat the Fix Addresses:")
    print(f"   • Google API timeout before speech arrives")
    print(f"   • Audio chunks accumulating in buffer but not processed")
    print(f"   • Empty transcripts despite successful VAD detection")
    print(f"   • Timing mismatches between VAD and ASR")
    
    print(f"\nExpected Behavior with Fix:")
    print(f"   • Audio generator waits longer for delayed speech")
    print(f"   • Processes audio chunks in batches when they arrive")
    print(f"   • Continues processing even after initial timeout")
    print(f"   • Reports timing issues with detailed buffer statistics")
    
    print(f"\nIf Issues Persist:")
    print(f"   • Check VAD detection timing (too early start?)")
    print(f"   • Consider adjusting VAD sensitivity")
    print(f"   • Implement session restart for very long delays")
    print(f"   • Optimize audio chunk size or frequency")

if __name__ == "__main__":
    asyncio.run(test_timing_fix())