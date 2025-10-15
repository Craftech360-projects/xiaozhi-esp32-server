-- This file is used to initialize system parameter data, no need to execute manually, it will be executed automatically when the project starts
-- --------------------------------------------------------
-- Initialize parameter management configuration
DROP TABLE IF EXISTS sys_params;
-- Parameter management
create table sys_params
(
  id                   bigint NOT NULL,
  param_code           varchar(100),
  param_value          varchar(2000),
  value_type           varchar(20) default 'string',
  param_type           SMALLINT default 1,
  remark               varchar(200),
  creator              bigint,
  create_date          TIMESTAMP,
  updater              bigint,
  update_date          TIMESTAMP,
  PRIMARY KEY (id),
  CONSTRAINT uk_param_code UNIQUE (param_code)
);
COMMENT ON TABLE sys_params IS 'Parameter management';
COMMENT ON COLUMN sys_params.id IS 'id';
COMMENT ON COLUMN sys_params.param_code IS 'Parameter code';
COMMENT ON COLUMN sys_params.param_value IS 'Parameter value';
COMMENT ON COLUMN sys_params.value_type IS 'Value type: string-string, number-number, boolean-boolean, array-array';
COMMENT ON COLUMN sys_params.param_type IS 'Type 0: system parameter 1: non-system parameter';
COMMENT ON COLUMN sys_params.remark IS 'remark';
COMMENT ON COLUMN sys_params.creator IS 'creator';
COMMENT ON COLUMN sys_params.create_date IS 'creation time';
COMMENT ON COLUMN sys_params.updater IS 'updater';
COMMENT ON COLUMN sys_params.update_date IS 'update time';

-- Server configuration
INSERT INTO sys_params (id, param_code, param_value, value_type, param_type, remark) VALUES (100, 'server.ip', '0.0.0.0', 'string', 1, 'Server listening IP address');
INSERT INTO sys_params (id, param_code, param_value, value_type, param_type, remark) VALUES (101, 'server.port', '8000', 'number', 1, 'Server listening port');
INSERT INTO sys_params (id, param_code, param_value, value_type, param_type, remark) VALUES (102, 'server.secret', 'null', 'string', 1, 'Server secret key');
INSERT INTO sys_params (id, param_code, param_value, value_type, param_type, remark) VALUES (201, 'log.log_format', '<green>{time:YYMMDD HH:mm:ss}</green>[<light-blue>{version}-{selected_module}</light-blue>][<light-blue>{extra[tag]}</light-blue>]-<level>{level}</level>-<light-green>{message}</light-green>', 'string', 1, 'Console log format');
INSERT INTO sys_params (id, param_code, param_value, value_type, param_type, remark) VALUES (202, 'log.log_format_file', '{time:YYYY-MM-DD HH:mm:ss} - {version}_{selected_module} - {name} - {level} - {extra[tag]} - {message}', 'string', 1, 'File log format');
INSERT INTO sys_params (id, param_code, param_value, value_type, param_type, remark) VALUES (203, 'log.log_level', 'INFO', 'string', 1, 'Log level');
INSERT INTO sys_params (id, param_code, param_value, value_type, param_type, remark) VALUES (204, 'log.log_dir', 'tmp', 'string', 1, 'Log directory');
INSERT INTO sys_params (id, param_code, param_value, value_type, param_type, remark) VALUES (205, 'log.log_file', 'server.log', 'string', 1, 'Log filename');
INSERT INTO sys_params (id, param_code, param_value, value_type, param_type, remark) VALUES (206, 'log.data_dir', 'data', 'string', 1, 'Data directory');
INSERT INTO sys_params (id, param_code, param_value, value_type, param_type, remark) VALUES (301, 'delete_audio', 'true', 'boolean', 1, 'Whether to delete audio files after use');
INSERT INTO sys_params (id, param_code, param_value, value_type, param_type, remark) VALUES (302, 'close_connection_no_voice_time', '120', 'number', 1, 'Disconnect time when no voice input (seconds)');
INSERT INTO sys_params (id, param_code, param_value, value_type, param_type, remark) VALUES (303, 'tts_timeout', '10', 'number', 1, 'TTS request timeout (seconds)');
INSERT INTO sys_params (id, param_code, param_value, value_type, param_type, remark) VALUES (304, 'enable_wakeup_words_response_cache', 'false', 'boolean', 1, 'Whether to enable wake word acceleration');
INSERT INTO sys_params (id, param_code, param_value, value_type, param_type, remark) VALUES (305, 'enable_greeting', 'true', 'boolean', 1, 'Whether to enable opening greeting');
INSERT INTO sys_params (id, param_code, param_value, value_type, param_type, remark) VALUES (306, 'enable_stop_tts_notify', 'false', 'boolean', 1, 'Whether to enable end notification sound');
INSERT INTO sys_params (id, param_code, param_value, value_type, param_type, remark) VALUES (307, 'stop_tts_notify_voice', 'config/assets/tts_notify.mp3', 'string', 1, 'End notification sound file path');
INSERT INTO sys_params (id, param_code, param_value, value_type, param_type, remark) VALUES (308, 'exit_commands', 'exit;quit;close', 'array', 1, 'Exit command list');
INSERT INTO sys_params (id, param_code, param_value, value_type, param_type, remark) VALUES (309, 'xiaozhi', '{
  "type": "hello",
  "version": 1,
  "transport": "websocket",
  "audio_params": {
    "format": "opus",
    "sample_rate": 16000,
    "channels": 1,
    "frame_duration": 60
  }
}', 'json', 1, 'Xiaozhi type');
INSERT INTO sys_params (id, param_code, param_value, value_type, param_type, remark) VALUES (310, 'wakeup_words', 'hello xiaozhi;hello xiaoai;hey xiaoai;hello xiaoxin;hi xiaolong;hey xiaomei;hello xiaolin;hey xiaobing', 'array', 1, 'Wake word list, used to recognize wake words');
INSERT INTO sys_params (id, param_code, param_value, value_type, param_type, remark) VALUES (400, 'plugins.get_weather.api_key', 'a861d0d5e7bf4ee1a83d9a9e4f96d4da', 'string', 1, 'Weather plugin API key');
INSERT INTO sys_params (id, param_code, param_value, value_type, param_type, remark) VALUES (401, 'plugins.get_weather.default_location', 'Guangzhou', 'string', 1, 'Weather plugin default city');
INSERT INTO sys_params (id, param_code, param_value, value_type, param_type, remark) VALUES (410, 'plugins.get_news.default_rss_url', 'https://www.chinanews.com.cn/rss/society.xml', 'string', 1, 'News plugin default RSS URL');
INSERT INTO sys_params (id, param_code, param_value, value_type, param_type, remark) VALUES (411, 'plugins.get_news.category_urls', '{"society":"https://www.chinanews.com.cn/rss/society.xml","world":"https://www.chinanews.com.cn/rss/world.xml","finance":"https://www.chinanews.com.cn/rss/finance.xml"}', 'json', 1, 'News plugin category RSS URLs');
INSERT INTO sys_params (id, param_code, param_value, value_type, param_type, remark) VALUES (421, 'plugins.home_assistant.devices', 'living room,toy light,switch.cuco_cn_460494544_cp1_on_p_2_1;bedroom,table lamp,switch.iot_cn_831898993_socn1_on_p_2_1', 'array', 1, 'Home Assistant device list');
INSERT INTO sys_params (id, param_code, param_value, value_type, param_type, remark) VALUES (422, 'plugins.home_assistant.base_url', 'http://homeassistant.local:8123', 'string', 1, 'Home Assistant server address');
INSERT INTO sys_params (id, param_code, param_value, value_type, param_type, remark) VALUES (423, 'plugins.home_assistant.api_key', 'your home assistant api access token', 'string', 1, 'Home Assistant API key');
INSERT INTO sys_params (id, param_code, param_value, value_type, param_type, remark) VALUES (430, 'plugins.play_music.music_dir', './music', 'string', 1, 'Music file storage path');
INSERT INTO sys_params (id, param_code, param_value, value_type, param_type, remark) VALUES (431, 'plugins.play_music.music_ext', 'mp3;wav;p3', 'array', 1, 'Music file types');
INSERT INTO sys_params (id, param_code, param_value, value_type, param_type, remark) VALUES (432, 'plugins.play_music.refresh_time', '300', 'number', 1, 'Music list refresh interval (seconds)');
