# Audio Recording Feature

This feature allows the MQTT Gateway to record incoming audio from ESP32 devices in WAV format for quality analysis and debugging purposes.

## Configuration

Add the following configuration to your `config/mqtt.json`:

```json
{
  "audio_recording": {
    "enabled": true,
    "max_duration_seconds": 30,
    "format": "wav",
    "sample_rate": 16000,
    "channels": 1,
    "bits_per_sample": 16
  }
}
```

### Configuration Options

- `enabled`: Enable/disable audio recording (default: false)
- `max_duration_seconds`: Maximum recording duration per session (default: 30 seconds)
- `format`: Audio format - currently only "wav" is supported
- `sample_rate`: Audio sample rate in Hz (default: 16000)
- `channels`: Number of audio channels (default: 1 for mono)
- `bits_per_sample`: Bits per audio sample (default: 16)

## How It Works

1. **Automatic Start**: Recording starts automatically when the first audio data is received from an ESP32 device
2. **File Naming**: Files are saved with the format: `esp32_audio_{MAC_ADDRESS}_{TIMESTAMP}.wav`
3. **Auto Stop**: Recording stops automatically when:
   - Maximum duration is reached
   - The device connection is closed
   - The LiveKit bridge is closed

## File Location

Audio files are saved in the `recordings/` directory within the mqtt-gateway folder:
```
main/mqtt-gateway/recordings/
├── esp32_audio_28_56_2f_07_c6_ec_2025-11-01T12-34-56-789Z.wav
├── esp32_audio_aa_bb_cc_dd_ee_ff_2025-11-01T12-35-12-123Z.wav
└── ...
```

## Audio Format Details

- **Format**: WAV (PCM)
- **Sample Rate**: 16 kHz (matches ESP32 audio)
- **Channels**: 1 (Mono)
- **Bit Depth**: 16-bit signed integer
- **Byte Order**: Little-endian

## Usage Examples

### Enable Recording
```json
{
  "audio_recording": {
    "enabled": true,
    "max_duration_seconds": 60
  }
}
```

### Disable Recording
```json
{
  "audio_recording": {
    "enabled": false
  }
}
```

### Short Recording Sessions
```json
{
  "audio_recording": {
    "enabled": true,
    "max_duration_seconds": 10
  }
}
```

## MQTT Control Commands

You can control recording remotely via MQTT commands:

### Topic Format
```
control/recording/{device_id}/{command}
```

### Available Commands

#### Start Recording
```bash
# Topic: control/recording/28:56:2f:07:c6:ec/start
# Payload: {"timestamp": "2025-11-01T12:34:56.789Z"}
```

#### Stop Recording
```bash
# Topic: control/recording/28:56:2f:07:c6:ec/stop
# Payload: {"timestamp": "2025-11-01T12:34:56.789Z"}
```

#### Get Status
```bash
# Topic: control/recording/28:56:2f:07:c6:ec/status
# Payload: {"timestamp": "2025-11-01T12:34:56.789Z"}
```

### Response Topics
Responses are published to:
```
control/recording/{device_id}/{command}/response
```

### Example Response Payloads

#### Status Response (Recording)
```json
{
  "timestamp": "2025-11-01T12:34:56.789Z",
  "device_id": "28:56:2f:07:c6:ec",
  "command": "status",
  "success": true,
  "recording": true,
  "enabled": true,
  "duration": 15.23,
  "stats": {
    "filePath": "/path/to/recordings/esp32_audio_28_56_2f_07_c6_ec_2025-11-01T12-34-56-789Z.wav",
    "totalBytes": 488190,
    "durationSeconds": 15.23
  }
}
```

#### Status Response (Not Recording)
```json
{
  "timestamp": "2025-11-01T12:34:56.789Z",
  "device_id": "28:56:2f:07:c6:ec",
  "command": "status",
  "success": true,
  "recording": false,
  "enabled": true,
  "duration": 0,
  "stats": null
}
```

### Test Scripts

#### MQTT Control Test
Use the provided test script to control recording via MQTT:

```bash
# Interactive mode
node test_recording_control.js

# Direct commands
node test_recording_control.js start
node test_recording_control.js stop
node test_recording_control.js status
node test_recording_control.js auto
```

#### Simple Recording Control
For basic testing without full MQTT setup:

```bash
# Interactive mode
node test_recording_simple.js

# Direct commands  
node test_recording_simple.js start
node test_recording_simple.js stop
node test_recording_simple.js status
```

#### Testing with Python Client
To test with real audio from the Python client (`main/xiaozhi-server/client.py`):

1. **Enable recording** in `config/mqtt.json`:
   ```json
   {
     "audio_recording": {
       "enabled": true,
       "max_duration_seconds": 60
     }
   }
   ```

2. **Start the MQTT Gateway**:
   ```bash
   cd main/mqtt-gateway
   node app.js
   ```

3. **Run the Python client**:
   ```bash
   cd main/xiaozhi-server
   python client.py
   ```

4. **Trigger audio**:
   - Press 's' in the Python client to start conversation
   - Speak into your microphone
   - Audio will be automatically recorded to `recordings/` directory

5. **Check recordings**:
   ```bash
   ls -la recordings/
   # Look for files like: esp32_audio_00_16_3e_ac_b5_38_2025-11-01T12-34-56-789Z.wav
   ```

## Log Messages

The system provides detailed logging for recording activities:

```
🎵 [WAV] Started recording incoming audio: esp32_audio_28_56_2f_07_c6_ec_2025-11-01T12-34-56-789Z.wav
   📊 Max duration: 30s

✅ [WAV] Saved WAV file: /path/to/recordings/esp32_audio_28_56_2f_07_c6_ec_2025-11-01T12-34-56-789Z.wav
   📊 Duration: 15.23s (recorded in 15.4s)
   📦 Size: 488234 bytes (488190 audio + 44 header)

🛑 [WAV] Stopped recording (connection_closed)
   ⏱️ Duration: 15.4s
   📁 File: /path/to/recordings/esp32_audio_28_56_2f_07_c6_ec_2025-11-01T12-34-56-789Z.wav
   📊 Audio data: 488190 bytes (15.23s)
```

## Audio Flow & Quality Analysis

### Audio Processing Pipeline

The MQTT Gateway processes audio in this sequence:

1. **Client Device** (ESP32/Python client):
   - Records microphone audio
   - Encodes to Opus format (16kHz, mono)
   - Encrypts with AES-CTR
   - Sends via UDP to gateway

2. **MQTT Gateway**:
   - Receives encrypted UDP packets
   - Decrypts with AES-CTR
   - **Detects audio format** (Opus vs raw PCM)
   - **Decodes Opus to PCM** (if Opus detected)
   - **Records PCM to WAV** ← *This is where recording happens*
   - Forwards PCM to LiveKit for AI processing

3. **LiveKit Agent**:
   - Receives clean PCM audio
   - Processes with AI (STT, LLM, TTS)

### What Gets Recorded

The WAV recording captures **decoded PCM audio** after:
- ✅ UDP decryption
- ✅ Opus decompression 
- ✅ Format conversion to 16kHz mono PCM

This means the recorded audio shows:
- **Actual quality** received by the AI agent
- **Effects of Opus compression** from the client
- **Network transmission quality** (packet loss, jitter)
- **Decryption/decoding accuracy**

### Quality Analysis

Use the recorded WAV files to:

1. **Check Audio Quality**: Play files with any audio player (VLC, Windows Media Player, etc.)
2. **Analyze with Tools**: Use audio analysis tools like Audacity, FFmpeg, or SoX
3. **Debug Issues**: Compare recordings from different devices or sessions
4. **Verify Format**: Confirm audio is being received correctly from ESP32 devices
5. **Measure Compression**: Compare with original client audio to see Opus quality impact

### Example Analysis Commands

```bash
# Get audio file information
ffprobe esp32_audio_*.wav

# Convert to other formats if needed
ffmpeg -i esp32_audio_*.wav -ar 48000 output_48khz.wav

# Analyze audio spectrum
sox esp32_audio_*.wav -n spectrogram

# Play audio file
ffplay esp32_audio_*.wav
```

## Troubleshooting

### No Audio Files Created
- Check that `audio_recording.enabled` is set to `true`
- Verify ESP32 device is sending audio data
- Check file permissions in the recordings directory

### Empty or Short Files
- ESP32 might not be sending audio data
- Check network connectivity
- Verify UDP audio streaming is working

### Large File Sizes
- Reduce `max_duration_seconds` for shorter recordings
- Consider the file size: 16kHz mono 16-bit = ~32KB per second

## Performance Impact

- **CPU**: Minimal impact - WAV writing is very efficient
- **Memory**: Small buffer for audio chunks (~1-2KB per chunk)
- **Disk**: ~32KB per second of audio (16kHz mono 16-bit)
- **Network**: No additional network overhead

## Security Considerations

- Audio files contain actual conversation data
- Ensure proper file permissions on the recordings directory
- Consider automatic cleanup of old recordings
- Be aware of privacy implications when recording audio