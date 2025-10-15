-- Update ai_model_provider fields, change type dict to string
UPDATE ai_model_provider SET fields = REPLACE(fields::text, '"type": "dict"', '"type": "string"')::json WHERE id NOT IN ('SYSTEM_LLM_fastgpt', 'SYSTEM_TTS_custom');
UPDATE ai_model_provider SET fields = REPLACE(fields::text, '"type":"dict"', '"type": "string"')::json WHERE id NOT IN ('SYSTEM_LLM_fastgpt', 'SYSTEM_TTS_custom');
