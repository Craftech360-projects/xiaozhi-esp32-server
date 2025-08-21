# Xiaozhi ESP32 Server - Database Visual Schema

## 🎨 ASCII Art Database Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    XIAOZHI ESP32 SERVER DATABASE SCHEMA                                        │
│                                         16 Tables - 6 Categories                                               │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                        🔐 SYSTEM MANAGEMENT LAYER                                              │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────┘

    ┌─────────────────────┐         ┌─────────────────────┐         ┌─────────────────────┐
    │     sys_user        │◄────────┤   sys_user_token    │         │    sys_params       │
    │ ─────────────────── │  1:1    │ ─────────────────── │         │ ─────────────────── │
    │ 🔑 id (PK)          │         │ 🔑 id (PK)          │         │ 🔑 id (PK)          │
    │ 🔒 username (UK)    │         │ 🔗 user_id (FK)     │         │ 🔒 param_code (UK)  │
    │    password         │         │ 🔒 token (UK)       │         │    param_value      │
    │    super_admin      │         │    expire_date      │         │    param_type       │
    │    status           │         │    create_date      │         │    remark           │
    │    create_date      │         │    update_date      │         │    creator          │
    │    creator          │         └─────────────────────┘         │    create_date      │
    │    updater          │                                         │    updater          │
    │    update_date      │                                         │    update_date      │
    └─────────────────────┘                                         └─────────────────────┘
            │                                                               
            │ 1:M                                                           
            ▼                                                               
    ┌─────────────────────┐         ┌─────────────────────┐                 
    │   sys_dict_type     │◄────────┤   sys_dict_data     │                 
    │ ─────────────────── │  1:M    │ ─────────────────── │                 
    │ 🔑 id (PK)          │         │ 🔑 id (PK)          │                 
    │ 🔒 dict_type (UK)   │         │ 🔗 dict_type_id(FK) │                 
    │    dict_name        │         │    dict_label       │                 
    │    remark           │         │    dict_value       │                 
    │    sort             │         │    remark           │                 
    │    creator          │         │    sort             │                 
    │    create_date      │         │    creator          │                 
    │    updater          │         │    create_date      │                 
    │    update_date      │         │    updater          │                 
    └─────────────────────┘         │    update_date      │                 
                                    └─────────────────────┘                 

┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                      🤖 AI MODEL CONFIGURATION LAYER                                           │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────┘

    ┌─────────────────────┐         ┌─────────────────────┐         ┌─────────────────────┐
    │ ai_model_provider   │         │  ai_model_config    │◄────────┤   ai_tts_voice      │
    │ ─────────────────── │         │ ─────────────────── │  1:M    │ ─────────────────── │
    │ 🔑 id (PK)          │         │ 🔑 id (PK)          │         │ 🔑 id (PK)          │
    │    model_type       │         │    model_type       │         │ 🔗 tts_model_id(FK) │
    │    provider_code    │         │    model_code       │         │    name             │
    │    name             │         │    model_name       │         │    tts_voice        │
    │    fields (JSON)    │         │    is_default       │         │    languages        │
    │    sort             │         │    is_enabled       │         │    voice_demo       │
    │    creator          │         │    config_json      │         │    remark           │
    │    create_date      │         │    doc_link         │         │    sort             │
    │    updater          │         │    remark           │         │    creator          │
    │    update_date      │         │    sort             │         │    create_date      │
    └─────────────────────┘         │    creator          │         │    updater          │
                                    │    create_date      │         │    update_date      │
                                    │    updater          │         └─────────────────────┘
                                    │    update_date      │                 
                                    └─────────────────────┘                 
                                            │                               
                                            │ M:M (via agent configs)       
                                            ▼                               

┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                        🧠 AI AGENT MANAGEMENT LAYER                                            │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────┘

    ┌─────────────────────┐         ┌─────────────────────┐
    │ ai_agent_template   │────────►│     ai_agent        │◄─────────┐
    │ ─────────────────── │ template│ ─────────────────── │          │
    │ 🔑 id (PK)          │   base  │ 🔑 id (PK)          │          │
    │    agent_code       │         │ 🔗 user_id (FK)     │          │ 1:M
    │    agent_name       │         │    agent_code       │          │
    │    asr_model_id     │         │    agent_name       │          │
    │    vad_model_id     │         │    asr_model_id     │          │
    │    llm_model_id     │         │    vad_model_id     │          │
    │    vllm_model_id    │         │    llm_model_id     │          │
    │    tts_model_id     │         │    vllm_model_id    │          │
    │    tts_voice_id     │         │    tts_model_id     │          │
    │    mem_model_id     │         │    tts_voice_id     │          │
    │    intent_model_id  │         │    mem_model_id     │          │
    │    system_prompt    │         │    intent_model_id  │          │
    │    lang_code        │         │    system_prompt    │          │
    │    language         │         │    lang_code        │          │
    │    sort             │         │    language         │          │
    │    creator          │         │    sort             │          │
    │    created_at       │         │    creator          │          │
    │    updater          │         │    created_at       │          │
    │    updated_at       │         │    updater          │          │
    └─────────────────────┘         │    updated_at       │          │
                                    └─────────────────────┘          │
                                            │                        │
                                            │ 1:M                    │
                                            ▼                        │
                                                                     │
                                    ┌─────────────────────┐          │
                                    │     sys_user        │──────────┘
                                    │ ─────────────────── │
                                    │ 🔑 id (PK)          │
                                    │ 🔒 username (UK)    │
                                    │    password         │
                                    │    super_admin      │
                                    │    status           │
                                    │    create_date      │
                                    │    creator          │
                                    │    updater          │
                                    │    update_date      │
                                    └─────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                      📱 DEVICE MANAGEMENT LAYER                                                │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────┘

    ┌─────────────────────┐         ┌─────────────────────┐
    │     ai_device       │◄────────┤     ai_agent        │
    │ ─────────────────── │  M:1    │ ─────────────────── │
    │ 🔑 id (PK)          │         │ 🔑 id (PK)          │
    │ 🔗 user_id (FK)     │         │ 🔗 user_id (FK)     │
    │    mac_address      │         │    agent_code       │
    │    last_connected   │         │    agent_name       │
    │    auto_update      │         │    asr_model_id     │
    │    board            │         │    vad_model_id     │
    │    alias            │         │    llm_model_id     │
    │ 🔗 agent_id (FK)    │         │    vllm_model_id    │
    │    app_version      │         │    tts_model_id     │
    │    sort             │         │    tts_voice_id     │
    │    creator          │         │    mem_model_id     │
    │    create_date      │         │    intent_model_id  │
    │    updater          │         │    system_prompt    │
    │    update_date      │         │    lang_code        │
    └─────────────────────┘         │    language         │
            │                       │    sort             │
            │ 1:M                   │    creator          │
            ▼                       │    created_at       │
                                    │    updater          │
                                    │    updated_at       │
                                    └─────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                       🔊 VOICE RECOGNITION LAYER                                               │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────┘

    ┌─────────────────────┐         ┌─────────────────────┐         ┌─────────────────────┐
    │   ai_voiceprint     │◄────────┤     sys_user        │────────►│     ai_agent        │
    │ ─────────────────── │  M:1    │ ─────────────────── │  1:M    │ ─────────────────── │
    │ 🔑 id (PK)          │         │ 🔑 id (PK)          │         │ 🔑 id (PK)          │
    │    name             │         │ 🔒 username (UK)    │         │ 🔗 user_id (FK)     │
    │ 🔗 user_id (FK)     │         │    password         │         │    agent_code       │
    │ 🔗 agent_id (FK)    │         │    super_admin      │         │    agent_name       │
    │    agent_code       │         │    status           │         │    asr_model_id     │
    │    agent_name       │         │    create_date      │         │    vad_model_id     │
    │    description      │         │    creator          │         │    llm_model_id     │
    │    embedding        │         │    updater          │         │    vllm_model_id    │
    │    memory           │         │    update_date      │         │    tts_model_id     │
    │    sort             │         └─────────────────────┘         │    tts_voice_id     │
    │    creator          │                                         │    mem_model_id     │
    │    created_at       │                                         │    intent_model_id  │
    │    updater          │                                         │    system_prompt    │
    │    updated_at       │                                         │    lang_code        │
    └─────────────────────┘                                         │    language         │
                                                                    │    sort             │
                                                                    │    creator          │
                                                                    │    created_at       │
                                                                    │    updater          │
                                                                    │    updated_at       │
                                                                    └─────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                      💬 CHAT & COMMUNICATION LAYER                                             │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────┘

                                    ┌─────────────────────┐
                                    │     sys_user        │
                                    │ ─────────────────── │
                                    │ 🔑 id (PK)          │
                                    │ 🔒 username (UK)    │
                                    │    password         │
                                    │    super_admin      │
                                    │    status           │
                                    │    create_date      │
                                    │    creator          │
                                    │    updater          │
                                    │    update_date      │
                                    └─────────────────────┘
                                            │
                                            │ 1:M
                                            ▼
    ┌─────────────────────┐         ┌─────────────────────┐         ┌─────────────────────┐
    │  ai_chat_history    │◄────────┤     ai_agent        │────────►│     ai_device       │
    │ ─────────────────── │  M:1    │ ─────────────────── │  1:M    │ ─────────────────── │
    │ 🔑 id (PK)          │         │ 🔑 id (PK)          │         │ 🔑 id (PK)          │
    │ 🔗 user_id (FK)     │         │ 🔗 user_id (FK)     │         │ 🔗 user_id (FK)     │
    │ 🔗 agent_id (FK)    │         │    agent_code       │         │    mac_address      │
    │ 🔗 device_id (FK)   │         │    agent_name       │         │    last_connected   │
    │    message_count    │         │    asr_model_id     │         │    auto_update      │
    │    creator          │         │    vad_model_id     │         │    board            │
    │    create_date      │         │    llm_model_id     │         │    alias            │
    │    updater          │         │    vllm_model_id    │         │ 🔗 agent_id (FK)    │
    │    update_date      │         │    tts_model_id     │         │    app_version      │
    └─────────────────────┘         │    tts_voice_id     │         │    sort             │
            │                       │    mem_model_id     │         │    creator          │
            │ 1:M                   │    intent_model_id  │         │    create_date      │
            ▼                       │    system_prompt    │         │    updater          │
    ┌─────────────────────┐         │    lang_code        │         │    update_date      │
    │  ai_chat_message    │         │    language         │         └─────────────────────┘
    │ ─────────────────── │         │    sort             │                 │
    │ 🔑 id (PK)          │         │    creator          │                 │ via mac_address
    │ 🔗 user_id (FK)     │         │    created_at       │                 │
    │ 🔗 chat_id (FK)     │         │    updater          │                 ▼
    │    role (ENUM)      │         │    updated_at       │         ┌─────────────────────┐
    │    content          │         └─────────────────────┘         │ai_agent_chat_history│
    │    prompt_tokens    │                 │                       │ ─────────────────── │
    │    total_tokens     │                 │ 1:M                   │ 🔑 id (PK)          │
    │    completion_tokens│                 ▼                       │    mac_address      │
    │    prompt_ms        │                                         │ 🔗 agent_id (FK)    │
    │    total_ms         │                                         │    session_id       │
    │    completion_ms    │                                         │    chat_type        │
    │    creator          │                                         │    content          │
    │    create_date      │                                         │ 🔗 audio_id (FK)    │
    │    updater          │                                         │    created_at       │
    │    update_date      │                                         │    updated_at       │
    └─────────────────────┘                                         └─────────────────────┘
                                                                            │
                                                                            │ 1:1
                                                                            ▼
                                                                    ┌─────────────────────┐
                                                                    │ai_agent_chat_audio  │
                                                                    │ ─────────────────── │
                                                                    │ 🔑 id (PK)          │
                                                                    │    audio (LONGBLOB) │
                                                                    └─────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                         📊 RELATIONSHIP SUMMARY                                                │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────┘

🔗 PRIMARY RELATIONSHIPS:
├── sys_user (1) ──────────── (M) ai_agent           │ Users own multiple AI agents
├── sys_user (1) ──────────── (M) ai_device          │ Users own multiple ESP32 devices
├── sys_user (1) ──────────── (M) ai_voiceprint      │ Users have multiple voiceprints
├── sys_user (1) ──────────── (M) ai_chat_history    │ Users participate in multiple chats
├── sys_user (1) ──────────── (1) sys_user_token     │ Each user has one active token
├── ai_agent (1) ─────────── (M) ai_device           │ Agent can be assigned to multiple devices
├── ai_agent (1) ─────────── (M) ai_chat_history     │ Agent participates in multiple chats
├── ai_agent (1) ─────────── (M) ai_agent_chat_history │ Agent has multiple device interactions
├── ai_model_config (1) ──── (M) ai_tts_voice        │ TTS models have multiple voices
└── ai_chat_history (1) ──── (M) ai_chat_message     │ Chat sessions contain multiple messages

🔗 SECONDARY RELATIONSHIPS:
├── sys_dict_type (1) ──────── (M) sys_dict_data     │ Dictionary types contain multiple entries
├── ai_agent_template ────────── ai_agent            │ Templates used to create agents
├── ai_device ───────────────── ai_agent_chat_history │ Devices connect via MAC address
└── ai_agent_chat_history (1) ── (1) ai_agent_chat_audio │ Chat entries may have audio data

🔗 MODEL CONFIGURATION RELATIONSHIPS:
├── ai_agent.asr_model_id ────── ai_model_config.id  │ Speech Recognition Model
├── ai_agent.vad_model_id ────── ai_model_config.id  │ Voice Activity Detection Model
├── ai_agent.llm_model_id ────── ai_model_config.id  │ Large Language Model
├── ai_agent.vllm_model_id ───── ai_model_config.id  │ Vision Language Model
├── ai_agent.tts_model_id ────── ai_model_config.id  │ Text-to-Speech Model
├── ai_agent.mem_model_id ────── ai_model_config.id  │ Memory Model
├── ai_agent.intent_model_id ─── ai_model_config.id  │ Intent Recognition Model
└── ai_agent.tts_voice_id ────── ai_tts_voice.id     │ TTS Voice Configuration

┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                           🔑 LEGEND                                                            │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────┘

SYMBOLS:
🔑 PK    = Primary Key
🔗 FK    = Foreign Key
🔒 UK    = Unique Key
(1)      = One (in relationship)
(M)      = Many (in relationship)
◄────────┤ = One-to-Many relationship (arrow points to "One" side)
────────► = Many-to-One relationship (arrow points to "One" side)
│        = Connection line
▼        = Relationship flow direction

TABLE CATEGORIES:
🔐 System Management    = User authentication, system configuration
🤖 AI Model Config      = AI model providers, configurations, voices
🧠 AI Agent Management  = Agent templates and user-created agents
📱 Device Management    = ESP32 device information and assignments
🔊 Voice Recognition    = Voiceprint storage and recognition
💬 Chat & Communication = Web and device-based chat systems

DATA TYPES:
VARCHAR(n)  = Variable character string
BIGINT      = 64-bit integer
TINYINT     = 8-bit integer
DATETIME    = Date and time
JSON        = JSON object
TEXT        = Large text field
LONGTEXT    = Very large text field
LONGBLOB    = Large binary object
ENUM        = Enumerated values

┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                        🎯 SYSTEM FLOW                                                          │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────┘

1. USER REGISTRATION & LOGIN
   sys_user → sys_user_token (Authentication)

2. AI AGENT CREATION
   sys_user → ai_agent_template → ai_agent (Agent setup)
   ai_model_config → ai_agent (Model assignment)
   ai_tts_voice → ai_agent (Voice assignment)

3. DEVICE MANAGEMENT
   sys_user → ai_device (Device ownership)
   ai_agent → ai_device (Agent assignment)

4. VOICE RECOGNITION
   sys_user → ai_voiceprint → ai_agent (Voice training)

5. COMMUNICATION CHANNELS
   A) Web Interface:
      sys_user → ai_chat_history → ai_chat_message

   B) Device Interface:
      ai_device → ai_agent_chat_history → ai_agent_chat_audio

6. SYSTEM CONFIGURATION
   sys_params (System settings)
   sys_dict_type → sys_dict_data (System dictionaries)

┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                      📈 DATABASE STATISTICS                                                    │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────┘

TOTAL TABLES: 16
├── System Management: 5 tables (31.25%)
├── AI Model Config: 3 tables (18.75%)
├── AI Agent Management: 2 tables (12.50%)
├── Device Management: 1 table (6.25%)
├── Voice Recognition: 1 table (6.25%)
└── Chat & Communication: 4 tables (25.00%)

RELATIONSHIP TYPES:
├── One-to-One: 2 relationships
├── One-to-Many: 12 relationships
├── Many-to-Many: 7 relationships (via foreign keys)
└── Template-based: 1 relationship

KEY FEATURES:
✅ Multi-user support with role-based access
✅ Modular AI pipeline (7 different model types)
✅ Dual communication channels (Web + Device)
✅ Voice recognition and personalization
✅ Device management with firmware tracking
✅ Comprehensive chat history and analytics
✅ Flexible system configuration
✅ Template-based agent creation

---
Generated: 2025-08-20 | Version: 1.0 | Format: ASCII Art Visualization
