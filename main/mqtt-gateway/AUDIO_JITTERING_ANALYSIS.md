# Audio Jittering Issue Analysis - MQTT Gateway

## Problem Statement
UDP streaming of audio from MQTT gateway to client experiences jittering in the `livekit_function_calling` branch, while the same functionality works fine in the `Production1` branch.

## Branch Comparison

### Production1 Branch (Working)
- **Bridge Type**: `WebSocketBridge`
- **Backend**: WebSocket server at `ws://139.59.7.72:8000/toy/v1/`
- **Audio Format**: Raw Opus data received directly via WebSocket binary messages
- **Processing**: Minimal - direct pass-through of Opus data
- **Data Flow**: WebSocket → Direct UDP transmission

### livekit_function_calling Branch (Jittering)
- **Bridge Type**: `LiveKitBridge`
- **Backend**: LiveKit server at `ws://localhost:7880`
- **Audio Format**: 48kHz PCM from LiveKit, resampled to 16kHz
- **Processing**: Complex audio pipeline with resampling and buffering
- **Data Flow**: LiveKit → Resampler → Buffer → PCM transmission (Opus encoding disabled)

## Root Cause Analysis

### 1. Missing Opus Encoding (PRIMARY CAUSE)
The Opus encoding is **commented out** in `app.js` (lines 152-164):

```javascript
// Current implementation - sending raw PCM
this.connection.sendUdpMessage(frameData, timestamp);  // 640 bytes per frame

// Commented out Opus encoding
/*
if (opusEncoder) {
  try {
    const alignedBuffer = Buffer.allocUnsafe(frameData.length);
    frameData.copy(alignedBuffer);
    const opusBuffer = opusEncoder.encode(alignedBuffer, this.targetFrameSize);
    this.connection.sendUdpMessage(opusBuffer, timestamp);  // ~60 bytes per frame
  } catch (err) {
    console.error(`❌ [BUFFERED] Encode error: ${err.message}`);
  }
}
*/
```

**Impact**:
- PCM: 640 bytes per 20ms frame
- Opus: ~60 bytes per 20ms frame
- **10x increase in network traffic**

### 2. Audio Resampling Overhead
```javascript
// Line 89 - Using QUICK quality for speed over quality
this.audioResampler = new AudioResampler(48000, 16000, 1, AudioResamplerQuality.QUICK);
```

**Impact**:
- Processing delay for 48kHz → 16kHz conversion
- Potential audio artifacts from QUICK quality setting
- Additional CPU overhead

### 3. Frame Buffering Mechanism
```javascript
// Lines 92-94 - Buffer management
this.frameBuffer = Buffer.alloc(0);
this.targetFrameSize = 320; // 320 samples = 20ms at 16kHz
this.targetFrameBytes = this.targetFrameSize * 2; // 640 bytes
```

**Impact**:
- Variable latency based on buffer fill state
- Potential frame drops when buffers don't align
- Timing inconsistencies

### 4. Encoder/Decoder Mismatch
```javascript
// Lines 44-45 - Encoder at 24kHz, Decoder at 16kHz
opusEncoder = new OpusEncoder(24000, 1, OpusApplication.OPUS_APPLICATION_AUDIO);
opusDecoder = new OpusDecoder(16000, 1);
```

**Impact**:
- Sample rate mismatch between encoder and decoder
- Potential quality issues

## Network Impact Analysis

### Without Opus Encoding (Current)
- **Frame size**: 640 bytes (PCM)
- **Frames per second**: 50 (20ms frames)
- **Bandwidth**: 640 × 50 = 32,000 bytes/sec = **256 kbps**
- **UDP overhead**: Potential packet fragmentation

### With Opus Encoding (Fixed)
- **Frame size**: ~60 bytes (Opus)
- **Frames per second**: 50 (20ms frames)
- **Bandwidth**: 60 × 50 = 3,000 bytes/sec = **24 kbps**
- **UDP overhead**: Single packet per frame

## Solution

### Immediate Fix (High Priority)

1. **Re-enable Opus Encoding**

   In `app.js`, uncomment lines 154-163 and comment out line 150:
   ```javascript
   // this.connection.sendUdpMessage(frameData, timestamp); // COMMENT THIS OUT

   // UNCOMMENT THIS BLOCK:
   if (opusEncoder) {
     try {
       const alignedBuffer = Buffer.allocUnsafe(frameData.length);
       frameData.copy(alignedBuffer);
       const opusBuffer = opusEncoder.encode(alignedBuffer, this.targetFrameSize);
       this.connection.sendUdpMessage(opusBuffer, timestamp);
     } catch (err) {
       console.error(`❌ [BUFFERED] Encode error: ${err.message}`);
     }
   }
   ```

2. **Fix Encoder Sample Rate**

   Change line 44 to match decoder:
   ```javascript
   // From:
   opusEncoder = new OpusEncoder(24000, 1, OpusApplication.OPUS_APPLICATION_AUDIO);
   // To:
   opusEncoder = new OpusEncoder(16000, 1, OpusApplication.OPUS_APPLICATION_AUDIO);
   ```

### Additional Optimizations (Medium Priority)

3. **Improve Resampler Quality**

   Change line 89:
   ```javascript
   // From:
   this.audioResampler = new AudioResampler(48000, 16000, 1, AudioResamplerQuality.QUICK);
   // To:
   this.audioResampler = new AudioResampler(48000, 16000, 1, AudioResamplerQuality.HIGH);
   ```

4. **Reduce Buffer Latency**

   Consider processing partial frames more aggressively or reducing target frame size for lower latency.

### Long-term Solutions (Low Priority)

5. **Configure LiveKit for 16kHz Output**

   Eliminate resampling entirely by configuring LiveKit to output 16kHz audio natively.

6. **Implement Adaptive Bitrate**

   Adjust Opus bitrate based on network conditions.

## Testing Checklist

After implementing fixes:

- [ ] Verify Opus encoding is active (check logs for encoded packet sizes)
- [ ] Monitor bandwidth usage (should drop from ~256 kbps to ~24 kbps)
- [ ] Test audio quality with multiple concurrent connections
- [ ] Verify no frame drops or buffer underruns
- [ ] Check CPU usage (should decrease with Opus encoding)
- [ ] Test with various network conditions (latency, packet loss)

## Expected Results

After implementing the primary fix (re-enabling Opus encoding):

1. **Bandwidth reduction**: 90% decrease (256 kbps → 24 kbps)
2. **Jitter elimination**: Consistent frame delivery without fragmentation
3. **Lower latency**: Smaller packets traverse network faster
4. **Better scalability**: Support more concurrent connections

## Code Locations Reference

- **Main audio processing**: `app.js` lines 127-167 (`processBufferedFrames` method)
- **Opus initialization**: `app.js` lines 42-56
- **Resampler setup**: `app.js` line 89
- **UDP message sending**: `app.js` line 150 (currently), lines 154-163 (should be)
- **Frame buffering**: `app.js` lines 92-94

## Conclusion

The jittering issue is primarily caused by sending uncompressed PCM audio over UDP instead of compressed Opus data. This results in a 10x increase in network traffic, leading to packet fragmentation, network congestion, and ultimately audio jittering. Re-enabling the Opus encoding will resolve the issue immediately.