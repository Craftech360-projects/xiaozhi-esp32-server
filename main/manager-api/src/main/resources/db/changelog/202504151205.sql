-- Increase ai_tts_voice name column length to support longer voice names
ALTER TABLE ai_tts_voice ALTER COLUMN name TYPE VARCHAR(100);
