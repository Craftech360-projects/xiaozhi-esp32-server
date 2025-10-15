-- Add Index-TTS-vLLM streaming TTS provider
DELETE FROM ai_model_provider WHERE id = 'SYSTEM_TTS_IndexStreamTTS';
INSERT INTO ai_model_provider (id, model_type, provider_code, name, fields, sort, creator, create_date, updater, update_date) VALUES
('SYSTEM_TTS_IndexStreamTTS', 'TTS', 'index_stream', 'Index-TTS-vLLM Streaming TTS', '[{"key":"api_url","label":"API Service Address","type":"string"},{"key":"voice","label":"Default Voice","type":"string"},{"key":"audio_format","label":"Audio Format","type":"string"},{"key":"output_dir","label":"Output Directory","type":"string"}]', 16, 1, NOW(), 1, NOW());

-- Add Index-TTS-vLLM streaming TTS model configuration
DELETE FROM ai_model_config WHERE id = 'TTS_IndexStreamTTS';
INSERT INTO ai_model_config VALUES ('TTS_IndexStreamTTS', 'TTS', 'IndexStreamTTS', 'Index-TTS-vLLM Streaming TTS', FALSE, TRUE, '{"type": "index_stream", "api_url": "http://127.0.0.1:11996/tts", "voice": "jay_klee", "audio_format": "pcm", "output_dir": "tmp/"}', NULL, NULL, 19, NULL, NULL, NULL, NULL);

-- Update Index-TTS-vLLM streaming TTS configuration notes
UPDATE ai_model_config SET
doc_link = 'https://github.com/Ksuriuri/index-tts-vllm',
remark = 'Index-TTS-vLLM Streaming TTS Configuration:
1. Index-TTS-vLLM is a vLLM inference service based on Index-TTS project, providing streaming speech synthesis functionality
2. Supports multiple voices with natural voice quality, suitable for various voice interaction scenarios
3. Need to deploy Index-TTS-vLLM service first, then configure API address
4. Supports real-time streaming synthesis with low latency
5. Supports custom voices, can register new voices in project assets folder
Deployment steps:
1. Clone project: git clone https://github.com/Ksuriuri/index-tts-vllm.git
2. Install dependencies: pip install -r requirements.txt
3. Start service: python app.py
4. Service runs on http://127.0.0.1:11996 by default
5. For other voices, register in project assets folder
6. Supports multiple audio formats: pcm, wav, mp3, etc.
For more configuration, see: https://github.com/Ksuriuri/index-tts-vllm/blob/master/README.md
' WHERE id = 'TTS_IndexStreamTTS';

-- Add Index-TTS-vLLM streaming TTS voices
DELETE FROM ai_tts_voice WHERE tts_model_id = 'TTS_IndexStreamTTS';
-- Default voice
INSERT INTO ai_tts_voice (id, tts_model_id, name, tts_voice, languages, voice_demo, remark, sort, creator, create_date, updater, update_date) VALUES ('TTS_IndexStreamTTS_0001', 'TTS_IndexStreamTTS', 'Jay Klee', 'jay_klee', 'Chinese and Chinese-English mixed', NULL, NULL, 1, 1, NOW(), 1, NOW());
