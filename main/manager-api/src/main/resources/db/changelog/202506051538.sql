-- Add LinkeraiTTS provider and model configuration
DELETE FROM ai_model_provider WHERE id = 'SYSTEM_TTS_LinkeraiTTS';
INSERT INTO ai_model_provider (id, model_type, provider_code, name, fields, sort, creator, create_date, updater, update_date) VALUES
('SYSTEM_TTS_LinkeraiTTS', 'TTS', 'linkerai', 'Linkerai TTS', '[{"key":"api_url","label":"API Address","type":"string"},{"key":"audio_format","label":"Audio Format","type":"string"},{"key":"access_token","label":"Access Token","type":"string"},{"key":"voice","label":"Default Voice","type":"string"}]', 14, 1, NOW(), 1, NOW());

DELETE FROM ai_model_config WHERE id = 'TTS_LinkeraiTTS';
INSERT INTO ai_model_config VALUES ('TTS_LinkeraiTTS', 'TTS', 'LinkeraiTTS', 'Linkerai TTS', FALSE, TRUE, '{"type": "linkerai", "api_url": "https://tts.linkerai.cn/tts", "audio_format": "pcm", "access_token": "U4YdYXVfpwWnk2t5Gp822zWPCuORyeJL", "voice": "OUeAo1mhq6IBExi"}', NULL, NULL, 17, NULL, NULL, NULL, NULL);

-- LinkeraiTTS model configuration documentation
UPDATE ai_model_config SET
doc_link = 'https://tts.linkerai.cn/docs',
remark = 'Linkerai TTS service configuration instructions:
1. Visit https://linkerai.cn to register and obtain access token
2. Default access_token for testing only, do not use for commercial purposes
3. Supports voice cloning, can upload audio and fill in voice parameter
4. If voice parameter empty, will use default voice' WHERE id = 'TTS_LinkeraiTTS';


DELETE FROM ai_tts_voice WHERE tts_model_id = 'TTS_LinkeraiTTS';
INSERT INTO ai_tts_voice (id, tts_model_id, name, tts_voice, languages, voice_demo, remark, sort, creator, create_date, updater, update_date) VALUES ('TTS_LinkeraiTTS_0001', 'TTS_LinkeraiTTS', 'Zhiruo', 'OUeAo1mhq6IBExi', 'Chinese', NULL, NULL, 1, 1, NOW(), 1, NOW());
