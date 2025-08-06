# MQTT+UDP to WebSocket Bridge Service

## Project Overview

This is a bridge service for IoT device communication, enabling conversion between MQTT and UDP protocols to WebSocket. The service allows devices to transmit control messages via MQTT and efficiently transfer audio data via UDP, bridging both to a WebSocket service.

## Features

- **Multi-protocol support**: Supports MQTT, UDP, and WebSocket protocols simultaneously
- **Audio data transmission**: Optimized mechanism for audio data streaming
- **Encrypted communication**: Uses AES-128-CTR encryption for UDP data transfer
- **Session management**: Complete device session lifecycle management
- **Auto-reconnect**: Automatic reconnection when connections drop
- **Heartbeat detection**: Periodic connection activity checks
- **Dev/Prod environment config**: Supports configuration switching for different environments

## Technical Architecture

- **MQTT Server**: Handles device control messages
- **UDP Server**: Handles efficient audio data transmission
- **WebSocket Client**: Connects to chat server
- **Bridge Layer**: Converts and routes messages between protocols

## Project Structure

```
├── app.js                # Main application entry
├── mqtt-protocol.js      # MQTT protocol implementation
├── ecosystem.config.js   # PM2 config file
├── package.json          # Project dependencies
├── .env                  # Environment variable config
├── utils/
│   ├── config-manager.js # Config management utility
│   ├── mqtt_config_v2.js # MQTT config validation utility
│   └── weixinAlert.js    # WeChat alert utility
└── config/               # Config files directory
```

## Dependencies

- **debug**: Debug log output
- **dotenv**: Environment variable management
- **ws**: WebSocket client
- **events**: Node.js events module

## Requirements

- Node.js 14.x or higher
- npm or yarn package manager
- PM2 (for production deployment)

## Installation Steps

1. Clone the repository

```bash
git clone <repository-url>
cd mqtt-websocket-bridge
```

2. Install dependencies

```bash
npm install
```

3. Create config files

```bash
mkdir -p config
cp config/mqtt.json.example config/mqtt.json
```

4. Edit `config/mqtt.json` and set appropriate parameters

## Configuration

The `config/mqtt.json` file should include:

```json
{
  "debug": false,
  "development": {
    "mac_addresss": ["aa:bb:cc:dd:ee:ff"],
    "chat_servers": ["wss://dev-chat-server.example.com/ws"]
  },
  "production": {
    "chat_servers": ["wss://chat-server.example.com/ws"]
  }
}
```

## Environment Variables

Create a `.env` file and set the following variables:

```
MQTT_PORT=1883       # MQTT server port
UDP_PORT=8884        # UDP server port
PUBLIC_IP=your-ip    # Server public IP
```

## Running the Service

### Development

```bash
# Run directly
node app.js

# Run in debug mode
DEBUG=mqtt-server node app.js
```

### Production (using PM2)

```bash
# Install PM2
npm install -g pm2

# Start service
pm2 start ecosystem.config.js

# View logs
pm2 logs xz-mqtt

# Monitor service
pm2 monit
```

The service will start on the following ports:

- MQTT Server: Port 1883 (can be changed via env variable)
- UDP Server: Port 8884 (can be changed via env variable)

## Protocol Description

### Device Connection Flow

1. Device connects to server via MQTT
2. Device sends a `hello` message with audio parameters and features
3. Server creates a WebSocket connection to the chat server
4. Server returns UDP connection parameters to the device
5. Device sends audio data via UDP
6. Server forwards audio data to WebSocket
7. Control messages from WebSocket are sent to the device via MQTT

### Message Formats

#### Hello Message (Device -> Server)

```json
{
  "type": "hello",
  "version": 3,
  "audio_params": { ... },
  "features": { ... }
}
```

#### Hello Response (Server -> Device)

```json
{
  "type": "hello",
  "version": 3,
  "session_id": "uuid",
  "transport": "udp",
  "udp": {
    "server": "server-ip",
    "port": 8884,
    "encryption": "aes-128-ctr",
    "key": "hex-encoded-key",
    "nonce": "hex-encoded-nonce"
  },
  "audio_params": { ... }
}
```

## Security Notes

- UDP communication uses AES-128-CTR encryption
- Each session uses a unique encryption key
- Sequence numbers prevent replay attacks
- Devices are authenticated via MAC address
- Supports device grouping and UUID verification

## Performance Optimization

- Uses pre-allocated buffers to reduce memory allocation
- UDP protocol for efficient audio data transfer
- Periodic cleanup of inactive connections
- Connection and active connection monitoring
- Supports load balancing across multiple chat servers

## Troubleshooting

- Check device MAC address format
- Ensure UDP port is open in firewall
- Enable debug mode for detailed logs
- Verify chat server address in config file
- Validate device authentication info

## Development Guide

### Adding New Features

1. Modify `mqtt-protocol.js` to support new MQTT features
2. Add new message handling methods in the `MQTTConnection` class
3. Update config manager for new config options
4. Add new WebSocket handling logic in the `WebSocketBridge` class

### Debugging Tips

```bash
# Enable all debug output
DEBUG=* node app.js

# Enable only MQTT server debug
DEBUG=mqtt-server node app.js
```
