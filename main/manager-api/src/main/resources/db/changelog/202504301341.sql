UPDATE ai_model_provider SET fields = '[{"key": "api_url","label": "API Address","type": "string"},{"key": "voice","label": "Voice","type": "string"},{"key": "output_dir","label": "Output Directory","type": "string"},{"key": "authorization","label": "Authorization","type": "string"},{"key": "appid","label": "Application ID","type": "string"},{"key": "access_token","label": "Access Token","type": "string"},{"key": "cluster","label": "Cluster","type": "string"},{"key": "speed_ratio","label": "Speech Rate","type": "number"},{"key": "volume_ratio","label": "Volume","type": "number"},{"key": "pitch_ratio","label": "Pitch","type": "number"}]'
WHERE id = 'SYSTEM_TTS_doubao';

-- Add Aliyun ASR provider
DELETE FROM ai_model_provider WHERE id = 'SYSTEM_ASR_AliyunASR';
INSERT INTO ai_model_provider (id, model_type, provider_code, name, fields, sort, creator, create_date, updater, update_date) VALUES
('SYSTEM_ASR_AliyunASR', 'ASR', 'aliyun', 'Aliyun Speech Recognition', '[{"key":"appkey","label":"Application AppKey","type":"string"},{"key":"token","label":"Temporary Token","type":"string"},{"key":"access_key_id","label":"AccessKey ID","type":"string"},{"key":"access_key_secret","label":"AccessKey Secret","type":"string"},{"key":"output_dir","label":"Output Directory","type":"string"}]', 5, 1, NOW(), 1, NOW());

-- Add Aliyun ASR model configuration
DELETE FROM ai_model_config WHERE id = 'ASR_AliyunASR';
INSERT INTO ai_model_config VALUES ('ASR_AliyunASR', 'ASR', 'AliyunASR', 'Aliyun Speech Recognition', FALSE, TRUE, '{"type": "aliyun", "appkey": "", "token": "", "access_key_id": "", "access_key_secret": "", "output_dir": "tmp/"}', NULL, NULL, 6, NULL, NULL, NULL, NULL);

-- Update Aliyun ASR model configuration documentation
UPDATE ai_model_config SET
doc_link = 'https://nls-portal.console.aliyun.com/',
remark = 'Aliyun ASR configuration instructions:
1. Visit https://nls-portal.console.aliyun.com/ to enable service
2. Visit https://nls-portal.console.aliyun.com/applist to get appkey
3. Visit https://nls-portal.console.aliyun.com/overview to get token
4. Obtain access_key_id and access_key_secret
5. Fill into configuration file' WHERE id = 'ASR_AliyunASR';

-- Insert firmware type dictionary type
DELETE FROM sys_dict_type WHERE id = 101;
INSERT INTO sys_dict_type (id, dict_type, dict_name, remark, sort, creator, create_date, updater, update_date) VALUES
(101, 'FIRMWARE_TYPE', 'Firmware Type', 'Firmware type dictionary', 0, 1, NOW(), 1, NOW());

-- Insert firmware type dictionary data
DELETE FROM sys_dict_data WHERE dict_type_id = 101;
INSERT INTO sys_dict_data (id, dict_type_id, dict_label, dict_value, remark, sort, creator, create_date, updater, update_date) VALUES
(101001, 101, 'Breadboard New Wiring (WiFi)', 'bread-compact-wifi', 'Breadboard New Wiring (WiFi)', 1, 1, NOW(), 1, NOW()),
(101002, 101, 'Breadboard New Wiring (WiFi) + LCD', 'bread-compact-wifi-lcd', 'Breadboard New Wiring (WiFi) + LCD', 2, 1, NOW(), 1, NOW()),
(101003, 101, 'Breadboard New Wiring (ML307 AT)', 'bread-compact-ml307', 'Breadboard New Wiring (ML307 AT)', 3, 1, NOW(), 1, NOW()),
(101004, 101, 'Breadboard (WiFi) ESP32 DevKit', 'bread-compact-esp32', 'Breadboard (WiFi) ESP32 DevKit', 4, 1, NOW(), 1, NOW()),
(101005, 101, 'Breadboard (WiFi + LCD) ESP32 DevKit', 'bread-compact-esp32-lcd', 'Breadboard (WiFi + LCD) ESP32 DevKit', 5, 1, NOW(), 1, NOW()),
(101006, 101, 'DFRobot Unihiker k10', 'df-k10', 'DFRobot Unihiker k10', 6, 1, NOW(), 1, NOW()),
(101007, 101, 'ESP32 CGC', 'esp32-cgc', 'ESP32 CGC', 7, 1, NOW(), 1, NOW()),
(101008, 101, 'ESP BOX 3', 'esp-box-3', 'ESP BOX 3', 8, 1, NOW(), 1, NOW()),
(101009, 101, 'ESP BOX', 'esp-box', 'ESP BOX', 9, 1, NOW(), 1, NOW()),
(101010, 101, 'ESP BOX Lite', 'esp-box-lite', 'ESP BOX Lite', 10, 1, NOW(), 1, NOW()),
(101011, 101, 'Kevin Box 1', 'kevin-box-1', 'Kevin Box 1', 11, 1, NOW(), 1, NOW()),
(101012, 101, 'Kevin Box 2', 'kevin-box-2', 'Kevin Box 2', 12, 1, NOW(), 1, NOW()),
(101013, 101, 'Kevin C3', 'kevin-c3', 'Kevin C3', 13, 1, NOW(), 1, NOW()),
(101014, 101, 'Kevin SP V3 Dev Board', 'kevin-sp-v3-dev', 'Kevin SP V3 Dev Board', 14, 1, NOW(), 1, NOW()),
(101015, 101, 'Kevin SP V4 Dev Board', 'kevin-sp-v4-dev', 'Kevin SP V4 Dev Board', 15, 1, NOW(), 1, NOW()),
(101016, 101, 'Osprey Tech 3.13 LCD Dev Board', 'kevin-yuying-313lcd', 'Osprey Tech 3.13 LCD Dev Board', 16, 1, NOW(), 1, NOW()),
(101017, 101, 'LCEDA Action ESP32-S3 Dev Board', 'lichuang-dev', 'LCEDA Action ESP32-S3 Dev Board', 17, 1, NOW(), 1, NOW()),
(101018, 101, 'LCEDA Action ESP32-C3 Dev Board', 'lichuang-c3-dev', 'LCEDA Action ESP32-C3 Dev Board', 18, 1, NOW(), 1, NOW()),
(101019, 101, 'Magic Button Magiclick 2.4', 'magiclick-2p4', 'Magic Button Magiclick 2.4', 19, 1, NOW(), 1, NOW()),
(101020, 101, 'Magic Button Magiclick 2.5', 'magiclick-2p5', 'Magic Button Magiclick 2.5', 20, 1, NOW(), 1, NOW()),
(101021, 101, 'Magic Button Magiclick C3', 'magiclick-c3', 'Magic Button Magiclick C3', 21, 1, NOW(), 1, NOW()),
(101022, 101, 'Magic Button Magiclick C3 v2', 'magiclick-c3-v2', 'Magic Button Magiclick C3 v2', 22, 1, NOW(), 1, NOW()),
(101023, 101, 'M5Stack CoreS3', 'm5stack-core-s3', 'M5Stack CoreS3', 23, 1, NOW(), 1, NOW()),
(101024, 101, 'AtomS3 + Echo Base', 'atoms3-echo-base', 'AtomS3 + Echo Base', 24, 1, NOW(), 1, NOW()),
(101025, 101, 'AtomS3R + Echo Base', 'atoms3r-echo-base', 'AtomS3R + Echo Base', 25, 1, NOW(), 1, NOW()),
(101026, 101, 'AtomS3R CAM/M12 + Echo Base', 'atoms3r-cam-m12-echo-base', 'AtomS3R CAM/M12 + Echo Base', 26, 1, NOW(), 1, NOW()),
(101027, 101, 'AtomMatrix + Echo Base', 'atommatrix-echo-base', 'AtomMatrix + Echo Base', 27, 1, NOW(), 1, NOW()),
(101028, 101, 'Shrimp Mini C3', 'xmini-c3', 'Shrimp Mini C3', 28, 1, NOW(), 1, NOW()),
(101029, 101, 'ESP32S3 KORVO2 V3 Dev Board', 'esp32s3-korvo2-v3', 'ESP32S3 KORVO2 V3 Dev Board', 29, 1, NOW(), 1, NOW()),
(101030, 101, 'ESP-SparkBot Dev Board', 'esp-sparkbot', 'ESP-SparkBot Dev Board', 30, 1, NOW(), 1, NOW()),
(101031, 101, 'ESP-Spot-S3', 'esp-spot-s3', 'ESP-Spot-S3', 31, 1, NOW(), 1, NOW()),
(101032, 101, 'Waveshare ESP32-S3-Touch-AMOLED-1.8', 'esp32-s3-touch-amoled-1.8', 'Waveshare ESP32-S3-Touch-AMOLED-1.8', 32, 1, NOW(), 1, NOW()),
(101033, 101, 'Waveshare ESP32-S3-Touch-LCD-1.85C', 'esp32-s3-touch-lcd-1.85c', 'Waveshare ESP32-S3-Touch-LCD-1.85C', 33, 1, NOW(), 1, NOW()),
(101034, 101, 'Waveshare ESP32-S3-Touch-LCD-1.85', 'esp32-s3-touch-lcd-1.85', 'Waveshare ESP32-S3-Touch-LCD-1.85', 34, 1, NOW(), 1, NOW()),
(101035, 101, 'Waveshare ESP32-S3-Touch-LCD-1.46', 'esp32-s3-touch-lcd-1.46', 'Waveshare ESP32-S3-Touch-LCD-1.46', 35, 1, NOW(), 1, NOW()),
(101036, 101, 'Waveshare ESP32-S3-Touch-LCD-3.5', 'esp32-s3-touch-lcd-3.5', 'Waveshare ESP32-S3-Touch-LCD-3.5', 36, 1, NOW(), 1, NOW()),
(101037, 101, 'Potato', 'tudouzi', 'Potato', 37, 1, NOW(), 1, NOW()),
(101038, 101, 'LILYGO T-Circle-S3', 'lilygo-t-circle-s3', 'LILYGO T-Circle-S3', 38, 1, NOW(), 1, NOW()),
(101039, 101, 'LILYGO T-CameraPlus-S3', 'lilygo-t-cameraplus-s3', 'LILYGO T-CameraPlus-S3', 39, 1, NOW(), 1, NOW()),
(101040, 101, 'Movecall Moji XiaoZhi AI Derivative', 'movecall-moji-esp32s3', 'Movecall Moji XiaoZhi AI Derivative', 40, 1, NOW(), 1, NOW()),
(101041, 101, 'Movecall CuiCan AI Pendant', 'movecall-cuican-esp32s3', 'Movecall CuiCan AI Pendant', 41, 1, NOW(), 1, NOW()),
(101042, 101, 'Alientek DNESP32S3 Dev Board', 'atk-dnesp32s3', 'Alientek DNESP32S3 Dev Board', 42, 1, NOW(), 1, NOW()),
(101043, 101, 'Alientek DNESP32S3-BOX', 'atk-dnesp32s3-box', 'Alientek DNESP32S3-BOX', 43, 1, NOW(), 1, NOW()),
(101044, 101, 'Dudu Dev Board CHATX (wifi)', 'du-chatx', 'Dudu Dev Board CHATX (wifi)', 44, 1, NOW(), 1, NOW()),
(101045, 101, 'Taiji Pi esp32s3', 'taiji-pi-s3', 'Taiji Pi esp32s3', 45, 1, NOW(), 1, NOW()),
(101046, 101, 'Unnamed Tech XingZhi 0.85 (WIFI)', 'xingzhi-cube-0.85tft-wifi', 'Unnamed Tech XingZhi 0.85 (WIFI)', 46, 1, NOW(), 1, NOW()),
(101047, 101, 'Unnamed Tech XingZhi 0.85 (ML307)', 'xingzhi-cube-0.85tft-ml307', 'Unnamed Tech XingZhi 0.85 (ML307)', 47, 1, NOW(), 1, NOW()),
(101048, 101, 'Unnamed Tech XingZhi 0.96 (WIFI)', 'xingzhi-cube-0.96oled-wifi', 'Unnamed Tech XingZhi 0.96 (WIFI)', 48, 1, NOW(), 1, NOW()),
(101049, 101, 'Unnamed Tech XingZhi 0.96 (ML307)', 'xingzhi-cube-0.96oled-ml307', 'Unnamed Tech XingZhi 0.96 (ML307)', 49, 1, NOW(), 1, NOW()),
(101050, 101, 'Unnamed Tech XingZhi 1.54 (WIFI)', 'xingzhi-cube-1.54tft-wifi', 'Unnamed Tech XingZhi 1.54 (WIFI)', 50, 1, NOW(), 1, NOW()),
(101051, 101, 'Unnamed Tech XingZhi 1.54 (ML307)', 'xingzhi-cube-1.54tft-ml307', 'Unnamed Tech XingZhi 1.54 (ML307)', 51, 1, NOW(), 1, NOW()),
(101052, 101, 'SenseCAP Watcher', 'sensecap-watcher', 'SenseCAP Watcher', 52, 1, NOW(), 1, NOW()),
(101053, 101, 'DOIT AI Companion Box', 'doit-s3-aibox', 'DOIT AI Companion Box', 53, 1, NOW(), 1, NOW()),
(101054, 101, 'MixGo Nova', 'mixgo-nova', 'MixGo Nova', 54, 1, NOW(), 1, NOW());
