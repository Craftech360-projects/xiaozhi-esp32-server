-- Update MQTT and server configuration to use correct local IP address
-- This migration updates the default values to use the correct local development IP

-- Update server.websocket to use correct IP
UPDATE `sys_params`
SET param_value = 'ws://192.168.1.113:8000/xiaozhi/v1/'
WHERE param_code = 'server.websocket';

-- Update server.ota to use correct IP
UPDATE `sys_params`
SET param_value = 'http://192.168.1.113:8002/toy/ota/'
WHERE param_code = 'server.ota';

-- Update mqtt.broker to use local IP instead of public IP
UPDATE `sys_params`
SET param_value = '192.168.1.113'
WHERE param_code = 'mqtt.broker';

-- Log the updates for verification
SELECT 'Updated configuration parameters to use local IP 192.168.1.113' as message;
SELECT param_code, param_value, remark
FROM sys_params
WHERE param_code IN ('server.websocket', 'server.ota', 'mqtt.broker');