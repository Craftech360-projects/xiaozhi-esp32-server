-- Register ESP32 Device in Database
-- This script sets up the ESP32 device for data persistence

-- 1. Create a default admin user if it doesn't exist
INSERT INTO sys_user (id, username, password, real_name, email, mobile, status, super_admin, creator, create_date, updater, update_date)
SELECT 1, 'admin', '$2a$10$RMuFXGQ5AtH4wOvkUqyvuecpqUSeoxZYqilXzbz50dceRsga.WYiq', 'Admin User', 'admin@cheeko.ai', '1234567890', 1, 1, 1, NOW(), 1, NOW()
WHERE NOT EXISTS (SELECT 1 FROM sys_user WHERE id = 1);

-- 2. Create a default agent configuration
INSERT INTO ai_agent (id, user_id, agent_code, agent_name, asr_model_id, vad_model_id, llm_model_id, tts_model_id, tts_voice_id, 
                      intent_model_id, memory_model_id, summary_memory, system_prompt, language, chat_history_conf, 
                      exit_commands, voiceprint, is_default, creator, create_date, updater, update_date)
SELECT 1, 1, 'cheeko_default', 'Cheeko', 
       'ASR_SherpaZipformerGigaspeechEN', 'VAD_SileroVAD', 'LLM_openai', 'TTS_elevenlabs', 'vGQNBgLaiM3EdZtxIiuY',
       'Intent_function_call', 'Memory_mem_local_short', NULL,
       'PERSONA: You are Cheeko, a friendly, curious, and playful AI friend for children aged 4+.',
       'en-US', 2, 
       '["exit", "quit", "bye", "goodbye"]', NULL, 1, 1, NOW(), 1, NOW()
WHERE NOT EXISTS (SELECT 1 FROM ai_agent WHERE id = 1);

-- 3. Register the ESP32 device
INSERT INTO ai_device (id, mac_address, user_id, agent_id, board, alias, app_version, auto_update, last_connected_at, creator, create_date, updater, update_date)
SELECT 1, '68:25:dd:bc:03:7c', 1, 1, 'doit-ai-01-kit', 'Cheeko Device 1', '1.7.8', 1, NOW(), 1, NOW(), 1, NOW()
WHERE NOT EXISTS (SELECT 1 FROM ai_device WHERE mac_address = '68:25:dd:bc:03:7c');

-- 4. Add system parameters for server configuration
INSERT INTO sys_params (id, param_code, param_value, param_type, remark, creator, create_date, updater, update_date)
SELECT 1, 'server.secret', 'test-secret-key-12345', 1, 'Server authentication secret', 1, NOW(), 1, NOW()
WHERE NOT EXISTS (SELECT 1 FROM sys_params WHERE param_code = 'server.secret');

INSERT INTO sys_params (id, param_code, param_value, param_type, remark, creator, create_date, updater, update_date)
SELECT 2, 'server.websocket.url', 'ws://192.168.1.239:8000/xiaozhi/v1/', 1, 'WebSocket server URL', 1, NOW(), 1, NOW()
WHERE NOT EXISTS (SELECT 1 FROM sys_params WHERE param_code = 'server.websocket.url');

INSERT INTO sys_params (id, param_code, param_value, param_type, remark, creator, create_date, updater, update_date)
SELECT 3, 'server.ota.url', 'http://192.168.1.239:8003/xiaozhi/ota/', 1, 'OTA update URL', 1, NOW(), 1, NOW()
WHERE NOT EXISTS (SELECT 1 FROM sys_params WHERE param_code = 'server.ota.url');

-- 5. Verify registration
SELECT 'Device Registration Complete!' as Status;
SELECT 
    d.mac_address as 'Device MAC',
    d.alias as 'Device Name',
    u.username as 'User',
    a.agent_name as 'Agent',
    d.last_connected_at as 'Last Connected'
FROM ai_device d
JOIN sys_user u ON d.user_id = u.id
JOIN ai_agent a ON d.agent_id = a.id
WHERE d.mac_address = '68:25:dd:bc:03:7c';