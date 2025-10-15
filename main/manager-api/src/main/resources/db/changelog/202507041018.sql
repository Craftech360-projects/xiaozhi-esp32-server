DROP TABLE IF EXISTS ai_agent_voice_print;
CREATE TABLE ai_agent_voice_print (
  id VARCHAR(32) NOT NULL,
  agent_id VARCHAR(32) NOT NULL,
  source_name VARCHAR(50) NOT NULL,
  introduce VARCHAR(200),
  create_date TIMESTAMP,
  creator BIGINT,
  update_date TIMESTAMP,
  updater BIGINT,
  PRIMARY KEY (id)
);

COMMENT ON TABLE ai_agent_voice_print IS 'Agent voiceprint table';
COMMENT ON COLUMN ai_agent_voice_print.id IS 'Voiceprint ID';
COMMENT ON COLUMN ai_agent_voice_print.agent_id IS 'Associated agent ID';
COMMENT ON COLUMN ai_agent_voice_print.source_name IS 'Name of voiceprint source person';
COMMENT ON COLUMN ai_agent_voice_print.introduce IS 'Description of voiceprint source person';
COMMENT ON COLUMN ai_agent_voice_print.create_date IS 'Creation time';
COMMENT ON COLUMN ai_agent_voice_print.creator IS 'Creator';
COMMENT ON COLUMN ai_agent_voice_print.update_date IS 'Update time';
COMMENT ON COLUMN ai_agent_voice_print.updater IS 'Updater';