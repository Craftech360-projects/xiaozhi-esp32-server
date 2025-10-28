# FunASR Quick Start Guide

Get started with FunASR local speech recognition in 3 simple steps!

## What is FunASR?

FunASR is Alibaba's open-source speech recognition system that runs **completely locally** on your machine:

✅ **Zero API Costs** - No external API calls
✅ **Privacy-First** - All audio processing stays on-device
✅ **Multilingual** - Chinese, English, Japanese, Korean
✅ **Offline Capable** - Works without internet
✅ **Fast** - Optimized for real-time applications

---

## Quick Start (3 Steps)

### Step 1: Install Dependencies

```bash
pip install funasr==1.2.3 modelscope onnxruntime psutil
```

### Step 2: Download Model (One-Time)

```bash
python scripts/download_funasr_model.py
```

**Expected output:**
```
============================================================
FunASR SenseVoiceSmall Model Download
============================================================
Downloading to: C:\Users\...\model_cache\funasr
Model size: ~300MB
This is a one-time download...

✓ Model downloaded successfully!
============================================================
```

**Model size:** ~300MB (one-time download)

### Step 3: Configure & Run

**Update `.env`:**
```env
STT_PROVIDER=funasr
FUNASR_DEVICE=cpu
```

**Run the agent:**
```bash
python main.py --workers 3
```

**Done!** 🎉 FunASR is now handling all speech recognition locally.

---

## Configuration Options

### Basic Configuration

```env
# Enable FunASR
STT_PROVIDER=funasr

# Model location (default: model_cache/funasr/SenseVoiceSmall)
FUNASR_MODEL_DIR=model_cache/funasr/SenseVoiceSmall

# Language: auto, zh, en, ja, ko
FUNASR_LANGUAGE=auto

# Compute device: cpu or cuda:0
FUNASR_DEVICE=cpu
```

### Advanced Configuration

```env
# Inverse Text Normalization (spoken numbers → digits)
FUNASR_USE_ITN=true

# Max VAD segment duration (ms)
FUNASR_MAX_SEGMENT_TIME=30000

# Use external Silero VAD
FUNASR_USE_EXTERNAL_VAD=false
```

---

## GPU Acceleration (Optional)

If you have an NVIDIA GPU, you can significantly speed up inference:

### Enable GPU

**1. Install GPU support:**
```bash
pip install onnxruntime-gpu
```

**2. Update .env:**
```env
FUNASR_DEVICE=cuda:0
```

### Performance Comparison

| Device | Latency | Throughput |
|--------|---------|------------|
| **CPU** | ~350ms | 5 concurrent sessions |
| **GPU** | ~100ms | 20+ concurrent sessions |

---

## Supported Languages

| Language | Code | Example |
|----------|------|---------|
| **Auto-detect** | `auto` | Automatically detects language |
| **Chinese** | `zh` | "你好世界" |
| **English** | `en` | "Hello world" |
| **Japanese** | `ja` | "こんにちは世界" |
| **Korean** | `ko` | "안녕하세요 세계" |

**Example - Chinese mode:**
```env
FUNASR_LANGUAGE=zh
```

---

## System Requirements

### Minimum Requirements

- **RAM:** 2GB available
- **Disk:** 500MB for model
- **CPU:** Multi-core recommended
- **OS:** Windows, Linux, macOS

### Recommended Requirements

- **RAM:** 4GB+ available
- **GPU:** NVIDIA GPU with CUDA support (optional)
- **CPU:** 4+ cores for concurrent sessions

---

## Troubleshooting

### Model Not Found

**Error:**
```
FunASR model not found at model_cache/funasr/SenseVoiceSmall
```

**Solution:**
```bash
python scripts/download_funasr_model.py
```

### Out of Memory

**Error:**
```
Insufficient memory for FunASR: 1.5GB available, minimum 2GB required
```

**Solutions:**
1. Close other applications
2. Restart your computer
3. Add swap space (Linux)
4. Upgrade RAM

### Import Errors

**Error:**
```
ModuleNotFoundError: No module named 'funasr'
```

**Solution:**
```bash
pip install -r requirements.txt
```

### Slow Performance

**Symptom:** Transcription takes > 1 second

**Solutions:**
1. Enable GPU: `FUNASR_DEVICE=cuda:0`
2. Reduce concurrent sessions
3. Check CPU usage (should be < 80%)
4. Reduce `FUNASR_MAX_SEGMENT_TIME`

---

## Comparison with Cloud STT

### FunASR (Local)

✅ **$0 per transcription**
✅ **100% private** (all processing local)
✅ **Works offline**
✅ **No API rate limits**
✅ **Multilingual** (4 languages)

⚠️ Requires model download (~300MB)
⚠️ Requires 2GB+ RAM

### Groq/Deepgram (Cloud)

✅ **No model download**
✅ **Lower memory usage**
✅ **More languages supported**

⚠️ **Costs $0.10-0.25 per 1000 requests**
⚠️ **Requires internet**
⚠️ **Audio sent to external servers**
⚠️ **Subject to API rate limits**

---

## Testing

### Run Unit Tests

```bash
pytest tests/test_funasr_provider.py -v
```

### Run Integration Tests

```bash
pytest tests/test_funasr_integration.py -v
```

### Run Performance Benchmarks

```bash
python tests/benchmark_funasr.py
```

**Expected benchmark results:**
```
=== Latency Benchmark ===
Average: 350.25ms
Min: 320.10ms
Max: 380.50ms
Throughput: 2.85 transcriptions/sec

=== Memory Benchmark ===
Baseline: 150.00 MB
After model load: 2650.00 MB
Model memory usage: 2500.00 MB

=== CPU Benchmark ===
Average CPU: 65.50%
Max CPU: 85.20%
```

---

## Advanced Usage

### Custom Model Path

```env
FUNASR_MODEL_DIR=/custom/path/to/model
```

### Multiple Devices

```python
# Device 1: Use FunASR
STT_PROVIDER=funasr

# Device 2: Use Groq
STT_PROVIDER=groq
```

### ITN (Inverse Text Normalization)

Convert spoken numbers to digits:

```env
FUNASR_USE_ITN=true
```

**Examples:**
- "一百" → "100" (Chinese)
- "one hundred" → "100" (English)
- "百" → "100" (Japanese)

---

## Migration from Groq/Deepgram

### Step-by-Step Migration

**1. Backup current config:**
```bash
cp .env .env.backup
```

**2. Download FunASR model:**
```bash
python scripts/download_funasr_model.py
```

**3. Update .env:**
```env
# Before
STT_PROVIDER=groq

# After
STT_PROVIDER=funasr
```

**4. Test:**
```bash
python main.py --workers 1
```

**5. If successful, scale up:**
```bash
python main.py --workers 3
```

### Rollback (if needed)

```bash
# Restore backup
cp .env.backup .env

# Restart
python main.py --workers 3
```

---

## FAQ

### Q: Can I use FunASR and Groq simultaneously?

**A:** Yes! Configure different devices to use different providers based on your needs.

### Q: Does FunASR support real-time streaming?

**A:** Yes, FunASR supports real-time speech recognition with built-in VAD.

### Q: Can I use my own trained model?

**A:** Yes, set `FUNASR_MODEL_DIR` to your custom model path.

### Q: What's the model file size?

**A:** ~300MB for SenseVoiceSmall (one-time download).

### Q: Can I delete the model after loading?

**A:** No, the model is loaded from disk on each startup. Keep it available.

### Q: Does FunASR work on ARM processors (Raspberry Pi)?

**A:** Yes, but performance may vary. GPU acceleration not available on ARM.

---

## Support

**Documentation:**
- [FunASR Integration Plan](FUNASR_INTEGRATION_PLAN.md)
- [Main README](README.md)
- [Test Documentation](tests/README.md)

**External Resources:**
- [FunASR GitHub](https://github.com/alibaba-damo-academy/FunASR)
- [FunASR Documentation](https://alibaba-damo-academy.github.io/FunASR/)
- [LiveKit Documentation](https://docs.livekit.io/)

**Issues:**
- Check [FUNASR_INTEGRATION_PLAN.md](FUNASR_INTEGRATION_PLAN.md) for detailed troubleshooting
- Review system logs for error details
- Ensure system meets minimum requirements

---

**Version:** 1.0
**Last Updated:** 2025-10-28
**Status:** Production Ready ✅
