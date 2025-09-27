# Volume Control Test Questions

Test each volume function one by one using these questions with the AI assistant.

## 1. Set Volume Functions

**Test `self_set_volume()` and `set_device_volume()`:**
- "Set the volume to 50"
- "Change volume to 25"
- "Set volume to 80 percent"
- "Set the volume to 100"
- "Set volume to 0"

## 2. Get Volume Functions

**Test `self_get_volume()` and `get_device_volume()`:**
- "What's the current volume?"
- "Check the volume level"
- "What volume is it set to?"
- "Tell me the current volume"

## 3. Volume Up Functions

**Test `self_volume_up()`:**
- "Turn the volume up"
- "Increase the volume"
- "Make it louder"
- "Volume up"
- "Raise the volume"

## 4. Volume Down Functions

**Test `self_volume_down()`:**
- "Turn the volume down"
- "Decrease the volume"
- "Make it quieter"
- "Volume down"
- "Lower the volume"

## 5. Adjust Volume Functions

**Test `adjust_device_volume()` with custom steps:**
- "Increase volume by 20"
- "Turn volume up by 15"
- "Decrease volume by 10"
- "Raise volume by 5"
- "Lower volume by 30"

## 6. Mute Functions

**Test `self_mute()`:**
- "Mute the device"
- "Turn off the sound"
- "Silence it"
- "Mute audio"
- "Turn off volume"

## 7. Unmute Functions

**Test `self_unmute()`:**
- "Unmute the device"
- "Turn the sound back on"
- "Restore audio"
- "Unmute"
- "Turn volume back on"

## Testing Procedure

1. **Start the LiveKit server**
   ```bash
   cd D:\cheekofinal\xiaozhi-esp32-server\main\livekit-server
   python main.py
   ```

2. **Start the MQTT Gateway**
   ```bash
   cd D:\cheekofinal\xiaozhi-esp32-server\main\mqtt-gateway
   node app.js
   ```

3. **Connect via voice/chat interface**

4. **Test each question systematically**
   - Ask one question at a time
   - Wait for response
   - Check MQTT logs for proper MCP format
   - Verify ESP32 device responds correctly

## Expected MCP Message Format

The MQTT gateway should convert to this format:

```json
{
  "type": "mcp",
  "payload": {
    "method": "tools/call",
    "params": {
      "name": "self_set_volume",
      "arguments": {"volume": 50}
    },
    "jsonrpc": "2.0",
    "id": 123
  }
}
```

## Function Mapping

| User Intent | LiveKit Function | MCP Function Name | Arguments |
|-------------|------------------|-------------------|-----------|
| Set volume | `self_set_volume` | `self_set_volume` | `{volume: number}` |
| Get volume | `self_get_volume` | `self_get_volume` | `{}` |
| Volume up | `self_volume_up` | `self_volume_up` | `{step: number}` |
| Volume down | `self_volume_down` | `self_volume_down` | `{step: number}` |
| Mute | `self_mute` | `self_mute` | `{}` |
| Unmute | `self_unmute` | `self_unmute` | `{}` |

## Log Checking

**MQTT Gateway logs to monitor:**
- Function call received from LiveKit
- MCP message conversion
- Message sent to ESP32

**ESP32 logs to monitor:**
- MCP message received
- Function execution
- Volume change confirmation

## Troubleshooting

If any function doesn't work:
1. Check LiveKit server logs for function tool execution
2. Check MQTT gateway logs for message conversion
3. Check ESP32 logs for MCP message processing
4. Verify topic names match: `mcp_function_call`
5. Verify message format includes proper JSON-RPC 2.0 fields