-- Initialize agent chat history
DROP TABLE IF EXISTS ai_chat_history;
DROP TABLE IF EXISTS ai_chat_message;
DROP TABLE IF EXISTS ai_agent_chat_history;
CREATE TABLE ai_agent_chat_history
(
    id          BIGSERIAL PRIMARY KEY,
    mac_address VARCHAR(50),
    agent_id VARCHAR(32),
    session_id  VARCHAR(50),
    chat_type   SMALLINT,
    content     VARCHAR(1024),
    audio_id    VARCHAR(32),
    created_at  TIMESTAMP(3) DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at  TIMESTAMP(3) DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX idx_ai_agent_chat_history_mac ON ai_agent_chat_history(mac_address);
CREATE INDEX idx_ai_agent_chat_history_session_id ON ai_agent_chat_history(session_id);
CREATE INDEX idx_ai_agent_chat_history_agent_id ON ai_agent_chat_history(agent_id);
CREATE INDEX idx_ai_agent_chat_history_agent_session_created ON ai_agent_chat_history(agent_id, session_id, created_at);

COMMENT ON TABLE ai_agent_chat_history IS 'Agent chat history table';
COMMENT ON COLUMN ai_agent_chat_history.id IS 'Primary key ID';
COMMENT ON COLUMN ai_agent_chat_history.mac_address IS 'MAC address';
COMMENT ON COLUMN ai_agent_chat_history.agent_id IS 'Agent ID';
COMMENT ON COLUMN ai_agent_chat_history.session_id IS 'Session ID';
COMMENT ON COLUMN ai_agent_chat_history.chat_type IS 'Message type: 1-user, 2-agent';
COMMENT ON COLUMN ai_agent_chat_history.content IS 'Chat content';
COMMENT ON COLUMN ai_agent_chat_history.audio_id IS 'Audio ID';
COMMENT ON COLUMN ai_agent_chat_history.created_at IS 'Created time';
COMMENT ON COLUMN ai_agent_chat_history.updated_at IS 'Updated time';

DROP TABLE IF EXISTS ai_agent_chat_audio;
CREATE TABLE ai_agent_chat_audio
(
    id          VARCHAR(32) PRIMARY KEY,
    audio       BYTEA
);

COMMENT ON TABLE ai_agent_chat_audio IS 'Agent chat audio data table';
COMMENT ON COLUMN ai_agent_chat_audio.id IS 'Primary key ID';
COMMENT ON COLUMN ai_agent_chat_audio.audio IS 'Audio opus data';
