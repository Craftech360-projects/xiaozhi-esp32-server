# OpenAI Realtime API Integration Setup

This guide explains how to integrate OpenAI's Realtime API with your Xiaozhi ESP32 server for low-latency speech-to-speech conversations.

## What is the Realtime API?

OpenAI's Realtime API enables natural speech-to-speech conversations with GPT-4o. It provides:
- **Low latency**: ~500ms response time
- **Natural interruptions**: Like ChatGPT's Advanced Voice Mode  
- **Direct audio streaming**: Bypasses traditional ASR->LLM->TTS pipeline
- **Function calling**: Voice-triggered actions

## Prerequisites

1. **OpenAI API Access**: Paid OpenAI account with Realtime API access
2. **Python dependencies**: websockets, scipy, numpy, opuslib-next (already in your system)

## Installation Steps

### 1. Install Dependencies

```bash
# Navigate to xiaozhi-server directory
cd main/xiaozhi-server

# Install Python dependencies (if missing)
pip install websockets scipy numpy

# Note: opuslib-next is already installed in your system
# The system will use existing audio encoding/decoding utilities
```

### 2. Configure the Realtime API

Add this configuration to your `config.yaml` or `data/.config.yaml`:

```yaml
# OpenAI Realtime API Configuration
openai_realtime:
  enabled: true
  api_key: "your-openai-api-key-here"
  model: "gpt-4o-realtime-preview"
  voice: "alloy"  # Options: alloy, echo, fable, onyx, nova, shimmer
  
  session:
    instructions: "You are a helpful AI assistant. Respond naturally and conversationally."
    temperature: 0.8
    max_response_output_tokens: 2048
    
    vad:
      threshold: 0.5
      prefix_padding_ms: 300
      silence_duration_ms: 500

# Optional: Fallback configuration
realtime_fallback:
  use_fallback: true
  fallback_asr: "openai"
  fallback_llm: "openai"
  fallback_tts: "edge"
```

### 3. Update Your Configuration

Replace `your-openai-api-key-here` with your actual OpenAI API key.

## How It Works

### Architecture Flow

1. **ESP32 Device** → Sends Opus audio (16kHz) via WebSocket
2. **Audio Converter** → Converts Opus to PCM16 and resamples to 24kHz  
3. **OpenAI Realtime API** → Processes audio and returns PCM16 response
4. **Audio Converter** → Converts back to Opus 16kHz for ESP32
5. **ESP32 Device** → Plays audio response

### Bypassed Components

When Realtime API is active, these traditional components are bypassed:
- VAD (Voice Activity Detection) 
- ASR (Speech Recognition)
- Traditional LLM processing
- TTS (Text-to-Speech)

## Configuration Options

### Voice Options
- `alloy`: Neutral, balanced voice
- `echo`: Clear, friendly voice  
- `fable`: Warm, expressive voice
- `onyx`: Deep, authoritative voice
- `nova`: Bright, energetic voice
- `shimmer`: Soft, gentle voice

### VAD Settings
- `threshold`: 0.0-1.0, higher = more sensitive to voice
- `prefix_padding_ms`: Audio captured before speech detection
- `silence_duration_ms`: Silence duration to end speech detection

## Usage

### Start the Server
```bash
cd main/xiaozhi-server
python app.py
```

The server will automatically:
1. Initialize Realtime API connection
2. Handle ESP32 WebSocket connections
3. Route audio through Realtime API when enabled
4. Fall back to traditional pipeline if needed

### Testing

1. **Check Logs**: Look for "Realtime handler initialized" messages
2. **Audio Test**: Speak to your ESP32 device
3. **Latency**: Should see ~500ms response time
4. **Fallback**: Traditional pipeline activates if Realtime API fails

## Pricing Considerations

OpenAI Realtime API pricing (as of 2024):
- **Audio Input**: ~$0.06/minute ($100 per 1M tokens)
- **Audio Output**: ~$0.24/minute ($200 per 1M tokens)
- **Text Input**: $5 per 1M tokens
- **Text Output**: $20 per 1M tokens

## Troubleshooting

### Common Issues

**1. Connection Fails**
```
Error: Failed to connect to OpenAI Realtime API
```
- Check API key is valid
- Ensure you have Realtime API access
- Verify internet connection

**2. Audio Conversion Errors**
```
Error: Missing audio utility: No module named 'opuslib_next'
```
- Install opuslib-next: `pip install opuslib-next`
- Verify scipy and numpy are installed
- Check existing audio utilities are working

**3. High Latency**
```
Response time > 1 second
```
- Check internet connection speed
- Try different voice models
- Verify server location (US recommended)

**4. Audio Quality Issues**
```
Distorted or choppy audio
```
- Check ESP32 audio quality
- Verify Opus encoding parameters
- Test with different bitrates

### Debug Mode

Enable debug logging in your config:

```yaml
log:
  log_level: DEBUG
```

This will show detailed audio processing and WebSocket communication logs.

## Advanced Configuration

### Custom Instructions
```yaml
openai_realtime:
  session:
    instructions: |
      You are a smart home assistant named Xiaozhi. You can:
      - Control smart home devices
      - Answer questions about weather, news, time
      - Play music and stories
      - Have natural conversations
      
      Always respond in a friendly, helpful manner. Keep responses concise.
```

### Function Calling
```yaml
openai_realtime:
  session:
    enable_functions: true
    tools:
      - type: "function"
        name: "get_weather"
        description: "Get current weather information"
```

### Multiple Voice Profiles
You can configure different voices for different devices or users by modifying the handler initialization.

## Performance Tips

1. **Use Dedicated Server**: Deploy on a server with good internet connectivity
2. **Monitor Usage**: Track API costs with OpenAI dashboard
3. **Optimize Audio**: Use appropriate bitrates and quality settings
4. **Fallback Strategy**: Always configure fallback providers
5. **Caching**: Consider caching common responses

## Integration with Existing Features

The Realtime API integrates with existing Xiaozhi features:
- **Device Management**: Works with existing device registration
- **User Authentication**: Respects existing auth settings  
- **Plugin System**: Can trigger function calls to plugins
- **Home Assistant**: Compatible with HA integrations
- **Multi-language**: Supports different languages based on configuration

## Next Steps

1. Test with your ESP32 device
2. Monitor performance and costs
3. Customize voice and behavior
4. Integrate with smart home functions
5. Optimize for your use case

For support, check the project issues or documentation.