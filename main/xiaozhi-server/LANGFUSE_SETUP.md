# Langfuse Integration Setup Guide

This guide explains how to set up Langfuse for comprehensive LLM, STT, and TTS tracking in the xiaozhi-esp32-server project.

## What is Langfuse?

Langfuse is an LLM observability platform that helps you track, analyze, and optimize your AI applications by monitoring:
- **LLM calls** with costs, tokens, and performance metrics
- **STT (Speech-to-Text)** operations with audio metadata and response times
- **TTS (Text-to-Speech)** operations with voice settings and character counts
- **Complete conversation traces** linking STT → LLM → TTS pipelines

## Integration Features

### ✅ Already Implemented:

1. **LLM Tracking** (`core/providers/llm/openai/openai.py`):
   - Token usage (input/output) with precise counting using tiktoken
   - Cost calculation for all major models (GPT-4, GPT-3.5, Claude, Gemini, etc.)
   - Response time monitoring
   - Streaming and function-calling support
   - Error tracking and debugging

2. **STT Tracking** (`core/providers/asr/openai.py`):
   - Audio metadata (format, language, file size)
   - Transcription quality and length
   - Response time monitoring
   - Error handling and status tracking

3. **TTS Tracking** (`core/providers/tts/ttson.py`):
   - Voice settings (voice_id, emotion, format, speed, pitch)
   - Character processing metrics
   - Audio generation success/failure tracking
   - Response time monitoring

4. **Comprehensive Cost Tracking**:
   - Real-time cost calculation for 15+ models
   - Input/output token-based pricing
   - USD pricing with 6-decimal precision

5. **Session-based Traces**:
   - Links STT → LLM → TTS operations in conversations
   - Session ID tracking across all providers
   - Pipeline performance analysis

## Quick Setup

### 1. Get Langfuse API Keys

1. Sign up at [Langfuse](https://cloud.langfuse.com) (free tier available)
2. Create a new project
3. Get your API keys from the project settings:
   - `LANGFUSE_SECRET_KEY` (starts with `sk-lf-...`)
   - `LANGFUSE_PUBLIC_KEY` (starts with `pk-lf-...`)

### 2. Set Environment Variables

**Option A: Using `.env` file (Recommended)**
```bash
# Create .env file in the xiaozhi-server directory
echo "LANGFUSE_SECRET_KEY=sk-lf-your-secret-key-here" >> .env
echo "LANGFUSE_PUBLIC_KEY=pk-lf-your-public-key-here" >> .env
echo "LANGFUSE_HOST=https://cloud.langfuse.com" >> .env  # Optional
```

**Option B: System Environment Variables**
```bash
# Windows
set LANGFUSE_SECRET_KEY=sk-lf-your-secret-key-here
set LANGFUSE_PUBLIC_KEY=pk-lf-your-public-key-here

# Linux/Mac
export LANGFUSE_SECRET_KEY=sk-lf-your-secret-key-here
export LANGFUSE_PUBLIC_KEY=pk-lf-your-public-key-here
```

### 3. Test the Integration

```bash
cd main/xiaozhi-server
python test_langfuse_config.py
```

Expected output when properly configured:
```
============================================================
LANGFUSE INTEGRATION TEST
============================================================
1. Testing Langfuse Configuration...
   [OK] Langfuse client initialized successfully
   [INFO] Client instance: <class 'langfuse.client.Langfuse'>

...

[SUCCESS] LANGFUSE INTEGRATION TEST COMPLETED SUCCESSFULLY!
```

### 4. Verify in Dashboard

1. Run some conversations with your xiaozhi device
2. Check your Langfuse dashboard at https://cloud.langfuse.com
3. You should see traces with:
   - **Sessions** for each conversation
   - **Generations** for LLM calls with costs and tokens
   - **STT operations** with audio metadata
   - **TTS operations** with voice settings

## Configuration Files

### Core Components:
- `config/langfuse_config.py` - Main configuration and client setup
- `core/providers/llm/langfuse_wrapper.py` - Comprehensive tracking wrapper
- `requirements.txt` - Includes `langfuse>=3.0.0` and `tiktoken>=0.5.0`

### Integration Points:
- `core/providers/llm/openai/openai.py` - LLM tracking decorators
- `core/providers/asr/openai.py` - STT manual tracking
- `core/providers/tts/ttson.py` - TTS manual tracking

## Troubleshooting

### Issue: "Langfuse client not initialized"
**Solution**: Check environment variables are set correctly
```bash
python -c "import os; print('SECRET:', bool(os.getenv('LANGFUSE_SECRET_KEY'))); print('PUBLIC:', bool(os.getenv('LANGFUSE_PUBLIC_KEY')))"
```

### Issue: "Authentication error"
**Solution**: Verify API keys are correct and have proper permissions

### Issue: "No traces appearing in dashboard"
**Solution**: 
1. Check if tracking is enabled: `langfuse_config.is_enabled()`
2. Verify session IDs are being passed correctly
3. Check for network connectivity issues

### Issue: Token counting errors
**Solution**: Ensure tiktoken is installed: `pip install tiktoken>=0.5.0`

## Monitoring & Analytics

### Key Metrics Available:
1. **Cost Analysis**: Track spending per model, session, and time period
2. **Performance**: Response times for STT, LLM, and TTS operations
3. **Usage**: Token consumption, audio processing volume
4. **Quality**: Error rates, success ratios
5. **User Analytics**: Session lengths, interaction patterns

### Dashboard Views:
- **Sessions**: Complete conversation traces with all components
- **Generations**: Individual LLM/STT/TTS operations
- **Users**: Session-based user analytics (using device IDs)
- **Models**: Performance comparison across different providers

## Security Notes

- API keys are loaded from environment variables only
- No sensitive data is logged to traces by default
- Audio files are tracked via metadata only (no actual audio content)
- All network communication uses HTTPS

## Self-Hosting (Optional)

For organizations requiring on-premise deployment:
1. Follow [Langfuse self-hosting guide](https://langfuse.com/docs/deployment/self-host)
2. Set `LANGFUSE_HOST` to your self-hosted instance URL
3. Use same API key configuration process

## Support

- **Langfuse Documentation**: https://langfuse.com/docs
- **Test Script**: Run `python test_langfuse_config.py` for diagnostics
- **Configuration Check**: All settings in `config/langfuse_config.py`

---

## Integration Summary

✅ **Comprehensive tracking** for all AI operations  
✅ **Real-time cost monitoring** with accurate token counting  
✅ **Performance analytics** with response time tracking  
✅ **Error monitoring** and debugging capabilities  
✅ **Session-based tracing** linking entire conversation flows  
✅ **Zero impact** on application performance when disabled  
✅ **Production-ready** with proper error handling and fallbacks