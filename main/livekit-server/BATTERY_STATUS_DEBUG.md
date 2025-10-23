# Battery Status Debug Guide

## Expected Log Flow

When you test the battery status function, you should see these logs in sequence:

### 1. LiveKit Agent - Function Call
```
🔋 check_battery_level called
🔋 Context set on mcp_executor, calling get_battery_status
Sending battery status request and waiting for response...
```

### 2. MQTT Gateway - Response Received from Device
```
📨 [MQTT IN] Device message from internal/server-ingest - Device: 68:25:dd:ba:39:78, Message type: mcp
🔋 [MCP-RESPONSE] Processing MCP response from device 68:25:dd:ba:39:78
```

### 3. MQTT Gateway - Forwarding to LiveKit
```
🔋 [MCP-FORWARD] Forwarding MCP response for device 68:25:dd:ba:39:78
✅ [MCP-FORWARD] Successfully forwarded MCP response to LiveKit agent
✅ [MCP-FORWARD] Request ID: req_XXXXX
```

### 4. LiveKit Server - Response Received
```
🔋 [MCP-RECEIVE] ====== MCP RESPONSE RECEIVED ======
🔋 [MCP-RECEIVE] Full message received: {...}
🔋 [MCP-PAYLOAD] Extracted payload: {...}
🔋 [MCP-IDS] Request ID: req_XXXXX
🔋 [MCP-DATA] Actual battery data: {"voltage_mv":3608,"percentage":40,...}
```

### 5. LiveKit Server - Forwarding to MCP Client
```
✅ [MCP-FORWARD] Forwarding to mcp_client.handle_response()
✅ [MCP-FORWARD] Request ID: req_XXXXX
✅ [MCP-FORWARD] handle_response() call completed
🔋 [MCP-RECEIVE] ====== MCP RESPONSE PROCESSING COMPLETE ======
```

### 6. MCP Client - Response Matched
```
✅ Response handled for request req_XXXXX
```

### 7. LiveKit Agent - Function Returns
```
Parsed battery data: {'voltage_mv': 3608, 'percentage': 40, 'state': 'normal', 'charging': False}
Returning battery status: Battery is at 40% (3.61V)
🔋 check_battery_level result: Battery is at 40% (3.61V)
```

## Troubleshooting

### If timeout occurs (no response after 5 seconds):

**Check MQTT Gateway logs for:**
- ❌ Missing: `🔋 [MCP-RESPONSE] Processing MCP response`
  - **Issue**: Gateway not detecting MCP response from device
  - **Check**: Device is sending MCP response to topic `internal/server-ingest`

- ❌ Missing: `✅ [MCP-FORWARD] Successfully forwarded`
  - **Issue**: Gateway can't publish to LiveKit data channel
  - **Check**: `deviceInfo.connection` has valid bridge and room

### If response not parsed correctly:

**Check LiveKit logs for:**
- ⚠️ `No request_id in MCP response, attempting fallback matching`
  - **Issue**: Request ID format mismatch
  - **Check**: MQTT gateway creating request_id as `req_${payload.id}`

- ⚠️ `Battery response has no content`
  - **Issue**: Payload structure not matching expected format
  - **Check**: Payload has `result.content[0].text` structure

## Expected Battery Data Structure

From ESP32 device:
```json
{
  "voltage_mv": 3608,
  "percentage": 40,
  "state": "normal",
  "charging": false,
  "low_battery": false,
  "critical_battery": false
}
```

Wrapped in MCP response:
```json
{
  "type": "mcp",
  "payload": {
    "id": 1234567890,
    "result": {
      "content": [
        {
          "type": "text",
          "text": "{\"voltage_mv\":3608,\"percentage\":40,...}"
        }
      ]
    }
  }
}
```

## Testing Command

Ask the device: "What's the battery level?" or "Check battery status"

The agent should respond with natural language like:
- "Battery is at 40% (3.61V)"
- "Battery is at 75% (4.05V) and charging"
- "Battery is at 15% (3.45V). Battery is low, please charge soon."
