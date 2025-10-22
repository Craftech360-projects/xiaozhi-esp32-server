# PCM Jitter Testing Guide

This guide helps you isolate jitter issues by testing your MQTT gateway's audio streaming pipeline without LiveKit.

## Overview

The jitter testing setup allows you to:
1. **Bypass LiveKit** - Stream a PCM file directly through your UDP pipeline
2. **Isolate the issue** - Determine if jitter comes from LiveKit or your gateway
3. **Test your pipeline** - Verify Opus encoding, AES encryption, and UDP streaming work correctly

## Files Added

- `test_pcm_streaming.js` - Core PCM streaming logic that mimics LiveKit audio processing
- `test_pcm_client.js` - MQTT test client to trigger PCM streaming
- `test.pcm` - Your test audio file (already exists)

## How It Works

1. **Normal Flow**: Client → MQTT → LiveKit → Audio Processing → Opus → AES → UDP → Client
2. **Test Flow**: test.pcm → Audio Processing → Opus → AES → UDP → Client

The test bypasses LiveKit and streams your `test.pcm` file through the exact same audio processing pipeline that LiveKit audio would go through.

## Usage

### Method 1: Using the Test Client (Recommended)

```bash
# Start your MQTT gateway normally
npm start

# In another terminal, run the test client
node test_pcm_client.js
```

The test client will:
1. Connect to your MQTT broker
2. Send a hello message to establish a session
3. Send a `test_pcm` command to trigger PCM streaming
4. Your gateway will stream `test.pcm` through the UDP pipeline
5. Monitor the output for jitter analysis

### Method 2: Manual MQTT Command

If you have your own MQTT client or device, send this message:

```json
{
  "type": "test_pcm",
  "session_id": "your_session_id",
  "timestamp": 1640995200000
}
```

## Audio Parameters

The test uses the same parameters as your LiveKit setup:
- **Sample Rate**: 24kHz (outgoing to client)
- **Channels**: 1 (mono)
- **Frame Duration**: 60ms
- **Frame Size**: 1440 samples (2880 bytes PCM)
- **Encoding**: Opus (if available, otherwise PCM)
- **Encryption**: AES-128-CTR

## Analyzing Results

### What to Look For

1. **Timing Consistency**: Check frame processing times in logs
2. **Buffer Management**: Monitor frame buffer levels
3. **Opus Encoding**: Verify consistent encoding times
4. **UDP Transmission**: Check for dropped or delayed packets

### Log Analysis

Look for these log patterns:

```
🎵 [OPUS] Frame 1: 24kHz 60ms PCM 2880B → Opus 120B
⏱️ [TIMING] Frame 1: processed in 2ms, next delay: 58ms
🔍 [FRAME] 1: samples=1440, max=8192, first10=[1024,2048,...]
```

### Jitter Indicators

- **Inconsistent frame timing**: Processing times vary significantly
- **Buffer underruns**: Frame buffer becomes empty
- **Encoding delays**: Opus encoding takes too long
- **Network delays**: UDP transmission delays

## Troubleshooting

### No Audio Output
- Check if `test.pcm` exists and has correct format
- Verify Opus encoder is working
- Check UDP connection is established

### Timing Issues
- Monitor CPU usage during test
- Check for other processes interfering
- Verify frame timing calculations

### Encoding Problems
- Test with PCM mode (disable Opus) to isolate encoding issues
- Check Opus library installation

## Expected Results

### If Jitter is from LiveKit:
- PCM test should show smooth, consistent timing
- Frame processing should be regular
- No buffer underruns or delays

### If Jitter is from Gateway:
- PCM test will show the same jitter patterns
- Inconsistent frame timing
- Buffer management issues

## Next Steps

Based on results:

1. **Jitter in PCM test**: Focus on gateway optimization
   - Buffer management
   - Frame timing
   - Opus encoding performance
   - UDP transmission

2. **No jitter in PCM test**: Focus on LiveKit integration
   - Audio resampling
   - LiveKit frame delivery
   - Network between gateway and LiveKit

## Configuration

You can modify test parameters in `test_pcm_streaming.js`:

```javascript
const SAMPLE_RATE = 24000;        // Audio sample rate
const FRAME_DURATION_MS = 60;     // Frame duration
const FRAME_SIZE_SAMPLES = 1440;  // Samples per frame
```

## PCM File Format

Your `test.pcm` should be:
- **Format**: 16-bit signed PCM
- **Sample Rate**: 24kHz (to match outgoing audio)
- **Channels**: 1 (mono)
- **Byte Order**: Little-endian

To convert audio files to this format:
```bash
ffmpeg -i input.wav -f s16le -ar 24000 -ac 1 test.pcm
```