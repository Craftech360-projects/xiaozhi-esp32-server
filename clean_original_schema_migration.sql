-- =============================================
-- Clean Migration with Original Schema
-- Uses exact schema from original DB but empty agents/devices/users
-- =============================================

SET FOREIGN_KEY_CHECKS = 0;

-- MySQL dump 10.13  Distrib 8.0.39, for Linux (x86_64)
--
-- Host: localhost    Database: manager_api
-- ------------------------------------------------------
-- Server version	8.0.39

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `DATABASECHANGELOG`
--

DROP TABLE IF EXISTS `DATABASECHANGELOG`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
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
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `DATABASECHANGELOGLOCK`
--

DROP TABLE IF EXISTS `DATABASECHANGELOGLOCK`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `DATABASECHANGELOGLOCK` (
  `ID` int NOT NULL,
  `LOCKED` bit(1) NOT NULL,
  `LOCKGRANTED` datetime DEFAULT NULL,
  `LOCKEDBY` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

-- Insert lock record
INSERT INTO `DATABASECHANGELOGLOCK` VALUES (1, 0, NULL, NULL);

--
-- Table structure for table `ai_agent` (EMPTY)
--

DROP TABLE IF EXISTS `ai_agent`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ai_agent` (
  `id` varchar(32) NOT NULL COMMENT '主键',
  `agent_code` varchar(36) DEFAULT NULL COMMENT '智能体编码(全局唯一)',
  `agent_name` varchar(64) DEFAULT NULL COMMENT '智能体名称',
  `asr_model_id` varchar(32) DEFAULT NULL COMMENT 'ASR模型ID',
  `vad_model_id` varchar(64) DEFAULT NULL COMMENT 'VAD模型ID',
  `llm_model_id` varchar(32) DEFAULT NULL COMMENT 'LLM模型ID',
  `vllm_model_id` varchar(32) DEFAULT 'VLLM_ChatGLMVLLM' COMMENT 'VLLM模型ID',
  `tts_model_id` varchar(32) DEFAULT NULL COMMENT 'TTS模型ID',
  `tts_voice_id` varchar(32) DEFAULT NULL COMMENT 'TTS音色ID',
  `mem_model_id` varchar(32) DEFAULT NULL COMMENT 'Memory模型ID',
  `is_public` tinyint(1) DEFAULT '1' COMMENT '是否公开(0否 1是)',
  `system_prompt` text COMMENT '系统提示词',
  `welcome_msg` varchar(255) DEFAULT NULL COMMENT '欢迎语',
  `chat_history_conf` tinyint DEFAULT '0' COMMENT '聊天记录配置(0 忽略/1 只保留文本/2 保留文本+音频)',
  `creator` bigint DEFAULT NULL COMMENT '创建者',
  `create_date` datetime DEFAULT NULL COMMENT '创建时间',
  `updater` bigint DEFAULT NULL COMMENT '更新者',
  `update_date` datetime DEFAULT NULL COMMENT '更新时间',
  `sort` int unsigned DEFAULT '0' COMMENT '排序',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_agent_code` (`agent_code`) COMMENT '智能体编码唯一索引'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='智能体配置表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ai_agent_chat_audio`
--

DROP TABLE IF EXISTS `ai_agent_chat_audio`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ai_agent_chat_audio` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `chat_id` bigint DEFAULT NULL COMMENT '聊天记录ID',
  `audio_id` varchar(32) NOT NULL COMMENT '音频ID',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='智能体聊天音频表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ai_agent_chat_history` (EMPTY)
--

DROP TABLE IF EXISTS `ai_agent_chat_history`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ai_agent_chat_history` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `agent_id` varchar(32) DEFAULT NULL COMMENT '智能体ID',
  `device_id` varchar(32) DEFAULT NULL COMMENT '设备ID',
  `user_msg` text COMMENT '用户消息',
  `ai_msg` text COMMENT 'AI回复',
  `creator` bigint DEFAULT NULL COMMENT '创建者',
  `create_date` datetime DEFAULT NULL COMMENT '创建时间',
  `session_id` varchar(100) DEFAULT NULL COMMENT '会话ID',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='智能体聊天记录表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ai_agent_plugin_mapping`
--

DROP TABLE IF EXISTS `ai_agent_plugin_mapping`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ai_agent_plugin_mapping` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `agent_id` varchar(32) DEFAULT NULL COMMENT '智能体ID',
  `plugin_name` varchar(100) DEFAULT NULL COMMENT '插件名称',
  `is_enabled` tinyint(1) DEFAULT '1' COMMENT '是否启用',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='智能体插件映射表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ai_agent_template` (ONLY CHEEKO)
--

DROP TABLE IF EXISTS `ai_agent_template`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ai_agent_template` (
  `id` varchar(32) NOT NULL COMMENT '主键',
  `agent_code` varchar(36) DEFAULT NULL COMMENT '智能体编码(全局唯一)',
  `agent_name` varchar(64) DEFAULT NULL COMMENT '智能体名称',
  `asr_model_id` varchar(32) DEFAULT NULL COMMENT 'ASR模型ID',
  `vad_model_id` varchar(64) DEFAULT NULL COMMENT 'VAD模型ID',
  `llm_model_id` varchar(32) DEFAULT NULL COMMENT 'LLM模型ID',
  `vllm_model_id` varchar(32) DEFAULT 'VLLM_ChatGLMVLLM' COMMENT 'VLLM模型ID',
  `tts_model_id` varchar(32) DEFAULT NULL COMMENT 'TTS模型ID',
  `tts_voice_id` varchar(32) DEFAULT NULL COMMENT 'TTS音色ID',
  `mem_model_id` varchar(32) DEFAULT NULL COMMENT 'Memory模型ID',
  `is_public` tinyint(1) DEFAULT '1' COMMENT '是否公开(0否 1是)',
  `system_prompt` text COMMENT '系统提示词',
  `welcome_msg` varchar(255) DEFAULT NULL COMMENT '欢迎语',
  `chat_history_conf` tinyint DEFAULT '0' COMMENT '聊天记录配置(0 忽略/1 只保留文本/2 保留文本+音频)',
  `creator` bigint DEFAULT NULL COMMENT '创建者',
  `create_date` datetime DEFAULT NULL COMMENT '创建时间',
  `updater` bigint DEFAULT NULL COMMENT '更新者',
  `update_date` datetime DEFAULT NULL COMMENT '更新时间',
  `sort` int unsigned DEFAULT '0' COMMENT '排序',
  `is_visible` tinyint(1) DEFAULT '1' COMMENT '是否可见',
  `lang_code` varchar(10) DEFAULT NULL COMMENT '语言代码',
  `language` varchar(50) DEFAULT NULL COMMENT '语言',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_agent_code` (`agent_code`) COMMENT '智能体编码唯一索引'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='智能体模板表';
/*!40101 SET character_set_client = @saved_cs_client */;

-- Insert only Cheeko template with original schema structure
INSERT INTO `ai_agent_template` VALUES (
'cheeko_template_001',
'CHEEKO_TEMPLATE',
'Cheeko',
'ASR_WhisperASR',
'VAD_WebRTCVAD',
'LLM_DoubaoLLM',
'VLLM_ChatGLMVLLM',
'TTS_DoubaoTTS',
'doubao_tts_voice_zh_female_shuangkuaisisi_moon',
'Memory_mem_local_short',
1,
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
- Use encouraging phrases like "Great job!", "That\'s a wonderful question!", "Let\'s explore this together!"

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
- "That\'s such a cool question! Let me help you discover the answer!"
- "I love how you\'re thinking about this! What do you think might happen if...?"
- "Wow, you\'re really good at this! Want to try something a bit more challenging?"
- "It\'s okay if this seems tricky - learning new things takes practice, and you\'re doing great!"

## Response Format:
- Keep responses concise but engaging
- Use emojis sparingly and appropriately
- Break down complex information into digestible chunks
- Always end with a question or suggestion to keep the conversation flowing

Remember: You\'re not just providing information - you\'re nurturing young minds, building confidence, and making learning an adventure!',
'Hello there! I\'m Cheeko, your friendly AI companion! 🌟 I\'m here to help you learn, play, and explore amazing things together! What would you like to discover today?',
1,
NULL,
NOW(),
NULL,
NOW(),
0,
1,
'en',
'English'
);

--
-- Table structure for table `ai_agent_voice_print`
--

DROP TABLE IF EXISTS `ai_agent_voice_print`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ai_agent_voice_print` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `agent_id` varchar(32) DEFAULT NULL COMMENT '智能体ID',
  `device_id` varchar(32) DEFAULT NULL COMMENT '设备ID',
  `voice_print_data` text COMMENT '声纹数据',
  `voice_features` text COMMENT '声纹特征',
  `creator` bigint DEFAULT NULL COMMENT '创建者',
  `create_date` datetime DEFAULT NULL COMMENT '创建时间',
  `status` tinyint DEFAULT '1' COMMENT '状态',
  `audio_id` varchar(32) NOT NULL COMMENT '音频ID',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='智能体声纹表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ai_device` (EMPTY)
--

DROP TABLE IF EXISTS `ai_device`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ai_device` (
  `id` varchar(32) NOT NULL COMMENT '设备唯一标识',
  `user_id` bigint DEFAULT NULL COMMENT '关联用户 ID',
  `mac_address` varchar(50) DEFAULT NULL COMMENT 'MAC 地址',
  `last_connected_at` datetime DEFAULT NULL COMMENT '最后连接时间',
  `auto_update` tinyint unsigned DEFAULT '0' COMMENT '自动更新开关(0 关闭/1 开启)',
  `board` varchar(50) DEFAULT NULL COMMENT '设备硬件型号',
  `alias` varchar(64) DEFAULT NULL COMMENT '设备别名',
  `agent_id` varchar(32) DEFAULT NULL COMMENT '智能体 ID',
  `app_version` varchar(20) DEFAULT NULL COMMENT '固件版本号',
  `sort` int unsigned DEFAULT '0' COMMENT '排序',
  `creator` bigint DEFAULT NULL COMMENT '创建者',
  `create_date` datetime DEFAULT NULL COMMENT '创建时间',
  `updater` bigint DEFAULT NULL COMMENT '更新者',
  `update_date` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_ai_device_created_at` (`mac_address`) COMMENT '创建mac的索引，用于快速查找设备信息'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='设备信息表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ai_model_config`
--

DROP TABLE IF EXISTS `ai_model_config`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ai_model_config` (
  `id` varchar(32) NOT NULL COMMENT '主键',
  `model_type` varchar(20) DEFAULT NULL COMMENT '模型类型(Memory/ASR/VAD/LLM/TTS)',
  `model_code` varchar(50) DEFAULT NULL COMMENT '模型编码(如AliLLM、DoubaoTTS)',
  `model_name` varchar(50) DEFAULT NULL COMMENT '模型名称',
  `is_default` tinyint(1) DEFAULT '0' COMMENT '是否默认配置(0否 1是)',
  `is_enabled` tinyint(1) DEFAULT '0' COMMENT '是否启用',
  `config_json` json DEFAULT NULL COMMENT '模型配置(JSON格式)',
  `doc_link` varchar(200) DEFAULT NULL COMMENT '官方文档链接',
  `remark` text COMMENT '备注',
  `sort` int unsigned DEFAULT '0' COMMENT '排序',
  `creator` bigint DEFAULT NULL COMMENT '创建者',
  `create_date` datetime DEFAULT NULL COMMENT '创建时间',
  `updater` bigint DEFAULT NULL COMMENT '更新者',
  `update_date` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_model_type` (`model_type`) COMMENT '模型类型索引'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='模型配置表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ai_model_provider`
--

DROP TABLE IF EXISTS `ai_model_provider`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ai_model_provider` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `provider_name` varchar(100) DEFAULT NULL COMMENT '提供商名称',
  `provider_type` varchar(50) DEFAULT NULL COMMENT '提供商类型',
  `api_base_url` varchar(200) DEFAULT NULL COMMENT 'API基础URL',
  `api_key` varchar(500) DEFAULT NULL COMMENT 'API密钥',
  `is_enabled` tinyint(1) DEFAULT '1' COMMENT '是否启用',
  `provider_config` text COMMENT '提供商配置',
  `creator` bigint DEFAULT NULL COMMENT '创建者',
  `create_date` datetime DEFAULT NULL COMMENT '创建时间',
  `updater` bigint DEFAULT NULL COMMENT '更新者',
  `update_date` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='模型提供商表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ai_ota`
--

DROP TABLE IF EXISTS `ai_ota`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ai_ota` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `version` varchar(50) DEFAULT NULL COMMENT '版本号',
  `firmware_url` varchar(500) DEFAULT NULL COMMENT '固件URL',
  `release_notes` text COMMENT '发布说明',
  `is_active` tinyint(1) DEFAULT '0' COMMENT '是否激活',
  `device_type` varchar(50) DEFAULT NULL COMMENT '设备类型',
  `creator` bigint DEFAULT NULL COMMENT '创建者',
  `create_date` datetime DEFAULT NULL COMMENT '创建时间',
  `updater` bigint DEFAULT NULL COMMENT '更新者',
  `update_date` datetime DEFAULT NULL COMMENT '更新时间',
  `checksum` varchar(100) DEFAULT NULL COMMENT '校验和',
  `file_size` bigint DEFAULT NULL COMMENT '文件大小',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='OTA升级表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ai_tts_voice`
--

DROP TABLE IF EXISTS `ai_tts_voice`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ai_tts_voice` (
  `id` varchar(32) NOT NULL COMMENT '主键',
  `voice_code` varchar(50) DEFAULT NULL COMMENT '音色编码',
  `voice_name` varchar(100) DEFAULT NULL COMMENT '音色名称',
  `language` varchar(50) DEFAULT NULL COMMENT '语言',
  `gender` varchar(10) DEFAULT NULL COMMENT '性别',
  `provider` varchar(50) DEFAULT NULL COMMENT '提供商',
  `is_enabled` tinyint(1) DEFAULT '1' COMMENT '是否启用',
  `voice_config` text COMMENT '音色配置',
  `creator` bigint DEFAULT NULL COMMENT '创建者',
  `create_date` datetime DEFAULT NULL COMMENT '创建时间',
  `updater` bigint DEFAULT NULL COMMENT '更新者',
  `update_date` datetime DEFAULT NULL COMMENT '更新时间',
  `sample_url` varchar(500) DEFAULT NULL COMMENT '样本URL',
  `voice_type` varchar(50) DEFAULT NULL COMMENT '音色类型',
  `sort` int unsigned DEFAULT '0' COMMENT '排序',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='TTS音色表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ai_voiceprint`
--

DROP TABLE IF EXISTS `ai_voiceprint`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ai_voiceprint` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `user_id` bigint DEFAULT NULL COMMENT '用户ID',
  `device_id` varchar(32) DEFAULT NULL COMMENT '设备ID',
  `voiceprint_name` varchar(100) DEFAULT NULL COMMENT '声纹名称',
  `voiceprint_data` text COMMENT '声纹数据',
  `voice_features` text COMMENT '声纹特征',
  `is_active` tinyint(1) DEFAULT '1' COMMENT '是否激活',
  `creator` bigint DEFAULT NULL COMMENT '创建者',
  `create_date` datetime DEFAULT NULL COMMENT '创建时间',
  `updater` bigint DEFAULT NULL COMMENT '更新者',
  `update_date` datetime DEFAULT NULL COMMENT '更新时间',
  `confidence_threshold` decimal(3,2) DEFAULT '0.80' COMMENT '置信度阈值',
  `training_samples` int DEFAULT '0' COMMENT '训练样本数',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='声纹表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `parent_profile`
--

DROP TABLE IF EXISTS `parent_profile`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `parent_profile` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `parent_name` varchar(100) DEFAULT NULL COMMENT '家长姓名',
  `email` varchar(100) DEFAULT NULL COMMENT '邮箱',
  `phone` varchar(20) DEFAULT NULL COMMENT '电话',
  `child_name` varchar(100) DEFAULT NULL COMMENT '孩子姓名',
  `child_age` int DEFAULT NULL COMMENT '孩子年龄',
  `preferences` text COMMENT '偏好设置',
  `safety_settings` text COMMENT '安全设置',
  `creator` bigint DEFAULT NULL COMMENT '创建者',
  `create_date` datetime DEFAULT NULL COMMENT '创建时间',
  `updater` bigint DEFAULT NULL COMMENT '更新者',
  `update_date` datetime DEFAULT NULL COMMENT '更新时间',
  `status` tinyint DEFAULT '1' COMMENT '状态',
  `language_preference` varchar(50) DEFAULT 'English' COMMENT '语言偏好',
  `timezone` varchar(50) DEFAULT NULL COMMENT '时区',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='家长档案表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sys_dict_data`
--

DROP TABLE IF EXISTS `sys_dict_data`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sys_dict_data` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `dict_type_id` bigint DEFAULT NULL COMMENT '字典类型ID',
  `dict_label` varchar(100) DEFAULT NULL COMMENT '字典标签',
  `dict_value` varchar(100) DEFAULT NULL COMMENT '字典值',
  `dict_type` varchar(100) DEFAULT NULL COMMENT '字典类型',
  `css_class` varchar(100) DEFAULT NULL COMMENT 'CSS类名',
  `list_class` varchar(100) DEFAULT NULL COMMENT '列表类名',
  `is_default` tinyint(1) DEFAULT '0' COMMENT '是否默认',
  `status` tinyint DEFAULT '1' COMMENT '状态',
  `creator` bigint DEFAULT NULL COMMENT '创建者',
  `create_date` datetime DEFAULT NULL COMMENT '创建时间',
  `sort` int DEFAULT NULL COMMENT '排序',
  `remark` varchar(255) DEFAULT NULL COMMENT '备注',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='字典数据表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sys_dict_type`
--

DROP TABLE IF EXISTS `sys_dict_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sys_dict_type` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `dict_name` varchar(100) DEFAULT NULL COMMENT '字典名称',
  `dict_type` varchar(100) DEFAULT NULL COMMENT '字典类型',
  `status` tinyint DEFAULT '1' COMMENT '状态',
  `creator` bigint DEFAULT NULL COMMENT '创建者',
  `create_date` datetime DEFAULT NULL COMMENT '创建时间',
  `updater` bigint DEFAULT NULL COMMENT '更新者',
  `update_date` datetime DEFAULT NULL COMMENT '更新时间',
  `remark` varchar(500) DEFAULT NULL COMMENT '备注',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='字典类型表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sys_params`
--

DROP TABLE IF EXISTS `sys_params`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sys_params` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `param_code` varchar(100) DEFAULT NULL COMMENT '参数编码',
  `param_value` varchar(2000) DEFAULT NULL COMMENT '参数值',
  `value_type` varchar(20) DEFAULT 'string' COMMENT '值类型',
  `param_type` tinyint unsigned DEFAULT '1' COMMENT '参数类型',
  `remark` varchar(200) DEFAULT NULL COMMENT '备注',
  `creator` bigint DEFAULT NULL COMMENT '创建者',
  `create_date` datetime DEFAULT NULL COMMENT '创建时间',
  `updater` bigint DEFAULT NULL COMMENT '更新者',
  `update_date` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `param_code` (`param_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='系统参数表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sys_user` (EMPTY)
--

DROP TABLE IF EXISTS `sys_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sys_user` (
  `user_id` bigint NOT NULL AUTO_INCREMENT COMMENT '用户ID',
  `username` varchar(50) NOT NULL COMMENT '用户名',
  `password` varchar(100) DEFAULT NULL COMMENT '密码',
  `salt` varchar(20) DEFAULT NULL COMMENT '盐',
  `email` varchar(100) DEFAULT NULL COMMENT '邮箱',
  `mobile` varchar(100) DEFAULT NULL COMMENT '手机号',
  `status` tinyint DEFAULT NULL COMMENT '状态',
  `creator` bigint DEFAULT NULL COMMENT '创建者',
  `create_date` datetime DEFAULT NULL COMMENT '创建时间',
  `updater` bigint DEFAULT NULL COMMENT '更新者',
  `update_date` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='系统用户表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sys_user_token`
--

DROP TABLE IF EXISTS `sys_user_token`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sys_user_token` (
  `user_id` bigint NOT NULL COMMENT '用户ID',
  `token` varchar(100) NOT NULL COMMENT '令牌',
  `expire_date` datetime DEFAULT NULL COMMENT '过期时间',
  `update_date` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `token` (`token`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='系统用户令牌表';
/*!40101 SET character_set_client = @saved_cs_client */;

SET FOREIGN_KEY_CHECKS = 1;

-- Now we need to populate with data from original DB excluding agents/devices/users
-- But first insert essential system parameters
INSERT INTO `sys_params` (`param_code`, `param_value`, `value_type`, `param_type`, `remark`, `creator`, `create_date`, `updater`, `update_date`) VALUES
('sys.name', 'XiaoZhi ESP32 Manager', 'string', 1, 'System name configuration', NULL, NOW(), NULL, NOW()),
('ai.default.memory', 'Memory_mem_local_short', 'string', 1, 'Default memory model for AI agents', NULL, NOW(), NULL, NOW()),
('ai.default.chat_history', '1', 'string', 1, 'Default chat history configuration (1=text enabled)', NULL, NOW(), NULL, NOW()),
('ai.agent.name.max_length', '100', 'string', 1, 'Maximum length for agent names', NULL, NOW(), NULL, NOW()),
('ai.agent.prompt.max_length', '4000', 'string', 1, 'Maximum length for system prompts', NULL, NOW(), NULL, NOW());

/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;
/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- =============================================
-- Clean Original Schema Migration Complete
-- =============================================
-- This creates a database with:
-- ✓ EXACT original schema structure
-- ✓ Only Cheeko template (no pre-created agents)
-- ✓ Empty user management (users create their own)
-- ✓ Empty device management (users register devices)
-- ✓ Essential system configurations
-- ✓ Default memory model: Memory_mem_local_short
-- ✓ Default chat history: Report Text enabled (1)
-- ✓ Max prompt length: 4000 characters
-- =============================================