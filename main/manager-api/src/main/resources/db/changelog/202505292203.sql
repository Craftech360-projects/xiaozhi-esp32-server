-- Configure intent_llm and function_call without function list
UPDATE ai_model_provider SET fields =  '[{"key":"llm","label":"LLM Model","type":"string"}]' WHERE  id = 'SYSTEM_Intent_intent_llm';
UPDATE ai_model_provider SET fields =  '[]' WHERE  id = 'SYSTEM_Intent_function_call';
UPDATE ai_model_config SET config_json =  '{"type": "intent_llm", "llm": "LLM_ChatGLMLLM"}' WHERE  id = 'Intent_intent_llm';
UPDATE ai_model_config SET config_json = '{"type": "function_call"}' WHERE id = 'Intent_function_call';


DELETE FROM ai_model_provider WHERE model_type = 'Plugin';
-- Weather query plugin
INSERT INTO ai_model_provider (id, model_type, provider_code, name, fields, sort, creator, create_date, updater, update_date)
VALUES ('SYSTEM_PLUGIN_WEATHER', 'Plugin', 'get_weather', 'Weather Query',
        '[]', 10, 0, NOW(), 0, NOW());

-- Server music playback plugin
INSERT INTO ai_model_provider (id, model_type, provider_code, name, fields, sort, creator, create_date, updater, update_date)
VALUES ('SYSTEM_PLUGIN_MUSIC', 'Plugin', 'play_music', 'Server Music Playback',
        '[]', 20, 0, NOW(), 0, NOW());

-- ChinaNews news plugin
INSERT INTO ai_model_provider (id, model_type, provider_code, name, fields, sort, creator, create_date, updater, update_date)
VALUES ('SYSTEM_PLUGIN_NEWS_CHINANEWS', 'Plugin', 'get_news_from_chinanews', 'ChinaNews',
        '[]', 30, 0, NOW(), 0, NOW());

-- NewsNow aggregation plugin
INSERT INTO ai_model_provider (id, model_type, provider_code, name, fields, sort, creator, create_date, updater, update_date)
VALUES ('SYSTEM_PLUGIN_NEWS_NEWSNOW', 'Plugin', 'get_news_from_newsnow', 'NewsNow Aggregation',
        '[]', 40, 0, NOW(), 0, NOW());

-- HomeAssistant state query plugin
INSERT INTO ai_model_provider (id, model_type, provider_code, name, fields, sort, creator, create_date, updater, update_date)
VALUES ('SYSTEM_PLUGIN_HA_GET_STATE', 'Plugin', 'hass_get_state', 'HomeAssistant Device State Query',
        '[]', 50, 0, NOW(), 0, NOW());

-- HomeAssistant state modification plugin
INSERT INTO ai_model_provider (id, model_type, provider_code, name, fields, sort, creator, create_date, updater, update_date)
VALUES ('SYSTEM_PLUGIN_HA_SET_STATE', 'Plugin', 'hass_set_state', 'HomeAssistant Device State Modification',
        '[]', 60, 0, NOW(), 0, NOW());

-- HomeAssistant music playback plugin
INSERT INTO ai_model_provider (id, model_type, provider_code, name, fields, sort, creator, create_date, updater, update_date)
VALUES ('SYSTEM_PLUGIN_HA_PLAY_MUSIC', 'Plugin', 'hass_play_music', 'HomeAssistant Music Playback',
        '[]', 70, 0, NOW(), 0, NOW());


-- Delete old plugin parameters from sys_params
DELETE FROM sys_params WHERE param_code LIKE 'plugins.%';


-- Add agent plugin mapping table
CREATE TABLE IF NOT EXISTS ai_agent_plugin_mapping
(
    id         BIGSERIAL PRIMARY KEY,
    agent_id   VARCHAR(32) NOT NULL,
    plugin_id  VARCHAR(32) NOT NULL,
    param_info JSON        NOT NULL,
    UNIQUE (agent_id, plugin_id)
);

COMMENT ON TABLE ai_agent_plugin_mapping IS 'Agent-Plugin unique mapping table';
COMMENT ON COLUMN ai_agent_plugin_mapping.id IS 'Primary key';
COMMENT ON COLUMN ai_agent_plugin_mapping.agent_id IS 'Agent ID';
COMMENT ON COLUMN ai_agent_plugin_mapping.plugin_id IS 'Plugin ID';
COMMENT ON COLUMN ai_agent_plugin_mapping.param_info IS 'Parameter information';
