# Remote Services Setup Guide

## 🎯 Goal
Run Whisper STT and Piper TTS on a separate PC to reduce memory usage on your main server.

## 📊 Memory Savings

### Current Setup (All on one PC):
```
Main Server:
- Whisper base.en:  2.5GB
- llama3.1:8b:      3.0GB
- Python + deps:    0.5GB
--------------------------
Total:              6.0GB (75% of 8GB RAM)
```

### With Remote Services:
```
Main Server:
- llama3.1:8b:      3.0GB
- Python + deps:    0.5GB
--------------------------
Total:              3.5GB (44% of 8GB RAM) ✅

Remote PC:
- Whisper base.en:  2.5GB
- Piper TTS:        0.5GB
--------------------------
Total:              3.0GB
```

**Benefit:** Main server memory drops from 6GB to 3.5GB! 🎉

---

## 🔧 Option 1: Use Groq API (Easiest - Cloud-based)

### Pros:
- ✅ No additional PC needed
- ✅ Very fast (cloud processing)
- ✅ No memory usage on your servers
- ✅ Free tier available

### Cons:
- ⚠️ Requires internet connection
- ⚠️ API rate limits on free tier

### Setup:
```bash
# In .env
STT_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key_here

# TTS - use Edge TTS (free, cloud-based)
TTS_PROVIDER=edge
```

**Memory Savings:** 2.5GB (Whisper) + 0.5GB (Piper) = **3GB saved!**

---

## 🔧 Option 2: Remote Whisper Server (Self-hosted)

### Setup Remote Whisper Server

#### On Remote PC (192.168.1.XXX):

1. **Install Whisper API Server:**
```bash
# Install faster-whisper-server
pip install faster-whisper-server

# Or use whisper-api
git clone https://github.com/ahmetoner/whisper-asr-webservice
cd whisper-asr-webservice
docker-compose up -d
```

2. **Start Whisper Server:**
```bash
# Using faster-whisper-server
faster-whisper-server --model base.en --host 0.0.0.0 --port 8000

# Or using Docker
docker run -d -p 8000:8000 \
  -e ASR_MODEL=base.en \
  onerahmet/openai-whisper-asr-webservice:latest
```

3. **Test the server:**
```bash
curl http://192.168.1.XXX:8000/health
```

#### On Main Server:

Update `.env`:
```bash
STT_PROVIDER=deepgram  # Use Deepgram provider as template
DEEPGRAM_API_KEY=dummy  # Not used for local server
WHISPER_API_URL=http://192.168.1.XXX:8000
```

**Memory Savings:** 2.5GB (Whisper moved to remote PC)

---

## 🔧 Option 3: Remote Piper TTS Server

### Setup Remote Piper Server

#### On Remote PC:

1. **Create Piper API Server:**

```python
# piper_server.py
from flask import Flask, request, send_file
import subprocess
import tempfile
import os

app = Flask(__name__)

PIPER_MODEL = "./piper_models/en_US-amy-medium.onnx"

@app.route('/tts', methods=['POST'])
def synthesize():
    text = request.json.get('text', '')
    
    # Create temp file
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        output_file = f.name
    
    # Run Piper
    cmd = [
        'piper',
        '--model', PIPER_MODEL,
        '--output_file', output_file
    ]
    
    process = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    process.communicate(input=text.encode())
    
    # Return audio file
    return send_file(output_file, mimetype='audio/wav')

@app.route('/health')
def health():
    return {'status': 'ok'}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8001)
```

2. **Start the server:**
```bash
pip install flask
python piper_server.py
```

3. **Test:**
```bash
curl -X POST http://192.168.1.XXX:8001/tts \
  -H "Content-Type: application/json" \
  -d '{"text":"Hello world"}' \
  --output test.wav
```

#### On Main Server:

Create custom TTS provider or use Edge TTS as alternative.

**Memory Savings:** 0.5GB (Piper moved to remote PC)

---

## 🎯 Recommended Setup (Best Balance)

### Use Groq for STT + Edge TTS

This is the **easiest and most effective** solution:

```bash
# In .env on main server
STT_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key_here

TTS_PROVIDER=edge
EDGE_TTS_VOICE=en-US-AnaNeural
```

**Benefits:**
- ✅ **3GB memory saved** on main server
- ✅ **No additional PC needed**
- ✅ **Very fast** (cloud processing)
- ✅ **Free** (Groq free tier)
- ✅ **Easy setup** (just change .env)

**Result:**
```
Main Server Memory:
- llama3.1:8b:      3.0GB
- Python + deps:    0.5GB
--------------------------
Total:              3.5GB (44% of 8GB) ✅
```

---

## 🚀 Quick Setup: Switch to Groq + Edge TTS

### Step 1: Update .env

```bash
# STT - Use Groq (cloud-based, free)
STT_PROVIDER=groq
STT_MODEL=whisper-large-v3
GROQ_API_KEY=your_groq_api_key_here

# TTS - Use Edge TTS (cloud-based, free)
TTS_PROVIDER=edge
EDGE_TTS_VOICE=en-US-AnaNeural
EDGE_TTS_RATE=+0%
EDGE_TTS_VOLUME=+0%
```

### Step 2: Restart Agent

```bash
python simple_main.py
```

### Step 3: Verify

Check logs for:
```
✅ STT provider: groq
✅ TTS provider: edge
📊 Memory: ~3.5GB (was 6GB)
```

---

## 📊 Comparison Table

| Setup | Main Server Memory | Additional PC Needed | Internet Required | Setup Difficulty |
|-------|-------------------|---------------------|-------------------|------------------|
| **Current (Local)** | 6.0GB | ❌ No | ❌ No | ✅ Easy |
| **Groq + Edge TTS** | 3.5GB | ❌ No | ✅ Yes | ✅ Easy |
| **Remote Whisper** | 3.5GB | ✅ Yes | ❌ No | ⚠️ Medium |
| **Remote Piper** | 5.5GB | ✅ Yes | ❌ No | ⚠️ Medium |
| **All Remote** | 3.5GB | ✅ Yes | ❌ No | ⚠️ Hard |

---

## 💡 Recommendations

### For Your Use Case:

**Option 1: Groq + Edge TTS (Recommended)**
- Best for: Easy setup, maximum memory savings
- Memory: 3.5GB (44% of 8GB)
- Setup time: 2 minutes
- Cost: Free

**Option 2: Keep Current Setup**
- Best for: No internet dependency
- Memory: 6.0GB (75% of 8GB)
- Setup time: 0 minutes (already done)
- Cost: Free

**Option 3: Remote Whisper Server**
- Best for: No internet, have spare PC
- Memory: 3.5GB (44% of 8GB)
- Setup time: 30 minutes
- Cost: Free (uses your hardware)

---

## 🔧 Implementation Scripts

### Quick Switch to Groq + Edge TTS:

```bash
# Backup current .env
cp .env .env.backup

# Update STT to Groq
sed -i 's/STT_PROVIDER=whisper/STT_PROVIDER=groq/' .env

# Update TTS to Edge
sed -i 's/TTS_PROVIDER=piper/TTS_PROVIDER=edge/' .env

# Restart agent
python simple_main.py
```

### Revert to Local:

```bash
# Restore backup
cp .env.backup .env

# Or manually change
sed -i 's/STT_PROVIDER=groq/STT_PROVIDER=whisper/' .env
sed -i 's/TTS_PROVIDER=edge/TTS_PROVIDER=piper/' .env

# Restart agent
python simple_main.py
```

---

## ✅ Summary

**Yes, you can run Whisper and Piper on another PC!**

**Easiest solution:** Use Groq + Edge TTS (cloud-based, free)
- Changes: 2 lines in `.env`
- Memory saved: 2.5GB
- Setup time: 2 minutes

**Self-hosted solution:** Run Whisper server on remote PC
- Changes: Custom provider + remote server setup
- Memory saved: 2.5GB
- Setup time: 30 minutes

Choose based on your needs:
- **Want easy?** → Use Groq + Edge TTS
- **Want offline?** → Keep current setup or use remote server
- **Want maximum savings?** → Use Groq + Edge TTS (3GB saved)
