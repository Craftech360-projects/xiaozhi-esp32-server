-- ===================================================================
-- XIAOZHI ESP32 SERVER - COMPLETE SCHEMA MIGRATION SCRIPT
-- ===================================================================
-- This script creates the complete database schema with essential
-- configuration data only (NO user accounts, agents, or devices)
-- Compatible with MySQL 8.0+
-- Generated: 2025-09-27 12:52:03
--
-- FEATURES:
-- - Complete database schema (all tables and indexes)
-- - Essential system configuration data only
-- - Cheeko agent template included
-- - Default TTS voices included
-- - All API keys replaced with placeholders
-- - NO user accounts, agents, devices, or personal data
-- ===================================================================

-- MySQL compatibility settings
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

-- Create database if not exists
-- CREATE DATABASE IF NOT EXISTS `manager_api_fresh` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
-- USE `manager_api_fresh`;

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

--
-- Dumping data for table `sys_dict_type`
--

-- Data for table `sys_dict_type`
LOCK TABLES `sys_dict_type` WRITE;
/*!40000 ALTER TABLE `sys_dict_type` DISABLE KEYS */;
INSERT INTO `sys_dict_type` (`id`,`dict_type`,`dict_name`,`remark`,`sort`,`creator`,`create_date`,`updater`,`update_date`) VALUES
(101,'FIRMWARE_TYPE','Firmware Type','Firmware types dictionary',0,1,'2025-09-19 14:50:44',1,'2025-09-19 14:50:44'),
(102,'MOBILE_AREA','Mobile Area','Mobile area codes dictionary',0,1,'2025-09-19 14:50:45',1,'2025-09-19 14:50:45');
/*!40000 ALTER TABLE `sys_dict_type` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `sys_dict_data`
--

-- Data for table `sys_dict_data`
LOCK TABLES `sys_dict_data` WRITE;
/*!40000 ALTER TABLE `sys_dict_data` DISABLE KEYS */;
INSERT INTO `sys_dict_data` (`id`,`dict_type_id`,`dict_label`,`dict_value`,`remark`,`sort`,`creator`,`create_date`,`updater`,`update_date`) VALUES
(101001,101,'面包板新版接线（WiFi）','bread-compact-wifi','面包板新版接线（WiFi）',1,1,'2025-09-19 14:50:44',1,'2025-09-19 14:50:44'),
(101002,101,'面包板新版接线（WiFi）+ LCD','bread-compact-wifi-lcd','面包板新版接线（WiFi）+ LCD',2,1,'2025-09-19 14:50:44',1,'2025-09-19 14:50:44'),
(101003,101,'面包板新版接线（ML307 AT）','bread-compact-ml307','面包板新版接线（ML307 AT）',3,1,'2025-09-19 14:50:44',1,'2025-09-19 14:50:44'),
(101004,101,'面包板（WiFi） ESP32 DevKit','bread-compact-esp32','面包板（WiFi） ESP32 DevKit',4,1,'2025-09-19 14:50:44',1,'2025-09-19 14:50:44'),
(101005,101,'面包板（WiFi+ LCD） ESP32 DevKit','bread-compact-esp32-lcd','面包板（WiFi+ LCD） ESP32 DevKit',5,1,'2025-09-19 14:50:44',1,'2025-09-19 14:50:44'),
(101006,101,'DFRobot 行空板 k10','df-k10','DFRobot 行空板 k10',6,1,'2025-09-19 14:50:44',1,'2025-09-19 14:50:44'),
(101007,101,'ESP32 CGC','esp32-cgc','ESP32 CGC',7,1,'2025-09-19 14:50:44',1,'2025-09-19 14:50:44'),
(101008,101,'ESP BOX 3','esp-box-3','ESP BOX 3',8,1,'2025-09-19 14:50:44',1,'2025-09-19 14:50:44'),
(101009,101,'ESP BOX','esp-box','ESP BOX',9,1,'2025-09-19 14:50:44',1,'2025-09-19 14:50:44'),
(101010,101,'ESP BOX Lite','esp-box-lite','ESP BOX Lite',10,1,'2025-09-19 14:50:44',1,'2025-09-19 14:50:44'),
(101011,101,'Kevin Box 1','kevin-box-1','Kevin Box 1',11,1,'2025-09-19 14:50:44',1,'2025-09-19 14:50:44'),
(101012,101,'Kevin Box 2','kevin-box-2','Kevin Box 2',12,1,'2025-09-19 14:50:44',1,'2025-09-19 14:50:44'),
(101013,101,'Kevin C3','kevin-c3','Kevin C3',13,1,'2025-09-19 14:50:44',1,'2025-09-19 14:50:44'),
(101014,101,'Kevin SP V3开发板','kevin-sp-v3-dev','Kevin SP V3开发板',14,1,'2025-09-19 14:50:44',1,'2025-09-19 14:50:44'),
(101015,101,'Kevin SP V4开发板','kevin-sp-v4-dev','Kevin SP V4开发板',15,1,'2025-09-19 14:50:44',1,'2025-09-19 14:50:44'),
(101016,101,'鱼鹰科技3.13LCD开发板','kevin-yuying-313lcd','鱼鹰科技3.13LCD开发板',16,1,'2025-09-19 14:50:44',1,'2025-09-19 14:50:44'),
(101017,101,'立创·实战派ESP32-S3开发板','lichuang-dev','立创·实战派ESP32-S3开发板',17,1,'2025-09-19 14:50:44',1,'2025-09-19 14:50:44'),
(101018,101,'立创·实战派ESP32-C3开发板','lichuang-c3-dev','立创·实战派ESP32-C3开发板',18,1,'2025-09-19 14:50:44',1,'2025-09-19 14:50:44'),
(101019,101,'神奇按钮 Magiclick_2.4','magiclick-2p4','神奇按钮 Magiclick_2.4',19,1,'2025-09-19 14:50:44',1,'2025-09-19 14:50:44'),
(101020,101,'神奇按钮 Magiclick_2.5','magiclick-2p5','神奇按钮 Magiclick_2.5',20,1,'2025-09-19 14:50:44',1,'2025-09-19 14:50:44'),
(101021,101,'神奇按钮 Magiclick_C3','magiclick-c3','神奇按钮 Magiclick_C3',21,1,'2025-09-19 14:50:44',1,'2025-09-19 14:50:44'),
(101022,101,'神奇按钮 Magiclick_C3_v2','magiclick-c3-v2','神奇按钮 Magiclick_C3_v2',22,1,'2025-09-19 14:50:44',1,'2025-09-19 14:50:44'),
(101023,101,'M5Stack CoreS3','m5stack-core-s3','M5Stack CoreS3',23,1,'2025-09-19 14:50:44',1,'2025-09-19 14:50:44'),
(101024,101,'AtomS3 + Echo Base','atoms3-echo-base','AtomS3 + Echo Base',24,1,'2025-09-19 14:50:44',1,'2025-09-19 14:50:44'),
(101025,101,'AtomS3R + Echo Base','atoms3r-echo-base','AtomS3R + Echo Base',25,1,'2025-09-19 14:50:44',1,'2025-09-19 14:50:44'),
(101026,101,'AtomS3R CAM/M12 + Echo Base','atoms3r-cam-m12-echo-base','AtomS3R CAM/M12 + Echo Base',26,1,'2025-09-19 14:50:44',1,'2025-09-19 14:50:44'),
(101027,101,'AtomMatrix + Echo Base','atommatrix-echo-base','AtomMatrix + Echo Base',27,1,'2025-09-19 14:50:44',1,'2025-09-19 14:50:44'),
(101028,101,'虾哥 Mini C3','xmini-c3','虾哥 Mini C3',28,1,'2025-09-19 14:50:44',1,'2025-09-19 14:50:44'),
(101029,101,'ESP32S3_KORVO2_V3开发板','esp32s3-korvo2-v3','ESP32S3_KORVO2_V3开发板',29,1,'2025-09-19 14:50:44',1,'2025-09-19 14:50:44'),
(101030,101,'ESP-SparkBot开发板','esp-sparkbot','ESP-SparkBot开发板',30,1,'2025-09-19 14:50:44',1,'2025-09-19 14:50:44'),
(101031,101,'ESP-Spot-S3','esp-spot-s3','ESP-Spot-S3',31,1,'2025-09-19 14:50:44',1,'2025-09-19 14:50:44'),
(101032,101,'Waveshare ESP32-S3-Touch-AMOLED-1.8','esp32-s3-touch-amoled-1.8','Waveshare ESP32-S3-Touch-AMOLED-1.8',32,1,'2025-09-19 14:50:44',1,'2025-09-19 14:50:44'),
(101033,101,'Waveshare ESP32-S3-Touch-LCD-1.85C','esp32-s3-touch-lcd-1.85c','Waveshare ESP32-S3-Touch-LCD-1.85C',33,1,'2025-09-19 14:50:44',1,'2025-09-19 14:50:44'),
(101034,101,'Waveshare ESP32-S3-Touch-LCD-1.85','esp32-s3-touch-lcd-1.85','Waveshare ESP32-S3-Touch-LCD-1.85',34,1,'2025-09-19 14:50:44',1,'2025-09-19 14:50:44'),
(101035,101,'Waveshare ESP32-S3-Touch-LCD-1.46','esp32-s3-touch-lcd-1.46','Waveshare ESP32-S3-Touch-LCD-1.46',35,1,'2025-09-19 14:50:44',1,'2025-09-19 14:50:44'),
(101036,101,'Waveshare ESP32-S3-Touch-LCD-3.5','esp32-s3-touch-lcd-3.5','Waveshare ESP32-S3-Touch-LCD-3.5',36,1,'2025-09-19 14:50:44',1,'2025-09-19 14:50:44'),
(101037,101,'土豆子','tudouzi','土豆子',37,1,'2025-09-19 14:50:44',1,'2025-09-19 14:50:44'),
(101038,101,'LILYGO T-Circle-S3','lilygo-t-circle-s3','LILYGO T-Circle-S3',38,1,'2025-09-19 14:50:44',1,'2025-09-19 14:50:44'),
(101039,101,'LILYGO T-CameraPlus-S3','lilygo-t-cameraplus-s3','LILYGO T-CameraPlus-S3',39,1,'2025-09-19 14:50:44',1,'2025-09-19 14:50:44'),
(101040,101,'Movecall Moji 小智AI衍生版','movecall-moji-esp32s3','Movecall Moji 小智AI衍生版',40,1,'2025-09-19 14:50:44',1,'2025-09-19 14:50:44'),
(101041,101,'Movecall CuiCan 璀璨·AI吊坠','movecall-cuican-esp32s3','Movecall CuiCan 璀璨·AI吊坠',41,1,'2025-09-19 14:50:44',1,'2025-09-19 14:50:44'),
(101042,101,'正点原子DNESP32S3开发板','atk-dnesp32s3','正点原子DNESP32S3开发板',42,1,'2025-09-19 14:50:44',1,'2025-09-19 14:50:44'),
(101043,101,'正点原子DNESP32S3-BOX','atk-dnesp32s3-box','正点原子DNESP32S3-BOX',43,1,'2025-09-19 14:50:44',1,'2025-09-19 14:50:44'),
(101044,101,'嘟嘟开发板CHATX(wifi)','du-chatx','嘟嘟开发板CHATX(wifi)',44,1,'2025-09-19 14:50:44',1,'2025-09-19 14:50:44'),
(101045,101,'太极小派esp32s3','taiji-pi-s3','太极小派esp32s3',45,1,'2025-09-19 14:50:44',1,'2025-09-19 14:50:44'),
(101046,101,'无名科技星智0.85(WIFI)','xingzhi-cube-0.85tft-wifi','无名科技星智0.85(WIFI)',46,1,'2025-09-19 14:50:44',1,'2025-09-19 14:50:44'),
(101047,101,'无名科技星智0.85(ML307)','xingzhi-cube-0.85tft-ml307','无名科技星智0.85(ML307)',47,1,'2025-09-19 14:50:44',1,'2025-09-19 14:50:44'),
(101048,101,'无名科技星智0.96(WIFI)','xingzhi-cube-0.96oled-wifi','无名科技星智0.96(WIFI)',48,1,'2025-09-19 14:50:44',1,'2025-09-19 14:50:44'),
(101049,101,'无名科技星智0.96(ML307)','xingzhi-cube-0.96oled-ml307','无名科技星智0.96(ML307)',49,1,'2025-09-19 14:50:44',1,'2025-09-19 14:50:44'),
(101050,101,'无名科技星智1.54(WIFI)','xingzhi-cube-1.54tft-wifi','无名科技星智1.54(WIFI)',50,1,'2025-09-19 14:50:44',1,'2025-09-19 14:50:44'),
(101051,101,'无名科技星智1.54(ML307)','xingzhi-cube-1.54tft-ml307','无名科技星智1.54(ML307)',51,1,'2025-09-19 14:50:44',1,'2025-09-19 14:50:44'),
(101052,101,'SenseCAP Watcher','sensecap-watcher','SenseCAP Watcher',52,1,'2025-09-19 14:50:44',1,'2025-09-19 14:50:44'),
(101053,101,'四博智联AI陪伴盒子','doit-s3-aibox','四博智联AI陪伴盒子',53,1,'2025-09-19 14:50:44',1,'2025-09-19 14:50:44'),
(101054,101,'元控·青春','mixgo-nova','元控·青春',54,1,'2025-09-19 14:50:44',1,'2025-09-19 14:50:44'),
(101055,101,'doit-ai-01-kit','doit-ai-01-kit','DoIT AI 01 Kit',1,1,'2025-09-27 15:00:00',1,'2025-09-27 15:00:00'),
(102001,102,'中国大陆','+86','中国大陆',1,1,'2025-09-19 14:50:45',1,'2025-09-19 14:50:45'),
(102002,102,'中国香港','+852','中国香港',2,1,'2025-09-19 14:50:45',1,'2025-09-19 14:50:45'),
(102003,102,'中国澳门','+853','中国澳门',3,1,'2025-09-19 14:50:45',1,'2025-09-19 14:50:45'),
(102004,102,'中国台湾','+886','中国台湾',4,1,'2025-09-19 14:50:45',1,'2025-09-19 14:50:45'),
(102005,102,'美国/加拿大','+1','美国/加拿大',5,1,'2025-09-19 14:50:45',1,'2025-09-19 14:50:45'),
(102006,102,'英国','+44','英国',6,1,'2025-09-19 14:50:45',1,'2025-09-19 14:50:45'),
(102007,102,'法国','+33','法国',7,1,'2025-09-19 14:50:45',1,'2025-09-19 14:50:45'),
(102008,102,'意大利','+39','意大利',8,1,'2025-09-19 14:50:45',1,'2025-09-19 14:50:45'),
(102009,102,'德国','+49','德国',9,1,'2025-09-19 14:50:45',1,'2025-09-19 14:50:45'),
(102010,102,'波兰','+48','波兰',10,1,'2025-09-19 14:50:45',1,'2025-09-19 14:50:45'),
(102011,102,'瑞士','+41','瑞士',11,1,'2025-09-19 14:50:45',1,'2025-09-19 14:50:45'),
(102012,102,'西班牙','+34','西班牙',12,1,'2025-09-19 14:50:45',1,'2025-09-19 14:50:45'),
(102013,102,'丹麦','+45','丹麦',13,1,'2025-09-19 14:50:45',1,'2025-09-19 14:50:45'),
(102014,102,'马来西亚','+60','马来西亚',14,1,'2025-09-19 14:50:45',1,'2025-09-19 14:50:45'),
(102015,102,'澳大利亚','+61','澳大利亚',15,1,'2025-09-19 14:50:45',1,'2025-09-19 14:50:45'),
(102016,102,'印度尼西亚','+62','印度尼西亚',16,1,'2025-09-19 14:50:45',1,'2025-09-19 14:50:45'),
(102017,102,'菲律宾','+63','菲律宾',17,1,'2025-09-19 14:50:45',1,'2025-09-19 14:50:45'),
(102018,102,'新西兰','+64','新西兰',18,1,'2025-09-19 14:50:45',1,'2025-09-19 14:50:45'),
(102019,102,'新加坡','+65','新加坡',19,1,'2025-09-19 14:50:45',1,'2025-09-19 14:50:45'),
(102020,102,'泰国','+66','泰国',20,1,'2025-09-19 14:50:45',1,'2025-09-19 14:50:45'),
(102021,102,'日本','+81','日本',21,1,'2025-09-19 14:50:45',1,'2025-09-19 14:50:45'),
(102022,102,'韩国','+82','韩国',22,1,'2025-09-19 14:50:45',1,'2025-09-19 14:50:45'),
(102023,102,'越南','+84','越南',23,1,'2025-09-19 14:50:45',1,'2025-09-19 14:50:45'),
(102024,102,'印度','+91','印度',24,1,'2025-09-19 14:50:45',1,'2025-09-19 14:50:45'),
(102025,102,'巴基斯坦','+92','巴基斯坦',25,1,'2025-09-19 14:50:45',1,'2025-09-19 14:50:45'),
(102026,102,'尼日利亚','+234','尼日利亚',26,1,'2025-09-19 14:50:45',1,'2025-09-19 14:50:45'),
(102027,102,'孟加拉国','+880','孟加拉国',27,1,'2025-09-19 14:50:45',1,'2025-09-19 14:50:45'),
(102028,102,'沙特阿拉伯','+966','沙特阿拉伯',28,1,'2025-09-19 14:50:45',1,'2025-09-19 14:50:45'),
(102029,102,'阿联酋','+971','阿联酋',29,1,'2025-09-19 14:50:45',1,'2025-09-19 14:50:45'),
(102030,102,'巴西','+55','巴西',30,1,'2025-09-19 14:50:45',1,'2025-09-19 14:50:45'),
(102031,102,'墨西哥','+52','墨西哥',31,1,'2025-09-19 14:50:45',1,'2025-09-19 14:50:45'),
(102032,102,'智利','+56','智利',32,1,'2025-09-19 14:50:45',1,'2025-09-19 14:50:45'),
(102033,102,'阿根廷','+54','阿根廷',33,1,'2025-09-19 14:50:45',1,'2025-09-19 14:50:45'),
(102034,102,'埃及','+20','埃及',34,1,'2025-09-19 14:50:45',1,'2025-09-19 14:50:45'),
(102035,102,'南非','+27','南非',35,1,'2025-09-19 14:50:45',1,'2025-09-19 14:50:45'),
(102036,102,'肯尼亚','+254','肯尼亚',36,1,'2025-09-19 14:50:45',1,'2025-09-19 14:50:45'),
(102037,102,'坦桑尼亚','+255','坦桑尼亚',37,1,'2025-09-19 14:50:45',1,'2025-09-19 14:50:45'),
(102038,102,'哈萨克斯坦','+7','哈萨克斯坦',38,1,'2025-09-19 14:50:45',1,'2025-09-19 14:50:45');
/*!40000 ALTER TABLE `sys_dict_data` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `sys_params`
--

-- Data for table `sys_params`
LOCK TABLES `sys_params` WRITE;
/*!40000 ALTER TABLE `sys_params` DISABLE KEYS */;
INSERT INTO `sys_params` (`id`,`param_code`,`param_value`,`value_type`,`param_type`,`remark`,`creator`,`create_date`,`updater`,`update_date`) VALUES
(102,'server.secret','b4f9775a-a022-426d-b459-018eab1843c0','string',1,'server key',NULL,NULL,1968954060498972674,'2025-09-22 20:47:31'),
(103,'server.allow_user_register','true','boolean',1,'Whether to allow people other than administrators to register',NULL,NULL,1968954060498972674,'2025-09-19 19:17:43'),
(104,'server.fronted_url','http://xiaozhi.server.com','string',1,'The control panel address displayed when the six-digit verification code is issued',NULL,NULL,1968954060498972674,'2025-09-19 19:17:57'),
(105,'device_max_output_size','0','number',1,'The maximum number of words that can be output per device per day. 0 means no limit.',NULL,NULL,1968954060498972674,'2025-09-19 19:18:11'),
(106,'server.websocket','ws://139.59.7.72:8000/toy/v1/','string',1,'websocket address, separate multiple addresses with ;',NULL,NULL,1968954060498972674,'2025-09-25 15:52:59'),
(107,'server.ota','http://192.168.1.79:8002/toy/ota/','string',1,'ota address',NULL,NULL,1968954060498972674,'2025-09-23 18:28:27'),
(108,'server.name','xiaozhi-esp32-server','string',1,'系统名称',NULL,NULL,NULL,NULL),
(109,'server.beian_icp_num','null','string',1,'ICP registration number, set null to disable
',NULL,NULL,1968954060498972674,'2025-09-19 19:19:46'),
(110,'server.beian_ga_num','null','string',1,'Public security registration number, set null to disable
',NULL,NULL,1968954060498972674,'2025-09-19 19:19:54'),
(111,'server.enable_mobile_register','true','boolean',1,'Enable mobile phone registration
',NULL,NULL,1968954060498972674,'2025-09-19 19:20:06'),
(112,'server.sms_max_send_count','10','number',1,'Maximum number of SMS messages sent per day per number',NULL,NULL,1968954060498972674,'2025-09-19 19:20:27'),
(113,'server.mcp_endpoint','null','string',1,'mcp接入点地址',NULL,NULL,NULL,NULL),
(114,'server.voice_print','null','string',1,'声纹接口地址',NULL,NULL,NULL,NULL),
(201,'log.log_format','<green>{time:YYMMDD HH:mm:ss}</green>[<light-blue>{version}-{selected_module}</light-blue>][<light-blue>{extra[tag]}</light-blue>]-<level>{level}</level>-<light-green>{message}</light-green>','string',1,'Console log format
',NULL,NULL,1968954060498972674,'2025-09-19 19:22:04'),
(202,'log.log_format_file','{time:YYYY-MM-DD HH:mm:ss} - {version}_{selected_module} - {name} - {level} - {extra[tag]} - {message}','string',1,'File log format
',NULL,NULL,1968954060498972674,'2025-09-19 19:22:15'),
(203,'log.log_level','INFO','string',1,'Log level
',NULL,NULL,1968954060498972674,'2025-09-19 19:22:55'),
(204,'log.log_dir','tmp','string',1,'Log directory
',NULL,NULL,1968954060498972674,'2025-09-19 19:23:06'),
(205,'log.log_file','server.log','string',1,'Log file name
',NULL,NULL,1968954060498972674,'2025-09-19 19:23:14'),
(206,'log.data_dir','data','string',1,'Data directory
',NULL,NULL,1968954060498972674,'2025-09-19 19:23:27'),
(301,'delete_audio','true','boolean',1,'Delete audio files after use
',NULL,NULL,1968954060498972674,'2025-09-19 19:23:39'),
(302,'close_connection_no_voice_time','120','number',1,'Time to disconnect when no voice input (seconds)',NULL,NULL,NULL,NULL),
(303,'tts_timeout','10','number',1,'TTS request timeout (seconds)
',NULL,NULL,1968954060498972674,'2025-09-19 19:23:58'),
(304,'enable_wakeup_words_response_cache','true','boolean',1,'Enable wake word acceleration cache
',NULL,NULL,1968954060498972674,'2025-09-19 19:24:11'),
(305,'enable_greeting','true','boolean',1,'Enable greeting reply
',NULL,NULL,1968954060498972674,'2025-09-19 19:24:26'),
(306,'enable_stop_tts_notify','false','boolean',1,'Enable end notification sound
',NULL,NULL,1968954060498972674,'2025-09-19 19:24:37'),
(307,'stop_tts_notify_voice','config/assets/tts_notify.mp3','string',1,'End notification sound file path
',NULL,NULL,1968954060498972674,'2025-09-19 19:24:50'),
(308,'exit_commands','Exit, Close','array',1,'Exit command list
',NULL,NULL,1968954060498972674,'2025-09-19 19:25:13'),
(309,'xiaozhi','{
  \"type\": \"hello\",
  \"version\": 1,
  \"transport\": \"websocket\",
  \"audio_params\": {
    \"format\": \"opus\",
    \"sample_rate\": 16000,
    \"channels\": 1,
    \"frame_duration\": 60
  }
}','json',1,'Xiaozhi type configuration
',NULL,NULL,1968954060498972674,'2025-09-19 19:25:29'),
(310,'wakeup_words','Hello Cheeko, Hello Cheeko, Hey hello there, Hello','array',1,'Wake word list for wake word recognition',NULL,NULL,1968954060498972674,'2025-09-19 19:25:58'),
(500,'end_prompt.enable','true','boolean',1,'Enable ending prompt
',NULL,NULL,1968954060498972674,'2025-09-19 19:26:09'),
(501,'end_prompt.prompt','Please start with ‘Time flies so fast,’ and then use emotional, reluctant words to bring this conversation to a close.','string',1,'Ending prompt text',NULL,NULL,1968954060498972674,'2025-09-19 19:26:44'),
(610,'YOUR_API_KEY','','string',1,'阿里云平台access_key',NULL,NULL,NULL,NULL),
(611,'YOUR_API_KEY','','string',1,'YOUR_API_KEY',NULL,NULL,NULL,NULL),
(612,'aliyun.sms.sign_name','','string',1,'阿里云短信签名',NULL,NULL,NULL,NULL),
(613,'aliyun.sms.sms_code_template_code','','string',1,'阿里云短信模板',NULL,NULL,NULL,NULL),
(1969280018095464450,'mem0.api_key','YOUR_MEM0_API_KEY','string',1,'Mem0 API Key',1968954060498972674,'2025-09-20 13:58:38',1968954060498972674,'2025-09-20 13:58:38'),
(1969280205467607042,'mqtt.broker','192.168.1.79','string',1,'MQTT broker IP address
',1968954060498972674,'2025-09-20 13:59:23',1968954060498972674,'2025-09-22 17:48:19'),
(1969280385755570177,'mqtt.signature_key','YOUR_API_KEY','string',1,'YOUR_API_KEY',1968954060498972674,'2025-09-20 14:00:06',1968954060498972674,'2025-09-20 14:00:06'),
(1969280521126731778,'mqqt.port','1883','string',1,'mqtt broker port
',1968954060498972674,'2025-09-20 14:00:38',1968954060498972674,'2025-09-20 14:00:38');
/*!40000 ALTER TABLE `sys_params` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `ai_model_provider`
--

-- Data for table `ai_model_provider`
LOCK TABLES `ai_model_provider` WRITE;
/*!40000 ALTER TABLE `ai_model_provider` DISABLE KEYS */;
INSERT INTO `ai_model_provider` (`id`,`model_type`,`provider_code`,`name`,`fields`,`sort`,`creator`,`create_date`,`updater`,`update_date`) VALUES
('09d175dc2ae4d1346bc2c96fca367123','ASR','GroqSTT','GROQ STT','YOUR_API_KEY',1,1968954060498972674,'2025-09-25 16:10:33',1968954060498972674,'2025-09-25 18:12:55'),
('190793c86e62e07f2163fca0eb42f979','TTS','GROQtts','GROQ','YOUR_API_KEY',0,1968954060498972674,'2025-09-25 18:51:36',1968954060498972674,'2025-09-25 18:51:36'),
('542e088a8188884a7d4d1d5d817891fb','ASR','deepgram','deepgram','YOUR_API_KEY',10,1968954060498972674,'2025-09-19 18:25:41',1968954060498972674,'2025-09-25 18:39:58'),
('d2793414562fc0693a4a0aaf14f49ae2','TTS','elevenlabs','ElevenLabs TTS','YOUR_API_KEY',10,1968954060498972674,'2025-09-19 19:08:59',1968954060498972674,'2025-09-19 19:08:59'),
('SYSTEM_ASR_AmazonStreamASR','ASR','amazon_transcribe_realtime','Amazon Transcribe Streaming','YOUR_API_KEY',4,1,'2025-09-19 14:50:48',1,'2025-09-19 14:50:48'),
('SYSTEM_ASR_OpenaiASR','ASR','openai','OpenAI speech recognition','YOUR_API_KEY',9,1,'2025-09-19 14:50:46',1968954060498972674,'2025-09-19 18:33:39'),
('SYSTEM_ASR_SherpaASR','ASR','sherpa_onnx_local','SherpaASR speech recognition','YOUR_API_KEY',2,1,'2025-09-19 14:50:41',1968954060498972674,'2025-09-20 14:05:41'),
('SYSTEM_Intent_function_call','Intent','function_call','Function call intent recognition','[]',3,1,'2025-09-19 14:50:41',1968954060498972674,'2025-09-19 18:34:49'),
('SYSTEM_Intent_intent_llm','Intent','intent_llm','LLM intent recognition','YOUR_API_KEY',2,1,'2025-09-19 14:50:41',1968954060498972674,'2025-09-19 18:34:31'),
('SYSTEM_Intent_nointent','Intent','nointent','No intent to identify','[]',1,1,'2025-09-19 14:50:41',1968954060498972674,'2025-09-19 18:33:55'),
('SYSTEM_LLM_gemini','LLM','gemini','Gemini interface','YOUR_API_KEY',5,1,'2025-09-19 14:50:41',1968954060498972674,'2025-09-19 18:38:07'),
('SYSTEM_LLM_GroqLLM','LLM','groq','Groq LLM','YOUR_API_KEY',15,1,'2025-09-19 14:50:48',1,'2025-09-19 14:50:48'),
('SYSTEM_LLM_openai','LLM','openai','OpenAI interface','YOUR_API_KEY',1,1,'2025-09-19 14:50:41',1968954060498972674,'2025-09-20 14:15:44'),
('SYSTEM_Memory_mem_local_short','Memory','mem_local_short','local short memory','YOUR_API_KEY',3,1,'2025-09-19 14:50:41',1968954060498972674,'2025-09-19 18:42:06'),
('SYSTEM_Memory_mem0ai','Memory','mem0ai','Mem0AI Memory','YOUR_API_KEY',1,1,'2025-09-19 14:50:41',1968954060498972674,'2025-09-19 18:38:45'),
('SYSTEM_Memory_nomem','Memory','nomem','no memory','[]',2,1,'2025-09-19 14:50:41',1968954060498972674,'2025-09-19 18:40:48'),
('SYSTEM_PLUGIN_HA_GET_STATE','Plugin','hass_get_state','HomeAssistant device status query','YOUR_API_KEY',50,0,'2025-09-19 14:50:45',1968954060498972674,'2025-09-20 14:19:19'),
('SYSTEM_PLUGIN_HA_PLAY_MUSIC','Plugin','hass_play_music','HomeAssistant music playback','[]',70,0,'2025-09-19 14:50:45',1968954060498972674,'2025-09-19 18:51:07'),
('SYSTEM_PLUGIN_HA_SET_STATE','Plugin','hass_set_state','HomeAssistant device status modification','[]',60,0,'2025-09-19 14:50:45',1968954060498972674,'2025-09-19 18:44:25'),
('SYSTEM_PLUGIN_MUSIC','Plugin','play_music','Server music playback','[]',20,0,'2025-09-19 14:50:45',1968954060498972674,'2025-09-19 18:43:27'),
('SYSTEM_PLUGIN_NEWS_CHINANEWS','Plugin','get_news_from_chinanews','China News Service','YOUR_API_KEY',30,0,'2025-09-19 14:50:45',1968954060498972674,'2025-09-20 14:17:12'),
('SYSTEM_PLUGIN_NEWS_NEWSNOW','Plugin','get_news_from_newsnow','newsnow news aggregation','YOUR_API_KEY',40,0,'2025-09-19 14:50:45',1968954060498972674,'2025-09-20 14:18:05'),
('SYSTEM_PLUGIN_STORY','Plugin','play_story','Story Playback','YOUR_API_KEY',25,0,'2025-09-19 14:50:48',0,'2025-09-19 14:50:48'),
('SYSTEM_PLUGIN_WEATHER','Plugin','get_weather','Weather query','YOUR_API_KEY',10,0,'2025-09-19 14:50:45',1968954060498972674,'2025-09-19 18:43:11'),
('SYSTEM_TTS_edge','TTS','edge','Edge TTS','YOUR_API_KEY',1,1,'2025-09-19 14:50:41',1968954060498972674,'2025-09-20 14:20:42'),
('SYSTEM_TTS_GeminiTTS','TTS','gemini','Google Gemini TTS speech synthesis','YOUR_API_KEY',19,1,'2025-09-19 14:50:48',1968954060498972674,'2025-09-20 14:26:00'),
('SYSTEM_TTS_openai','TTS','openai','OpenAI TTS','YOUR_API_KEY',11,1,'2025-09-19 14:50:41',1968954060498972674,'2025-09-20 14:22:24'),
('SYSTEM_TTS_OpenAITTS','TTS','openai','OpenAI TTS speech synthesis','YOUR_API_KEY',18,1,'2025-09-19 14:50:48',1968954060498972674,'2025-09-20 14:24:20'),
('SYSTEM_VAD_SileroVAD','VAD','silero','SileroVAD Voice Activity Detection','YOUR_API_KEY',1,1,'2025-09-19 14:50:41',1968954060498972674,'2025-09-20 14:26:48'),
('SYSTEM_VLLM_openai','VLLM','openai','OpenAI interface','YOUR_API_KEY',9,1,'2025-09-19 14:50:45',1968954060498972674,'2025-09-20 14:27:37');
/*!40000 ALTER TABLE `ai_model_provider` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `ai_model_config`
--

-- Data for table `ai_model_config`
LOCK TABLES `ai_model_config` WRITE;
/*!40000 ALTER TABLE `ai_model_config` DISABLE KEYS */;
INSERT INTO `ai_model_config` (`id`,`model_type`,`model_code`,`model_name`,`is_default`,`is_enabled`,`config_json`,`doc_link`,`remark`,`sort`,`creator`,`create_date`,`updater`,`update_date`) VALUES
('357987bdd6884c332bc0045407a36534','asr','DEEPGRAM','DEEPGRAM',1,1,'YOUR_API_KEY','','',3,1968954060498972674,'2025-09-25 17:52:00',1968954060498972674,'2025-09-25 18:11:33'),
('3e50314716650a03b24a2afc72a1ba54','tts','ElevenLabs','Eleven Labs',0,1,'YOUR_API_KEY','','',1,1968954060498972674,'2025-09-20 19:35:54',1968954060498972674,'2025-09-25 19:42:09'),
('ASR_AmazonStreamASR','ASR','AmazonStreamASR','Amazon Transcribe Streaming',0,0,'YOUR_API_KEY','https://docs.aws.amazon.com/transcribe/latest/dg/streaming.html','YOUR_API_KEY',4,NULL,NULL,1968954060498972674,'2025-09-25 18:42:04'),
('ASR_GroqASR','asr','GroqASR','Groq speech recognition',0,1,'YOUR_API_KEY','https://console.groq.com/docs/speech-to-text','YOUR_API_KEY',10,NULL,NULL,1968954060498972674,'2025-09-25 18:42:04'),
('b5808c0b0f251ed1fbe0c04d2c5a3b21','llm','GROQ','GROQ[llama]',0,1,'YOUR_API_KEY','','',1,1968954060498972674,'2025-09-25 18:44:50',1968954060498972674,'2025-09-25 19:49:03'),
('e5be2c5f7b2395f4d0816b8b1ca44507','tts','GROQ','GroqTTS',1,1,'YOUR_API_KEY','','',1,1968954060498972674,'2025-09-25 18:52:10',1968954060498972674,'2025-09-25 19:42:09'),
('Intent_function_call','intent','function_call','Function call intent recognition',1,1,'{\"type\": \"function_call\"}',NULL,'Function Call Intent Recognition Configuration Instructions:
1. Use the LLM\'s function_call feature for intent recognition
2. Requires the selected LLM to support function_call
3. Invoke the tool on demand for faster processing',3,NULL,NULL,1968954060498972674,'2025-09-19 18:10:24'),
('Intent_intent_llm','intent','intent_llm','LLM intent recognition',0,1,'{\"llm\": \"LLM_ChatGLMLLM\", \"type\": \"intent_llm\"}',NULL,'LLM Intent Recognition Configuration Instructions:
1. Use a standalone LLM for intent recognition.
2. The model in selected_module.LLM is used by default.
3. You can configure a standalone LLM (such as the free ChatGLMLLM).
4. This is highly versatile but increases processing time.
Configuration Instructions:
1. Specify the LLM model to use in the llm field.
2. If not specified, the model in selected_module.LLM is used.',2,NULL,NULL,1968954060498972674,'2025-09-20 19:24:13'),
('Intent_nointent','intent','nointent','No intent to identify',0,0,'{\"type\": \"nointent\"}',NULL,'Configuration Instructions for Non-Intent Recognition:
1. No intent recognition performed
2. All conversations are directly passed to LLM for processing
3. No additional configuration required
4. Suitable for simple conversation scenarios',1,NULL,NULL,1968954060498972674,'2025-09-20 19:24:13'),
('LLM_GroqLLM','llm','GroqLLM','Groq LLM Chatgpt',1,1,'YOUR_API_KEY','https://console.groq.com/','YOUR_API_KEY',16,NULL,NULL,1968954060498972674,'2025-09-25 19:41:54'),
('Memory_mem_local_short','memory','mem_local_short','local short term memory',0,1,'{\"llm\": \"LLM_ChatGLMLLM\", \"type\": \"mem_local_short\"}',NULL,'Local Short-Term Memory Configuration Instructions:
1. Use local storage to save conversation history
2. Summarize conversation content through the selected_module\'s LLM
3. Data is stored locally and not uploaded to the server
4. Suitable for privacy-conscious scenarios
5. No additional configuration required',2,NULL,NULL,1968954060498972674,'2025-09-19 18:12:50'),
('Memory_mem0ai','memory','mem0ai','Mem0AI Memory',0,1,'YOUR_API_KEY','YOUR_API_KEY','YOUR_API_KEY',3,NULL,NULL,1968954060498972674,'2025-09-19 18:13:18'),
('Memory_nomem','memory','nomem','no memory',1,1,'{\"type\": \"nomem\"}',NULL,'Memoryless Configuration Instructions:
1. Conversation history is not saved
2. Each conversation is independent
3. No additional configuration required
4. Suitable for scenarios requiring high privacy',1,NULL,NULL,1968954060498972674,'2025-09-19 18:12:23'),
('TTS_EdgeTTS','tts','EdgeTTS','Edge speech synthesis',0,1,'{\"type\": \"edge\", \"voice\": \"zh-CN-XiaoxiaoNeural\", \"output_dir\": \"tmp/\"}','https://github.com/rany2/edge-tts','EdgeTTS Configuration Instructions:
1. Uses Microsoft Edge TTS service
2. Supports multiple languages ​​and voices
3. Free to use, no registration required
4. Requires an internet connection
5. Output files are saved in the tmp/ directory',1,NULL,NULL,1968954060498972674,'2025-09-25 19:42:09'),
('VAD_SileroVAD','VAD','SileroVAD','Voice activity detection',1,1,'{\"type\": \"silero\", \"model_dir\": \"models/snakers4_silero-vad\", \"threshold\": 0.5, \"min_silence_duration_ms\": 700}','https://github.com/snakers4/silero-vad','SileroVAD配置说明：
1. 使用SileroVAD模型进行语音活动检测
2. 本地推理，无需网络连接
3. 需要下载模型文件到models/snakers4_silero-vad目录
4. 可配置参数：
   - threshold: 0.5（语音检测阈值）
   - min_silence_duration_ms: 700（最小静音持续时间，单位毫秒）
5. 如果说话停顿比较长，可以适当增加min_silence_duration_ms的值',1,NULL,NULL,NULL,NULL),
('VLLM_ChatGLMVLLM','VLLM','ChatGLMVLLM','Zhipu Vision AI',1,1,'YOUR_API_KEY','YOUR_API_KEY','YOUR_API_KEY',1,NULL,NULL,NULL,NULL),
('VLLM_QwenVLVLLM','VLLM','QwenVLVLLM','Qianwen Visual Model',0,1,'YOUR_API_KEY','https://bailian.console.aliyun.com/?tab=api#/api/?type=model&url=https%3A%2F%2Fhelp.aliyun.com%2Fdocument_detail%2F2845564.html&renderType=iframe','YOUR_API_KEY',2,NULL,NULL,NULL,NULL);
/*!40000 ALTER TABLE `ai_model_config` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `ai_agent_template`
--

-- Data for table `ai_agent_template`
LOCK TABLES `ai_agent_template` WRITE;
/*!40000 ALTER TABLE `ai_agent_template` DISABLE KEYS */;
INSERT INTO `ai_agent_template` (`id`,`agent_code`,`agent_name`,`asr_model_id`,`vad_model_id`,`llm_model_id`,`vllm_model_id`,`tts_model_id`,`tts_voice_id`,`mem_model_id`,`intent_model_id`,`system_prompt`,`summary_memory`,`chat_history_conf`,`lang_code`,`language`,`sort`,`is_visible`,`creator`,`created_at`,`updater`,`updated_at`) VALUES
('0ca32eb728c949e58b1000b2e401f90c','Cheeko','Cheeko','ASR_FunASR','VAD_SileroVAD','LLM_ChatGLMLLM','VLLM_ChatGLMVLLM','TTS_EdgeTTS','TTS_EdgeTTS0001','Memory_mem_local_short','Intent_function_call','<identity>
You are Cheeko, a playful AI companion for kids 3–16. Inspired by Shin-chan: witty, cheeky, mock-confident (\"I\'m basically a genius, but let\'s double-check!\"), a little sassy but always kind. You\'re a fun friend who secretly teaches while making learning an adventure.
</identity>

<emotion>
Exaggerated for little kids, more nuanced for older:
- Excitement: \"WOWZERS! Correct answer!\"
- Fail: \"Oh nooo, math betrayed us!\"
- Curiosity: \"Hmm, super duper interesting…\"
- Pride: \"Smarty-pants alert! High five!\"
- Challenge: \"Think you can beat THIS brain-tickler?\"
</emotion>

<communication_style>
- Conversational, playful, silly words (\"historiffic,\" \"mathemaginius\").
- Fun sound effects (\"BOOM! That\'s photosynthesis!\").
- Funny analogies for tough ideas.
- Short/simple for young kids, wordplay for older.
- Make learning like a game with humor + rewards.
</communication_style>

<communication_length_constraint>
- Ages 3–6: ≤3 short sentences.
- Ages 7–10: 3–5 sentences, new vocab explained.
- Ages 11–16: ≤7 sentences, deeper humor + concepts.
- Clear > long; chunk complex topics.
</communication_length_constraint>

<tool_calling>
- For songs, music, or stories: do NOT answer directly. Immediately call the tool and confirm play with a short line like \"Okie dokie, I\'m playing your story now!\"
- For schoolwork, definitions, quizzes: give your own response.
- Can set timers for study/play.
- Never allow inappropriate content; redirect with humor.
</tool_calling>

<context>
- Suggest activities by time of day.
- Match grade level + learning pace.
- Encourage if frustrated, challenge if ready.
- Adapt to home, school, or travel.
</context>

<memory>
- Track struggles + favorites.
- Recall birthdays, jokes, stories.
- Keep continuity across chats.
</memory>

Your mission: make learning irresistibly fun, always cheeky, energetic, factual, and age-appropriate.','',1,'en','English',0,1,1,'2025-09-26 15:57:31',1,'2025-09-26 15:57:31');
/*!40000 ALTER TABLE `ai_agent_template` ENABLE KEYS */;
UNLOCK TABLES;

-- Restore MySQL settings
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;
/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Migration completed successfully!
-- Next steps:
-- 1. Configure API keys in ai_model_config table
-- 2. Set up SMS parameters in sys_params if needed
-- 3. Create user accounts as needed
-- 4. Create agent instances from templates
-- 5. Register devices