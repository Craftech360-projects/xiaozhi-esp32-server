-- Add OTA configuration parameters to sys_params table
-- Execute this script to configure the required WebSocket and OTA parameters

-- Insert server.websocket parameter
INSERT INTO `sys_params` (
    `id`,
    `param_code`,
    `param_value`,
    `value_type`,
    `param_type`,
    `remark`,
    `creator`,
    `create_date`,
    `updater`,
    `update_date`
) VALUES (
    1966453680394723331,
    'server.websocket',
    'ws://192.168.1.102:8080',
    'string',
    0,
    'WebSocket cluster addresses for OTA functionality',
    1,
    NOW(),
    1,
    NOW()
) ON DUPLICATE KEY UPDATE
    `param_value` = 'ws://192.168.1.102:8080',
    `updater` = 1,
    `update_date` = NOW();

-- Insert server.ota parameter
INSERT INTO `sys_params` (
    `id`,
    `param_code`,
    `param_value`,
    `value_type`,
    `param_type`,
    `remark`,
    `creator`,
    `create_date`,
    `updater`,
    `update_date`
) VALUES (
    1966453680394723332,
    'server.ota',
    'http://192.168.1.102:8002',
    'string',
    0,
    'OTA server addresses for firmware updates',
    1,
    NOW(),
    1,
    NOW()
) ON DUPLICATE KEY UPDATE
    `param_value` = 'http://192.168.1.102:8002',
    `updater` = 1,
    `update_date` = NOW();

-- Verify the parameters were added
SELECT param_code, param_value, remark
FROM sys_params
WHERE param_code IN ('server.websocket', 'server.ota');