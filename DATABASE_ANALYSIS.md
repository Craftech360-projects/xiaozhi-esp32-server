# Database Analysis for Xiaozhi AI Toy Server

## Executive Summary
This document provides a comprehensive analysis of the database schema and configuration for the Xiaozhi ESP32 AI Toy server. The system uses MySQL with MyBatis-Plus ORM and Liquibase for database migrations.

## 1. Database Infrastructure

### Technology Stack
- **Database Type**: MySQL 8.0+
- **ORM Framework**: MyBatis-Plus 3.5.5
- **Migration Tool**: Liquibase 4.20.0
- **Connection Pool**: Druid (Alibaba)
- **Cache Layer**: Redis
- **Current Connection**: Railway cloud MySQL instance (remote database)

### Connection Configuration
- **Host**: turntable.proxy.rlwy.net:38288
- **Database**: railway
- **Character Set**: UTF-8
- **Timezone**: Asia/Shanghai

## 2. Database Schema Overview

### 2.1 System Management Tables

#### sys_user
- **Purpose**: User authentication and management
- **Key Fields**: id, username, password, super_admin, status
- **Security**: BCrypt password encryption

#### sys_user_token
- **Purpose**: Authentication token management
- **Key Fields**: id, user_id, token, expire_date
- **Indexes**: Unique on user_id and token

#### sys_params
- **Purpose**: System configuration parameters
- **Key Fields**: id, param_code, param_value, param_type
- **Usage**: Stores server URLs, API keys, feature flags

#### sys_dict_type / sys_dict_data
- **Purpose**: Data dictionary management
- **Key Fields**: dict_type, dict_name, dict_label, dict_value
- **Usage**: Manages dropdown options and system constants

### 2.2 AI Configuration Tables

#### ai_model_provider
- **Purpose**: Defines available AI model providers
- **Model Types**: 
  - ASR (Automatic Speech Recognition)
  - TTS (Text-to-Speech)
  - LLM (Large Language Models)
  - VAD (Voice Activity Detection)
  - Memory (Context management)
  - Intent (Intent recognition)
  - Plugin (External integrations)
- **Key Fields**: id, model_type, provider_code, name, fields (JSON)

#### ai_model_config
- **Purpose**: Specific model configurations
- **Key Fields**: id, model_type, model_code, is_default, is_enabled, config_json
- **Features**: Supports multiple configurations per model type

#### ai_tts_voice
- **Purpose**: TTS voice configurations
- **Key Fields**: id, tts_model_id, name, tts_voice, languages, voice_demo
- **Usage**: Maps voice options to TTS models

#### ai_agent_template
- **Purpose**: Pre-defined agent personalities and configurations
- **Key Fields**: agent_code, agent_name, system_prompt, language
- **Examples**: 湾湾小何, 星际游子, 英语老师, 好奇男孩, 汪汪队长

#### ai_agent
- **Purpose**: User-specific agent configurations
- **Key Fields**: 
  - Identity: id, user_id, agent_code, agent_name
  - Models: asr_model_id, vad_model_id, llm_model_id, tts_model_id, tts_voice_id
  - Settings: system_prompt, summary_memory, language
  - Features: chat_history_conf (0=none, 1=text only, 2=text+audio)

### 2.3 Device Management Tables

#### ai_device
- **Purpose**: IoT device registry and management
- **Key Fields**: 
  - Identity: id, mac_address, user_id
  - Configuration: agent_id, board, alias
  - Status: last_connected_at, app_version
  - Features: auto_update
- **Indexes**: On mac_address for quick device lookup

#### ai_ota
- **Purpose**: Firmware OTA update management
- **Key Fields**: id, firmware_name, type, version, size, firmware_path
- **Usage**: Manages firmware versions and update distribution

### 2.4 Chat History Tables

#### ai_agent_chat_history
- **Purpose**: Chat conversation records
- **Key Fields**: 
  - Identity: id, mac_address, agent_id, session_id
  - Content: chat_type (1=user, 2=agent), content, audio_id
  - Timestamps: created_at, updated_at
- **Indexes**: Multiple indexes for performance (mac, session, agent)

#### ai_agent_chat_audio
- **Purpose**: Audio data storage
- **Key Fields**: id, audio (LONGBLOB)
- **Storage**: Binary audio data in OPUS format

#### ai_voiceprint
- **Purpose**: Voice recognition profiles
- **Key Fields**: id, user_id, agent_id, embedding (voice features), memory
- **Usage**: Stores voice characteristics for speaker identification

### 2.5 Plugin System Tables

#### ai_agent_plugin_mapping
- **Purpose**: Agent-to-plugin associations
- **Key Fields**: agent_id, plugin_id, param_info (JSON)
- **Unique Constraint**: (agent_id, plugin_id)
- **Supported Plugins**:
  - Weather query
  - Music playback
  - News aggregation (ChinaNews, NewsNow)
  - HomeAssistant integration

## 3. Database Relationships

### Primary Relationships
```
Users (sys_user)
  ├── Agents (ai_agent) [1:N]
  ├── Devices (ai_device) [1:N]
  └── Tokens (sys_user_token) [1:1]

Agents (ai_agent)
  ├── Devices (ai_device) [1:N]
  ├── Chat History (ai_agent_chat_history) [1:N]
  ├── Plugins (ai_agent_plugin_mapping) [1:N]
  └── Model Configs (references to ai_model_config)

Chat History (ai_agent_chat_history)
  └── Audio Data (ai_agent_chat_audio) [1:1]
```

## 4. Data Access Patterns

### ORM Implementation
- **Base Framework**: MyBatis-Plus with BaseMapper
- **Entity Mapping**: JPA annotations with Lombok
- **Automatic Fields**: create_date, update_date, creator, updater
- **ID Generation**: UUID for most tables, AUTO_INCREMENT for chat history

### Performance Optimizations
- **Connection Pooling**: Druid with configurable pool sizes
- **Caching**: Redis integration for frequently accessed data
- **Indexing Strategy**: 
  - Unique indexes on identifiers
  - Composite indexes for query optimization
  - Time-based indexes for historical queries

## 5. Security Features

### Authentication & Authorization
- **Password Storage**: BCrypt encryption
- **Token Management**: Unique tokens with expiration
- **Role System**: super_admin flag for privileged access
- **Session Management**: Token-based stateless authentication

### Data Protection
- **SQL Injection Prevention**: Parameterized queries via MyBatis
- **XSS Protection**: Configurable XSS filter
- **Sensitive Data**: API keys and secrets stored in sys_params

## 6. Migration Strategy

### Liquibase Configuration
- **Master File**: db.changelog-master.yaml
- **Migration Pattern**: Timestamp-based (YYYYMMDDHHMM.sql)
- **Execution**: Automatic on application startup
- **Rollback Support**: Each changeset is reversible

### Migration History (Key Milestones)
1. **202503141335**: Initial schema creation
2. **202503141346**: AI model and agent tables
3. **202504251422**: OTA support added
4. **202505022134**: Chat history restructuring
5. **202505292203**: Plugin system implementation

## 7. Configuration Requirements

### For Your AI Toy Implementation

#### Step 1: Database Setup
```yaml
# Update application.yml
spring:
  datasource:
    url: jdbc:mysql://your-host:3306/your-db
    username: your-username
    password: your-password
```

#### Step 2: Essential Tables to Configure
1. **ai_model_config**: Configure your AI models
   - ASR model for speech recognition
   - TTS model for speech synthesis
   - LLM model for conversation

2. **ai_agent_template**: Define agent personalities
   - Create custom personalities for your toy
   - Set appropriate system prompts

3. **ai_device**: Register ESP32 devices
   - Use MAC address as unique identifier
   - Link to appropriate agent configuration

4. **sys_params**: System parameters
   - server.websocket: WebSocket server URLs
   - server.mqtt_gateway: MQTT configuration
   - server.ota: OTA update server

#### Step 3: Data Initialization
```sql
-- Example: Register a device
INSERT INTO ai_device (id, mac_address, user_id, agent_id, board)
VALUES (UUID(), 'AA:BB:CC:DD:EE:FF', 1, 'agent-id', 'esp32');

-- Example: Configure a model
INSERT INTO ai_model_config (id, model_type, model_code, is_enabled)
VALUES ('MY_ASR', 'ASR', 'fun_local', 1);
```

## 8. Scaling Considerations

### Current Limitations
- **Audio Storage**: LONGBLOB in database (not scalable)
- **Chat History**: Can grow large over time
- **Single Database**: No sharding or read replicas

### Recommended Improvements
1. **File Storage**: Move audio files to object storage (S3/MinIO)
2. **Data Archival**: Archive old chat history
3. **Read Replicas**: Add read replicas for scaling
4. **Partitioning**: Partition chat_history by date

## 9. Monitoring & Maintenance

### Key Metrics to Monitor
- Connection pool usage
- Query performance (slow query log)
- Table sizes (especially chat_history and audio)
- Index effectiveness

### Regular Maintenance Tasks
1. Analyze and optimize tables monthly
2. Clean up expired tokens
3. Archive old chat history
4. Monitor and optimize slow queries

## 10. Integration Points

### External Systems
- **MQTT Gateway**: Device communication
- **WebSocket Server**: Real-time updates
- **Redis Cache**: Performance optimization
- **OTA Server**: Firmware updates

### API Endpoints (via manager-api)
- User management
- Device registration and management
- Agent configuration
- Chat history retrieval
- Model configuration

## Conclusion

The Xiaozhi database schema is well-structured for an AI toy platform, supporting multi-tenant usage, flexible AI model configuration, and comprehensive device management. The use of Liquibase ensures maintainable schema evolution, while MyBatis-Plus provides efficient data access patterns.

For your AI toy implementation, focus on:
1. Setting up the database connection
2. Configuring the AI models you'll use
3. Registering your ESP32 devices
4. Creating appropriate agent personalities
5. Implementing proper authentication for users

The system is designed to be extensible, allowing you to add custom plugins and integrate with external services as needed.