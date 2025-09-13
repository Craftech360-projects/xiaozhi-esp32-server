# Audio Timing Fix for Google Speech ASR

## Problem Summary
The xiaozhi-server was experiencing timing issues where audio chunks were not reaching Google's ASR service, resulting in empty transcripts despite successful VAD detection. The root cause was a dual-path conflict and timing mismatch between VAD detection and ASR streaming sessions.

## Root Causes Identified

1. **Dual-Path Audio Processing Conflict**: Audio was being sent to both streaming path AND traditional buffering simultaneously
2. **Google API Timeout Before Speech**: Streaming sessions were timing out (~11 seconds) exactly when speech began arriving
3. **Audio Generator Inefficiency**: The generator processed chunks one-by-one and had short timeout windows
4. **No Recovery Mechanism**: When Google API timed out, there was no way to restart the session for delayed speech

## Fixes Implemented

### 1. Direct VAD-to-ASR Streaming Architecture
**File**: `core/providers/asr/google_speech_v2.py`
- Changed `interface_type` from `NON_STREAM` to `STREAM`
- Implemented proper streaming interface with session management
- Added streaming methods: `start_streaming_session()`, `stream_audio_chunk()`, `end_streaming_session()`

### 2. Audio Routing Fix
**File**: `core/connection.py`
- Added ASR interface type checking to route audio to only one path
- Direct streaming bypasses traditional buffering when `InterfaceType.STREAM` is detected
- Eliminated dual-path conflicts

### 3. VAD Streaming Integration
**File**: `core/providers/vad/silero_onnx.py`
- Added ASR interface type checking before starting streaming sessions
- Implemented `direct_streaming_mode` flag for bypass logic
- Reduced excessive logging from INFO to DEBUG level

### 4. Improved Audio Generator
**File**: `core/providers/asr/google_speech_v2.py` (lines 351-415)
- **Batch Processing**: Processes up to 5 audio chunks per cycle instead of 1
- **Extended Patience**: Waits 5 seconds (250 cycles × 20ms) instead of 2 seconds for delayed audio
- **Smarter Timeout Logic**: Only exits when session is inactive AND no audio in buffer
- **Better Logging**: Logs every 10th chunk and provides periodic status updates

### 5. Session Restart Mechanism
**File**: `core/providers/asr/google_speech_v2.py` (lines 506-527)
- Detects when streaming task ends but audio still arrives (timing mismatch)
- Automatically restarts streaming sessions up to 2 times
- Prevents infinite restart loops with configurable limits
- Provides detailed logging for timing analysis

### 6. Enhanced Error Handling
**File**: `core/providers/asr/google_speech_v2.py` (lines 447-482)
- Improved timeout detection and reporting
- Detailed buffer statistics when timing issues occur
- Fallback transcript salvaging from partial results
- Clear guidance for troubleshooting persistent issues

## Key Improvements

### Before Fix:
```
VAD Detection → Audio sent to BOTH:
├─ Traditional Buffer → ASR (conflict)
└─ Direct Streaming → Google API timeout → Empty transcript
```

### After Fix:
```
VAD Detection → Interface Type Check → Direct Streaming Only:
└─ Google API → Timeout Detection → Auto Restart → Process Delayed Audio → Transcript
```

## Performance Improvements

1. **Eliminated Dual-Path Conflicts**: Audio now routes to single processing path
2. **Reduced Latency**: Direct VAD-to-ASR streaming bypasses buffering delays  
3. **Better Timeout Handling**: Sessions restart automatically for delayed speech
4. **Batch Processing**: Processes multiple audio chunks per cycle for efficiency
5. **Reduced Logging Noise**: Changed frequent logs to DEBUG level

## Testing Results

The timing fix was verified with `test_timing_fix.py` which simulates:
1. Starting Google API streaming session
2. 3-second delay (no audio)
3. Burst of 30 audio chunks (delayed speech)
4. Session restart detection and handling
5. Final transcript extraction

**Results**: Session restart mechanism successfully detects timing mismatches and automatically restarts streaming sessions when delayed audio arrives.

## Configuration

No configuration changes required. The fix automatically detects `InterfaceType.STREAM` and applies the improved routing logic.

## Log Indicators

Look for these log messages to verify the fix is working:

- `[STREAM-START] Streaming session started successfully`
- `[AUDIO-GEN] Sending audio chunk #N`
- `[STREAM-AUDIO] Streaming task ended but audio still arriving` (timing issue detected)
- `[STREAM-AUDIO] Restarted streaming task` (automatic recovery)
- `[STREAM-TASK] Session stats before timeout: X chunks received, Y remaining`

## Future Enhancements

1. **Adaptive Timeouts**: Dynamically adjust Google API timeout based on VAD patterns
2. **Smarter VAD Timing**: Fine-tune VAD start/stop thresholds to reduce false starts
3. **Audio Buffering Strategy**: Implement smart pre-buffering for consistent audio flow
4. **Session Pooling**: Maintain warm connections to reduce session startup latency

## Files Modified

- `core/providers/asr/google_speech_v2.py` - Main streaming implementation
- `core/providers/vad/silero_onnx.py` - VAD streaming integration  
- `core/connection.py` - Audio routing logic
- `core/providers/asr/base.py` - Bypass logic for direct streaming
- `test_timing_fix.py` - Verification test script (created)