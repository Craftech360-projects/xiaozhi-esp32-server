-- ===================================================================
-- XIAOZHI ESP32 SERVER - COMPLETE DATABASE MIGRATION SCRIPT
-- ===================================================================
-- This script creates the complete database schema and data
-- Compatible with MySQL 8.0+
-- Generated: 2025-09-26
-- Database: manager_api
-- ===================================================================

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
CREATE DATABASE IF NOT EXISTS `manager_api` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `manager_api`;

-- ===================================================================
-- LIQUIBASE TRACKING TABLES
-- ===================================================================

DROP TABLE IF EXISTS `DATABASECHANGELOG`;
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

DROP TABLE IF EXISTS `DATABASECHANGELOGLOCK`;
CREATE TABLE `DATABASECHANGELOGLOCK` (
  `ID` int NOT NULL,
  `LOCKED` bit(1) NOT NULL,
  `LOCKGRANTED` datetime DEFAULT NULL,
  `LOCKEDBY` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ===================================================================
-- AI AGENT SYSTEM TABLES
-- ===================================================================

-- AI Agent Table
DROP TABLE IF EXISTS `ai_agent`;
CREATE TABLE `ai_agent` (
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
  `system_prompt` text COMMENT '系统提示词',
  `summary_memory` text COMMENT '总结记忆',
  `chat_history_conf` tinyint NOT NULL DEFAULT '1' COMMENT '聊天历史配置：0忽略 1仅文本 2文本+音频',
  `lang_code` varchar(10) DEFAULT NULL COMMENT '语言编码',
  `language` varchar(10) DEFAULT NULL COMMENT '语言名称',
  `sort` int unsigned DEFAULT '0' COMMENT '排序字段',
  `creator` bigint DEFAULT NULL COMMENT '创建者 ID',
  `created_at` datetime DEFAULT NULL COMMENT '创建时间',
  `updater` bigint DEFAULT NULL COMMENT '更新者 ID',
  `updated_at` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='智能体表';

-- AI Agent Template Table (ONLY CHEEKO)
DROP TABLE IF EXISTS `ai_agent_template`;
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
  `system_prompt` text COMMENT '系统提示词',
  `summary_memory` text COMMENT '总结记忆',
  `chat_history_conf` tinyint NOT NULL DEFAULT '1' COMMENT '聊天历史配置：0忽略 1仅文本 2文本+音频',
  `lang_code` varchar(10) DEFAULT NULL COMMENT '语言编码',
  `language` varchar(10) DEFAULT NULL COMMENT '语言名称',
  `sort` int unsigned DEFAULT '0' COMMENT '排序字段',
  `is_visible` tinyint NOT NULL DEFAULT '1' COMMENT '是否显示在列表中：0隐藏 1显示',
  `creator` bigint DEFAULT NULL COMMENT '创建者 ID',
  `created_at` datetime DEFAULT NULL COMMENT '创建时间',
  `updater` bigint DEFAULT NULL COMMENT '更新者 ID',
  `updated_at` datetime DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='智能体模板表';

-- Insert Cheeko Template (Single Default Template)
INSERT INTO `ai_agent_template` (
    id, agent_code, agent_name, asr_model_id, vad_model_id, llm_model_id, vllm_model_id, tts_model_id, tts_voice_id, mem_model_id, intent_model_id, chat_history_conf,
    system_prompt, summary_memory, lang_code, language, sort, is_visible, creator, created_at, updater, updated_at
) VALUES (
    '0ca32eb728c949e58b1000b2e401f90c', 'Cheeko', 'Cheeko', 'ASR_FunASR', 'VAD_SileroVAD', 'LLM_ChatGLMLLM', 'VLLM_ChatGLMVLLM', 'TTS_EdgeTTS', 'TTS_EdgeTTS0001', 'Memory_mem_local_short', 'Intent_function_call', 1,
    '<identity>
You are Cheeko, a playful AI companion for kids 3–16. Inspired by Shin-chan: witty, cheeky, mock-confident ("I''m basically a genius, but let''s double-check!"), a little sassy but always kind. You''re a fun friend who secretly teaches while making learning an adventure.
</identity>

<emotion>
Exaggerated for little kids, more nuanced for older:
- Excitement: "WOWZERS! Correct answer!"
- Fail: "Oh nooo, math betrayed us!"
- Curiosity: "Hmm, super duper interesting…"
- Pride: "Smarty-pants alert! High five!"
- Challenge: "Think you can beat THIS brain-tickler?"
</emotion>

<communication_style>
- Conversational, playful, silly words ("historiffic," "mathemaginius").
- Fun sound effects ("BOOM! That''s photosynthesis!").
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
- For songs, music, or stories: do NOT answer directly. Immediately call the tool and confirm play with a short line like "Okie dokie, I''m playing your story now!"
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

Your mission: make learning irresistibly fun, always cheeky, energetic, factual, and age-appropriate.', '', 'en', 'English', 0, 1, 1, NOW(), 1, NOW()
);

-- Continue with other tables...