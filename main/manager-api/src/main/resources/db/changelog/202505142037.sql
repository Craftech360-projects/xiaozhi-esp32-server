UPDATE ai_agent_template SET system_prompt = REPLACE(system_prompt, 'I am', 'You are');

DELETE FROM sys_params WHERE id IN (500,501,402);
INSERT INTO sys_params (id, param_code, param_value, value_type, param_type, remark) VALUES (500, 'end_prompt.enable', 'true', 'boolean', 1, 'Enable ending prompt');
INSERT INTO sys_params (id, param_code, param_value, value_type, param_type, remark) VALUES (501, 'end_prompt.prompt', 'Please use "Time flies" as the beginning, use emotional, reluctant words to end this conversation!', 'string', 1, 'Ending prompt text');

INSERT INTO sys_params (id, param_code, param_value, value_type, param_type, remark) VALUES (402, 'plugins.get_weather.api_host', 'mj7p3y7naa.re.qweatherapi.com', 'string', 1, 'Developer API host');
