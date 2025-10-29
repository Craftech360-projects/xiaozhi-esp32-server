# LiveKit Error Handling Implementation

## Overview

This implementation provides comprehensive error handling for LiveKit agents with proper recovery mechanisms for LLM, STT, and TTS components. It follows LiveKit best practices and provides graceful degradation when services fail.

## Files

### Core Implementation
- `error_handler.py` - Main error handling module with reusable components
- `error_callback.py` - Example standalone agent with error handling
- `test_error_handling.py` - Comprehensive test suite
- `create_error_audio.py` - Utility to create fallback audio files

### Integration
- `main.py` - Updated to use the error handling system
- `filtered_agent.py` - Updated with proper empty response handling

## Features

### 🛡️ **Comprehensive Error Recovery**
- **LLM Errors**: API failures, rate limits, invalid keys
- **TTS Errors**: Voice synthesis failures, service outages
- **STT Errors**: Speech recognition failures, connection issues

### 🔄 **Smart Retry Logic**
- Configurable retry limits per error type
- Automatic error count tracking
- Success-based error count reset

### 💬 **User-Friendly Fallbacks**
- Context-appropriate error messages
- Custom audio file support for TTS failures
- Graceful conversation continuation

### 📊 **Error Monitoring**
- Detailed error logging with emojis
- Error statistics tracking
- Session-end error reporting

## Usage

### Basic Integration

```python
from src.agent.error_handler import setup_error_handling

# Set up your LiveKit session
session = AgentSession(llm=llm, stt=stt, tts=tts, vad=vad)

# Add comprehensive error handling
error_manager = setup_error_handling(
    session=session,
    max_retries=3,
    custom_audio_path="path/to/error_audio.ogg"  # Optional
)

# Start your session
await session.start(agent=agent, room=room)

# Get error statistics at the end
error_stats = error_manager.get_error_stats()
print(f"Session errors: {error_stats}")
```

### Advanced Configuration

```python
# Custom error recovery manager
error_manager = ErrorRecoveryManager(
    max_retries=5,
    custom_audio_path="/path/to/custom/error.ogg"
)

# Custom fallback messages
error_manager.fallback_messages["llm"] = [
    "Custom LLM error message 1",
    "Custom LLM error message 2"
]
```

## Error Types & Recovery Strategies

### 🧠 **LLM Errors**
- **Detection**: OpenAI, Anthropic, Groq API failures
- **Recovery**: Mark as recoverable, provide fallback message
- **Examples**: Invalid API key, rate limits, model unavailable

### 🎤 **TTS Errors** 
- **Detection**: Cartesia, ElevenLabs, Azure TTS failures
- **Recovery**: Use custom audio file or mark as recoverable
- **Examples**: Voice synthesis failure, service outage

### 👂 **STT Errors**
- **Detection**: Deepgram, Whisper, Azure STT failures  
- **Recovery**: Reset agent session, reinitialize STT stream
- **Examples**: Connection failure, audio processing error

## Error Flow

```
Error Occurs
     ↓
Check if already recoverable
     ↓
Determine error type (LLM/TTS/STT)
     ↓
Check retry count vs max_retries
     ↓
If under limit:
  - Apply recovery strategy
  - Mark as recoverable
  - Provide user feedback
     ↓
If over limit:
  - Provide final error message
  - Let session close gracefully
```

## Success Events

The system automatically resets error counts when components work successfully:

- **LLM Success**: `function_calls_finished` event
- **TTS Success**: `agent_speech_committed` event  
- **STT Success**: `user_speech_committed` event

## Testing

Run the comprehensive test suite:

```bash
cd main/livekit-server
python -m src.agent.test_error_handling
```

Tests cover:
- Error type detection
- Retry logic
- Recovery strategies
- Success event handling
- Max retry scenarios

## Configuration Options

### Environment Variables
- `LIVEKIT_URL` - LiveKit server URL
- `LIVEKIT_API_KEY` - LiveKit API key
- `LIVEKIT_API_SECRET` - LiveKit API secret
- `OPENAI_API_KEY` - OpenAI API key
- `GROQ_API_KEY` - Groq API key
- `DEEPGRAM_API_KEY` - Deepgram API key
- `CARTESIA_API_KEY` - Cartesia API key

### Error Handler Settings
- `max_retries` - Maximum retry attempts per error type (default: 3)
- `custom_audio_path` - Path to fallback audio file
- `fallback_messages` - Custom error messages per type

## Best Practices

### ✅ **Do**
- Use `session.say()` for reliable message delivery
- Mark appropriate errors as recoverable
- Provide context-specific error messages
- Log errors with sufficient detail
- Test error scenarios regularly

### ❌ **Don't**
- Block the main thread during error handling
- Retry indefinitely without limits
- Expose technical error details to users
- Ignore error statistics
- Skip testing error scenarios

## Monitoring & Debugging

### Error Logs
```
🚨 LLM Error: Invalid API key
🔍 Error source: OpenAI
🔄 Recoverable: False
🔄 Error count for llm: 1/3
🔄 Attempting LLM error recovery...
✅ LLM fallback message delivered
```

### Session Statistics
```
📊 Session error statistics: {'llm': 2, 'tts': 0, 'stt': 1}
⚠️ Total errors encountered: 3
```

## Integration with Existing Code

The error handling system integrates seamlessly with existing LiveKit agents:

1. **Import the handler**: `from src.agent.error_handler import setup_error_handling`
2. **Set up after session creation**: `error_manager = setup_error_handling(session)`
3. **Optional: Log statistics on cleanup**: `error_stats = error_manager.get_error_stats()`

No changes to existing agent logic are required - the error handling works at the session level.

## Production Considerations

### Performance
- Error handling adds minimal overhead
- Fallback messages are delivered asynchronously
- Error counting is O(1) operation

### Reliability
- Graceful degradation when services fail
- Conversation continuity maintained
- User experience preserved during errors

### Monitoring
- Comprehensive error logging
- Error statistics for analysis
- Integration with existing logging systems

## Future Enhancements

- [ ] Error rate limiting per time window
- [ ] Custom error handlers per error type
- [ ] Integration with external monitoring systems
- [ ] Automatic service health checks
- [ ] Dynamic retry strategy adjustment

---

This error handling system provides production-ready reliability for LiveKit voice agents while maintaining excellent user experience during service disruptions.