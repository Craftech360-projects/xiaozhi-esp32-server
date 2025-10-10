# 🚀 Offline Quick Start Guide

Get your LiveKit server running offline in minutes!

## Prerequisites

- Docker & Docker Compose installed
- 16GB+ RAM
- 20GB+ free disk space
- Python 3.9+

## Setup (5 Minutes)

### 1. Configure for Offline Mode

```bash
cd main/livekit-server
cp .env .env.cloud.backup  # Backup current config
cp .env.offline .env        # Use offline config
```

### 2. Start Services

```bash
docker-compose up -d
```

Wait 30 seconds for services to start.

### 3. Download AI Model

```bash
# Download Ollama model (~5GB, takes 2-5 minutes)
docker exec ollama-llm ollama pull llama3.1:8b
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Migrate Data

```bash
# Migrate Qdrant collections (requires internet once)
python scripts/migrate_qdrant_collections.py

# Download media files (requires internet once)
python scripts/download_media_from_s3.py
```

### 6. Start LiveKit Server

```bash
python main.py dev
```

## ✅ Verification

Check if services are running:

```bash
# All services should be "Up"
docker-compose ps

# Test Ollama
curl http://localhost:11434/api/tags

# Test Qdrant
curl http://localhost:6333/collections

# Test Media Server
curl http://localhost:8080/
```

## 📝 Key Configuration

Edit `.env` to customize:

```env
# LLM Model (change for different models)
LLM_PROVIDER=ollama
LLM_MODEL=llama3.1:8b

# STT Model (tiny/base/small/medium/large)
STT_PROVIDER=local_whisper
WHISPER_MODEL=base

# TTS Provider (coqui/edge)
TTS_PROVIDER=coqui

# Memory (local/cloud)
MEM0_TYPE=local

# Media (local server)
USE_CDN=false
LOCAL_MEDIA_URL=http://192.168.1.2:8080
```

## 🔧 Common Issues

### Ollama model not found
```bash
docker exec ollama-llm ollama pull llama3.1:8b
```

### Qdrant connection failed
```bash
docker-compose restart qdrant
```

### Out of memory
```bash
# Use smaller models in .env:
LLM_MODEL=phi3:mini
WHISPER_MODEL=tiny
TTS_PROVIDER=edge  # Instead of coqui
```

### Slow performance
```bash
# Enable GPU (if available):
WHISPER_DEVICE=cuda
COQUI_USE_GPU=true
```

## 🔄 Switch Back to Cloud

```bash
cp .env.cloud.backup .env
docker-compose restart
```

## 📚 Full Documentation

See [OFFLINE_SETUP_GUIDE.md](OFFLINE_SETUP_GUIDE.md) for detailed instructions.

## 🎯 What's Included

| Component | Local Solution | Status |
|-----------|---------------|--------|
| LLM | Ollama (llama3.1:8b) | ✅ |
| STT | faster-whisper | ✅ |
| TTS | Coqui TTS | ✅ |
| Vector DB | Qdrant (local) | ✅ |
| Media Files | Nginx server | ✅ |
| Memory | File-based | ✅ |

## 📊 Resource Usage

- **RAM**: 12-16 GB
- **Disk**: 10-20 GB
- **CPU**: 8-16 cores
- **GPU**: Optional (5-10x faster)

## 🎉 Done!

Your LiveKit server is now fully offline!

**Next**: Test all features work without internet connection.
