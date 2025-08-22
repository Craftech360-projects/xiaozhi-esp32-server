# 🚀 Gemini Real-time Quick Start Guide

Complete setup for the real-time audio pipeline: **ESP32 → Deepgram ASR → Gemini LLM+TTS → ESP32**

## ✅ **What's Already Configured**

Your system is now configured for the complete real-time pipeline:

- ✅ **Deepgram ASR**: High-accuracy speech recognition
- ✅ **Gemini LLM**: Advanced conversation processing  
- ✅ **Gemini TTS**: Natural voice synthesis
- ✅ **Real-time streaming**: Low-latency audio pipeline
- ✅ **API Keys**: Both Deepgram and Gemini keys are set

## 🎯 **Audio Pipeline Flow**

```
ESP32 Device → WebSocket → Deepgram ASR → Gemini LLM → Gemini TTS → WebSocket → ESP32 Device
```

**Benefits:**
- **Single API call** to Gemini handles both LLM and TTS
- **Streaming audio** responses for natural conversation
- **Lower latency** than separate LLM + TTS calls
- **Consistent voice** throughout the conversation

## 🚀 **How to Start**

### **Step 1: Start the Gemini Real-time Server**

```bash
cd main/xiaozhi-server
python app_gemini_realtime.py
```

You should see:
```
🚀 Gemini Real-time Server started successfully!
📡 WebSocket endpoint: ws://0.0.0.0:8000/xiaozhi/v1/
🎤 Audio pipeline: ESP32 → Deepgram ASR → Gemini LLM+TTS → ESP32
```

### **Step 2: Test the Pipeline**

```bash
# In another terminal
python test_full_pipeline.py
```

This will test:
- ✅ WebSocket connection
- ✅ Text message → Gemini response
- ✅ Audio input → Complete pipeline

### **Step 3: Connect Your ESP32**

Update your ESP32 firmware to connect to:
```
ws://your-server-ip:8000/xiaozhi/v1/
```

## 🔧 **Configuration Summary**

### **Your Current Settings:**

```yaml
# Main module selection
selected_module:
  ASR: DeepgramASR           # Uses Deepgram for speech recognition
  LLM: GeminiRealtimeLLM     # Uses Gemini for LLM + TTS
  TTS: elevenlabs            # Fallback TTS (not used in real-time mode)

# Real-time integration
gemini_realtime_integration:
  enabled: true              # Real-time pipeline active
  
# API Keys (already set)
deepgram_asr:
  api_key: 2bc99f78...       # Your Deepgram key
gemini_realtime:
  api_key: AIzaSyCl9yu...    # Your Gemini key
```

### **Audio Processing Settings:**
- **Processing delay**: ~480ms (8 chunks)
- **Max buffer**: ~2.4 seconds (40 chunks)  
- **Voice**: Zephyr (child-friendly)
- **Language**: English (India)

## 🎮 **How It Works**

### **1. ESP32 Sends Audio**
- ESP32 captures audio in 60ms chunks
- Sends via WebSocket as binary data
- Server buffers chunks until voice detected

### **2. Deepgram Processing**
- Accumulated audio sent to Deepgram ASR
- Returns accurate transcript with punctuation
- Processing time: ~500-1000ms

### **3. Gemini Real-time Processing**
- Transcript sent to Gemini Live API
- Gemini processes with conversation context
- Generates both text response AND audio
- Streams audio back in real-time

### **4. ESP32 Receives Audio**
- Server streams Gemini audio to ESP32
- ESP32 plays audio immediately
- Natural conversation flow maintained

## 🔍 **Troubleshooting**

### **Server Won't Start**
```bash
# Check API keys
python test_gemini_integration.py

# Check configuration
grep -A 5 "gemini_realtime_integration" data/.config.yaml
```

### **No Audio Response**
1. Check Gemini API key is valid
2. Verify `enable_audio_output: true`
3. Check WebSocket connection
4. Monitor server logs

### **High Latency**
1. Reduce `min_chunks_for_processing` (currently 8)
2. Check network connectivity
3. Monitor Deepgram response times

### **Audio Quality Issues**
1. Verify ESP32 audio format (16kHz, mono)
2. Check WebSocket binary message handling
3. Test with different Gemini voices

## 📊 **Performance Expectations**

### **Latency Breakdown:**
- **Audio buffering**: ~480ms (8 chunks × 60ms)
- **Deepgram ASR**: ~500-1000ms
- **Gemini processing**: ~200-800ms  
- **Audio streaming**: ~100-300ms
- **Total latency**: ~1.3-2.6 seconds

### **Quality Metrics:**
- **ASR accuracy**: 95%+ (Deepgram Nova-3)
- **Voice quality**: High (Gemini TTS)
- **Conversation flow**: Natural (Gemini LLM)

## 🎯 **Optimizations for Cheeko**

Your configuration is optimized for child interactions:

### **Faster Response:**
- Reduced processing chunks (8 vs 10)
- Shorter timeouts (25s vs 30s)
- Child-friendly voice (Zephyr)

### **Better Conversations:**
- Gemini's advanced language understanding
- Consistent personality throughout conversation
- Natural voice inflection and emotion

### **Maintained Features:**
- All your existing functions (weather, news, music)
- Indian English language support
- Cheeko's personality prompt

## 🔄 **Switching Between Modes**

### **Real-time Mode (Current):**
```yaml
gemini_realtime_integration:
  enabled: true
```
- Uses: `app_gemini_realtime.py`
- Pipeline: ESP32 → Deepgram → Gemini LLM+TTS → ESP32

### **Standard Mode (Fallback):**
```yaml
gemini_realtime_integration:
  enabled: false
```
- Uses: `app.py` (standard server)
- Pipeline: ESP32 → Deepgram → Groq → ElevenLabs → ESP32

## 🎉 **You're Ready!**

Your Xiaozhi system now has:

1. **🎤 Best-in-class ASR** with Deepgram
2. **🤖 Advanced conversations** with Gemini
3. **🔊 Natural voice synthesis** with Gemini TTS
4. **⚡ Real-time streaming** for natural flow
5. **👶 Child-optimized** settings for Cheeko

The complete real-time pipeline is active and ready for your ESP32 device! 🚀

## 📞 **Support**

If you encounter issues:
1. Check the server logs for detailed error messages
2. Run `test_full_pipeline.py` to validate the setup
3. Verify API keys and network connectivity
4. Monitor the real-time audio streaming