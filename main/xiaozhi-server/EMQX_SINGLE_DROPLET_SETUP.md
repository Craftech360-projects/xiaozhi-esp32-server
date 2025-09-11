# EMQX Setup on Single Droplet (64.227.170.31)

This guide shows how to run both xiaozhi-server and EMQX on the same droplet for simplified communication.

## Benefits of Single Droplet Setup

- **Simplified networking**: Both services communicate via localhost
- **No firewall issues**: Internal communication on 127.0.0.1
- **Better security**: HTTP auth endpoint not exposed to internet
- **Lower latency**: No network hops between services
- **Easier debugging**: All logs on one server

## Server Information
- **Droplet IP**: `64.227.170.31`
- **xiaozhi-server**: Port 8000 (WebSocket), 8003 (HTTP)
- **EMQX**: Port 1883 (MQTT), 18083 (Dashboard)

## Installation Steps

### 1. SSH into Droplet
```bash
ssh root@64.227.170.31
```

### 2. Install Docker
```bash
# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
systemctl start docker
systemctl enable docker
```

### 3. Create EMQX Configuration
```bash
# Create config directory
mkdir -p /opt/emqx/etc

# Create configuration file
nano /opt/emqx/etc/emqx.conf
```

**Configuration Content:**
```hocon
node {
  name = "emqx@127.0.0.1"
  cookie = "emqxsecretcookie" 
  data_dir = "/opt/emqx/data"
}

cluster {
  name = emqxcl
  discovery_strategy = manual
}

authentication = [
  {
    mechanism = password_based
    backend = http
    method = post
    url = "http://127.0.0.1:8003/mqtt/auth"
    headers {
      "Content-Type" = "application/json"
      "User-Agent" = "EMQX-HTTP-Auth"
    }
    body {
      client_id = "${clientid}"
      username = "${username}" 
      password = "${password}"
      client_ip = "${peerhost}"
      protocol = "${proto_name}"
    }
    connect_timeout = 5s
    request_timeout = 10s
    pool_size = 8
    enable = true
  }
]

mqtt {
  max_clientid_len = 200
}

log {
  console {
    enable = true
    level = info
  }
}
```

### 4. Create Data Directory and Start EMQX
```bash
# Create and set permissions for data directory
mkdir -p /opt/emqx/data
chown -R 1000:1000 /opt/emqx/data

# Start EMQX container
docker run -d \
  --name emqx \
  --restart unless-stopped \
  -p 1883:1883 \
  -p 8083:8083 \
  -p 8084:8084 \
  -p 8883:8883 \
  -p 18083:18083 \
  -v /opt/emqx/etc/emqx.conf:/opt/emqx/etc/emqx.conf \
  emqx/emqx:5.8.0
```

### 5. Configure Firewall
```bash
# Allow necessary ports
ufw allow 1883/tcp    # MQTT
ufw allow 18083/tcp   # EMQX Dashboard
ufw allow 8003/tcp    # xiaozhi-server HTTP
ufw allow 8000/tcp    # xiaozhi-server WebSocket
ufw allow 22/tcp      # SSH
ufw --force enable
```

### 6. Verify EMQX Installation
```bash
# Check container status
docker ps

# Check logs
docker logs emqx

# Should see: "EMQX 5.8.0 is running now!"
```

## xiaozhi-server Configuration

### Update your local config file:
**File**: `data/.config.yaml`

```yaml
server:
  mqtt_gateway:
    enabled: true
    broker: 64.227.170.31  # Public IP for external clients
    port: 1883
    udp_port: 8884
```

### Deploy xiaozhi-server to Droplet
Upload your xiaozhi-server code to the droplet and start it:

```bash
# On the droplet, start xiaozhi-server
cd /path/to/xiaozhi-server
python main.py
```

## Testing and Verification

### 1. Test EMQX Dashboard
- **URL**: http://64.227.170.31:18083
- **Login**: admin / public
- **Check**: Management → Authentication (should show HTTP auth)

### 2. Test HTTP Authentication Endpoint
```bash
# From the droplet
curl http://127.0.0.1:8003/mqtt/auth

# From outside
curl http://64.227.170.31:8003/mqtt/auth
```

### 3. Test MQTT Connection
```bash
# Install MQTT client tools
apt install mosquitto-clients -y

# Test connection (should fail with auth error - that's expected)
mosquitto_pub -h 64.227.170.31 -p 1883 -t test -m "hello"
```

### 4. Check Logs
```bash
# EMQX logs
docker logs emqx

# xiaozhi-server logs (adjust path)
tail -f /path/to/xiaozhi-server/tmp/server.log
```

## Service Communication Flow

```
Device/Client
     ↓ (MQTT connection)
64.227.170.31:1883 (EMQX)
     ↓ (HTTP auth request)
127.0.0.1:8003 (xiaozhi-server HTTP auth endpoint)
     ↓ (validates credentials)
EMQX allows/denies connection
```

## Expected Behavior

1. **Device connects** to EMQX at `64.227.170.31:1883`
2. **EMQX validates** credentials via `127.0.0.1:8003/mqtt/auth`
3. **xiaozhi-server** uses existing HMAC logic to validate
4. **Connection allowed/denied** based on validation result

## Troubleshooting

### EMQX Authentication Issues
```bash
# Check if xiaozhi-server HTTP endpoint is running
curl http://127.0.0.1:8003/mqtt/auth

# Check EMQX logs for auth attempts
docker logs emqx | grep -i auth
```

### Port Conflicts
```bash
# Check what's using ports
netstat -tulpn | grep :1883
netstat -tulpn | grep :8003
```

### Firewall Issues
```bash
# Check firewall status
ufw status

# Temporarily disable firewall for testing
ufw disable
```

## Advantages of This Setup

1. **Simplified Configuration**: No need to expose internal services
2. **Better Security**: HTTP auth endpoint only accessible locally
3. **No Network Issues**: All communication on same server
4. **Easy Debugging**: All logs and services on one machine
5. **Cost Effective**: Single droplet instead of multiple servers

## Next Steps After Setup

1. Deploy your xiaozhi-server code to the droplet
2. Test device connections
3. Monitor logs for any authentication issues
4. Set up monitoring and backup procedures

## Important Notes

- Keep the EMQX dashboard secure (change default password)
- Monitor resource usage on the single droplet
- Consider setting up log rotation
- Plan for scaling if needed in the future