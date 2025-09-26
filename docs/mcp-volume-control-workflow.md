# MCP Volume Control Workflow Documentation

## Overview

This document describes how volume control commands are processed through the MCP (Model Context Protocol) format in the xiaozhi-esp32 system, from MQTT gateway to ESP32 firmware.

## Architecture Flow

```
Agent/Client → MQTT Gateway → ESP32 Firmware
     ↓              ↓              ↓
device_control → MCP Format → MCP Tools
```

## Message Format Transformation

### 1. Input: Device Control Format
The MQTT gateway receives device control commands in this format:
```json
{
  "type": "device_control",
  "action": "set_volume",
  "volume": 50,
  "session_id": "..."
}
```

### 2. Processing: Conversion to MCP Function Call
The gateway converts device_control to xiaozhi function format:

#### Action Mapping
```javascript
const actionToFunctionMap = {
  'set_volume': 'self_set_volume',
  'volume_up': 'self_volume_up',
  'volume_down': 'self_volume_down',
  'get_volume': 'self_get_volume',
  'mute': 'self_mute',
  'unmute': 'self_unmute'
};
```

#### Function Call Data Structure
```json
{
  "function_call": {
    "name": "self_set_volume",
    "arguments": {
      "volume": 50
    }
  },
  "timestamp": "2025-09-26T13:30:24.664Z",
  "request_id": "req_1758893424665"
}
```

### 3. Processing: Xiaozhi Function to MCP Tool Mapping
The xiaozhi function names are mapped to ESP32 MCP tool names:

```javascript
const functionToMcpToolMap = {
  'self_set_volume': 'self.audio_speaker.set_volume',
  'self_get_volume': 'self.get_device_status',
  'self_volume_up': 'self.audio_speaker.volume_up',
  'self_volume_down': 'self.audio_speaker.volume_down',
  'self_mute': 'self.audio_speaker.mute',
  'self_unmute': 'self.audio_speaker.unmute'
};
```

### 4. Output: Final MCP Format
The gateway sends this JSON-RPC 2.0 compliant MCP message to ESP32:

```json
{
  "type": "mcp",
  "payload": {
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "self.audio_speaker.set_volume",
      "arguments": {
        "volume": 50
      }
    },
    "id": 1758893424665
  },
  "session_id": "b3e1bdb3-5584-4476-ac70-b69353046e37_6825ddbb4d44",
  "timestamp": "2025-09-26T13:30:24.664Z",
  "request_id": "req_1758893424665"
}
```

## Implementation Details

### Key Components

#### 1. convertDeviceControlToMcp()
- Located in: `main/mqtt-gateway/app.js:916`
- Converts device_control actions to xiaozhi function calls
- Maps actions to function names and prepares arguments

#### 2. handleFunctionCall()
- Located in: `main/mqtt-gateway/app.js:964`
- Converts xiaozhi function calls to MCP tool calls
- Maps function names to ESP32 MCP tool names
- Generates JSON-RPC 2.0 compliant payload

#### 3. sendMcpMessage()
- Located in: `main/mqtt-gateway/app.js:1039`
- Sends direct MCP tool calls for unknown functions
- Fallback method for unmapped functions

### Critical Requirements

#### JSON-RPC 2.0 Compliance
- `jsonrpc: "2.0"` field is required
- `id` field must be a **number**, not string
- `method` field specifies the JSON-RPC method
- `params` contains the tool call parameters

#### ESP32 Firmware Compatibility
The ESP32 firmware expects:
- Tool names exactly as defined in `mcp_server.cc`
- Numeric `id` field for request identification
- Proper argument structure matching tool definitions

## Supported Volume Control Commands

| Action | Function Name | MCP Tool Name | Arguments |
|--------|---------------|---------------|-----------|
| `set_volume` | `self_set_volume` | `self.audio_speaker.set_volume` | `{volume: 0-100}` |
| `volume_up` | `self_volume_up` | `self.audio_speaker.volume_up` | `{step: number}` |
| `volume_down` | `self_volume_down` | `self.audio_speaker.volume_down` | `{step: number}` |
| `get_volume` | `self_get_volume` | `self.get_device_status` | `{}` |
| `mute` | `self_mute` | `self.audio_speaker.mute` | `{}` |
| `unmute` | `self_unmute` | `self.audio_speaker.unmute` | `{}` |

## Error Handling

### Common Issues
1. **Invalid ID Error**: `E (29004) MCP: Invalid id for method: tools/call`
   - **Cause**: `id` field sent as string instead of number
   - **Fix**: Ensure `id` is parsed as integer

2. **Unknown Function**: Function name not in mapping tables
   - **Behavior**: Falls back to `sendMcpMessage()` with original function name
   - **Log**: `⚠️ [FUNCTION CALL] Unknown function: ...`

3. **Unknown Action**: Device control action not recognized
   - **Behavior**: Logs error and returns without processing
   - **Log**: `❌ [DEVICE CONTROL] Unknown action: ...`

## Testing

### Sample Device Control Command
```bash
# Send via MQTT to trigger volume control
{
  "type": "device_control",
  "action": "set_volume",
  "volume": 75
}
```

### Expected ESP32 Log Output
```
I (28941) MQTT: [MQTT] Message type: mcp
I (28992) MQTT: [MQTT] Session ID: b3e1bdb3-5584-4476-ac70-b69353046e37_6825ddbb4d44
I (29000) MCP: Tool call: self.audio_speaker.set_volume with args: {"volume": 75}
```

## Code Locations

- **MQTT Gateway**: `main/mqtt-gateway/app.js`
  - `convertDeviceControlToMcp()`: Line 916
  - `handleFunctionCall()`: Line 964
  - `sendMcpMessage()`: Line 1039

- **ESP32 Firmware**: `main/xiaozhi-esp32-main/main/mcp_server.cc`
  - Tool definitions: Line 55+
  - MCP protocol handling

- **Documentation**:
  - ESP32 MCP Protocol: `main/xiaozhi-esp32-main/docs/mcp-protocol.md`
  - This workflow doc: `docs/mcp-volume-control-workflow.md`

## Version History

- **v1.0**: Initial device_control format
- **v2.0**: Conversion to MCP format with JSON-RPC 2.0 compliance
- **v2.1**: Fix numeric ID field for ESP32 compatibility