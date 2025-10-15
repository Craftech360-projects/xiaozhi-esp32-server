-- Add Alibaba Cloud streaming TTS provider
DELETE FROM ai_model_provider WHERE id = 'SYSTEM_TTS_AliyunStreamTTS';
INSERT INTO ai_model_provider (id, model_type, provider_code, name, fields, sort, creator, create_date, updater, update_date) VALUES
('SYSTEM_TTS_AliyunStreamTTS', 'TTS', 'aliyun_stream', 'Alibaba Cloud TTS (Streaming)', '[{"key":"appkey","label":"App AppKey","type":"string"},{"key":"token","label":"Temporary Token","type":"string"},{"key":"access_key_id","label":"AccessKey ID","type":"string"},{"key":"access_key_secret","label":"AccessKey Secret","type":"string"},{"key":"host","label":"Service Address","type":"string"},{"key":"voice","label":"Default Voice","type":"string"},{"key":"format","label":"Audio Format","type":"string"},{"key":"sample_rate","label":"Sample Rate","type":"number"},{"key":"volume","label":"Volume","type":"number"},{"key":"speech_rate","label":"Speech Rate","type":"number"},{"key":"pitch_rate","label":"Pitch","type":"number"},{"key":"output_dir","label":"Output Directory","type":"string"}]', 15, 1, NOW(), 1, NOW());

-- Add Alibaba Cloud streaming TTS model configuration
DELETE FROM ai_model_config WHERE id = 'TTS_AliyunStreamTTS';
INSERT INTO ai_model_config VALUES ('TTS_AliyunStreamTTS', 'TTS', 'AliyunStreamTTS', 'Alibaba Cloud TTS (Streaming)', FALSE, TRUE, '{"type": "aliyun_stream", "appkey": "", "token": "", "access_key_id": "", "access_key_secret": "", "host": "nls-gateway-cn-beijing.aliyuncs.com", "voice": "longxiaochun", "format": "pcm", "sample_rate": 16000, "volume": 50, "speech_rate": 0, "pitch_rate": 0, "output_dir": "tmp/"}', NULL, NULL, 18, NULL, NULL, NULL, NULL);

-- Update Alibaba Cloud streaming TTS configuration notes
UPDATE ai_model_config SET
doc_link = 'https://nls-portal.console.aliyun.com/',
remark = 'Alibaba Cloud Streaming TTS Configuration:
1. Difference between Alibaba Cloud TTS and Alibaba Cloud (Streaming) TTS: The former is one-time synthesis, the latter is real-time streaming synthesis
2. Streaming TTS has lower latency and better real-time performance, suitable for voice interaction scenarios
3. Need to create application and obtain authentication info in Alibaba Cloud Intelligent Speech Interaction console
4. Supports CosyVoice large model voices with more natural voice quality
5. Supports real-time adjustment of volume, speech rate, pitch and other parameters
Application steps:
1. Visit https://nls-portal.console.aliyun.com/ to enable Intelligent Speech Interaction service
2. Visit https://nls-portal.console.aliyun.com/applist to create project and obtain appkey
3. Visit https://nls-portal.console.aliyun.com/overview to get temporary token (or configure access_key_id and access_key_secret for auto-retrieval)
4. For dynamic token management, recommend configuring access_key_id and access_key_secret
5. Can choose servers in different regions like Beijing, Shanghai to optimize latency
6. voice parameter supports CosyVoice large model voices, such as longxiaochun, longyueyue, etc.
For more parameter configuration, see: https://help.aliyun.com/zh/isi/developer-reference/real-time-speech-synthesis
' WHERE id = 'TTS_AliyunStreamTTS';

-- Add Alibaba Cloud streaming TTS voices
DELETE FROM ai_tts_voice WHERE tts_model_id = 'TTS_AliyunStreamTTS';
-- Gentle female voice series
INSERT INTO ai_tts_voice (id, tts_model_id, name, tts_voice, languages, voice_demo, remark, sort, creator, create_date, updater, update_date) VALUES ('TTS_AliyunStreamTTS_0001', 'TTS_AliyunStreamTTS', 'Long Xiaochun - Gentle Sister', 'longxiaochun', 'Chinese and Chinese-English mixed', NULL, NULL, 1, 1, NOW(), 1, NOW());
INSERT INTO ai_tts_voice (id, tts_model_id, name, tts_voice, languages, voice_demo, remark, sort, creator, create_date, updater, update_date) VALUES ('TTS_AliyunStreamTTS_0002', 'TTS_AliyunStreamTTS', 'Long Xiaoxia - Gentle Female', 'longxiaoxia', 'Chinese and Chinese-English mixed', NULL, NULL, 2, 1, NOW(), 1, NOW());
INSERT INTO ai_tts_voice (id, tts_model_id, name, tts_voice, languages, voice_demo, remark, sort, creator, create_date, updater, update_date) VALUES ('TTS_AliyunStreamTTS_0003', 'TTS_AliyunStreamTTS', 'Long Mei - Gentle Female', 'longmei', 'Chinese and Chinese-English mixed', NULL, NULL, 3, 1, NOW(), 1, NOW());
INSERT INTO ai_tts_voice (id, tts_model_id, name, tts_voice, languages, voice_demo, remark, sort, creator, create_date, updater, update_date) VALUES ('TTS_AliyunStreamTTS_0004', 'TTS_AliyunStreamTTS', 'Long Gui - Gentle Female', 'longgui', 'Chinese and Chinese-English mixed', NULL, NULL, 4, 1, NOW(), 1, NOW());
-- Mature female voice series
INSERT INTO ai_tts_voice (id, tts_model_id, name, tts_voice, languages, voice_demo, remark, sort, creator, create_date, updater, update_date) VALUES ('TTS_AliyunStreamTTS_0005', 'TTS_AliyunStreamTTS', 'Long Yu - Mature Female', 'longyu', 'Chinese and Chinese-English mixed', NULL, NULL, 5, 1, NOW(), 1, NOW());
INSERT INTO ai_tts_voice (id, tts_model_id, name, tts_voice, languages, voice_demo, remark, sort, creator, create_date, updater, update_date) VALUES ('TTS_AliyunStreamTTS_0006', 'TTS_AliyunStreamTTS', 'Long Jiao - Mature Female', 'longjiao', 'Chinese and Chinese-English mixed', NULL, NULL, 6, 1, NOW(), 1, NOW());
-- Male voice series
INSERT INTO ai_tts_voice (id, tts_model_id, name, tts_voice, languages, voice_demo, remark, sort, creator, create_date, updater, update_date) VALUES ('TTS_AliyunStreamTTS_0007', 'TTS_AliyunStreamTTS', 'Long Chen - Dubbed Film Male', 'longchen', 'Chinese and Chinese-English mixed', NULL, NULL, 7, 1, NOW(), 1, NOW());
INSERT INTO ai_tts_voice (id, tts_model_id, name, tts_voice, languages, voice_demo, remark, sort, creator, create_date, updater, update_date) VALUES ('TTS_AliyunStreamTTS_0008', 'TTS_AliyunStreamTTS', 'Long Xiu - Young Male', 'longxiu', 'Chinese and Chinese-English mixed', NULL, NULL, 8, 1, NOW(), 1, NOW());
INSERT INTO ai_tts_voice (id, tts_model_id, name, tts_voice, languages, voice_demo, remark, sort, creator, create_date, updater, update_date) VALUES ('TTS_AliyunStreamTTS_0009', 'TTS_AliyunStreamTTS', 'Long Cheng - Sunny Male', 'longcheng', 'Chinese and Chinese-English mixed', NULL, NULL, 9, 1, NOW(), 1, NOW());
INSERT INTO ai_tts_voice (id, tts_model_id, name, tts_voice, languages, voice_demo, remark, sort, creator, create_date, updater, update_date) VALUES ('TTS_AliyunStreamTTS_0010', 'TTS_AliyunStreamTTS', 'Long Zhe - Mature Male', 'longzhe', 'Chinese and Chinese-English mixed', NULL, NULL, 10, 1, NOW(), 1, NOW());
-- Professional broadcast series
INSERT INTO ai_tts_voice (id, tts_model_id, name, tts_voice, languages, voice_demo, remark, sort, creator, create_date, updater, update_date) VALUES ('TTS_AliyunStreamTTS_0011', 'TTS_AliyunStreamTTS', 'Bella2.0 - News Female', 'loongbella', 'Chinese and Chinese-English mixed', NULL, NULL, 11, 1, NOW(), 1, NOW());
INSERT INTO ai_tts_voice (id, tts_model_id, name, tts_voice, languages, voice_demo, remark, sort, creator, create_date, updater, update_date) VALUES ('TTS_AliyunStreamTTS_0012', 'TTS_AliyunStreamTTS', 'Stella2.0 - Spirited Female', 'loongstella', 'Chinese and Chinese-English mixed', NULL, NULL, 12, 1, NOW(), 1, NOW());
INSERT INTO ai_tts_voice (id, tts_model_id, name, tts_voice, languages, voice_demo, remark, sort, creator, create_date, updater, update_date) VALUES ('TTS_AliyunStreamTTS_0013', 'TTS_AliyunStreamTTS', 'Long Shu - News Male', 'longshu', 'Chinese and Chinese-English mixed', NULL, NULL, 13, 1, NOW(), 1, NOW());
INSERT INTO ai_tts_voice (id, tts_model_id, name, tts_voice, languages, voice_demo, remark, sort, creator, create_date, updater, update_date) VALUES ('TTS_AliyunStreamTTS_0014', 'TTS_AliyunStreamTTS', 'Long Jing - Serious Female', 'longjing', 'Chinese and Chinese-English mixed', NULL, NULL, 14, 1, NOW(), 1, NOW());
-- Special voice series
INSERT INTO ai_tts_voice (id, tts_model_id, name, tts_voice, languages, voice_demo, remark, sort, creator, create_date, updater, update_date) VALUES ('TTS_AliyunStreamTTS_0015', 'TTS_AliyunStreamTTS', 'Long Qi - Lively Child', 'longqi', 'Chinese and Chinese-English mixed', NULL, NULL, 15, 1, NOW(), 1, NOW());
INSERT INTO ai_tts_voice (id, tts_model_id, name, tts_voice, languages, voice_demo, remark, sort, creator, create_date, updater, update_date) VALUES ('TTS_AliyunStreamTTS_0016', 'TTS_AliyunStreamTTS', 'Long Hua - Lively Girl', 'longhua', 'Chinese and Chinese-English mixed', NULL, NULL, 16, 1, NOW(), 1, NOW());
INSERT INTO ai_tts_voice (id, tts_model_id, name, tts_voice, languages, voice_demo, remark, sort, creator, create_date, updater, update_date) VALUES ('TTS_AliyunStreamTTS_0017', 'TTS_AliyunStreamTTS', 'Long Wu - Funny Male', 'longwu', 'Chinese and Chinese-English mixed', NULL, NULL, 17, 1, NOW(), 1, NOW());
INSERT INTO ai_tts_voice (id, tts_model_id, name, tts_voice, languages, voice_demo, remark, sort, creator, create_date, updater, update_date) VALUES ('TTS_AliyunStreamTTS_0018', 'TTS_AliyunStreamTTS', 'Long Dachui - Humorous Male', 'longdachui', 'Chinese and Chinese-English mixed', NULL, NULL, 18, 1, NOW(), 1, NOW());
-- Cantonese series
INSERT INTO ai_tts_voice (id, tts_model_id, name, tts_voice, languages, voice_demo, remark, sort, creator, create_date, updater, update_date) VALUES ('TTS_AliyunStreamTTS_0019', 'TTS_AliyunStreamTTS', 'Long Jiayi - Cantonese Female', 'longjiayi', 'Cantonese and Cantonese-English mixed', NULL, NULL, 19, 1, NOW(), 1, NOW());
INSERT INTO ai_tts_voice (id, tts_model_id, name, tts_voice, languages, voice_demo, remark, sort, creator, create_date, updater, update_date) VALUES ('TTS_AliyunStreamTTS_0020', 'TTS_AliyunStreamTTS', 'Long Tao - Cantonese Female', 'longtao', 'Cantonese and Cantonese-English mixed', NULL, NULL, 20, 1, NOW(), 1, NOW());
