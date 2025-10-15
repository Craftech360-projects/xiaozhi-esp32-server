-- Add Baidu ASR model configuration
delete from ai_model_config where id = 'ASR_BaiduASR';
INSERT INTO ai_model_config VALUES ('ASR_BaiduASR', 'ASR', 'BaiduASR', 'Baidu speech recognition', FALSE, TRUE, '{"type": "baidu", "app_id": "", "api_key": "", "secret_key": "", "dev_pid": 1537, "output_dir": "tmp/"}', NULL, NULL, 7, NULL, NULL, NULL, NULL);


-- Add Baidu ASR provider
delete from ai_model_provider where id = 'SYSTEM_ASR_BaiduASR';
INSERT INTO ai_model_provider (id, model_type, provider_code, name, fields, sort, creator, create_date, updater, update_date) VALUES
('SYSTEM_ASR_BaiduASR', 'ASR', 'baidu', 'Baidu speech recognition', '[{"key":"app_id","label":"Application AppID","type":"string"},{"key":"api_key","label":"API Key","type":"string"},{"key":"secret_key","label":"Secret Key","type":"string"},{"key":"dev_pid","label":"Language parameter","type":"number"},{"key":"output_dir","label":"Output directory","type":"string"}]', 7, 1, NOW(), 1, NOW());


-- Update Baidu ASR configuration description
UPDATE ai_model_config SET
doc_link = 'https://console.bce.baidu.com/ai-engine/old/#/ai/speech/app/list',
remark = 'Baidu ASR configuration description:
1. Visit https://console.bce.baidu.com/ai-engine/old/#/ai/speech/app/list
2. Create new application
3. Get AppID, API Key and Secret Key
4. Fill in configuration file
View resource quotas: https://console.bce.baidu.com/ai-engine/old/#/ai/speech/overview/resource/list
Language parameter description: https://ai.baidu.com/ai-doc/SPEECH/0lbxfnc9b
' WHERE id = 'ASR_BaiduASR';

-- Update Doubao provider fields
update ai_model_provider set fields =
'[{"key":"appid","label":"Application ID","type":"string"},{"key":"access_token","label":"Access token","type":"string"},{"key":"cluster","label":"Cluster","type":"string"},{"key":"boosting_table_name","label":"Hot word file name","type":"string"},{"key":"correct_table_name","label":"Replacement word file name","type":"string"},{"key":"output_dir","label":"Output directory","type":"string"}]'
where id = 'SYSTEM_ASR_DoubaoASR';

-- Update Doubao ASR configuration description
UPDATE ai_model_config SET
doc_link = 'https://console.volcengine.com/speech/app',
remark = 'Doubao ASR configuration description:
1. Need to create application in Volcano Engine console and get appid and access_token
2. Supports Chinese speech recognition
3. Requires network connection
4. Output files saved in tmp/ directory
Application steps:
1. Visit https://console.volcengine.com/speech/app
2. Create new application
3. Get appid and access_token
4. Fill in configuration file
To set hot words, please refer to: https://www.volcengine.com/docs/6561/155738
' WHERE id = 'ASR_DoubaoASR';
