# Mode Change Integration Guide

## How to Integrate Mode Change Handler into app.js

### Step 1: Add Import at Top of app.js

```javascript
const { ModeChangeHandler } = require('./mode_change_handler');
```

### Step 2: Initialize Handler After MQTT Client Connection

Add this code after MQTT client connects successfully:

```javascript
// After: mqttClient = mqtt.connect(...)

// Initialize Mode Change Handler
let modeChangeHandler = null;

mqttClient.on('connect', () => {
  console.log('✅ [MQTT] Connected to MQTT broker');

  // Initialize mode change handler
  const config = {
    managerApiUrl: process.env.MANAGER_API_URL || 'http://192.168.1.168:8002/toy'
  };

  modeChangeHandler = new ModeChangeHandler(mqttClient, config);
  modeChangeHandler.initializeSubscriptions();
});
```

### Step 3: Add Message Handler

Add this to the MQTT message handler:

```javascript
mqttClient.on('message', async (topic, message) => {
  const parts = topic.split('/');

  // Handle mode change request: device/{macAddress}/mode_change_request
  if (parts[0] === 'device' && parts[2] === 'mode_change_request') {
    const macAddress = parts[1];

    try {
      const payload = JSON.parse(message.toString());
      await modeChangeHandler.handleModeChangeRequest(macAddress, payload);
    } catch (error) {
      console.error('❌ [MODE-CHANGE] Error parsing message:', error);
    }

    return; // Don't process further
  }

  // ... rest of your existing message handlers
});
```

### Step 4: Environment Variables

Add to your `.env` file:

```env
MANAGER_API_URL=http://192.168.1.168:8002/toy
```

## Testing

### 1. Prepare Audio Files

Place Opus audio files in `audio/mode_change/`:
- `mode_rhymetime.opus`
- `mode_cheeko.opus`
- `mode_changed.opus` (default)
- `mode_error.opus`

### 2. Test with MQTT Client

Publish test message:
```bash
mosquitto_pub -h localhost -t "device/6825ddba3978/mode_change_request" -m '{"action":"cycle_mode"}'
```

### 3. Expected Output

Console should show:
```
🔘 [MODE-CHANGE] Button pressed on device: 6825ddba3978
📡 [MODE-CHANGE] Calling API: http://192.168.1.168:8002/toy/agent/device/6825ddba3978/cycle-mode
✅ [MODE-CHANGE] Mode updated: Cheeko → RhymeTime
🎵 [OPUS-STREAMER] Streaming audio for mode: RhymeTime from mode_rhymetime.opus
📤 [OPUS-STREAMER] TTS start sent to 6825ddba3978
📦 [OPUS-STREAMER] Sent 15 audio packets
📤 [OPUS-STREAMER] TTS stop sent to 6825ddba3978
✅ [OPUS-STREAMER] Successfully streamed 60243 bytes to 6825ddba3978
📤 [MODE-CHANGE] Confirmation sent to 6825ddba3978
```

## MQTT Topics

### ESP32 Publishes:
- `device/{macAddress}/mode_change_request`
  ```json
  {"action": "cycle_mode"}
  ```

### ESP32 Subscribes:
- `device/{macAddress}/mode_changed` - TTS start/stop & confirmation
- `device/{macAddress}/audio_stream` - Opus audio packets

### Message Formats:

**TTS Start:**
```json
{
  "type": "tts",
  "state": "start",
  "text": "Switched to RhymeTime mode",
  "timestamp": 1728000000000
}
```

**Audio Packet:**
```json
{
  "type": "audio",
  "format": "opus",
  "index": 0,
  "data": "base64_encoded_opus_data...",
  "sample_rate": 24000,
  "channels": 1,
  "total_size": 60243,
  "chunk_size": 4000
}
```

**TTS Stop:**
```json
{
  "type": "tts",
  "state": "stop",
  "timestamp": 1728000000000
}
```

**Confirmation:**
```json
{
  "type": "mode_change_confirm",
  "timestamp": 1728000000000,
  "success": true,
  "newMode": "RhymeTime",
  "oldMode": "Cheeko",
  "agentId": "11507ab86d464c769803b12e228791c9"
}
```

## Troubleshooting

### Audio Not Streaming
1. Check audio files exist in `audio/mode_change/`
2. Verify file names match mode names
3. Check MQTT max message size settings

### API Errors
1. Verify `MANAGER_API_URL` in `.env`
2. Check Manager API is running
3. Verify device MAC exists in database

### MQTT Not Receiving
1. Check MQTT broker is running
2. Verify ESP32 is subscribed to correct topics
3. Check firewall/network settings
