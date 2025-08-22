# Gemini Real-time + Deepgram ASR Integration Guide

This guide explains how to integrate Google Gemini's real-time audio capabilities with Deepgram ASR in your Xiaozhi voice assistant system.

## 🎯 What This Integration Provides

This hybrid approach combines the best of both worlds:

### **🎤 Deepgram ASR (Speech-to-Text)**
- Industry-leading accuracy (Nova-2 model)
- 100+ languages supported
- Smart formatting and punctuation
- Fast processing (< 1 second)

### **🤖 Gemini Real-time (LLM + TTS)**
- Natural conversation flow
- Real-time audio generation
- Low-latency responses
- High-quality voice synthesis

### **🔄 Integration Benefits**
- **Best ASR accuracy** with Deepgram
- **Natural conversations** with Gemini
- **Real-time audio** responses
- **Seamless integration** with existing Xiaozhi architecture

## 📋 Prerequisites

1. **Deepgram Account**: Get API key from [console.deepgram.com](https://console.deepgram.com/)
2. **Google AI Account**: Get API key from [aistudio.google.com](https://aistudio.google.com/apikey)
3. **Python Dependencies**: Already added to requirements.txt

## 🚀 Quick Setup

### Step 1: Get API Keys

#### Deepgram API Key
1. Sign up at [Deepgram Console](https://console.deepgram.com/)
2. Get $200 in free credits
3. Create an API key and copy it

#### Gemini API Key
1. Go to [Google AI Studio](https://aistudio.google.com/apikey)
2. Create a new API key
3. Copy the key

### Step 2: Configure Integration

Edit `main/xiaozhi-server/config.yaml`:

```yaml
# Enable the integration
gemini_realtime_integration:
  enabled: true
  
  # Your Deepgram configuration
  deepgram_asr:
    api_key: your-actual-deepgram-api-key
    model: nova-2
    language: en  # or zh, es, fr, etc.
    smart_format: true
    punctuate: true
    
  # Your Gemini configuration  
  gemini_realtime:
    api_key: your-actual-gemini-api-key
    model: models/gemini-2.5-flash-preview-native-audio-dialog
    voice_name: Zephyr  # or Aria, Charon, Kore, Fenrir, Aoede
    enable_audio_output: true
```

### Step 3: Install Dependencies

```bash
cd main/xiaozhi-server
pip install -r requirements.txt
```

### Step 4: Test the Integration

```bash
cd main/xiaozhi-server
python test_gemini_integration.py
```

## 🔧 How It Works

### **Audio Processing Flow**

```
ESP32 Device → WebSocket → Xiaozhi Server
                              ↓
                    Audio Chunks Buffered
                              ↓
                    Deepgram ASR Processing
                              ↓
                    Text → Gemini Real-time
                              ↓
                    Audio Response Generated
                              ↓
                    ESP32 Device ← WebSocket
```

### **Key Components**

1. **GeminiRealtimeHandler**: Manages the hybrid processing
2. **GeminiConnectionHandler**: Extended WebSocket connection handler
3. **Deepgram ASR Provider**: High-accuracy speech recognition
4. **Gemini Real-time LLM**: Natural conversation and TTS

## ⚙️ Configuration Options

### **Audio Processing Settings**

```yaml
audio_settings:
  # Affects latency vs accuracy trade-off
  min_chunks_for_processing: 10  # ~600ms of audio
  max_buffer_chunks: 50          # ~3 seconds max
  voice_threshold: 100           # Voice detection threshold
  processing_timeout: 30         # Max processing time
```

### **Deepgram Options**

```yaml
deepgram_asr:
  model: nova-2        # Best accuracy
  language: en         # Language code
  smart_format: true   # Auto punctuation
  punctuate: true      # Add punctuation
  diarize: false       # Speaker identification
```

### **Gemini Voice Options**

```yaml
gemini_realtime:
  voice_name: Zephyr   # Available voices:
  # - Zephyr: Balanced, natural
  # - Aria: Warm, expressive  
  # - Charon: Deep, authoritative
  # - Kore: Clear, professional
  # - Fenrir: Dynamic, energetic
  # - Aoede: Melodic, gentle
```

## 🔌 Integration with Existing Server

### **Option 1: Replace Standard Connection Handler**

In your WebSocket server, use the new connection handler:

```python
from core.connection_gemini import GeminiConnectionHandler

# In your WebSocket handler
async def handle_connection(websocket, path):
    session_id = generate_session_id()
    
    # Use Gemini-enabled handler
    async with GeminiConnectionHandler(websocket, session_id, config) as handler:
        await handler.handle_messages()
```

### **Option 2: Conditional Integration**

Enable based on configuration:

```python
# Check if Gemini integration is enabled
if config.get("gemini_realtime_integration", {}).get("enabled", False):
    handler = GeminiConnectionHandler(websocket, session_id, config)
else:
    handler = ConnectionHandler(websocket, session_id, config)
```

## 📊 Performance Characteristics

### **Latency Breakdown**
- **Audio Buffering**: ~600ms (configurable)
- **Deepgram ASR**: ~500-1000ms
- **Gemini Processing**: ~200-500ms
- **Audio Generation**: ~100-300ms
- **Total Latency**: ~1.4-2.4 seconds

### **Accuracy**
- **ASR Accuracy**: 95%+ (Deepgram Nova-2)
- **Language Understanding**: Excellent (Gemini)
- **Voice Quality**: High (Gemini TTS)

## 🔍 Troubleshooting

### **Common Issues**

1. **"Failed to connect to Gemini"**
   - Check your Gemini API key
   - Ensure you have access to the audio model
   - Verify internet connectivity

2. **"Deepgram ASR failed"**
   - Verify Deepgram API key
   - Check audio format compatibility
   - Ensure sufficient credits

3. **"No audio responses"**
   - Check `enable_audio_output: true`
   - Verify WebSocket connection
   - Check audio format compatibility

4. **High latency**
   - Reduce `min_chunks_for_processing`
   - Check network connectivity
   - Monitor API response times

### **Debug Mode**

Enable detailed logging:

```python
import logging
logging.getLogger().setLevel(logging.DEBUG)
```

### **Testing Tools**

```bash
# Test configuration
python test_gemini_integration.py

# Test Deepgram only
python test_deepgram_asr.py

# Monitor logs
tail -f logs/server.log
```

## 💡 Best Practices

### **For Best Performance**
1. Use `nova-2` model for highest accuracy
2. Set appropriate buffer sizes for your use case
3. Monitor API usage and costs
4. Implement proper error handling

### **For Production**
1. Set up API key rotation
2. Implement rate limiting
3. Monitor latency metrics
4. Have fallback mechanisms

### **For Development**
1. Use smaller buffer sizes for faster iteration
2. Enable debug logging
3. Test with various audio qualities
4. Monitor memory usage

## 💰 Cost Considerations

### **Deepgram Pricing**
- Free tier: $200 credits (~45 hours)
- Pay-as-you-go: ~$0.0043/minute
- Volume discounts available

### **Gemini Pricing**
- Free tier: Generous limits
- Audio processing: Check current rates
- Real-time usage: Monitor carefully

## 🆚 Comparison with Standard Xiaozhi

| Feature | Standard Xiaozhi | Gemini Integration |
|---------|------------------|-------------------|
| ASR | Various providers | Deepgram (best accuracy) |
| LLM | Various providers | Gemini (real-time) |
| TTS | Various providers | Gemini (natural) |
| Latency | Variable | ~1.4-2.4 seconds |
| Audio Quality | Good | Excellent |
| Setup Complexity | Medium | Medium-High |

## 🎉 You're All Set!

Once configured, your Xiaozhi assistant will provide:

1. **🎤 Industry-leading ASR** with Deepgram
2. **🤖 Natural conversations** with Gemini
3. **🔊 High-quality TTS** responses
4. **⚡ Real-time processing** pipeline
5. **🔄 Seamless integration** with existing features

The hybrid approach gives you the best possible voice assistant experience! 🚀

## 🔗 Useful Links

- [Deepgram Console](https://console.deepgram.com/)
- [Google AI Studio](https://aistudio.google.com/)
- [Gemini Audio Models](https://ai.google.dev/gemini-api/docs/audio)
- [Deepgram Documentation](https://developers.deepgram.com/)

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section
2. Run the test scripts
3. Review the logs
4. Check API status pages