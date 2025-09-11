# EMQX Integration Setup Guide

This guide shows how to replace your current MQTT broker with EMQX while keeping your existing authentication system.

## Overview

Your current system generates dynamic MQTT credentials using HMAC-SHA256 signatures. EMQX will use HTTP authentication to validate these credentials against your xiaozhi-server.

## What Was Added

### 1. HTTP Authentication Endpoint
- **File**: `core/api/mqtt_auth_handler.py`
- **Route**: `http://your-server:8003/mqtt/auth`
- **Method**: POST
- **Purpose**: Validates MQTT credentials using your existing logic

### 2. Route Registration
- **File**: `core/http_server.py` (modified)
- **Routes Added**:
  - `GET /mqtt/auth` - Status endpoint
  - `POST /mqtt/auth` - Authentication endpoint
  - `OPTIONS /mqtt/auth` - CORS support

### 3. EMQX Configuration
- **File**: `config/emqx-auth.conf`
- **Purpose**: Configure EMQX to use HTTP authentication

## Installation Steps

### Step 1: Install EMQX

#### Docker Installation (Recommended):
```bash
# Pull EMQX Docker image
docker pull emqx/emqx:5.8.0

# Create EMQX container with your config
docker run -d \
  --name emqx \
  -p 1883:1883 \
  -p 8083:8083 \
  -p 8084:8084 \
  -p 8883:8883 \
  -p 18083:18083 \
  -v /path/to/your/emqx-auth.conf:/opt/emqx/etc/emqx.conf \
  emqx/emqx:5.8.0
```

#### Native Installation:
```bash
# Ubuntu/Debian
wget https://www.emqx.com/en/downloads/broker/5.8.0/emqx-5.8.0-ubuntu20.04-amd64.deb
sudo dpkg -i emqx-5.8.0-ubuntu20.04-amd64.deb

# Copy configuration file
sudo cp config/emqx-auth.conf /etc/emqx/emqx.conf
```

### Step 2: Update EMQX Configuration

1. **Edit the config file**:
   ```bash
   # Update the xiaozhi-server URL in emqx-auth.conf
   url = "http://YOUR_XIAOZHI_SERVER_IP:8003/mqtt/auth"
   ```

2. **Replace YOUR_XIAOZHI_SERVER_IP** with your actual server IP:
   - If EMQX is on same machine: `127.0.0.1` or `localhost`
   - If EMQX is on different machine: Your xiaozhi-server's IP address

### Step 3: Update Your xiaozhi-server Configuration

Edit your `data/.config.yaml`:

```yaml
server:
  mqtt_gateway:
    enabled: true
    broker: YOUR_EMQX_SERVER_IP  # Change from 192.168.1.111 to EMQX IP
    port: 1883                   # EMQX MQTT port
    udp_port: 8884              # Keep existing
```

### Step 4: Start Services

1. **Start EMQX**:
   ```bash
   # Docker
   docker start emqx
   
   # Native
   sudo systemctl start emqx
   ```

2. **Start xiaozhi-server**:
   ```bash
   cd xiaozhi-server
   python main.py
   ```

### Step 5: Verify Setup

1. **Check EMQX Dashboard**: http://your-emqx-ip:18083
   - Default login: admin/public
   - Go to Authentication → HTTP to see auth requests

2. **Test Authentication Endpoint**:
   ```bash
   curl http://your-xiaozhi-server:8003/mqtt/auth
   ```

3. **Check Logs**:
   ```bash
   # xiaozhi-server logs
   tail -f tmp/server.log | grep "MQTT Auth"
   
   # EMQX logs
   docker logs -f emqx
   # or
   tail -f /var/log/emqx/emqx.log
   ```

## How It Works

### Authentication Flow:
1. **Device connects** to EMQX with credentials
2. **EMQX sends** HTTP POST to `xiaozhi-server:8003/mqtt/auth`
3. **xiaozhi-server validates** using existing HMAC logic
4. **Returns HTTP 200** (success) or **401** (failure)
5. **EMQX allows/denies** connection based on response

### Credential Format (Unchanged):
- **Client ID**: `GID_test@@@mac_address@@@uuid`
- **Username**: Base64 encoded JSON with IP
- **Password**: HMAC-SHA256 signature

## Troubleshooting

### Common Issues:

1. **Authentication Always Fails**:
   - Check MQTT_SIGNATURE_KEY environment variable
   - Verify xiaozhi-server HTTP port (8003) is accessible
   - Check EMQX can reach xiaozhi-server (firewall/network)

2. **Connection Refused**:
   - Ensure xiaozhi-server HTTP server is running
   - Check port 8003 is not blocked by firewall
   - Verify EMQX config has correct xiaozhi-server URL

3. **EMQX Can't Start**:
   - Check EMQX config file syntax
   - Ensure port 1883 is not in use by old MQTT broker
   - Check EMQX logs for specific errors

### Debug Mode:

1. **Enable Debug Logs in xiaozhi-server**:
   ```yaml
   # In .config.yaml
   log:
     log_level: DEBUG
   ```

2. **Enable Debug Logs in EMQX**:
   ```hocon
   # In emqx.conf
   log {
     console {
       level = debug
     }
   }
   ```

### Testing Authentication:

```bash
# Test auth endpoint directly
curl -X POST http://192.168.1.111:8003/mqtt/auth \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "GID_test@@@AA_BB_CC_DD_EE_FF@@@test-uuid",
    "username": "eyJpcCI6ICIxOTIuMTY4LjEuMTAwIn0=",
    "password": "your-hmac-signature"
  }'
```

## Migration Checklist

- [ ] EMQX installed and configured
- [ ] HTTP authentication endpoint working
- [ ] xiaozhi-server config updated with EMQX IP
- [ ] Old MQTT broker stopped
- [ ] Device connections tested
- [ ] Authentication logs verified
- [ ] Performance monitoring setup

## Benefits of EMQX

- **Better Performance**: Handles more concurrent connections
- **Advanced Features**: Rule engine, webhooks, clustering
- **Monitoring**: Built-in dashboard and metrics
- **Scalability**: Easy horizontal scaling
- **Enterprise Ready**: High availability and reliability

## Rollback Plan

If issues occur, quickly rollback:

1. **Stop EMQX**: `docker stop emqx` or `systemctl stop emqx`
2. **Restart old MQTT broker** (mosquitto/etc)
3. **Revert config**: Change broker IP back to old broker
4. **Restart xiaozhi-server**

Your authentication system remains unchanged, so rollback is safe and quick.