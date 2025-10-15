-- VLLM model configuration
DELETE FROM ai_model_config WHERE id = 'VLLM_QwenVLVLLM';
INSERT INTO ai_model_config VALUES ('VLLM_QwenVLVLLM', 'VLLM', 'QwenVLVLLM', 'Qwen Vision Model', FALSE, TRUE, '{"type": "openai", "model_name": "qwen2.5-vl-3b-instruct", "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1", "api_key": "your_api_key"}', NULL, NULL, 2, NULL, NULL, NULL, NULL);

-- Update documentation
UPDATE ai_model_config SET
doc_link = 'https://bailian.console.aliyun.com/?tab=api#/api/?type=model&url=https%3A%2F%2Fhelp.aliyun.com%2Fdocument_detail%2F2845564.html&renderType=iframe',
remark = 'Qwen Vision Model configuration instructions:
1. Visit https://bailian.console.aliyun.com/?tab=model#/api-key
2. Register and obtain API key
3. Fill into configuration file' WHERE id = 'VLLM_QwenVLVLLM';

-- Delete parameters, these moved to python config file
DELETE FROM sys_params WHERE id IN (113,114);
