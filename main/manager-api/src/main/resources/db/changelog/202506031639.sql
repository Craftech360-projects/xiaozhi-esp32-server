-- Doubao Stream ASR model provider
DELETE FROM ai_model_provider WHERE id = 'SYSTEM_ASR_DoubaoStreamASR';
INSERT INTO ai_model_provider (id, model_type, provider_code, name, fields, sort, creator, create_date, updater, update_date) VALUES
('SYSTEM_ASR_DoubaoStreamASR', 'ASR', 'doubao_stream', 'Volcano Engine ASR (Streaming)', '[{"key":"appid","label":"Application ID","type":"string"},{"key":"access_token","label":"Access Token","type":"string"},{"key":"cluster","label":"Cluster","type":"string"},{"key":"boosting_table_name","label":"Hotword File Name","type":"string"},{"key":"correct_table_name","label":"Replacement File Name","type":"string"},{"key":"output_dir","label":"Output Directory","type":"string"}]', 3, 1, NOW(), 1, NOW());


-- Doubao Stream ASR model configuration
DELETE FROM ai_model_config WHERE id = 'ASR_DoubaoStreamASR';
INSERT INTO ai_model_config VALUES ('ASR_DoubaoStreamASR', 'ASR', 'DoubaoStreamASR', 'Doubao ASR (Streaming)', FALSE, TRUE, '{"type": "doubao_stream", "appid": "", "access_token": "", "cluster": "volcengine_input_common", "output_dir": "tmp/"}', NULL, NULL, 3, NULL, NULL, NULL, NULL);


-- Update Doubao ASR configuration documentation
UPDATE ai_model_config SET
doc_link = 'https://console.volcengine.com/speech/app',
remark = 'Doubao ASR configuration instructions:
1. Difference between Doubao ASR and Doubao Streaming ASR: Doubao ASR charges per request, Doubao Streaming ASR charges per time
2. Generally per-request charging is cheaper, but Doubao Streaming ASR uses large model technology with better results
3. Need to create application in Volcano Engine console and obtain appid and access_token
4. Supports Chinese speech recognition
5. Requires network connection
6. Output files saved in tmp/ directory
Application steps:
1. Visit https://console.volcengine.com/speech/app
2. Create new application
3. Obtain appid and access_token
4. Fill into configuration file
For hotword settings, refer to: https://www.volcengine.com/docs/6561/155738
' WHERE id = 'ASR_DoubaoASR';

UPDATE ai_model_config SET
doc_link = 'https://console.volcengine.com/speech/app',
remark = 'Doubao ASR configuration instructions:
1. Difference between Doubao ASR and Doubao Streaming ASR: Doubao ASR charges per request, Doubao Streaming ASR charges per time
2. Generally per-request charging is cheaper, but Doubao Streaming ASR uses large model technology with better results
3. Need to create application in Volcano Engine console and obtain appid and access_token
4. Supports Chinese speech recognition
5. Requires network connection
6. Output files saved in tmp/ directory
Application steps:
1. Visit https://console.volcengine.com/speech/app
2. Create new application
3. Obtain appid and access_token
4. Fill into configuration file
For hotword settings, refer to: https://www.volcengine.com/docs/6561/155738
' WHERE id = 'ASR_DoubaoStreamASR';
