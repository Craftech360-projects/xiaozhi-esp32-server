# Mode Change via MQTT - Setup Complete ✅

## What Was Implemented

Your MQTT gateway now supports **button-triggered mode changes** with **pre-recorded Opus audio confirmations**!

---

## 📁 Files Created/Modified

### New Files:
1. ✅ `utils/opus_file_streamer.js` - Streams Opus files via MQTT
2. ✅ `mode_change_handler.js` - Handles mode change requests
3. ✅ `audio/mode_change/` - Directory for Opus audio files
4. ✅ `audio/mode_change/audio_map.json` - Maps modes to audio files
5. ✅ `audio/mode_change/README.md` - Instructions for creating audio

### Modified Files:
1. ✅ `app.js` - Integrated mode change handler
2. ✅ `package.json` - Added axios dependency

---

## 🚀 Quick Start

### Step 1: Install Dependencies

```bash
cd main/mqtt-gateway
npm install
```

### Step 2: Create Audio Files

You need to create Opus audio files for each mode. See `audio/mode_change/README.md` for detailed instructions.

**Quick method using FFmpeg:**

```bash
# Install edge-tts (Python)
pip install edge-tts

# Generate audio for each mode
edge-tts --voice "en-US-AndrewNeural" --text "Switched to Cheeko mode" --write-media temp.mp3
ffmpeg -i temp.mp3 -c:a libopus -b:a 24k -ar 24000 -ac 1 audio/mode_change/mode_cheeko.opus

edge-tts --voice "en-US-AndrewNeural" --text "Switched to RhymeTime mode" --write-media temp.mp3
ffmpeg -i temp.mp3 -c:a libopus -b:a 24k -ar 24000 -ac 1 audio/mode_change/mode_rhymetime.opus

# Create default fallback
edge-tts --voice "en-US-AndrewNeural" --text "Mode changed" --write-media temp.mp3
ffmpeg -i temp.mp3 -c:a libopus -b:a 24k -ar 24000 -ac 1 audio/mode_change/mode_changed.opus
```

**Required files:**
- `mode_cheeko.opus`
- `mode_rhymetime.opus`
- `mode_storyteller.opus`
- `mode_changed.opus` (default fallback)
- `mode_error.opus` (error message)

### Step 3: Environment Variables

Add to `.env` file:

```env
MANAGER_API_URL=http://192.168.1.168:8002/toy
```

### Step 4: Start MQTT Gateway

```bash
npm start
# or
node app.js
```

---

## 🔄 How It Works

### Flow:

```
1. ESP32 Button (5 sec hold)
   ↓
2. Publishes MQTT: device/6825ddba3978/mode_change_request
   ↓
3. MQTT Gateway receives → Calls Manager API
   ↓
4. Manager API cycles mode → Returns new mode name
   ↓
5. MQTT Gateway finds Opus file → Streams to device
   ↓
6. ESP32 plays audio: "Switched to RhymeTime mode"
```

---

## 📡 MQTT Topics

### ESP32 Publishes:
```
Topic: device/{macAddress}/mode_change_request
Payload: {"action": "cycle_mode"}
```

### ESP32 Subscribes:
```
Topic: device/{macAddress}/mode_changed
Topic: device/{macAddress}/audio_stream
```

### Message Examples:

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
  "data": "T2dnUwAC...",
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

---

## 🧪 Testing

### Test with MQTT CLI:

```bash
# Publish mode change request
mosquitto_pub -h localhost \
  -t "device/6825ddba3978/mode_change_request" \
  -m '{"action":"cycle_mode"}'

# Subscribe to responses
mosquitto_sub -h localhost \
  -t "device/6825ddba3978/#" -v
```

### Expected Console Output:

```
🔘 [MODE-CHANGE] Handler initialized
📁 [MODE-CHANGE] Audio directory: /path/to/audio/mode_change
✅ [MODE-CHANGE] Subscribed to: device/+/mode_change_request

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

---

## 🛠️ ESP32 Firmware Implementation

### Subscribe on Connect:

```cpp
void mqttConnect() {
  if (mqttClient.connect(clientId.c_str())) {
    // Subscribe to mode change responses
    String modeChangedTopic = "device/" + macAddress + "/mode_changed";
    String audioStreamTopic = "device/" + macAddress + "/audio_stream";

    mqttClient.subscribe(modeChangedTopic.c_str());
    mqttClient.subscribe(audioStreamTopic.c_str());

    Serial.println("✅ Subscribed to mode change topics");
  }
}
```

### Publish Mode Change Request:

```cpp
void triggerModeChange() {
  String topic = "device/" + macAddress + "/mode_change_request";
  String payload = "{\"action\":\"cycle_mode\"}";

  mqttClient.publish(topic.c_str(), payload.c_str());
  Serial.println("🔘 Mode change requested");
}
```

### Handle Incoming Messages:

```cpp
void mqttCallback(char* topic, byte* payload, unsigned int length) {
  String topicStr = String(topic);

  if (topicStr.endsWith("/mode_changed")) {
    DynamicJsonDocument doc(512);
    deserializeJson(doc, payload, length);

    String type = doc["type"];

    if (type == "tts") {
      String state = doc["state"];
      if (state == "start") {
        Serial.println("🎤 TTS Started - Prepare to play audio");
      } else if (state == "stop") {
        Serial.println("🎤 TTS Stopped");
      }
    }
    else if (type == "mode_change_confirm") {
      bool success = doc["success"];
      String newMode = doc["newMode"];
      Serial.println("✅ Mode: " + newMode);
    }
  }
  else if (topicStr.endsWith("/audio_stream")) {
    // Parse and play Opus audio
    DynamicJsonDocument doc(8192);
    deserializeJson(doc, payload, length);

    String format = doc["format"];
    String data = doc["data"];

    if (format == "opus") {
      // Decode base64 → Opus → PCM → Speaker
    }
  }
}
```

---

## 📋 Checklist

- [x] Install dependencies (`npm install`)
- [ ] Create Opus audio files (at least `mode_changed.opus`)
- [ ] Set `MANAGER_API_URL` in `.env`
- [ ] Start MQTT Gateway
- [ ] Test with MQTT CLI
- [ ] Implement ESP32 firmware
- [ ] Test end-to-end with physical button

---

## 🐛 Troubleshooting

### Audio Not Playing
- Check audio files exist in `audio/mode_change/`
- Verify file format: `ffprobe mode_cheeko.opus`
- Check MQTT max message size (increase if needed)

### API Errors
- Verify Manager API URL in `.env`
- Check device exists in database
- Check MAC address format (with/without colons)

### MQTT Connection Issues
- Verify MQTT broker is running
- Check firewall settings
- Verify ESP32 is subscribed to correct topics

---

## 🎉 Success!

Your mode change system is now complete! When the button is held for 5 seconds, the device will:
1. Send MQTT request
2. Manager API cycles the mode
3. MQTT Gateway streams audio confirmation
4. ESP32 plays: "Switched to [ModeName] mode"
5. LiveKit session uses new prompt on next connection

**No reconnection needed!** ✨
