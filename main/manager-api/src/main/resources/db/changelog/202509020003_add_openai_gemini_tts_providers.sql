-- Add OpenAI TTS and Gemini TTS providers to ai_model_provider table
-- This file adds the provider definitions needed for the dashboard dropdown
-- -----------------------------------------------------------------------

-- Add OpenAI TTS provider definition
DELETE FROM ai_model_provider WHERE id = 'SYSTEM_TTS_OpenAITTS';
INSERT INTO ai_model_provider (id, model_type, provider_code, name, fields, sort, creator, create_date, updater, update_date) VALUES
('SYSTEM_TTS_OpenAITTS', 'TTS', 'openai', 'OpenAI TTS Speech Synthesis', '[{"key":"api_key","label":"API Key","type":"string","required":true},{"key":"api_url","label":"API Address","type":"string","required":true},{"key":"model","label":"Model","type":"string","required":true},{"key":"voice","label":"Voice","type":"string","required":true},{"key":"speed","label":"Speed","type":"number"},{"key":"output_dir","label":"Output Directory","type":"string"}]', 18, 1, NOW(), 1, NOW());

-- Add Gemini TTS provider definition
DELETE FROM ai_model_provider WHERE id = 'SYSTEM_TTS_GeminiTTS';
INSERT INTO ai_model_provider (id, model_type, provider_code, name, fields, sort, creator, create_date, updater, update_date) VALUES
('SYSTEM_TTS_GeminiTTS', 'TTS', 'gemini', 'Google Gemini TTS Speech Synthesis', '[{"key":"api_key","label":"API Key","type":"string","required":true},{"key":"api_url","label":"API Address","type":"string","required":true},{"key":"model","label":"Model","type":"string","required":true},{"key":"voice","label":"Voice","type":"string","required":true},{"key":"language","label":"Language","type":"string"},{"key":"output_dir","label":"Output Directory","type":"string"}]', 19, 1, NOW(), 1, NOW());