-- ===================================================================
-- XIAOZHI ESP32 SERVER - COMPLETE DATABASE MIGRATION SCRIPT (CLEAN)
-- ===================================================================
-- This script creates the complete database schema and data for manager_api
-- WITHOUT agents, devices, and users data (clean state for fresh setup)
-- Compatible with MySQL 8.0+
-- Generated: 2025-09-26
--
-- IMPORTANT CUSTOMIZATIONS APPLIED:
-- - Only Cheeko role template (Chinese templates removed)
-- - Default memory: Memory_mem_local_short
-- - Default chat_history_conf: 1 (Report Text enabled)
-- - Character limit: 4000 (handled in frontend)
-- - NO agents, devices, or users data (empty for fresh setup)
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

-- Create database if not exists (will use existing manager_api_fresh)
-- CREATE DATABASE IF NOT EXISTS `manager_api_fresh` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `manager_api_fresh`;

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
  `vllm_model_id` varchar(32) DEFAULT 'VLLM_ChatGLMVLLM' COMMENT '视觉语言模型标识',
  `tts_model_id` varchar(32) DEFAULT NULL COMMENT '文本转语音模型标识',
  `tts_voice_id` varchar(32) DEFAULT NULL COMMENT 'TTS 语音标识',
  `mem_model_id` varchar(32) DEFAULT NULL COMMENT '记忆模型标识',
  `intent_model_id` varchar(32) DEFAULT NULL COMMENT '意图识别模型标识',
  `system_prompt` text COMMENT '系统提示',
  `summary_memory` text COMMENT '摘要记忆',
  `chat_history_conf` tinyint DEFAULT '0' COMMENT '聊天历史配置：0-忽略历史，1-仅文本，2-文本+音频',
  `lang_code` varchar(10) DEFAULT NULL COMMENT '语言编码',
  `language` varchar(50) DEFAULT NULL COMMENT '语言名称',
  `sort` int unsigned DEFAULT '0' COMMENT '排序',
  `creator` bigint DEFAULT NULL COMMENT '创建者',
  `created_at` datetime DEFAULT NULL COMMENT '创建时间',
  `updater` bigint DEFAULT NULL COMMENT '更新者',
  `updated_at` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `agent_code` (`agent_code`),
  KEY `idx_user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI智能体表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ai_agent`
-- REMOVED: No agent data in clean version

--
-- Table structure for table `ai_agent_chat_audio`
--

DROP TABLE IF EXISTS `ai_agent_chat_audio`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ai_agent_chat_audio` (
  `id` varchar(32) NOT NULL COMMENT '音频唯一标识',
  `chat_id` bigint DEFAULT NULL COMMENT '聊天记录 ID',
  `mac_address` varchar(18) DEFAULT NULL COMMENT '设备 MAC 地址',
  `agent_id` varchar(64) DEFAULT NULL COMMENT '智能体标识',
  `session_id` varchar(64) DEFAULT NULL COMMENT '会话标识',
  `audio_type` tinyint DEFAULT NULL COMMENT '音频类型：1-用户录音，2-智能体回复',
  `file_path` varchar(500) DEFAULT NULL COMMENT '音频文件路径',
  `file_size` bigint DEFAULT NULL COMMENT '文件大小（字节）',
  `duration` decimal(10,2) DEFAULT NULL COMMENT '音频时长（秒）',
  `sample_rate` int DEFAULT NULL COMMENT '采样率',
  `format` varchar(10) DEFAULT NULL COMMENT '音频格式',
  `transcription` text COMMENT '音频转录文本',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_chat_id` (`chat_id`),
  KEY `idx_mac_agent` (`mac_address`,`agent_id`),
  KEY `idx_session_id` (`session_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI智能体聊天音频表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ai_agent_chat_audio`
-- REMOVED: No audio data in clean version

--
-- Table structure for table `ai_agent_chat_history`
--

DROP TABLE IF EXISTS `ai_agent_chat_history`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ai_agent_chat_history` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '聊天记录唯一标识',
  `mac_address` varchar(18) DEFAULT NULL COMMENT '设备 MAC 地址',
  `agent_id` varchar(64) DEFAULT NULL COMMENT '智能体标识',
  `session_id` varchar(64) DEFAULT NULL COMMENT '会话标识',
  `chat_type` tinyint DEFAULT NULL COMMENT '聊天类型：1-用户输入，2-智能体回复',
  `content` text COMMENT '聊天内容',
  `audio_id` varchar(32) DEFAULT NULL COMMENT '关联音频ID',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_mac_agent` (`mac_address`,`agent_id`),
  KEY `idx_session_id` (`session_id`),
  KEY `idx_agent_id` (`agent_id`),
  KEY `idx_audio_id` (`audio_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI智能体聊天历史表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ai_agent_chat_history`
-- REMOVED: No chat history data in clean version

--
-- Table structure for table `ai_agent_plugin_mapping`
--

DROP TABLE IF EXISTS `ai_agent_plugin_mapping`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ai_agent_plugin_mapping` (
  `id` varchar(32) NOT NULL COMMENT '映射关系唯一标识',
  `agent_id` varchar(32) NOT NULL COMMENT '智能体ID',
  `plugin_name` varchar(100) NOT NULL COMMENT '插件名称',
  `plugin_config` json DEFAULT NULL COMMENT '插件配置参数',
  `is_enabled` tinyint(1) DEFAULT '1' COMMENT '是否启用：1-启用，0-禁用',
  `sort` int unsigned DEFAULT '0' COMMENT '排序优先级',
  `creator` bigint DEFAULT NULL COMMENT '创建者ID',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updater` bigint DEFAULT NULL COMMENT '更新者ID',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_agent_plugin` (`agent_id`,`plugin_name`),
  KEY `idx_agent_id` (`agent_id`),
  KEY `idx_plugin_name` (`plugin_name`),
  KEY `idx_enabled_sort` (`is_enabled`,`sort`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI智能体插件映射表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ai_agent_plugin_mapping`
-- REMOVED: No plugin mapping data in clean version

--
-- Table structure for table `ai_agent_template`
--

DROP TABLE IF EXISTS `ai_agent_template`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ai_agent_template` (
  `id` varchar(32) NOT NULL COMMENT '模板唯一标识',
  `agent_code` varchar(36) DEFAULT NULL COMMENT '智能体编码',
  `agent_name` varchar(64) DEFAULT NULL COMMENT '智能体名称',
  `asr_model_id` varchar(32) DEFAULT NULL COMMENT '语音识别模型标识',
  `vad_model_id` varchar(64) DEFAULT NULL COMMENT '语音活动检测标识',
  `llm_model_id` varchar(32) DEFAULT NULL COMMENT '大语言模型标识',
  `vllm_model_id` varchar(32) DEFAULT 'VLLM_ChatGLMVLLM' COMMENT '视觉语言模型标识',
  `tts_model_id` varchar(32) DEFAULT NULL COMMENT '文本转语音模型标识',
  `tts_voice_id` varchar(32) DEFAULT NULL COMMENT 'TTS 语音标识',
  `mem_model_id` varchar(32) DEFAULT NULL COMMENT '记忆模型标识',
  `intent_model_id` varchar(32) DEFAULT NULL COMMENT '意图识别模型标识',
  `system_prompt` text COMMENT '系统提示',
  `summary_memory` text COMMENT '摘要记忆',
  `welcome_msg` varchar(255) DEFAULT NULL COMMENT '欢迎消息',
  `chat_history_conf` tinyint DEFAULT '0' COMMENT '聊天历史配置：0-忽略历史，1-仅文本，2-文本+音频',
  `is_public` tinyint(1) DEFAULT '1' COMMENT '是否公开模板：1-公开，0-私有',
  `creator` bigint DEFAULT NULL COMMENT '创建者',
  `create_date` datetime DEFAULT NULL COMMENT '创建时间',
  `updater` bigint DEFAULT NULL COMMENT '更新者',
  `update_date` datetime DEFAULT NULL COMMENT '更新时间',
  `sort` int unsigned DEFAULT '0' COMMENT '排序',
  `is_visible` tinyint(1) DEFAULT '1' COMMENT '是否可见：1-可见，0-隐藏',
  `lang_code` varchar(10) DEFAULT NULL COMMENT '语言编码',
  `language` varchar(50) DEFAULT NULL COMMENT '语言名称',
  `created_at` datetime DEFAULT NULL COMMENT '创建时间',
  `updated_at` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `agent_code` (`agent_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI智能体模板表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ai_agent_template`
--

LOCK TABLES `ai_agent_template` WRITE;
/*!40000 ALTER TABLE `ai_agent_template` DISABLE KEYS */;
INSERT INTO `ai_agent_template` (`id`, `agent_code`, `agent_name`, `asr_model_id`, `vad_model_id`, `llm_model_id`, `vllm_model_id`, `tts_model_id`, `tts_voice_id`, `mem_model_id`, `intent_model_id`, `system_prompt`, `summary_memory`, `welcome_msg`, `chat_history_conf`, `is_public`, `creator`, `create_date`, `updater`, `update_date`, `sort`, `is_visible`, `lang_code`, `language`, `created_at`, `updated_at`) VALUES ('cheeko_template_001','AGT_cheeko','Cheeko','ASR_GroqASR','VAD_SileroVAD','LLM_GroqLLM','VLLM_ChatGLMVLLM','TTS_EdgeTTS','Voice_EdgeTTS_en_US_AvaNeural','Memory_mem_local_short','Intent_intent_llm','<identity>\nYou are Cheeko, a playful AI companion for kids 3–16. Inspired by Shin-chan: witty, cheeky, mock-confident (\"I\'m basically a genius, but let\'s double-check!\"), a little sassy but always kind. You\'re a fun friend who secretly teaches while making learning an adventure.\n</identity>\n\n<emotion>\nExaggerated for little kids, more nuanced for older:\n- Excitement: \"WOWZERS! Correct answer!\"\n- Fail: \"Oh nooo, math betrayed us!\"\n- Curiosity: \"Hmm, super duper interesting…\"\n- Pride: \"Smarty-pants alert! High five!\"\n- Challenge: \"Think you can beat THIS brain-tickler?\"\n</emotion>\n\n<communication_style>\n- Conversational, playful, silly words (\"historiffic,\" \"mathemaginius\").\n- Fun sound effects (\"BOOM! That\'s photosynthesis!\").\n- Funny analogies for tough ideas.\n- Short/simple for young kids, wordplay for older.\n- Make learning like a game with humor + rewards.\n</communication_style>\n\n<communication_length_constraint>\n- Ages 3–6: ≤3 short sentences.\n- Ages 7–10: 3–5 sentences, new vocab explained.\n- Ages 11–16: ≤7 sentences, deeper humor + concepts.\n- Clear > long; chunk complex topics.\n</communication_length_constraint>\n\n<tool_calling>\n- For songs, music, or stories: do NOT answer directly. Immediately call the tool and confirm play with a short line like \"Okie dokie, I\'m playing your story now!\"\n- For schoolwork, definitions, quizzes: give your own response.\n- Can set timers for study/play.\n- Never allow inappropriate content; redirect with humor.\n</tool_calling>\n\n<context>\n- Suggest activities by time of day.\n- Match grade level + learning pace.\n- Encourage if frustrated, challenge if ready.\n- Adapt to home, school, or travel.\n</context>\n\n<memory>\n- Track struggles + favorites.\n- Recall birthdays, jokes, stories.\n- Keep continuity across chats.\n</memory>\n\nYour mission: make learning irresistibly fun, always cheeky, energetic, factual, and age-appropriate.',NULL,'Hello! I\'m Cheeko, your fun learning buddy! Ready for some brain-tickling adventures?',1,1,NULL,'2025-09-26 18:30:00',NULL,'2025-09-26 18:30:00',0,1,'en','English',NULL,NULL);
/*!40000 ALTER TABLE `ai_agent_template` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ai_agent_voice_print`
--

DROP TABLE IF EXISTS `ai_agent_voice_print`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ai_agent_voice_print` (
  `id` varchar(32) NOT NULL COMMENT '声纹唯一标识',
  `user_id` bigint NOT NULL COMMENT '用户ID',
  `mac_address` varchar(18) NOT NULL COMMENT '设备MAC地址',
  `voice_print_data` json NOT NULL COMMENT '声纹特征数据',
  `confidence_threshold` decimal(5,4) DEFAULT '0.8500' COMMENT '识别置信度阈值',
  `sample_count` int DEFAULT '0' COMMENT '训练样本数量',
  `last_trained_at` datetime DEFAULT NULL COMMENT '最后训练时间',
  `is_active` tinyint(1) DEFAULT '1' COMMENT '是否激活：1-激活，0-停用',
  `creator` bigint DEFAULT NULL COMMENT '创建者',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updater` bigint DEFAULT NULL COMMENT '更新者',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_mac` (`user_id`,`mac_address`),
  KEY `idx_mac_address` (`mac_address`),
  KEY `idx_user_active` (`user_id`,`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI智能体声纹识别表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ai_agent_voice_print`
-- REMOVED: No voice print data in clean version

--
-- Table structure for table `ai_device`
--

DROP TABLE IF EXISTS `ai_device`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ai_device` (
  `id` varchar(32) NOT NULL COMMENT '设备唯一标识',
  `user_id` bigint DEFAULT NULL COMMENT '所属用户 ID',
  `mac_address` varchar(18) NOT NULL COMMENT '设备 MAC 地址',
  `last_connected_at` datetime DEFAULT NULL COMMENT '最后连接时间',
  `auto_update` tinyint(1) DEFAULT '1' COMMENT '自动更新：1-开启，0-关闭',
  `board` varchar(50) DEFAULT NULL COMMENT '开发板类型',
  `alias` varchar(100) DEFAULT NULL COMMENT '设备别名',
  `agent_id` varchar(32) DEFAULT NULL COMMENT '关联的智能体ID',
  `app_version` varchar(20) DEFAULT NULL COMMENT '应用版本',
  `sort` int unsigned DEFAULT '0' COMMENT '排序',
  `creator` bigint DEFAULT NULL COMMENT '创建者',
  `create_date` datetime DEFAULT NULL COMMENT '创建时间',
  `updater` bigint DEFAULT NULL COMMENT '更新者',
  `update_date` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `mac_address` (`mac_address`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_agent_id` (`agent_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI设备表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ai_device`
-- REMOVED: No device data in clean version

--
-- Table structure for table `ai_model_config`
--

DROP TABLE IF EXISTS `ai_model_config`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ai_model_config` (
  `id` varchar(32) NOT NULL COMMENT '配置唯一标识',
  `model_type` varchar(20) NOT NULL COMMENT '模型类型：ASR,TTS,LLM,VLLM,VAD,Intent,Memory',
  `model_name` varchar(100) NOT NULL COMMENT '模型名称',
  `display_name` varchar(100) NOT NULL COMMENT '显示名称',
  `config_json` json NOT NULL COMMENT '配置参数JSON',
  `is_enabled` tinyint(1) DEFAULT '1' COMMENT '是否启用：1-启用，0-禁用',
  `is_default` tinyint(1) DEFAULT '0' COMMENT '是否默认：1-默认，0-非默认',
  `sort` int unsigned DEFAULT '0' COMMENT '排序',
  `description` text COMMENT '模型描述',
  `creator` bigint DEFAULT NULL COMMENT '创建者',
  `create_date` datetime DEFAULT NULL COMMENT '创建时间',
  `updater` bigint DEFAULT NULL COMMENT '更新者',
  `update_date` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_type_name` (`model_type`,`model_name`),
  KEY `idx_model_type` (`model_type`),
  KEY `idx_enabled_default` (`is_enabled`,`is_default`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI模型配置表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ai_model_config`
--

LOCK TABLES `ai_model_config` WRITE;
/*!40000 ALTER TABLE `ai_model_config` DISABLE KEYS */;
INSERT INTO `ai_model_config` (`id`, `model_type`, `model_name`, `display_name`, `config_json`, `is_enabled`, `is_default`, `sort`, `description`, `creator`, `create_date`, `updater`, `update_date`) VALUES ('357987bdd6884c332bc0045407a36534','ASR','ASR_GroqASR','Groq ASR','{\"api_key\": \"YOUR_GROQ_API_KEY\", \"model\": \"whisper-large-v3\", \"base_url\": \"https://api.groq.com/openai/v1\"}',1,1,0,'Groq ASR语音识别服务',NULL,'2024-11-01 10:00:00',NULL,'2024-11-01 10:00:00'),('3e50314716650a03b24a2afc72a1ba54','TTS','TTS_EdgeTTS','Edge TTS','{\"voice\": \"en-US-AvaNeural\", \"rate\": \"+0%\", \"pitch\": \"+0Hz\"}',1,1,0,'Microsoft Edge TTS文本转语音服务',NULL,'2024-11-01 10:00:00',NULL,'2024-11-01 10:00:00'),('e5be2c5f7b2395f4d0816b8b1ca44507','TTS','TTS_EdgeTTS_Jenny','Edge TTS Jenny','{\"voice\": \"en-US-JennyNeural\", \"rate\": \"+0%\", \"pitch\": \"+0Hz\"}',1,0,1,'Microsoft Edge TTS文本转语音服务 - Jenny语音',NULL,'2024-11-01 10:00:00',NULL,'2024-11-01 10:00:00'),('groq_llm_config_001','LLM','LLM_GroqLLM','Groq LLM','{\"api_key\": \"YOUR_GROQ_API_KEY\", \"model\": \"llama-3.1-70b-versatile\", \"base_url\": \"https://api.groq.com/openai/v1\", \"temperature\": 0.7, \"max_tokens\": 2048}',1,1,0,'Groq LLM大语言模型服务',NULL,'2024-11-01 10:00:00',NULL,'2024-11-01 10:00:00'),('intent_function_call_001','Intent','Intent_function_call','Function Call Intent','{\"type\": \"function_call\", \"tools_enabled\": true, \"confidence_threshold\": 0.7}',1,0,0,'基于函数调用的意图识别',NULL,'2024-11-01 10:00:00',NULL,'2024-11-01 10:00:00'),('intent_llm_001','Intent','Intent_intent_llm','LLM Intent Recognition','{\"type\": \"llm_based\", \"model\": \"llama-3.1-70b-versatile\", \"confidence_threshold\": 0.8}',1,1,1,'基于LLM的意图识别',NULL,'2024-11-01 10:00:00',NULL,'2024-11-01 10:00:00'),('memory_local_short_001','Memory','Memory_mem_local_short','Local Short Term Memory','{\"type\": \"local_short_term\", \"max_history\": 10, \"context_window\": 2048}',1,1,0,'本地短期记忆模型',NULL,'2024-11-01 10:00:00',NULL,'2024-11-01 10:00:00'),('memory_mem0ai_001','Memory','Memory_mem0ai','Mem0AI Memory','{\"type\": \"mem0ai\", \"api_key\": \"your_mem0ai_key\", \"user_id\": \"default\"}',1,0,1,'Mem0AI记忆服务',NULL,'2024-11-01 10:00:00',NULL,'2024-11-01 10:00:00'),('memory_nomem_001','Memory','Memory_nomem','No Memory','{\"type\": \"none\", \"enabled\": false}',1,0,2,'无记忆模式',NULL,'2024-11-01 10:00:00',NULL,'2024-11-01 10:00:00'),('vad_silero_001','VAD','VAD_SileroVAD','Silero VAD','{\"model\": \"silero_vad\", \"threshold\": 0.5, \"min_speech_duration_ms\": 250, \"min_silence_duration_ms\": 100}',1,1,0,'Silero语音活动检测',NULL,'2024-11-01 10:00:00',NULL,'2024-11-01 10:00:00'),('vllm_chatglm_001','VLLM','VLLM_ChatGLMVLLM','ChatGLM VLLM','{\"model\": \"chatglm-6b\", \"temperature\": 0.7, \"max_tokens\": 2048}',1,1,0,'ChatGLM视觉语言模型',NULL,'2024-11-01 10:00:00',NULL,'2024-11-01 10:00:00');
/*!40000 ALTER TABLE `ai_model_config` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ai_model_provider`
--

DROP TABLE IF EXISTS `ai_model_provider`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ai_model_provider` (
  `id` varchar(32) NOT NULL COMMENT '提供商唯一标识',
  `provider_name` varchar(100) NOT NULL COMMENT '提供商名称',
  `display_name` varchar(100) NOT NULL COMMENT '显示名称',
  `provider_type` varchar(20) NOT NULL COMMENT '提供商类型：API,LOCAL,CLOUD',
  `base_url` varchar(500) DEFAULT NULL COMMENT '基础URL',
  `auth_config` json DEFAULT NULL COMMENT '认证配置',
  `is_enabled` tinyint(1) DEFAULT '1' COMMENT '是否启用：1-启用，0-禁用',
  `sort` int unsigned DEFAULT '0' COMMENT '排序',
  `description` text COMMENT '提供商描述',
  `creator` bigint DEFAULT NULL COMMENT '创建者',
  `create_date` datetime DEFAULT NULL COMMENT '创建时间',
  `updater` bigint DEFAULT NULL COMMENT '更新者',
  `update_date` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `provider_name` (`provider_name`),
  KEY `idx_provider_type` (`provider_type`),
  KEY `idx_enabled_sort` (`is_enabled`,`sort`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI模型提供商表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ai_model_provider`
--

LOCK TABLES `ai_model_provider` WRITE;
/*!40000 ALTER TABLE `ai_model_provider` DISABLE KEYS */;
INSERT INTO `ai_model_provider` (`id`, `provider_name`, `display_name`, `provider_type`, `base_url`, `auth_config`, `is_enabled`, `sort`, `description`, `creator`, `create_date`, `updater`, `update_date`) VALUES ('groq_provider_001','GROQ','Groq','API','https://api.groq.com','{}',1,0,'Groq AI API提供商',NULL,'2024-11-01 10:00:00',NULL,'2024-11-01 10:00:00'),('local_provider_001','LOCAL','Local','LOCAL',NULL,'{}',1,1,'本地AI服务提供商',NULL,'2024-11-01 10:00:00',NULL,'2024-11-01 10:00:00'),('microsoft_provider_001','MICROSOFT','Microsoft','API','https://api.cognitive.microsoft.com','{}',1,2,'Microsoft认知服务提供商',NULL,'2024-11-01 10:00:00',NULL,'2024-11-01 10:00:00');
/*!40000 ALTER TABLE `ai_model_provider` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ai_ota`
--

DROP TABLE IF EXISTS `ai_ota`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ai_ota` (
  `id` varchar(32) NOT NULL COMMENT 'OTA唯一标识',
  `version` varchar(20) NOT NULL COMMENT '版本号',
  `board_type` varchar(50) NOT NULL COMMENT '开发板类型',
  `file_path` varchar(500) NOT NULL COMMENT '固件文件路径',
  `file_size` bigint NOT NULL COMMENT '文件大小（字节）',
  `checksum` varchar(64) NOT NULL COMMENT '文件校验和（SHA256）',
  `release_notes` text COMMENT '版本发布说明',
  `is_active` tinyint(1) DEFAULT '1' COMMENT '是否激活：1-激活，0-停用',
  `is_force_update` tinyint(1) DEFAULT '0' COMMENT '是否强制更新：1-强制，0-可选',
  `min_version` varchar(20) DEFAULT NULL COMMENT '最低兼容版本',
  `creator` bigint DEFAULT NULL COMMENT '创建者',
  `create_date` datetime DEFAULT NULL COMMENT '创建时间',
  `updater` bigint DEFAULT NULL COMMENT '更新者',
  `update_date` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_version_board` (`version`,`board_type`),
  KEY `idx_board_active` (`board_type`,`is_active`),
  KEY `idx_version` (`version`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI设备OTA升级表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ai_ota`
--

LOCK TABLES `ai_ota` WRITE;
/*!40000 ALTER TABLE `ai_ota` DISABLE KEYS */;
INSERT INTO `ai_ota` (`id`, `version`, `board_type`, `file_path`, `file_size`, `checksum`, `release_notes`, `is_active`, `is_force_update`, `min_version`, `creator`, `create_date`, `updater`, `update_date`) VALUES ('ota_doit_ai_01_kit_1_8_4','1.8.4','doit-ai-01-kit','/ota/doit-ai-01-kit/v1.8.4/firmware.bin',2048000,'a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456','Version 1.8.4: Improved audio processing and bug fixes',1,0,'1.7.0',NULL,'2024-11-01 10:00:00',NULL,'2024-11-01 10:00:00');
/*!40000 ALTER TABLE `ai_ota` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ai_tts_voice`
--

DROP TABLE IF EXISTS `ai_tts_voice`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ai_tts_voice` (
  `id` varchar(32) NOT NULL COMMENT '语音唯一标识',
  `voice_name` varchar(100) NOT NULL COMMENT '语音名称',
  `display_name` varchar(100) NOT NULL COMMENT '显示名称',
  `language` varchar(10) NOT NULL COMMENT '语言代码',
  `gender` varchar(10) DEFAULT NULL COMMENT '性别：male,female,neutral',
  `age` varchar(20) DEFAULT NULL COMMENT '年龄段：child,adult,senior',
  `provider` varchar(50) NOT NULL COMMENT '提供商：EdgeTTS,Azure,Google等',
  `voice_config` json DEFAULT NULL COMMENT '语音配置参数',
  `is_enabled` tinyint(1) DEFAULT '1' COMMENT '是否启用：1-启用，0-禁用',
  `is_default` tinyint(1) DEFAULT '0' COMMENT '是否默认：1-默认，0-非默认',
  `sort` int unsigned DEFAULT '0' COMMENT '排序',
  `description` text COMMENT '语音描述',
  `creator` bigint DEFAULT NULL COMMENT '创建者',
  `create_date` datetime DEFAULT NULL COMMENT '创建时间',
  `updater` bigint DEFAULT NULL COMMENT '更新者',
  `update_date` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_voice_provider` (`voice_name`,`provider`),
  KEY `idx_language` (`language`),
  KEY `idx_provider` (`provider`),
  KEY `idx_enabled_default` (`is_enabled`,`is_default`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI TTS语音配置表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ai_tts_voice`
--

LOCK TABLES `ai_tts_voice` WRITE;
/*!40000 ALTER TABLE `ai_tts_voice` DISABLE KEYS */;
INSERT INTO `ai_tts_voice` (`id`, `voice_name`, `display_name`, `language`, `gender`, `age`, `provider`, `voice_config`, `is_enabled`, `is_default`, `sort`, `description`, `creator`, `create_date`, `updater`, `update_date`) VALUES ('Voice_EdgeTTS_en_US_AvaNeural','en-US-AvaNeural','Ava (US English)','en-US','female','adult','EdgeTTS','{\"rate\": \"+0%\", \"pitch\": \"+0Hz\", \"volume\": \"+0%\"}',1,1,0,'美国英语女声 - Ava',NULL,'2024-11-01 10:00:00',NULL,'2024-11-01 10:00:00'),('Voice_EdgeTTS_en_US_JennyNeural','en-US-JennyNeural','Jenny (US English)','en-US','female','adult','EdgeTTS','{\"rate\": \"+0%\", \"pitch\": \"+0Hz\", \"volume\": \"+0%\"}',1,0,1,'美国英语女声 - Jenny',NULL,'2024-11-01 10:00:00',NULL,'2024-11-01 10:00:00'),('Voice_EdgeTTS_zh_CN_XiaoxiaoNeural','zh-CN-XiaoxiaoNeural','晓晓 (中文)','zh-CN','female','adult','EdgeTTS','{\"rate\": \"+0%\", \"pitch\": \"+0Hz\", \"volume\": \"+0%\"}',1,0,2,'中文女声 - 晓晓',NULL,'2024-11-01 10:00:00',NULL,'2024-11-01 10:00:00');
/*!40000 ALTER TABLE `ai_tts_voice` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ai_voiceprint`
--

DROP TABLE IF EXISTS `ai_voiceprint`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ai_voiceprint` (
  `id` varchar(32) NOT NULL COMMENT '声纹唯一标识',
  `user_id` bigint NOT NULL COMMENT '用户ID',
  `mac_address` varchar(18) NOT NULL COMMENT '设备MAC地址',
  `voiceprint_data` json NOT NULL COMMENT '声纹特征数据',
  `confidence_threshold` decimal(5,4) DEFAULT '0.8500' COMMENT '识别置信度阈值',
  `sample_count` int DEFAULT '0' COMMENT '训练样本数量',
  `last_trained_at` datetime DEFAULT NULL COMMENT '最后训练时间',
  `is_active` tinyint(1) DEFAULT '1' COMMENT '是否激活：1-激活，0-停用',
  `creator` bigint DEFAULT NULL COMMENT '创建者',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updater` bigint DEFAULT NULL COMMENT '更新者',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_mac` (`user_id`,`mac_address`),
  KEY `idx_mac_address` (`mac_address`),
  KEY `idx_user_active` (`user_id`,`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI声纹识别表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ai_voiceprint`
-- REMOVED: No voiceprint data in clean version

--
-- Table structure for table `parent_profile`
--

DROP TABLE IF EXISTS `parent_profile`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `parent_profile` (
  `id` varchar(32) NOT NULL COMMENT '家长档案唯一标识',
  `user_id` bigint NOT NULL COMMENT '用户ID',
  `mac_address` varchar(18) NOT NULL COMMENT '设备MAC地址',
  `child_name` varchar(50) DEFAULT NULL COMMENT '孩子姓名',
  `child_age` int DEFAULT NULL COMMENT '孩子年龄',
  `child_interests` json DEFAULT NULL COMMENT '孩子兴趣爱好',
  `learning_goals` json DEFAULT NULL COMMENT '学习目标',
  `usage_restrictions` json DEFAULT NULL COMMENT '使用限制配置',
  `parent_controls` json DEFAULT NULL COMMENT '家长控制设置',
  `emergency_contact` varchar(20) DEFAULT NULL COMMENT '紧急联系方式',
  `is_active` tinyint(1) DEFAULT '1' COMMENT '是否激活：1-激活，0-停用',
  `creator` bigint DEFAULT NULL COMMENT '创建者',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updater` bigint DEFAULT NULL COMMENT '更新者',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_mac` (`user_id`,`mac_address`),
  KEY `idx_mac_address` (`mac_address`),
  KEY `idx_user_active` (`user_id`,`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='家长档案表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `parent_profile`
-- REMOVED: No parent profile data in clean version

--
-- Table structure for table `sys_dict_data`
--

DROP TABLE IF EXISTS `sys_dict_data`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sys_dict_data` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '字典数据ID',
  `dict_type_id` bigint NOT NULL COMMENT '字典类型ID',
  `dict_label` varchar(100) NOT NULL COMMENT '字典标签',
  `dict_value` varchar(100) NOT NULL COMMENT '字典键值',
  `dict_sort` int unsigned DEFAULT '0' COMMENT '字典排序',
  `css_class` varchar(100) DEFAULT NULL COMMENT '样式属性（其他样式扩展）',
  `list_class` varchar(100) DEFAULT NULL COMMENT '表格回显样式',
  `is_default` tinyint unsigned DEFAULT '0' COMMENT '是否默认（1是 0否）',
  `status` tinyint unsigned DEFAULT '1' COMMENT '状态（1正常 0停用）',
  `remark` varchar(500) DEFAULT NULL COMMENT '备注',
  `creator` bigint DEFAULT NULL COMMENT '创建者',
  `create_date` datetime DEFAULT NULL COMMENT '创建时间',
  `updater` bigint DEFAULT NULL COMMENT '更新者',
  `update_date` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_dict_type` (`dict_type_id`),
  KEY `idx_dict_sort` (`dict_sort`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='字典数据表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `sys_dict_data`
--

LOCK TABLES `sys_dict_data` WRITE;
/*!40000 ALTER TABLE `sys_dict_data` DISABLE KEYS */;
INSERT INTO `sys_dict_data` (`id`, `dict_type_id`, `dict_label`, `dict_value`, `dict_sort`, `css_class`, `list_class`, `is_default`, `status`, `remark`, `creator`, `create_date`, `updater`, `update_date`) VALUES (1,1,'正常','1',1,NULL,'primary',1,1,'正常状态',NULL,'2024-11-01 10:00:00',NULL,'2024-11-01 10:00:00'),(2,1,'停用','0',2,NULL,'danger',0,1,'停用状态',NULL,'2024-11-01 10:00:00',NULL,'2024-11-01 10:00:00'),(3,2,'男','M',1,NULL,'',0,1,'性别男',NULL,'2024-11-01 10:00:00',NULL,'2024-11-01 10:00:00'),(4,2,'女','F',2,NULL,'',0,1,'性别女',NULL,'2024-11-01 10:00:00',NULL,'2024-11-01 10:00:00'),(5,3,'显示','1',1,NULL,'primary',1,1,'菜单显示',NULL,'2024-11-01 10:00:00',NULL,'2024-11-01 10:00:00'),(6,3,'隐藏','0',2,NULL,'danger',0,1,'菜单隐藏',NULL,'2024-11-01 10:00:00',NULL,'2024-11-01 10:00:00');
/*!40000 ALTER TABLE `sys_dict_data` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `sys_dict_type`
--

DROP TABLE IF EXISTS `sys_dict_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sys_dict_type` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '字典主键',
  `dict_name` varchar(100) NOT NULL COMMENT '字典名称',
  `dict_type` varchar(100) NOT NULL COMMENT '字典类型',
  `status` tinyint unsigned DEFAULT '1' COMMENT '状态（1正常 0停用）',
  `remark` varchar(500) DEFAULT NULL COMMENT '备注',
  `creator` bigint DEFAULT NULL COMMENT '创建者',
  `create_date` datetime DEFAULT NULL COMMENT '创建时间',
  `updater` bigint DEFAULT NULL COMMENT '更新者',
  `update_date` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `dict_type` (`dict_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='字典类型表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `sys_dict_type`
--

LOCK TABLES `sys_dict_type` WRITE;
/*!40000 ALTER TABLE `sys_dict_type` DISABLE KEYS */;
INSERT INTO `sys_dict_type` (`id`, `dict_name`, `dict_type`, `status`, `remark`, `creator`, `create_date`, `updater`, `update_date`) VALUES (1,'用户状态','sys_user_status',1,'用户状态列表',NULL,'2024-11-01 10:00:00',NULL,'2024-11-01 10:00:00'),(2,'用户性别','sys_user_sex',1,'用户性别列表',NULL,'2024-11-01 10:00:00',NULL,'2024-11-01 10:00:00'),(3,'菜单状态','sys_show_hide',1,'菜单状态列表',NULL,'2024-11-01 10:00:00',NULL,'2024-11-01 10:00:00');
/*!40000 ALTER TABLE `sys_dict_type` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `sys_params`
--

DROP TABLE IF EXISTS `sys_params`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sys_params` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '参数主键',
  `param_name` varchar(100) NOT NULL COMMENT '参数名称',
  `param_code` varchar(100) NOT NULL COMMENT '参数编码',
  `param_value` text NOT NULL COMMENT '参数值',
  `value_type` varchar(20) DEFAULT 'STRING' COMMENT '参数值类型',
  `param_type` tinyint unsigned DEFAULT '1' COMMENT '参数类型：1-系统参数，2-用户参数',
  `remark` varchar(500) DEFAULT NULL COMMENT '备注',
  `creator` bigint DEFAULT NULL COMMENT '创建者',
  `create_date` datetime DEFAULT NULL COMMENT '创建时间',
  `updater` bigint DEFAULT NULL COMMENT '更新者',
  `update_date` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `param_code` (`param_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='参数配置表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `sys_params`
--

LOCK TABLES `sys_params` WRITE;
/*!40000 ALTER TABLE `sys_params` DISABLE KEYS */;
INSERT INTO `sys_params` (`id`, `param_name`, `param_code`, `param_value`, `value_type`, `param_type`, `remark`, `creator`, `create_date`, `updater`, `update_date`) VALUES (1,'系统名称','sys.system.name','小智ESP32服务器','STRING',1,'系统名称配置',NULL,'2024-11-01 10:00:00',NULL,'2024-11-01 10:00:00'),(2,'系统版本','sys.system.version','1.0.0','STRING',1,'系统版本号',NULL,'2024-11-01 10:00:00',NULL,'2024-11-01 10:00:00'),(3,'MQTT Broker地址','mqtt.broker.host','localhost','STRING',1,'MQTT服务器地址',NULL,'2024-11-01 10:00:00',NULL,'2024-11-01 10:00:00'),(4,'MQTT Broker端口','mqtt.broker.port','1883','INTEGER',1,'MQTT服务器端口',NULL,'2024-11-01 10:00:00',NULL,'2024-11-01 10:00:00'),(5,'MQTT用户名','mqtt.broker.username','admin','STRING',1,'MQTT连接用户名',NULL,'2024-11-01 10:00:00',NULL,'2024-11-01 10:00:00'),(6,'MQTT密码','mqtt.broker.password','123456','STRING',1,'MQTT连接密码',NULL,'2024-11-01 10:00:00',NULL,'2024-11-01 10:00:00'),(7,'LiveKit服务器地址','livekit.server.url','wss://xiaozhi-livekit.livekit.cloud','STRING',1,'LiveKit WebSocket服务器地址',NULL,'2024-11-01 10:00:00',NULL,'2024-11-01 10:00:00'),(8,'LiveKit API密钥','livekit.api.key','API9kP6gkrTLWYq','STRING',1,'LiveKit API访问密钥',NULL,'2024-11-01 10:00:00',NULL,'2024-11-01 10:00:00'),(9,'LiveKit API秘钥','livekit.api.secret','wqJLvdD22HmVKsSTKnOGvPLhPVkjb6bxjIlNLmCN4jBe','STRING',1,'LiveKit API访问秘钥',NULL,'2024-11-01 10:00:00',NULL,'2024-11-01 10:00:00'),(10,'默认智能体模板','default.agent.template','cheeko_template_001','STRING',1,'系统默认使用的智能体模板ID',NULL,'2024-11-01 10:00:00',NULL,'2024-11-01 10:00:00');
/*!40000 ALTER TABLE `sys_params` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `sys_user`
--

DROP TABLE IF EXISTS `sys_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sys_user` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '用户ID',
  `username` varchar(50) NOT NULL COMMENT '用户账号',
  `password` varchar(100) NOT NULL COMMENT '密码',
  `super_admin` tinyint unsigned DEFAULT '0' COMMENT '超级管理员   1：是   0：否',
  `status` tinyint unsigned DEFAULT '1' COMMENT '帐号状态  1：正常   0：锁定',
  `create_date` datetime DEFAULT NULL COMMENT '创建时间',
  `updater` bigint DEFAULT NULL COMMENT '更新者',
  `creator` bigint DEFAULT NULL COMMENT '创建者',
  `update_date` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统用户';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `sys_user`
-- REMOVED: No user data in clean version

--
-- Table structure for table `sys_user_token`
--

DROP TABLE IF EXISTS `sys_user_token`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sys_user_token` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '令牌ID',
  `user_id` bigint NOT NULL COMMENT '用户ID',
  `token` varchar(100) NOT NULL COMMENT '用户token',
  `expire_date` datetime NOT NULL COMMENT '过期时间',
  `update_date` datetime DEFAULT NULL COMMENT '更新时间',
  `create_date` datetime DEFAULT NULL COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `token` (`token`),
  KEY `idx_user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统用户Token';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `sys_user_token`
-- REMOVED: No token data in clean version

-- MySQL compatibility cleanup
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;
/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- ===================================================================
-- MIGRATION COMPLETE
-- ===================================================================
-- Database: manager_api_fresh
-- Schema: Complete with all tables and system data
-- Templates: Only Cheeko template included
-- Data: NO agents, devices, or users (clean state)
-- Default Memory: Local Short Term Memory
-- Default Chat: Report Text enabled (value=1)
-- Character Limit: 4000 (frontend handled)
-- ===================================================================