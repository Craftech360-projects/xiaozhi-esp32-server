# Memory Optimization Guide

## 🔴 Current Issue
- **Memory Usage:** 4.4GB per process (95% of system RAM)
- **Model:** Whisper `medium.en` (1.5GB)
- **Clients:** 2 active connections
- **Status:** High memory warnings

## 📊 Whisper Model Comparison

| Model | Size | RAM Usage | Speed | Accuracy | Recommendation |
|-------|------|-----------|-------|----------|----------------|
| **tiny.en** | 39MB | ~500MB | ⚡⚡⚡⚡⚡ Fastest | ⭐⭐⭐ Good | ✅ Best for low-memory |
| **base.en** | 74MB | ~800MB | ⚡⚡⚡⚡ Very Fast | ⭐⭐⭐⭐ Very Good | ✅ **RECOMMENDED** |
| **small.en** | 244MB | ~1.2GB | ⚡⚡⚡ Fast | ⭐⭐⭐⭐⭐ Excellent | ⚠️ Good balance |
| **medium.en** | 769MB | ~1.5GB | ⚡⚡ Moderate | ⭐⭐⭐⭐⭐ Excellent | ❌ Current (too heavy) |
| **large** | 1.5GB | ~3GB | ⚡ Slow | ⭐⭐⭐⭐⭐ Best | ❌ Not recommended |

## ✅ Recommended Fix: Switch to `base.en`

### Why `base.en`?
- ✅ **3x less memory** (~800MB vs 1.5GB)
- ✅ **2x faster** transcription
- ✅ **Still excellent accuracy** for conversational English
- ✅ **Perfect for kids' content** (simple vocabulary)
- ✅ **Allows more concurrent clients**

### Expected Results After Switch:
```
Before (medium.en):
- Memory: 4.4GB per process (95% RAM)
- Can handle: 2 clients max
- Transcription: ~2-3 seconds

After (base.en):
- Memory: ~2.5GB per process (50% RAM)
- Can handle: 4-5 clients
- Transcription: ~1-2 seconds
```

## 🔧 How to Apply Fix

### Step 1: Update `.env` file
Change line 60 in `main/livekit-server_simple/.env`:

```bash
# Before
STT_MODEL=medium.en

# After
STT_MODEL=base.en
```

### Step 2: Restart the agent
```bash
# Stop current agent (Ctrl+C)
# Start again
python simple_main.py
```

### Step 3: Verify
Check logs for:
```
🆕 [STT-CACHE] Creating new WhisperSTT instance: base.en_en
⏳ [WHISPER-LOAD] Loading Whisper model: base.en
✅ [WHISPER-LOAD] Whisper model loaded successfully: base.en
```

Memory should drop to ~2.5GB per process.

## 🎯 Alternative: Use `tiny.en` for Maximum Performance

If you need even lower memory:

```bash
STT_MODEL=tiny.en
```

**Results:**
- Memory: ~1.5GB per process (30% RAM)
- Can handle: 8-10 clients
- Transcription: <1 second
- Accuracy: Still good for simple conversations

**Trade-off:** Slightly lower accuracy on complex words, but perfect for kids' content.

## 📈 Memory Usage by Configuration

| Config | Memory/Process | Max Clients | Total RAM (8GB system) |
|--------|---------------|-------------|------------------------|
| **medium.en** | 4.4GB | 2 | 95% (current) |
| **small.en** | 3.0GB | 3 | 75% |
| **base.en** | 2.5GB | 4 | 50% ✅ |
| **tiny.en** | 1.5GB | 6 | 30% |

## 🔍 Other Memory Optimizations

### 1. Limit LLM Context History
Add to your config:
```python
# In simple_main.py or config
max_context_messages = 10  # Keep only last 10 messages
```

### 2. Enable Garbage Collection
Add periodic cleanup:
```python
import gc
gc.collect()  # Force garbage collection every N requests
```

### 3. Use FastWhisper Instead
FastWhisper is 2-4x faster and uses less memory:
```bash
STT_PROVIDER=fastwhisper
STT_MODEL=base.en
```

### 4. Reduce Worker Count
If running multiple workers, reduce to 2:
```bash
# In your start script
python simple_main.py --workers 2
```

## 🎯 Recommended Configuration

For your use case (kids' learning toy with 2-3 concurrent users):

```bash
# .env
STT_PROVIDER=whisper
STT_MODEL=base.en  # ✅ Best balance

# Or for maximum performance:
STT_PROVIDER=fastwhisper
STT_MODEL=base.en
```

**Expected Results:**
- ✅ Memory: 2.5GB per process (50% RAM)
- ✅ CPU: 30-40% average
- ✅ Transcription: 1-2 seconds
- ✅ Accuracy: Excellent for kids' content
- ✅ Can handle 4-5 concurrent clients

## 📊 Monitoring

After applying the fix, monitor:
```
📊 RESOURCES | Clients: 2 | RAM: 50% (proc: 2500MB)  ✅ GOOD
```

Instead of:
```
📊 RESOURCES | Clients: 2 | RAM: 95% (proc: 4400MB)  ❌ BAD
```

## 🚀 Quick Fix Command

```bash
# 1. Stop agent (Ctrl+C)

# 2. Update .env
sed -i 's/STT_MODEL=medium.en/STT_MODEL=base.en/' .env

# 3. Restart
python simple_main.py
```

Memory usage should drop from 4.4GB to ~2.5GB immediately! 🎉
