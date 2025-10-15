-- Add Alibaba Cloud streaming ASR provider
DELETE FROM ai_model_provider WHERE id = 'SYSTEM_ASR_AliyunStreamASR';
INSERT INTO ai_model_provider (id, model_type, provider_code, name, fields, sort, creator, create_date, updater, update_date) VALUES
('SYSTEM_ASR_AliyunStreamASR', 'ASR', 'aliyun_stream', 'Alibaba Cloud ASR (Streaming)', '[{"key":"appkey","label":"App AppKey","type":"string"},{"key":"token","label":"Temporary Token","type":"string"},{"key":"access_key_id","label":"AccessKey ID","type":"string"},{"key":"access_key_secret","label":"AccessKey Secret","type":"string"},{"key":"host","label":"Service Address","type":"string"},{"key":"max_sentence_silence","label":"Sentence Break Detection Time","type":"number"},{"key":"output_dir","label":"Output Directory","type":"string"}]', 6, 1, NOW(), 1, NOW());

-- Add Alibaba Cloud streaming ASR model configuration
DELETE FROM ai_model_config WHERE id = 'ASR_AliyunStreamASR';
INSERT INTO ai_model_config VALUES ('ASR_AliyunStreamASR', 'ASR', 'AliyunStreamASR', 'Alibaba Cloud ASR (Streaming)', FALSE, TRUE, '{"type": "aliyun_stream", "appkey": "", "token": "", "access_key_id": "", "access_key_secret": "", "host": "nls-gateway-cn-shanghai.aliyuncs.com", "max_sentence_silence": 800, "output_dir": "tmp/"}', NULL, NULL, 8, NULL, NULL, NULL, NULL);

-- Update Alibaba Cloud streaming ASR configuration notes
UPDATE ai_model_config SET
doc_link = 'https://nls-portal.console.aliyun.com/',
remark = 'Alibaba Cloud Streaming ASR Configuration:
1. Difference between Alibaba Cloud ASR and Alibaba Cloud (Streaming) ASR: The former is one-time recognition, the latter is real-time streaming recognition
2. Streaming ASR has lower latency and better real-time performance, suitable for voice interaction scenarios
3. Need to create application and obtain authentication info in Alibaba Cloud Intelligent Speech Interaction console
4. Supports real-time Chinese speech recognition, punctuation prediction and inverse text normalization
5. Requires network connection, output files saved in tmp/ directory
Application steps:
1. Visit https://nls-portal.console.aliyun.com/ to enable Intelligent Speech Interaction service
2. Visit https://nls-portal.console.aliyun.com/applist to create project and obtain appkey
3. Visit https://nls-portal.console.aliyun.com/overview to get temporary token (or configure access_key_id and access_key_secret for auto-retrieval)
4. For dynamic token management, recommend configuring access_key_id and access_key_secret
5. max_sentence_silence parameter controls sentence break detection time (milliseconds), default 800ms
For more parameter configuration, see: https://help.aliyun.com/zh/isi/developer-reference/real-time-speech-recognition
' WHERE id = 'ASR_AliyunStreamASR';
