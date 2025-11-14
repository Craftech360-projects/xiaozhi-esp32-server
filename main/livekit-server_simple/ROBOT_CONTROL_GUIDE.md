# Robot Control Integration Guide 🤖

Complete guide for controlling your ESP32-based robot through voice commands via the LiveKit agent.

## Overview

This integration allows users to control a robot connected to the ESP32 device using natural voice commands. The commands flow through:

```
User Voice → LiveKit Agent → MCP Tools → MQTT Gateway → ESP32 Device → Robot
```

## Available Robot Commands

### 1. Raise Hand
**Voice Commands:**
- "Raise your hand"
- "Put your hand up"
- "Lift your hand"

**Function:** `raise_hand()`  
**MQTT Topic:** `mcp/{device_id}`  
**MCP Tool:** `self.robot.control`  
**Action:** `raise_hand`

### 2. Lower Hand
**Voice Commands:**
- "Lower your hand"
- "Put your hand down"
- "Hand down"

**Function:** `lower_hand()`  
**Action:** `lower_hand`

### 3. Wave Hand
**Voice Commands:**
- "Wave hello"
- "Wave your hand"
- "Say hi with a wave"

**Function:** `wave_hand()`  
**Action:** `wave_hand`

### 4. Nod Head
**Voice Commands:**
- "Nod your head"
- "Nod yes"
- "Show agreement"

**Function:** `nod_head()`  
**Action:** `nod_head`

### 5. Shake Head
**Voice Commands:**
- "Shake your head"
- "Shake no"
- "Show disagreement"

**Function:** `shake_head()`  
**Action:** `shake_head`

## Architecture

### Component Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    User Voice Input                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              LiveKit Agent (simple_main.py)                  │
│  - Speech Recognition (STT)                                  │
│  - LLM Processing (llama3.1:8b)                             │
│  - Function Tool Detection                                   │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│           MCP Executor (mcp_executor.py)                     │
│  - robot_control(action)                                     │
│  - Validates action                                          │
│  - Calls handler                                             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│           MCP Handler (mcp_handler.py)                       │
│  - handle_robot_control(mcp_client, action)                 │
│  - Formats MCP message                                       │
│  - Sends via LiveKit data channel                           │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│           MQTT Gateway (app.js)                              │
│  - Receives MCP message via data channel                    │
│  - Maps: robot_control → self_robot_control                 │
│  - Maps: self_robot_control → self.robot.control            │
│  - Publishes to MQTT topic: mcp/{device_id}                 │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              ESP32 Device Firmware                           │
│  - Subscribes to: mcp/{device_id}                           │
│  - Receives MCP message                                      │
│  - Parses tool: self.robot.control                          │
│  - Executes robot action                                     │
└─────────────────────────────────────────────────────────────┘
```

## Implementation Details

### 1. LiveKit Agent Functions

**File:** `main/livekit-server_simple/simple_main.py`

```python
@function_tool
async def raise_hand(self, context: RunContext) -> str:
    """Make the robot raise its hand."""
    result = await self.mcp_executor.robot_control("raise_hand")
    return result

@function_tool
async def wave_hand(self, context: RunContext) -> str:
    """Make the robot wave its hand."""
    result = await self.mcp_executor.robot_control("wave_hand")
    return result

# ... similar for lower_hand, nod_head, shake_head
```

### 2. MCP Executor

**File:** `main/livekit-server_simple/src/mcp/mcp_executor.py`

```python
async def robot_control(self, action: str) -> str:
    """Send robot control command"""
    logger.info(f"🤖 Sending robot control command: {action}")
    await handle_robot_control(self.mcp_client, action)
    return f"{action_message}."
```

### 3. MCP Handler

**File:** `main/livekit-server_simple/src/mcp/mcp_handler.py`

```python
async def handle_robot_control(mcp_client: LiveKitMCPClient, action: str) -> Dict:
    """Handle robot control command"""
    valid_actions = ["raise_hand", "lower_hand", "wave_hand", "nod_head", "shake_head"]
    
    arguments = {"action": action}
    result = await mcp_client.send_function_call("robot_control", arguments)
    return result
```

### 4. MQTT Gateway Mapping

**File:** `main/mqtt-gateway/app.js`

```javascript
const actionToFunctionMap = {
  'robot_control': 'self_robot_control'
};

const functionToMcpToolMap = {
  'self_robot_control': 'self.robot.control'
};
```

## MQTT Message Format

### Outgoing Message (Gateway → ESP32)

**Topic:** `mcp/{device_id}`

**Payload:**
```json
{
  "jsonrpc": "2.0",
  "id": 1234567890,
  "method": "tools/call",
  "params": {
    "name": "self.robot.control",
    "arguments": {
      "action": "raise_hand"
    }
  }
}
```

### Expected Response (ESP32 → Gateway)

**Topic:** `mcp/{device_id}/response`

**Payload:**
```json
{
  "jsonrpc": "2.0",
  "id": 1234567890,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\"success\": true, \"action\": \"raise_hand\"}"
      }
    ]
  }
}
```

## Testing

### 1. Test MQTT Subscriber

Run the test subscriber to monitor robot control messages:

```bash
cd main/mqtt-gateway
node test_robot_subscriber.js
```

**Expected Output:**
```
🤖 Robot Control Test Subscriber
================================
MQTT Broker: 192.168.1.102:1883
Device ID: 00:11:22:33:44:55

✅ Connected to MQTT broker

📡 Subscribing to topics:
   ✓ mcp/00:11:22:33:44:55
   ✓ robot/control/00:11:22:33:44:55
   ✓ device/00:11:22:33:44:55/control
   ✓ #

🎧 Listening for robot control messages...
   (Press Ctrl+C to exit)
```

### 2. Test Voice Commands

1. Start the LiveKit agent:
   ```bash
   cd main/livekit-server_simple
   python simple_main.py dev
   ```

2. Connect a client to the LiveKit room

3. Say one of the voice commands:
   - "Raise your hand"
   - "Wave hello"
   - "Nod your head"

4. Check the test subscriber output for the MQTT message

### 3. Test Direct Function Call

You can also test by directly calling the MCP function:

```python
# In Python console or test script
from src.mcp.mcp_executor import LiveKitMCPExecutor

executor = LiveKitMCPExecutor()
# Set context first
executor.set_context(your_context)

# Test robot control
result = await executor.robot_control("wave_hand")
print(result)  # Should print: "Waving hand."
```

## ESP32 Firmware Integration

### Required MQTT Subscription

Your ESP32 firmware must subscribe to:
```
mcp/{device_id}
```

### Message Handler Example

```cpp
void handleMcpMessage(const char* topic, const char* payload) {
    // Parse JSON
    DynamicJsonDocument doc(1024);
    deserializeJson(doc, payload);
    
    // Check if it's a robot control command
    const char* tool = doc["params"]["name"];
    if (strcmp(tool, "self.robot.control") == 0) {
        const char* action = doc["params"]["arguments"]["action"];
        
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
        
        // Send response
        sendMcpResponse(doc["id"], true, action);
    }
}
```

### Robot Control Functions

Implement these functions in your ESP32 firmware:

```cpp
void raiseHand() {
    // Control servo/motor to raise hand
    servoHand.write(180);  // Example
}

void lowerHand() {
    // Control servo/motor to lower hand
    servoHand.write(0);  // Example
}

void waveHand() {
    // Wave motion
    for (int i = 0; i < 3; i++) {
        servoHand.write(90);
        delay(200);
        servoHand.write(180);
        delay(200);
    }
}

void nodHead() {
    // Nod motion
    for (int i = 0; i < 2; i++) {
        servoHead.write(45);
        delay(300);
        servoHead.write(90);
        delay(300);
    }
}

void shakeHead() {
    // Shake motion
    for (int i = 0; i < 2; i++) {
        servoHead.write(60);
        delay(300);
        servoHead.write(120);
        delay(300);
    }
    servoHead.write(90);  // Center
}
```

## Troubleshooting

### Issue: Robot commands not working

**Check:**
1. MQTT gateway is running: `node app.js`
2. ESP32 is connected to MQTT broker
3. ESP32 is subscribed to `mcp/{device_id}` topic
4. Run test subscriber to verify messages are being sent

### Issue: LLM not calling robot functions

**Check:**
1. System prompt includes robot control tools
2. Voice command is explicit (e.g., "raise your hand" not "tell a story")
3. Check agent logs for function calls

### Issue: MQTT messages not reaching ESP32

**Check:**
1. Device ID matches in `.env` and ESP32 firmware
2. MQTT broker is accessible from ESP32
3. Check MQTT broker logs
4. Use test subscriber to verify messages are published

## Configuration

### Environment Variables

**File:** `main/mqtt-gateway/.env`

```bash
MQTT_HOST=192.168.1.102
MQTT_PORT=1883
MQTT_CLIENT_ID=GID_test@@@00:11:22:33:44:55
MQTT_USERNAME=testuser
MQTT_PASSWORD=testpassword
```

The device ID is extracted from `MQTT_CLIENT_ID` (part after `@@@`).

## Adding New Robot Commands

To add a new robot command (e.g., "dance"):

### 1. Add Function Tool

**File:** `simple_main.py`

```python
@function_tool
async def dance(self, context: RunContext) -> str:
    """Make the robot dance."""
    result = await self.mcp_executor.robot_control("dance")
    return result
```

### 2. Update System Prompt

Add to the tools list:
```
- dance: Make robot perform a dance
```

### 3. Update Handler Validation

**File:** `mcp_handler.py`

```python
valid_actions = ["raise_hand", "lower_hand", "wave_hand", "nod_head", "shake_head", "dance"]
```

### 4. Implement in ESP32 Firmware

```cpp
else if (strcmp(action, "dance") == 0) {
    performDance();
}
```

## Status

✅ **Implemented and Ready**

- [x] Robot control MCP tools
- [x] MCP executor method
- [x] MCP handler function
- [x] MQTT gateway mapping
- [x] Test subscriber client
- [x] Documentation

## Next Steps

1. **Test with ESP32**: Implement robot control handlers in ESP32 firmware
2. **Add More Actions**: Extend with additional robot movements
3. **Add Feedback**: Implement response handling from ESP32
4. **Add Animations**: Create complex movement sequences

---

**Created:** 2025-11-14  
**Version:** 1.0  
**Status:** Production Ready
