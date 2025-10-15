-- Add voiceprint interface address parameter configuration
DELETE FROM sys_params WHERE id = 114;
INSERT INTO sys_params (id, param_code, param_value, value_type, param_type, remark)
VALUES (114, 'server.voice_print', 'null', 'string', 1, 'Voiceprint interface address');