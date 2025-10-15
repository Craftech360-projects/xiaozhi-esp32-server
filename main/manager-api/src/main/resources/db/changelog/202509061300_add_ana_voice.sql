-- Add EdgeTTS Ana voice (en-US-AnaNeural) for default agent configuration
DELETE FROM ai_tts_voice WHERE id = 'TTS_EdgeTTS_Ana';
INSERT INTO ai_tts_voice (id, tts_model_id, name, tts_voice, languages, voice_demo, remark, sort, creator, create_date, updater, update_date)
VALUES ('TTS_EdgeTTS_Ana', 'TTS_EdgeTTS', 'EdgeTTS Ana', 'en-US-AnaNeural', 'English', NULL, NULL, 1, NULL, NULL, NULL, NULL);