-- MySQL dump 10.13  Distrib 8.0.43, for Linux (x86_64)
--
-- Host: localhost    Database: manager_api
-- ------------------------------------------------------
-- Server version	8.0.43

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
  `ID` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `AUTHOR` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `FILENAME` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `DATEEXECUTED` datetime NOT NULL,
  `ORDEREXECUTED` int NOT NULL,
  `EXECTYPE` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL,
  `MD5SUM` varchar(35) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `DESCRIPTION` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `COMMENTS` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `TAG` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `LIQUIBASE` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `CONTEXTS` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `LABELS` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `DEPLOYMENT_ID` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
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
  `LOCKEDBY` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ai_agent`
--

DROP TABLE IF EXISTS `ai_agent`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ai_agent` (
  `id` varchar(32) NOT NULL COMMENT '智能体唯一标识',
  `user_id` bigint DEFAULT NULL COMMENT '所属用户 ID',
  `agent_code` varchar(36) DEFAULT NULL COMMENT '智能体编码',
  `agent_name` varchar(64) DEFAULT NULL COMMENT '智能体名称',
  `asr_model_id` varchar(32) DEFAULT NULL COMMENT '语音识别模型标识',
  `vad_model_id` varchar(64) DEFAULT NULL COMMENT '语音活动检测标识',
  `llm_model_id` varchar(32) DEFAULT NULL COMMENT '大语言模型标识',
  `vllm_model_id` varchar(32) DEFAULT 'VLLM_ChatGLMVLLM' COMMENT '视觉模型标识',
  `tts_model_id` varchar(32) DEFAULT NULL COMMENT '语音合成模型标识',
  `tts_voice_id` varchar(32) DEFAULT NULL COMMENT '音色标识',
  `mem_model_id` varchar(32) DEFAULT NULL COMMENT '记忆模型标识',
  `intent_model_id` varchar(32) DEFAULT NULL COMMENT '意图模型标识',
  `system_prompt` text COMMENT '角色设定参数',
  `summary_memory` text COMMENT '总结记忆',
  `chat_history_conf` tinyint NOT NULL DEFAULT '0' COMMENT '聊天记录配置（0不记录 1仅记录文本 2记录文本和语音）',
  `lang_code` varchar(10) DEFAULT NULL COMMENT '语言编码',
  `language` varchar(10) DEFAULT NULL COMMENT '交互语种',
  `sort` int unsigned DEFAULT '0' COMMENT '排序权重',
  `creator` bigint DEFAULT NULL COMMENT '创建者 ID',
  `created_at` datetime DEFAULT NULL COMMENT '创建时间',
  `updater` bigint DEFAULT NULL COMMENT '更新者 ID',
  `updated_at` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_ai_agent_user_id` (`user_id`) COMMENT '创建用户的索引，用于快速查找用户下的智能体信息'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='智能体配置表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ai_agent_chat_audio`
--

DROP TABLE IF EXISTS `ai_agent_chat_audio`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ai_agent_chat_audio` (
  `id` varchar(32) NOT NULL COMMENT '主键ID',
  `audio` longblob COMMENT '音频opus数据',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='智能体聊天音频数据表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ai_agent_chat_history`
--

DROP TABLE IF EXISTS `ai_agent_chat_history`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ai_agent_chat_history` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `mac_address` varchar(50) DEFAULT NULL COMMENT 'MAC地址',
  `agent_id` varchar(64) DEFAULT NULL,
  `session_id` varchar(50) DEFAULT NULL COMMENT '会话ID',
  `chat_type` tinyint DEFAULT NULL COMMENT '消息类型: 1-用户, 2-智能体',
  `content` varchar(1024) DEFAULT NULL COMMENT '聊天内容',
  `audio_id` varchar(32) DEFAULT NULL COMMENT '音频ID',
  `created_at` datetime(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '创建时间',
  `updated_at` datetime(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_ai_agent_chat_history_mac` (`mac_address`),
  KEY `idx_ai_agent_chat_history_session_id` (`session_id`),
  KEY `idx_ai_agent_chat_history_agent_id` (`agent_id`),
  KEY `idx_ai_agent_chat_history_agent_session_created` (`agent_id`,`session_id`,`created_at`)
) ENGINE=InnoDB AUTO_INCREMENT=489 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='智能体聊天记录表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ai_agent_plugin_mapping`
--

DROP TABLE IF EXISTS `ai_agent_plugin_mapping`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ai_agent_plugin_mapping` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `agent_id` varchar(32) NOT NULL COMMENT '智能体ID',
  `plugin_id` varchar(32) NOT NULL COMMENT '插件ID',
  `param_info` json NOT NULL COMMENT '参数信息',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_agent_provider` (`agent_id`,`plugin_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1971477388619079685 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='Agent与插件的唯一映射表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ai_agent_template`
--

DROP TABLE IF EXISTS `ai_agent_template`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ai_agent_template` (
  `id` varchar(32) NOT NULL COMMENT '智能体唯一标识',
  `agent_code` varchar(36) DEFAULT NULL COMMENT '智能体编码',
  `agent_name` varchar(64) DEFAULT NULL COMMENT '智能体名称',
  `asr_model_id` varchar(32) DEFAULT NULL COMMENT '语音识别模型标识',
  `vad_model_id` varchar(64) DEFAULT NULL COMMENT '语音活动检测标识',
  `llm_model_id` varchar(32) DEFAULT NULL COMMENT '大语言模型标识',
  `vllm_model_id` varchar(32) DEFAULT 'VLLM_ChatGLMVLLM' COMMENT '视觉模型标识',
  `tts_model_id` varchar(32) DEFAULT NULL COMMENT '语音合成模型标识',
  `tts_voice_id` varchar(32) DEFAULT NULL COMMENT '音色标识',
  `mem_model_id` varchar(32) DEFAULT NULL COMMENT '记忆模型标识',
  `intent_model_id` varchar(32) DEFAULT NULL COMMENT '意图模型标识',
  `system_prompt` text COMMENT '角色设定参数',
  `summary_memory` text COMMENT '总结记忆',
  `chat_history_conf` tinyint NOT NULL DEFAULT '0' COMMENT '聊天记录配置（0不记录 1仅记录文本 2记录文本和语音）',
  `lang_code` varchar(10) DEFAULT NULL COMMENT '语言编码',
  `language` varchar(10) DEFAULT NULL COMMENT '交互语种',
  `sort` int unsigned DEFAULT '0' COMMENT '排序权重',
  `is_visible` tinyint NOT NULL DEFAULT '0' COMMENT '是否在应用中显示（0不显示 1显示）',
  `creator` bigint DEFAULT NULL COMMENT '创建者 ID',
  `created_at` datetime DEFAULT NULL COMMENT '创建时间',
  `updater` bigint DEFAULT NULL COMMENT '更新者 ID',
  `updated_at` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='智能体配置模板表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ai_agent_voice_print`
--

DROP TABLE IF EXISTS `ai_agent_voice_print`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ai_agent_voice_print` (
  `id` varchar(32) NOT NULL COMMENT '声纹ID',
  `agent_id` varchar(32) NOT NULL COMMENT '关联的智能体ID',
  `source_name` varchar(50) NOT NULL COMMENT '声纹来源的人的姓名',
  `introduce` varchar(200) DEFAULT NULL COMMENT '描述声纹来源的这个人',
  `create_date` datetime DEFAULT NULL COMMENT '创建时间',
  `creator` bigint DEFAULT NULL COMMENT '创建者',
  `update_date` datetime DEFAULT NULL COMMENT '修改时间',
  `updater` bigint DEFAULT NULL COMMENT '修改者',
  `audio_id` varchar(32) NOT NULL COMMENT '音频ID',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='智能体声纹表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ai_device`
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
  KEY `idx_ai_model_config_model_type` (`model_type`) COMMENT '创建模型类型的索引，用于快速查找特定类型下的所有配置信息'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='模型配置表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ai_model_provider`
--

DROP TABLE IF EXISTS `ai_model_provider`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ai_model_provider` (
  `id` varchar(32) NOT NULL COMMENT '主键',
  `model_type` varchar(20) DEFAULT NULL COMMENT '模型类型(Memory/ASR/VAD/LLM/TTS)',
  `provider_code` varchar(50) DEFAULT NULL COMMENT '供应器类型',
  `name` varchar(50) DEFAULT NULL COMMENT '供应器名称',
  `fields` json DEFAULT NULL COMMENT '供应器字段列表(JSON格式)',
  `sort` int unsigned DEFAULT '0' COMMENT '排序',
  `creator` bigint DEFAULT NULL COMMENT '创建者',
  `create_date` datetime DEFAULT NULL COMMENT '创建时间',
  `updater` bigint DEFAULT NULL COMMENT '更新者',
  `update_date` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_ai_model_provider_model_type` (`model_type`) COMMENT '创建模型类型的索引，用于快速查找特定类型下的所有供应器信息'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='模型配置表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ai_ota`
--

DROP TABLE IF EXISTS `ai_ota`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ai_ota` (
  `id` varchar(32) NOT NULL COMMENT 'ID',
  `firmware_name` varchar(100) DEFAULT NULL COMMENT '固件名称',
  `type` varchar(50) DEFAULT NULL COMMENT '固件类型',
  `version` varchar(50) DEFAULT NULL COMMENT '版本号',
  `size` bigint DEFAULT NULL COMMENT '文件大小(字节)',
  `remark` varchar(500) DEFAULT NULL COMMENT '备注/说明',
  `firmware_path` varchar(255) DEFAULT NULL COMMENT '固件路径',
  `sort` int unsigned DEFAULT '0' COMMENT '排序',
  `updater` bigint DEFAULT NULL COMMENT '更新者',
  `update_date` datetime DEFAULT NULL COMMENT '更新时间',
  `creator` bigint DEFAULT NULL COMMENT '创建者',
  `create_date` datetime DEFAULT NULL COMMENT '创建时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='固件信息表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ai_tts_voice`
--

DROP TABLE IF EXISTS `ai_tts_voice`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ai_tts_voice` (
  `id` varchar(32) NOT NULL COMMENT '主键',
  `tts_model_id` varchar(32) DEFAULT NULL COMMENT '对应 TTS 模型主键',
  `name` varchar(20) DEFAULT NULL COMMENT '音色名称',
  `tts_voice` varchar(50) DEFAULT NULL COMMENT '音色编码',
  `languages` varchar(50) DEFAULT NULL COMMENT '语言',
  `voice_demo` varchar(500) DEFAULT NULL COMMENT '音色 Demo',
  `remark` varchar(255) DEFAULT NULL COMMENT '备注',
  `reference_audio` varchar(500) DEFAULT NULL COMMENT '参考音频路径',
  `reference_text` varchar(500) DEFAULT NULL COMMENT '参考文本',
  `sort` int unsigned DEFAULT '0' COMMENT '排序',
  `creator` bigint DEFAULT NULL COMMENT '创建者',
  `create_date` datetime DEFAULT NULL COMMENT '创建时间',
  `updater` bigint DEFAULT NULL COMMENT '更新者',
  `update_date` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_ai_tts_voice_tts_model_id` (`tts_model_id`) COMMENT '创建 TTS 模型主键的索引，用于快速查找对应模型的音色信息'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='TTS 音色表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ai_voiceprint`
--

DROP TABLE IF EXISTS `ai_voiceprint`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ai_voiceprint` (
  `id` varchar(32) NOT NULL COMMENT '声纹唯一标识',
  `name` varchar(64) DEFAULT NULL COMMENT '声纹名称',
  `user_id` bigint DEFAULT NULL COMMENT '用户 ID（关联用户表）',
  `agent_id` varchar(32) DEFAULT NULL COMMENT '关联智能体 ID',
  `agent_code` varchar(36) DEFAULT NULL COMMENT '关联智能体编码',
  `agent_name` varchar(36) DEFAULT NULL COMMENT '关联智能体名称',
  `description` varchar(255) DEFAULT NULL COMMENT '声纹描述',
  `embedding` longtext COMMENT '声纹特征向量（JSON 数组格式）',
  `memory` text COMMENT '关联记忆数据',
  `sort` int unsigned DEFAULT '0' COMMENT '排序权重',
  `creator` bigint DEFAULT NULL COMMENT '创建者 ID',
  `created_at` datetime DEFAULT NULL COMMENT '创建时间',
  `updater` bigint DEFAULT NULL COMMENT '更新者 ID',
  `updated_at` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='声纹识别表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `parent_profile`
--

DROP TABLE IF EXISTS `parent_profile`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `parent_profile` (
  `id` bigint NOT NULL COMMENT 'Primary key ID',
  `user_id` bigint NOT NULL COMMENT 'Foreign key to sys_user table',
  `supabase_user_id` varchar(255) DEFAULT NULL COMMENT 'Supabase user ID for reference',
  `full_name` varchar(255) DEFAULT NULL COMMENT 'Parent full name',
  `email` varchar(255) DEFAULT NULL COMMENT 'Parent email address',
  `phone_number` varchar(50) DEFAULT NULL COMMENT 'Parent phone number',
  `preferred_language` varchar(10) DEFAULT 'en' COMMENT 'Preferred language code (en, es, fr, etc.)',
  `timezone` varchar(100) DEFAULT 'UTC' COMMENT 'User timezone',
  `notification_preferences` json DEFAULT NULL COMMENT 'JSON object with notification settings',
  `onboarding_completed` tinyint(1) DEFAULT '0' COMMENT 'Whether onboarding is completed',
  `terms_accepted_at` datetime DEFAULT NULL COMMENT 'When terms of service were accepted',
  `privacy_policy_accepted_at` datetime DEFAULT NULL COMMENT 'When privacy policy was accepted',
  `creator` bigint DEFAULT NULL COMMENT 'User who created this record',
  `create_date` datetime DEFAULT CURRENT_TIMESTAMP COMMENT 'Creation timestamp',
  `updater` bigint DEFAULT NULL COMMENT 'User who last updated this record',
  `update_date` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Last update timestamp',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_id` (`user_id`),
  UNIQUE KEY `uk_supabase_user_id` (`supabase_user_id`),
  KEY `idx_email` (`email`),
  KEY `idx_phone_number` (`phone_number`),
  CONSTRAINT `parent_profile_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `sys_user` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='Parent profile table for mobile app users';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sys_dict_data`
--

DROP TABLE IF EXISTS `sys_dict_data`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sys_dict_data` (
  `id` bigint NOT NULL COMMENT 'id',
  `dict_type_id` bigint NOT NULL COMMENT '字典类型ID',
  `dict_label` varchar(255) NOT NULL COMMENT '字典标签',
  `dict_value` varchar(255) DEFAULT NULL COMMENT '字典值',
  `remark` varchar(255) DEFAULT NULL COMMENT '备注',
  `sort` int unsigned DEFAULT NULL COMMENT '排序',
  `creator` bigint DEFAULT NULL COMMENT '创建者',
  `create_date` datetime DEFAULT NULL COMMENT '创建时间',
  `updater` bigint DEFAULT NULL COMMENT '更新者',
  `update_date` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_dict_type_value` (`dict_type_id`,`dict_value`),
  KEY `idx_sort` (`sort`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='字典数据';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sys_dict_type`
--

DROP TABLE IF EXISTS `sys_dict_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sys_dict_type` (
  `id` bigint NOT NULL COMMENT 'id',
  `dict_type` varchar(100) NOT NULL COMMENT '字典类型',
  `dict_name` varchar(255) NOT NULL COMMENT '字典名称',
  `remark` varchar(255) DEFAULT NULL COMMENT '备注',
  `sort` int unsigned DEFAULT NULL COMMENT '排序',
  `creator` bigint DEFAULT NULL COMMENT '创建者',
  `create_date` datetime DEFAULT NULL COMMENT '创建时间',
  `updater` bigint DEFAULT NULL COMMENT '更新者',
  `update_date` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `dict_type` (`dict_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='字典类型';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sys_params`
--

DROP TABLE IF EXISTS `sys_params`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sys_params` (
  `id` bigint NOT NULL COMMENT 'id',
  `param_code` varchar(100) DEFAULT NULL COMMENT '参数编码',
  `param_value` varchar(2000) DEFAULT NULL COMMENT '参数值',
  `value_type` varchar(20) DEFAULT 'string' COMMENT '值类型：string-字符串，number-数字，boolean-布尔，array-数组',
  `param_type` tinyint unsigned DEFAULT '1' COMMENT '类型   0：系统参数   1：非系统参数',
  `remark` varchar(200) DEFAULT NULL COMMENT '备注',
  `creator` bigint DEFAULT NULL COMMENT '创建者',
  `create_date` datetime DEFAULT NULL COMMENT '创建时间',
  `updater` bigint DEFAULT NULL COMMENT '更新者',
  `update_date` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_param_code` (`param_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='参数管理';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sys_user`
--

DROP TABLE IF EXISTS `sys_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sys_user` (
  `id` bigint NOT NULL COMMENT 'id',
  `username` varchar(50) NOT NULL COMMENT '用户名',
  `password` varchar(100) DEFAULT NULL COMMENT '密码',
  `super_admin` tinyint unsigned DEFAULT NULL COMMENT '超级管理员   0：否   1：是',
  `status` tinyint DEFAULT NULL COMMENT '状态  0：停用   1：正常',
  `create_date` datetime DEFAULT NULL COMMENT '创建时间',
  `updater` bigint DEFAULT NULL COMMENT '更新者',
  `creator` bigint DEFAULT NULL COMMENT '创建者',
  `update_date` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='系统用户';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sys_user_token`
--

DROP TABLE IF EXISTS `sys_user_token`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sys_user_token` (
  `id` bigint NOT NULL COMMENT 'id',
  `user_id` bigint NOT NULL COMMENT '用户id',
  `token` varchar(100) NOT NULL COMMENT '用户token',
  `expire_date` datetime DEFAULT NULL COMMENT '过期时间',
  `update_date` datetime DEFAULT NULL COMMENT '更新时间',
  `create_date` datetime DEFAULT NULL COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  UNIQUE KEY `token` (`token`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='系统用户Token';
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-09-26 20:50:51
