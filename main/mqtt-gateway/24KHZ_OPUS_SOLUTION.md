# 24kHz Opus Audio Pipeline Solution

## Executive Summary

**YES, it's absolutely possible!** Both LiveKit and Opus support 24kHz sample rate. This solution eliminates the need for resampling and provides better audio quality.

## Feasibility Test Results

### ✅ LiveKit 24kHz Support
```bash
# Tested successfully:
audio_source = rtc.AudioSource(24000, 1)  # 24kHz, mono
```

### ✅ Opus 24kHz Support
```bash
# Tested successfully:
OpusEncoder(24000, 1, OpusApplication.OPUS_APPLICATION_AUDIO)
OpusDecoder(24000, 1)
```

### ✅ ESP32 Compatibility
ESP32 can handle 24kHz Opus decoding (Opus is designed for this).

## Proposed Audio Pipeline

```
[Groq TTS] → [LiveKit Server] → [MQTT Gateway] → [ESP32 Client]
   24kHz         24kHz            24kHz Opus      24kHz
```

### Benefits of 24kHz Pipeline:

1. **No Resampling**: Eliminates 48kHz → 16kHz conversion overhead
2. **Better Audio Quality**: Higher sample rate preserves more audio detail
3. **Reduced CPU Usage**: No resampling processing in MQTT Gateway
4. **Lower Latency**: Direct pass-through without buffering for resampling
5. **Already Configured**: Opus encoder is already set to 24kHz in current code

## Required Configuration Changes

### 1. LiveKit Server Changes

**Files to modify**: All audio players in `main/livekit-server/src/services/`

#### Change AudioSource from 48kHz to 24kHz:

**File**: `foreground_audio_player.py:148`
```python
# FROM:
audio_source = rtc.AudioSource(48000, 1)  # 48kHz, mono

# TO:
audio_source = rtc.AudioSource(24000, 1)  # 24kHz, mono
```

**File**: `unified_audio_player.py:190`
```python
# FROM:
audio_segment = audio_segment.set_frame_rate(48000)
sample_rate = 48000

# TO:
audio_segment = audio_segment.set_frame_rate(24000)
sample_rate = 24000
```

**File**: `audio_player.py:128, 167`
```python
# FROM:
audio_source = rtc.AudioSource(48000, 1)
audio_segment = audio_segment.set_frame_rate(48000)

# TO:
audio_source = rtc.AudioSource(24000, 1)
audio_segment = audio_segment.set_frame_rate(24000)
```

**File**: `minimal_audio_player.py:52`
```python
# FROM:
self.audio_source = rtc.AudioSource(48000, 1)  # 48kHz, mono

# TO:
self.audio_source = rtc.AudioSource(24000, 1)  # 24kHz, mono
```

### 2. MQTT Gateway Changes

**File**: `main/mqtt-gateway/app.js`

#### Remove Audio Resampler (Lines 88-89):
```javascript
// REMOVE THESE LINES:
// this.audioResampler = new AudioResampler(48000, 16000, 1, AudioResamplerQuality.QUICK);

// ADD COMMENT:
// No resampling needed - LiveKit now outputs 24kHz directly
```

#### Update Frame Buffer Configuration (Lines 92-94):
```javascript
// FROM (16kHz):
this.frameBuffer = Buffer.alloc(0);
this.targetFrameSize = 320; // 320 samples = 20ms at 16kHz
this.targetFrameBytes = this.targetFrameSize * 2; // 640 bytes

// TO (24kHz):
this.frameBuffer = Buffer.alloc(0);
this.targetFrameSize = 480; // 480 samples = 20ms at 24kHz
this.targetFrameBytes = this.targetFrameSize * 2; // 960 bytes
```

#### Fix Opus Encoder Sample Rate (Line 44):
```javascript
// FROM:
opusEncoder = new OpusEncoder(24000, 1, OpusApplication.OPUS_APPLICATION_AUDIO);

// TO (already correct!):
opusEncoder = new OpusEncoder(24000, 1, OpusApplication.OPUS_APPLICATION_AUDIO);
```

#### Update Audio Stream Processing (Lines 287-376):
```javascript
// REMOVE resampling logic:
// const resampledFrames = this.audioResampler.push(value);

// REPLACE WITH direct processing:
// value is now an AudioFrame from LiveKit (24kHz)
const audioBuffer = Buffer.from(
  value.data.buffer,
  value.data.byteOffset,
  value.data.byteLength
);

// Append directly to frame buffer (no resampling needed)
this.frameBuffer = Buffer.concat([this.frameBuffer, audioBuffer]);
totalBytes += audioBuffer.length;
```

#### Re-enable Opus Encoding (Lines 154-163):
```javascript
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

// COMMENT OUT PCM transmission:
// this.connection.sendUdpMessage(frameData, timestamp);
```

## Audio Format Comparison

### Current (Problematic) Pipeline:
```
48kHz LiveKit → Resample to 16kHz → Send PCM (640B/frame) → ESP32
```
- **Bandwidth**: 256 kbps
- **Quality**: Reduced by resampling
- **CPU**: High (resampling + no compression)

### New 24kHz Pipeline:
```
24kHz LiveKit → Direct → Send Opus (~90B/frame) → ESP32
```
- **Bandwidth**: ~36 kbps (85% reduction)
- **Quality**: Higher (24kHz vs 16kHz)
- **CPU**: Lower (no resampling)

## Frame Size Calculations

### 24kHz Frame Sizes:
- **Sample Rate**: 24,000 Hz
- **Frame Duration**: 20ms
- **Samples per Frame**: 24,000 × 0.02 = 480 samples
- **PCM Frame Size**: 480 × 2 bytes = 960 bytes
- **Opus Frame Size**: ~90 bytes (typical compression)

### Bandwidth Impact:
- **Frames per Second**: 50 (20ms frames)
- **PCM Bandwidth**: 960 × 50 = 48,000 bytes/sec = 384 kbps
- **Opus Bandwidth**: 90 × 50 = 4,500 bytes/sec = 36 kbps

## Implementation Steps

### Step 1: Update LiveKit Server
1. Modify all audio player files to use 24kHz
2. Test TTS output at 24kHz
3. Verify LiveKit session works with 24kHz

### Step 2: Update MQTT Gateway
1. Remove resampler initialization
2. Update frame buffer sizes for 24kHz
3. Remove resampling logic from audio stream processing
4. Re-enable Opus encoding
5. Test with 24kHz audio frames

### Step 3: ESP32 Configuration
1. Verify ESP32 Opus decoder is set to 24kHz
2. Update audio output configuration if needed
3. Test playback quality

### Step 4: Testing
1. Test end-to-end audio quality
2. Monitor bandwidth usage (should be ~36 kbps)
3. Verify no jittering
4. Check CPU usage on both server and gateway

## Expected Results

✅ **Audio Quality**: Better (24kHz vs 16kHz)
✅ **Bandwidth**: 85% reduction (384 kbps → 36 kbps with Opus)
✅ **Latency**: Lower (no resampling delays)
✅ **CPU Usage**: Reduced (no resampling)
✅ **Jittering**: Eliminated (proper Opus compression)
✅ **Compatibility**: Full ESP32 support

## Rollback Plan

If issues occur, revert by:
1. Changing LiveKit back to 48kHz
2. Re-enabling resampler in MQTT Gateway
3. Keeping Opus encoding enabled (still beneficial)

This solution provides the best of both worlds: higher quality audio and dramatically reduced bandwidth usage.