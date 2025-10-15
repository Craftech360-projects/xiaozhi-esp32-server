-- Add new field to agent voiceprint
ALTER TABLE ai_agent_voice_print
    ADD COLUMN audio_id VARCHAR(32) NOT NULL;

COMMENT ON COLUMN ai_agent_voice_print.audio_id IS 'Audio ID';