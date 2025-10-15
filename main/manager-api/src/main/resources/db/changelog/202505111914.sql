-- Add chat history configuration field
ALTER TABLE ai_agent
ADD COLUMN chat_history_conf SMALLINT NOT NULL DEFAULT 0;

COMMENT ON COLUMN ai_agent.chat_history_conf IS 'Chat history config (0:no record 1:text only 2:text and audio)';

ALTER TABLE ai_agent_template
ADD COLUMN chat_history_conf SMALLINT NOT NULL DEFAULT 0;

COMMENT ON COLUMN ai_agent_template.chat_history_conf IS 'Chat history config (0:no record 1:text only 2:text and audio)';
