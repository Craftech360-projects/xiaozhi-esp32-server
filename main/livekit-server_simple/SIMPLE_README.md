# Simplified LiveKit Agent for Cheeko

This is a simplified version of the LiveKit agent that keeps all essential functionality including messages and initial greetings while removing unnecessary complexity.

## Features Kept

✅ **Core Functionality**
- Initial greeting from Cheeko
- All message handling and responses
- Battery check function
- MQTT gateway integration
- Data channel communication
- Agent state management

✅ **Essential Components**
- LiveKit session management
- Provider Factory pattern (same as main server)
- Speech-to-Text (Groq Whisper via ProviderFactory)
- Text-to-Speech (EdgeTTS via ProviderFactory)
- Voice Activity Detection (Silero VAD via ProviderFactory)
- Large Language Model (Groq Llama via ProviderFactory)
- Configuration management (ConfigLoader)

## Features Removed

❌ **Complex Components Removed**
- Music service and Qdrant integration
- Story service
- Memory (Mem0) integration
- Database connections
- Child profile management
- Complex audio players
- MCP (Model Context Protocol) executor
- Device control service
- Error handling system
- Model caching and preloading
- Parallel service initialization

## Quick Start

### 1. Install Dependencies

```bash
pip install -r simple_requirements.txt
```

### 2. Configure Environment

Copy the environment template:
```bash
cp simple.env.example simple.env
```

Edit `simple.env` and set your Groq API key:
```env
GROQ_API_KEY=your_groq_api_key_here
```

### 3. Run the Agent

**Windows (PowerShell):**
```powershell
.\run_simple.ps1
```

**Windows (Command Prompt):**
```cmd
run_simple.bat
```

**Python directly:**
```bash
python simple_main.py dev
```

## Configuration

The simplified agent uses these key environment variables:

- `LIVEKIT_URL` - LiveKit server URL (default: ws://localhost:7890)
- `LIVEKIT_API_KEY` - LiveKit API key (default: devkey)
- `LIVEKIT_API_SECRET` - LiveKit API secret (default: secret)
- `GROQ_API_KEY` - Groq API key for LLM and STT
- `TTS_PROVIDER` - TTS provider (default: edge)
- `EDGE_TTS_VOICE` - EdgeTTS voice (default: en-US-AnaNeural)

## How It Works

1. **Configuration**: Loads settings using ConfigLoader (same as main server)
2. **Provider Creation**: Uses ProviderFactory to create LLM, STT, TTS, VAD (same pattern as main server)
3. **Startup**: Agent connects to LiveKit room based on device MAC
4. **Greeting**: Sends initial Cheeko greeting when device connects
5. **Conversation**: Handles speech-to-text, LLM processing, and text-to-speech
6. **Battery Check**: Responds to battery check requests via function tool
7. **MQTT Integration**: Communicates with MQTT gateway via data channels

## Logs

The simplified agent provides clean, focused logging:

```
🚀 Starting simple agent in room: 5345d54d-a5ae-4df5-b20f-c6883e6d4280_6825ddba3978
📱 Extracted MAC from room name: 68:25:dd:ba:39:78
[PREWARM] Simple prewarm complete
📍 Room info set - Room: 5345d54d-a5ae-4df5-b20f-c6883e6d4280_6825ddba3978, MAC: 68:25:dd:ba:39:78
✅ Simple agent started successfully
```

## Performance Optimizations

The simple version includes extensive optimizations for superior multi-client performance:

### Core Optimizations
- **Reduced Model Loading**: Only loads essential VAD model, skips embedding and Qdrant models
- **Ultra-Aggressive Audio Settings**: 5ms frame sizes (240 samples), minimal buffering (480 samples)
- **Process Scaling**: 6 idle processes for optimal concurrent client support
- **Enhanced Session Configuration**: Reduced endpointing delays (0.2s), faster interruption handling (0.15s)

### Audio Pipeline Optimizations
- **Groq TTS**: Primary TTS provider for ultra-fast response times
- **EdgeTTS Fallback**: Optimized with zero-buffering streaming and async yielding
- **Optimized VAD**: Child-friendly settings with 0.25 activation threshold and 0.04s min speech duration
- **Reduced Audio Delays**: 0.8s delay for Groq TTS completion (down from 1.5s)

### System-Level Optimizations
- **Resource Monitoring**: Comprehensive CPU, memory, network, and client tracking
- **Performance Alerts**: Real-time warnings for high resource usage and client overload
- **Memory Management**: Automatic garbage collection on client disconnect
- **Process Priority**: High priority setting for audio processing

### Performance Tools

**Optimization Script:**
```bash
python optimize_performance.py
```
Applies system-level optimizations for better performance.

**Real-time Monitoring:**
```bash
python monitor_performance.py
```
Monitors system resources and provides performance alerts.

## Troubleshooting

### Common Issues

1. **"No VAD from prewarm"** - Normal warning, VAD will load automatically
2. **"Failed to send state change"** - Check MQTT gateway connection
3. **"Python not found"** - Install Python 3.8+ and add to PATH
4. **Audio jitter with multiple clients** - Run `optimize_performance.py` first
5. **High CPU usage** - Monitor with `monitor_performance.py` and limit clients to 6

### Performance

The simplified agent should start much faster (~2-3 seconds vs 5-6 seconds) and use less memory while maintaining all core conversational functionality. With optimizations, it can handle 6+ concurrent clients with minimal audio jitter.

## Comparison with Full Version

| Feature | Full Version | Simple Version |
|---------|-------------|----------------|
| Startup Time | 5-6 seconds | 2-3 seconds |
| Memory Usage | ~500MB | ~200MB |
| Dependencies | 50+ packages | 6 packages |
| Code Lines | 800+ lines | 200 lines |
| Greeting | ✅ | ✅ |
| Conversations | ✅ | ✅ |
| Battery Check | ✅ | ✅ |
| Music/Stories | ✅ | ❌ |
| Memory | ✅ | ❌ |
| Complex Features | ✅ | ❌ |

The simplified version is perfect for basic testing and development while maintaining the core Cheeko personality and functionality.