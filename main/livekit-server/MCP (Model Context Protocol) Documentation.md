# MCP (Model Context Protocol) Documentation
## Overview
CheekoAI implements the Model Context Protocol (MCP) for AI assistant integration, providing tools to control device hardware, monitor status, and interact with sensors.

## Battery Status Tool

**Tool:**  `self.battery.get_status`
**Description:** Get detailed battery status information including voltage, percentage, state, and charging status.
**Parameters:** None
**Response Format:**
```json
{
    "voltage_mv": 3650,
    "percentage": 85,
    "state": "normal",
    "charging": false,
    "low_battery": false,
    "critical_battery": false
}
```
**Fields:**
-  `voltage_mv` (integer): Battery voltage in millivolts
-  `percentage` (integer): Battery percentage (0-100)
-  `state` (string): Battery state - "unknown", "normal", "low", "critical", "charging"
-  `charging` (boolean): Whether device is currently charging
-  `low_battery` (boolean): Whether battery is in low state
-  `critical_battery` (boolean): Whether battery is in critical state
## Complete MCP Tools Documentation
### 1. Device Status Tool
**Tool:**  `self.get_device_status`
**Description:** Provides real-time information of the device
**Parameters:** None
**Response Format:**
```json
{
	"audio_speaker": {
		"volume": 70
	},
	"screen": {
		"brightness": 100,
		"theme": "light"
	},
	"battery": {
		"level": 50,
		"charging": true,
		"discharging": false,
		"voltage_mv": 3650,
		"state": "normal"
	},
	"network": {
		"type": "wifi",
		"ssid": "CheekoAI",
		"rssi": -60
	},
	"chip": {
		"temperature": 25
	}
}
```
### 2. Audio Speaker Control
**Tool:**  `self.audio_speaker.set_volume`
**Description:** Set the volume of the audio speaker
**Parameters:**
-  `volume` (integer, 0-100): Volume level

**Response:** Boolean success

  

### 3. Screen Brightness Control
**Tool:**  `self.screen.set_brightness`
**Description:** Set the brightness of the screen
**Parameters:**
-  `brightness` (integer, 0-100): Brightness level  

**Response:** Boolean success


### 4. Screen Theme Control
**Tool:**  `self.screen.set_theme`
**Description:** Set the theme of the screen
**Parameters:**
-  `theme` (string): Theme name ("light" or "dark")

**Response:** Boolean success
### 5. Camera Photo Capture
**Tool:**  `self.camera.take_photo`
**Description:** Take a photo and explain it
**Parameters:**
-  `question` (string): Question about the photo

  

**Response Format:**

```json
{
"success": true,
"message": "Description or error message"
}
```

  

### 6. LED Mode Control
**Tool:**  `self.led.set_mode`
**Description:** Set LED mode
**Parameters:**
-  `mode` (string): "default", "rainbow", or "custom"
 

**Response Format:**

```json
{
"success": true,
"mode": "rainbow"
}
```
### 7. LED Rainbow Speed Control

**Tool:**  `self.led.set_rainbow_speed`
**Description:** Set rainbow cycling speed
**Parameters:**
-  `speed_ms` (integer, 50-1000): Speed in milliseconds

**Response Format:**

```json
{
"success": true,
"speed_ms": 200
}
```


### 8. LED Custom Color Control

**Tool:**  `self.led.set_color`
**Description:** Set custom LED color with RGB values
**Parameters:**
-  `red` (integer, 0-255): Red component
-  `green` (integer, 0-255): Green component
-  `blue` (integer, 0-255): Blue component

  

**Response Format:**

```json
{
"success": true,
"color": {
"red": 255,
"green": 0,
"blue": 128
}
}
```
## MCP Protocol Structure

All MCP messages follow the JSON-RPC 2.0 format:
### Tool Call Request
```json
{
"jsonrpc": "2.0",
"id": 1,
"method": "tools/call",
"params": {
"name": "self.battery.get_status",
"arguments": {},
"stackSize": 2048
}
}
```
### Tool Call Response
```json
{
	"jsonrpc": "2.0",
	"id": 1,
	"result": "{\"voltage_mv\":3650,\"percentage\":85,\"state\":\"normal\",\"charging\":false,\"low_battery\":false,\"critical_battery\":false}"
}
```
### Error Response
```json
{
"jsonrpc": "2.0",
"id": 1,
"error": {
"message": "Tool not found"
}
}
```
## Integration Examples

  

### Server-Side Tool Calls
**Get Battery Status:**
```python
# Send MCP request

request = {
	"jsonrpc": "2.0",
	"id": 1,
	"method": "tools/call",
	"params": {
		"name": "self.battery.get_status",
		"arguments": {}
		}
}
# Response will contain battery information

response = {
	"jsonrpc": "2.0",
	"id": 1,
	"result": "{\"voltage_mv\":3650,\"percentage\":85,\"state\":\"normal\",\"charging\":false,\"low_battery\":false,\"critical_battery\":false}"
}
```
**Set LED Color:**
```python
# Send MCP request to set LED to red

request = {
	"jsonrpc": "2.0",
	"id": 2,
	"method": "tools/call",
	"params": {
		"name": "self.led.set_color",
		"arguments": {
			"red": 255,
			"green": 0,
			"blue": 0
			}
	 }
}
```
## Hardware Capabilities
-  **ESP32-C2**: Low-power microcontroller with WiFi
-  **Battery Monitoring**: Real-time voltage and percentage tracking
-  **LED Control**: RGB LED with multiple modes
-  **Audio**: Speaker with volume control
-  **Display**: OLED/LCD with brightness and theme control
-  **Camera**: Photo capture with AI analysis
-  **WiFi**: Network connectivity and status monitoring
## Development Notes

- All tools are registered in `mcp_server.cc:36`
- Battery monitoring implemented in `battery_monitor.cc`
- Device status aggregated in `wifi_board.cc:GetDeviceStatusJson()`
- MCP specification: [Model Context Protocol 2024-11-05](https://modelcontextprotocol.io/specification/2024-11-05)