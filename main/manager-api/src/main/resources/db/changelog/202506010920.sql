-- VLLM model provider
DELETE FROM ai_model_provider WHERE id = 'SYSTEM_VLLM_openai';
INSERT INTO ai_model_provider (id, model_type, provider_code, name, fields, sort, creator, create_date, updater, update_date) VALUES
('SYSTEM_VLLM_openai', 'VLLM', 'openai', 'OpenAI Interface', '[{"key":"base_url","label":"Base URL","type":"string"},{"key":"model_name","label":"Model Name","type":"string"},{"key":"api_key","label":"API Key","type":"string"}]', 9, 1, NOW(), 1, NOW());

-- VLLM model configuration
DELETE FROM ai_model_config WHERE id = 'VLLM_ChatGLMVLLM';
INSERT INTO ai_model_config VALUES ('VLLM_ChatGLMVLLM', 'VLLM', 'ChatGLMVLLM', 'Zhipu Vision AI', TRUE, TRUE, '{"type": "openai", "model_name": "glm-4v-flash", "base_url": "https://open.bigmodel.cn/api/paas/v4/", "api_key": "your_api_key"}', NULL, NULL, 1, NULL, NULL, NULL, NULL);

-- Update documentation
UPDATE ai_model_config SET
doc_link = 'https://bigmodel.cn/usercenter/proj-mgmt/apikeys',
remark = 'Zhipu Vision AI configuration instructions:
1. Visit https://bigmodel.cn/usercenter/proj-mgmt/apikeys
2. Register and obtain API key
3. Fill into configuration file' WHERE id = 'VLLM_ChatGLMVLLM';


-- Add parameters
INSERT INTO sys_params (id, param_code, param_value, value_type, param_type, remark) VALUES (113, 'server.http_port', '8003', 'number', 1, 'HTTP service port for vision analysis interface');
INSERT INTO sys_params (id, param_code, param_value, value_type, param_type, remark) VALUES (114, 'server.vision_explain', 'null', 'string', 1, 'Vision analysis interface address for device, multiple separated by semicolon');

-- Agent table add VLLM model configuration
ALTER TABLE ai_agent
ADD COLUMN vllm_model_id VARCHAR(32) NULL DEFAULT 'VLLM_ChatGLMVLLM';

COMMENT ON COLUMN ai_agent.vllm_model_id IS 'Vision model identifier';

-- Agent template table add VLLM model configuration
ALTER TABLE ai_agent_template
ADD COLUMN vllm_model_id VARCHAR(32) NULL DEFAULT 'VLLM_ChatGLMVLLM';

COMMENT ON COLUMN ai_agent_template.vllm_model_id IS 'Vision model identifier';
