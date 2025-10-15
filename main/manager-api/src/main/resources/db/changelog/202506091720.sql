ALTER TABLE ai_tts_voice
ADD COLUMN reference_audio VARCHAR(500) DEFAULT NULL,
ADD COLUMN reference_text VARCHAR(500) DEFAULT NULL;

COMMENT ON COLUMN ai_tts_voice.reference_audio IS 'Reference audio path';
COMMENT ON COLUMN ai_tts_voice.reference_text IS 'Reference text';
