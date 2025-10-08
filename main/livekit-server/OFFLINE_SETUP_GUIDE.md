# LiveKit Server Offline Setup Guide

Complete guide to setting up and running the LiveKit server in fully offline mode.

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Detailed Setup](#detailed-setup)
4. [Verification](#verification)
5. [Troubleshooting](#troubleshooting)
6. [Resource Requirements](#resource-requirements)

---

## Prerequisites

### System Requirements

- **CPU**: 8-16 cores (recommended)
- **RAM**: 12-16 GB minimum
- **Storage**: 20+ GB free space
- **OS**: Linux, macOS, or Windows with WSL2
- **Docker**: Docker & Docker Compose installed
- **Python**: Python 3.9+ (for migration scripts)

### Optional (for better performance)

- **GPU**: NVIDIA GPU with CUDA support (5-10x faster inference)
- **SSD**: For faster model loading and media serving

---

## Quick Start

If you want to get started quickly:

```bash
# 1. Navigate to livekit-server directory
cd main/livekit-server

# 2. Backup current configuration
cp .env .env.cloud.backup

# 3. Use offline configuration
cp .env.offline .env

# 4. Start all services
docker-compose up -d

# 5. Pull Ollama model (will download ~5GB)
docker exec ollama-llm ollama pull llama3.1:8b

# 6. Install Python dependencies
pip install -r requirements.txt

# 7. Run migration scripts (see Detailed Setup)
python scripts/migrate_qdrant_collections.py
python scripts/download_media_from_s3.py

# 8. Start the LiveKit server
python main.py
```

---

## Detailed Setup

### Step 1: Prepare Configuration Files

#### 1.1 Backup Current Configuration

```bash
cd main/livekit-server
cp .env .env.cloud.backup
```

#### 1.2 Create Offline Configuration

```bash
cp .env.offline .env
```

#### 1.3 Review and Customize .env

Edit `.env` and adjust settings as needed:

- **LLM Model**: Change `LLM_MODEL` for different Ollama models
- **Whisper Model**: Change `WHISPER_MODEL` (tiny/base/small/medium/large)
- **TTS Provider**: Choose between `coqui` (fully local) or `edge` (uses Microsoft)
- **GPU**: Set `WHISPER_DEVICE=cuda` and `COQUI_USE_GPU=true` if you have GPU

### Step 2: Start Docker Services

#### 2.1 Start All Services

```bash
docker-compose up -d
```

This will start:
- **livekit-server**: Real-time communication server
- **qdrant**: Local vector database
- **ollama**: Local LLM server
- **media-server**: Nginx server for audio files

#### 2.2 Verify Services Are Running

```bash
docker-compose ps
```

Expected output:
```
NAME                IMAGE                       STATUS
livekit-server      livekit/livekit-server     Up
qdrant-local        qdrant/qdrant              Up
ollama-llm          ollama/ollama              Up
media-server        nginx:alpine               Up
```

#### 2.3 Check Service Logs

```bash
# Check all services
docker-compose logs

# Check specific service
docker-compose logs ollama
docker-compose logs qdrant
```

### Step 3: Download and Setup AI Models

#### 3.1 Download Ollama Model

```bash
# Download llama3.1:8b model (~5GB)
docker exec ollama-llm ollama pull llama3.1:8b

# Alternative models (optional):
# docker exec ollama-llm ollama pull llama2:7b
# docker exec ollama-llm ollama pull mistral:7b
# docker exec ollama-llm ollama pull phi3:mini
```

#### 3.2 List Available Models

```bash
docker exec ollama-llm ollama list
```

#### 3.3 Test Ollama

```bash
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.1:8b",
  "prompt": "Hello, how are you?",
  "stream": false
}'
```

### Step 4: Install Python Dependencies

```bash
# Install all dependencies
pip install -r requirements.txt

# Or use virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Step 5: Migrate Qdrant Collections

#### 5.1 Run Migration Script

```bash
python scripts/migrate_qdrant_collections.py
```

This will:
- Connect to Qdrant Cloud
- Download all collections (music, stories)
- Upload to local Qdrant instance

#### 5.2 Verify Migration

```bash
# Check local Qdrant
curl http://localhost:6333/collections

# Should show music_collection and story_collection
```

### Step 6: Download Media Files

#### 6.1 Run Download Script

```bash
python scripts/download_media_from_s3.py
```

This will:
- Connect to S3 bucket
- Download all music files to `local_media/music/`
- Download all story files to `local_media/stories/`

#### 6.2 Verify Media Files

```bash
# Check downloaded files
ls -lh local_media/music/
ls -lh local_media/stories/

# Test media server
curl -I http://localhost:8080/
```

### Step 7: Update Service Configuration

#### 7.1 Update Music Service (if needed)

The music service should automatically use local media when `USE_CDN=false`.

Check [src/services/music_service.py](src/services/music_service.py:42-50) - it should use `LOCAL_MEDIA_URL`.

#### 7.2 Update Story Service (if needed)

Same for story service - it should use `LOCAL_MEDIA_URL` when CDN is disabled.

### Step 8: Start LiveKit Server

```bash
# Start in development mode
python main.py dev

# Or start in production mode
python main.py
```

---

## Verification

### Test 1: Check All Services

```bash
# Ollama LLM
curl http://localhost:11434/api/tags

# Qdrant
curl http://localhost:6333/collections

# Media Server
curl http://localhost:8080/

# LiveKit
curl http://localhost:7880/
```

### Test 2: Test AI Models

#### Test LLM

```python
import aiohttp
import asyncio

async def test_llm():
    url = "http://localhost:11434/api/generate"
    data = {
        "model": "llama3.1:8b",
        "prompt": "Say hello",
        "stream": False
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=data) as resp:
            result = await resp.json()
            print(result['response'])

asyncio.run(test_llm())
```

#### Test Whisper STT

```python
from src.providers.local_whisper_stt import LocalWhisperSTT
import asyncio

async def test_stt():
    stt = LocalWhisperSTT(model_size="base", device="cpu")
    # Test with audio file
    print("Whisper STT initialized successfully")

asyncio.run(test_stt())
```

#### Test Coqui TTS

```python
from src.providers.coqui_tts_provider import CoquiTTS
import asyncio

async def test_tts():
    tts = CoquiTTS()
    stream = tts.synthesize("Hello, this is a test")
    print("Coqui TTS initialized successfully")

asyncio.run(test_tts())
```

### Test 3: Network Isolation Test

```bash
# Disable internet (Linux)
sudo iptables -A OUTPUT -p tcp --dport 80 -j DROP
sudo iptables -A OUTPUT -p tcp --dport 443 -j DROP

# Start LiveKit server
python main.py dev

# Test all features - everything should work offline

# Re-enable internet
sudo iptables -D OUTPUT -p tcp --dport 80 -j DROP
sudo iptables -D OUTPUT -p tcp --dport 443 -j DROP
```

---

## Troubleshooting

### Issue 1: Ollama Model Not Found

**Symptom**: `Model 'llama3.1:8b' not found`

**Solution**:
```bash
# Pull the model
docker exec ollama-llm ollama pull llama3.1:8b

# Verify
docker exec ollama-llm ollama list
```

### Issue 2: Qdrant Connection Failed

**Symptom**: `Cannot connect to Qdrant at localhost:6333`

**Solution**:
```bash
# Check if Qdrant is running
docker-compose ps qdrant

# Restart Qdrant
docker-compose restart qdrant

# Check logs
docker-compose logs qdrant
```

### Issue 3: Whisper Model Download Fails

**Symptom**: `Failed to download Whisper model`

**Solution**:
```bash
# Manually download model (requires internet)
python -c "from faster_whisper import WhisperModel; WhisperModel('base')"

# Or use smaller model
# Edit .env: WHISPER_MODEL=tiny
```

### Issue 4: Out of Memory

**Symptom**: System crashes or freezes during inference

**Solution**:
- Use smaller models:
  - LLM: `llama2:7b` or `phi3:mini`
  - Whisper: `tiny` or `base`
  - TTS: Keep `edge` instead of `coqui`
- Close other applications
- Add more RAM or use swap

### Issue 5: Slow Inference

**Symptom**: Responses take too long

**Solution**:
1. Enable GPU:
   ```bash
   # Edit .env
   WHISPER_DEVICE=cuda
   COQUI_USE_GPU=true
   ```

2. Use smaller/faster models:
   ```bash
   # Edit .env
   LLM_MODEL=phi3:mini
   WHISPER_MODEL=tiny
   ```

3. Adjust compute type:
   ```bash
   # Edit .env
   WHISPER_COMPUTE_TYPE=int8  # Fastest
   ```

### Issue 6: Media Files Not Playing

**Symptom**: Music/stories don't play

**Solution**:
```bash
# Check media server
curl http://localhost:8080/

# Check files exist
ls local_media/music/

# Restart media server
docker-compose restart media-server

# Verify .env settings
# USE_CDN=false
# LOCAL_MEDIA_URL=http://192.168.1.2:8080
```

---

## Resource Requirements

### Disk Space

| Component | Size | Required |
|-----------|------|----------|
| Ollama llama3.1:8b | ~5 GB | Yes |
| Whisper base | ~150 MB | Yes |
| Whisper large | ~3 GB | Optional |
| Coqui TTS | ~500 MB | Yes (if using) |
| Qdrant data | 1-5 GB | Yes |
| Media files | Varies | Yes |
| **Total** | **10-20 GB** | - |

### Memory Usage

| Component | RAM Usage |
|-----------|-----------|
| Ollama (llama3.1:8b) | 8-10 GB |
| Whisper (base) | 1-2 GB |
| Coqui TTS | 1-2 GB |
| Qdrant | 500 MB |
| LiveKit Server | 500 MB |
| **Total** | **12-16 GB** |

### CPU Usage

- **Minimum**: 8 cores
- **Recommended**: 16 cores
- **With GPU**: CPU usage drops significantly

### GPU Requirements (Optional)

- **NVIDIA GPU** with CUDA support
- **VRAM**: 8+ GB recommended
- **Drivers**: Latest NVIDIA drivers + CUDA 11.8+

---

## Switching Between Cloud and Offline

### Switch to Offline Mode

```bash
cp .env .env.cloud.backup
cp .env.offline .env
docker-compose up -d
```

### Switch Back to Cloud Mode

```bash
cp .env.cloud.backup .env
docker-compose restart
```

---

## Performance Tips

1. **Use GPU** for 5-10x faster inference
2. **Use SSD** for faster model loading
3. **Preload models** using `startup_preloader.py`
4. **Adjust model sizes** based on your needs
5. **Enable swap** if running low on RAM
6. **Close unnecessary applications**

---

## Next Steps

After successful setup:

1. ✅ Test all AI features (LLM, STT, TTS)
2. ✅ Test music and story playback
3. ✅ Test memory storage (local file-based)
4. ✅ Run network isolation test
5. ✅ Monitor resource usage
6. ✅ Optimize settings for your hardware

---

## Support

For issues or questions:
1. Check logs: `docker-compose logs`
2. Review this guide's Troubleshooting section
3. Check the implementation plan: `OFFLINE_IMPLEMENTATION_PLAN1.md`

---

**Congratulations! Your LiveKit server is now running fully offline! 🎉**
