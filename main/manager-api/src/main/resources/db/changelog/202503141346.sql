-- Model provider table
DROP TABLE IF EXISTS ai_model_provider;
CREATE TABLE ai_model_provider (
    id VARCHAR(32) NOT NULL,
    model_type VARCHAR(20),
    provider_code VARCHAR(50),
    name VARCHAR(50),
    fields JSON,
    sort INTEGER DEFAULT 0,
    creator BIGINT,
    create_date TIMESTAMP,
    updater BIGINT,
    update_date TIMESTAMP,
    PRIMARY KEY (id)
);
CREATE INDEX idx_ai_model_provider_model_type ON ai_model_provider (model_type);
COMMENT ON TABLE ai_model_provider IS 'Model provider table';
COMMENT ON COLUMN ai_model_provider.id IS 'Primary key';
COMMENT ON COLUMN ai_model_provider.model_type IS 'Model type (Memory/ASR/VAD/LLM/TTS)';
COMMENT ON COLUMN ai_model_provider.provider_code IS 'Provider code';
COMMENT ON COLUMN ai_model_provider.name IS 'Provider name';
COMMENT ON COLUMN ai_model_provider.fields IS 'Provider field list (JSON format)';
COMMENT ON COLUMN ai_model_provider.sort IS 'sort order';
COMMENT ON COLUMN ai_model_provider.creator IS 'creator';
COMMENT ON COLUMN ai_model_provider.create_date IS 'creation time';
COMMENT ON COLUMN ai_model_provider.updater IS 'updater';
COMMENT ON COLUMN ai_model_provider.update_date IS 'update time';

-- Model configuration table
DROP TABLE IF EXISTS ai_model_config;
CREATE TABLE ai_model_config (
    id VARCHAR(32) NOT NULL,
    model_type VARCHAR(20),
    model_code VARCHAR(50),
    model_name VARCHAR(50),
    is_default BOOLEAN DEFAULT false,
    is_enabled BOOLEAN DEFAULT false,
    config_json JSON,
    doc_link VARCHAR(200),
    remark VARCHAR(255),
    sort INTEGER DEFAULT 0,
    creator BIGINT,
    create_date TIMESTAMP,
    updater BIGINT,
    update_date TIMESTAMP,
    PRIMARY KEY (id)
);
CREATE INDEX idx_ai_model_config_model_type ON ai_model_config (model_type);
COMMENT ON TABLE ai_model_config IS 'Model configuration table';
COMMENT ON COLUMN ai_model_config.id IS 'Primary key';
COMMENT ON COLUMN ai_model_config.model_type IS 'Model type (Memory/ASR/VAD/LLM/TTS)';
COMMENT ON COLUMN ai_model_config.model_code IS 'Model code (e.g., AliLLM, DoubaoTTS)';
COMMENT ON COLUMN ai_model_config.model_name IS 'Model name';
COMMENT ON COLUMN ai_model_config.is_default IS 'Is default configuration (false: no, true: yes)';
COMMENT ON COLUMN ai_model_config.is_enabled IS 'Is enabled';
COMMENT ON COLUMN ai_model_config.config_json IS 'Model configuration (JSON format)';
COMMENT ON COLUMN ai_model_config.doc_link IS 'Official documentation link';
COMMENT ON COLUMN ai_model_config.remark IS 'remark';
COMMENT ON COLUMN ai_model_config.sort IS 'sort order';
COMMENT ON COLUMN ai_model_config.creator IS 'creator';
COMMENT ON COLUMN ai_model_config.create_date IS 'creation time';
COMMENT ON COLUMN ai_model_config.updater IS 'updater';
COMMENT ON COLUMN ai_model_config.update_date IS 'update time';

-- TTS voice table
DROP TABLE IF EXISTS ai_tts_voice;
CREATE TABLE ai_tts_voice (
    id VARCHAR(32) NOT NULL,
    tts_model_id VARCHAR(32),
    name VARCHAR(20),
    tts_voice VARCHAR(50),
    languages VARCHAR(50),
    voice_demo VARCHAR(500) DEFAULT NULL,
    remark VARCHAR(255),
    sort INTEGER DEFAULT 0,
    creator BIGINT,
    create_date TIMESTAMP,
    updater BIGINT,
    update_date TIMESTAMP,
    PRIMARY KEY (id)
);
CREATE INDEX idx_ai_tts_voice_tts_model_id ON ai_tts_voice (tts_model_id);
COMMENT ON TABLE ai_tts_voice IS 'TTS voice table';
COMMENT ON COLUMN ai_tts_voice.id IS 'Primary key';
COMMENT ON COLUMN ai_tts_voice.tts_model_id IS 'Corresponding TTS model primary key';
COMMENT ON COLUMN ai_tts_voice.name IS 'Voice name';
COMMENT ON COLUMN ai_tts_voice.tts_voice IS 'Voice code';
COMMENT ON COLUMN ai_tts_voice.languages IS 'Languages';
COMMENT ON COLUMN ai_tts_voice.voice_demo IS 'Voice demo';
COMMENT ON COLUMN ai_tts_voice.remark IS 'remark';
COMMENT ON COLUMN ai_tts_voice.sort IS 'sort order';
COMMENT ON COLUMN ai_tts_voice.creator IS 'creator';
COMMENT ON COLUMN ai_tts_voice.create_date IS 'creation time';
COMMENT ON COLUMN ai_tts_voice.updater IS 'updater';
COMMENT ON COLUMN ai_tts_voice.update_date IS 'update time';

-- Agent configuration template table
DROP TABLE IF EXISTS ai_agent_template;
CREATE TABLE ai_agent_template (
    id VARCHAR(32) NOT NULL,
    agent_code VARCHAR(36),
    agent_name VARCHAR(64),
    asr_model_id VARCHAR(32),
    vad_model_id VARCHAR(64),
    llm_model_id VARCHAR(32),
    tts_model_id VARCHAR(32),
    tts_voice_id VARCHAR(32),
    mem_model_id VARCHAR(32),
    intent_model_id VARCHAR(32),
    system_prompt TEXT,
    lang_code VARCHAR(10),
    language VARCHAR(10),
    sort INTEGER DEFAULT 0,
    creator BIGINT,
    created_at TIMESTAMP,
    updater BIGINT,
    updated_at TIMESTAMP,
    PRIMARY KEY (id)
);
COMMENT ON TABLE ai_agent_template IS 'Agent configuration template table';
COMMENT ON COLUMN ai_agent_template.id IS 'Agent unique identifier';
COMMENT ON COLUMN ai_agent_template.agent_code IS 'Agent code';
COMMENT ON COLUMN ai_agent_template.agent_name IS 'Agent name';
COMMENT ON COLUMN ai_agent_template.asr_model_id IS 'Speech recognition model identifier';
COMMENT ON COLUMN ai_agent_template.vad_model_id IS 'Voice activity detection identifier';
COMMENT ON COLUMN ai_agent_template.llm_model_id IS 'Large language model identifier';
COMMENT ON COLUMN ai_agent_template.tts_model_id IS 'Text-to-speech model identifier';
COMMENT ON COLUMN ai_agent_template.tts_voice_id IS 'Voice identifier';
COMMENT ON COLUMN ai_agent_template.mem_model_id IS 'Memory model identifier';
COMMENT ON COLUMN ai_agent_template.intent_model_id IS 'Intent model identifier';
COMMENT ON COLUMN ai_agent_template.system_prompt IS 'Role setting parameters';
COMMENT ON COLUMN ai_agent_template.lang_code IS 'Language code';
COMMENT ON COLUMN ai_agent_template.language IS 'Interaction language';
COMMENT ON COLUMN ai_agent_template.sort IS 'sort weight';
COMMENT ON COLUMN ai_agent_template.creator IS 'creator ID';
COMMENT ON COLUMN ai_agent_template.created_at IS 'creation time';
COMMENT ON COLUMN ai_agent_template.updater IS 'updater ID';
COMMENT ON COLUMN ai_agent_template.updated_at IS 'update time';

-- Agent configuration table
DROP TABLE IF EXISTS ai_agent;
CREATE TABLE ai_agent (
    id VARCHAR(32) NOT NULL,
    user_id BIGINT,
    agent_code VARCHAR(36),
    agent_name VARCHAR(64),
    asr_model_id VARCHAR(32),
    vad_model_id VARCHAR(64),
    llm_model_id VARCHAR(32),
    tts_model_id VARCHAR(32),
    tts_voice_id VARCHAR(32),
    mem_model_id VARCHAR(32),
    intent_model_id VARCHAR(32),
    system_prompt TEXT,
    lang_code VARCHAR(10),
    language VARCHAR(10),
    sort INTEGER DEFAULT 0,
    creator BIGINT,
    created_at TIMESTAMP,
    updater BIGINT,
    updated_at TIMESTAMP,
    PRIMARY KEY (id)
);
CREATE INDEX idx_ai_agent_user_id ON ai_agent (user_id);
COMMENT ON TABLE ai_agent IS 'Agent configuration table';
COMMENT ON COLUMN ai_agent.id IS 'Agent unique identifier';
COMMENT ON COLUMN ai_agent.user_id IS 'User ID';
COMMENT ON COLUMN ai_agent.agent_code IS 'Agent code';
COMMENT ON COLUMN ai_agent.agent_name IS 'Agent name';
COMMENT ON COLUMN ai_agent.asr_model_id IS 'Speech recognition model identifier';
COMMENT ON COLUMN ai_agent.vad_model_id IS 'Voice activity detection identifier';
COMMENT ON COLUMN ai_agent.llm_model_id IS 'Large language model identifier';
COMMENT ON COLUMN ai_agent.tts_model_id IS 'Text-to-speech model identifier';
COMMENT ON COLUMN ai_agent.tts_voice_id IS 'Voice identifier';
COMMENT ON COLUMN ai_agent.mem_model_id IS 'Memory model identifier';
COMMENT ON COLUMN ai_agent.intent_model_id IS 'Intent model identifier';
COMMENT ON COLUMN ai_agent.system_prompt IS 'Role setting parameters';
COMMENT ON COLUMN ai_agent.lang_code IS 'Language code';
COMMENT ON COLUMN ai_agent.language IS 'Interaction language';
COMMENT ON COLUMN ai_agent.sort IS 'sort weight';
COMMENT ON COLUMN ai_agent.creator IS 'creator ID';
COMMENT ON COLUMN ai_agent.created_at IS 'creation time';
COMMENT ON COLUMN ai_agent.updater IS 'updater ID';
COMMENT ON COLUMN ai_agent.updated_at IS 'update time';

-- Device information table
DROP TABLE IF EXISTS ai_device;
CREATE TABLE ai_device (
    id VARCHAR(32) NOT NULL,
    user_id BIGINT,
    mac_address VARCHAR(50),
    last_connected_at TIMESTAMP,
    auto_update SMALLINT DEFAULT 0,
    board VARCHAR(50),
    alias VARCHAR(64) DEFAULT NULL,
    agent_id VARCHAR(32),
    app_version VARCHAR(20),
    sort INTEGER DEFAULT 0,
    creator BIGINT,
    create_date TIMESTAMP,
    updater BIGINT,
    update_date TIMESTAMP,
    PRIMARY KEY (id)
);
CREATE INDEX idx_ai_device_created_at ON ai_device (mac_address);
COMMENT ON TABLE ai_device IS 'Device information table';
COMMENT ON COLUMN ai_device.id IS 'Device unique identifier';
COMMENT ON COLUMN ai_device.user_id IS 'Associated user ID';
COMMENT ON COLUMN ai_device.mac_address IS 'MAC address';
COMMENT ON COLUMN ai_device.last_connected_at IS 'Last connection time';
COMMENT ON COLUMN ai_device.auto_update IS 'Auto update switch (0: off, 1: on)';
COMMENT ON COLUMN ai_device.board IS 'Device hardware model';
COMMENT ON COLUMN ai_device.alias IS 'Device alias';
COMMENT ON COLUMN ai_device.agent_id IS 'Agent ID';
COMMENT ON COLUMN ai_device.app_version IS 'Firmware version number';
COMMENT ON COLUMN ai_device.sort IS 'sort order';
COMMENT ON COLUMN ai_device.creator IS 'creator';
COMMENT ON COLUMN ai_device.create_date IS 'creation time';
COMMENT ON COLUMN ai_device.updater IS 'updater';
COMMENT ON COLUMN ai_device.update_date IS 'update time';

-- Voiceprint recognition table
DROP TABLE IF EXISTS ai_voiceprint;
CREATE TABLE ai_voiceprint (
    id VARCHAR(32) NOT NULL,
    name VARCHAR(64),
    user_id BIGINT,
    agent_id VARCHAR(32),
    agent_code VARCHAR(36),
    agent_name VARCHAR(36),
    description VARCHAR(255),
    embedding TEXT,
    memory TEXT,
    sort INTEGER DEFAULT 0,
    creator BIGINT,
    created_at TIMESTAMP,
    updater BIGINT,
    updated_at TIMESTAMP,
    PRIMARY KEY (id)
);
COMMENT ON TABLE ai_voiceprint IS 'Voiceprint recognition table';
COMMENT ON COLUMN ai_voiceprint.id IS 'Voiceprint unique identifier';
COMMENT ON COLUMN ai_voiceprint.name IS 'Voiceprint name';
COMMENT ON COLUMN ai_voiceprint.user_id IS 'User ID (associated with user table)';
COMMENT ON COLUMN ai_voiceprint.agent_id IS 'Associated agent ID';
COMMENT ON COLUMN ai_voiceprint.agent_code IS 'Associated agent code';
COMMENT ON COLUMN ai_voiceprint.agent_name IS 'Associated agent name';
COMMENT ON COLUMN ai_voiceprint.description IS 'Voiceprint description';
COMMENT ON COLUMN ai_voiceprint.embedding IS 'Voiceprint feature vector (JSON array format)';
COMMENT ON COLUMN ai_voiceprint.memory IS 'Associated memory data';
COMMENT ON COLUMN ai_voiceprint.sort IS 'sort weight';
COMMENT ON COLUMN ai_voiceprint.creator IS 'creator ID';
COMMENT ON COLUMN ai_voiceprint.created_at IS 'creation time';
COMMENT ON COLUMN ai_voiceprint.updater IS 'updater ID';
COMMENT ON COLUMN ai_voiceprint.updated_at IS 'update time';

-- Conversation history table
DROP TABLE IF EXISTS ai_chat_history;
CREATE TABLE ai_chat_history (
    id VARCHAR(32) NOT NULL,
    user_id BIGINT,
    agent_id VARCHAR(32) DEFAULT NULL,
    device_id VARCHAR(32) DEFAULT NULL,
    message_count INTEGER,
    creator BIGINT,
    create_date TIMESTAMP,
    updater BIGINT,
    update_date TIMESTAMP,
    PRIMARY KEY (id)
);
COMMENT ON TABLE ai_chat_history IS 'Conversation history table';
COMMENT ON COLUMN ai_chat_history.id IS 'Conversation ID';
COMMENT ON COLUMN ai_chat_history.user_id IS 'User ID';
COMMENT ON COLUMN ai_chat_history.agent_id IS 'Chat role';
COMMENT ON COLUMN ai_chat_history.device_id IS 'Device ID';
COMMENT ON COLUMN ai_chat_history.message_count IS 'Message summary';
COMMENT ON COLUMN ai_chat_history.creator IS 'creator';
COMMENT ON COLUMN ai_chat_history.create_date IS 'creation time';
COMMENT ON COLUMN ai_chat_history.updater IS 'updater';
COMMENT ON COLUMN ai_chat_history.update_date IS 'update time';

-- Conversation message table
DROP TABLE IF EXISTS ai_chat_message;
CREATE TABLE ai_chat_message (
    id VARCHAR(32) NOT NULL,
    user_id BIGINT,
    chat_id VARCHAR(64),
    role VARCHAR(20),
    content TEXT,
    prompt_tokens INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    completion_tokens INTEGER DEFAULT 0,
    prompt_ms INTEGER DEFAULT 0,
    total_ms INTEGER DEFAULT 0,
    completion_ms INTEGER DEFAULT 0,
    creator BIGINT,
    create_date TIMESTAMP,
    updater BIGINT,
    update_date TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT chk_role CHECK (role IN ('user', 'assistant'))
);
CREATE INDEX idx_ai_chat_message_user_id_chat_id_role ON ai_chat_message (user_id, chat_id);
CREATE INDEX idx_ai_chat_message_created_at ON ai_chat_message (create_date);
COMMENT ON TABLE ai_chat_message IS 'Conversation message table';
COMMENT ON COLUMN ai_chat_message.id IS 'Conversation record unique identifier';
COMMENT ON COLUMN ai_chat_message.user_id IS 'User unique identifier';
COMMENT ON COLUMN ai_chat_message.chat_id IS 'Conversation history ID';
COMMENT ON COLUMN ai_chat_message.role IS 'Role (user or assistant)';
COMMENT ON COLUMN ai_chat_message.content IS 'Conversation content';
COMMENT ON COLUMN ai_chat_message.prompt_tokens IS 'Prompt token count';
COMMENT ON COLUMN ai_chat_message.total_tokens IS 'Total token count';
COMMENT ON COLUMN ai_chat_message.completion_tokens IS 'Completion token count';
COMMENT ON COLUMN ai_chat_message.prompt_ms IS 'Prompt time (milliseconds)';
COMMENT ON COLUMN ai_chat_message.total_ms IS 'Total time (milliseconds)';
COMMENT ON COLUMN ai_chat_message.completion_ms IS 'Completion time (milliseconds)';
COMMENT ON COLUMN ai_chat_message.creator IS 'creator';
COMMENT ON COLUMN ai_chat_message.create_date IS 'creation time';
COMMENT ON COLUMN ai_chat_message.updater IS 'updater';
COMMENT ON COLUMN ai_chat_message.update_date IS 'update time';
