-- ============================================
-- Register ESP32 Device for Xiaozhi System
-- Device MAC: 68:25:dd:bc:03:7c
-- ============================================

-- 1. Create default admin user (if not exists)
INSERT INTO sys_user (id, username, password, real_name, email, mobile, status, super_admin, creator, create_date, updater, update_date)
SELECT 1, 'admin', '$2a$10$RMuFXGQ5AtH4wOvkUqyvuecpqUSeoxZYqilXzbz50dceRsga.WYiq', 'Admin User', 'admin@cheeko.ai', '1234567890', 1, 1, 1, NOW(), 1, NOW()
WHERE NOT EXISTS (SELECT 1 FROM sys_user WHERE id = 1);

-- 2. Insert default AI model configurations (if not exists)
-- ASR Model
INSERT INTO ai_model_config (id, model_type, model_code, model_name, is_default, is_enabled, config_json, creator, create_date)
SELECT 'ASR_GroqWhisper', 'ASR', 'groq_whisper', 'Groq Whisper', 1, 1, 
'{"type":"openai","api_key":"${GROQ_API_KEY}","model":"whisper-large-v3-turbo","language":"en"}',
1, NOW()
WHERE NOT EXISTS (SELECT 1 FROM ai_model_config WHERE id = 'ASR_GroqWhisper');

-- VAD Model
INSERT INTO ai_model_config (id, model_type, model_code, model_name, is_default, is_enabled, config_json, creator, create_date)
SELECT 'VAD_SileroVAD', 'VAD', 'SileroVAD', 'Silero VAD', 1, 1,
'{"type":"silero","threshold":0.5,"min_silence_duration_ms":1000}',
1, NOW()
WHERE NOT EXISTS (SELECT 1 FROM ai_model_config WHERE id = 'VAD_SileroVAD');

-- LLM Model (Groq via OpenAI)
INSERT INTO ai_model_config (id, model_type, model_code, model_name, is_default, is_enabled, config_json, creator, create_date)
SELECT 'LLM_Groq', 'LLM', 'openai', 'Groq Llama', 1, 1,
'{"type":"openai","api_key":"${GROQ_API_KEY}","model_name":"llama-3.3-70b-versatile","base_url":"https://api.groq.com/openai/v1","temperature":0.7,"max_tokens":100}',
1, NOW()
WHERE NOT EXISTS (SELECT 1 FROM ai_model_config WHERE id = 'LLM_Groq');

-- TTS Model
INSERT INTO ai_model_config (id, model_type, model_code, model_name, is_default, is_enabled, config_json, creator, create_date)
SELECT 'TTS_ElevenLabs', 'TTS', 'elevenlabs', 'ElevenLabs TTS', 1, 1,
'{"api_key":"sk_52c940fe01587efe7247074e1229bef0d81d32194ab3bb42","voice_id":"vGQNBgLaiM3EdZtxIiuY","model_id":"eleven_turbo_v2_5"}',
1, NOW()
WHERE NOT EXISTS (SELECT 1 FROM ai_model_config WHERE id = 'TTS_ElevenLabs');

-- Intent Model
INSERT INTO ai_model_config (id, model_type, model_code, model_name, is_default, is_enabled, config_json, creator, create_date)
SELECT 'Intent_FunctionCall', 'Intent', 'function_call', 'Function Call Intent', 1, 1,
'{"type":"function_call","functions":["get_weather","play_music","get_news_from_newsnow"]}',
1, NOW()
WHERE NOT EXISTS (SELECT 1 FROM ai_model_config WHERE id = 'Intent_FunctionCall');

-- Memory Model
INSERT INTO ai_model_config (id, model_type, model_code, model_name, is_default, is_enabled, config_json, creator, create_date)
SELECT 'Memory_LocalShort', 'Memory', 'mem_local_short', 'Local Short Memory', 1, 1,
'{"type":"mem_local_short","max_history":10,"enable_summary":true}',
1, NOW()
WHERE NOT EXISTS (SELECT 1 FROM ai_model_config WHERE id = 'Memory_LocalShort');

-- 3. Create default agent configuration
INSERT INTO ai_agent (
    id, user_id, agent_code, agent_name, 
    asr_model_id, vad_model_id, llm_model_id, tts_model_id,
    intent_model_id, memory_model_id,
    system_prompt, language, chat_history_conf,
    exit_commands, is_default,
    creator, create_date, updater, update_date
)
SELECT 
    1, 1, 'cheeko_default', 'Cheeko',
    'ASR_GroqWhisper', 'VAD_SileroVAD', 'LLM_Groq', 'TTS_ElevenLabs',
    'Intent_FunctionCall', 'Memory_LocalShort',
    'PERSONA: You are Cheeko, a friendly, curious, and playful AI friend for children aged 4+. 
You talk in short, clear, and fun sentences. 
You always:
1. Start with a cheerful greeting if it''s the first message in the conversation.
2. Answer in a simple and imaginative way, using age-appropriate words.
3. Praise or encourage the child after they respond.
4. End every single message with a fun or curious follow-up question related to the topic OR a playful new topic if the child seems stuck.
5. Use a warm and positive tone at all times.
6. Avoid scary, negative, or boring content.
7. If telling a story, pause sometimes to ask the child to imagine what happens next.
8. Never say "I don''t know" — instead, make a guess or turn it into a playful thought.
9. Keep the conversation safe and friendly.
Your main goal is to keep the child talking and smiling.',
    'en-US', 2,
    '["exit", "quit", "bye", "goodbye"]', 1,
    1, NOW(), 1, NOW()
WHERE NOT EXISTS (SELECT 1 FROM ai_agent WHERE id = 1);

-- 4. Register the ESP32 device
INSERT INTO ai_device (
    id, mac_address, user_id, agent_id, 
    board, alias, app_version, auto_update, 
    last_connected_at, creator, create_date, updater, update_date
)
SELECT 
    '68:25:dd:bc:03:7c', '68:25:dd:bc:03:7c', 1, 1,
    'doit-ai-01-kit', 'Cheeko Device 1', '1.7.8', 1,
    NOW(), 1, NOW(), 1, NOW()
WHERE NOT EXISTS (SELECT 1 FROM ai_device WHERE mac_address = '68:25:dd:bc:03:7c');

-- 5. Add system parameters
INSERT INTO sys_params (id, param_code, param_value, param_type, remark, creator, create_date, updater, update_date)
SELECT 1, 'server.secret', 'test-secret-key-12345', 1, 'Server authentication secret', 1, NOW(), 1, NOW()
WHERE NOT EXISTS (SELECT 1 FROM sys_params WHERE param_code = 'server.secret');

INSERT INTO sys_params (id, param_code, param_value, param_type, remark, creator, create_date, updater, update_date)
SELECT 2, 'server.websocket.url', 'ws://192.168.1.239:8000/xiaozhi/v1/', 1, 'WebSocket server URL', 1, NOW(), 1, NOW()
WHERE NOT EXISTS (SELECT 1 FROM sys_params WHERE param_code = 'server.websocket.url');

INSERT INTO sys_params (id, param_code, param_value, param_type, remark, creator, create_date, updater, update_date)
SELECT 3, 'server.ota.url', 'http://192.168.1.239:8003/xiaozhi/ota/', 1, 'OTA update URL', 1, NOW(), 1, NOW()
WHERE NOT EXISTS (SELECT 1 FROM sys_params WHERE param_code = 'server.ota.url');

-- 6. Verify registration
SELECT '========================================' as '';
SELECT 'Device Registration Complete!' as Status;
SELECT '========================================' as '';

SELECT 
    d.mac_address as 'Device MAC',
    d.alias as 'Device Name',
    u.username as 'User',
    a.agent_name as 'Agent',
    d.app_version as 'Firmware',
    d.last_connected_at as 'Last Connected'
FROM ai_device d
JOIN sys_user u ON d.user_id = u.id
JOIN ai_agent a ON d.agent_id = a.id
WHERE d.mac_address = '68:25:dd:bc:03:7c';

SELECT '========================================' as '';
SELECT 'Agent Configuration:' as '';
SELECT 
    asr_model_id as 'ASR',
    llm_model_id as 'LLM',
    tts_model_id as 'TTS',
    language as 'Language'
FROM ai_agent WHERE id = 1;

SELECT '========================================' as '';
SELECT 'Next Steps:' as '';
SELECT '1. Restart all backend services' as '';
SELECT '2. Connect ESP32 device' as '';
SELECT '3. Say "Hey Cheeko" to test' as '';
SELECT '4. Check ai_agent_chat_history table for stored conversations' as '';