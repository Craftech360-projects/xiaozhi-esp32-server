# LiveKit Audio Flow Analysis

## Audio Data Flow: LiveKit Server → MQTT Gateway → ESP32 Client

This document analyzes how audio flows from the LiveKit server to the ESP32 client through the MQTT gateway, including sample rates and processing at each stage.

## Audio Flow Overview

```
[Groq TTS] → [LiveKit Server] → [LiveKit Agent Session] → [MQTT Gateway] → [ESP32 Client]
   ???Hz         48kHz             48kHz               16kHz         16kHz
```

## 1. LiveKit Server Audio Configuration

### TTS Provider Configuration
**File**: `main/livekit-server/src/providers/provider_factory.py:23-28`

```python
@staticmethod
def create_tts(config):
    """Create Text-to-Speech provider based on configuration"""
    return groq.TTS(
        model=config['tts_model'],      # Default: 'playai-tts'
        voice=config['tts_voice']       # Default: 'Aaliyah-PlayAI'
    )
```

### Audio Source Configuration
**Files**: Multiple audio players in `main/livekit-server/src/services/`

All audio players consistently use **48kHz, mono** configuration:

```python
# From foreground_audio_player.py:148
audio_source = rtc.AudioSource(48000, 1)  # 48kHz, mono

# From unified_audio_player.py:190
audio_segment = audio_segment.set_frame_rate(48000)
sample_rate = 48000

# From audio_player.py:128, 167
audio_source = rtc.AudioSource(48000, 1)
audio_segment = audio_segment.set_frame_rate(48000)
```

## 2. LiveKit Audio Processing Details

### Frame Processing
**File**: `main/livekit-server/src/services/unified_audio_player.py:195-202`

```python
sample_rate = 48000
samples_per_frame = sample_rate * frame_duration_ms // 1000
# Default frame_duration_ms = 20ms
# samples_per_frame = 48000 * 20 / 1000 = 960 samples
# Frame size = 960 samples * 2 bytes = 1920 bytes per frame
```

### Audio Frame Creation
```python
frame = rtc.AudioFrame(
    data=audio_data,
    sample_rate=sample_rate,      # 48000 Hz
    num_channels=1,               # Mono
    samples_per_channel=samples_per_frame  # 960 samples
)
```

## 3. MQTT Gateway Audio Processing

### Receiving from LiveKit (48kHz)
**File**: `main/mqtt-gateway/app.js:287-401`

The MQTT gateway receives 48kHz audio from LiveKit through the `AudioStream`:

```javascript
const stream = new AudioStream(track);
const reader = stream.getReader();

while (true) {
    const { done, value } = await reader.read();
    // value is an AudioFrame from LiveKit (48kHz)
    const resampledFrames = this.audioResampler.push(value);
}
```

### Audio Resampling (48kHz → 16kHz)
**File**: `main/mqtt-gateway/app.js:89`

```javascript
// Initialize audio resampler for 48kHz -> 16kHz conversion
this.audioResampler = new AudioResampler(48000, 16000, 1, AudioResamplerQuality.QUICK);
```

### Frame Buffering and Target Sizes
**File**: `main/mqtt-gateway/app.js:92-94`

```javascript
this.frameBuffer = Buffer.alloc(0);
this.targetFrameSize = 320; // 320 samples = 20ms at 16kHz
this.targetFrameBytes = this.targetFrameSize * 2; // 640 bytes for 16-bit PCM
```

## 4. Current Audio Format Issues

### Problem: PCM Instead of Opus
**File**: `main/mqtt-gateway/app.js:149-150` (ACTIVE)

```javascript
// Send PCM directly without Opus encoding
this.connection.sendUdpMessage(frameData, timestamp);
```

**File**: `main/mqtt-gateway/app.js:154-163` (COMMENTED OUT)

```javascript
// Commented out Opus encoding for testing
/*
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
*/
```

### Sample Rate Mismatch in Opus Encoder/Decoder
**File**: `main/mqtt-gateway/app.js:44-45`

```javascript
// Encoder at 24kHz, Decoder at 16kHz - MISMATCH!
opusEncoder = new OpusEncoder(24000, 1, OpusApplication.OPUS_APPLICATION_AUDIO);
opusDecoder = new OpusDecoder(16000, 1);
```

## 5. Bandwidth Impact Analysis

### Current Implementation (PCM)
- **Frame Duration**: 20ms
- **Sample Rate**: 16kHz (after resampling)
- **Channels**: 1 (mono)
- **Bit Depth**: 16-bit
- **Frame Size**: 320 samples × 2 bytes = **640 bytes per frame**
- **Frames per Second**: 1000ms ÷ 20ms = 50 fps
- **Total Bandwidth**: 640 × 50 = **32,000 bytes/sec = 256 kbps**

### With Opus Encoding (Fixed)
- **Frame Duration**: 20ms
- **Compressed Size**: ~60 bytes per frame (typical Opus compression)
- **Frames per Second**: 50 fps
- **Total Bandwidth**: 60 × 50 = **3,000 bytes/sec = 24 kbps**
- **Compression Ratio**: ~90% reduction

## 6. Groq TTS Output Analysis

Based on the LiveKit server configuration, the Groq TTS likely outputs audio that gets processed into 48kHz before being sent to the MQTT gateway. The exact output sample rate from Groq's `playai-tts` model is not explicitly configured, but LiveKit standardizes it to 48kHz.

## 7. Complete Audio Pipeline

```
1. Groq TTS (playai-tts)
   ↓ (Unknown original sample rate)

2. LiveKit Audio Player
   ↓ (Converts to 48kHz, 1920 bytes/frame)

3. LiveKit AudioSource
   ↓ (48kHz PCM frames via AudioStream)

4. MQTT Gateway AudioResampler
   ↓ (48kHz → 16kHz, QUICK quality)

5. MQTT Gateway Frame Buffer
   ↓ (640 bytes PCM frames, 20ms duration)

6. UDP Transmission (CURRENT ISSUE)
   ↓ (Raw PCM - 256 kbps bandwidth)

7. ESP32 Client
   ↓ (Expects Opus compressed audio)
```

## 8. Root Cause Summary

1. **LiveKit sends 48kHz audio** - This is correct and standard
2. **MQTT Gateway resamples to 16kHz** - This is correct for ESP32
3. **Opus encoding is disabled** - This causes 10x bandwidth increase
4. **Sample rate mismatch in Opus config** - Encoder (24kHz) ≠ Decoder (16kHz)

## 9. Solution

### Primary Fix: Re-enable Opus Encoding
1. Uncomment Opus encoding in `processBufferedFrames()`
2. Fix encoder sample rate to match decoder (16kHz)
3. Comment out raw PCM transmission

### Secondary Fix: Improve Quality
1. Change resampler quality from QUICK to HIGH
2. Monitor CPU usage impact

This will reduce bandwidth from 256 kbps to 24 kbps and eliminate jittering caused by network congestion.