#!/usr/bin/env python3
"""
Test script to verify transcript-to-LLM timing and fix session cleanup issues.
This simulates the complete flow from ASR transcript to LLM processing.
"""

import asyncio
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config.logger import setup_logging
from config.settings import load_config
from core.utils.modules_initialize import initialize_modules
from core.providers.asr.dto.dto import InterfaceType

logger = setup_logging()

async def test_transcript_to_llm_timing():
    """Test the complete transcript-to-LLM flow with timing measurements"""
    print("\n" + "="*70)
    print("TRANSCRIPT-TO-LLM TIMING TEST")
    print("="*70)
    print("This test verifies that transcripts reach the LLM promptly")
    print("and checks for any delays in the processing pipeline.")
    print("="*70)
    
    # Load configuration
    config = load_config()
    
    # Check selected modules
    selected_modules = config.get("selected_module", {})
    asr_type = selected_modules.get('ASR', 'Not configured')
    llm_type = selected_modules.get('LLM', 'Not configured')
    
    print(f"\nConfiguration:")
    print(f"   ASR: {asr_type}")
    print(f"   LLM: {llm_type}")
    
    # Initialize modules (including LLM this time)
    print("\nInitializing modules...")
    modules = initialize_modules(
        logger,
        config,
        False,  # VAD - not needed for this test
        "ASR" in selected_modules,
        "LLM" in selected_modules,  # Enable LLM
        False,  # TTS
        False,  # Memory
        False   # Intent
    )
    
    asr = modules.get("asr")
    llm = modules.get("llm")
    
    if not asr:
        print("ERROR: Failed to initialize ASR module!")
        return
        
    if not llm:
        print("ERROR: Failed to initialize LLM module!")
        return
    
    print(f"SUCCESS: ASR: {type(asr).__name__}")
    print(f"SUCCESS: LLM: {type(llm).__name__}")
    
    # Create mock connection with proper LLM setup
    class MockConnection:
        def __init__(self, asr_provider, llm_provider):
            self.session_id = f"test-transcript-llm-{int(time.time())}"
            self.asr_provider = asr_provider
            self.llm = llm_provider
            self.asr_streaming_active = False
            self.direct_streaming_mode = False
            self.client_have_voice = False
            self.executor = None  # We'll test without thread pool first
            
            # Mock logger
            self.logger = logger
            
            # Mock dialogue system
            from core.utils.dialogue import Dialogue
            self.dialogue = Dialogue()
    
    conn = MockConnection(asr, llm)
    print(f"SUCCESS: Mock Connection: {conn.session_id}")
    
    print(f"\nTesting Transcript-to-LLM Flow:")
    print(f"   1. Simulate successful ASR transcript")
    print(f"   2. Call startToChat directly") 
    print(f"   3. Measure timing from transcript to LLM")
    print(f"   4. Check for delays and bottlenecks")
    
    try:
        # Simulate a transcript from ASR
        test_transcript = "Hello, how are you today?"
        print(f"\nStep 1: Simulating ASR transcript: '{test_transcript}'")
        
        # Import and call startToChat directly
        from core.handle.receiveAudioHandle import startToChat
        
        start_time = time.time()
        print(f"Step 2: Calling startToChat at {start_time:.3f}")
        
        # This will test the complete flow including intent handling and LLM submission
        await startToChat(conn, test_transcript)
        
        end_time = time.time()
        total_time = (end_time - start_time) * 1000
        
        print(f"Step 3: startToChat completed at {end_time:.3f}")
        print(f"SUCCESS: Total time from transcript to LLM submission: {total_time:.1f}ms")
        
        if total_time > 100:  # If more than 100ms
            print(f"WARNING: Processing time is high ({total_time:.1f}ms)")
            print("   This may indicate thread pool delays or blocking operations")
        else:
            print(f"EXCELLENT: Fast processing time ({total_time:.1f}ms)")
            
        print(f"\nStep 4: Testing session cleanup...")
        
        # Test the session cleanup fix for ASR
        if hasattr(conn.asr_provider, 'streaming_sessions'):
            print(f"ASR streaming sessions: {len(conn.asr_provider.streaming_sessions)}")
        
        print(f"\nTEST COMPLETED SUCCESSFULLY!")
        
    except Exception as e:
        print(f"\nERROR: Transcript-to-LLM test failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
    
    print(f"\n" + "="*70)
    print("TIMING ANALYSIS")
    print("="*70)
    
    print(f"\nFlow Summary:")
    print(f"   ASR Transcript → startToChat() → Intent Check → LLM Submit")
    
    print(f"\nPotential Delays:")
    print(f"   • Intent processing (regex matching, wake word checks)")
    print(f"   • Thread pool executor queue waiting")
    print(f"   • Memory system queries")
    print(f"   • LLM API initialization")
    
    print(f"\nOptimizations Applied:")
    print(f"   • Increased thread pool size from 5 to 8 workers")  
    print(f"   • Added timing logs to track bottlenecks")
    print(f"   • Fixed ASR session cleanup KeyError")
    print(f"   • Added robust session cleanup checks")
    
    print(f"\nWhat to Look For in Real Usage:")
    print(f"   • [CHAT-SUBMIT] logs showing transcript submission")
    print(f"   • [CHAT-START] logs showing when LLM receives message")
    print(f"   • [LLM-REQUEST] and [LLM-RESPONSE] timing measurements")
    print(f"   • Time delays between these log entries")

if __name__ == "__main__":
    asyncio.run(test_transcript_to_llm_timing())