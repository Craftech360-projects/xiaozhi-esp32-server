# Robot Control Implementation Guide

## Overview

This guide documents the complete implementation of robot control commands for your ESP32-based robot device. The system allows voice commands to control robot gestures like raising hand, waving, nodding, etc.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Voice Command                        │
│              "Hey robot, raise your hand"                    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              LiveKit Agent (simple_main.py)                  │
│  - Speech Recognition (Whisper/Groq)                        │
│  - LLM Processing (llama3.1:8b)                             │
│  - Function Call: raise_hand()                              │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│           MCP Executor (mcp_executor.py)                     │
│  - robot_control(action="raise_hand")                       │
│  - Calls: handle_robot_control()                            │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│           MCP Handler (mcp_handler.py)                       │
│  - Formats MCP message                                      │
│  - Sends via LiveKit data channel                           │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│           MQTT Gateway (app.js)                              │
│  - Receives MCP message                                     │
│  - Maps: self_robot_control → self.robot.control           │
│  - Publishes to MQTT topic: robot/control                  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              MQTT Broker (192.168.1.102:1883)               │
│  Topic: robot/control                                       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│           ESP32 Robot / Test Subscriber                      │
│  - Subscribes to: robot/control                             │
│  - Receives: {"action": "raise_hand", ...}                  │
│  - Executes robot movement                                  │
└─────────────────────────────────────────────────────────────┘
```

## Implementation Details

### 1. Robot Control Functions (simple_main.py)

Added 5 new MCP tool functions:

```python
@function_tool
async def raise_hand(self, context: RunContext) -> str:
    """Make the robot raise its hand"""
    result = await self.mcp_executor.robot_control("raise_hand")
    return result

@function_tool
async def lower_hand(self, context: RunContext) -> str:
    """Make the robot lower its hand"""
    result = await self.mcp_executor.robot_control("lower_hand")
    return result

@function_tool
async def wave_hand(self, context: RunContext) -> str:
    """Make the robot wave its hand"""
    result = await self.mcp_executor.robot_control("wave_hand")
    return result

@function_tool
async def nod_head(self, context: RunContext) -> str:
    """Make the robot nod its head (yes gesture)"""
    result = await self.mcp_executor.robot_control("nod_head")
    return result

@function_tool
async def shake_head(self, context: RunContext) -> str:
    """Make the robot shake its head (no gesture)"""
    result = await self.mcp_executor.robot_control("shake_head")
    return result
```

### 2. MCP Executor Method (mcp_executor.py)

```python
async def robot_control(self, action: str) -> str:
    """
    Send robot control command
    
    Args:
        action: Robot action (raise_hand, lower_hand, wave_hand, nod_head, shake_head)
    """
    await handle_robot_control(self.mcp_client, action)
    
    action_messages = {
        "raise_hand": "Raising hand",
        "lower_hand": "Lowering hand",
        "wave_hand": "Waving hand",
        "nod_head": "Nodding head",
        "shake_head": "Shaking head"
    }
    
    message = action_messages.get(action, f"Executing {action}")
    return f"{message}."
```

### 3. MCP Handler (mcp_handler.py)

```python
async def handle_robot_control(mcp_client: LiveKitMCPClient, action: str) -> Dict:
    """Handle robot control command"""
    
    # Validate action
    valid_actions = ["raise_hand", "lower_hand", "wave_hand", "nod_head", "shake_head"]
    if action not in valid_actions:
        raise ValueError(f"Invalid action. Must be one of: {', '.join(valid_actions)}")
    
    arguments = {"action": action}
    result = await mcp_client.send_function_call("robot_control", arguments)
    return result
```

### 4. MQTT Gateway Updates (app.js)

**Action Mapping:**
```javascript
const actionToFunctionMap = {
  // ... existing mappings ...
  'robot_control': 'self_robot_control'
};
```

**Function to MCP Tool Mapping:**
```javascript
const functionToMcpToolMap = {
  // ... existing mappings ...
  'self_robot_control': 'self.robot.control'
};
```

**Robot Control Topic Publishing:**
```javascript
// In sendMcpMessage method
if (toolName === 'self.robot.control' && this.mqttClient && this.mqttClient.connected) {
  const robotMessage = {
    action: toolArgs.action,
    timestamp: new Date().toISOString(),
    request_id: `req_${requestId}`,
    source: 'livekit_agent'
  };
  
  this.mqttClient.publish('robot/control', JSON.stringify(robotMessage));
}
```

## MQTT Topic Structure

### Topic: `robot/control`

**Message Format:**
```json
{
  "action": "raise_hand",
  "timestamp": "2025-11-14T04:30:00.000Z",
  "request_id": "req_1731557400000",
  "source": "livekit_agent"
}
```

**Valid Actions:**
- `raise_hand` - Raise robot's hand
- `lower_hand` - Lower robot's hand
- `wave_hand` - Wave hand (greeting gesture)
- `nod_head` - Nod head (yes gesture)
- `shake_head` - Shake head (no gesture)

## Testing

### 1. Start Test Subscriber

```bash
cd main/mqtt-gateway
node test_robot_subscriber.js
```

**Expected Output:**
```
🤖 Robot Control Test Subscriber
================================
MQTT Broker: 192.168.1.102:1883

✅ Connected to MQTT broker

📡 Subscribing to topics:
   ✓ robot/control
   ✓ robot/status
   ✓ robot/#

🎧 Listening for robot control messages...
   (Press Ctrl+C to exit)
```

### 2. Start LiveKit Agent

```bash
cd main/livekit-server_simple
python simple_main.py dev
```

### 3. Test Voice Commands

Say any of these commands:
- "Raise your hand"
- "Wave hello"
- "Nod your head"
- "Shake your head"
- "Lower your hand"

### 4. Verify MQTT Messages

The test subscriber should show:

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

## ESP32 Robot Implementation

Your ESP32 robot should subscribe to `robot/control` and handle messages:

```cpp
// Arduino/ESP32 Example
#include <PubSubClient.h>

void callback(char* topic, byte* payload, unsigned int length) {
  if (strcmp(topic, "robot/control") == 0) {
    // Parse JSON
    StaticJsonDocument<200> doc;
    deserializeJson(doc, payload, length);
    
    const char* action = doc["action"];
    
    // Execute robot action
    if (strcmp(action, "raise_hand") == 0) {
      raiseHand();
    } else if (strcmp(action, "lower_hand") == 0) {
      lowerHand();
    } else if (strcmp(action, "wave_hand") == 0) {
      waveHand();
    } else if (strcmp(action, "nod_head") == 0) {
      nodHead();
    } else if (strcmp(action, "shake_head") == 0) {
      shakeHead();
    }
  }
}

void setup() {
  // Subscribe to robot control topic
  mqttClient.subscribe("robot/control");
}
```

## System Prompt Updates

The LLM is instructed to use robot control functions only when explicitly requested:

```
Robot Control:
- raise_hand: Make robot raise its hand
- lower_hand: Make robot lower its hand
- wave_hand: Make robot wave (greeting gesture)
- nod_head: Make robot nod head (yes gesture)
- shake_head: Make robot shake head (no gesture)

IMPORTANT: Use these functions ONLY when the user EXPLICITLY asks you to:
- "raise your hand" → use raise_hand
- "wave hello" → use wave_hand
- "nod your head" → use nod_head
```

## Troubleshooting

### No MQTT Messages Received

1. **Check MQTT Broker Connection:**
   ```bash
   # Test MQTT broker
   mosquitto_sub -h 192.168.1.102 -p 1883 -t "robot/#" -v
   ```

2. **Check Gateway Logs:**
   ```bash
   cd main/mqtt-gateway
   npm start
   # Look for: "🤖 [ROBOT] Publishing to robot/control topic"
   ```

3. **Check Agent Logs:**
   ```bash
   # Look for: "🤖 Robot raise hand requested"
   # Look for: "🤖 Sending robot control command: raise_hand"
   ```

### Function Not Being Called

1. **Check System Prompt:** Ensure robot control functions are listed
2. **Test Direct Command:** Say "raise your hand" (very explicit)
3. **Check LLM Logs:** Look for function_call in agent logs

### MQTT Topic Not Created

1. **Check Gateway MQTT Client:** Ensure `this.mqttClient.connected` is true
2. **Check Topic Name:** Should be exactly `robot/control` (no device ID)
3. **Check Publish Permissions:** Ensure MQTT user has publish rights

## Files Modified

1. `main/livekit-server_simple/simple_main.py` - Added 5 robot control functions
2. `main/livekit-server_simple/src/mcp/mcp_executor.py` - Added robot_control method
3. `main/livekit-server_simple/src/mcp/mcp_handler.py` - Added handle_robot_control
4. `main/mqtt-gateway/app.js` - Added robot control mapping and topic publishing
5. `main/mqtt-gateway/test_robot_subscriber.js` - Created test subscriber

## Next Steps

1. ✅ Test with test subscriber
2. ⏳ Implement ESP32 robot subscriber
3. ⏳ Add robot status feedback (optional)
4. ⏳ Add more robot actions (optional)

---

**Status**: ✅ Implementation Complete  
**Date**: 2025-11-14  
**Topic**: `robot/control` (simple, no device ID)
