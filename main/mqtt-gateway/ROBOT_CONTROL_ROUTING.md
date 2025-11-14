# Robot Control Message Routing

## Overview

Robot control messages are routed ONLY to the robot via MQTT topic `robot/control`, NOT to the ESP32 device.

## Message Flow

```
Voice Command: "Raise your hand"
         ↓
LiveKit Agent (simple_main.py)
         ↓
MCP Executor → robot_control("raise_hand")
         ↓
MCP Handler → send function_call("robot_control")
         ↓
MQTT Gateway (app.js)
         ↓
    ┌────┴────┐
    │         │
    ✅        ❌
    │         │
robot/control  ESP32 Device
  (MQTT)      (SKIPPED)
    │
    ↓
Robot Subscriber
```

## Gateway Logic

### handleFunctionCall() - Updated

```javascript
// Special handling: Robot control - ONLY publish to robot/control topic
if (functionCall.name === 'self_robot_control') {
  // Publish to robot/control topic
  this.mqttClient.publish('robot/control', JSON.stringify(robotMessage));
  
  return; // ⚠️ IMPORTANT: Don't send to ESP32 device
}

// All other functions go to ESP32 device
const mcpToolName = functionToMcpToolMap[functionCall.name];
this.connection.sendMqttMessage(JSON.stringify(message));
```

## Why This Design?

1. **Separation of Concerns**: Robot is a separate device from ESP32
2. **No Firmware Update**: ESP32 doesn't need to know about robot commands
3. **Simple Topic**: `robot/control` is easy to subscribe to
4. **Scalability**: Can add more robots without changing ESP32

## Message Format

### Topic: `robot/control`

```json
{
  "action": "raise_hand",
  "timestamp": "2025-11-14T04:30:00.000Z",
  "request_id": "req_1731557400000",
  "source": "livekit_agent",
  "device_mac": "68:25:dd:ba:fb:44"
}
```

### Valid Actions
- `raise_hand`
- `lower_hand`
- `wave_hand`
- `nod_head`
- `shake_head`

## Testing

### 1. Start Test Subscriber
```bash
cd main/mqtt-gateway
node test_robot_subscriber.js
```

### 2. Say Command
"Robot, raise your hand"

### 3. Expected Gateway Logs
```
🤖 [ROBOT] Publishing to robot/control topic: {"action":"raise_hand",...}
✅ [ROBOT] Published to robot/control successfully
```

### 4. Expected Test Subscriber Output
```
🤖 [2025-11-14T...] ROBOT CONTROL MESSAGE
   Topic: robot/control
   Data: {
     "action": "raise_hand",
     "timestamp": "2025-11-14T...",
     "request_id": "req_...",
     "source": "livekit_agent",
     "device_mac": "68:25:dd:ba:fb:44"
   }
```

## What Changed

### Before ❌
- Robot control sent to ESP32 device
- ESP32 returned "Unknown tool: robot_control" error
- Message also sent to robot/control topic (duplicate)

### After ✅
- Robot control ONLY sent to robot/control topic
- ESP32 device never receives robot commands
- No errors from ESP32
- Clean separation of robot and ESP32 control

## Implementation Details

### Files Modified
1. `main/mqtt-gateway/app.js` - Updated `handleFunctionCall()`
   - Added early return for `self_robot_control`
   - Publishes only to `robot/control` topic
   - Skips ESP32 device message

### Function Mapping (ESP32 Only)
```javascript
const functionToMcpToolMap = {
  'self_set_volume': 'self.audio_speaker.set_volume',      // → ESP32
  'self_set_light_color': 'self.led.set_color',            // → ESP32
  'self_get_battery_status': 'self.battery.get_status',    // → ESP32
  'self_robot_control': 'self.robot.control'               // → robot/control (NOT ESP32)
};
```

## Robot Subscriber Implementation

Your robot should subscribe to `robot/control`:

```python
# Python Example
import paho.mqtt.client as mqtt

def on_message(client, userdata, msg):
    if msg.topic == "robot/control":
        data = json.loads(msg.payload)
        action = data['action']
        
        if action == 'raise_hand':
            robot.raise_hand()
        elif action == 'lower_hand':
            robot.lower_hand()
        # ... etc

client = mqtt.Client()
client.on_message = on_message
client.connect("192.168.1.102", 1883)
client.subscribe("robot/control")
client.loop_forever()
```

## Summary

✅ Robot control messages go ONLY to `robot/control` topic  
✅ ESP32 device never receives robot commands  
✅ No firmware update needed for ESP32  
✅ Clean separation of concerns  
✅ Easy to test with test subscriber  

---

**Status**: ✅ Complete  
**Date**: 2025-11-14  
**Topic**: `robot/control` (robot only, not ESP32)
