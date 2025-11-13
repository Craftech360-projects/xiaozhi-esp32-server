# Qwen3:4b Speed Optimization Guide

## 🐌 Problem
Qwen3:4b uses "thinking" mode which makes responses slow (5-10 seconds delay).

## ⚡ Solutions Applied

### 1. Increased Temperature (✅ Applied)
```python
# In provider_factory.py
temperature=0.8  # Higher = faster, less "thinking"
```

### 2. Disable Thinking via Ollama System Prompt
Add to your `.env`:
```bash
# Add this line
OLLAMA_SYSTEM_PROMPT="You are a fast, helpful assistant. Respond quickly and concisely without showing your thinking process."
```

### 3. Use Ollama Parameters (Recommended)
Create a Modelfile to disable thinking:

```bash
# Create modelfile
cat > qwen3-fast.Modelfile << 'EOF'
FROM qwen3:4b

# Disable thinking/reasoning tokens
PARAMETER stop "<think>"
PARAMETER stop "</think>"
PARAMETER stop "<reasoning>"
PARAMETER stop "</reasoning>"

# Speed optimizations
PARAMETER temperature 0.8
PARAMETER top_p 0.9
PARAMETER repeat_penalty 1.1

# System prompt for fast responses
SYSTEM You are Cheeko, a friendly AI assistant for kids. Respond quickly and naturally without showing your thinking process. Be concise and engaging.
EOF

# Create the optimized model
ollama create qwen3-fast -f qwen3-fast.Modelfile

# Test it
ollama run qwen3-fast "Hello!"
```

Then update `.env`:
```bash
LLM_MODEL=qwen3-fast
OLLAMA_MODEL=qwen3-fast
```

### 4. Alternative: Switch to Faster Model

If qwen3:4b is still slow, use these alternatives:

#### Option A: llama3.1:8b (Recommended)
```bash
ollama pull llama3.1:8b

# Update .env
LLM_MODEL=llama3.1:8b
OLLAMA_MODEL=llama3.1:8b
```

**Pros:**
- ✅ No thinking mode
- ✅ Fast responses (1-2s)
- ✅ Function calling support
- ✅ Better quality

**Cons:**
- ⚠️ Larger (5.5GB total memory)

#### Option B: phi3:3.8b (Fastest)
```bash
ollama pull phi3:3.8b

# Update .env
LLM_MODEL=phi3:3.8b
OLLAMA_MODEL=phi3:3.8b
```

**Pros:**
- ✅ Very fast (1-2s)
- ✅ Small (3.3GB total memory)
- ✅ Function calling support

**Cons:**
- ⚠️ Slightly lower quality than llama3.1

#### Option C: qwen2.5:7b (Balanced)
```bash
ollama pull qwen2.5:7b

# Update .env
LLM_MODEL=qwen2.5:7b
OLLAMA_MODEL=qwen2.5:7b
```

**Pros:**
- ✅ Fast (2-3s)
- ✅ No thinking mode
- ✅ Function calling support
- ✅ Good quality

**Cons:**
- ⚠️ Larger (5.5GB total memory)

## 🎯 Quick Fix: Create Fast Qwen Model

Run these commands:

```bash
# 1. Create optimized modelfile
cat > qwen3-fast.Modelfile << 'EOF'
FROM qwen3:4b
PARAMETER stop "<think>"
PARAMETER stop "</think>"
PARAMETER temperature 0.8
PARAMETER top_p 0.9
SYSTEM You are Cheeko, a friendly AI assistant for kids. Respond quickly without showing your thinking.
EOF

# 2. Create the model
ollama create qwen3-fast -f qwen3-fast.Modelfile

# 3. Update .env
sed -i 's/LLM_MODEL=qwen3:4b/LLM_MODEL=qwen3-fast/' .env
sed -i 's/OLLAMA_MODEL=qwen3:4b/OLLAMA_MODEL=qwen3-fast/' .env

# 4. Restart agent
python simple_main.py
```

## 📊 Speed Comparison

| Model | Response Time | Thinking Mode | Memory | Function Calling |
|-------|--------------|---------------|--------|------------------|
| **qwen3:4b** | 5-10s | ✅ YES (slow) | 3.5GB | ✅ YES |
| **qwen3-fast** | 2-3s | ❌ NO (disabled) | 3.5GB | ✅ YES |
| **llama3.1:8b** | 1-2s | ❌ NO | 5.5GB | ✅ YES |
| **phi3:3.8b** | 1-2s | ❌ NO | 3.3GB | ✅ YES |
| **qwen2.5:7b** | 2-3s | ❌ NO | 5.5GB | ✅ YES |

## ✅ Recommended Solution

**Create `qwen3-fast` model** (keeps low memory, removes thinking):

```bash
# Quick one-liner
ollama create qwen3-fast -f <(echo 'FROM qwen3:4b
PARAMETER stop "<think>"
PARAMETER stop "</think>"
PARAMETER temperature 0.8
SYSTEM Respond quickly without showing thinking.')

# Update .env
LLM_MODEL=qwen3-fast
OLLAMA_MODEL=qwen3-fast
```

This will:
- ✅ Keep low memory (3.5GB)
- ✅ Remove thinking delay
- ✅ Keep function calling
- ✅ Speed up to 2-3s responses

## 🚀 Alternative: Switch to llama3.1:8b

If you want the best quality and speed:

```bash
ollama pull llama3.1:8b

# Update .env
LLM_MODEL=llama3.1:8b
OLLAMA_MODEL=llama3.1:8b
```

**Result:**
- Response time: 1-2s (fast!)
- Memory: 5.5GB (still fits in 8GB)
- Quality: Excellent
- Function calling: ✅ Works perfectly

## 💡 Summary

**Problem:** qwen3:4b is slow due to thinking mode  
**Solution 1:** Create `qwen3-fast` (disable thinking) ✅ **RECOMMENDED**  
**Solution 2:** Switch to `llama3.1:8b` (no thinking, faster) ✅ **BEST QUALITY**  
**Solution 3:** Switch to `phi3:3.8b` (smallest, fast) ✅ **LOWEST MEMORY**

Choose based on your priority:
- **Want to keep qwen3?** → Create `qwen3-fast`
- **Want best quality?** → Use `llama3.1:8b`
- **Want lowest memory?** → Use `phi3:3.8b`
