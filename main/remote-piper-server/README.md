# Remote Piper TTS Server

Self-hosted Piper text-to-speech server with HTTP API.

## 🚀 Quick Start

### Windows:
```bash
setup.bat
start.bat
```

### Linux/Mac:
```bash
chmod +x setup.sh
./setup.sh
./start.sh
```

## 📝 Configuration

Edit `.env` file:
```bash
PIPER_BINARY=piper/piper.exe  # Path to Piper binary
PIPER_MODEL=piper_models/en_US-amy-medium.onnx  # Model file
PIPER_VOICE=en_US-amy-medium  # Voice name
SAMPLE_RATE=22050             # Audio sample rate
HOST=0.0.0.0                  # Listen on all interfaces
PORT=8001                     # Server port
```

### Available Voices:
- `en_US-amy-medium` - Female, clear (recommended)
- `en_US-lessac-medium` - Male, clear
- `en_GB-alan-medium` - British male
- More at: https://github.com/rhasspy/piper/releases

## 🧪 Testing

```bash
# Health check
curl http://localhost:8001/health

# Synthesize speech
curl -X POST http://localhost:8001/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text":"Hello world"}' \
  --output test.wav
```

## 📊 Memory Usage

| Voice | Model Size | RAM Usage | Quality |
|-------|------------|-----------|---------|
| amy-low | 3MB | ~100MB | ⭐⭐⭐ |
| amy-medium | 18MB | ~200MB | ⭐⭐⭐⭐ |
| amy-high | 63MB | ~400MB | ⭐⭐⭐⭐⭐ |

## 🔗 API Endpoints

### GET /health
Health check
```json
{
  "status": "ok",
  "piper_available": true,
  "model_exists": true,
  "model": "piper_models/en_US-amy-medium.onnx",
  "voice": "en_US-amy-medium",
  "sample_rate": 22050
}
```

### POST /synthesize
Synthesize speech
```bash
curl -X POST http://localhost:8001/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text":"Hello, how are you?"}' \
  --output speech.wav
```

Returns: WAV audio file

### GET /info
Server information
```json
{
  "piper_binary": "piper/piper.exe",
  "model": "piper_models/en_US-amy-medium.onnx",
  "voice": "en_US-amy-medium",
  "sample_rate": 22050,
  "model_exists": true
}
```

## 🌐 Remote Access

To access from other machines on your network:

1. Find your IP address:
   ```bash
   # Windows
   ipconfig
   
   # Linux/Mac
   ifconfig
   ```

2. Use that IP from other machines:
   ```
   http://192.168.1.XXX:8001
   ```

3. Make sure firewall allows port 8001

## 🔧 Troubleshooting

### Piper not found:
Download from: https://github.com/rhasspy/piper/releases

### Model not found:
Download models from: https://github.com/rhasspy/piper/releases

### Port already in use:
Change PORT in `.env` file

### Slow synthesis:
- Use lower quality model (amy-low)
- Reduce text length
- Check CPU usage
