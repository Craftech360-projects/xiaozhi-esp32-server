# Chat History Implementation Plan

## Overview
Implement comprehensive chat history tracking for LiveKit agent conversations, capturing both user queries (voice transcripts) and LLM responses, then saving them to MySQL database via Manager API for agent-specific chat history.

## Architecture

```
ESP32 Device → MQTT Gateway → LiveKit Agent → Manager API → MySQL Database
                                     ↓
                              Chat History Service
                                     ↓
                              Event Capture System
```

## Implementation Steps

### 1. Create Chat History Service
**File**: `src/services/chat_history_service.py`

**Features**:
- Buffer messages for batch sending (every 5 messages or 30 seconds)
- Handle HTTP communication with Manager API endpoint
- Implement retry logic with exponential backoff
- Local JSON backup for reliability
- Async batch processing for performance

**Key Methods**:
- `add_message(chat_type, content, timestamp)` - Add message to buffer
- `flush_messages()` - Send all buffered messages to API
- `start_periodic_sending()` - Background task for periodic sends
- `cleanup()` - Final cleanup and backup on session end

### 2. Update Event Handlers
**File**: `src/handlers/chat_logger.py`

**Capture Points**:
- `user_input_transcribed` events - User speech-to-text results
- `speech_created` events - Agent LLM responses before TTS
- Extract text content, timestamps, and event metadata

**Integration**:
- Add chat history service instance to event handler
- Pass captured messages to service for processing
- Maintain existing data channel functionality

### 3. Integrate with Main Agent
**File**: `main.py`

**Initialization**:
- Create chat history service instance after MAC extraction
- Configure with Manager API URL, secret, device MAC, session ID
- Start background sending task
- Set service reference in event handlers

**Session Lifecycle**:
- Initialize service on session start
- Capture messages throughout conversation
- Clean flush and backup on session end

### 4. Create Database Helper
**File**: `src/utils/database_helper.py`

**Purpose**:
- Get agent_id from database using MAC address
- Make API calls to Manager API for agent lookup
- Handle authentication with server secret

### 5. API Integration

**Endpoint**: `POST /agent/chat-history/report`

**Payload Format**:
```json
{
    "macAddress": "68:25:dd:ba:39:78",
    "sessionId": "d3746a02-cfeb-417d-ad05-0c6d3095632d_6825ddba3978",
    "chatType": 1,  // 1=user, 2=agent
    "content": "Hello, how can I help you?",
    "audioBase64": null,  // Optional audio data
    "reportTime": 1758701973  // Unix timestamp
}
```

**Authentication**: Bearer token using Manager API secret

## Database Schema (Existing)

**Table**: `ai_agent_chat_history`
```sql
CREATE TABLE ai_agent_chat_history (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    mac_address VARCHAR(17) NOT NULL,
    agent_id VARCHAR(255),
    session_id VARCHAR(255) NOT NULL,
    chat_type TINYINT NOT NULL,  -- 1=user, 2=agent
    content TEXT NOT NULL,
    audio_id VARCHAR(255),       -- Future: audio reference
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

## Data Flow

1. **User speaks** → ESP32 → MQTT Gateway → LiveKit Agent
2. **STT processes** → `user_input_transcribed` event fired
3. **Event handler captures** → Chat History Service buffers message
4. **Agent responds** → LLM generates response → `speech_created` event fired
5. **Event handler captures** → Chat History Service buffers response
6. **Periodic/Batch sending** → Manager API → MySQL Database
7. **Session ends** → Final flush → Local backup saved

## Key Features

### Real-time Capture
- Event-driven message capture as conversation happens
- Immediate buffering prevents data loss
- Background sending doesn't block main agent

### Reliability
- Buffered messages with retry logic
- Local JSON backups for debugging/recovery
- Graceful error handling - failures don't affect agent

### Performance
- Batch sending reduces API calls
- Async processing maintains responsiveness
- Configurable send intervals and batch sizes

### Agent Association
- Links conversations to specific agents via MAC address
- Session-based organization with UUIDs
- Maintains conversation context and history

## Configuration

**Manager API Settings** (from `config.yaml`):
```yaml
manager_api:
  url: "http://192.168.1.101:8002/toy"
  secret: "a3c1734a-1efe-4ab7-8f43-98f88b874e4b"
  timeout: 5
```

**Chat History Settings** (configurable):
```python
BATCH_SIZE = 5          # Send after 5 messages
SEND_INTERVAL = 30      # Send every 30 seconds
RETRY_ATTEMPTS = 3      # Retry failed requests 3 times
BACKUP_ENABLED = True   # Save local JSON backups
```

## Error Handling

### API Failures
- Retry with exponential backoff
- Re-add failed messages to buffer
- Log errors without breaking agent flow

### Network Issues
- Buffer messages until connectivity restored
- Local backup ensures no data loss
- Graceful degradation

### Data Validation
- Validate message content before sending
- Skip empty or invalid messages
- Sanitize content for database storage

## Monitoring & Logging

### Log Levels
- `DEBUG`: Message buffering, API calls
- `INFO`: Batch sends, service lifecycle
- `WARN`: Retry attempts, validation issues
- `ERROR`: Critical failures, data loss

### Metrics
- Messages captured per session
- API success/failure rates
- Buffer size and send frequency
- Session conversation length

## Testing Strategy

### Unit Tests
- Chat History Service methods
- Message buffering and batching
- API communication and retries
- Local backup functionality

### Integration Tests
- End-to-end conversation capture
- Manager API integration
- Database persistence verification
- Error recovery scenarios

### Load Testing
- Multiple concurrent sessions
- High message volume handling
- Network failure simulation
- Memory usage optimization

## Future Enhancements

### Audio Support
- Capture and store audio data (Base64 encoded)
- Link audio to text transcripts
- Compression and storage optimization

### Analytics
- Conversation sentiment analysis
- Topic extraction and categorization
- User behavior patterns
- Agent performance metrics

### Real-time Dashboard
- Live conversation monitoring
- Agent activity visualization
- Error rate dashboards
- Performance metrics

### Export Features
- Conversation history export
- Multiple format support (JSON, CSV, PDF)
- Date range filtering
- Agent-specific exports

This implementation provides a robust, scalable foundation for capturing and storing all agent conversations while maintaining system performance and reliability.