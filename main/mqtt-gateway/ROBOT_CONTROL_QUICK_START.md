# Robot Control Quick Start

## 🚀 Quick Test (3 Steps)

### Step 1: Start Test Subscriber
```bash
cd main/mqtt-gateway
node test_robot_subscriber.js
```

You should see:
```
✅ Connected to MQTT broker
🎧 Listening for robot control messages...
```

### Step 2: Start LiveKit Agent
```bash
cd main/livekit-server_simple
python simple_main.py dev
```

### Step 3: Test Voice Commands

Say any of these:
- **"Raise your hand"**
- **"Wave hello"**
- **"Nod your head"**
- **"Shake your head"**
- **"Lower your hand"**

## ✅ Expected Result

The test subscriber will show:
```
🤖 [2025-11-14T04:30:00.000Z] ROBOT CONTROL MESSAGE
   Topic: robot/control
   Data: {
     "action": "raise_hand",
     "timestamp": "2025-11-14T04:30:00.000Z",
     "request_id": "req_1731557400000",
     "source": "livekit_agent"
   }
```

## 📋 Available Commands

| Voice Command | Action | Description |
|--------------|--------|-------------|
| "Raise your hand" | `raise_hand` | Robot raises hand |
| "Lower your hand" | `lower_hand` | Robot lowers hand |
| "Wave hello" | `wave_hand` | Robot waves (greeting) |
| "Nod your head" | `nod_head` | Robot nods (yes) |
| "Shake your head" | `shake_head` | Robot shakes head (no) |

## 🤖 ESP32 Robot Setup

Your ESP32 should subscribe to: **`robot/control`**

**Message Format:**
```json
{
  "action": "raise_hand",
  "timestamp": "2025-11-14T04:30:00.000Z",
  "request_id": "req_1731557400000",
  "source": "livekit_agent"
}
```

**Arduino Example:**
```cpp
void callback(char* topic, byte* payload, unsigned int length) {
  if (strcmp(topic, "robot/control") == 0) {
    StaticJsonDocument<200> doc;
    deserializeJson(doc, payload, length);
    const char* action = doc["action"];
    
    if (strcmp(action, "raise_hand") == 0) raiseHand();
    else if (strcmp(action, "wave_hand") == 0) waveHand();
    // ... etc
  }
}

void setup() {
  mqttClient.subscribe("robot/control");
}
```

## 🔧 Troubleshooting

**No messages received?**
1. Check MQTT broker is running: `192.168.1.102:1883`
2. Check test subscriber is connected
3. Check gateway logs for "🤖 [ROBOT] Publishing"

**Function not called?**
1. Say command very clearly: "raise your hand"
2. Check agent logs for "🤖 Robot raise hand requested"

## 📚 Full Documentation

See `ROBOT_CONTROL_IMPLEMENTATION.md` for complete details.
