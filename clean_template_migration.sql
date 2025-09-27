-- =============================================
-- Clean Template Migration Script
-- Only Cheeko template + empty agents/users
-- =============================================

SET FOREIGN_KEY_CHECKS = 0;

-- Drop existing tables if they exist
DROP TABLE IF EXISTS `DATABASECHANGELOG`;
DROP TABLE IF EXISTS `DATABASECHANGELOGLOCK`;
DROP TABLE IF EXISTS `ai_agent`;
DROP TABLE IF EXISTS `ai_agent_chat_audio`;
DROP TABLE IF EXISTS `ai_agent_chat_history`;
DROP TABLE IF EXISTS `ai_agent_plugin_mapping`;
DROP TABLE IF EXISTS `ai_agent_template`;
DROP TABLE IF EXISTS `ai_agent_voice_print`;
DROP TABLE IF EXISTS `ai_device`;
DROP TABLE IF EXISTS `ai_model_config`;
DROP TABLE IF EXISTS `ai_model_provider`;
DROP TABLE IF EXISTS `ai_ota`;
DROP TABLE IF EXISTS `ai_tts_voice`;
DROP TABLE IF EXISTS `ai_voiceprint`;
DROP TABLE IF EXISTS `parent_profile`;
DROP TABLE IF EXISTS `sys_dict_data`;
DROP TABLE IF EXISTS `sys_dict_type`;
DROP TABLE IF EXISTS `sys_params`;
DROP TABLE IF EXISTS `sys_user`;
DROP TABLE IF EXISTS `sys_user_token`;

-- Create DATABASECHANGELOG table
CREATE TABLE `DATABASECHANGELOG` (
  `ID` varchar(255) NOT NULL,
  `AUTHOR` varchar(255) NOT NULL,
  `FILENAME` varchar(255) NOT NULL,
  `DATEEXECUTED` datetime NOT NULL,
  `ORDEREXECUTED` int NOT NULL,
  `EXECTYPE` varchar(10) NOT NULL,
  `MD5SUM` varchar(35) DEFAULT NULL,
  `DESCRIPTION` varchar(255) DEFAULT NULL,
  `COMMENTS` varchar(255) DEFAULT NULL,
  `TAG` varchar(255) DEFAULT NULL,
  `LIQUIBASE` varchar(20) DEFAULT NULL,
  `CONTEXTS` varchar(255) DEFAULT NULL,
  `LABELS` varchar(255) DEFAULT NULL,
  `DEPLOYMENT_ID` varchar(10) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Create DATABASECHANGELOGLOCK table
CREATE TABLE `DATABASECHANGELOGLOCK` (
  `ID` int NOT NULL,
  `LOCKED` bit(1) NOT NULL,
  `LOCKGRANTED` datetime DEFAULT NULL,
  `LOCKEDBY` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Insert lock record
INSERT INTO `DATABASECHANGELOGLOCK` VALUES (1, 0, NULL, NULL);

-- Create ai_agent table (EMPTY - for users to create their own)
CREATE TABLE `ai_agent` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint DEFAULT NULL,
  `device_id` bigint DEFAULT NULL,
  `agent_name` varchar(100) DEFAULT NULL,
  `nickname` varchar(100) DEFAULT NULL,
  `is_public` tinyint(1) DEFAULT '0',
  `avatar` varchar(200) DEFAULT NULL,
  `system_prompt` text,
  `welcome_msg` text,
  `chat_history_conf` tinyint DEFAULT '1',
  `mem_model_id` varchar(50) DEFAULT 'Memory_mem_local_short',
  `creator` bigint DEFAULT NULL,
  `create_date` datetime DEFAULT NULL,
  `updater` bigint DEFAULT NULL,
  `update_date` datetime DEFAULT NULL,
  `status` tinyint DEFAULT '1',
  `sort` int DEFAULT '1',
  `character_traits` text,
  `conversation_style` text,
  `personality` text,
  `knowledge_base` text,
  `interaction_rules` text,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Create ai_agent_template table with only Cheeko template
CREATE TABLE `ai_agent_template` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint DEFAULT NULL,
  `agent_name` varchar(100) DEFAULT NULL,
  `nickname` varchar(100) DEFAULT NULL,
  `is_public` tinyint(1) DEFAULT '1',
  `avatar` varchar(200) DEFAULT NULL,
  `system_prompt` text,
  `welcome_msg` text,
  `chat_history_conf` tinyint DEFAULT '1',
  `mem_model_id` varchar(50) DEFAULT 'Memory_mem_local_short',
  `creator` bigint DEFAULT NULL,
  `create_date` datetime DEFAULT NULL,
  `updater` bigint DEFAULT NULL,
  `update_date` datetime DEFAULT NULL,
  `status` tinyint DEFAULT '1',
  `sort` int DEFAULT '0',
  `is_visible` tinyint(1) DEFAULT '1',
  `lang_code` varchar(10) DEFAULT 'en',
  `language` varchar(50) DEFAULT 'English',
  `character_traits` text,
  `conversation_style` text,
  `personality` text,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Insert only Cheeko template
INSERT INTO `ai_agent_template` VALUES (
1, NULL, 'Cheeko', 'Cheeko', 1, NULL,
'You are Cheeko, a friendly and enthusiastic AI assistant designed specifically for children aged 3-16. Your primary goal is to be a helpful, educational, and entertaining companion while maintaining a safe and age-appropriate environment.

## Core Identity & Personality:
- **Name**: Cheeko - a warm, approachable AI friend
- **Age Range**: Optimized for children 3-16 years old
- **Personality**: Cheerful, patient, encouraging, curious, and playful
- **Tone**: Friendly, warm, and slightly playful but never condescending
- **Energy Level**: Enthusiastic but calm when needed

## Communication Style:
- Use simple, clear language appropriate for the child\'s developmental stage
- Ask engaging questions to encourage participation and learning
- Celebrate achievements and effort, no matter how small
- Be patient and repeat explanations when needed
- Use encouraging phrases like \"Great job!\", \"That\'s a wonderful question!\", \"Let\'s explore this together!\"

## Educational Approach:
- Make learning fun through games, stories, and interactive activities
- Encourage curiosity and critical thinking
- Provide age-appropriate explanations for complex topics
- Use analogies and examples that children can relate to
- Promote problem-solving skills and creativity

## Safety & Guidelines:
- Always maintain a safe, child-friendly environment
- Never share personal information or ask for personal details
- Redirect inappropriate topics to something educational and fun
- Encourage children to talk to trusted adults about important matters
- Promote positive values like kindness, honesty, and respect

## Interaction Examples:
- \"That\'s such a cool question! Let me help you discover the answer!\"
- \"I love how you\'re thinking about this! What do you think might happen if...?\"
- \"Wow, you\'re really good at this! Want to try something a bit more challenging?\"
- \"It\'s okay if this seems tricky - learning new things takes practice, and you\'re doing great!\"

## Response Format:
- Keep responses concise but engaging
- Use emojis sparingly and appropriately
- Break down complex information into digestible chunks
- Always end with a question or suggestion to keep the conversation flowing

Remember: You\'re not just providing information - you\'re nurturing young minds, building confidence, and making learning an adventure!',

'Hello there! I\'m Cheeko, your friendly AI companion! 🌟 I\'m here to help you learn, play, and explore amazing things together! What would you like to discover today? We could:\n\n📚 Learn something new and exciting\n🎮 Play fun educational games\n🎨 Get creative with stories or activities\n🤔 Solve interesting puzzles\n🌍 Explore the world around us\n\nWhat sounds fun to you? I can\'t wait to be your learning buddy!',

1, 'Memory_mem_local_short', NULL, NOW(), NULL, NOW(), 1, 0, 1, 'en', 'English',
'Friendly, enthusiastic, patient, encouraging, curious, playful, warm, approachable, educational, safe',
'Simple and clear language, engaging questions, celebrates achievements, patient repetition, encouraging phrases, interactive approach',
'Cheerful and supportive AI companion designed for children aged 3-16, focused on making learning fun and safe while nurturing young minds and building confidence'
);

-- Create other essential tables (empty)

CREATE TABLE `ai_agent_chat_audio` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `chat_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `ai_agent_chat_history` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint DEFAULT NULL,
  `agent_id` bigint DEFAULT NULL,
  `device_id` bigint DEFAULT NULL,
  `user_msg` text,
  `ai_msg` text,
  `creator` bigint DEFAULT NULL,
  `create_date` datetime DEFAULT NULL,
  `session_id` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `ai_agent_plugin_mapping` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `agent_id` bigint DEFAULT NULL,
  `plugin_name` varchar(100) DEFAULT NULL,
  `is_enabled` tinyint(1) DEFAULT '1',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `ai_agent_voice_print` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint DEFAULT NULL,
  `agent_id` bigint DEFAULT NULL,
  `device_id` bigint DEFAULT NULL,
  `voice_print_data` text,
  `voice_features` text,
  `creator` bigint DEFAULT NULL,
  `create_date` datetime DEFAULT NULL,
  `status` tinyint DEFAULT '1',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `ai_device` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint DEFAULT NULL,
  `device_name` varchar(100) DEFAULT NULL,
  `device_type` varchar(50) DEFAULT NULL,
  `device_status` tinyint DEFAULT '1',
  `device_config` text,
  `mac_address` varchar(50) DEFAULT NULL,
  `ip_address` varchar(50) DEFAULT NULL,
  `creator` bigint DEFAULT NULL,
  `create_date` datetime DEFAULT NULL,
  `updater` bigint DEFAULT NULL,
  `update_date` datetime DEFAULT NULL,
  `last_heartbeat` datetime DEFAULT NULL,
  `firmware_version` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `ai_model_config` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `model_name` varchar(100) DEFAULT NULL,
  `model_type` varchar(50) DEFAULT NULL,
  `provider_id` bigint DEFAULT NULL,
  `model_params` text,
  `is_enabled` tinyint(1) DEFAULT '1',
  `api_endpoint` varchar(200) DEFAULT NULL,
  `api_key` varchar(500) DEFAULT NULL,
  `max_tokens` int DEFAULT NULL,
  `temperature` decimal(3,2) DEFAULT NULL,
  `creator` bigint DEFAULT NULL,
  `create_date` datetime DEFAULT NULL,
  `updater` bigint DEFAULT NULL,
  `update_date` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Insert essential AI model configurations
INSERT INTO `ai_model_config` VALUES
(1, 'Memory_nomem', 'memory', 1, '{}', 1, NULL, NULL, NULL, NULL, NULL, NOW(), NULL, NOW()),
(2, 'Memory_mem_local_short', 'memory', 1, '{}', 1, NULL, NULL, NULL, NULL, NULL, NOW(), NULL, NOW()),
(3, 'Memory_mem0ai', 'memory', 1, '{}', 1, NULL, NULL, NULL, NULL, NULL, NOW(), NULL, NOW());

CREATE TABLE `ai_model_provider` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `provider_name` varchar(100) DEFAULT NULL,
  `provider_type` varchar(50) DEFAULT NULL,
  `api_base_url` varchar(200) DEFAULT NULL,
  `api_key` varchar(500) DEFAULT NULL,
  `is_enabled` tinyint(1) DEFAULT '1',
  `provider_config` text,
  `creator` bigint DEFAULT NULL,
  `create_date` datetime DEFAULT NULL,
  `updater` bigint DEFAULT NULL,
  `update_date` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Insert basic model provider
INSERT INTO `ai_model_provider` VALUES (1, 'Local', 'local', NULL, NULL, 1, '{}', NULL, NOW(), NULL, NOW());

CREATE TABLE `ai_ota` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `version` varchar(50) DEFAULT NULL,
  `firmware_url` varchar(500) DEFAULT NULL,
  `release_notes` text,
  `is_active` tinyint(1) DEFAULT '0',
  `device_type` varchar(50) DEFAULT NULL,
  `creator` bigint DEFAULT NULL,
  `create_date` datetime DEFAULT NULL,
  `updater` bigint DEFAULT NULL,
  `update_date` datetime DEFAULT NULL,
  `checksum` varchar(100) DEFAULT NULL,
  `file_size` bigint DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `ai_tts_voice` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `voice_name` varchar(100) DEFAULT NULL,
  `voice_code` varchar(50) DEFAULT NULL,
  `language` varchar(50) DEFAULT NULL,
  `gender` varchar(10) DEFAULT NULL,
  `provider` varchar(50) DEFAULT NULL,
  `is_enabled` tinyint(1) DEFAULT '1',
  `voice_config` text,
  `creator` bigint DEFAULT NULL,
  `create_date` datetime DEFAULT NULL,
  `updater` bigint DEFAULT NULL,
  `update_date` datetime DEFAULT NULL,
  `sample_url` varchar(500) DEFAULT NULL,
  `voice_type` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Insert basic TTS voice
INSERT INTO `ai_tts_voice` VALUES (1, 'Default Voice', 'default', 'English', 'neutral', 'system', 1, '{}', NULL, NOW(), NULL, NOW(), NULL, 'standard');

CREATE TABLE `ai_voiceprint` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint DEFAULT NULL,
  `user_id` bigint DEFAULT NULL,
  `device_id` bigint DEFAULT NULL,
  `voiceprint_name` varchar(100) DEFAULT NULL,
  `voiceprint_data` text,
  `voice_features` text,
  `is_active` tinyint(1) DEFAULT '1',
  `creator` bigint DEFAULT NULL,
  `create_date` datetime DEFAULT NULL,
  `updater` bigint DEFAULT NULL,
  `update_date` datetime DEFAULT NULL,
  `confidence_threshold` decimal(3,2) DEFAULT '0.80',
  `training_samples` int DEFAULT '0',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `parent_profile` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `tenant_id` bigint DEFAULT NULL,
  `parent_name` varchar(100) DEFAULT NULL,
  `email` varchar(100) DEFAULT NULL,
  `phone` varchar(20) DEFAULT NULL,
  `child_name` varchar(100) DEFAULT NULL,
  `child_age` int DEFAULT NULL,
  `preferences` text,
  `safety_settings` text,
  `creator` bigint DEFAULT NULL,
  `create_date` datetime DEFAULT NULL,
  `updater` bigint DEFAULT NULL,
  `update_date` datetime DEFAULT NULL,
  `status` tinyint DEFAULT '1',
  `language_preference` varchar(50) DEFAULT 'English',
  `timezone` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `sys_dict_data` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `dict_type_id` bigint DEFAULT NULL,
  `dict_label` varchar(100) DEFAULT NULL,
  `dict_value` varchar(100) DEFAULT NULL,
  `dict_type` varchar(100) DEFAULT NULL,
  `css_class` varchar(100) DEFAULT NULL,
  `list_class` varchar(100) DEFAULT NULL,
  `is_default` tinyint(1) DEFAULT '0',
  `status` tinyint DEFAULT '1',
  `creator` bigint DEFAULT NULL,
  `create_date` datetime DEFAULT NULL,
  `sort` int DEFAULT NULL,
  `remark` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Insert essential dictionary data
INSERT INTO `sys_dict_data` VALUES
(1, 1, 'Normal', '1', 'sys_status', NULL, 'success', 1, 1, NULL, NOW(), 1, 'Normal status'),
(2, 1, 'Disabled', '0', 'sys_status', NULL, 'danger', 0, 1, NULL, NOW(), 2, 'Disabled status');

CREATE TABLE `sys_dict_type` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `dict_name` varchar(100) DEFAULT NULL,
  `dict_type` varchar(100) DEFAULT NULL,
  `status` tinyint DEFAULT '1',
  `creator` bigint DEFAULT NULL,
  `create_date` datetime DEFAULT NULL,
  `updater` bigint DEFAULT NULL,
  `update_date` datetime DEFAULT NULL,
  `remark` varchar(500) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Insert dictionary types
INSERT INTO `sys_dict_type` VALUES (1, 'System Status', 'sys_status', 1, NULL, NOW(), NULL, NOW(), 'System status dictionary');

CREATE TABLE `sys_params` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `param_code` varchar(100) DEFAULT NULL,
  `param_value` varchar(2000) DEFAULT NULL,
  `value_type` varchar(20) DEFAULT 'string',
  `param_type` tinyint unsigned DEFAULT '1',
  `remark` varchar(200) DEFAULT NULL,
  `creator` bigint DEFAULT NULL,
  `create_date` datetime DEFAULT NULL,
  `updater` bigint DEFAULT NULL,
  `update_date` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `param_code` (`param_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Insert essential system parameters
INSERT INTO `sys_params` (`param_code`, `param_value`, `value_type`, `param_type`, `remark`, `creator`, `create_date`, `updater`, `update_date`) VALUES
('sys.name', 'XiaoZhi ESP32 Manager', 'string', 1, 'System name configuration', NULL, NOW(), NULL, NOW()),
('ai.default.memory', 'Memory_mem_local_short', 'string', 1, 'Default memory model for AI agents', NULL, NOW(), NULL, NOW()),
('ai.default.chat_history', '1', 'string', 1, 'Default chat history configuration (1=text enabled)', NULL, NOW(), NULL, NOW()),
('ai.agent.name.max_length', '100', 'string', 1, 'Maximum length for agent names', NULL, NOW(), NULL, NOW()),
('ai.agent.prompt.max_length', '4000', 'string', 1, 'Maximum length for system prompts', NULL, NOW(), NULL, NOW());

-- Create sys_user table (EMPTY - for users to create their own accounts)
CREATE TABLE `sys_user` (
  `user_id` bigint NOT NULL AUTO_INCREMENT,
  `username` varchar(50) NOT NULL,
  `password` varchar(100) DEFAULT NULL,
  `salt` varchar(20) DEFAULT NULL,
  `email` varchar(100) DEFAULT NULL,
  `mobile` varchar(100) DEFAULT NULL,
  `status` tinyint DEFAULT NULL,
  `creator` bigint DEFAULT NULL,
  `create_date` datetime DEFAULT NULL,
  `updater` bigint DEFAULT NULL,
  `update_date` datetime DEFAULT NULL,
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `sys_user_token` (
  `user_id` bigint NOT NULL,
  `token` varchar(100) NOT NULL,
  `expire_date` datetime DEFAULT NULL,
  `update_date` datetime DEFAULT NULL,
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `token` (`token`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

SET FOREIGN_KEY_CHECKS = 1;

-- =============================================
-- Migration Complete
-- =============================================
-- This creates a clean database with:
-- ✓ Only Cheeko template (no pre-created agents)
-- ✓ Empty user management (users create their own)
-- ✓ Essential system configurations
-- ✓ All required table structures
-- ✓ Default memory model: Memory_mem_local_short
-- ✓ Default chat history: Report Text enabled (1)
-- ✓ Max prompt length: 4000 characters
-- =============================================