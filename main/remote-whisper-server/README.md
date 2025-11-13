# Remote Whisper STT Server

Self-hosted Whisper speech-to-text server with HTTP API.

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
WHISPER_MODEL=base.en  # Model size
HOST=0.0.0.0           # Listen on all interfaces
PORT=8000              # Server port
```

### Available Models:
- `tiny.en` - 39MB, fastest, ~500MB RAM
- `base.en` - 74MB, recommended, ~800MB RAM
- `small.en` - 244MB, better quality, ~1.2GB RAM
- `medium.en` - 769MB, excellent quality, ~2.5GB RAM

## 🧪 Testing

```bash
# Health check
curl http://localhost:8000/health

# Transcribe audio file
curl -X POST http://localhost:8000/transcribe \
  -F "audio=@test.wav"
```

## 📊 Memory Usage

| Model | RAM Usage | Speed | Quality |
|-------|-----------|-------|---------|
| tiny.en | ~500MB | ⚡⚡⚡⚡⚡ | ⭐⭐⭐ |
| base.en | ~800MB | ⚡⚡⚡⚡ | ⭐⭐⭐⭐ |
| small.en | ~1.2GB | ⚡⚡⚡ | ⭐⭐⭐⭐⭐ |

## 🔗 API Endpoints

### GET /health
Health check
```json
{
  "status": "ok",
  "model": "base.en",
  "device": "cpu",
  "model_loaded": true
}
```

### POST /transcribe
Transcribe audio
```bash
curl -X POST http://localhost:8000/transcribe \
  -F "audio=@audio.wav"
```

Response:
```json
{
  "text": "Hello world",
  "language": "en"
}
```

### GET /info
Server information
```json
{
  "model": "base.en",
  "device": "cpu",
  "cuda_available": false,
  "model_loaded": true
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
   http://192.168.1.XXX:8000
   ```

3. Make sure firewall allows port 8000

## 🔧 Troubleshooting

### Port already in use:
Change PORT in `.env` file

### Out of memory:
Use smaller model (tiny.en or base.en)

### Slow transcription:
- Use GPU if available (CUDA)
- Use smaller model
- Reduce audio length
