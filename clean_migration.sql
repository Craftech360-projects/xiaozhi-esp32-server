-- =====================================================
-- Clean Database Migration Script - Railway to Local Docker
-- Generated: 2025-09-19
-- Target Database: manager_api
-- All comments and data in English
-- =====================================================

SET FOREIGN_KEY_CHECKS = 0;
SET SQL_MODE = 'NO_AUTO_VALUE_ON_ZERO';
SET AUTOCOMMIT = 0;
START TRANSACTION;

-- =====================================================
-- Drop existing tables if they exist
-- =====================================================
DROP TABLE IF EXISTS ai_chat_message;
DROP TABLE IF EXISTS ai_chat_history;
DROP TABLE IF EXISTS ai_voiceprint;
DROP TABLE IF EXISTS ai_device;
DROP TABLE IF EXISTS ai_agent;
DROP TABLE IF EXISTS ai_agent_template;
DROP TABLE IF EXISTS ai_tts_voice;
DROP TABLE IF EXISTS ai_model_config;
DROP TABLE IF EXISTS ai_model_provider;
DROP TABLE IF EXISTS sys_dict_data;
DROP TABLE IF EXISTS sys_dict_type;
DROP TABLE IF EXISTS sys_user_token;
DROP TABLE IF EXISTS sys_params;
DROP TABLE IF EXISTS sys_user;

-- =====================================================
-- System Users Table
-- =====================================================
CREATE TABLE sys_user (
  id bigint NOT NULL COMMENT 'Primary key',
  username varchar(50) NOT NULL COMMENT 'Username',
  password varchar(100) COMMENT 'Password',
  super_admin tinyint unsigned COMMENT 'Super administrator: 0=No, 1=Yes',
  status tinyint COMMENT 'Status: 0=Disabled, 1=Normal',
  create_date datetime COMMENT 'Create time',
  updater bigint COMMENT 'Updater',
  creator bigint COMMENT 'Creator',
  update_date datetime COMMENT 'Update time',
  PRIMARY KEY (id),
  UNIQUE KEY uk_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='System Users';

-- =====================================================
-- System User Token Table
-- =====================================================
CREATE TABLE sys_user_token (
  id bigint NOT NULL COMMENT 'Primary key',
  user_id bigint NOT NULL COMMENT 'User ID',
  token varchar(100) NOT NULL COMMENT 'User token',
  expire_date datetime COMMENT 'Expire time',
  update_date datetime COMMENT 'Update time',
  create_date datetime COMMENT 'Create time',
  PRIMARY KEY (id),
  UNIQUE KEY user_id (user_id),
  UNIQUE KEY token (token)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='System User Token';

-- =====================================================
-- Parameter Management Table
-- =====================================================
CREATE TABLE sys_params (
  id bigint NOT NULL COMMENT 'Primary key',
  param_code varchar(32) COMMENT 'Parameter code',
  param_value varchar(2000) COMMENT 'Parameter value',
  param_type tinyint unsigned default 1 COMMENT 'Type: 0=System parameter, 1=Non-system parameter',
  remark varchar(200) COMMENT 'Remark',
  creator bigint COMMENT 'Creator',
  create_date datetime COMMENT 'Create time',
  updater bigint COMMENT 'Updater',
  update_date datetime COMMENT 'Update time',
  PRIMARY KEY (id),
  UNIQUE KEY uk_param_code (param_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Parameter Management';

-- =====================================================
-- Dictionary Type Table
-- =====================================================
CREATE TABLE sys_dict_type (
  id bigint NOT NULL COMMENT 'Primary key',
  dict_type varchar(100) NOT NULL COMMENT 'Dictionary type',
  dict_name varchar(255) NOT NULL COMMENT 'Dictionary name',
  remark varchar(255) COMMENT 'Remark',
  sort int unsigned COMMENT 'Sort order',
  creator bigint COMMENT 'Creator',
  create_date datetime COMMENT 'Create time',
  updater bigint COMMENT 'Updater',
  update_date datetime COMMENT 'Update time',
  PRIMARY KEY (id),
  UNIQUE KEY(dict_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Dictionary Type';

-- =====================================================
-- Dictionary Data Table
-- =====================================================
CREATE TABLE sys_dict_data (
  id bigint NOT NULL COMMENT 'Primary key',
  dict_type_id bigint NOT NULL COMMENT 'Dictionary type ID',
  dict_label varchar(255) NOT NULL COMMENT 'Dictionary label',
  dict_value varchar(255) COMMENT 'Dictionary value',
  remark varchar(255) COMMENT 'Remark',
  sort int unsigned COMMENT 'Sort order',
  creator bigint COMMENT 'Creator',
  create_date datetime COMMENT 'Create time',
  updater bigint COMMENT 'Updater',
  update_date datetime COMMENT 'Update time',
  PRIMARY KEY (id),
  UNIQUE KEY uk_dict_type_value (dict_type_id, dict_value),
  KEY idx_sort (sort)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Dictionary Data';

-- =====================================================
-- AI Model Provider Table
-- =====================================================
CREATE TABLE ai_model_provider (
  id VARCHAR(32) NOT NULL COMMENT 'Primary key',
  model_type VARCHAR(20) COMMENT 'Model type (Memory/ASR/VAD/LLM/TTS)',
  provider_code VARCHAR(50) COMMENT 'Provider code',
  name VARCHAR(50) COMMENT 'Provider name',
  fields JSON COMMENT 'Provider fields list (JSON format)',
  sort INT UNSIGNED DEFAULT 0 COMMENT 'Sort order',
  creator BIGINT COMMENT 'Creator',
  create_date DATETIME COMMENT 'Create time',
  updater BIGINT COMMENT 'Updater',
  update_date DATETIME COMMENT 'Update time',
  PRIMARY KEY (id),
  INDEX idx_ai_model_provider_model_type (model_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='AI Model Provider';

-- =====================================================
-- AI Model Config Table
-- =====================================================
CREATE TABLE ai_model_config (
  id VARCHAR(32) NOT NULL COMMENT 'Primary key',
  model_type VARCHAR(20) COMMENT 'Model type (Memory/ASR/VAD/LLM/TTS)',
  model_code VARCHAR(50) COMMENT 'Model code',
  model_name VARCHAR(50) COMMENT 'Model name',
  is_default TINYINT(1) DEFAULT 0 COMMENT 'Is default configuration (0=No, 1=Yes)',
  is_enabled TINYINT(1) DEFAULT 0 COMMENT 'Is enabled (0=No, 1=Yes)',
  config_json JSON COMMENT 'Model configuration (JSON format)',
  doc_link VARCHAR(200) COMMENT 'Documentation link',
  remark VARCHAR(255) COMMENT 'Remark',
  sort INT UNSIGNED DEFAULT 0 COMMENT 'Sort order',
  creator BIGINT COMMENT 'Creator',
  create_date DATETIME COMMENT 'Create time',
  updater BIGINT COMMENT 'Updater',
  update_date DATETIME COMMENT 'Update time',
  PRIMARY KEY (id),
  INDEX idx_ai_model_config_model_type (model_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='AI Model Configuration';

-- =====================================================
-- TTS Voice Table
-- =====================================================
CREATE TABLE ai_tts_voice (
  id VARCHAR(32) NOT NULL COMMENT 'Primary key',
  tts_model_id VARCHAR(32) COMMENT 'TTS model ID',
  name VARCHAR(20) COMMENT 'Voice name',
  tts_voice VARCHAR(50) COMMENT 'Voice code',
  languages VARCHAR(50) COMMENT 'Languages',
  voice_demo VARCHAR(500) DEFAULT NULL COMMENT 'Voice demo',
  remark VARCHAR(255) COMMENT 'Remark',
  sort INT UNSIGNED DEFAULT 0 COMMENT 'Sort order',
  creator BIGINT COMMENT 'Creator',
  create_date DATETIME COMMENT 'Create time',
  updater BIGINT COMMENT 'Updater',
  update_date DATETIME COMMENT 'Update time',
  PRIMARY KEY (id),
  INDEX idx_ai_tts_voice_tts_model_id (tts_model_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='TTS Voice';

-- =====================================================
-- AI Agent Template Table
-- =====================================================
CREATE TABLE ai_agent_template (
  id VARCHAR(32) NOT NULL COMMENT 'Agent unique identifier',
  agent_code VARCHAR(36) COMMENT 'Agent code',
  agent_name VARCHAR(64) COMMENT 'Agent name',
  asr_model_id VARCHAR(32) COMMENT 'ASR model identifier',
  vad_model_id VARCHAR(64) COMMENT 'VAD model identifier',
  llm_model_id VARCHAR(32) COMMENT 'LLM model identifier',
  tts_model_id VARCHAR(32) COMMENT 'TTS model identifier',
  tts_voice_id VARCHAR(32) COMMENT 'Voice identifier',
  mem_model_id VARCHAR(32) COMMENT 'Memory model identifier',
  intent_model_id VARCHAR(32) COMMENT 'Intent model identifier',
  system_prompt TEXT COMMENT 'System prompt',
  lang_code VARCHAR(10) COMMENT 'Language code',
  language VARCHAR(10) COMMENT 'Interaction language',
  sort INT UNSIGNED DEFAULT 0 COMMENT 'Sort weight',
  creator BIGINT COMMENT 'Creator ID',
  created_at DATETIME COMMENT 'Create time',
  updater BIGINT COMMENT 'Updater ID',
  updated_at DATETIME COMMENT 'Update time',
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='AI Agent Template';

-- =====================================================
-- AI Agent Table
-- =====================================================
CREATE TABLE ai_agent (
  id VARCHAR(32) NOT NULL COMMENT 'Agent unique identifier',
  user_id BIGINT COMMENT 'User ID',
  agent_code VARCHAR(36) COMMENT 'Agent code',
  agent_name VARCHAR(64) COMMENT 'Agent name',
  asr_model_id VARCHAR(32) COMMENT 'ASR model identifier',
  vad_model_id VARCHAR(64) COMMENT 'VAD model identifier',
  llm_model_id VARCHAR(32) COMMENT 'LLM model identifier',
  tts_model_id VARCHAR(32) COMMENT 'TTS model identifier',
  tts_voice_id VARCHAR(32) COMMENT 'Voice identifier',
  mem_model_id VARCHAR(32) COMMENT 'Memory model identifier',
  intent_model_id VARCHAR(32) COMMENT 'Intent model identifier',
  system_prompt TEXT COMMENT 'System prompt',
  lang_code VARCHAR(10) COMMENT 'Language code',
  language VARCHAR(10) COMMENT 'Interaction language',
  sort INT UNSIGNED DEFAULT 0 COMMENT 'Sort weight',
  creator BIGINT COMMENT 'Creator ID',
  created_at DATETIME COMMENT 'Create time',
  updater BIGINT COMMENT 'Updater ID',
  updated_at DATETIME COMMENT 'Update time',
  PRIMARY KEY (id),
  INDEX idx_ai_agent_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='AI Agent Configuration';

-- =====================================================
-- Device Information Table
-- =====================================================
CREATE TABLE ai_device (
  id VARCHAR(32) NOT NULL COMMENT 'Device unique identifier',
  user_id BIGINT COMMENT 'User ID',
  mac_address VARCHAR(50) COMMENT 'MAC address',
  last_connected_at DATETIME COMMENT 'Last connected time',
  auto_update TINYINT UNSIGNED DEFAULT 0 COMMENT 'Auto update (0=Disabled, 1=Enabled)',
  board VARCHAR(50) COMMENT 'Hardware model',
  alias VARCHAR(64) DEFAULT NULL COMMENT 'Device alias',
  agent_id VARCHAR(32) COMMENT 'Agent ID',
  app_version VARCHAR(20) COMMENT 'Firmware version',
  sort INT UNSIGNED DEFAULT 0 COMMENT 'Sort order',
  creator BIGINT COMMENT 'Creator',
  create_date DATETIME COMMENT 'Create time',
  updater BIGINT COMMENT 'Updater',
  update_date DATETIME COMMENT 'Update time',
  PRIMARY KEY (id),
  INDEX idx_ai_device_mac_address (mac_address)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Device Information';

-- =====================================================
-- Voiceprint Recognition Table
-- =====================================================
CREATE TABLE ai_voiceprint (
  id VARCHAR(32) NOT NULL COMMENT 'Voiceprint unique identifier',
  name VARCHAR(64) COMMENT 'Voiceprint name',
  user_id BIGINT COMMENT 'User ID',
  agent_id VARCHAR(32) COMMENT 'Agent ID',
  agent_code VARCHAR(36) COMMENT 'Agent code',
  agent_name VARCHAR(36) COMMENT 'Agent name',
  description VARCHAR(255) COMMENT 'Voiceprint description',
  embedding LONGTEXT COMMENT 'Feature vector (JSON array format)',
  memory TEXT COMMENT 'Associated memory data',
  sort INT UNSIGNED DEFAULT 0 COMMENT 'Sort weight',
  creator BIGINT COMMENT 'Creator ID',
  created_at DATETIME COMMENT 'Create time',
  updater BIGINT COMMENT 'Updater ID',
  updated_at DATETIME COMMENT 'Update time',
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Voiceprint Recognition';

-- =====================================================
-- Chat History Table
-- =====================================================
CREATE TABLE ai_chat_history (
  id VARCHAR(32) NOT NULL COMMENT 'Chat ID',
  user_id BIGINT COMMENT 'User ID',
  agent_id VARCHAR(32) DEFAULT NULL COMMENT 'Agent ID',
  device_id VARCHAR(32) DEFAULT NULL COMMENT 'Device ID',
  message_count INT COMMENT 'Message count',
  creator BIGINT COMMENT 'Creator',
  create_date DATETIME COMMENT 'Create time',
  updater BIGINT COMMENT 'Updater',
  update_date DATETIME COMMENT 'Update time',
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Chat History';

-- =====================================================
-- Chat Message Table
-- =====================================================
CREATE TABLE ai_chat_message (
  id VARCHAR(32) NOT NULL COMMENT 'Message unique identifier',
  user_id BIGINT COMMENT 'User ID',
  chat_id VARCHAR(64) COMMENT 'Chat history ID',
  role ENUM('user', 'assistant') COMMENT 'Role (user or assistant)',
  content TEXT COMMENT 'Message content',
  prompt_tokens INT UNSIGNED DEFAULT 0 COMMENT 'Prompt tokens',
  total_tokens INT UNSIGNED DEFAULT 0 COMMENT 'Total tokens',
  completion_tokens INT UNSIGNED DEFAULT 0 COMMENT 'Completion tokens',
  prompt_ms INT UNSIGNED DEFAULT 0 COMMENT 'Prompt time (milliseconds)',
  total_ms INT UNSIGNED DEFAULT 0 COMMENT 'Total time (milliseconds)',
  completion_ms INT UNSIGNED DEFAULT 0 COMMENT 'Completion time (milliseconds)',
  creator BIGINT COMMENT 'Creator',
  create_date DATETIME COMMENT 'Create time',
  updater BIGINT COMMENT 'Updater',
  update_date DATETIME COMMENT 'Update time',
  PRIMARY KEY (id),
  INDEX idx_ai_chat_message_user_id_chat_id (user_id, chat_id),
  INDEX idx_ai_chat_message_created_at (create_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Chat Message';

-- =====================================================
-- Insert default admin user
-- =====================================================
INSERT INTO sys_user (id, username, password, super_admin, status, create_date, creator)
VALUES (1, 'admin', '$2a$10$012Kx2ba5jzqr9gLlG4MX.bnQJTjjNEacl5.I1FuqrnqyaOJkWopp', 1, 1, NOW(), 1);

-- =====================================================
-- Complete transaction
-- =====================================================
SET FOREIGN_KEY_CHECKS = 1;
COMMIT;

SELECT 'Database migration completed successfully!' as message;