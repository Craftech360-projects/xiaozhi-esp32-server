-- =====================================================
-- Data Population Script - Essential System Data
-- Translated to English
-- =====================================================

SET FOREIGN_KEY_CHECKS = 0;

-- =====================================================
-- AI Model Providers Data
-- =====================================================
DELETE FROM `ai_model_provider`;
INSERT INTO `ai_model_provider` (`id`, `model_type`, `provider_code`, `name`, `fields`, `sort`, `creator`, `create_date`, `updater`, `update_date`) VALUES

-- VAD Model Providers
('SYSTEM_VAD_SileroVAD', 'VAD', 'silero', 'SileroVAD Voice Activity Detection', '[{"key":"threshold","label":"Detection threshold","type":"number"},{"key":"model_dir","label":"Model directory","type":"string"},{"key":"min_silence_duration_ms","label":"Minimum silence duration","type":"number"}]', 1, 1, NOW(), 1, NOW()),

-- ASR Model Providers
('SYSTEM_ASR_FunASR', 'ASR', 'fun_local', 'FunASR Speech Recognition', '[{"key":"model_dir","label":"Model directory","type":"string"},{"key":"output_dir","label":"Output directory","type":"string"}]', 1, 1, NOW(), 1, NOW()),
('SYSTEM_ASR_SherpaASR', 'ASR', 'sherpa_onnx_local', 'SherpaASR Speech Recognition', '[{"key":"model_dir","label":"Model directory","type":"string"},{"key":"output_dir","label":"Output directory","type":"string"}]', 2, 1, NOW(), 1, NOW()),
('SYSTEM_ASR_DoubaoASR', 'ASR', 'doubao', 'Volcano Engine Speech Recognition', '[{"key":"appid","label":"Application ID","type":"string"},{"key":"access_token","label":"Access token","type":"string"},{"key":"cluster","label":"Cluster","type":"string"},{"key":"output_dir","label":"Output directory","type":"string"}]', 3, 1, NOW(), 1, NOW()),

-- LLM Model Providers
('SYSTEM_LLM_openai', 'LLM', 'openai', 'OpenAI Interface', '[{"key":"base_url","label":"Base URL","type":"string"},{"key":"model_name","label":"Model name","type":"string"},{"key":"api_key","label":"API key","type":"string"},{"key":"temperature","label":"Temperature","type":"number"},{"key":"max_tokens","label":"Max tokens","type":"number"},{"key":"top_p","label":"Top P value","type":"number"},{"key":"top_k","label":"Top K value","type":"number"},{"key":"frequency_penalty","label":"Frequency penalty","type":"number"}]', 1, 1, NOW(), 1, NOW()),
('SYSTEM_LLM_AliBL', 'LLM', 'AliBL', 'Alibaba Bailian Interface', '[{"key":"base_url","label":"Base URL","type":"string"},{"key":"app_id","label":"Application ID","type":"string"},{"key":"api_key","label":"API key","type":"string"},{"key":"is_no_prompt","label":"Disable local prompt","type":"boolean"},{"key":"ali_memory_id","label":"Memory ID","type":"string"}]', 2, 1, NOW(), 1, NOW()),
('SYSTEM_LLM_ollama', 'LLM', 'ollama', 'Ollama Interface', '[{"key":"model_name","label":"Model name","type":"string"},{"key":"base_url","label":"Service address","type":"string"}]', 3, 1, NOW(), 1, NOW()),
('SYSTEM_LLM_dify', 'LLM', 'dify', 'Dify Interface', '[{"key":"base_url","label":"Base URL","type":"string"},{"key":"api_key","label":"API key","type":"string"},{"key":"mode","label":"Chat mode","type":"string"}]', 4, 1, NOW(), 1, NOW()),
('SYSTEM_LLM_gemini', 'LLM', 'gemini', 'Gemini Interface', '[{"key":"api_key","label":"API key","type":"string"},{"key":"model_name","label":"Model name","type":"string"},{"key":"http_proxy","label":"HTTP proxy","type":"string"},{"key":"https_proxy","label":"HTTPS proxy","type":"string"}]', 5, 1, NOW(), 1, NOW()),
('SYSTEM_LLM_coze', 'LLM', 'coze', 'Coze Interface', '[{"key":"bot_id","label":"Bot ID","type":"string"},{"key":"user_id","label":"User ID","type":"string"},{"key":"personal_access_token","label":"Personal access token","type":"string"}]', 6, 1, NOW(), 1, NOW()),
('SYSTEM_LLM_fastgpt', 'LLM', 'fastgpt', 'FastGPT Interface', '[{"key":"base_url","label":"Base URL","type":"string"},{"key":"api_key","label":"API key","type":"string"},{"key":"variables","label":"Variables","type":"dict","dict_name":"variables"}]', 7, 1, NOW(), 1, NOW()),
('SYSTEM_LLM_xinference', 'LLM', 'xinference', 'Xinference Interface', '[{"key":"model_name","label":"Model name","type":"string"},{"key":"base_url","label":"Service address","type":"string"}]', 8, 1, NOW(), 1, NOW()),
('SYSTEM_LLM_doubao', 'LLM', 'doubao', 'Volcano Engine LLM', '[{"key":"base_url","label":"Base URL","type":"string"},{"key":"model_name","label":"Model name","type":"string"},{"key":"api_key","label":"API key","type":"string"}]', 9, 1, NOW(), 1, NOW()),
('SYSTEM_LLM_chatglm', 'LLM', 'chatglm', 'ChatGLM Interface', '[{"key":"model_name","label":"Model name","type":"string"},{"key":"url","label":"Service address","type":"string"},{"key":"api_key","label":"API key","type":"string"}]', 10, 1, NOW(), 1, NOW()),

-- TTS Model Providers
('SYSTEM_TTS_edge', 'TTS', 'edge', 'Edge TTS', '[{"key":"voice","label":"Voice","type":"string"},{"key":"output_dir","label":"Output directory","type":"string"}]', 1, 1, NOW(), 1, NOW()),
('SYSTEM_TTS_doubao', 'TTS', 'doubao', 'Volcano Engine TTS', '[{"key":"api_url","label":"API URL","type":"string"},{"key":"voice","label":"Voice","type":"string"},{"key":"output_dir","label":"Output directory","type":"string"},{"key":"authorization","label":"Authorization","type":"string"},{"key":"appid","label":"Application ID","type":"string"},{"key":"access_token","label":"Access token","type":"string"},{"key":"cluster","label":"Cluster","type":"string"}]', 2, 1, NOW(), 1, NOW()),
('SYSTEM_TTS_openai', 'TTS', 'openai', 'OpenAI TTS', '[{"key":"api_key","label":"API key","type":"string"},{"key":"api_url","label":"API URL","type":"string"},{"key":"model","label":"Model","type":"string"},{"key":"voice","label":"Voice","type":"string"},{"key":"speed","label":"Speed","type":"number"},{"key":"output_dir","label":"Output directory","type":"string"}]', 11, 1, NOW(), 1, NOW()),

-- Memory Model Providers
('SYSTEM_Memory_mem0ai', 'Memory', 'mem0ai', 'Mem0AI Memory', '[{"key":"api_key","label":"API key","type":"string"}]', 1, 1, NOW(), 1, NOW()),
('SYSTEM_Memory_nomem', 'Memory', 'nomem', 'No Memory', '[]', 2, 1, NOW(), 1, NOW()),
('SYSTEM_Memory_mem_local_short', 'Memory', 'mem_local_short', 'Local Short Memory', '[]', 3, 1, NOW(), 1, NOW()),

-- Intent Model Providers
('SYSTEM_Intent_nointent', 'Intent', 'nointent', 'No Intent Recognition', '[]', 1, 1, NOW(), 1, NOW()),
('SYSTEM_Intent_intent_llm', 'Intent', 'intent_llm', 'LLM Intent Recognition', '[{"key":"llm","label":"LLM model","type":"string"}]', 2, 1, NOW(), 1, NOW()),
('SYSTEM_Intent_function_call', 'Intent', 'function_call', 'Function Call Intent Recognition', '[{"key":"functions","label":"Function list","type":"dict","dict_name":"functions"}]', 3, 1, NOW(), 1, NOW());

-- =====================================================
-- AI Model Configurations
-- =====================================================
DELETE FROM `ai_model_config`;
INSERT INTO `ai_model_config` VALUES

-- VAD Configurations
('VAD_SileroVAD', 'VAD', 'SileroVAD', 'SileroVAD', 1, 1, '{"type": "silero", "threshold": 0.5, "model_dir": "./models/silero_vad_onnx", "min_silence_duration_ms": 500}', 'https://github.com/snakers4/silero-vad', 'SileroVAD voice activity detection configuration', 1, NULL, NULL, NULL, NULL),

-- ASR Configurations
('ASR_FunASR', 'ASR', 'FunASR', 'FunASR', 1, 1, '{"type": "fun_local", "model_dir": "./models/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch", "output_dir": "./output/asr"}', 'https://github.com/alibaba-damo-academy/FunASR', 'FunASR speech recognition configuration', 1, NULL, NULL, NULL, NULL),

-- LLM Configurations
('LLM_openai', 'LLM', 'openai', 'OpenAI GPT', 0, 1, '{"type": "openai", "base_url": "https://api.openai.com/v1", "model_name": "gpt-3.5-turbo", "api_key": "your-api-key", "temperature": 0.7, "max_tokens": 1000}', 'https://platform.openai.com/docs', 'OpenAI GPT model configuration', 1, NULL, NULL, NULL, NULL),

-- TTS Configurations
('TTS_edge', 'TTS', 'edge', 'Edge TTS', 1, 1, '{"type": "edge", "voice": "zh-CN-XiaoxiaoNeural", "output_dir": "./output/tts"}', 'https://github.com/rany2/edge-tts', 'Microsoft Edge TTS configuration', 1, NULL, NULL, NULL, NULL),

-- Memory Configurations
('Memory_local_short', 'Memory', 'mem_local_short', 'Local Short Memory', 1, 1, '{"type": "mem_local_short"}', NULL, 'Local short-term memory configuration', 1, NULL, NULL, NULL, NULL),

-- Intent Configurations
('Intent_nointent', 'Intent', 'nointent', 'No Intent', 1, 1, '{"type": "nointent"}', NULL, 'No intent recognition configuration', 1, NULL, NULL, NULL, NULL);

-- =====================================================
-- TTS Voice Configurations
-- =====================================================
DELETE FROM `ai_tts_voice`;
INSERT INTO `ai_tts_voice` VALUES
('TTS_edge_xiaoxiao', 'TTS_edge', 'Xiaoxiao', 'zh-CN-XiaoxiaoNeural', 'Chinese', NULL, 'Female voice', 1, 1, NOW(), 1, NOW()),
('TTS_edge_yunxi', 'TTS_edge', 'Yunxi', 'zh-CN-YunxiNeural', 'Chinese', NULL, 'Male voice', 2, 1, NOW(), 1, NOW()),
('TTS_edge_xiaoyi', 'TTS_edge', 'Xiaoyi', 'zh-CN-XiaoyiNeural', 'Chinese', NULL, 'Female voice', 3, 1, NOW(), 1, NOW());

-- =====================================================
-- System Parameters
-- =====================================================
DELETE FROM `sys_params`;
INSERT INTO `sys_params` (`id`, `param_code`, `param_value`, `param_type`, `remark`, `creator`, `create_date`, `updater`, `update_date`) VALUES
(1, 'SYSTEM_VERSION', '1.0.0', 0, 'System version', 1, NOW(), 1, NOW()),
(2, 'DEFAULT_LANGUAGE', 'zh-CN', 0, 'Default system language', 1, NOW(), 1, NOW()),
(3, 'ENABLE_REGISTRATION', 'true', 0, 'Enable user registration', 1, NOW(), 1, NOW()),
(4, 'MAX_UPLOAD_SIZE', '10485760', 0, 'Maximum upload file size (bytes)', 1, NOW(), 1, NOW()),
(5, 'SESSION_TIMEOUT', '3600', 0, 'Session timeout (seconds)', 1, NOW(), 1, NOW());

-- =====================================================
-- Dictionary Types
-- =====================================================
DELETE FROM `sys_dict_type`;
INSERT INTO `sys_dict_type` (`id`, `dict_type`, `dict_name`, `remark`, `sort`, `creator`, `create_date`, `updater`, `update_date`) VALUES
(1, 'DEVICE_STATUS', 'Device Status', 'Device status dictionary', 1, 1, NOW(), 1, NOW()),
(2, 'USER_STATUS', 'User Status', 'User status dictionary', 2, 1, NOW(), 1, NOW()),
(3, 'LANGUAGE_CODE', 'Language Code', 'Language code dictionary', 3, 1, NOW(), 1, NOW()),
(4, 'MODEL_TYPE', 'Model Type', 'AI model type dictionary', 4, 1, NOW(), 1, NOW());

-- =====================================================
-- Dictionary Data
-- =====================================================
DELETE FROM `sys_dict_data`;
INSERT INTO `sys_dict_data` (`id`, `dict_type_id`, `dict_label`, `dict_value`, `remark`, `sort`, `creator`, `create_date`, `updater`, `update_date`) VALUES
-- Device Status
(1, 1, 'Online', '1', 'Device is online', 1, 1, NOW(), 1, NOW()),
(2, 1, 'Offline', '0', 'Device is offline', 2, 1, NOW(), 1, NOW()),

-- User Status
(3, 2, 'Normal', '1', 'User is active', 1, 1, NOW(), 1, NOW()),
(4, 2, 'Disabled', '0', 'User is disabled', 2, 1, NOW(), 1, NOW()),

-- Language Codes
(5, 3, 'Chinese', 'zh-CN', 'Simplified Chinese', 1, 1, NOW(), 1, NOW()),
(6, 3, 'English', 'en-US', 'English (US)', 2, 1, NOW(), 1, NOW()),

-- Model Types
(7, 4, 'Speech Recognition', 'ASR', 'Automatic Speech Recognition', 1, 1, NOW(), 1, NOW()),
(8, 4, 'Text to Speech', 'TTS', 'Text to Speech', 2, 1, NOW(), 1, NOW()),
(9, 4, 'Large Language Model', 'LLM', 'Large Language Model', 3, 1, NOW(), 1, NOW()),
(10, 4, 'Voice Activity Detection', 'VAD', 'Voice Activity Detection', 4, 1, NOW(), 1, NOW()),
(11, 4, 'Memory', 'Memory', 'Memory System', 5, 1, NOW(), 1, NOW()),
(12, 4, 'Intent Recognition', 'Intent', 'Intent Recognition', 6, 1, NOW(), 1, NOW());

-- =====================================================
-- Default AI Agent Template
-- =====================================================
DELETE FROM `ai_agent_template`;
INSERT INTO `ai_agent_template` VALUES
('default_template', 'DEFAULT', 'Default AI Agent', 'ASR_FunASR', 'VAD_SileroVAD', 'LLM_openai', 'TTS_edge', 'TTS_edge_xiaoxiao', 'Memory_local_short', 'Intent_nointent', 'You are a helpful AI assistant. Please respond to user queries in a friendly and informative manner.', 'zh-CN', 'Chinese', 1, 1, NOW(), 1, NOW());

SET FOREIGN_KEY_CHECKS = 1;

SELECT 'Data population completed successfully!' as message;