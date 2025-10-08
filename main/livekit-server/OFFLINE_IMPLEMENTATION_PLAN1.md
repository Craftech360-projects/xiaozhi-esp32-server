# LiveKit-Server Offline Implementation Plan

## Overview
This document outlines the changes required to run the LiveKit-Server completely offline without any internet dependencies.

---

## Current Internet Dependencies Analysis

### 1. AI Model Providers (CRITICAL - External APIs)

#### Current State
- **Groq API** (Primary LLM, STT, TTS)
  - LLM Model: `openai/gpt-oss-20b` or `llama-3.1-8b-instant`
  - STT Model: `whisper-large-v3-turbo`
  - TTS Model: `playai-tts`
  - Requires: `GROQ_API_KEY`

- **Deepgram API** (Alternative STT)
  - Model: `nova-2` / `nova-3`
  - Requires: `DEEPGRAM_API_KEY`

- **ElevenLabs API** (Alternative TTS)
  - Model: `eleven_turbo_v2_5`
  - Requires: `ELEVEN_API_KEY`

- **Google API**
  - Requires: `GOOGLE_API_KEY`

#### Files Affected
- `src/providers/provider_factory.py`
- `requirements.txt`
- `.env`

---

### 2. Memory System (Mem0 Cloud Service)

#### Current State
- **Mem0 Cloud API**: `mem0.ai`
- Used for: Long-term conversation memory
- Requires: `MEM0_API_KEY=m0-tNiOs5lPRZMUGeNglTt9np3GBHt7EOIBZr3FbUtC`
- Configuration: `MEM0_ENABLED=true`

#### Files Affected
- `src/memory/mem0_provider.py`
- `main.py` (lines 239-271, 354-375, 461-491)
- `.env`

---

### 3. Qdrant Vector Database (Cloud-Hosted)

#### Current State
- **Qdrant Cloud**: `https://a2482b9f-2c29-476e-9ff0-741aaaaf632e.eu-west-1-0.aws.cloud.qdrant.io`
- Used for: Semantic search for music and stories
- Requires: `QDRANT_API_KEY`
- Collections: Music metadata, Story metadata

#### Files Affected
- `src/services/semantic_search.py`
- `src/services/qdrant_semantic_search.py`
- `src/services/music_service.py`
- `src/services/story_service.py`
- `.env`
- `config.yaml`

---

### 4. AWS S3 / CloudFront CDN (Media Streaming)

#### Current State
- **CloudFront Domain**: `dbtnllz9fcr1z.cloudfront.net`
- **S3 Bucket**: `cheeko-audio-files` (us-east-1)
- **S3 Base URL**: `https://cheeko-audio-files.s3.us-east-1.amazonaws.com`
- Used for: Streaming music and story audio files
- Configuration: `USE_CDN=true`

#### Files Affected
- `src/services/music_service.py` (lines 21-23, 42-50)
- `src/services/story_service.py`
- `.env`

---

### 5. Manager API (Local Network - Already Partially Local)

#### Current State
- **URL**: `http://192.168.1.2:8002/toy`
- Used for: Fetching device-specific prompts and configurations
- Authentication: `MANAGER_API_SECRET`
- Configuration: `read_config_from_api=true`

#### Status
✅ **Already on Local Network** - No changes needed if Manager API remains available
⚠️ **Alternative**: Can be disabled for fully standalone operation

#### Files Affected
- `src/services/prompt_service.py`
- `src/utils/database_helper.py`
- `config.yaml`
- `.env`

---

### 6. Local Services (Already Local - No Changes Needed)

#### Redis
✅ **Already Local**: `redis://:redispassword@192.168.1.2:6380`
- Used for: Caching and session state

#### MQTT
✅ **Already Local**: `192.168.1.2:1883`
- Used for: Device communication

#### LiveKit Server
✅ **Already Local**: `ws://192.168.1.2:7880`
- Used for: Real-time audio/video communication

---

## Implementation Plan

### Phase 1: Replace AI Providers with Local Models

#### Step 1.1: Local LLM (Replace Groq LLM)
**Option A: Ollama (Recommended)**
```bash
# Install Ollama
# Download model
ollama pull llama3.1:8b

# Add to docker-compose.yml
services:
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
```

**Option B: llama.cpp with OpenAI-compatible API**
```bash
# Install llama-cpp-python with server
pip install llama-cpp-python[server]
```

**Code Changes:**
- Create `src/providers/ollama_provider.py`
- Update `src/providers/provider_factory.py`:
  ```python
  @staticmethod
  def create_llm(config):
      provider = config.get('llm_provider', 'groq').lower()
      if provider == 'ollama':
          from .ollama_provider import OllamaLLM
          return OllamaLLM(
              base_url=config.get('ollama_url', 'http://localhost:11434'),
              model=config.get('llm_model', 'llama3.1:8b')
          )
      # ... existing code
  ```

**Environment Variables:**
```env
LLM_PROVIDER=ollama
OLLAMA_URL=http://localhost:11434
LLM_MODEL=llama3.1:8b
```

---

#### Step 1.2: Local STT (Replace Groq/Deepgram STT)
**Option: Whisper.cpp or faster-whisper**

```bash
# Install faster-whisper
pip install faster-whisper
```

**Code Changes:**
- Create `src/providers/local_whisper_stt.py`
- Update `src/providers/provider_factory.py`:
  ```python
  @staticmethod
  def create_stt(config, vad=None):
      provider = config.get('stt_provider', 'groq').lower()
      if provider == 'local_whisper':
          from .local_whisper_stt import LocalWhisperSTT
          return stt.StreamAdapter(
              stt=LocalWhisperSTT(
                  model_size=config.get('whisper_model', 'base'),
                  device=config.get('whisper_device', 'cpu')
              ),
              vad=vad
          )
      # ... existing code
  ```

**Environment Variables:**
```env
STT_PROVIDER=local_whisper
WHISPER_MODEL=base  # Options: tiny, base, small, medium, large
WHISPER_DEVICE=cpu  # or cuda for GPU
```

---

#### Step 1.3: Local TTS (Already Partially Implemented)
**Current: EdgeTTS (uses Microsoft servers)**
**Better Option: Coqui TTS (fully local)**

```bash
# Install Coqui TTS
pip install TTS
```

**Code Changes:**
- Create `src/providers/coqui_tts_provider.py`
- Update `src/providers/provider_factory.py`:
  ```python
  @staticmethod
  def create_tts(groq_config, tts_config):
      provider = tts_config.get('provider', 'groq').lower()
      if provider == 'coqui':
          from .coqui_tts_provider import CoquiTTS
          return CoquiTTS(
              model_name=tts_config.get('coqui_model', 'tts_models/en/ljspeech/tacotron2-DDC'),
              use_gpu=tts_config.get('coqui_use_gpu', False)
          )
      # ... existing code (including edge)
  ```

**Environment Variables:**
```env
TTS_PROVIDER=coqui
# or keep edge if Microsoft servers are acceptable
TTS_PROVIDER=edge
EDGE_TTS_VOICE=en-US-AvaNeural
```

---

### Phase 2: Deploy Local Qdrant

#### Step 2.1: Add Qdrant to Docker Compose
**Update `docker-compose.yml`:**
```yaml
services:
  livekit-server:
    # ... existing config

  qdrant:
    image: qdrant/qdrant:latest
    container_name: qdrant-local
    restart: unless-stopped
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant_storage:/qdrant/storage
    networks:
      - manager-api_manager-api-network

volumes:
  qdrant_storage:
```

#### Step 2.2: Export Collections from Cloud
```python
# Create script: scripts/export_qdrant_collections.py
from qdrant_client import QdrantClient

# Connect to cloud
cloud_client = QdrantClient(
    url="https://a2482b9f-2c29-476e-9ff0-741aaaaf632e.eu-west-1-0.aws.cloud.qdrant.io",
    api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
)

# Connect to local
local_client = QdrantClient(
    url="http://localhost:6333"
)

# Export collections
collections = ['music_collection', 'story_collection']
for collection_name in collections:
    # Get all points
    points = cloud_client.scroll(collection_name, limit=10000)
    # Recreate collection locally
    local_client.recreate_collection(...)
    local_client.upsert(collection_name, points)
```

#### Step 2.3: Update Configuration
**Update `.env`:**
```env
QDRANT_URL=http://localhost:6333
# Remove QDRANT_API_KEY (not needed for local)
```

**Update `config.yaml`:**
```yaml
qdrant:
  url: "http://localhost:6333"
  api_key: ""  # Empty for local instance
```

---

### Phase 3: Local Media Storage

#### Step 3.1: Download Media Files from S3
```bash
# Install AWS CLI
pip install awscli

# Download all music files
aws s3 sync s3://cheeko-audio-files/music/ ./local_media/music/ \
  --region us-east-1

# Download all story files
aws s3 sync s3://cheeko-audio-files/stories/ ./local_media/stories/ \
  --region us-east-1
```

#### Step 3.2: Set Up Local File Server
**Option A: Add Nginx to Docker Compose**
```yaml
services:
  media-server:
    image: nginx:alpine
    container_name: media-server
    restart: unless-stopped
    ports:
      - "8080:80"
    volumes:
      - ./local_media:/usr/share/nginx/html:ro
    networks:
      - manager-api_manager-api-network
```

**Option B: Use Python HTTP Server**
```bash
cd local_media
python -m http.server 8080
```

#### Step 3.3: Update Media Service URLs
**Update `src/services/music_service.py`:**
```python
def __init__(self, preloaded_model=None, preloaded_client=None):
    # Change to local file server
    self.use_cdn = False  # Disable CDN
    self.local_media_url = os.getenv("LOCAL_MEDIA_URL", "http://localhost:8080")
    # ... rest of init

def get_song_url(self, filename: str, language: str = "English") -> str:
    """Generate URL for song file from local server"""
    audio_path = f"music/{language}/{filename}"
    encoded_path = urllib.parse.quote(audio_path)
    return f"{self.local_media_url}/{encoded_path}"
```

**Update `.env`:**
```env
USE_CDN=false
LOCAL_MEDIA_URL=http://192.168.1.2:8080
# Remove AWS credentials
# AWS_ACCESS_KEY_ID=
# AWS_SECRET_ACCESS_KEY=
```

---

### Phase 4: Handle Memory System

#### Option A: Disable Mem0 (Simplest)
**Update `.env`:**
```env
MEM0_ENABLED=false
```

#### Option B: Implement Local Memory Storage
**Create `src/memory/local_memory_provider.py`:**
```python
import json
from pathlib import Path

class LocalMemoryProvider:
    def __init__(self, storage_dir: str, role_id: str):
        self.storage_dir = Path(storage_dir)
        self.role_id = role_id
        self.memory_file = self.storage_dir / f"{role_id}.json"

    async def save_memory(self, history_dict: dict):
        """Save to local JSON file"""
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.memory_file, 'w') as f:
            json.dump(history_dict, f, indent=2)

    async def query_memory(self, query: str) -> str:
        """Load from local JSON file"""
        if not self.memory_file.exists():
            return ""
        with open(self.memory_file, 'r') as f:
            data = json.load(f)
            # Format and return memories
            return self._format_memories(data)
```

**Update `main.py`:**
```python
if device_mac and mem0_enabled:
    mem0_type = os.getenv("MEM0_TYPE", "cloud").lower()
    if mem0_type == "local":
        from src.memory.local_memory_provider import LocalMemoryProvider
        mem0_provider = LocalMemoryProvider(
            storage_dir="./local_memory",
            role_id=device_mac
        )
    else:
        # ... existing mem0 cloud code
```

**Update `.env`:**
```env
MEM0_ENABLED=true
MEM0_TYPE=local  # Options: cloud, local
```

---

### Phase 5: Manager API Configuration

#### Option A: Keep Manager API (Already Local)
✅ **No changes needed** - Manager API runs on local network (`192.168.1.2:8002`)

#### Option B: Disable API Fetching (Fully Standalone)
**Update `config.yaml`:**
```yaml
# Disable API configuration fetching
read_config_from_api: false

# Use local default prompt
default_prompt: |
  <identity>
  You are Cheeko, a playful AI companion...
  </identity>
  # ... rest of prompt
```

**Update `.env`:**
```env
# Comment out Manager API if not needed
# MANAGER_API_URL=http://192.168.1.2:8002/toy
# MANAGER_API_SECRET=da11d988-f105-4e71-b095-da62ada82189
```

---

## Phase 6: Update Dependencies

### Update `requirements.txt`
```txt
# Core LiveKit dependencies
livekit-plugins-groq  # Keep for backward compatibility, but not used
python-dotenv
pydub
aiohttp

# Local AI Models (ADD THESE)
faster-whisper  # Local STT
TTS  # Coqui TTS for local TTS
# ollama-python  # If using Ollama client library

# Vector database
qdrant-client
sentence-transformers

# EdgeTTS support (works offline with Microsoft servers)
edge-tts

# Room management and JWT
livekit-api
PyJWT

# Memory provider (optional - only if using local memory)
# mem0  # Comment out if using local memory
```

### Update `docker-compose.yml` (Complete)
```yaml
version: '3.8'

services:
  livekit-server:
    image: livekit/livekit-server:latest
    container_name: livekit-server
    restart: unless-stopped
    ports:
      - "7880-7882:7880-7882/tcp"
      - "50000-50200:50000-50200/udp"
    environment:
      LIVEKIT_KEYS: "devkey: secret"
      REDIS_URL: "redis://:redispassword@manager-api-redis:6379"
    networks:
      - manager-api_manager-api-network

  qdrant:
    image: qdrant/qdrant:latest
    container_name: qdrant-local
    restart: unless-stopped
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant_storage:/qdrant/storage
    networks:
      - manager-api_manager-api-network

  ollama:
    image: ollama/ollama:latest
    container_name: ollama-llm
    restart: unless-stopped
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    networks:
      - manager-api_manager-api-network

  media-server:
    image: nginx:alpine
    container_name: media-server
    restart: unless-stopped
    ports:
      - "8080:80"
    volumes:
      - ./local_media:/usr/share/nginx/html:ro
    networks:
      - manager-api_manager-api-network

networks:
  manager-api_manager-api-network:
    external: true

volumes:
  qdrant_storage:
  ollama_data:
```

---

## Phase 7: Testing & Verification

### Test Checklist

#### Network Isolation Test
```bash
# Disable internet access temporarily
sudo iptables -A OUTPUT -p tcp --dport 80 -j DROP
sudo iptables -A OUTPUT -p tcp --dport 443 -j DROP

# Test all features
python main.py dev
```

#### Component Tests
- [ ] LLM responds without internet (Ollama/local model)
- [ ] STT transcribes audio locally (Whisper)
- [ ] TTS generates speech locally (Coqui/Edge)
- [ ] Music search works (local Qdrant)
- [ ] Story search works (local Qdrant)
- [ ] Media playback works (local file server)
- [ ] Memory saves/loads (local storage or disabled)
- [ ] Device prompts load (from config or Manager API)

#### Monitoring
```bash
# Monitor network connections
netstat -tupn | grep python

# Should only see connections to:
# - localhost:6333 (Qdrant)
# - localhost:11434 (Ollama)
# - localhost:8080 (Media server)
# - 192.168.1.2:7880 (LiveKit)
# - 192.168.1.2:6380 (Redis)
# - 192.168.1.2:1883 (MQTT)
# - 192.168.1.2:8002 (Manager API - optional)
```

---

## Configuration Summary

### Final `.env` File (Fully Offline)
```env
# Read config from API (set to false for fully standalone)
read_config_from_api=false

# MQTT Configuration (Local)
MQTT_HOST=192.168.1.2
MQTT_PORT=1883
MQTT_CLIENT_ID=GID_test@@@00:11:22:33:44:55
MQTT_USERNAME=testuser
MQTT_PASSWORD=testpassword

# LiveKit Configuration (Local)
LIVEKIT_URL=ws://192.168.1.2:7880
LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=secret

# Redis Configuration (Local)
REDIS_URL=redis://:redispassword@192.168.1.2:6380
REDIS_PASSWORD=redispassword

# Agent Settings
PREEMPTIVE_GENERATION=false
NOISE_CANCELLATION=false
ENABLE_EDUCATION=true

# LLM Configuration (Local)
LLM_PROVIDER=ollama
OLLAMA_URL=http://localhost:11434
LLM_MODEL=llama3.1:8b

# STT Configuration (Local)
STT_PROVIDER=local_whisper
WHISPER_MODEL=base
WHISPER_DEVICE=cpu
STT_LANGUAGE=en

# TTS Configuration (Local)
TTS_PROVIDER=coqui
COQUI_MODEL=tts_models/en/ljspeech/tacotron2-DDC
COQUI_USE_GPU=false

# Qdrant Configuration (Local)
QDRANT_URL=http://localhost:6333

# Media Storage (Local)
USE_CDN=false
LOCAL_MEDIA_URL=http://192.168.1.2:8080

# Memory Configuration (Local)
MEM0_ENABLED=true
MEM0_TYPE=local

# Manager API (Optional - already local network)
MANAGER_API_URL=http://192.168.1.2:8002/toy
MANAGER_API_SECRET=da11d988-f105-4e71-b095-da62ada82189

# Weather API (Optional - requires internet if enabled)
# WEATHER_API=12dd0eea5789636262549c9ec7f4f7d8
```

---

## Implementation Timeline

### Week 1: Infrastructure Setup
- Day 1-2: Deploy local Qdrant, set up Ollama
- Day 3-4: Download and organize media files
- Day 5: Set up local media server

### Week 2: Code Implementation
- Day 1-2: Implement local LLM provider
- Day 3-4: Implement local STT (Whisper)
- Day 5: Implement/configure local TTS

### Week 3: Integration & Testing
- Day 1-2: Update services to use local resources
- Day 3-4: Integration testing
- Day 5: Network isolation testing

### Week 4: Optimization & Documentation
- Day 1-2: Performance optimization
- Day 3-4: Final testing and bug fixes
- Day 5: Documentation and deployment

---

## Rollback Plan

If offline implementation encounters issues:

1. **Keep current `.env` as `.env.cloud.backup`**
2. **Create `.env.offline` with new configuration**
3. **Use environment switching:**
   ```bash
   # Switch to offline mode
   cp .env.offline .env

   # Switch back to cloud mode
   cp .env.cloud.backup .env
   ```

---

## Performance Considerations

### Resource Requirements (Offline Mode)

#### CPU
- Whisper (base): ~2-4 CPU cores
- Ollama (llama3.1:8b): ~4-8 CPU cores
- Coqui TTS: ~2 CPU cores
- **Total**: 8-16 CPU cores recommended

#### RAM
- Whisper (base): ~1-2 GB
- Ollama (llama3.1:8b): ~8-10 GB
- Coqui TTS: ~1-2 GB
- Qdrant: ~500 MB
- **Total**: 12-16 GB RAM minimum

#### Storage
- Ollama models: ~5 GB
- Whisper models: ~150 MB (base)
- Coqui TTS models: ~500 MB
- Media files: Variable (depends on library size)
- Qdrant storage: ~1-5 GB
- **Total**: 10-20 GB+ storage

#### GPU (Optional but Recommended)
- Significantly speeds up Whisper STT
- Speeds up Ollama LLM inference
- Speeds up Coqui TTS generation

---

## Security Considerations

### Benefits of Offline Operation
✅ No data leaves local network
✅ No API keys exposed to external services
✅ Full control over data privacy
✅ No dependency on external service availability

### Remaining Considerations
⚠️ Ensure local network security (firewall, VPN)
⚠️ Secure Redis with strong password
⚠️ Secure Manager API with authentication
⚠️ Regular backups of local data

---

## Conclusion

This implementation plan provides a complete path to running the LiveKit-Server fully offline. The main challenges are:

1. **AI Model Performance**: Local models may be slower than cloud APIs
2. **Storage Requirements**: Media files and models require significant storage
3. **Initial Setup Complexity**: More components to deploy and configure

However, the benefits include:
- Complete data privacy
- No recurring API costs
- No dependency on internet connectivity
- Full control over the system

Choose the implementation phases based on priority and available resources.
