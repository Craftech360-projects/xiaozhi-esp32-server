-- Add paddle_speech streaming TTS provider
DELETE FROM ai_model_provider WHERE id = 'SYSTEM_TTS_PaddleSpeechTTS';
INSERT INTO ai_model_provider (id, model_type, provider_code, name, fields, sort, creator, create_date, updater, update_date)
VALUES ('SYSTEM_TTS_PaddleSpeechTTS', 'TTS', 'paddle_speech', 'PaddleSpeechTTS',
'[{"key":"protocol","label":"Protocol Type","type":"string","options":["websocket","http"]},{"key":"url","label":"Service Address","type":"string"},{"key":"spk_id","label":"Voice","type":"int"},{"key":"sample_rate","label":"Sample Rate","type":"float"},{"key":"speed","label":"Speed","type":"float"},{"key":"volume","label":"Volume","type":"float"},{"key":"save_path","label":"Save Path","type":"string"}]',
17, 1, NOW(), 1, NOW());

-- Add paddle_speech streaming TTS model configuration
DELETE FROM ai_model_config WHERE id = 'TTS_PaddleSpeechTTS';
INSERT INTO ai_model_config VALUES ('TTS_PaddleSpeechTTS', 'TTS', 'PaddleSpeechTTS', 'PaddleSpeechTTS', FALSE, TRUE,
'{"type": "paddle_speech", "protocol": "websocket", "url": "ws://127.0.0.1:8092/paddlespeech/tts/streaming", "spk_id": "0", "sample_rate": 24000, "speed": 1.0, "volume": 1.0, "save_path": "./streaming_tts.wav"}',
NULL, NULL, 20, NULL, NULL, NULL, NULL);

-- Update PaddleSpeechTTS configuration notes
UPDATE ai_model_config SET
doc_link = 'https://github.com/PaddlePaddle/PaddleSpeech',
remark = 'PaddleSpeechTTS Configuration:
1. PaddleSpeech is Baidu PaddlePaddle open source speech synthesis tool, supports local offline deployment and model training. PaddlePaddle Baidu framework address: https://www.paddlepaddle.org.cn/
2. Supports WebSocket and HTTP protocols, uses WebSocket for streaming by default (see deployment docs: https://github.com/xinnan-tech/xiaozhi-esp32-server/blob/main/docs/paddlespeech-deploy.md).
3. Need to deploy paddlespeech service locally before use, service runs on ws://127.0.0.1:8092/paddlespeech/tts/streaming by default
4. Supports custom speaker, speed, volume and sample rate.
' WHERE id = 'TTS_PaddleSpeechTTS';

-- Delete old voices and add default voice
DELETE FROM ai_tts_voice WHERE tts_model_id = 'TTS_PaddleSpeechTTS';
INSERT INTO ai_tts_voice (id, tts_model_id, name, tts_voice, languages, voice_demo, remark, sort, creator, create_date, updater, update_date) VALUES ('TTS_PaddleSpeechTTS_0000', 'TTS_PaddleSpeechTTS', 'Default', '0', 'Chinese', NULL, NULL, 1, 1, NOW(), 1, NOW());