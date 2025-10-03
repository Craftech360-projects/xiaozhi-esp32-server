-- Add MQTT broker configuration parameters
-- These parameters are used by the OTA endpoint to provide MQTT credentials to mobile app and ESP32 devices

-- Delete existing if any to avoid duplicates
DELETE FROM `sys_params` WHERE param_code IN ('mqtt.broker', 'mqtt.port', 'mqtt.signature_key');
DELETE FROM `sys_params` WHERE id IN (102, 106, 107);

-- Insert MQTT configuration parameters
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES
(102, 'server.secret', 'da11d988-f105-4e71-b095-da62ada82189', 'string', 1, '服务器密钥'),
(106, 'server.websocket', 'ws://192.168.1.236:8000/xiaozhi/v1/', 'string', 1, 'websocket地址，多个用;分隔'),
(107, 'server.ota', 'http://192.168.1.236:8002/toy/ota/', 'string', 1, 'ota地址'),
(600, 'mqtt.broker', '139.59.5.142', 'string', 1, 'MQTT broker IP address or hostname'),
(601, 'mqtt.port', '1883', 'string', 1, 'MQTT broker port'),
(602, 'mqtt.signature_key', 'test-signature-key-12345', 'string', 1, 'MQTT password signature key for HMAC-SHA256');
