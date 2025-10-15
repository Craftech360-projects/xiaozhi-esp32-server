-- Modify parameters for versions before 0.3.0
update sys_params set param_value = '.mp3;.wav;.p3' where  param_code = 'plugins.play_music.music_ext';
update ai_model_config set config_json =  '{"type": "intent_llm", "llm": "LLM_ChatGLMLLM"}' where  id = 'Intent_intent_llm';

-- Add Edge voice options
delete from ai_tts_voice where tts_model_id = 'TTS_EdgeTTS';
INSERT INTO ai_tts_voice (id, tts_model_id, name, tts_voice, languages, voice_demo, remark, sort, creator, create_date, updater, update_date) VALUES
('TTS_EdgeTTS0001', 'TTS_EdgeTTS', 'EdgeTTS Female-Xiaoxiao', 'zh-CN-XiaoxiaoNeural', 'Mandarin', NULL, NULL, 1, 1, NOW(), 1, NOW()),
('TTS_EdgeTTS0002', 'TTS_EdgeTTS', 'EdgeTTS Male-Yunyang', 'zh-CN-YunyangNeural', 'Mandarin', NULL, NULL, 2, 1, NOW(), 1, NOW()),
('TTS_EdgeTTS0003', 'TTS_EdgeTTS', 'EdgeTTS Female-Xiaoyi', 'zh-CN-XiaoyiNeural', 'Mandarin', NULL, NULL, 3, 1, NOW(), 1, NOW()),
('TTS_EdgeTTS0004', 'TTS_EdgeTTS', 'EdgeTTS Male-Yunjian', 'zh-CN-YunjianNeural', 'Mandarin', NULL, NULL, 4, 1, NOW(), 1, NOW()),
('TTS_EdgeTTS0005', 'TTS_EdgeTTS', 'EdgeTTS Male-Yunxi', 'zh-CN-YunxiNeural', 'Mandarin', NULL, NULL, 5, 1, NOW(), 1, NOW()),
('TTS_EdgeTTS0006', 'TTS_EdgeTTS', 'EdgeTTS Male-Yunxia', 'zh-CN-YunxiaNeural', 'Mandarin', NULL, NULL, 6, 1, NOW(), 1, NOW()),
('TTS_EdgeTTS0007', 'TTS_EdgeTTS', 'EdgeTTS Female-Liaoning Xiaobei', 'zh-CN-liaoning-XiaobeiNeural', 'Liaoning', NULL, NULL, 7, 1, NOW(), 1, NOW()),
('TTS_EdgeTTS0008', 'TTS_EdgeTTS', 'EdgeTTS Female-Shaanxi Xiaoni', 'zh-CN-shaanxi-XiaoniNeural', 'Shaanxi', NULL, NULL, 8, 1, NOW(), 1, NOW()),
('TTS_EdgeTTS0009', 'TTS_EdgeTTS', 'EdgeTTS Female-HK HiuGaai', 'zh-HK-HiuGaaiNeural', 'Cantonese', NULL, 'Friendly, Positive', 9, 1, NOW(), 1, NOW()),
('TTS_EdgeTTS0010', 'TTS_EdgeTTS', 'EdgeTTS Female-HK HiuMaan', 'zh-HK-HiuMaanNeural', 'Cantonese', NULL, 'Friendly, Positive', 10, 1, NOW(), 1, NOW()),
('TTS_EdgeTTS0011', 'TTS_EdgeTTS', 'EdgeTTS Male-HK WanLung', 'zh-HK-WanLungNeural', 'Cantonese', NULL, 'Friendly, Positive', 11, 1, NOW(), 1, NOW());

-- Add parameter for user registration
delete from sys_params where  id in (103,104);
INSERT INTO sys_params (id, param_code, param_value, value_type, param_type, remark) VALUES (103, 'server.allow_user_register', 'true', 'boolean', 1, 'Whether to allow user registration besides admin');
INSERT INTO sys_params (id, param_code, param_value, value_type, param_type, remark) VALUES (104, 'server.fronted_url', 'http://xiaozhi.server.com', 'string', 1, 'Control panel address displayed when issuing 6-digit verification code');

-- Fix CosyVoiceSiliconflow voices
delete from ai_tts_voice where tts_model_id = 'TTS_CosyVoiceSiliconflow';
INSERT INTO ai_tts_voice (id, tts_model_id, name, tts_voice, languages, voice_demo, remark, sort, creator, create_date, updater, update_date) VALUES ('TTS_CosyVoiceSiliconflow0001', 'TTS_CosyVoiceSiliconflow', 'CosyVoice Male', 'FunAudioLLM/CosyVoice2-0.5B:alex', 'Chinese', 'https://example.com/cosyvoice/alex.mp3', NULL, 1, 1, NOW(), 1, NOW());
INSERT INTO ai_tts_voice (id, tts_model_id, name, tts_voice, languages, voice_demo, remark, sort, creator, create_date, updater, update_date) VALUES ('TTS_CosyVoiceSiliconflow0002', 'TTS_CosyVoiceSiliconflow', 'CosyVoice Female', 'FunAudioLLM/CosyVoice2-0.5B:bella', 'Chinese', 'https://example.com/cosyvoice/bella.mp3', NULL, 2, 1, NOW(), 1, NOW());
