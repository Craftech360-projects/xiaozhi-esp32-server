-- OpenAI ASR model provider
DELETE FROM ai_model_provider WHERE id = 'SYSTEM_ASR_OpenaiASR';
INSERT INTO ai_model_provider (id, model_type, provider_code, name, fields, sort, creator, create_date, updater, update_date) VALUES
('SYSTEM_ASR_OpenaiASR', 'ASR', 'openai', 'OpenAI Speech Recognition', '[{"key": "base_url", "type": "string", "label": "Base URL"}, {"key": "model_name", "type": "string", "label": "Model Name"}, {"key": "api_key", "type": "string", "label": "API Key"}, {"key": "output_dir", "type": "string", "label": "Output Directory"}]', 9, 1, NOW(), 1, NOW());


-- OpenAI ASR model configuration
DELETE FROM ai_model_config WHERE id = 'ASR_OpenaiASR';
INSERT INTO ai_model_config VALUES ('ASR_OpenaiASR', 'ASR', 'OpenaiASR', 'OpenAI Speech Recognition', FALSE, TRUE, '{"type": "openai", "api_key": "", "base_url": "https://api.openai.com/v1/audio/transcriptions", "model_name": "gpt-4o-mini-transcribe", "output_dir": "tmp/"}', NULL, NULL, 9, NULL, NULL, NULL, NULL);

-- Groq ASR model configuration
DELETE FROM ai_model_config WHERE id = 'ASR_GroqASR';
INSERT INTO ai_model_config VALUES ('ASR_GroqASR', 'ASR', 'GroqASR', 'Groq Speech Recognition', FALSE, TRUE, '{"type": "openai", "api_key": "", "base_url": "https://api.groq.com/openai/v1/audio/transcriptions", "model_name": "whisper-large-v3-turbo", "output_dir": "tmp/"}', NULL, NULL, 10, NULL, NULL, NULL, NULL);


-- Update OpenAI ASR configuration notes
UPDATE ai_model_config SET
doc_link = 'https://platform.openai.com/docs/api-reference/audio/createTranscription',
remark = 'OpenAI ASR Configuration:
1. Need to create organization and obtain api_key on OpenAI platform
2. Supports multiple speech recognition languages including Chinese, English, Japanese, Korean, see docs https://platform.openai.com/docs/guides/speech-to-text
3. Requires network connection
4. Output files saved in tmp/ directory
Application steps:
**OpenAI ASR Application Steps:**
1. Login to OpenAI Platform: https://auth.openai.com/log-in
2. Create api-key: https://platform.openai.com/settings/organization/api-keys
3. Can choose model gpt-4o-transcribe or GPT-4o mini Transcribe
' WHERE id = 'ASR_OpenaiASR';

-- Update Groq ASR configuration notes
UPDATE ai_model_config SET
doc_link = 'https://console.groq.com/docs/speech-to-text',
remark = 'Groq ASR Configuration:
1. Login to groq Console: https://console.groq.com/home
2. Create api-key: https://console.groq.com/keys
3. Can choose model whisper-large-v3-turbo or whisper-large-v3 (distil-whisper-large-v3-en only supports English transcription)
' WHERE id = 'ASR_GroqASR';