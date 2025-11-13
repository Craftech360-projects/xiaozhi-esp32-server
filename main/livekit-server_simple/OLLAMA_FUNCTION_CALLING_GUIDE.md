# Ollama Models - Function Calling Support Guide

## 🎯 Function Calling Requirements

For MCP (device control) to work, you need a model that supports **function calling / tool use**.

## ✅ Models That Support Function Calling

### Llama Models:
| Model | Size | Function Calling | Speed | Recommendation |
|-------|------|------------------|-------|----------------|
| **llama3.1:8b** | 4.7GB | ✅ YES | ⚡⚡⚡ Fast | ✅ **BEST for function calling** |
| **llama3.1:70b** | 40GB | ✅ YES | ⚡ Slow | ❌ Too large |
| **llama3.2:1b** | 1.3GB | ❌ NO | ⚡⚡⚡⚡⚡ Fastest | ❌ No tools |
| **llama3.2:3b** | 2.0GB | ❌ NO | ⚡⚡⚡⚡ Very Fast | ❌ No tools (current) |
| **llama3.3:70b** | 43GB | ✅ YES | ⚡ Slow | ❌ Too large |

### Other Models with Function Calling:
| Model | Size | Function Calling | Speed | Recommendation |
|-------|------|------------------|-------|----------------|
| **qwen2.5:7b** | 4.7GB | ✅ YES | ⚡⚡⚡ Fast | ✅ Excellent |
| **qwen2.5:14b** | 9.0GB | ✅ YES | ⚡⚡ Moderate | ⚠️ Large |
| **qwen3:4b** | 2.5GB | ✅ YES | ⚡⚡⚡⚡ Very Fast | ✅ **RECOMMENDED** (current) |
| **mistral:7b** | 4.1GB | ✅ YES | ⚡⚡⚡ Fast | ✅ Good |
| **mixtral:8x7b** | 26GB | ✅ YES | ⚡ Slow | ❌ Too large |
| **gemma2:9b** | 5.5GB | ✅ YES | ⚡⚡⚡ Fast | ✅ Good |
| **gemma3:1b** | 815MB | ❌ NO | ⚡⚡⚡⚡⚡ Fastest | ❌ No tools |
| **phi3:3.8b** | 2.3GB | ✅ YES | ⚡⚡⚡⚡ Very Fast | ✅ Good |
| **phi4:14b** | 9.1GB | ✅ YES | ⚡⚡ Moderate | ⚠️ Large |

## 🎯 Recommended Models for Your Use Case

### Best Balance (Function Calling + Performance):
1. **qwen3:4b** (2.5GB) - ✅ **CURRENT CHOICE**
   - Fast, supports tools, good for kids' content
   - Memory: ~3.5GB total

2. **llama3.1:8b** (4.7GB) - ✅ **BEST LLAMA OPTION**
   - Official Llama with function calling
   - Memory: ~5.5GB total
   - Better reasoning than qwen3:4b

3. **phi3:3.8b** (2.3GB) - ✅ Good alternative
   - Small, fast, supports tools
   - Memory: ~3.3GB total

### If You Want Llama Specifically:
**Use `llama3.1:8b`** - This is the smallest Llama model with function calling support.

## 📥 How to Download Models

```bash
# Download llama3.1:8b (recommended Llama with function calling)
ollama pull llama3.1:8b

# Or download qwen2.5:7b (excellent alternative)
ollama pull qwen2.5:7b

# Or download phi3:3.8b (smaller alternative)
ollama pull phi3:3.8b
```

## 🔧 How to Switch Models

### Option 1: Use llama3.1:8b (Best Llama)
```bash
# In .env file
LLM_MODEL=llama3.1:8b
OLLAMA_MODEL=llama3.1:8b
```

**Expected Memory:** ~5.5GB total (2.5GB Whisper + 3GB model)

### Option 2: Keep qwen3:4b (Current - Good)
```bash
# In .env file (already set)
LLM_MODEL=qwen3:4b
OLLAMA_MODEL=qwen3:4b
```

**Expected Memory:** ~3.5GB total (2.5GB Whisper + 1GB model)

### Option 3: Use phi3:3.8b (Smallest with tools)
```bash
# In .env file
LLM_MODEL=phi3:3.8b
OLLAMA_MODEL=phi3:3.8b
```

**Expected Memory:** ~3.3GB total (2.5GB Whisper + 800MB model)

## ⚠️ Why llama3.2:3b Doesn't Work

The `llama3.2` series (1b, 3b) are **lightweight models** that don't support function calling:
- ❌ No tool use capability
- ❌ Will output JSON as text instead of calling functions
- ❌ MCP device control won't work

The `llama3.1` series (8b, 70b) are **full models** with function calling:
- ✅ Proper tool use support
- ✅ Can call MCP functions
- ✅ Device control works

## 🧪 Test Function Calling

After switching models, test with:
```bash
python test_ollama.py
```

Or test manually:
```bash
curl http://192.168.1.114:11434/api/chat -d '{
  "model": "llama3.1:8b",
  "messages": [{"role": "user", "content": "Set volume to 50"}],
  "tools": [{
    "type": "function",
    "function": {
      "name": "set_device_volume",
      "description": "Set device volume",
      "parameters": {
        "type": "object",
        "properties": {
          "volume": {"type": "integer"}
        }
      }
    }
  }]
}'
```

If the model supports tools, it will return:
```json
{
  "message": {
    "tool_calls": [{
      "function": {
        "name": "set_device_volume",
        "arguments": {"volume": 50}
      }
    }]
  }
}
```

If it doesn't support tools, it will return text like:
```json
{
  "message": {
    "content": "{\"name\": \"set_device_volume\", \"parameters\": {\"volume\": 50}}"
  }
}
```

## 📊 Memory Comparison

| Configuration | Whisper | LLM | Total | Function Calling |
|---------------|---------|-----|-------|------------------|
| **Current (qwen3:4b + base.en)** | 2.5GB | 1.0GB | 3.5GB | ✅ YES |
| **llama3.1:8b + base.en** | 2.5GB | 3.0GB | 5.5GB | ✅ YES |
| **llama3.2:3b + base.en** | 2.5GB | 0.8GB | 3.3GB | ❌ NO |
| **phi3:3.8b + base.en** | 2.5GB | 0.8GB | 3.3GB | ✅ YES |

## 🎯 Final Recommendation

### For Your 8GB RAM System:

**Option 1: Keep qwen3:4b (Current)**
- ✅ Already working
- ✅ Low memory (3.5GB)
- ✅ Fast
- ✅ Function calling works
- ⚠️ Not a Llama model

**Option 2: Switch to llama3.1:8b**
- ✅ Official Llama with function calling
- ✅ Better reasoning
- ⚠️ Higher memory (5.5GB)
- ⚠️ Slower than qwen3:4b

**Option 3: Switch to phi3:3.8b**
- ✅ Smallest with function calling
- ✅ Low memory (3.3GB)
- ✅ Fast
- ⚠️ Not a Llama model

## 🚀 Quick Fix Commands

### To use llama3.1:8b (Best Llama):
```bash
# 1. Download model
ollama pull llama3.1:8b

# 2. Update .env
sed -i 's/LLM_MODEL=qwen3:4b/LLM_MODEL=llama3.1:8b/' .env
sed -i 's/OLLAMA_MODEL=qwen3:4b/OLLAMA_MODEL=llama3.1:8b/' .env

# 3. Restart agent
python simple_main.py
```

### To use phi3:3.8b (Smallest with tools):
```bash
# 1. Download model
ollama pull phi3:3.8b

# 2. Update .env
sed -i 's/LLM_MODEL=qwen3:4b/LLM_MODEL=phi3:3.8b/' .env
sed -i 's/OLLAMA_MODEL=qwen3:4b/OLLAMA_MODEL=phi3:3.8b/' .env

# 3. Restart agent
python simple_main.py
```

## ✅ Summary

- **llama3.2:3b** ❌ No function calling
- **llama3.1:8b** ✅ Has function calling (recommended Llama)
- **qwen3:4b** ✅ Has function calling (current, good choice)
- **phi3:3.8b** ✅ Has function calling (smallest option)

Choose based on your priorities:
- **Want Llama?** → Use `llama3.1:8b`
- **Want low memory?** → Keep `qwen3:4b` or use `phi3:3.8b`
- **Want best quality?** → Use `llama3.1:8b`
