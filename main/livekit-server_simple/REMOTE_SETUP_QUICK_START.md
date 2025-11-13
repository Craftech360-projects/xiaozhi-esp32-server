# Remote Services Quick Start Guide

This guide shows you how to quickly set up and use remote Whisper and Piper servers to offload heavy processing from your main LiveKit server.

## Architecture Overview

```
┌─────────────────────┐
│  LiveKit Server     │
│  (Main PC)          │
│  - Ollama LLM       │
│  - Agent Logic      │
└──────┬──────────────┘
       │
       │ HTTP Requests
       │
       ├─────────────────────────┐
       │                         │
       ▼                         ▼
┌──────────────┐        ┌──────────────┐
│ Whisper      │        │ Piper        │
│ Server       │        │ Server       │
│ (Remote PC)  │        │ (Remote PC)  │
│ Port: 8000   │        │ Port: 8001   │
└──────────────┘        └──────────────┘
```

## Quick Setup Steps

### 1. On Remote PC (Windows or Linux)

**Option A: Automated Setup (Recommended)**
```bash
# Windows
cd main/remote-services
setup_remote_pc.bat

# Linux/Mac
cd main/remote-services
chmod +x setup_remote_pc.sh
./setup_remote_pc.sh
```

**Option B: Manual Setup**
```bash
# Install dependencies
pip install -r requirements.txt

# Start Whisper server (Terminal 1)
python whisper_server.py

# Start Piper server (Terminal 2)
python piper_server.py
```

### 2. On Main PC (LiveKit Server)

**Update your `.env` file:**
```bash
# STT Configuration - Remote Whisper
STT_PROVIDER=remote_whisper
STT_MODEL=base.en
STT_LANGUAGE=en
REMOTE_WHISPER_URL=http://192.168.1.XXX:8000

# TTS Configuration - Remote Piper
TTS_PROVIDER=remote_piper
TTS_VOICE=en_US-amy-medium
TTS_SAMPLE_RATE=22050
REMOTE_PIPER_URL=http://192.168.1.XXX:8001
```

Replace `192.168.1.XXX` with your remote PC's IP address.

### 3. Start Your LiveKit Agent

```bash
python simple_main.py dev
```

## Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `REMOTE_WHISPER_URL` | `http://localhost:8000` | Whisper server URL |
| `REMOTE_PIPER_URL` | `http://localhost:8001` | Piper server URL |
| `STT_PROVIDER` | - | Set to `remote_whisper` |
| `TTS_PROVIDER` | - | Set to `remote_piper` |

### Fallback Configuration

You can enable fallback to local providers if remote servers are unavailable:

```bash
# Enable fallback
FALLBACK_ENABLED=true

# Fallback providers (comma-separated, in order of preference)
STT_PROVIDERS=remote_whisper,whisper
TTS_PROVIDERS=remote_piper,piper
```

## Testing the Setup

### Test Whisper Server
```bash
curl -X POST http://192.168.1.XXX:8000/transcribe \
  -F "audio=@test.wav" \
  -F "language=en"
```

### Test Piper Server
```bash
curl -X POST http://192.168.1.XXX:8001/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text":"Hello world","voice":"en_US-amy-medium"}' \
  --output test.wav
```

## Troubleshooting

### Remote servers not responding
1. Check firewall settings on remote PC
2. Verify IP address is correct
3. Ensure servers are running: `netstat -an | findstr "8000 8001"`

### Connection timeout
- Increase timeout in `.env`: `REMOTE_TIMEOUT=60`
- Check network latency: `ping 192.168.1.XXX`

### Audio quality issues
- For Piper: Adjust `TTS_SAMPLE_RATE` (default: 22050)
- For Whisper: Try different models: `base.en`, `small.en`, `medium.en`

## Performance Benefits

| Component | Local | Remote | Improvement |
|-----------|-------|--------|-------------|
| Whisper Load Time | 19s | 0s | Instant |
| Memory Usage | ~4GB | ~100MB | 97% reduction |
| CPU Usage | High | Low | Offloaded |
| Piper Load Time | 5s | 0s | Instant |

## Network Requirements

- **Bandwidth**: ~100 KB/s per audio stream
- **Latency**: <50ms recommended for real-time
- **Ports**: 8000 (Whisper), 8001 (Piper)

## Security Notes

⚠️ **Important**: These servers have no authentication by default.

For production:
1. Use VPN or private network
2. Add API key authentication
3. Use HTTPS with SSL certificates
4. Implement rate limiting

## Advanced Configuration

### Custom Ports
Edit the server files to change ports:
- `whisper_server.py`: Change `port=8000`
- `piper_server.py`: Change `port=8001`

### Multiple Remote Servers
You can run multiple instances for load balancing:
```bash
REMOTE_WHISPER_URL=http://192.168.1.10:8000,http://192.168.1.11:8000
```

### Docker Deployment
See `main/remote-services/README.md` for Docker instructions.

## Support

For issues or questions:
1. Check server logs on remote PC
2. Check agent logs on main PC
3. Verify network connectivity
4. Review `REMOTE_SERVICES_GUIDE.md` for detailed documentation
