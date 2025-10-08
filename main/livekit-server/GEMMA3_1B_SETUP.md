# 🚀 Gemma2:2b Setup Guide

Quick guide for using Google's Gemma2:2b model with your offline LiveKit server.

## Why Gemma2:2b?

**Gemma2:2b** is an excellent choice for offline operation:

✅ **Small Size**: Only ~1.5GB (vs 5GB for llama3.1:8b)
✅ **Fast**: Quick responses, low latency
✅ **Low Memory**: Uses only ~2-3GB RAM
✅ **Good Quality**: Google's efficient architecture
✅ **Great for Conversational AI**: Optimized for chat

## Quick Setup

### 1. Pull the Model

```bash
# Pull gemma2:2b from Ollama
docker exec ollama-llm ollama pull gemma2:2b

# Verify it's downloaded
docker exec ollama-llm ollama list
```

Expected output:
```
NAME            ID              SIZE    MODIFIED
gemma2:2b       abc123def456    1.5 GB  2 minutes ago
```

### 2. Configuration Already Set

Your `.env` file is already configured to use gemma2:2b:

```env
LLM_PROVIDER=ollama
OLLAMA_URL=http://localhost:11434
LLM_MODEL=gemma2:2b
```

### 3. Test the Model

```bash
# Test directly with Ollama
docker exec ollama-llm ollama run gemma2:2b "Hello, how are you?"

# Or test via API
curl http://localhost:11434/api/generate -d '{
  "model": "gemma2:2b",
  "prompt": "Hello, introduce yourself",
  "stream": false
}'
```

### 4. Start LiveKit Server

```bash
python main.py dev
```

## Model Comparison

| Model | Size | RAM | Speed | Quality | Best For |
|-------|------|-----|-------|---------|----------|
| **gemma2:2b** | 1.5GB | 2-3GB | ⚡⚡⚡ Fast | ⭐⭐⭐ Good | Conversational AI |
| llama3.1:8b | 5GB | 8-10GB | ⚡ Slow | ⭐⭐⭐⭐⭐ Excellent | Complex tasks |
| phi3:mini | 2GB | 2-4GB | ⚡⚡ Fast | ⭐⭐⭐ Good | Quick responses |
| mistral:7b | 4GB | 6-8GB | ⚡⚡ Medium | ⭐⭐⭐⭐ Very Good | General purpose |

## Resource Requirements with Gemma2:2b

### Minimum Configuration
- **CPU**: 4-8 cores
- **RAM**: 8 GB total (vs 12GB for llama3.1:8b)
- **Disk**: 5 GB (vs 10GB)
- **Model**: gemma2:2b + tiny whisper + edge TTS

### Recommended Configuration
- **CPU**: 8-12 cores
- **RAM**: 12 GB
- **Disk**: 10 GB
- **Model**: gemma2:2b + base whisper + coqui TTS

## Performance Tips with Gemma2:2b

### 1. Optimal Temperature
```env
LLM_TEMPERATURE=0.7  # Good balance
# LLM_TEMPERATURE=0.5  # More focused responses
# LLM_TEMPERATURE=0.9  # More creative responses
```

### 2. System Prompt Optimization

Gemma2 works best with clear, concise system prompts:

```python
# Good for Gemma2
system_prompt = """You are Cheeko, a friendly AI assistant.
Keep responses brief and conversational."""

# Avoid overly long prompts with Gemma2:2b
```

### 3. Context Window

Gemma2:2b has a smaller context window:
- Keep conversation history concise
- Summarize older messages
- Focus on recent context

## Troubleshooting

### Model Not Found

```bash
# Check if model exists
docker exec ollama-llm ollama list

# If not, pull it
docker exec ollama-llm ollama pull gemma2:2b
```

### Slow Responses

```bash
# Check Ollama logs
docker logs ollama-llm

# Restart Ollama
docker-compose restart ollama
```

### Out of Memory

Gemma2:2b should NOT cause OOM issues. If you still have problems:

```bash
# Check memory usage
docker stats

# Use even smaller model
docker exec ollama-llm ollama pull gemma:1b
# Then edit .env: LLM_MODEL=gemma:1b
```

### Quality Issues

If responses aren't good enough, try:

1. **Adjust temperature**:
   ```env
   LLM_TEMPERATURE=0.5  # More focused
   ```

2. **Improve prompts**: Be more specific
3. **Use larger model** if resources allow:
   ```bash
   docker exec ollama-llm ollama pull gemma2:9b
   # Edit .env: LLM_MODEL=gemma2:9b
   ```

## Alternative Gemma Models

### Gemma 1 Series (Older)
```bash
ollama pull gemma:2b    # 1.5GB
ollama pull gemma:7b    # 4GB
```

### Gemma 2 Series (Newer, Better)
```bash
ollama pull gemma2:2b   # 1.5GB ✅ Current choice
ollama pull gemma2:9b   # 5GB  (better quality)
ollama pull gemma2:27b  # 15GB (best quality)
```

## Testing Gemma2:2b

### Interactive Test
```bash
docker exec -it ollama-llm ollama run gemma2:2b
```

Then chat:
```
>>> Hello!
Hello! 👋 How can I help you today?

>>> What's your name?
I'm Gemma, a large language model...

>>> /bye
```

### Benchmark Test

```python
import time
import aiohttp
import asyncio

async def test_gemma_speed():
    url = "http://localhost:11434/api/generate"

    prompts = [
        "Say hello",
        "What's 2+2?",
        "Tell me a joke",
        "Explain AI briefly",
    ]

    for prompt in prompts:
        data = {
            "model": "gemma2:2b",
            "prompt": prompt,
            "stream": False
        }

        start = time.time()
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data) as resp:
                result = await resp.json()

        elapsed = time.time() - start
        response = result.get('response', '')

        print(f"\nPrompt: {prompt}")
        print(f"Time: {elapsed:.2f}s")
        print(f"Response: {response[:100]}...")

asyncio.run(test_gemma_speed())
```

## Configuration Summary

Your current setup uses:

```env
# LLM: Gemma2:2b (Fast, efficient)
LLM_PROVIDER=ollama
LLM_MODEL=gemma2:2b

# STT: Whisper base (Good balance)
STT_PROVIDER=local_whisper
WHISPER_MODEL=base

# TTS: Coqui or Edge
TTS_PROVIDER=coqui  # or edge
```

This is an **excellent configuration** for:
- Low-resource environments
- Fast response times
- Conversational AI applications
- Battery-powered devices (if applicable)

## Expected Performance

With Gemma2:2b, expect:

- **Latency**: 0.5-2 seconds per response
- **Memory**: 2-3GB for Ollama + model
- **CPU**: 50-70% during inference
- **Quality**: Good for conversations, may struggle with complex reasoning

## Upgrading Later

If you need better quality later:

```bash
# Pull larger model
docker exec ollama-llm ollama pull llama3.1:8b

# Edit .env
LLM_MODEL=llama3.1:8b

# Restart
python main.py dev
```

## Best Practices

1. **Keep prompts concise** - Gemma2:2b works best with focused prompts
2. **Use system prompts** - Guide the model's behavior
3. **Monitor memory** - Should stay under 3GB
4. **Test thoroughly** - Ensure quality meets your needs
5. **Have fallback** - Keep a larger model ready if needed

## Need Help?

- **Documentation**: See [OFFLINE_SETUP_GUIDE.md](OFFLINE_SETUP_GUIDE.md)
- **Ollama Issues**: `docker logs ollama-llm`
- **Model Info**: `docker exec ollama-llm ollama show gemma2:2b`

---

## ✅ You're All Set!

Your LiveKit server is configured to use **Gemma2:2b** - a fast, efficient model perfect for offline conversational AI!

**Next steps:**
1. Pull the model: `docker exec ollama-llm ollama pull gemma2:2b`
2. Test it: `docker exec ollama-llm ollama run gemma2:2b "hello"`
3. Start server: `python main.py dev`

Enjoy your fast, offline AI! 🚀
