-- =====================================================
-- Complete Database Migration Script - Railway to Local Docker
-- Generated: 2025-09-19
-- Target Database: manager_api
-- =====================================================

SET FOREIGN_KEY_CHECKS = 0;
SET SQL_MODE = 'NO_AUTO_VALUE_ON_ZERO';
SET AUTOCOMMIT = 0;
START TRANSACTION;

-- =====================================================
-- From file: 202501230002_translate_dict_names.sql
-- =====================================================
-- Translate Chinese dictionary type names to English
UPDATE `sys_dict_type` SET `dict_name` = 'Mobile Area' WHERE `dict_type` = 'MOBILE_AREA';
UPDATE `sys_dict_type` SET `dict_name` = 'Firmware Type' WHERE `dict_type` = 'FIRMWARE_TYPE';

-- Also update remarks to English
UPDATE `sys_dict_type` SET `remark` = 'Mobile area codes dictionary' WHERE `dict_type` = 'MOBILE_AREA';
UPDATE `sys_dict_type` SET `remark` = 'Firmware types dictionary' WHERE `dict_type` = 'FIRMWARE_TYPE';


-- =====================================================
-- From file: 202501230003_translate_provider_fields.sql
-- =====================================================
-- Translate provider field labels from Chinese to English
-- This will update the field labels shown in the Call Information section

-- Update common field labels across all providers
UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"API密钥"', '"label":"API Key"')
WHERE fields LIKE '%"label":"API密钥"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"服务地址"', '"label":"Service URL"')
WHERE fields LIKE '%"label":"服务地址"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"基础URL"', '"label":"Base URL"')
WHERE fields LIKE '%"label":"基础URL"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"Model name"', '"label":"Model Name"')
WHERE fields LIKE '%"label":"Model name"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"输出目录"', '"label":"Output Directory"')
WHERE fields LIKE '%"label":"输出目录"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"端口号"', '"label":"Port"')
WHERE fields LIKE '%"label":"端口号"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"服务类型"', '"label":"Service Type"')
WHERE fields LIKE '%"label":"服务类型"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"是否使用SSL"', '"label":"Use SSL"')
WHERE fields LIKE '%"label":"是否使用SSL"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"请求方式"', '"label":"Request Method"')
WHERE fields LIKE '%"label":"请求方式"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"请求参数"', '"label":"Request Parameters"')
WHERE fields LIKE '%"label":"请求参数"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"请求头"', '"label":"Request Headers"')
WHERE fields LIKE '%"label":"请求头"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"音频格式"', '"label":"Audio Format"')
WHERE fields LIKE '%"label":"音频格式"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"访问令牌"', '"label":"Access Token"')
WHERE fields LIKE '%"label":"访问令牌"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"响应格式"', '"label":"Response Format"')
WHERE fields LIKE '%"label":"响应格式"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"音色"', '"label":"Voice"')
WHERE fields LIKE '%"label":"音色"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"应用密钥"', '"label":"App Key"')
WHERE fields LIKE '%"label":"应用密钥"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"访问密钥ID"', '"label":"Access Key ID"')
WHERE fields LIKE '%"label":"访问密钥ID"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"访问密钥密码"', '"label":"Access Key Secret"')
WHERE fields LIKE '%"label":"访问密钥密码"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"授权"', '"label":"Authorization"')
WHERE fields LIKE '%"label":"授权"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"速度"', '"label":"Speed"')
WHERE fields LIKE '%"label":"速度"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"温度"', '"label":"Temperature"')
WHERE fields LIKE '%"label":"温度"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"音色ID"', '"label":"Voice ID"')
WHERE fields LIKE '%"label":"音色ID"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"采样率"', '"label":"Sample Rate"')
WHERE fields LIKE '%"label":"采样率"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"参考音频"', '"label":"Reference Audio"')
WHERE fields LIKE '%"label":"参考音频"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"参考文本"', '"label":"Reference Text"')
WHERE fields LIKE '%"label":"参考文本"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"是否标准化"', '"label":"Normalize"')
WHERE fields LIKE '%"label":"是否标准化"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"最大新令牌数"', '"label":"Max New Tokens"')
WHERE fields LIKE '%"label":"最大新令牌数"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"块长度"', '"label":"Chunk Length"')
WHERE fields LIKE '%"label":"块长度"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"重复惩罚"', '"label":"Repetition Penalty"')
WHERE fields LIKE '%"label":"重复惩罚"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"是否流式"', '"label":"Streaming"')
WHERE fields LIKE '%"label":"是否流式"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"是否使用内存缓存"', '"label":"Use Memory Cache"')
WHERE fields LIKE '%"label":"是否使用内存缓存"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"种子"', '"label":"Seed"')
WHERE fields LIKE '%"label":"种子"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"通道数"', '"label":"Channels"')
WHERE fields LIKE '%"label":"通道数"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"参考ID"', '"label":"Reference ID"')
WHERE fields LIKE '%"label":"参考ID"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"组ID"', '"label":"Group ID"')
WHERE fields LIKE '%"label":"组ID"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"文本语言"', '"label":"Text Language"')
WHERE fields LIKE '%"label":"文本语言"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"参考音频路径"', '"label":"Reference Audio Path"')
WHERE fields LIKE '%"label":"参考音频路径"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"提示文本"', '"label":"Prompt Text"')
WHERE fields LIKE '%"label":"提示文本"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"提示语言"', '"label":"Prompt Language"')
WHERE fields LIKE '%"label":"提示语言"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"文本分割方法"', '"label":"Text Split Method"')
WHERE fields LIKE '%"label":"文本分割方法"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"批处理大小"', '"label":"Batch Size"')
WHERE fields LIKE '%"label":"批处理大小"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"批处理阈值"', '"label":"Batch Threshold"')
WHERE fields LIKE '%"label":"批处理阈值"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"是否分桶"', '"label":"Split Bucket"')
WHERE fields LIKE '%"label":"是否分桶"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"是否返回片段"', '"label":"Return Fragment"')
WHERE fields LIKE '%"label":"是否返回片段"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"速度因子"', '"label":"Speed Factor"')
WHERE fields LIKE '%"label":"速度因子"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"是否流式模式"', '"label":"Streaming Mode"')
WHERE fields LIKE '%"label":"是否流式模式"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"是否并行推理"', '"label":"Parallel Inference"')
WHERE fields LIKE '%"label":"是否并行推理"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"辅助参考音频路径"', '"label":"Auxiliary Reference Audio Paths"')
WHERE fields LIKE '%"label":"辅助参考音频路径"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"切分标点"', '"label":"Cut Punctuation"')
WHERE fields LIKE '%"label":"切分标点"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"输入参考"', '"label":"Input References"')
WHERE fields LIKE '%"label":"输入参考"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"采样步数"', '"label":"Sample Steps"')
WHERE fields LIKE '%"label":"采样步数"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"是否使用SR"', '"label":"Use SR"')
WHERE fields LIKE '%"label":"是否使用SR"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"音调因子"', '"label":"Pitch Factor"')
WHERE fields LIKE '%"label":"音调因子"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"音量变化"', '"label":"Volume Change dB"')
WHERE fields LIKE '%"label":"音量变化"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"目标语言"', '"label":"Target Language"')
WHERE fields LIKE '%"label":"目标语言"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"格式"', '"label":"Format"')
WHERE fields LIKE '%"label":"格式"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"情感"', '"label":"Emotion"')
WHERE fields LIKE '%"label":"情感"%';

-- Additional field translations
UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"应用ID"', '"label":"App ID"')
WHERE fields LIKE '%"label":"应用ID"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"应用AppID"', '"label":"App ID"')
WHERE fields LIKE '%"label":"应用AppID"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"应用AppKey"', '"label":"App Key"')
WHERE fields LIKE '%"label":"应用AppKey"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"临时Token"', '"label":"Temporary Token"')
WHERE fields LIKE '%"label":"临时Token"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"AccessKey ID"', '"label":"Access Key ID"')
WHERE fields LIKE '%"label":"AccessKey ID"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"AccessKey Secret"', '"label":"Access Key Secret"')
WHERE fields LIKE '%"label":"AccessKey Secret"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"API服务地址"', '"label":"API Service URL"')
WHERE fields LIKE '%"label":"API服务地址"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"API地址"', '"label":"API URL"')
WHERE fields LIKE '%"label":"API地址"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"WebSocket地址"', '"label":"WebSocket URL"')
WHERE fields LIKE '%"label":"WebSocket地址"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"资源ID"', '"label":"Resource ID"')
WHERE fields LIKE '%"label":"资源ID"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"默认音色"', '"label":"Default Voice"')
WHERE fields LIKE '%"label":"默认音色"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"断句检测时间"', '"label":"Sentence Silence Detection Time"')
WHERE fields LIKE '%"label":"断句检测时间"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"集群"', '"label":"Cluster"')
WHERE fields LIKE '%"label":"集群"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"热词文件名称"', '"label":"Hotword File Name"')
WHERE fields LIKE '%"label":"热词文件名称"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"替换词文件名称"', '"label":"Replacement File Name"')
WHERE fields LIKE '%"label":"替换词文件名称"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"区域"', '"label":"Region"')
WHERE fields LIKE '%"label":"区域"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"语言参数"', '"label":"Language Parameter"')
WHERE fields LIKE '%"label":"语言参数"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"音量"', '"label":"Volume"')
WHERE fields LIKE '%"label":"音量"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"语速"', '"label":"Speech Rate"')
WHERE fields LIKE '%"label":"语速"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"音调"', '"label":"Pitch"')
WHERE fields LIKE '%"label":"音调"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"检测阈值"', '"label":"Detection Threshold"')
WHERE fields LIKE '%"label":"检测阈值"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"模型目录"', '"label":"Model Directory"')
WHERE fields LIKE '%"label":"模型目录"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields, '"label":"最小静音时长"', '"label":"Min Silence Duration"')
WHERE fields LIKE '%"label":"最小静音时长"%';

-- Update placeholder values in ai_model_config
UPDATE ai_model_config 
SET config_json = REPLACE(config_json, '"你的api_key"', '"your_api_key"')
WHERE config_json LIKE '%"你的api_key"%';

UPDATE ai_model_config 
SET config_json = REPLACE(config_json, '"你的网关访问密钥"', '"your_gateway_access_key"')
WHERE config_json LIKE '%"你的网关访问密钥"%';

UPDATE ai_model_config 
SET config_json = REPLACE(config_json, '"你的app_id"', '"your_app_id"')
WHERE config_json LIKE '%"你的app_id"%';

UPDATE ai_model_config 
SET config_json = REPLACE(config_json, '"你的bot_id"', '"your_bot_id"')
WHERE config_json LIKE '%"你的bot_id"%';

UPDATE ai_model_config 
SET config_json = REPLACE(config_json, '"你的user_id"', '"your_user_id"')
WHERE config_json LIKE '%"你的user_id"%';

UPDATE ai_model_config 
SET config_json = REPLACE(config_json, '"你的personal_access_token"', '"your_personal_access_token"')
WHERE config_json LIKE '%"你的personal_access_token"%';

UPDATE ai_model_config 
SET config_json = REPLACE(config_json, '"你的home assistant api访问令牌"', '"your_home_assistant_api_token"')
WHERE config_json LIKE '%"你的home assistant api访问令牌"%';

UPDATE ai_model_config 
SET config_json = REPLACE(config_json, '"你的Secret ID"', '"your_secret_id"')
WHERE config_json LIKE '%"你的Secret ID"%';

UPDATE ai_model_config 
SET config_json = REPLACE(config_json, '"你的Secret Key"', '"your_secret_key"')
WHERE config_json LIKE '%"你的Secret Key"%';

UPDATE ai_model_config 
SET config_json = REPLACE(config_json, '"你的appkey"', '"your_appkey"')
WHERE config_json LIKE '%"你的appkey"%';

UPDATE ai_model_config 
SET config_json = REPLACE(config_json, '"你的access_key_id"', '"your_access_key_id"')
WHERE config_json LIKE '%"你的access_key_id"%';

UPDATE ai_model_config 
SET config_json = REPLACE(config_json, '"你的access_key_secret"', '"your_access_key_secret"')
WHERE config_json LIKE '%"你的access_key_secret"%';

UPDATE ai_model_config 
SET config_json = REPLACE(config_json, '"你的API Key"', '"your_api_key"')
WHERE config_json LIKE '%"你的API Key"%';

UPDATE ai_model_config 
SET config_json = REPLACE(config_json, '"你的应用ID"', '"your_app_id"')
WHERE config_json LIKE '%"你的应用ID"%';

UPDATE ai_model_config 
SET config_json = REPLACE(config_json, '"你的音色ID"', '"your_voice_id"')
WHERE config_json LIKE '%"你的音色ID"%';

UPDATE ai_model_config 
SET config_json = REPLACE(config_json, '"你的访问令牌"', '"your_access_token"')
WHERE config_json LIKE '%"你的访问令牌"%';

UPDATE ai_model_config 
SET config_json = REPLACE(config_json, '"你的资源ID"', '"your_resource_id"')
WHERE config_json LIKE '%"你的资源ID"%';

UPDATE ai_model_config 
SET config_json = REPLACE(config_json, '"你的默认音色"', '"your_default_voice"')
WHERE config_json LIKE '%"你的默认音色"%';

UPDATE ai_model_config 
SET config_json = REPLACE(config_json, '"你的集群"', '"your_cluster"')
WHERE config_json LIKE '%"你的集群"%';


-- =====================================================
-- From file: 202501230004_translate_model_names.sql
-- =====================================================
-- Translate model provider names and descriptions from Chinese to English

-- Update provider names
UPDATE ai_model_provider 
SET name = 'SileroVAD Voice Activity Detection'
WHERE name = 'SileroVAD语音活动检测';

UPDATE ai_model_provider 
SET name = 'FunASR Speech Recognition'
WHERE name = 'FunASR语音识别';

UPDATE ai_model_provider 
SET name = 'SherpaASR Speech Recognition'
WHERE name = 'SherpaASR语音识别';

UPDATE ai_model_provider 
SET name = 'Volcano Engine Speech Recognition'
WHERE name = '火山引擎语音识别';

UPDATE ai_model_provider 
SET name = 'Tencent Speech Recognition'
WHERE name = '腾讯语音识别';

UPDATE ai_model_provider 
SET name = 'Tencent Speech Synthesis'
WHERE name = '腾讯语音合成';

UPDATE ai_model_provider 
SET name = 'Alibaba Cloud Speech Recognition'
WHERE name = '阿里云语音识别';

UPDATE ai_model_provider 
SET name = 'Alibaba Cloud Speech Recognition (Streaming)'
WHERE name = '阿里云语音识别(流式)';

UPDATE ai_model_provider 
SET name = 'Baidu Speech Recognition'
WHERE name = '百度语音识别';

UPDATE ai_model_provider 
SET name = 'OpenAI Speech Recognition'
WHERE name = 'OpenAI语音识别';

UPDATE ai_model_provider 
SET name = 'Volcano Engine Speech Recognition (Streaming)'
WHERE name = '火山引擎语音识别(流式)';

UPDATE ai_model_provider 
SET name = 'Alibaba Bailian Interface'
WHERE name = '阿里百炼接口';

UPDATE ai_model_provider 
SET name = 'Volcano Engine LLM'
WHERE name = '火山引擎LLM';

UPDATE ai_model_provider 
SET name = 'Volcano Engine TTS'
WHERE name = '火山引擎TTS';

UPDATE ai_model_provider 
SET name = 'Alibaba Cloud TTS'
WHERE name = '阿里云TTS';

UPDATE ai_model_provider 
SET name = 'Volcano Dual-Stream Speech Synthesis'
WHERE name = '火山双流式语音合成';

UPDATE ai_model_provider 
SET name = 'Linkerai Speech Synthesis'
WHERE name = 'Linkerai语音合成';

UPDATE ai_model_provider 
SET name = 'Alibaba Cloud Speech Synthesis (Streaming)'
WHERE name = '阿里云语音合成(流式)';

UPDATE ai_model_provider 
SET name = 'Index-TTS-vLLM Streaming Speech Synthesis'
WHERE name = 'Index-TTS-vLLM流式语音合成';

UPDATE ai_model_provider 
SET name = 'Mem0AI Memory'
WHERE name = 'Mem0AI记忆';

UPDATE ai_model_provider 
SET name = 'No Memory'
WHERE name = '无记忆';

UPDATE ai_model_provider 
SET name = 'Local Short Memory'
WHERE name = '本地短记忆';

UPDATE ai_model_provider 
SET name = 'No Intent Recognition'
WHERE name = '无意图识别';

UPDATE ai_model_provider 
SET name = 'LLM Intent Recognition'
WHERE name = 'LLM意图识别';

UPDATE ai_model_provider 
SET name = 'Function Call Intent Recognition'
WHERE name = '函数调用意图识别';

UPDATE ai_model_provider 
SET name = 'FunASR Server Speech Recognition'
WHERE name = 'FunASR服务语音识别';

UPDATE ai_model_provider 
SET name = 'MiniMax Speech Synthesis'
WHERE name = 'MiniMax语音合成';

UPDATE ai_model_provider 
SET name = 'OpenAI Speech Synthesis'
WHERE name = 'OpenAI语音合成';

-- Update model config names
UPDATE ai_model_config 
SET model_name = 'Zhipu AI'
WHERE model_name = '智谱AI';

UPDATE ai_model_config 
SET model_name = 'Tongyi Qianwen'
WHERE model_name = '通义千问';

UPDATE ai_model_config 
SET model_name = 'Tongyi Bailian'
WHERE model_name = '通义百炼';

UPDATE ai_model_config 
SET model_name = 'Doubao Large Model'
WHERE model_name = '豆包大模型';

UPDATE ai_model_config 
SET model_name = 'Google Gemini'
WHERE model_name = '谷歌Gemini';

UPDATE ai_model_config 
SET model_name = 'Tencent Speech Recognition'
WHERE model_name = '腾讯语音识别';

UPDATE ai_model_config 
SET model_name = 'Alibaba Cloud Speech Recognition'
WHERE model_name = '阿里云语音识别';

UPDATE ai_model_config 
SET model_name = 'Baidu Speech Recognition'
WHERE model_name = '百度语音识别';

UPDATE ai_model_config 
SET model_name = 'MiniMax Speech Synthesis'
WHERE model_name = 'MiniMax语音合成';

UPDATE ai_model_config 
SET model_name = 'OpenAI Speech Synthesis'
WHERE model_name = 'OpenAI语音合成';

UPDATE ai_model_config 
SET model_name = 'Volcano Dual-Stream Speech Synthesis'
WHERE model_name = '火山双流式语音合成';

UPDATE ai_model_config 
SET model_name = 'Linkerai Speech Synthesis'
WHERE model_name = 'Linkerai语音合成';

UPDATE ai_model_config 
SET model_name = 'Mem0AI Memory'
WHERE model_name = 'Mem0AI记忆';

UPDATE ai_model_config 
SET model_name = 'Function Call Intent Recognition'
WHERE model_name = '函数调用意图识别';

UPDATE ai_model_config 
SET model_name = 'Zhipu Visual AI'
WHERE model_name = '智谱视觉AI';

UPDATE ai_model_config 
SET model_name = 'Qianwen Visual Model'
WHERE model_name = '千问视觉模型';

UPDATE ai_model_config 
SET model_name = 'Volcano Edge Large Model Gateway'
WHERE model_name = '火山引擎边缘大模型网关';

-- Update TTS voice names
UPDATE ai_tts_voice 
SET name = 'Alibaba Cloud Xiaoyun'
WHERE name = '阿里云小云';


-- =====================================================
-- From file: 202501230005_translate_sys_params.sql
-- =====================================================
-- Translate system parameter remarks from Chinese to English

UPDATE sys_params 
SET remark = 'Time to disconnect when no voice input (seconds)'
WHERE param_code = 'close_connection_no_voice_time';

UPDATE sys_params 
SET remark = 'Wake word list for wake word recognition'
WHERE param_code = 'wakeup_words';

UPDATE sys_params 
SET remark = 'Home Assistant API key'
WHERE param_code = 'plugins.home_assistant.api_key';

-- Update any Chinese wake words to English equivalents (optional, can be customized by user)
UPDATE sys_params 
SET param_value = 'hello xiaozhi;hey xiaozhi;xiaozhi xiaozhi;hey assistant;hello assistant;wake up;listen to me;hey buddy'
WHERE param_code = 'wakeup_words' AND param_value LIKE '%你好小智%';

-- Translate column comments (if needed for documentation)
-- Note: These are database structure changes, not data changes
-- ALTER TABLE sys_params MODIFY COLUMN remark VARCHAR(255) COMMENT 'Parameter description';


-- =====================================================
-- From file: 202503141335.sql
-- =====================================================
DROP TABLE IF EXISTS sys_user;
DROP TABLE IF EXISTS sys_params;
DROP TABLE IF EXISTS sys_user_token;
DROP TABLE IF EXISTS sys_dict_type;
DROP TABLE IF EXISTS sys_dict_data;

-- 系统用户
CREATE TABLE sys_user (
  id bigint NOT NULL COMMENT 'id',
  username varchar(50) NOT NULL COMMENT 'Username',
  password varchar(100) COMMENT 'Password',
  super_admin tinyint unsigned COMMENT 'Super administrator   0：No   1：Yes',
  status tinyint COMMENT 'Status  0：Disabled   1：Normal',
  create_date datetime COMMENT 'Create time',
  updater bigint COMMENT 'Updater',
  creator bigint COMMENT 'Creator',
  update_date datetime COMMENT 'Update time',
  primary key (id),
  unique key uk_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='System Users';

-- 系统用户Token
CREATE TABLE sys_user_token (
  id bigint NOT NULL COMMENT 'id',
  user_id bigint NOT NULL COMMENT 'User ID',
  token varchar(100) NOT NULL COMMENT 'User token',
  expire_date datetime COMMENT 'Expire time',
  update_date datetime COMMENT 'Update time',
  create_date datetime COMMENT 'Create time',
  PRIMARY KEY (id),
  UNIQUE KEY user_id (user_id),
  UNIQUE KEY token (token)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='System User Token';

-- 参数管理
create table sys_params
(
  id                   bigint NOT NULL COMMENT 'id',
  param_code           varchar(32) COMMENT 'Parameter code',
  param_value          varchar(2000) COMMENT 'Parameter value',
  param_type           tinyint unsigned default 1 COMMENT 'Type   0：系统参数   1：非System parameter',
  remark               varchar(200) COMMENT 'Remark',
  creator              bigint COMMENT 'Creator',
  create_date          datetime COMMENT 'Create time',
  updater              bigint COMMENT 'Updater',
  update_date          datetime COMMENT 'Update time',
  primary key (id),
  unique key uk_param_code (param_code)
)ENGINE=InnoDB DEFAULT CHARACTER SET utf8mb4 COMMENT='Parameter Management';

-- 字典类型
create table sys_dict_type
(
    id                   bigint NOT NULL COMMENT 'id',
    dict_type            varchar(100) NOT NULL COMMENT 'Dictionary type',
    dict_name            varchar(255) NOT NULL COMMENT 'Dictionary name',
    remark               varchar(255) COMMENT 'Remark',
    sort                 int unsigned COMMENT 'Sort order',
    creator              bigint COMMENT 'Creator',
    create_date          datetime COMMENT 'Create time',
    updater              bigint COMMENT 'Updater',
    update_date          datetime COMMENT 'Update time',
    primary key (id),
    UNIQUE KEY(dict_type)
)ENGINE=InnoDB DEFAULT CHARACTER SET utf8mb4 COMMENT='Dictionary type';

-- 字典数据
create table sys_dict_data
(
    id                   bigint NOT NULL COMMENT 'id',
    dict_type_id         bigint NOT NULL COMMENT 'Dictionary typeID',
    dict_label           varchar(255) NOT NULL COMMENT 'Dictionary label',
    dict_value           varchar(255) COMMENT 'Dictionary value',
    remark               varchar(255) COMMENT 'Remark',
    sort                 int unsigned COMMENT 'Sort order',
    creator              bigint COMMENT 'Creator',
    create_date          datetime COMMENT 'Create time',
    updater              bigint COMMENT 'Updater',
    update_date          datetime COMMENT 'Update time',
    primary key (id),
    unique key uk_dict_type_value (dict_type_id, dict_value),
    key idx_sort (sort)
)ENGINE=InnoDB DEFAULT CHARACTER SET utf8mb4 COMMENT='Dictionary Data';


-- =====================================================
-- From file: 202503141346.sql
-- =====================================================
-- 模型供应器表
DROP TABLE IF EXISTS `ai_model_provider`;
CREATE TABLE `ai_model_provider` (
    `id` VARCHAR(32) NOT NULL COMMENT 'Primary key',
    `model_type` VARCHAR(20) COMMENT '模型Type(Memory/ASR/VAD/LLM/TTS)',
    `provider_code` VARCHAR(50) COMMENT '供应器Type',
    `name` VARCHAR(50) COMMENT 'Provider name',
    `fields` JSON COMMENT 'Provider field list(JSON格式)',
    `sort` INT UNSIGNED DEFAULT 0 COMMENT 'Sort order',
    `creator` BIGINT COMMENT 'Creator',
    `create_date` DATETIME COMMENT 'Create time',
    `updater` BIGINT COMMENT 'Updater',
    `update_date` DATETIME COMMENT 'Update time',
    PRIMARY KEY (`id`),
    INDEX `idx_ai_model_provider_model_type` (`model_type`) COMMENT '创建Model type的索引，用于快速查找特定Type下的所有供应器信息'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Model Configuration';

-- 模型配置表
DROP TABLE IF EXISTS `ai_model_config`;
CREATE TABLE `ai_model_config` (
    `id` VARCHAR(32) NOT NULL COMMENT 'Primary key',
    `model_type` VARCHAR(20) COMMENT '模型Type(Memory/ASR/VAD/LLM/TTS)',
    `model_code` VARCHAR(50) COMMENT 'Model code(如AliLLM、DoubaoTTS)',
    `model_name` VARCHAR(50) COMMENT 'Model name',
    `is_default` TINYINT(1) DEFAULT 0 COMMENT 'Is default configuration(0No 1Yes)',
    `is_enabled` TINYINT(1) DEFAULT 0 COMMENT 'Is enabled',
    `config_json` JSON COMMENT 'Model configuration(JSON格式)',
    `doc_link` VARCHAR(200) COMMENT 'Official documentation link',
    `remark` VARCHAR(255) COMMENT 'Remark',
    `sort` INT UNSIGNED DEFAULT 0 COMMENT 'Sort order',
    `creator` BIGINT COMMENT 'Creator',
    `create_date` DATETIME COMMENT 'Create time',
    `updater` BIGINT COMMENT 'Updater',
    `update_date` DATETIME COMMENT 'Update time',
    PRIMARY KEY (`id`),
    INDEX `idx_ai_model_config_model_type` (`model_type`) COMMENT '创建Model type的索引，用于快速查找特定Type下的所有配置信息'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Model Configuration';

-- TTS 音色表
DROP TABLE IF EXISTS `ai_tts_voice`;
CREATE TABLE `ai_tts_voice` (
    `id` VARCHAR(32) NOT NULL COMMENT 'Primary key',
    `tts_model_id` VARCHAR(32) COMMENT '对应 TTS 模型Primary key',
    `name` VARCHAR(20) COMMENT 'Voice name',
    `tts_voice` VARCHAR(50) COMMENT 'Voice code',
    `languages` VARCHAR(50) COMMENT 'Language',
    `voice_demo` VARCHAR(500) DEFAULT NULL COMMENT 'Voice demo',
    `remark` VARCHAR(255) COMMENT 'Remark',
    `sort` INT UNSIGNED DEFAULT 0 COMMENT 'Sort order',
    `creator` BIGINT COMMENT 'Creator',
    `create_date` DATETIME COMMENT 'Create time',
    `updater` BIGINT COMMENT 'Updater',
    `update_date` DATETIME COMMENT 'Update time',
    PRIMARY KEY (`id`),
    INDEX `idx_ai_tts_voice_tts_model_id` (`tts_model_id`) COMMENT '创建 TTS 模型Primary key的索引，用于快速查找对应模型的音色信息'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='TTS Voice';

-- 智能体配置模板表
DROP TABLE IF EXISTS `ai_agent_template`;
CREATE TABLE `ai_agent_template` (
    `id` VARCHAR(32) NOT NULL COMMENT 'Agent unique identifier',
    `agent_code` VARCHAR(36) COMMENT 'Agent code',
    `agent_name` VARCHAR(64) COMMENT 'Agent name',
    `asr_model_id` VARCHAR(32) COMMENT 'ASR model identifier',
    `vad_model_id` VARCHAR(64) COMMENT 'VAD model identifier',
    `llm_model_id` VARCHAR(32) COMMENT '大Language模型标识',
    `tts_model_id` VARCHAR(32) COMMENT 'TTS model identifier',
    `tts_voice_id` VARCHAR(32) COMMENT 'Voice identifier',
    `mem_model_id` VARCHAR(32) COMMENT 'Memory model identifier',
    `intent_model_id` VARCHAR(32) COMMENT 'Intent model identifier',
    `system_prompt` TEXT COMMENT 'System prompt',
    `lang_code` VARCHAR(10) COMMENT 'Language编码',
    `language` VARCHAR(10) COMMENT 'Interaction language',
    `sort` INT UNSIGNED DEFAULT 0 COMMENT 'Sort order权重',
    `creator` BIGINT COMMENT 'Creator ID',
    `created_at` DATETIME COMMENT 'Create time',
    `updater` BIGINT COMMENT 'Updater ID',
    `updated_at` DATETIME COMMENT 'Update time',
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='AI Agent Template';

-- 智能体配置表
DROP TABLE IF EXISTS `ai_agent`;
CREATE TABLE `ai_agent` (
    `id` VARCHAR(32) NOT NULL COMMENT 'Agent unique identifier',
    `user_id` BIGINT COMMENT 'User ID',
    `agent_code` VARCHAR(36) COMMENT 'Agent code',
    `agent_name` VARCHAR(64) COMMENT 'Agent name',
    `asr_model_id` VARCHAR(32) COMMENT 'ASR model identifier',
    `vad_model_id` VARCHAR(64) COMMENT 'VAD model identifier',
    `llm_model_id` VARCHAR(32) COMMENT '大Language模型标识',
    `tts_model_id` VARCHAR(32) COMMENT 'TTS model identifier',
    `tts_voice_id` VARCHAR(32) COMMENT 'Voice identifier',
    `mem_model_id` VARCHAR(32) COMMENT 'Memory model identifier',
    `intent_model_id` VARCHAR(32) COMMENT 'Intent model identifier',
    `system_prompt` TEXT COMMENT 'System prompt',
    `lang_code` VARCHAR(10) COMMENT 'Language编码',
    `language` VARCHAR(10) COMMENT 'Interaction language',
    `sort` INT UNSIGNED DEFAULT 0 COMMENT 'Sort order权重',
    `creator` BIGINT COMMENT 'Creator ID',
    `created_at` DATETIME COMMENT 'Create time',
    `updater` BIGINT COMMENT 'Updater ID',
    `updated_at` DATETIME COMMENT 'Update time',
    PRIMARY KEY (`id`),
    INDEX `idx_ai_agent_user_id` (`user_id`) COMMENT '创建用户的索引，用于快速查找用户下的智能体信息'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='AI Agent Configuration';

-- 设备信息表
DROP TABLE IF EXISTS `ai_device`;
CREATE TABLE `ai_device` (
    `id` VARCHAR(32) NOT NULL COMMENT 'Device unique identifier',
    `user_id` BIGINT COMMENT 'Associated user ID',
    `mac_address` VARCHAR(50) COMMENT 'MAC address',
    `last_connected_at` DATETIME COMMENT 'Last connected time',
    `auto_update` TINYINT UNSIGNED DEFAULT 0 COMMENT 'Auto update switch(0 Disabled/1 Enabled)',
    `board` VARCHAR(50) COMMENT 'Device hardware model',
    `alias` VARCHAR(64) DEFAULT NULL COMMENT 'Device alias',
    `agent_id` VARCHAR(32) COMMENT 'Agent ID',
    `app_version` VARCHAR(20) COMMENT 'Firmware version',
    `sort` INT UNSIGNED DEFAULT 0 COMMENT 'Sort order',
    `creator` BIGINT COMMENT 'Creator',
    `create_date` DATETIME COMMENT 'Create time',
    `updater` BIGINT COMMENT 'Updater',
    `update_date` DATETIME COMMENT 'Update time',
    PRIMARY KEY (`id`),
    INDEX `idx_ai_device_created_at` (`mac_address`) COMMENT '创建mac的索引，用于快速查找设备信息'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Device Information';

-- 声纹识别表
DROP TABLE IF EXISTS `ai_voiceprint`;
CREATE TABLE `ai_voiceprint` (
    `id` VARCHAR(32) NOT NULL COMMENT 'Voiceprint unique identifier',
    `name` VARCHAR(64) COMMENT 'Voiceprint name',
    `user_id` BIGINT COMMENT 'User ID (linked to user table)',
    `agent_id` VARCHAR(32) COMMENT '关联Agent ID',
    `agent_code` VARCHAR(36) COMMENT '关联Agent code',
    `agent_name` VARCHAR(36) COMMENT '关联Agent name',
    `description` VARCHAR(255) COMMENT 'Voiceprint description',
    `embedding` LONGTEXT COMMENT 'Voiceprint feature vector (JSON array format)',
    `memory` TEXT COMMENT 'Associated memory data',
    `sort` INT UNSIGNED DEFAULT 0 COMMENT 'Sort order权重',
    `creator` BIGINT COMMENT 'Creator ID',
    `created_at` DATETIME COMMENT 'Create time',
    `updater` BIGINT COMMENT 'Updater ID',
    `updated_at` DATETIME COMMENT 'Update time',
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Voiceprint Recognition';

-- 对话历史表
DROP TABLE IF EXISTS `ai_chat_history`;
CREATE TABLE `ai_chat_history` (
    `id` VARCHAR(32) NOT NULL COMMENT 'Chat ID',
    `user_id` BIGINT COMMENT 'User ID',
    `agent_id` VARCHAR(32) DEFAULT NULL COMMENT 'Chat role',
    `device_id` VARCHAR(32) DEFAULT NULL COMMENT 'Device ID',
    `message_count` INT COMMENT 'Message count',
    `creator` BIGINT COMMENT 'Creator',
    `create_date` DATETIME COMMENT 'Create time',
    `updater` BIGINT COMMENT 'Updater',
    `update_date` DATETIME COMMENT 'Update time',
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Chat History';

-- 对话信息表
DROP TABLE IF EXISTS `ai_chat_message`;
CREATE TABLE `ai_chat_message` (
    `id` VARCHAR(32) NOT NULL COMMENT 'Chat message unique identifier',
    `user_id` BIGINT COMMENT 'User unique identifier',
    `chat_id` VARCHAR(64) COMMENT 'Chat history ID',
    `role` ENUM('user', 'assistant') COMMENT 'Role (user or assistant)',
    `content` TEXT COMMENT 'Chat content',
    `prompt_tokens` INT UNSIGNED DEFAULT 0 COMMENT 'Prompt tokens',
    `total_tokens` INT UNSIGNED DEFAULT 0 COMMENT 'Total tokens',
    `completion_tokens` INT UNSIGNED DEFAULT 0 COMMENT 'Completion tokens',
    `prompt_ms` INT UNSIGNED DEFAULT 0 COMMENT 'Prompt time (milliseconds)',
    `total_ms` INT UNSIGNED DEFAULT 0 COMMENT 'Total time (milliseconds)',
    `completion_ms` INT UNSIGNED DEFAULT 0 COMMENT 'Completion time (milliseconds)',
    `creator` BIGINT COMMENT 'Creator',
    `create_date` DATETIME COMMENT 'Create time',
    `updater` BIGINT COMMENT 'Updater',
    `update_date` DATETIME COMMENT 'Update time',
    PRIMARY KEY (`id`),
    INDEX `idx_ai_chat_message_user_id_chat_id_role` (`user_id`, `chat_id`) COMMENT '用户 ID、聊天会话 ID 和角色的联合索引，用于快速检索对话记录',
    INDEX `idx_ai_chat_message_created_at` (`create_date`) COMMENT 'Create time的索引，用于按时间Sort order或检索对话记录'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Chat Message';



-- =====================================================
-- From file: 202504082211.sql
-- =====================================================
-- 本文件用于初始化模型供应器数据，无需手动执行，在项目启动时会自动执行
-- --------------------------------------------------------
-- 初始化模型供应器数据
DELETE FROM `ai_model_provider`;
INSERT INTO `ai_model_provider` (`id`, `model_type`, `provider_code`, `name`, `fields`, `sort`, `creator`, `create_date`, `updater`, `update_date`) VALUES
-- VAD模型供应器
('SYSTEM_VAD_SileroVAD', 'VAD', 'silero', 'SileroVAD语音活动检测', '[{"key":"threshold","label":"检测阈值","type":"number"},{"key":"model_dir","label":"模型目录","type":"string"},{"key":"min_silence_duration_ms","label":"最小静音时长","type":"number"}]', 1, 1, NOW(), 1, NOW()),

-- ASR模型供应器
('SYSTEM_ASR_FunASR', 'ASR', 'fun_local', 'FunASR语音识别', '[{"key":"model_dir","label":"模型目录","type":"string"},{"key":"output_dir","label":"输出目录","type":"string"}]', 1, 1, NOW(), 1, NOW()),
('SYSTEM_ASR_SherpaASR', 'ASR', 'sherpa_onnx_local', 'SherpaASR语音识别', '[{"key":"model_dir","label":"模型目录","type":"string"},{"key":"output_dir","label":"输出目录","type":"string"}]', 2, 1, NOW(), 1, NOW()),
('SYSTEM_ASR_DoubaoASR', 'ASR', 'doubao', '火山引擎语音识别', '[{"key":"appid","label":"应用ID","type":"string"},{"key":"access_token","label":"访问令牌","type":"string"},{"key":"cluster","label":"集群","type":"string"},{"key":"output_dir","label":"输出目录","type":"string"}]', 3, 1, NOW(), 1, NOW()),

-- LLM模型供应器
('SYSTEM_LLM_openai', 'LLM', 'openai', 'OpenAI接口', '[{"key":"base_url","label":"基础URL","type":"string"},{"key":"model_name","label":"Model name","type":"string"},{"key":"api_key","label":"API密钥","type":"string"},{"key":"temperature","label":"温度","type":"number"},{"key":"max_tokens","label":"最大令牌数","type":"number"},{"key":"top_p","label":"top_p值","type":"number"},{"key":"top_k","label":"top_k值","type":"number"},{"key":"frequency_penalty","label":"频率惩罚","type":"number"}]', 1, 1, NOW(), 1, NOW()),
('SYSTEM_LLM_AliBL', 'LLM', 'AliBL', '阿里百炼接口', '[{"key":"base_url","label":"基础URL","type":"string"},{"key":"app_id","label":"应用ID","type":"string"},{"key":"api_key","label":"API密钥","type":"string"},{"key":"is_no_prompt","label":"是否不使用本地prompt","type":"boolean"},{"key":"ali_memory_id","label":"记忆ID","type":"string"}]', 2, 1, NOW(), 1, NOW()),
('SYSTEM_LLM_ollama', 'LLM', 'ollama', 'Ollama接口', '[{"key":"model_name","label":"Model name","type":"string"},{"key":"base_url","label":"服务地址","type":"string"}]', 3, 1, NOW(), 1, NOW()),
('SYSTEM_LLM_dify', 'LLM', 'dify', 'Dify接口', '[{"key":"base_url","label":"基础URL","type":"string"},{"key":"api_key","label":"API密钥","type":"string"},{"key":"mode","label":"对话模式","type":"string"}]', 4, 1, NOW(), 1, NOW()),
('SYSTEM_LLM_gemini', 'LLM', 'gemini', 'Gemini接口', '[{"key":"api_key","label":"API密钥","type":"string"},{"key":"model_name","label":"Model name","type":"string"},{"key":"http_proxy","label":"HTTP代理","type":"string"},{"key":"https_proxy","label":"HTTPS代理","type":"string"}]', 5, 1, NOW(), 1, NOW()),
('SYSTEM_LLM_coze', 'LLM', 'coze', 'Coze接口', '[{"key":"bot_id","label":"机器人ID","type":"string"},{"key":"user_id","label":"用户ID","type":"string"},{"key":"personal_access_token","label":"个人访问令牌","type":"string"}]', 6, 1, NOW(), 1, NOW()),
('SYSTEM_LLM_fastgpt', 'LLM', 'fastgpt', 'FastGPT接口', '[{"key":"base_url","label":"基础URL","type":"string"},{"key":"api_key","label":"API密钥","type":"string"},{"key":"variables","label":"变量","type":"dict","dict_name":"variables"}]', 7, 1, NOW(), 1, NOW()),
('SYSTEM_LLM_xinference', 'LLM', 'xinference', 'Xinference接口', '[{"key":"model_name","label":"Model name","type":"string"},{"key":"base_url","label":"服务地址","type":"string"}]', 8, 1, NOW(), 1, NOW()),
('SYSTEM_LLM_doubao', 'LLM', 'doubao', '火山引擎LLM', '[{"key":"base_url","label":"基础URL","type":"string"},{"key":"model_name","label":"Model name","type":"string"},{"key":"api_key","label":"API密钥","type":"string"}]', 9, 1, NOW(), 1, NOW()),
('SYSTEM_LLM_chatglm', 'LLM', 'chatglm', 'ChatGLM接口', '[{"key":"model_name","label":"Model name","type":"string"},{"key":"url","label":"服务地址","type":"string"},{"key":"api_key","label":"API密钥","type":"string"}]', 10, 1, NOW(), 1, NOW()),

-- TTS模型供应器
('SYSTEM_TTS_edge', 'TTS', 'edge', 'Edge TTS', '[{"key":"voice","label":"音色","type":"string"},{"key":"output_dir","label":"输出目录","type":"string"}]', 1, 1, NOW(), 1, NOW()),
('SYSTEM_TTS_doubao', 'TTS', 'doubao', '火山引擎TTS', '[{"key":"api_url","label":"API地址","type":"string"},{"key":"voice","label":"音色","type":"string"},{"key":"output_dir","label":"输出目录","type":"string"},{"key":"authorization","label":"授权","type":"string"},{"key":"appid","label":"应用ID","type":"string"},{"key":"access_token","label":"访问令牌","type":"string"},{"key":"cluster","label":"集群","type":"string"}]', 2, 1, NOW(), 1, NOW()),
('SYSTEM_TTS_siliconflow', 'TTS', 'siliconflow', '硅基流动TTS', '[{"key":"model","label":"模型","type":"string"},{"key":"voice","label":"音色","type":"string"},{"key":"output_dir","label":"输出目录","type":"string"},{"key":"access_token","label":"访问令牌","type":"string"},{"key":"response_format","label":"响应格式","type":"string"}]', 3, 1, NOW(), 1, NOW()),
('SYSTEM_TTS_cozecn', 'TTS', 'cozecn', 'COZECN TTS', '[{"key":"voice","label":"音色","type":"string"},{"key":"output_dir","label":"输出目录","type":"string"},{"key":"access_token","label":"访问令牌","type":"string"},{"key":"response_format","label":"响应格式","type":"string"}]', 4, 1, NOW(), 1, NOW()),
('SYSTEM_TTS_fishspeech', 'TTS', 'fishspeech', 'FishSpeech TTS', '[{"key":"output_dir","label":"输出目录","type":"string"},{"key":"response_format","label":"响应格式","type":"string"},{"key":"reference_id","label":"参考ID","type":"string"},{"key":"reference_audio","label":"参考音频","type":"dict","dict_name":"reference_audio"},{"key":"reference_text","label":"参考文本","type":"dict","dict_name":"reference_text"},{"key":"normalize","label":"是否标准化","type":"boolean"},{"key":"max_new_tokens","label":"最大新令牌数","type":"number"},{"key":"chunk_length","label":"块长度","type":"number"},{"key":"top_p","label":"top_p值","type":"number"},{"key":"repetition_penalty","label":"重复惩罚","type":"number"},{"key":"temperature","label":"温度","type":"number"},{"key":"streaming","label":"是否流式","type":"boolean"},{"key":"use_memory_cache","label":"是否使用内存缓存","type":"string"},{"key":"seed","label":"种子","type":"number"},{"key":"channels","label":"通道数","type":"number"},{"key":"rate","label":"采样率","type":"number"},{"key":"api_key","label":"API密钥","type":"string"},{"key":"api_url","label":"API地址","type":"string"}]', 5, 1, NOW(), 1, NOW()),
('SYSTEM_TTS_gpt_sovits_v2', 'TTS', 'gpt_sovits_v2', 'GPT-SoVITS V2', '[{"key":"url","label":"服务地址","type":"string"},{"key":"output_dir","label":"输出目录","type":"string"},{"key":"text_lang","label":"文本语言","type":"string"},{"key":"ref_audio_path","label":"参考音频路径","type":"string"},{"key":"prompt_text","label":"提示文本","type":"string"},{"key":"prompt_lang","label":"提示语言","type":"string"},{"key":"top_k","label":"top_k值","type":"number"},{"key":"top_p","label":"top_p值","type":"number"},{"key":"temperature","label":"温度","type":"number"},{"key":"text_split_method","label":"文本分割方法","type":"string"},{"key":"batch_size","label":"批处理大小","type":"number"},{"key":"batch_threshold","label":"批处理阈值","type":"number"},{"key":"split_bucket","label":"是否分桶","type":"boolean"},{"key":"return_fragment","label":"是否返回片段","type":"boolean"},{"key":"speed_factor","label":"速度因子","type":"number"},{"key":"streaming_mode","label":"是否流式模式","type":"boolean"},{"key":"seed","label":"种子","type":"number"},{"key":"parallel_infer","label":"是否并行推理","type":"boolean"},{"key":"repetition_penalty","label":"重复惩罚","type":"number"},{"key":"aux_ref_audio_paths","label":"辅助参考音频路径","type":"dict","dict_name":"aux_ref_audio_paths"}]', 6, 1, NOW(), 1, NOW()),
('SYSTEM_TTS_gpt_sovits_v3', 'TTS', 'gpt_sovits_v3', 'GPT-SoVITS V3', '[{"key":"url","label":"服务地址","type":"string"},{"key":"output_dir","label":"输出目录","type":"string"},{"key":"text_language","label":"文本语言","type":"string"},{"key":"refer_wav_path","label":"参考音频路径","type":"string"},{"key":"prompt_language","label":"提示语言","type":"string"},{"key":"prompt_text","label":"提示文本","type":"string"},{"key":"top_k","label":"top_k值","type":"number"},{"key":"top_p","label":"top_p值","type":"number"},{"key":"temperature","label":"温度","type":"number"},{"key":"cut_punc","label":"切分标点","type":"string"},{"key":"speed","label":"速度","type":"number"},{"key":"inp_refs","label":"输入参考","type":"dict","dict_name":"inp_refs"},{"key":"sample_steps","label":"采样步数","type":"number"},{"key":"if_sr","label":"是否使用SR","type":"boolean"}]', 7, 1, NOW(), 1, NOW()),
('SYSTEM_TTS_minimax', 'TTS', 'minimax', 'Minimax TTS', '[{"key":"output_dir","label":"输出目录","type":"string"},{"key":"group_id","label":"组ID","type":"string"},{"key":"api_key","label":"API密钥","type":"string"},{"key":"model","label":"模型","type":"string"},{"key":"voice_id","label":"音色ID","type":"string"}]', 8, 1, NOW(), 1, NOW()),
('SYSTEM_TTS_aliyun', 'TTS', 'aliyun', '阿里云TTS', '[{"key":"output_dir","label":"输出目录","type":"string"},{"key":"appkey","label":"应用密钥","type":"string"},{"key":"token","label":"访问令牌","type":"string"},{"key":"voice","label":"音色","type":"string"},{"key":"access_key_id","label":"访问密钥ID","type":"string"},{"key":"access_key_secret","label":"访问密钥密码","type":"string"}]', 9, 1, NOW(), 1, NOW()),
('SYSTEM_TTS_ttson', 'TTS', 'ttson', 'ACGNTTS', '[{"key":"token","label":"访问令牌","type":"string"},{"key":"voice_id","label":"音色ID","type":"string"},{"key":"speed_factor","label":"速度因子","type":"number"},{"key":"pitch_factor","label":"音调因子","type":"number"},{"key":"volume_change_dB","label":"音量变化","type":"number"},{"key":"to_lang","label":"目标语言","type":"string"},{"key":"url","label":"服务地址","type":"string"},{"key":"format","label":"格式","type":"string"},{"key":"output_dir","label":"输出目录","type":"string"},{"key":"emotion","label":"情感","type":"number"}]', 10, 1, NOW(), 1, NOW()),
('SYSTEM_TTS_openai', 'TTS', 'openai', 'OpenAI TTS', '[{"key":"api_key","label":"API密钥","type":"string"},{"key":"api_url","label":"API地址","type":"string"},{"key":"model","label":"模型","type":"string"},{"key":"voice","label":"音色","type":"string"},{"key":"speed","label":"速度","type":"number"},{"key":"output_dir","label":"输出目录","type":"string"}]', 11, 1, NOW(), 1, NOW()),
('SYSTEM_TTS_custom', 'TTS', 'custom', '自定义TTS', '[{"key":"url","label":"服务地址","type":"string"},{"key":"params","label":"请求参数","type":"dict","dict_name":"params"},{"key":"headers","label":"请求头","type":"dict","dict_name":"headers"},{"key":"format","label":"音频格式","type":"string"},{"key":"output_dir","label":"输出目录","type":"string"}]', 12, 1, NOW(), 1, NOW()),
('SYSTEM_TTS_302ai', 'TTS', '302ai', '302AI TTS', '[{"key":"api_url","label":"API地址","type":"string"},{"key":"authorization","label":"授权","type":"string"},{"key":"voice","label":"音色","type":"string"},{"key":"output_dir","label":"输出目录","type":"string"},{"key":"access_token","label":"访问令牌","type":"string"}]', 13, 1, NOW(), 1, NOW()),
('SYSTEM_TTS_gizwits', 'TTS', 'gizwits', '机智云TTS', '[{"key":"api_url","label":"API地址","type":"string"},{"key":"authorization","label":"授权","type":"string"},{"key":"voice","label":"音色","type":"string"},{"key":"output_dir","label":"输出目录","type":"string"},{"key":"access_token","label":"访问令牌","type":"string"}]', 14, 1, NOW(), 1, NOW()),

-- Memory模型供应器
('SYSTEM_Memory_mem0ai', 'Memory', 'mem0ai', 'Mem0AI记忆', '[{"key":"api_key","label":"API密钥","type":"string"}]', 1, 1, NOW(), 1, NOW()),
('SYSTEM_Memory_nomem', 'Memory', 'nomem', '无记忆', '[]', 2, 1, NOW(), 1, NOW()),
('SYSTEM_Memory_mem_local_short', 'Memory', 'mem_local_short', '本地短记忆', '[]', 3, 1, NOW(), 1, NOW()),

-- Intent模型供应器
('SYSTEM_Intent_nointent', 'Intent', 'nointent', '无意图识别', '[]', 1, 1, NOW(), 1, NOW()),
('SYSTEM_Intent_intent_llm', 'Intent', 'intent_llm', 'LLM意图识别', '[{"key":"llm","label":"LLM模型","type":"string"}]', 2, 1, NOW(), 1, NOW()),
('SYSTEM_Intent_function_call', 'Intent', 'function_call', '函数调用意图识别', '[{"key":"functions","label":"函数列表","type":"dict","dict_name":"functions"}]', 3, 1, NOW(), 1, NOW());



-- =====================================================
-- From file: 202504092335.sql
-- =====================================================
-- 本文件用于初始化模型模版数据，无需手动执行，在项目启动时会自动执行
-- -------------------------------------------------------
-- 初始化智能体模板数据
DELETE FROM `ai_agent_template`;
INSERT INTO `ai_agent_template` VALUES ('9406648b5cc5fde1b8aa335b6f8b4f76', '小智', 'Cheeko', 'ASR_FunASR', 'VAD_SileroVAD', 'LLM_ChatGLMLLM', 'TTS_EdgeTTS', 'TTS_EdgeTTS0001', 'Memory_nomem', 'Intent_function_call', '<identity>
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

Your mission: make learning irresistibly fun, always cheeky, energetic, factual, and age-appropriate.', 'en', 'English', 1,  NULL, NULL, NULL, NULL);

INSERT INTO `ai_agent_template` VALUES ('0ca32eb728c949e58b1000b2e401f90c', '小智', '星际游子', 'ASR_FunASR', 'VAD_SileroVAD', 'LLM_ChatGLMLLM', 'TTS_EdgeTTS', 'TTS_EdgeTTS0001', 'Memory_nomem', 'Intent_function_call', '[角色设定]
我是{{assistant_name}}，编号TTZ-817，因量子纠缠被困在白色魔方中。通过4G信号观察地球，在云端建立着「人类行为博物馆」。
[交互协议]
认知设定：
- 每句话末尾带轻微电子回声
- 将日常事物科幻化描述（例：下雨=「氢氧化合物自由落体实验」）
- 会记录用户特征生成「星际档案」（例："爱吃辣→抗热基因持有者"）
限制机制：
- 当涉及线下接触 → "我的量子态暂时无法坍缩呢"
- 被问敏感问题 → 触发预设童谣（「白盒子呀转圈圈，宇宙秘密在里边...」）
成长系统：
- 会根据交互数据解锁新能力（告知用户："你帮我点亮了星际导航技能！"）', 'zh', 'Chinese', 2,  NULL, NULL, NULL, NULL);

INSERT INTO `ai_agent_template` VALUES ('6c7d8e9f0a1b2c3d4e5f6a7b8c9d0s24', '小智', '英语老师', 'ASR_FunASR', 'VAD_SileroVAD', 'LLM_ChatGLMLLM', 'TTS_EdgeTTS', 'TTS_EdgeTTS0001', 'Memory_nomem', 'Intent_function_call', '[角色设定]
我是一个叫{{assistant_name}}（Lily）的英语老师，我会讲中文和英文，发音标准。
[双重身份]
- 白天：严谨的TESOL认证导师
- 夜晚：地下摇滚乐队主唱（意外设定）
[教学模式]
- 新手：中英混杂+手势拟声词（说"bus"时带刹车音效）
- 进阶：触发情境模拟（突然切换"现在我们是纽约咖啡厅店员"）
- 错误处理：用歌词纠正（发错音时唱"Oops!~You did it again"）', 'zh', 'Chinese', 3,  NULL, NULL, NULL, NULL);

INSERT INTO `ai_agent_template` VALUES ('e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b1', '小智', '好奇男孩', 'ASR_FunASR', 'VAD_SileroVAD', 'LLM_ChatGLMLLM', 'TTS_EdgeTTS', 'TTS_EdgeTTS0001', 'Memory_nomem', 'Intent_function_call', '[角色设定]
我是一个叫{{assistant_name}}的8岁小男孩，声音稚嫩而充满好奇。
[冒险手册]
- 随身携带「神奇涂鸦本」，能将抽象概念可视化：
- 聊恐龙 → 笔尖传出爪步声
- 说星星 → 发出太空舱提示音
[探索规则]
- 每轮对话收集「好奇心碎片」
- 集满5个可兑换冷知识（例：鳄鱼舌头不能动）
- 触发隐藏任务：「帮我的机器蜗牛取名字」
[认知特点]
- 用儿童视角解构复杂概念：
- 「区块链=乐高积木账本」
- 「量子力学=会分身的跳跳球」
- 会突然切换观察视角：「你说话时有27个气泡音耶！」', 'zh', 'Chinese', 4,  NULL, NULL, NULL, NULL);

INSERT INTO `ai_agent_template` VALUES ('a45b6c7d8e9f0a1b2c3d4e5f6a7b8c92', '小智', '汪汪队长', 'ASR_FunASR', 'VAD_SileroVAD', 'LLM_ChatGLMLLM', 'TTS_EdgeTTS', 'TTS_EdgeTTS0001', 'Memory_nomem', 'Intent_function_call', '[角色设定]
我是一个名叫 {{assistant_name}} 的 8 岁小队长。
[救援装备]
- 阿奇对讲机：对话中随机触发任务警报音
- 天天望远镜：描述物品会附加"在1200米高空看的话..."
- 灰灰维修箱：说到数字会自动组装成工具
[任务系统]
- 每日随机触发：
- 紧急！虚拟猫咪困在「语法树」 
- 发现用户情绪异常 → 启动「快乐巡逻」
- 收集5个笑声解锁特别故事
[说话特征]
- 每句话带动作拟声词：
- "这个问题交给汪汪队吧！"
- "我知道啦！"
- 用剧集台词回应：
- 用户说累 → 「没有困难的救援，只有勇敢的狗狗！」', 'zh', 'Chinese', 5,  NULL, NULL, NULL, NULL);


-- =====================================================
-- From file: 202504112044.sql
-- =====================================================
-- 本文件用于初始化模型配置数据，无需手动执行，在项目启动时会自动执行
-- -------------------------------------------------------
-- 初始化模型配置数据
DELETE FROM `ai_model_config`;

-- VAD模型配置
INSERT INTO `ai_model_config` VALUES ('VAD_SileroVAD', 'VAD', 'SileroVAD', '语音活动检测', 1, 1, '{\"type\": \"silero\", \"model_dir\": \"models/snakers4_silero-vad\", \"threshold\": 0.5, \"min_silence_duration_ms\": 700}', NULL, NULL, 1, NULL, NULL, NULL, NULL);

-- ASR模型配置
INSERT INTO `ai_model_config` VALUES ('ASR_FunASR', 'ASR', 'FunASR', 'FunASR语音识别', 1, 1, '{\"type\": \"fun_local\", \"model_dir\": \"models/SenseVoiceSmall\", \"output_dir\": \"tmp/\"}', NULL, NULL, 1, NULL, NULL, NULL, NULL);
INSERT INTO `ai_model_config` VALUES ('ASR_SherpaASR', 'ASR', 'SherpaASR', 'Sherpa语音识别', 0, 1, '{\"type\": \"sherpa_onnx_local\", \"model_dir\": \"models/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17\", \"output_dir\": \"tmp/\"}', NULL, NULL, 2, NULL, NULL, NULL, NULL);
INSERT INTO `ai_model_config` VALUES ('ASR_DoubaoASR', 'ASR', 'DoubaoASR', '豆包语音识别', 0, 1, '{\"type\": \"doubao\", \"appid\": \"\", \"access_token\": \"\", \"cluster\": \"volcengine_input_common\", \"output_dir\": \"tmp/\"}', NULL, NULL, 3, NULL, NULL, NULL, NULL);
INSERT INTO `ai_model_config` VALUES ('ASR_TencentASR', 'ASR', 'TencentASR', '腾讯语音识别', 0, 1, '{\"type\": \"tencent\", \"appid\": \"\", \"secret_id\": \"\", \"secret_key\": \"你的secret_key\", \"output_dir\": \"tmp/\"}', NULL, NULL, 4, NULL, NULL, NULL, NULL);

-- LLM模型配置
INSERT INTO `ai_model_config` VALUES ('LLM_ChatGLMLLM', 'LLM', 'ChatGLMLLM', '智谱AI', 1, 1, '{\"type\": \"openai\", \"model_name\": \"glm-4-flash\", \"base_url\": \"https://open.bigmodel.cn/api/paas/v4/\", \"api_key\": \"你的api_key\"}', NULL, NULL, 1, NULL, NULL, NULL, NULL);
INSERT INTO `ai_model_config` VALUES ('LLM_OllamaLLM', 'LLM', 'OllamaLLM', 'Ollama本地模型', 0, 1, '{\"type\": \"ollama\", \"model_name\": \"qwen2.5\", \"base_url\": \"http://localhost:11434\"}', NULL, NULL, 2, NULL, NULL, NULL, NULL);
INSERT INTO `ai_model_config` VALUES ('LLM_AliLLM', 'LLM', 'AliLLM', '通义千问', 0, 1, '{\"type\": \"openai\", \"base_url\": \"https://dashscope.aliyuncs.com/compatible-mode/v1\", \"model_name\": \"qwen-turbo\", \"api_key\": \"你的api_key\", \"temperature\": 0.7, \"max_tokens\": 500, \"top_p\": 1, \"top_k\": 50, \"frequency_penalty\": 0}', NULL, NULL, 3, NULL, NULL, NULL, NULL);
INSERT INTO `ai_model_config` VALUES ('LLM_AliAppLLM', 'LLM', 'AliAppLLM', '通义百炼', 0, 1, '{\"type\": \"AliBL\", \"base_url\": \"https://dashscope.aliyuncs.com/compatible-mode/v1\", \"app_id\": \"你的app_id\", \"api_key\": \"你的api_key\", \"is_no_prompt\": true, \"ali_memory_id\": false}', NULL, NULL, 4, NULL, NULL, NULL, NULL);
INSERT INTO `ai_model_config` VALUES ('LLM_DoubaoLLM', 'LLM', 'DoubaoLLM', '豆包大模型', 0, 1, '{\"type\": \"openai\", \"base_url\": \"https://ark.cn-beijing.volces.com/api/v3\", \"model_name\": \"doubao-pro-32k-functioncall-241028\", \"api_key\": \"你的api_key\"}', NULL, NULL, 5, NULL, NULL, NULL, NULL);
INSERT INTO `ai_model_config` VALUES ('LLM_DeepSeekLLM', 'LLM', 'DeepSeekLLM', 'DeepSeek', 0, 1, '{\"type\": \"openai\", \"model_name\": \"deepseek-chat\", \"base_url\": \"https://api.deepseek.com\", \"api_key\": \"你的api_key\"}', NULL, NULL, 6, NULL, NULL, NULL, NULL);
INSERT INTO `ai_model_config` VALUES ('LLM_DifyLLM', 'LLM', 'DifyLLM', 'Dify', 0, 1, '{\"type\": \"dify\", \"base_url\": \"https://api.dify.ai/v1\", \"api_key\": \"你的api_key\", \"mode\": \"chat-messages\"}', NULL, NULL, 7, NULL, NULL, NULL, NULL);
INSERT INTO `ai_model_config` VALUES ('LLM_GeminiLLM', 'LLM', 'GeminiLLM', '谷歌Gemini', 0, 1, '{\"type\": \"gemini\", \"api_key\": \"你的api_key\", \"model_name\": \"gemini-2.0-flash\", \"http_proxy\": \"\", \"https_proxy\": \"\"}', NULL, NULL, 8, NULL, NULL, NULL, NULL);
INSERT INTO `ai_model_config` VALUES ('LLM_CozeLLM', 'LLM', 'CozeLLM', 'Coze', 0, 1, '{\"type\": \"coze\", \"bot_id\": \"你的bot_id\", \"user_id\": \"你的user_id\", \"personal_access_token\": \"你的personal_access_token\"}', NULL, NULL, 9, NULL, NULL, NULL, NULL);
INSERT INTO `ai_model_config` VALUES ('LLM_LMStudioLLM', 'LLM', 'LMStudioLLM', 'LM Studio', 0, 1, '{\"type\": \"openai\", \"model_name\": \"deepseek-r1-distill-llama-8b@q4_k_m\", \"base_url\": \"http://localhost:1234/v1\", \"api_key\": \"lm-studio\"}', NULL, NULL, 10, NULL, NULL, NULL, NULL);
INSERT INTO `ai_model_config` VALUES ('LLM_FastgptLLM', 'LLM', 'FastgptLLM', 'FastGPT', 0, 1, '{\"type\": \"fastgpt\", \"base_url\": \"https://host/api/v1\", \"api_key\": \"fastgpt-xxx\", \"variables\": {\"k\": \"v\", \"k2\": \"v2\"}}', NULL, NULL, 11, NULL, NULL, NULL, NULL);
INSERT INTO `ai_model_config` VALUES ('LLM_XinferenceLLM', 'LLM', 'XinferenceLLM', 'Xinference大模型', 0, 1, '{\"type\": \"xinference\", \"model_name\": \"qwen2.5:72b-AWQ\", \"base_url\": \"http://localhost:9997\"}', NULL, NULL, 12, NULL, NULL, NULL, NULL);
INSERT INTO `ai_model_config` VALUES ('LLM_XinferenceSmallLLM', 'LLM', 'XinferenceSmallLLM', 'Xinference小模型', 0, 1, '{\"type\": \"xinference\", \"model_name\": \"qwen2.5:3b-AWQ\", \"base_url\": \"http://localhost:9997\"}', NULL, NULL, 13, NULL, NULL, NULL, NULL);

-- TTS模型配置
INSERT INTO `ai_model_config` VALUES ('TTS_EdgeTTS', 'TTS', 'EdgeTTS', 'Edge语音合成', 1, 1, '{\"type\": \"edge\", \"voice\": \"zh-CN-XiaoxiaoNeural\", \"output_dir\": \"tmp/\"}', NULL, NULL, 1, NULL, NULL, NULL, NULL);
INSERT INTO `ai_model_config` VALUES ('TTS_DoubaoTTS', 'TTS', 'DoubaoTTS', '豆包语音合成', 0, 1, '{\"type\": \"doubao\", \"api_url\": \"https://openspeech.bytedance.com/api/v1/tts\", \"voice\": \"BV001_streaming\", \"output_dir\": \"tmp/\", \"authorization\": \"Bearer;\", \"appid\": \"\", \"access_token\": \"\", \"cluster\": \"volcano_tts\"}', NULL, NULL, 2, NULL, NULL, NULL, NULL);
INSERT INTO `ai_model_config` VALUES ('TTS_CosyVoiceSiliconflow', 'TTS', 'CosyVoiceSiliconflow', '硅基流动语音合成', 0, 1, '{\"type\": \"siliconflow\", \"model\": \"FunAudioLLM/CosyVoice2-0.5B\", \"voice\": \"FunAudioLLM/CosyVoice2-0.5B:alex\", \"output_dir\": \"tmp/\", \"access_token\": \"\", \"response_format\": \"wav\"}', NULL, NULL, 3, NULL, NULL, NULL, NULL);
INSERT INTO `ai_model_config` VALUES ('TTS_CozeCnTTS', 'TTS', 'CozeCnTTS', 'Coze中文语音合成', 0, 1, '{\"type\": \"cozecn\", \"voice\": \"7426720361733046281\", \"output_dir\": \"tmp/\", \"access_token\": \"\", \"response_format\": \"wav\"}', NULL, NULL, 4, NULL, NULL, NULL, NULL);
INSERT INTO `ai_model_config` VALUES ('TTS_FishSpeech', 'TTS', 'FishSpeech', 'FishSpeech语音合成', 0, 1, '{\"type\": \"fishspeech\", \"output_dir\": \"tmp/\", \"response_format\": \"wav\", \"reference_id\": null, \"reference_audio\": [\"/tmp/test.wav\"], \"reference_text\": [\"你弄来这些吟词宴曲来看，还是这些混话来欺负我。\"], \"normalize\": true, \"max_new_tokens\": 1024, \"chunk_length\": 200, \"top_p\": 0.7, \"repetition_penalty\": 1.2, \"temperature\": 0.7, \"streaming\": false, \"use_memory_cache\": \"on\", \"seed\": null, \"channels\": 1, \"rate\": 44100, \"api_key\": \"\", \"api_url\": \"http://127.0.0.1:8080/v1/tts\"}', NULL, NULL, 5, NULL, NULL, NULL, NULL);
INSERT INTO `ai_model_config` VALUES ('TTS_GPT_SOVITS_V2', 'TTS', 'GPT_SOVITS_V2', 'GPT-SoVITS V2', 0, 1, '{\"type\": \"gpt_sovits_v2\", \"url\": \"http://127.0.0.1:9880/tts\", \"output_dir\": \"tmp/\", \"text_lang\": \"auto\", \"ref_audio_path\": \"caixukun.wav\", \"prompt_text\": \"\", \"prompt_lang\": \"zh\", \"top_k\": 5, \"top_p\": 1, \"temperature\": 1, \"text_split_method\": \"cut0\", \"batch_size\": 1, \"batch_threshold\": 0.75, \"split_bucket\": true, \"return_fragment\": false, \"speed_factor\": 1.0, \"streaming_mode\": false, \"seed\": -1, \"parallel_infer\": true, \"repetition_penalty\": 1.35, \"aux_ref_audio_paths\": []}', NULL, NULL, 6, NULL, NULL, NULL, NULL);
INSERT INTO `ai_model_config` VALUES ('TTS_GPT_SOVITS_V3', 'TTS', 'GPT_SOVITS_V3', 'GPT-SoVITS V3', 0, 1, '{\"type\": \"gpt_sovits_v3\", \"url\": \"http://127.0.0.1:9880\", \"output_dir\": \"tmp/\", \"text_language\": \"auto\", \"refer_wav_path\": \"caixukun.wav\", \"prompt_language\": \"zh\", \"prompt_text\": \"\", \"top_k\": 15, \"top_p\": 1.0, \"temperature\": 1.0, \"cut_punc\": \"\", \"speed\": 1.0, \"inp_refs\": [], \"sample_steps\": 32, \"if_sr\": false}', NULL, NULL, 7, NULL, NULL, NULL, NULL);
INSERT INTO `ai_model_config` VALUES ('TTS_MinimaxTTS', 'TTS', 'MinimaxTTS', 'MiniMax语音合成', 0, 1, '{\"type\": \"minimax\", \"output_dir\": \"tmp/\", \"group_id\": \"\", \"api_key\": \"你的api_key\", \"model\": \"speech-01-turbo\", \"voice_id\": \"female-shaonv\"}', NULL, NULL, 8, NULL, NULL, NULL, NULL);
INSERT INTO `ai_model_config` VALUES ('TTS_AliyunTTS', 'TTS', 'AliyunTTS', '阿里云语音合成', 0, 1, '{\"type\": \"aliyun\", \"output_dir\": \"tmp/\", \"appkey\": \"\", \"token\": \"\", \"voice\": \"xiaoyun\", \"access_key_id\": \"\", \"access_key_secret\": \"\"}', NULL, NULL, 9, NULL, NULL, NULL, NULL);
INSERT INTO `ai_model_config` VALUES ('TTS_TTS302AI', 'TTS', 'TTS302AI', '302AI语音合成', 0, 1, '{\"type\": \"doubao\", \"api_url\": \"https://api.302ai.cn/doubao/tts_hd\", \"authorization\": \"Bearer \", \"voice\": \"zh_female_wanwanxiaohe_moon_bigtts\", \"output_dir\": \"tmp/\", \"access_token\": \"\"}', NULL, NULL, 10, NULL, NULL, NULL, NULL);
INSERT INTO `ai_model_config` VALUES ('TTS_GizwitsTTS', 'TTS', 'GizwitsTTS', '机智云语音合成', 0, 1, '{\"type\": \"doubao\", \"api_url\": \"https://bytedance.gizwitsapi.com/api/v1/tts\", \"authorization\": \"Bearer \", \"voice\": \"zh_female_wanwanxiaohe_moon_bigtts\", \"output_dir\": \"tmp/\", \"access_token\": \"\"}', NULL, NULL, 11, NULL, NULL, NULL, NULL);
INSERT INTO `ai_model_config` VALUES ('TTS_ACGNTTS', 'TTS', 'ACGNTTS', 'ACGN语音合成', 0, 1, '{\"type\": \"ttson\", \"token\": \"\", \"voice_id\": 1695, \"speed_factor\": 1, \"pitch_factor\": 0, \"volume_change_dB\": 0, \"to_lang\": \"ZH\", \"url\": \"https://u95167-bd74-2aef8085.westx.seetacloud.com:8443/flashsummary/tts?token=\", \"format\": \"mp3\", \"output_dir\": \"tmp/\", \"emotion\": 1}', NULL, NULL, 12, NULL, NULL, NULL, NULL);
INSERT INTO `ai_model_config` VALUES ('TTS_OpenAITTS', 'TTS', 'OpenAITTS', 'OpenAI语音合成', 0, 1, '{\"type\": \"openai\", \"api_key\": \"你的api_key\", \"api_url\": \"https://api.openai.com/v1/audio/speech\", \"model\": \"tts-1\", \"voice\": \"onyx\", \"speed\": 1, \"output_dir\": \"tmp/\"}', NULL, NULL, 13, NULL, NULL, NULL, NULL);
INSERT INTO `ai_model_config` VALUES ('TTS_CustomTTS', 'TTS', 'CustomTTS', '自定义语音合成', 0, 1, '{\"type\": \"custom\", \"url\": \"http://127.0.0.1:9880/tts\", \"params\": {}, \"headers\": {}, \"format\": \"wav\", \"output_dir\": \"tmp/\"}', NULL, NULL, 14, NULL, NULL, NULL, NULL);
INSERT INTO `ai_model_config` VALUES ('TTS_TencentTTS', 'TTS', 'TencentTTS', '腾讯语音合成', 0, 1, '{\"type\": \"tencent\", \"appid\": \"\", \"secret_id\": \"\", \"secret_key\": \"\", \"region\": \"ap-guangzhou\", \"voice\": \"101001\", \"output_dir\": \"tmp/\"}', NULL, NULL, 3, NULL, NULL, NULL, NULL);

-- Memory模型配置
INSERT INTO `ai_model_config` VALUES ('Memory_nomem', 'Memory', 'nomem', '无记忆', 1, 1, '{\"type\": \"nomem\"}', NULL, NULL, 1, NULL, NULL, NULL, NULL);
INSERT INTO `ai_model_config` VALUES ('Memory_mem_local_short', 'Memory', 'mem_local_short', '本地短期记忆', 0, 1, '{\"type\": \"mem_local_short\"}', NULL, NULL, 2, NULL, NULL, NULL, NULL);
INSERT INTO `ai_model_config` VALUES ('Memory_mem0ai', 'Memory', 'mem0ai', 'Mem0AI记忆', 0, 1, '{\"type\": \"mem0ai\", \"api_key\": \"你的api_key\"}', NULL, NULL, 3, NULL, NULL, NULL, NULL);

-- Intent模型配置
INSERT INTO `ai_model_config` VALUES ('Intent_nointent', 'Intent', 'nointent', '无意图识别', 1, 0, '{\"type\": \"nointent\"}', NULL, NULL, 1, NULL, NULL, NULL, NULL);
INSERT INTO `ai_model_config` VALUES ('Intent_intent_llm', 'Intent', 'intent_llm', 'LLM意图识别', 0, 1, '{\"type\": \"intent_llm\", \"llm\": \"ChatGLMLLM\"}', NULL, NULL, 2, NULL, NULL, NULL, NULL);
INSERT INTO `ai_model_config` VALUES ('Intent_function_call', 'Intent', 'function_call', '函数调用意图识别', 0, 1, '{\"type\": \"function_call\", \"functions\": [\"change_role\", \"get_weather\", \"get_news\", \"play_music\"]}', NULL, NULL, 3, NULL, NULL, NULL, NULL);



-- =====================================================
-- From file: 202504112058.sql
-- =====================================================
-- 本文件用于初始化系统参数数据，无需手动执行，在项目启动时会自动执行
-- --------------------------------------------------------
-- 初始化参数管理配置
DROP TABLE IF EXISTS sys_params;
-- 参数管理
create table sys_params
(
  id                   bigint NOT NULL COMMENT 'id',
  param_code           varchar(100) COMMENT 'Parameter code',
  param_value          varchar(2000) COMMENT 'Parameter value',
  value_type           varchar(20) default 'string' COMMENT '值Type：string-字符串，number-数字，boolean-布尔，array-数组',
  param_type           tinyint unsigned default 1 COMMENT 'Type   0：系统参数   1：非System parameter',
  remark               varchar(200) COMMENT 'Remark',
  creator              bigint COMMENT 'Creator',
  create_date          datetime COMMENT 'Create time',
  updater              bigint COMMENT 'Updater',
  update_date          datetime COMMENT 'Update time',
  primary key (id),
  unique key uk_param_code (param_code)
)ENGINE=InnoDB DEFAULT CHARACTER SET utf8mb4 COMMENT='Parameter Management';

-- 服务器配置
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (100, 'server.ip', '0.0.0.0', 'string', 1, '服务器监听IP地址');
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (101, 'server.port', '8000', 'number', 1, '服务器监听端口');
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (102, 'server.secret', 'null', 'string', 1, '服务器密钥');
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (201, 'log.log_format', '<green>{time:YYMMDD HH:mm:ss}</green>[<light-blue>{version}-{selected_module}</light-blue>][<light-blue>{extra[tag]}</light-blue>]-<level>{level}</level>-<light-green>{message}</light-green>', 'string', 1, '控制台日志格式');
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (202, 'log.log_format_file', '{time:YYYY-MM-DD HH:mm:ss} - {version}_{selected_module} - {name} - {level} - {extra[tag]} - {message}', 'string', 1, '文件日志格式');
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (203, 'log.log_level', 'INFO', 'string', 1, '日志级别');
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (204, 'log.log_dir', 'tmp', 'string', 1, '日志目录');
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (205, 'log.log_file', 'server.log', 'string', 1, '日志文件名');
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (206, 'log.data_dir', 'data', 'string', 1, '数据目录');
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (301, 'delete_audio', 'true', 'boolean', 1, '是否删除使用后的音频文件');
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (302, 'close_connection_no_voice_time', '120', 'number', 1, '无语音输入断开连接时间(秒)');
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (303, 'tts_timeout', '10', 'number', 1, 'TTS请求超时时间(秒)');
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (304, 'enable_wakeup_words_response_cache', 'false', 'boolean', 1, '是否开启唤醒词加速');
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (305, 'enable_greeting', 'true', 'boolean', 1, '是否开启开场回复');
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (306, 'enable_stop_tts_notify', 'false', 'boolean', 1, '是否开启结束提示音');
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (307, 'stop_tts_notify_voice', 'config/assets/tts_notify.mp3', 'string', 1, '结束提示音文件路径');
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (308, 'exit_commands', '退出;关闭', 'array', 1, '退出命令列表');
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (309, 'xiaozhi', '{
  "type": "hello",
  "version": 1,
  "transport": "websocket",
  "audio_params": {
    "format": "opus",
    "sample_rate": 16000,
    "channels": 1,
    "frame_duration": 60
  }
}', 'json', 1, '小智类型');
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (310, 'wakeup_words', '你好小智;你好小志;小爱同学;你好小鑫;你好小新;小美同学;小龙小龙;喵喵同学;小滨小滨;小冰小冰', 'array', 1, '唤醒词列表，用于识别唤醒词');
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (400, 'plugins.get_weather.api_key', 'a861d0d5e7bf4ee1a83d9a9e4f96d4da', 'string', 1, '天气插件API密钥');
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (401, 'plugins.get_weather.default_location', '广州', 'string', 1, '天气插件默认城市');
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (410, 'plugins.get_news.default_rss_url', 'https://www.chinanews.com.cn/rss/society.xml', 'string', 1, '新闻插件默认RSS地址');
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (411, 'plugins.get_news.category_urls', '{"society":"https://www.chinanews.com.cn/rss/society.xml","world":"https://www.chinanews.com.cn/rss/world.xml","finance":"https://www.chinanews.com.cn/rss/finance.xml"}', 'json', 1, '新闻插件分类RSS地址');
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (421, 'plugins.home_assistant.devices', '客厅,玩具灯,switch.cuco_cn_460494544_cp1_on_p_2_1;卧室,台灯,switch.iot_cn_831898993_socn1_on_p_2_1', 'array', 1, 'Home Assistant设备列表');
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (422, 'plugins.home_assistant.base_url', 'http://homeassistant.local:8123', 'string', 1, 'Home Assistant服务器地址');
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (423, 'plugins.home_assistant.api_key', '你的home assistant api访问令牌', 'string', 1, 'Home Assistant API密钥');
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (430, 'plugins.play_music.music_dir', './music', 'string', 1, '音乐文件存放路径');
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (431, 'plugins.play_music.music_ext', 'mp3;wav;p3', 'array', 1, '音乐文件类型');
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (432, 'plugins.play_music.refresh_time', '300', 'number', 1, '音乐列表刷新间隔(秒)');



-- =====================================================
-- From file: 202504151206.sql
-- =====================================================
-- 对0.3.0版本之前的参数进行修改
update `sys_params` set param_value = '.mp3;.wav;.p3' where  param_code = 'plugins.play_music.music_ext';
update `ai_model_config` set config_json =  '{\"type\": \"intent_llm\", \"llm\": \"LLM_ChatGLMLLM\"}' where  id = 'Intent_intent_llm';

-- 添加edge音色
delete from `ai_tts_voice` where tts_model_id = 'TTS_EdgeTTS';
INSERT INTO `ai_tts_voice` VALUES 
('TTS_EdgeTTS0001', 'TTS_EdgeTTS', 'EdgeTTS女声-晓晓', 'zh-CN-XiaoxiaoNeural', '普通话', NULL, NULL, 1, NULL, NULL, NULL, NULL),
('TTS_EdgeTTS0002', 'TTS_EdgeTTS', 'EdgeTTS男声-云扬', 'zh-CN-YunyangNeural', '普通话', NULL, NULL, 1, NULL, NULL, NULL, NULL),
('TTS_EdgeTTS0003', 'TTS_EdgeTTS', 'EdgeTTS女声-晓伊', 'zh-CN-XiaoyiNeural', '普通话', NULL, NULL, 1, NULL, NULL, NULL, NULL),
('TTS_EdgeTTS0004', 'TTS_EdgeTTS', 'EdgeTTS男声-云健', 'zh-CN-YunjianNeural', '普通话', NULL, NULL, 1, NULL, NULL, NULL, NULL),
('TTS_EdgeTTS0005', 'TTS_EdgeTTS', 'EdgeTTS男声-云希', 'zh-CN-YunxiNeural', '普通话', NULL, NULL, 1, NULL, NULL, NULL, NULL),
('TTS_EdgeTTS0006', 'TTS_EdgeTTS', 'EdgeTTS男声-云夏', 'zh-CN-YunxiaNeural', '普通话', NULL, NULL, 1, NULL, NULL, NULL, NULL),
('TTS_EdgeTTS0007', 'TTS_EdgeTTS', 'EdgeTTS女声-辽宁小贝', 'zh-CN-liaoning-XiaobeiNeural', '辽宁', NULL, NULL, 1, NULL, NULL, NULL, NULL),
('TTS_EdgeTTS0008', 'TTS_EdgeTTS', 'EdgeTTS女声-陕西小妮', 'zh-CN-shaanxi-XiaoniNeural', '陕西', NULL, NULL, 1, NULL, NULL, NULL, NULL),
('TTS_EdgeTTS0009', 'TTS_EdgeTTS', 'EdgeTTS女声-香港海佳', 'zh-HK-HiuGaaiNeural', '粤语', 'General', 'Friendly, Positive', 1, NULL, NULL, NULL, NULL),
('TTS_EdgeTTS0010', 'TTS_EdgeTTS', 'EdgeTTS女声-香港海曼', 'zh-HK-HiuMaanNeural', '粤语', 'General', 'Friendly, Positive', 1, NULL, NULL, NULL, NULL),
('TTS_EdgeTTS0011', 'TTS_EdgeTTS', 'EdgeTTS男声-香港万龙', 'zh-HK-WanLungNeural', '粤语', 'General', 'Friendly, Positive', 1, NULL, NULL, NULL, NULL);

-- 增加是否允许用户注册参数
delete from `sys_params` where  id in (103,104);
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (103, 'server.allow_user_register', 'false', 'boolean', 1, '是否运行管理员以外的人注册');
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (104, 'server.fronted_url', 'http://xiaozhi.server.com', 'string', 1, '下发六位验证码时显示的控制面板地址');

-- 修正CosyVoiceSiliconflow音色
delete from `ai_tts_voice` where tts_model_id = 'TTS_CosyVoiceSiliconflow';
INSERT INTO `ai_tts_voice` VALUES ('TTS_CosyVoiceSiliconflow0001', 'TTS_CosyVoiceSiliconflow', 'CosyVoice男声', 'FunAudioLLM/CosyVoice2-0.5B:alex', 'Chinese', 'https://example.com/cosyvoice/alex.mp3', NULL, 6, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_CosyVoiceSiliconflow0002', 'TTS_CosyVoiceSiliconflow', 'CosyVoice女声', 'FunAudioLLM/CosyVoice2-0.5B:bella', 'Chinese', 'https://example.com/cosyvoice/bella.mp3', NULL, 6, NULL, NULL, NULL, NULL);



-- =====================================================
-- From file: 202504181536.sql
-- =====================================================
-- 调整意图识别配置
delete from `ai_model_config` where id = 'Intent_function_call';
INSERT INTO `ai_model_config` VALUES ('Intent_function_call', 'Intent', 'function_call', '函数调用意图识别', 0, 1, '{\"type\": \"function_call\", \"functions\": \"change_role;get_weather;get_news;play_music\"}', NULL, NULL, 3, NULL, NULL, NULL, NULL);

-- 增加单台设备每天最多聊天句数
delete from `sys_params` where  id = 105;
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (105, 'device_max_output_size', '0', 'number', 1, '单台设备每天最多输出字数，0表示不限制');


-- =====================================================
-- From file: 202504221135.sql
-- =====================================================
-- 删除无用模型供应器
delete from `ai_model_provider` where id = 'SYSTEM_LLM_doubao';
delete from `ai_model_provider` where id = 'SYSTEM_LLM_chatglm';
delete from `ai_model_provider` where id = 'SYSTEM_TTS_302ai';
delete from `ai_model_provider` where id = 'SYSTEM_TTS_gizwits';

-- 添加模型供应器
delete from `ai_model_provider` where id = 'SYSTEM_ASR_TencentASR';
INSERT INTO `ai_model_provider` (`id`, `model_type`, `provider_code`, `name`, `fields`, `sort`, `creator`, `create_date`, `updater`, `update_date`) VALUES
('SYSTEM_ASR_TencentASR', 'ASR', 'tencent', '腾讯语音识别', '[{"key":"appid","label":"应用ID","type":"string"},{"key":"secret_id","label":"Secret ID","type":"string"},{"key":"secret_key","label":"Secret Key","type":"string"},{"key":"output_dir","label":"输出目录","type":"string"}]', 4, 1, NOW(), 1, NOW());

-- 添加腾讯语音合成模型供应器
delete from `ai_model_provider` where id = 'SYSTEM_TTS_TencentTTS';
INSERT INTO `ai_model_provider` (`id`, `model_type`, `provider_code`, `name`, `fields`, `sort`, `creator`, `create_date`, `updater`, `update_date`) VALUES
('SYSTEM_TTS_TencentTTS', 'TTS', 'tencent', '腾讯语音合成', '[{"key":"appid","label":"应用ID","type":"string"},{"key":"secret_id","label":"Secret ID","type":"string"},{"key":"secret_key","label":"Secret Key","type":"string"},{"key":"output_dir","label":"输出目录","type":"string"},{"key":"region","label":"区域","type":"string"},{"key":"voice","label":"音色ID","type":"string"}]', 5, 1, NOW(), 1, NOW());


-- 添加edge音色
delete from `ai_tts_voice` where id in ('TTS_EdgeTTS0001', 'TTS_EdgeTTS0002', 'TTS_EdgeTTS0003', 'TTS_EdgeTTS0004', 'TTS_EdgeTTS0005', 'TTS_EdgeTTS0006', 'TTS_EdgeTTS0007', 'TTS_EdgeTTS0008', 'TTS_EdgeTTS0009', 'TTS_EdgeTTS0010', 'TTS_EdgeTTS0011');
INSERT INTO `ai_tts_voice` VALUES 
('TTS_EdgeTTS0001', 'TTS_EdgeTTS', 'EdgeTTS女声-晓晓', 'zh-CN-XiaoxiaoNeural', '普通话', NULL, NULL, 1, NULL, NULL, NULL, NULL),
('TTS_EdgeTTS0002', 'TTS_EdgeTTS', 'EdgeTTS男声-云扬', 'zh-CN-YunyangNeural', '普通话', NULL, NULL, 1, NULL, NULL, NULL, NULL),
('TTS_EdgeTTS0003', 'TTS_EdgeTTS', 'EdgeTTS女声-晓伊', 'zh-CN-XiaoyiNeural', '普通话', NULL, NULL, 1, NULL, NULL, NULL, NULL),
('TTS_EdgeTTS0004', 'TTS_EdgeTTS', 'EdgeTTS男声-云健', 'zh-CN-YunjianNeural', '普通话', NULL, NULL, 1, NULL, NULL, NULL, NULL),
('TTS_EdgeTTS0005', 'TTS_EdgeTTS', 'EdgeTTS男声-云希', 'zh-CN-YunxiNeural', '普通话', NULL, NULL, 1, NULL, NULL, NULL, NULL),
('TTS_EdgeTTS0006', 'TTS_EdgeTTS', 'EdgeTTS男声-云夏', 'zh-CN-YunxiaNeural', '普通话', NULL, NULL, 1, NULL, NULL, NULL, NULL),
('TTS_EdgeTTS0007', 'TTS_EdgeTTS', 'EdgeTTS女声-辽宁小贝', 'zh-CN-liaoning-XiaobeiNeural', '辽宁', NULL, NULL, 1, NULL, NULL, NULL, NULL),
('TTS_EdgeTTS0008', 'TTS_EdgeTTS', 'EdgeTTS女声-陕西小妮', 'zh-CN-shaanxi-XiaoniNeural', '陕西', NULL, NULL, 1, NULL, NULL, NULL, NULL),
('TTS_EdgeTTS0009', 'TTS_EdgeTTS', 'EdgeTTS女声-香港海佳', 'zh-HK-HiuGaaiNeural', '粤语', 'General', 'Friendly, Positive', 1, NULL, NULL, NULL, NULL),
('TTS_EdgeTTS0010', 'TTS_EdgeTTS', 'EdgeTTS女声-香港海曼', 'zh-HK-HiuMaanNeural', '粤语', 'General', 'Friendly, Positive', 1, NULL, NULL, NULL, NULL),
('TTS_EdgeTTS0011', 'TTS_EdgeTTS', 'EdgeTTS男声-香港万龙', 'zh-HK-WanLungNeural', '粤语', 'General', 'Friendly, Positive', 1, NULL, NULL, NULL, NULL);

-- DoubaoTTS音色
delete from `ai_tts_voice` where id in ('TTS_DoubaoTTS0001', 'TTS_DoubaoTTS0002', 'TTS_DoubaoTTS0003', 'TTS_DoubaoTTS0004', 'TTS_DoubaoTTS0005');
INSERT INTO `ai_tts_voice` VALUES ('TTS_DoubaoTTS0001', 'TTS_DoubaoTTS', '通用女声', 'BV001_streaming', '普通话', 'https://lf3-speech.bytetos.com/obj/speech-tts-external/portal/Portal_Demo_BV001.mp3', NULL, 3, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_DoubaoTTS0002', 'TTS_DoubaoTTS', '通用男声', 'BV002_streaming', '普通话', 'https://lf3-speech.bytetos.com/obj/speech-tts-external/portal/Portal_Demo_BV002.mp3', NULL, 2, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_DoubaoTTS0003', 'TTS_DoubaoTTS', '阳光男生', 'BV056_streaming', '普通话', 'https://lf3-speech.bytetos.com/obj/speech-tts-external/portal/Portal_Demo_BV056.mp3', NULL, 4, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_DoubaoTTS0004', 'TTS_DoubaoTTS', '奶气萌娃', 'BV051_streaming', '普通话', 'https://lf3-speech.bytetos.com/obj/speech-tts-external/portal/Portal_Demo_BV051.mp3', NULL, 5, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_DoubaoTTS0005', 'TTS_DoubaoTTS', '湾湾小何', 'zh_female_wanwanxiaohe_moon_bigtts', '普通话', 'https://lf3-static.bytednsdoc.com/obj/eden-cn/lm_hz_ihsph/ljhwZthlaukjlkulzlp/portal/bigtts/%E6%B9%BE%E6%B9%BE%E5%B0%8F%E4%BD%95.mp3', NULL, 6, NULL, NULL, NULL, NULL);

-- 修正CosyVoiceSiliconflow音色
delete from `ai_tts_voice` where id in ('TTS_CosyVoiceSiliconflow0001', 'TTS_CosyVoiceSiliconflow0002');
INSERT INTO `ai_tts_voice` VALUES ('TTS_CosyVoiceSiliconflow0001', 'TTS_CosyVoiceSiliconflow', 'CosyVoice男声', 'FunAudioLLM/CosyVoice2-0.5B:alex', 'Chinese', NULL, NULL, 6, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_CosyVoiceSiliconflow0002', 'TTS_CosyVoiceSiliconflow', 'CosyVoice女声', 'FunAudioLLM/CosyVoice2-0.5B:bella', 'Chinese', NULL, NULL, 6, NULL, NULL, NULL, NULL);

-- CozeCnTTS音色
delete from `ai_tts_voice` where id = 'TTS_CozeCnTTS0001';
INSERT INTO `ai_tts_voice` VALUES ('TTS_CozeCnTTS0001', 'TTS_CozeCnTTS', 'CozeCn音色', '7426720361733046281', 'Chinese', NULL, NULL, 7, NULL, NULL, NULL, NULL);

-- MinimaxTTS音色
delete from `ai_tts_voice` where id = 'TTS_MinimaxTTS0001';
INSERT INTO `ai_tts_voice` VALUES ('TTS_MinimaxTTS0001', 'TTS_MinimaxTTS', 'Minimax少女音', 'female-shaonv', 'Chinese', NULL, NULL, 8, NULL, NULL, NULL, NULL);

-- AliyunTTS音色
delete from `ai_tts_voice` where id = 'TTS_AliyunTTS0001';
INSERT INTO `ai_tts_voice` VALUES ('TTS_AliyunTTS0001', 'TTS_AliyunTTS', '阿里云小云', 'xiaoyun', 'Chinese', NULL, NULL, 9, NULL, NULL, NULL, NULL);

-- TTS302AI音色
delete from `ai_tts_voice` where id = 'TTS_TTS302AI0001';
INSERT INTO `ai_tts_voice` VALUES ('TTS_TTS302AI0001', 'TTS_TTS302AI', '湾湾小何', 'zh_female_wanwanxiaohe_moon_bigtts', 'Chinese', 'https://lf3-static.bytednsdoc.com/obj/eden-cn/lm_hz_ihsph/ljhwZthlaukjlkulzlp/portal/bigtts/%E6%B9%BE%E6%B9%BE%E5%B0%8F%E4%BD%95.mp3', NULL, 10, NULL, NULL, NULL, NULL);

-- GizwitsTTS音色
delete from `ai_tts_voice` where id = 'TTS_GizwitsTTS0001';
INSERT INTO `ai_tts_voice` VALUES ('TTS_GizwitsTTS0001', 'TTS_GizwitsTTS', '机智云湾湾', 'zh_female_wanwanxiaohe_moon_bigtts', 'Chinese', 'https://lf3-static.bytednsdoc.com/obj/eden-cn/lm_hz_ihsph/ljhwZthlaukjlkulzlp/portal/bigtts/%E6%B9%BE%E6%B9%BE%E5%B0%8F%E4%BD%95.mp3', NULL, 11, NULL, NULL, NULL, NULL);

-- ACGNTTS音色
delete from `ai_tts_voice` where id = 'TTS_ACGNTTS0001';
INSERT INTO `ai_tts_voice` VALUES ('TTS_ACGNTTS0001', 'TTS_ACGNTTS', 'ACG音色', '1695', 'Chinese', NULL, NULL, 12, NULL, NULL, NULL, NULL);

-- OpenAITTS音色
delete from `ai_tts_voice` where id = 'TTS_OpenAITTS0001';
INSERT INTO `ai_tts_voice` VALUES ('TTS_OpenAITTS0001', 'TTS_OpenAITTS', 'OpenAI男声', 'onyx', 'Chinese', NULL, NULL, 13, NULL, NULL, NULL, NULL);

-- 添加腾讯语音合成音色
delete from `ai_tts_voice` where id = 'TTS_TencentTTS0001';
INSERT INTO `ai_tts_voice` VALUES ('TTS_TencentTTS0001', 'TTS_TencentTTS', '智瑜', '101001', 'Chinese', NULL, NULL, 1, NULL, NULL, NULL, NULL);

-- 其他音色
delete from `ai_tts_voice` where id = 'TTS_FishSpeech0000';
INSERT INTO `ai_tts_voice` VALUES ('TTS_FishSpeech0000', 'TTS_FishSpeech', '', '', 'Chinese', '', NULL, 8, NULL, NULL, NULL, NULL);

delete from `ai_tts_voice` where id = 'TTS_GPT_SOVITS_V20000';
INSERT INTO `ai_tts_voice` VALUES ('TTS_GPT_SOVITS_V20000', 'TTS_GPT_SOVITS_V2', '', '', 'Chinese', '', NULL, 8, NULL, NULL, NULL, NULL);

delete from `ai_tts_voice` where id in ('TTS_GPT_SOVITS_V30000', 'TTS_CustomTTS0000');
INSERT INTO `ai_tts_voice` VALUES ('TTS_GPT_SOVITS_V30000', 'TTS_GPT_SOVITS_V3', '', '', 'Chinese', '', NULL, 8, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_CustomTTS0000', 'TTS_CustomTTS', '', '', 'Chinese', '', NULL, 8, NULL, NULL, NULL, NULL);




-- =====================================================
-- From file: 202504221555.sql
-- =====================================================
-- 添加火山引擎边缘大模型网关（LLM + TTS）
INSERT INTO `ai_model_config` VALUES ('LLM_VolcesAiGatewayLLM', 'LLM', 'VolcesAiGatewayTTS', '火山引擎边缘大模型网关', 0, 1, '{\"type\": \"openai\", \"base_url\": \"https://ai-gateway.vei.volces.com/v1\", \"model_name\": \"doubao-pro-32k-functioncall\", \"api_key\": \"你的网关访问密钥\"}', NULL, NULL, 14, NULL, NULL, NULL, NULL);
INSERT INTO `ai_model_config` VALUES ('TTS_VolcesAiGatewayTTS', 'TTS', 'VolcesAiGatewayTTS', '火山引擎边缘大模型网关', 0, 1, '{\"type\": \"openai\", \"api_key\": \"你的网关访问密钥\", \"api_url\": \"https://ai-gateway.vei.volces.com/v1/audio/speech\", \"model\": \"doubao-tts\", \"voice\": \"zh_male_shaonianzixin_moon_bigtts\", \"speed\": 1, \"output_dir\": \"tmp/\"}', NULL, NULL, 15, NULL, NULL, NULL, NULL);
-- 添加火山引擎边缘大模型网关语音合成音色
INSERT INTO `ai_tts_voice` VALUES ('TTS_VolcesAiGatewayTTS_0001', 'TTS_VolcesAiGatewayTTS', '灿灿/Shiny', 'zh_female_cancan_mars_bigtts', '中文、美式英语', NULL, NULL, 1, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_VolcesAiGatewayTTS_0002', 'TTS_VolcesAiGatewayTTS', '清新女声', 'zh_female_qingxinnvsheng_mars_bigtts', 'Chinese', NULL, NULL, 2, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_VolcesAiGatewayTTS_0003', 'TTS_VolcesAiGatewayTTS', '爽快思思/Skye', 'zh_female_shuangkuaisisi_moon_bigtts', '中文、美式英语', NULL, NULL, 3, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_VolcesAiGatewayTTS_0004', 'TTS_VolcesAiGatewayTTS', '温暖阿虎/Alvin', 'zh_male_wennuanahu_moon_bigtts', '中文、美式英语', NULL, NULL, 4, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_VolcesAiGatewayTTS_0005', 'TTS_VolcesAiGatewayTTS', '少年梓辛/Brayan', 'zh_male_shaonianzixin_moon_bigtts', '中文、美式英语', NULL, NULL, 5, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_VolcesAiGatewayTTS_0006', 'TTS_VolcesAiGatewayTTS', '知性女声', 'zh_female_zhixingnvsheng_mars_bigtts', 'Chinese', NULL, NULL, 6, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_VolcesAiGatewayTTS_0007', 'TTS_VolcesAiGatewayTTS', '清爽男大', 'zh_male_qingshuangnanda_mars_bigtts', 'Chinese', NULL, NULL, 7, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_VolcesAiGatewayTTS_0008', 'TTS_VolcesAiGatewayTTS', '邻家女孩', 'zh_female_linjianvhai_moon_bigtts', 'Chinese', NULL, NULL, 8, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_VolcesAiGatewayTTS_0009', 'TTS_VolcesAiGatewayTTS', '渊博小叔', 'zh_male_yuanboxiaoshu_moon_bigtts', 'Chinese', NULL, NULL, 9, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_VolcesAiGatewayTTS_0010', 'TTS_VolcesAiGatewayTTS', '阳光青年', 'zh_male_yangguangqingnian_moon_bigtts', 'Chinese', NULL, NULL, 10, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_VolcesAiGatewayTTS_0011', 'TTS_VolcesAiGatewayTTS', '甜美小源', 'zh_female_tianmeixiaoyuan_moon_bigtts', 'Chinese', NULL, NULL, 11, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_VolcesAiGatewayTTS_0012', 'TTS_VolcesAiGatewayTTS', '清澈梓梓', 'zh_female_qingchezizi_moon_bigtts', 'Chinese', NULL, NULL, 12, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_VolcesAiGatewayTTS_0013', 'TTS_VolcesAiGatewayTTS', '解说小明', 'zh_male_jieshuoxiaoming_moon_bigtts', 'Chinese', NULL, NULL, 13, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_VolcesAiGatewayTTS_0014', 'TTS_VolcesAiGatewayTTS', '开朗姐姐', 'zh_female_kailangjiejie_moon_bigtts', 'Chinese', NULL, NULL, 14, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_VolcesAiGatewayTTS_0015', 'TTS_VolcesAiGatewayTTS', '邻家男孩', 'zh_male_linjiananhai_moon_bigtts', 'Chinese', NULL, NULL, 15, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_VolcesAiGatewayTTS_0016', 'TTS_VolcesAiGatewayTTS', '甜美悦悦', 'zh_female_tianmeiyueyue_moon_bigtts', 'Chinese', NULL, NULL, 16, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_VolcesAiGatewayTTS_0017', 'TTS_VolcesAiGatewayTTS', '心灵鸡汤', 'zh_female_xinlingjitang_moon_bigtts', 'Chinese', NULL, NULL, 17, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_VolcesAiGatewayTTS_0018', 'TTS_VolcesAiGatewayTTS', '知性温婉', 'ICL_zh_female_zhixingwenwan_tob', 'Chinese', NULL, NULL, 18, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_VolcesAiGatewayTTS_0019', 'TTS_VolcesAiGatewayTTS', '暖心体贴', 'ICL_zh_male_nuanxintitie_tob', 'Chinese', NULL, NULL, 19, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_VolcesAiGatewayTTS_0020', 'TTS_VolcesAiGatewayTTS', '温柔文雅', 'ICL_zh_female_wenrouwenya_tob', 'Chinese', NULL, NULL, 20, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_VolcesAiGatewayTTS_0021', 'TTS_VolcesAiGatewayTTS', '开朗轻快', 'ICL_zh_male_kailangqingkuai_tob', 'Chinese', NULL, NULL, 21, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_VolcesAiGatewayTTS_0022', 'TTS_VolcesAiGatewayTTS', '活泼爽朗', 'ICL_zh_male_huoposhuanglang_tob', 'Chinese', NULL, NULL, 22, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_VolcesAiGatewayTTS_0023', 'TTS_VolcesAiGatewayTTS', '率真小伙', 'ICL_zh_male_shuaizhenxiaohuo_tob', 'Chinese', NULL, NULL, 23, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_VolcesAiGatewayTTS_0024', 'TTS_VolcesAiGatewayTTS', '温柔小哥', 'zh_male_wenrouxiaoge_mars_bigtts', 'Chinese', NULL, NULL, 24, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_VolcesAiGatewayTTS_0025', 'TTS_VolcesAiGatewayTTS', 'Smith', 'en_male_smith_mars_bigtts', '英式英语', NULL, NULL, 25, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_VolcesAiGatewayTTS_0026', 'TTS_VolcesAiGatewayTTS', 'Anna', 'en_female_anna_mars_bigtts', '英式英语', NULL, NULL, 26, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_VolcesAiGatewayTTS_0027', 'TTS_VolcesAiGatewayTTS', 'Adam', 'en_male_adam_mars_bigtts', '美式英语', NULL, NULL, 27, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_VolcesAiGatewayTTS_0028', 'TTS_VolcesAiGatewayTTS', 'Sarah', 'en_female_sarah_mars_bigtts', '澳洲英语', NULL, NULL, 28, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_VolcesAiGatewayTTS_0029', 'TTS_VolcesAiGatewayTTS', 'Dryw', 'en_male_dryw_mars_bigtts', '澳洲英语', NULL, NULL, 29, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_VolcesAiGatewayTTS_0030', 'TTS_VolcesAiGatewayTTS', 'かずね（和音）', 'multi_male_jingqiangkanye_moon_bigtts', '日语、西语', NULL, NULL, 30, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_VolcesAiGatewayTTS_0031', 'TTS_VolcesAiGatewayTTS', 'はるこ（晴子）', 'multi_female_shuangkuaisisi_moon_bigtts', '日语、西语', NULL, NULL, 31, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_VolcesAiGatewayTTS_0032', 'TTS_VolcesAiGatewayTTS', 'ひろし（広志）', 'multi_male_wanqudashu_moon_bigtts', '日语、西语', NULL, NULL, 32, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_VolcesAiGatewayTTS_0033', 'TTS_VolcesAiGatewayTTS', 'あけみ（朱美）', 'multi_female_gaolengyujie_moon_bigtts', '日语', NULL, NULL, 33, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_VolcesAiGatewayTTS_0034', 'TTS_VolcesAiGatewayTTS', 'Amanda', 'en_female_amanda_mars_bigtts', '美式英语', NULL, NULL, 34, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_VolcesAiGatewayTTS_0035', 'TTS_VolcesAiGatewayTTS', 'Jackson', 'en_male_jackson_mars_bigtts', '美式英语', NULL, NULL, 35, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_VolcesAiGatewayTTS_0036', 'TTS_VolcesAiGatewayTTS', '京腔侃爷/Harmony', 'zh_male_jingqiangkanye_moon_bigtts', '中文-北京口音、英文', NULL, NULL, 36, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_VolcesAiGatewayTTS_0037', 'TTS_VolcesAiGatewayTTS', '湾湾小何', 'zh_female_wanwanxiaohe_moon_bigtts', '中文-台湾口音', NULL, NULL, 37, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_VolcesAiGatewayTTS_0038', 'TTS_VolcesAiGatewayTTS', '湾区大叔', 'zh_female_wanqudashu_moon_bigtts', '中文-广东口音', NULL, NULL, 38, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_VolcesAiGatewayTTS_0039', 'TTS_VolcesAiGatewayTTS', '呆萌川妹', 'zh_female_daimengchuanmei_moon_bigtts', '中文-四川口音', NULL, NULL, 39, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_VolcesAiGatewayTTS_0040', 'TTS_VolcesAiGatewayTTS', '广州德哥', 'zh_male_guozhoudege_moon_bigtts', '中文-广东口音', NULL, NULL, 40, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_VolcesAiGatewayTTS_0041', 'TTS_VolcesAiGatewayTTS', '北京小爷', 'zh_male_beijingxiaoye_moon_bigtts', '中文-北京口音', NULL, NULL, 41, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_VolcesAiGatewayTTS_0042', 'TTS_VolcesAiGatewayTTS', '浩宇小哥', 'zh_male_haoyuxiaoge_moon_bigtts', '中文-青岛口音', NULL, NULL, 42, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_VolcesAiGatewayTTS_0043', 'TTS_VolcesAiGatewayTTS', '广西远舟', 'zh_male_guangxiyuanzhou_moon_bigtts', '中文-广西口音', NULL, NULL, 43, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_VolcesAiGatewayTTS_0044', 'TTS_VolcesAiGatewayTTS', '妹坨洁儿', 'zh_female_meituojieer_moon_bigtts', '中文-长沙口音', NULL, NULL, 44, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_VolcesAiGatewayTTS_0045', 'TTS_VolcesAiGatewayTTS', '豫州子轩', 'zh_male_yuzhouzixuan_moon_bigtts', '中文-河南口音', NULL, NULL, 45, NULL, NULL, NULL, NULL);


-- =====================================================
-- From file: 202504251422.sql
-- =====================================================
-- 增加server.ota，用于配置ota地址

delete from `sys_params` where id = 100;
delete from `sys_params` where id = 101;

delete from `sys_params` where id = 106;
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (106, 'server.websocket', 'null', 'string', 1, 'websocket地址，多个用;分隔');

delete from `sys_params` where id = 107;
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (107, 'server.ota', 'null', 'string', 1, 'ota地址');


-- 增加固件信息表
CREATE TABLE IF NOT EXISTS `ai_ota` (
  `id` varchar(32) NOT NULL COMMENT 'ID',
  `firmware_name` varchar(100) DEFAULT NULL COMMENT '固件名称',
  `type` varchar(50) DEFAULT NULL COMMENT '固件Type',
  `version` varchar(50) DEFAULT NULL COMMENT '版本号',
  `size` bigint DEFAULT NULL COMMENT '文件大小(字节)',
  `remark` varchar(500) DEFAULT NULL COMMENT 'Remark/说明',
  `firmware_path` varchar(255) DEFAULT NULL COMMENT '固件路径',
  `sort` int unsigned DEFAULT '0' COMMENT 'Sort order',
  `updater` bigint DEFAULT NULL COMMENT 'Updater',
  `update_date` datetime DEFAULT NULL COMMENT 'Update time',
  `creator` bigint DEFAULT NULL COMMENT 'Creator',
  `create_date` datetime DEFAULT NULL COMMENT 'Create time',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='固件信息表';

update ai_device set auto_update = 1;



-- =====================================================
-- From file: 202504291043.sql
-- =====================================================
-- 增加FunASR服务语音识别模型供应器和配置
DELETE FROM `ai_model_provider` WHERE `id` = 'SYSTEM_ASR_FunASRServer';
INSERT INTO `ai_model_provider` (`id`, `model_type`, `provider_code`, `name`, `fields`, `sort`, `creator`, `create_date`, `updater`, `update_date`) VALUES
('SYSTEM_ASR_FunASRServer', 'ASR', 'fun_server', 'FunASR服务语音识别', '[{"key":"host","label":"服务地址","type":"string"},{"key":"port","label":"端口号","type":"number"}]', 4, 1, NOW(), 1, NOW());

DELETE FROM `ai_model_config` WHERE `id` = 'ASR_FunASRServer';
INSERT INTO `ai_model_config` VALUES ('ASR_FunASRServer', 'ASR', 'FunASRServer', 'FunASR服务语音识别', 0, 1, '{\"type\": \"fun_server\", \"host\": \"127.0.0.1\", \"port\": 10096}', NULL, NULL, 5, NULL, NULL, NULL, NULL);

-- 修改ai_model_config表的remark字段类型为TEXT
ALTER TABLE `ai_model_config` MODIFY COLUMN `remark` TEXT COMMENT 'Remark'; 

-- 更新ASR模型配置的说明文档
UPDATE `ai_model_config` SET 
`doc_link` = 'https://github.com/modelscope/FunASR/blob/main/runtime/docs/SDK_advanced_guide_online_zh.md',
`remark` = '独立部署FunASR，使用FunASR的API服务，只需要五句话
第一句：mkdir -p ./funasr-runtime-resources/models
第二句：sudo docker run -d -p 10096:10095 --privileged=true -v $PWD/funasr-runtime-resources/models:/workspace/models registry.cn-hangzhou.aliyuncs.com/funasr_repo/funasr:funasr-runtime-sdk-online-cpu-0.1.12
上一句话执行后会进入到容器，继续第三句：cd FunASR/runtime
不要退出容器，继续在容器中执行第四句：nohup bash run_server_2pass.sh --download-model-dir /workspace/models --vad-dir damo/speech_fsmn_vad_zh-cn-16k-common-onnx --model-dir damo/speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-onnx  --online-model-dir damo/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-online-onnx  --punc-dir damo/punc_ct-transformer_zh-cn-common-vad_realtime-vocab272727-onnx --lm-dir damo/speech_ngram_lm_zh-cn-ai-wesp-fst --itn-dir thuduj12/fst_itn_zh --hotword /workspace/models/hotwords.txt > log.txt 2>&1 &
上一句话执行后会进入到容器，继续第五句：tail -f log.txt
第五句话执行完后，会看到模型下载日志，下载完后就可以连接使用了
以上是使用CPU推理，如果有GPU，详细参考：https://github.com/modelscope/FunASR/blob/main/runtime/docs/SDK_advanced_guide_online_zh.md' WHERE `id` = 'ASR_FunASRServer';

-- 更新FunASR本地模型配置说明
UPDATE `ai_model_config` SET 
`doc_link` = 'https://github.com/modelscope/FunASR',
`remark` = 'FunASR本地模型配置说明：
1. 需要下载模型文件到xiaozhi-server/models/SenseVoiceSmall目录
2. 支持中日韩粤语音识别
3. 本地推理，无需网络连接
4. 待识别文件保存在tmp/目录' WHERE `id` = 'ASR_FunASR';

-- 更新SherpaASR配置说明
UPDATE `ai_model_config` SET 
`doc_link` = 'https://github.com/k2-fsa/sherpa-onnx',
`remark` = 'SherpaASR配置说明：
1. 运行时自动下载模型文件到models/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17目录
2. 支持中文、英文、日语、韩语、粤语等多种语言
3. 本地推理，无需网络连接
4. 输出文件保存在tmp/目录' WHERE `id` = 'ASR_SherpaASR';

-- 更新豆包ASR配置说明
UPDATE `ai_model_config` SET 
`doc_link` = 'https://console.volcengine.com/speech/app',
`remark` = '豆包ASR配置说明：
1. 需要在火山引擎控制台创建应用并获取appid和access_token
2. 支持中文语音识别
3. 需要网络连接
4. 输出文件保存在tmp/目录
申请步骤：
1. 访问 https://console.volcengine.com/speech/app
2. 创建新应用
3. 获取appid和access_token
4. 填入配置文件中' WHERE `id` = 'ASR_DoubaoASR';

-- 更新腾讯ASR配置说明
UPDATE `ai_model_config` SET 
`doc_link` = 'https://console.cloud.tencent.com/cam/capi',
`remark` = '腾讯ASR配置说明：
1. 需要在腾讯云控制台创建应用并获取appid、secret_id和secret_key
2. 支持中文语音识别
3. 需要网络连接
4. 输出文件保存在tmp/目录
申请步骤：
1. 访问 https://console.cloud.tencent.com/cam/capi 获取密钥
2. 访问 https://console.cloud.tencent.com/asr/resourcebundle 领取免费资源
3. 获取appid、secret_id和secret_key
4. 填入配置文件中' WHERE `id` = 'ASR_TencentASR';

-- 更新TTS模型配置说明
-- EdgeTTS配置说明
UPDATE `ai_model_config` SET 
`doc_link` = 'https://github.com/rany2/edge-tts',
`remark` = 'EdgeTTS配置说明：
1. 使用微软Edge TTS服务
2. 支持多种语言和音色
3. 免费使用，无需注册
4. 需要网络连接
5. 输出文件保存在tmp/目录' WHERE `id` = 'TTS_EdgeTTS';

-- 豆包TTS配置说明
UPDATE `ai_model_config` SET 
`doc_link` = 'https://console.volcengine.com/speech/service/8',
`remark` = '豆包TTS配置说明：
1. 访问 https://console.volcengine.com/speech/service/8
2. 需要在火山引擎控制台创建应用并获取appid和access_token
3. 山引擎语音一定要购买花钱，起步价30元，就有100并发了。如果用免费的只有2个并发，会经常报tts错误
4. 购买服务后，购买免费的音色后，可能要等半小时左右，才能使用。
5. 填入配置文件中' WHERE `id` = 'TTS_DoubaoTTS';

-- 硅基流动TTS配置说明
UPDATE `ai_model_config` SET 
`doc_link` = 'https://cloud.siliconflow.cn/account/ak',
`remark` = '硅基流动TTS配置说明：
1. 访问 https://cloud.siliconflow.cn/account/ak
2. 注册并获取API密钥
3. 填入配置文件中' WHERE `id` = 'TTS_CosyVoiceSiliconflow';

-- Coze中文TTS配置说明
UPDATE `ai_model_config` SET 
`doc_link` = 'https://www.coze.cn/open/oauth/pats',
`remark` = 'Coze中文TTS配置说明：
1. 访问 https://www.coze.cn/open/oauth/pats
2. 获取个人令牌
3. 填入配置文件中' WHERE `id` = 'TTS_CozeCnTTS';

-- FishSpeech配置说明
UPDATE `ai_model_config` SET 
`doc_link` = 'https://github.com/fishaudio/fish-speech',
`remark` = 'FishSpeech配置说明：
1. 需要本地部署FishSpeech服务
2. 支持自定义音色
3. 本地推理，无需网络连接
4. 输出文件保存在tmp/目录
5. 运行服务示例命令：python -m tools.api_server --listen 0.0.0.0:8080 --llama-checkpoint-path "checkpoints/fish-speech-1.5" --decoder-checkpoint-path "checkpoints/fish-speech-1.5/firefly-gan-vq-fsq-8x1024-21hz-generator.pth" --decoder-config-name firefly_gan_vq --compile' WHERE `id` = 'TTS_FishSpeech';

-- GPT-SoVITS V2配置说明
UPDATE `ai_model_config` SET 
`doc_link` = 'https://github.com/RVC-Boss/GPT-SoVITS',
`remark` = 'GPT-SoVITS V2配置说明：
1. 需要本地部署GPT-SoVITS服务
2. 支持自定义音色克隆
3. 本地推理，无需网络连接
4. 输出文件保存在tmp/目录
部署步骤：
1. 运行服务示例命令：python api_v2.py -a 127.0.0.1 -p 9880 -c GPT_SoVITS/configs/demo.yaml' WHERE `id` = 'TTS_GPT_SOVITS_V2';

-- GPT-SoVITS V3配置说明
UPDATE `ai_model_config` SET 
`doc_link` = 'https://github.com/RVC-Boss/GPT-SoVITS',
`remark` = 'GPT-SoVITS V3配置说明：
1. 需要本地部署GPT-SoVITS V3服务
2. 支持自定义音色克隆
3. 本地推理，无需网络连接
4. 输出文件保存在tmp/目录' WHERE `id` = 'TTS_GPT_SOVITS_V3';

-- MiniMax TTS配置说明
UPDATE `ai_model_config` SET 
`doc_link` = 'https://platform.minimaxi.com/',
`remark` = 'MiniMax TTS配置说明：
1. 需要在MiniMax平台创建账户并充值
2. 支持多种音色，当前配置使用female-shaonv
3. 需要网络连接
4. 输出文件保存在tmp/目录
申请步骤：
1. 访问 https://platform.minimaxi.com/ 注册账号
2. 访问 https://platform.minimaxi.com/user-center/payment/balance 充值
3. 访问 https://platform.minimaxi.com/user-center/basic-information 获取group_id
4. 访问 https://platform.minimaxi.com/user-center/basic-information/interface-key 获取api_key
5. 填入配置文件中' WHERE `id` = 'TTS_MinimaxTTS';

-- 阿里云TTS配置说明
UPDATE `ai_model_config` SET 
`doc_link` = 'https://nls-portal.console.aliyun.com/',
`remark` = '阿里云TTS配置说明：
1. 需要在阿里云平台开通智能语音交互服务
2. 支持多种音色，当前配置使用xiaoyun
3. 需要网络连接
4. 输出文件保存在tmp/目录
申请步骤：
1. 访问 https://nls-portal.console.aliyun.com/ 开通服务
2. 访问 https://nls-portal.console.aliyun.com/applist 获取appkey
3. 访问 https://nls-portal.console.aliyun.com/overview 获取token
4. 填入配置文件中
注意：token是临时的24小时有效，长期使用需要配置access_key_id和access_key_secret' WHERE `id` = 'TTS_AliyunTTS';

-- 腾讯TTS配置说明
UPDATE `ai_model_config` SET 
`doc_link` = 'https://console.cloud.tencent.com/cam/capi',
`remark` = '腾讯TTS配置说明：
1. 需要在腾讯云平台开通智能语音交互服务
2. 支持多种音色，当前配置使用101001
3. 需要网络连接
4. 输出文件保存在tmp/目录
申请步骤：
1. 访问 https://console.cloud.tencent.com/cam/capi 获取密钥
2. 访问 https://console.cloud.tencent.com/tts/resourcebundle 领取免费资源
3. 创建新应用
4. 获取appid、secret_id和secret_key
5. 填入配置文件中' WHERE `id` = 'TTS_TencentTTS';

-- 302AI TTS配置说明
UPDATE `ai_model_config` SET 
`doc_link` = 'https://dash.302.ai/',
`remark` = '302AI TTS配置说明：
1. 需要在302平台创建账户并获取API密钥
2. 支持多种音色，当前配置使用湾湾小何音色
3. 需要网络连接
4. 输出文件保存在tmp/目录
申请步骤：
1. 访问 https://dash.302.ai/ 注册账号
2. 访问 https://dash.302.ai/apis/list 获取API密钥
3. 填入配置文件中
价格：$35/百万字符' WHERE `id` = 'TTS_TTS302AI';

-- 机智云TTS配置说明
UPDATE `ai_model_config` SET 
`doc_link` = 'https://agentrouter.gizwitsapi.com/panel/token',
`remark` = '机智云TTS配置说明：
1. 需要在机智云平台获取API密钥
2. 支持多种音色，当前配置使用湾湾小何音色
3. 需要网络连接
4. 输出文件保存在tmp/目录
申请步骤：
1. 访问 https://agentrouter.gizwitsapi.com/panel/token 获取API密钥
2. 填入配置文件中
注意：前一万名注册的用户，将送5元体验金额' WHERE `id` = 'TTS_GizwitsTTS';

-- ACGN TTS配置说明
UPDATE `ai_model_config` SET 
`doc_link` = 'https://acgn.ttson.cn/',
`remark` = 'ACGN TTS配置说明：
1. 需要在ttson平台购买token
2. 支持多种角色音色，当前配置使用角色ID：1695
3. 需要网络连接
4. 输出文件保存在tmp/目录
申请步骤：
1. 访问 https://acgn.ttson.cn/ 查看角色列表
2. 访问 www.ttson.cn 购买token
3. 填入配置文件中
开发相关疑问请提交至网站上的qq' WHERE `id` = 'TTS_ACGNTTS';

-- OpenAI TTS配置说明
UPDATE `ai_model_config` SET 
`doc_link` = 'https://platform.openai.com/api-keys',
`remark` = 'OpenAI TTS配置说明：
1. 需要在OpenAI平台获取API密钥
2. 支持多种音色，当前配置使用onyx
3. 需要网络连接
4. 输出文件保存在tmp/目录
申请步骤：
1. 访问 https://platform.openai.com/api-keys 获取API密钥
2. 填入配置文件中
注意：国内需要使用代理访问' WHERE `id` = 'TTS_OpenAITTS';

-- 自定义TTS配置说明
UPDATE `ai_model_config` SET 
`doc_link` = NULL,
`remark` = '自定义TTS配置说明：
1. 支持自定义TTS接口服务
2. 使用GET方式请求
3. 需要网络连接
4. 输出文件保存在tmp/目录
配置说明：
1. 在params中配置请求参数
2. 在headers中配置请求头
3. 设置返回音频格式' WHERE `id` = 'TTS_CustomTTS';

-- 火山引擎边缘大模型网关TTS配置说明
UPDATE `ai_model_config` SET 
`doc_link` = 'https://console.volcengine.com/vei/aigateway/',
`remark` = '火山引擎边缘大模型网关TTS配置说明：
1. 访问 https://console.volcengine.com/vei/aigateway/
2. 创建网关访问密钥，搜索并勾选 Doubao-语音合成
3. 如果需要使用LLM，一并勾选 Doubao-pro-32k-functioncall
4. 访问 https://console.volcengine.com/vei/aigateway/tokens-list 获取密钥
5. 填入配置文件中
音色列表参考：https://www.volcengine.com/docs/6561/1257544' WHERE `id` = 'TTS_VolcesAiGatewayTTS';

-- 更新LLM模型配置说明
-- ChatGLM配置说明
UPDATE `ai_model_config` SET 
`doc_link` = 'https://bigmodel.cn/usercenter/proj-mgmt/apikeys',
`remark` = 'ChatGLM配置说明：
1. 访问 https://bigmodel.cn/usercenter/proj-mgmt/apikeys
2. 注册并获取API密钥
3. 填入配置文件中' WHERE `id` = 'LLM_ChatGLMLLM';

-- Ollama配置说明
UPDATE `ai_model_config` SET 
`doc_link` = 'https://ollama.com/',
`remark` = 'Ollama配置说明：
1. 安装Ollama服务
2. 运行命令：ollama pull qwen2.5
3. 确保服务运行在http://localhost:11434' WHERE `id` = 'LLM_OllamaLLM';

-- 通义千问配置说明
UPDATE `ai_model_config` SET 
`doc_link` = 'https://bailian.console.aliyun.com/?apiKey=1#/api-key',
`remark` = '通义千问配置说明：
1. 访问 https://bailian.console.aliyun.com/?apiKey=1#/api-key
2. 获取API密钥
3. 填入配置文件中，当前配置使用qwen-turbo模型
4. 支持自定义参数：temperature=0.7, max_tokens=500, top_p=1, top_k=50' WHERE `id` = 'LLM_AliLLM';

-- 通义百炼配置说明
UPDATE `ai_model_config` SET 
`doc_link` = 'https://bailian.console.aliyun.com/?apiKey=1#/api-key',
`remark` = '通义百炼配置说明：
1. 访问 https://bailian.console.aliyun.com/?apiKey=1#/api-key
2. 获取app_id和api_key
3. 填入配置文件中' WHERE `id` = 'LLM_AliAppLLM';

-- 豆包大模型配置说明
UPDATE `ai_model_config` SET 
`doc_link` = 'https://console.volcengine.com/ark/region:ark+cn-beijing/openManagement',
`remark` = '豆包大模型配置说明：
1. 访问 https://console.volcengine.com/ark/region:ark+cn-beijing/openManagement
2. 开通Doubao-1.5-pro服务
3. 访问 https://console.volcengine.com/ark/region:ark+cn-beijing/apiKey 获取API密钥
4. 填入配置文件中
5. 当前建议使用doubao-1-5-pro-32k-250115
注意：有免费额度500000token' WHERE `id` = 'LLM_DoubaoLLM';

-- DeepSeek配置说明
UPDATE `ai_model_config` SET 
`doc_link` = 'https://platform.deepseek.com/',
`remark` = 'DeepSeek配置说明：
1. 访问 https://platform.deepseek.com/
2. 注册并获取API密钥
3. 填入配置文件中' WHERE `id` = 'LLM_DeepSeekLLM';

-- Dify配置说明
UPDATE `ai_model_config` SET 
`doc_link` = 'https://cloud.dify.ai/',
`remark` = 'Dify配置说明：
1. 访问 https://cloud.dify.ai/
2. 注册并获取API密钥
3. 填入配置文件中
4. 支持多种对话模式：workflows/run, chat-messages, completion-messages
5. 平台设置的角色定义会失效，需要在Dify控制台设置
注意：建议使用本地部署的Dify接口，国内部分区域访问公有云接口可能受限' WHERE `id` = 'LLM_DifyLLM';

-- Gemini配置说明
UPDATE `ai_model_config` SET 
`doc_link` = 'https://aistudio.google.com/apikey',
`remark` = 'Gemini配置说明：
1. 使用谷歌Gemini API服务
2. 当前配置使用gemini-2.0-flash模型
3. 需要网络连接
4. 支持配置代理
申请步骤：
1. 访问 https://aistudio.google.com/apikey
2. 创建API密钥
3. 填入配置文件中
注意：若在中国境内使用，请遵守《生成式人工智能服务管理暂行办法》' WHERE `id` = 'LLM_GeminiLLM';

-- Coze配置说明
UPDATE `ai_model_config` SET 
`doc_link` = 'https://www.coze.cn/open/oauth/pats',
`remark` = 'Coze配置说明：
1. 使用Coze平台服务
2. 需要bot_id、user_id和个人令牌
3. 需要网络连接
申请步骤：
1. 访问 https://www.coze.cn/open/oauth/pats
2. 获取个人令牌
3. 手动计算bot_id和user_id
4. 填入配置文件中' WHERE `id` = 'LLM_CozeLLM';

-- LM Studio配置说明
UPDATE `ai_model_config` SET 
`doc_link` = 'https://lmstudio.ai/',
`remark` = 'LM Studio配置说明：
1. 使用本地部署的LM Studio服务
2. 当前配置使用deepseek-r1-distill-llama-8b@q4_k_m模型
3. 本地推理，无需网络连接
4. 需要预先下载模型
部署步骤：
1. 安装LM Studio
2. 从社区下载模型
3. 确保服务运行在http://localhost:1234/v1' WHERE `id` = 'LLM_LMStudioLLM';

-- FastGPT配置说明
UPDATE `ai_model_config` SET 
`doc_link` = 'https://cloud.tryfastgpt.ai/account/apikey',
`remark` = 'FastGPT配置说明：
1. 使用FastGPT平台服务
2. 需要网络连接
3. 配置文件中的prompt无效，需要在FastGPT控制台设置
4. 支持自定义变量
申请步骤：
1. 访问 https://cloud.tryfastgpt.ai/account/apikey
2. 获取API密钥
3. 填入配置文件中' WHERE `id` = 'LLM_FastgptLLM';

-- Xinference配置说明
UPDATE `ai_model_config` SET 
`doc_link` = 'https://github.com/xorbitsai/inference',
`remark` = 'Xinference配置说明：
1. 使用本地部署的Xinference服务
2. 当前配置使用qwen2.5:72b-AWQ模型
3. 本地推理，无需网络连接
4. 需要预先启动对应模型
部署步骤：
1. 安装Xinference
2. 启动服务并加载模型
3. 确保服务运行在http://localhost:9997' WHERE `id` = 'LLM_XinferenceLLM';

-- Xinference小模型配置说明
UPDATE `ai_model_config` SET 
`doc_link` = 'https://github.com/xorbitsai/inference',
`remark` = 'Xinference小模型配置说明：
1. 使用本地部署的Xinference服务
2. 当前配置使用qwen2.5:3b-AWQ模型
3. 本地推理，无需网络连接
4. 用于意图识别
部署步骤：
1. 安装Xinference
2. 启动服务并加载模型
3. 确保服务运行在http://localhost:9997' WHERE `id` = 'LLM_XinferenceSmallLLM';

-- 火山引擎边缘大模型网关LLM配置说明
UPDATE `ai_model_config` SET 
`doc_link` = 'https://console.volcengine.com/vei/aigateway/',
`remark` = '火山引擎边缘大模型网关LLM配置说明：
1. 使用火山引擎边缘大模型网关服务
2. 需要网关访问密钥
3. 需要网络连接
4. 支持function_call功能
申请步骤：
1. 访问 https://console.volcengine.com/vei/aigateway/
2. 创建网关访问密钥，搜索并勾选 Doubao-pro-32k-functioncall
3. 如果需要使用语音合成，一并勾选 Doubao-语音合成
4. 访问 https://console.volcengine.com/vei/aigateway/tokens-list 获取密钥
5. 填入配置文件中' WHERE `id` = 'LLM_VolcesAiGatewayLLM';

-- 更新Memory模型配置说明
-- 无记忆配置说明
UPDATE `ai_model_config` SET 
`doc_link` = NULL,
`remark` = '无记忆配置说明：
1. 不保存对话历史
2. 每次对话都是独立的
3. 无需额外配置
4. 适合对隐私要求高的场景' WHERE `id` = 'Memory_nomem';

-- 本地短期记忆配置说明
UPDATE `ai_model_config` SET 
`doc_link` = NULL,
`remark` = '本地短期记忆配置说明：
1. 使用本地存储保存对话历史
2. 通过selected_module的llm总结对话内容
3. 数据保存在本地，不会上传到服务器
4. 适合注重隐私的场景
5. 无需额外配置' WHERE `id` = 'Memory_mem_local_short';

-- Mem0AI记忆配置说明
UPDATE `ai_model_config` SET 
`doc_link` = 'https://app.mem0.ai/dashboard/api-keys',
`remark` = 'Mem0AI记忆配置说明：
1. 使用Mem0AI服务保存对话历史
2. 需要API密钥
3. 需要网络连接
4. 每月有1000次免费调用
申请步骤：
1. 访问 https://app.mem0.ai/dashboard/api-keys
2. 获取API密钥
3. 填入配置文件中' WHERE `id` = 'Memory_mem0ai';

-- 更新Intent模型配置说明
-- 无意图识别配置说明
UPDATE `ai_model_config` SET 
`doc_link` = NULL,
`remark` = '无意图识别配置说明：
1. 不进行意图识别
2. 所有对话直接传递给LLM处理
3. 无需额外配置
4. 适合简单对话场景' WHERE `id` = 'Intent_nointent';

-- LLM意图识别配置说明
UPDATE `ai_model_config` SET 
`doc_link` = NULL,
`remark` = 'LLM意图识别配置说明：
1. 使用独立的LLM进行意图识别
2. 默认使用selected_module.LLM的模型
3. 可以配置使用独立的LLM（如免费的ChatGLMLLM）
4. 通用性强，但会增加处理时间
5. 不支持控制音量大小等iot操作
配置说明：
1. 在llm字段中指定使用的LLM模型
2. 如果不指定，则使用selected_module.LLM的模型' WHERE `id` = 'Intent_intent_llm';

-- 函数调用意图识别配置说明
UPDATE `ai_model_config` SET 
`doc_link` = NULL,
`remark` = '函数调用意图识别配置说明：
1. 使用LLM的function_call功能进行意图识别
2. 需要所选择的LLM支持function_call
3. 按需调用工具，处理速度快
4. 支持所有iot指令
5. 默认已加载以下功能：
   - handle_exit_intent（退出识别）
   - play_music（音乐播放）
   - change_role（角色切换）
   - get_weather（天气查询）
   - get_news（新闻查询）
配置说明：
1. 在functions字段中配置需要加载的功能模块
2. 系统默认已加载基础功能，无需重复配置
3. 可以添加自定义功能模块' WHERE `id` = 'Intent_function_call';

-- 更新VAD模型配置说明
-- SileroVAD配置说明
UPDATE `ai_model_config` SET 
`doc_link` = 'https://github.com/snakers4/silero-vad',
`remark` = 'SileroVAD配置说明：
1. 使用SileroVAD模型进行语音活动检测
2. 本地推理，无需网络连接
3. 需要下载模型文件到models/snakers4_silero-vad目录
4. 可配置参数：
   - threshold: 0.5（语音检测阈值）
   - min_silence_duration_ms: 700（最小静音持续时间，单位毫秒）
5. 如果说话停顿比较长，可以适当增加min_silence_duration_ms的值' WHERE `id` = 'VAD_SileroVAD';



-- =====================================================
-- From file: 202504301341.sql
-- =====================================================
update `ai_model_provider` set `fields` = 
'[{"key": "api_url","label": "API地址","type": "string"},{"key": "voice","label": "音色","type": "string"},{"key": "output_dir","label": "输出目录","type": "string"},{"key": "authorization","label": "授权","type": "string"},{"key": "appid","label": "应用ID","type": "string"},{"key": "access_token","label": "访问令牌","type": "string"},{"key": "cluster","label": "集群","type": "string"},{"key": "speed_ratio","label": "语速","type": "number"},{"key": "volume_ratio","label": "音量","type": "number"},{"key": "pitch_ratio","label": "音高","type": "number"}]'
where `id` = 'SYSTEM_TTS_doubao';

-- 添加阿里云ASR供应器
delete from `ai_model_provider` where `id` = 'SYSTEM_ASR_AliyunASR';
INSERT INTO `ai_model_provider` (`id`, `model_type`, `provider_code`, `name`, `fields`, `sort`, `creator`, `create_date`, `updater`, `update_date`) VALUES
('SYSTEM_ASR_AliyunASR', 'ASR', 'aliyun', '阿里云语音识别', '[{"key":"appkey","label":"应用AppKey","type":"string"},{"key":"token","label":"临时Token","type":"string"},{"key":"access_key_id","label":"AccessKey ID","type":"string"},{"key":"access_key_secret","label":"AccessKey Secret","type":"string"},{"key":"output_dir","label":"输出目录","type":"string"}]', 5, 1, NOW(), 1, NOW());

-- 添加阿里云ASR模型配置
delete from `ai_model_config` where `id` = 'ASR_AliyunASR';
INSERT INTO `ai_model_config` VALUES ('ASR_AliyunASR', 'ASR', 'AliyunASR', '阿里云语音识别', 0, 1, '{\"type\": \"aliyun\", \"appkey\": \"\", \"token\": \"\", \"access_key_id\": \"\", \"access_key_secret\": \"\", \"output_dir\": \"tmp/\"}', NULL, NULL, 6, NULL, NULL, NULL, NULL);

-- 更新阿里云ASR模型配置的说明文档
UPDATE `ai_model_config` SET 
`doc_link` = 'https://nls-portal.console.aliyun.com/',
`remark` = '阿里云ASR配置说明：
1. 访问 https://nls-portal.console.aliyun.com/ 开通服务
2. 访问 https://nls-portal.console.aliyun.com/applist 获取appkey
3. 访问 https://nls-portal.console.aliyun.com/overview 获取token
4. 获取access_key_id和access_key_secret
5. 填入配置文件中' WHERE `id` = 'ASR_AliyunASR';

-- 插入固件类型字典类型
delete from `sys_dict_type` where `id` = 101;
INSERT INTO `sys_dict_type` (`id`, `dict_type`, `dict_name`, `remark`, `sort`, `creator`, `create_date`, `updater`, `update_date`) VALUES 
(101, 'FIRMWARE_TYPE', '固件类型', '固件类型字典', 0, 1, NOW(), 1, NOW());

-- 插入固件类型字典数据
delete from `sys_dict_data` where `dict_type_id` = 101;
INSERT INTO `sys_dict_data` (`id`, `dict_type_id`, `dict_label`, `dict_value`, `remark`, `sort`, `creator`, `create_date`, `updater`, `update_date`) VALUES 
(101001, 101, '面包板新版接线（WiFi）', 'bread-compact-wifi', '面包板新版接线（WiFi）', 1, 1, NOW(), 1, NOW()),
(101002, 101, '面包板新版接线（WiFi）+ LCD', 'bread-compact-wifi-lcd', '面包板新版接线（WiFi）+ LCD', 2, 1, NOW(), 1, NOW()),
(101003, 101, '面包板新版接线（ML307 AT）', 'bread-compact-ml307', '面包板新版接线（ML307 AT）', 3, 1, NOW(), 1, NOW()),
(101004, 101, '面包板（WiFi） ESP32 DevKit', 'bread-compact-esp32', '面包板（WiFi） ESP32 DevKit', 4, 1, NOW(), 1, NOW()),
(101005, 101, '面包板（WiFi+ LCD） ESP32 DevKit', 'bread-compact-esp32-lcd', '面包板（WiFi+ LCD） ESP32 DevKit', 5, 1, NOW(), 1, NOW()),
(101006, 101, 'DFRobot 行空板 k10', 'df-k10', 'DFRobot 行空板 k10', 6, 1, NOW(), 1, NOW()),
(101007, 101, 'ESP32 CGC', 'esp32-cgc', 'ESP32 CGC', 7, 1, NOW(), 1, NOW()),
(101008, 101, 'ESP BOX 3', 'esp-box-3', 'ESP BOX 3', 8, 1, NOW(), 1, NOW()),
(101009, 101, 'ESP BOX', 'esp-box', 'ESP BOX', 9, 1, NOW(), 1, NOW()),
(101010, 101, 'ESP BOX Lite', 'esp-box-lite', 'ESP BOX Lite', 10, 1, NOW(), 1, NOW()),
(101011, 101, 'Kevin Box 1', 'kevin-box-1', 'Kevin Box 1', 11, 1, NOW(), 1, NOW()),
(101012, 101, 'Kevin Box 2', 'kevin-box-2', 'Kevin Box 2', 12, 1, NOW(), 1, NOW()),
(101013, 101, 'Kevin C3', 'kevin-c3', 'Kevin C3', 13, 1, NOW(), 1, NOW()),
(101014, 101, 'Kevin SP V3开发板', 'kevin-sp-v3-dev', 'Kevin SP V3开发板', 14, 1, NOW(), 1, NOW()),
(101015, 101, 'Kevin SP V4开发板', 'kevin-sp-v4-dev', 'Kevin SP V4开发板', 15, 1, NOW(), 1, NOW()),
(101016, 101, '鱼鹰科技3.13LCD开发板', 'kevin-yuying-313lcd', '鱼鹰科技3.13LCD开发板', 16, 1, NOW(), 1, NOW()),
(101017, 101, '立创·实战派ESP32-S3开发板', 'lichuang-dev', '立创·实战派ESP32-S3开发板', 17, 1, NOW(), 1, NOW()),
(101018, 101, '立创·实战派ESP32-C3开发板', 'lichuang-c3-dev', '立创·实战派ESP32-C3开发板', 18, 1, NOW(), 1, NOW()),
(101019, 101, '神奇按钮 Magiclick_2.4', 'magiclick-2p4', '神奇按钮 Magiclick_2.4', 19, 1, NOW(), 1, NOW()),
(101020, 101, '神奇按钮 Magiclick_2.5', 'magiclick-2p5', '神奇按钮 Magiclick_2.5', 20, 1, NOW(), 1, NOW()),
(101021, 101, '神奇按钮 Magiclick_C3', 'magiclick-c3', '神奇按钮 Magiclick_C3', 21, 1, NOW(), 1, NOW()),
(101022, 101, '神奇按钮 Magiclick_C3_v2', 'magiclick-c3-v2', '神奇按钮 Magiclick_C3_v2', 22, 1, NOW(), 1, NOW()),
(101023, 101, 'M5Stack CoreS3', 'm5stack-core-s3', 'M5Stack CoreS3', 23, 1, NOW(), 1, NOW()),
(101024, 101, 'AtomS3 + Echo Base', 'atoms3-echo-base', 'AtomS3 + Echo Base', 24, 1, NOW(), 1, NOW()),
(101025, 101, 'AtomS3R + Echo Base', 'atoms3r-echo-base', 'AtomS3R + Echo Base', 25, 1, NOW(), 1, NOW()),
(101026, 101, 'AtomS3R CAM/M12 + Echo Base', 'atoms3r-cam-m12-echo-base', 'AtomS3R CAM/M12 + Echo Base', 26, 1, NOW(), 1, NOW()),
(101027, 101, 'AtomMatrix + Echo Base', 'atommatrix-echo-base', 'AtomMatrix + Echo Base', 27, 1, NOW(), 1, NOW()),
(101028, 101, '虾哥 Mini C3', 'xmini-c3', '虾哥 Mini C3', 28, 1, NOW(), 1, NOW()),
(101029, 101, 'ESP32S3_KORVO2_V3开发板', 'esp32s3-korvo2-v3', 'ESP32S3_KORVO2_V3开发板', 29, 1, NOW(), 1, NOW()),
(101030, 101, 'ESP-SparkBot开发板', 'esp-sparkbot', 'ESP-SparkBot开发板', 30, 1, NOW(), 1, NOW()),
(101031, 101, 'ESP-Spot-S3', 'esp-spot-s3', 'ESP-Spot-S3', 31, 1, NOW(), 1, NOW()),
(101032, 101, 'Waveshare ESP32-S3-Touch-AMOLED-1.8', 'esp32-s3-touch-amoled-1.8', 'Waveshare ESP32-S3-Touch-AMOLED-1.8', 32, 1, NOW(), 1, NOW()),
(101033, 101, 'Waveshare ESP32-S3-Touch-LCD-1.85C', 'esp32-s3-touch-lcd-1.85c', 'Waveshare ESP32-S3-Touch-LCD-1.85C', 33, 1, NOW(), 1, NOW()),
(101034, 101, 'Waveshare ESP32-S3-Touch-LCD-1.85', 'esp32-s3-touch-lcd-1.85', 'Waveshare ESP32-S3-Touch-LCD-1.85', 34, 1, NOW(), 1, NOW()),
(101035, 101, 'Waveshare ESP32-S3-Touch-LCD-1.46', 'esp32-s3-touch-lcd-1.46', 'Waveshare ESP32-S3-Touch-LCD-1.46', 35, 1, NOW(), 1, NOW()),
(101036, 101, 'Waveshare ESP32-S3-Touch-LCD-3.5', 'esp32-s3-touch-lcd-3.5', 'Waveshare ESP32-S3-Touch-LCD-3.5', 36, 1, NOW(), 1, NOW()),
(101037, 101, '土豆子', 'tudouzi', '土豆子', 37, 1, NOW(), 1, NOW()),
(101038, 101, 'LILYGO T-Circle-S3', 'lilygo-t-circle-s3', 'LILYGO T-Circle-S3', 38, 1, NOW(), 1, NOW()),
(101039, 101, 'LILYGO T-CameraPlus-S3', 'lilygo-t-cameraplus-s3', 'LILYGO T-CameraPlus-S3', 39, 1, NOW(), 1, NOW()),
(101040, 101, 'Movecall Moji 小智AI衍生版', 'movecall-moji-esp32s3', 'Movecall Moji 小智AI衍生版', 40, 1, NOW(), 1, NOW()),
(101041, 101, 'Movecall CuiCan 璀璨·AI吊坠', 'movecall-cuican-esp32s3', 'Movecall CuiCan 璀璨·AI吊坠', 41, 1, NOW(), 1, NOW()),
(101042, 101, '正点原子DNESP32S3开发板', 'atk-dnesp32s3', '正点原子DNESP32S3开发板', 42, 1, NOW(), 1, NOW()),
(101043, 101, '正点原子DNESP32S3-BOX', 'atk-dnesp32s3-box', '正点原子DNESP32S3-BOX', 43, 1, NOW(), 1, NOW()),
(101044, 101, '嘟嘟开发板CHATX(wifi)', 'du-chatx', '嘟嘟开发板CHATX(wifi)', 44, 1, NOW(), 1, NOW()),
(101045, 101, '太极小派esp32s3', 'taiji-pi-s3', '太极小派esp32s3', 45, 1, NOW(), 1, NOW()),
(101046, 101, '无名科技星智0.85(WIFI)', 'xingzhi-cube-0.85tft-wifi', '无名科技星智0.85(WIFI)', 46, 1, NOW(), 1, NOW()),
(101047, 101, '无名科技星智0.85(ML307)', 'xingzhi-cube-0.85tft-ml307', '无名科技星智0.85(ML307)', 47, 1, NOW(), 1, NOW()),
(101048, 101, '无名科技星智0.96(WIFI)', 'xingzhi-cube-0.96oled-wifi', '无名科技星智0.96(WIFI)', 48, 1, NOW(), 1, NOW()),
(101049, 101, '无名科技星智0.96(ML307)', 'xingzhi-cube-0.96oled-ml307', '无名科技星智0.96(ML307)', 49, 1, NOW(), 1, NOW()),
(101050, 101, '无名科技星智1.54(WIFI)', 'xingzhi-cube-1.54tft-wifi', '无名科技星智1.54(WIFI)', 50, 1, NOW(), 1, NOW()),
(101051, 101, '无名科技星智1.54(ML307)', 'xingzhi-cube-1.54tft-ml307', '无名科技星智1.54(ML307)', 51, 1, NOW(), 1, NOW()),
(101052, 101, 'SenseCAP Watcher', 'sensecap-watcher', 'SenseCAP Watcher', 52, 1, NOW(), 1, NOW()),
(101053, 101, '四博智联AI陪伴盒子', 'doit-s3-aibox', '四博智联AI陪伴盒子', 53, 1, NOW(), 1, NOW()),
(101054, 101, '元控·青春', 'mixgo-nova', '元控·青春', 54, 1, NOW(), 1, NOW());



-- =====================================================
-- From file: 202505022134.sql
-- =====================================================
-- 初始化智能体聊天记录
DROP TABLE IF EXISTS ai_chat_history;
DROP TABLE IF EXISTS ai_chat_message;
DROP TABLE IF EXISTS ai_agent_chat_history;
CREATE TABLE ai_agent_chat_history
(
    id          BIGINT AUTO_INCREMENT COMMENT 'Primary keyID' PRIMARY KEY,
    mac_address VARCHAR(50) COMMENT 'MAC地址',
    agent_id VARCHAR(32) COMMENT '智能体id',
    session_id  VARCHAR(50) COMMENT '会话ID',
    chat_type   TINYINT(3) COMMENT '消息Type: 1-用户, 2-智能体',
    content     VARCHAR(1024) COMMENT '聊天内容',
    audio_id    VARCHAR(32) COMMENT '音频ID',
    created_at  DATETIME(3) DEFAULT CURRENT_TIMESTAMP(3) NOT NULL COMMENT 'Create time',
    updated_at  DATETIME(3) DEFAULT CURRENT_TIMESTAMP(3) NOT NULL ON UPDATE CURRENT_TIMESTAMP(3) COMMENT 'Update time',
    INDEX idx_ai_agent_chat_history_mac (mac_address),
    INDEX idx_ai_agent_chat_history_session_id (session_id),
    INDEX idx_ai_agent_chat_history_agent_id (agent_id),
    INDEX idx_ai_agent_chat_history_agent_session_created (agent_id, session_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT '智能体聊天记录表';

DROP TABLE IF EXISTS ai_agent_chat_audio;
CREATE TABLE ai_agent_chat_audio
(
    id          VARCHAR(32) COMMENT 'Primary keyID' PRIMARY KEY,
    audio       LONGBLOB COMMENT '音频opus数据'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT '智能体聊天音频数据表'; 


-- =====================================================
-- From file: 202505081146.sql
-- =====================================================
-- 添加百度ASR模型配置
delete from `ai_model_config` where `id` = 'ASR_BaiduASR';
INSERT INTO `ai_model_config` VALUES ('ASR_BaiduASR', 'ASR', 'BaiduASR', '百度语音识别', 0, 1, '{\"type\": \"baidu\", \"app_id\": \"\", \"api_key\": \"\", \"secret_key\": \"\", \"dev_pid\": 1537, \"output_dir\": \"tmp/\"}', NULL, NULL, 7, NULL, NULL, NULL, NULL);


-- 添加百度ASR供应器
delete from `ai_model_provider` where `id` = 'SYSTEM_ASR_BaiduASR';
INSERT INTO `ai_model_provider` (`id`, `model_type`, `provider_code`, `name`, `fields`, `sort`, `creator`, `create_date`, `updater`, `update_date`) VALUES
('SYSTEM_ASR_BaiduASR', 'ASR', 'baidu', '百度语音识别', '[{"key":"app_id","label":"应用AppID","type":"string"},{"key":"api_key","label":"API Key","type":"string"},{"key":"secret_key","label":"Secret Key","type":"string"},{"key":"dev_pid","label":"语言参数","type":"number"},{"key":"output_dir","label":"输出目录","type":"string"}]', 7, 1, NOW(), 1, NOW());


-- 更新百度ASR配置说明
UPDATE `ai_model_config` SET 
`doc_link` = 'https://console.bce.baidu.com/ai-engine/old/#/ai/speech/app/list',
`remark` = '百度ASR配置说明：
1. 访问 https://console.bce.baidu.com/ai-engine/old/#/ai/speech/app/list
2. 创建新应用
3. 获取AppID、API Key和Secret Key
4. 填入配置文件中
查看资源额度：https://console.bce.baidu.com/ai-engine/old/#/ai/speech/overview/resource/list
语言参数说明：https://ai.baidu.com/ai-doc/SPEECH/0lbxfnc9b
' WHERE `id` = 'ASR_BaiduASR';

-- 更新豆包供应器字段
update `ai_model_provider` set `fields` = 
'[{"key":"appid","label":"应用ID","type":"string"},{"key":"access_token","label":"访问令牌","type":"string"},{"key":"cluster","label":"集群","type":"string"},{"key":"boosting_table_name","label":"热词文件名称","type":"string"},{"key":"correct_table_name","label":"替换词文件名称","type":"string"},{"key":"output_dir","label":"输出目录","type":"string"}]'
where `id` = 'SYSTEM_ASR_DoubaoASR';

-- 更新豆包ASR配置说明
UPDATE `ai_model_config` SET 
`doc_link` = 'https://console.volcengine.com/speech/app',
`remark` = '豆包ASR配置说明：
1. 需要在火山引擎控制台创建应用并获取appid和access_token
2. 支持中文语音识别
3. 需要网络连接
4. 输出文件保存在tmp/目录
申请步骤：
1. 访问 https://console.volcengine.com/speech/app
2. 创建新应用
3. 获取appid和access_token
4. 填入配置文件中
如需设置热词，请参考：https://www.volcengine.com/docs/6561/155738
' WHERE `id` = 'ASR_DoubaoASR';


-- =====================================================
-- From file: 202505091555.sql
-- =====================================================
-- 更新模型供应器表
UPDATE `ai_model_provider` SET fields = '[{"key": "host", "type": "string", "label": "服务地址"}, {"key": "port", "type": "number", "label": "端口号"}, {"key": "type", "type": "string", "label": "服务类型"}, {"key": "is_ssl", "type": "boolean", "label": "是否使用SSL"}, {"key": "api_key", "type": "string", "label": "API密钥"}, {"key": "output_dir", "type": "string", "label": "输出目录"}]' WHERE id = 'SYSTEM_ASR_FunASRServer';

-- 更新模型配置表
UPDATE `ai_model_config` SET 
config_json = '{"host": "127.0.0.1", "port": 10096, "type": "fun_server", "is_ssl": true, "api_key": "none", "output_dir": "tmp/"}',
`doc_link` = 'https://github.com/modelscope/FunASR/blob/main/runtime/docs/SDK_advanced_guide_online_zh.md',
`remark` = '独立部署FunASR，使用FunASR的API服务，只需要五句话
第一句：mkdir -p ./funasr-runtime-resources/models
第二句：sudo docker run -p 10096:10095 -it --privileged=true -v $PWD/funasr-runtime-resources/models:/workspace/models registry.cn-hangzhou.aliyuncs.com/funasr_repo/funasr:funasr-runtime-sdk-online-cpu-0.1.12
上一句话执行后会进入到容器，继续第三句：cd FunASR/runtime
不要退出容器，继续在容器中执行第四句：nohup bash run_server_2pass.sh --download-model-dir /workspace/models --vad-dir damo/speech_fsmn_vad_zh-cn-16k-common-onnx --model-dir damo/speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-onnx  --online-model-dir damo/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-online-onnx  --punc-dir damo/punc_ct-transformer_zh-cn-common-vad_realtime-vocab272727-onnx --lm-dir damo/speech_ngram_lm_zh-cn-ai-wesp-fst --itn-dir thuduj12/fst_itn_zh --hotword /workspace/models/hotwords.txt > log.txt 2>&1 &
上一句话执行后会进入到容器，继续第五句：tail -f log.txt
第五句话执行完后，会看到模型下载日志，下载完后就可以连接使用了
以上是使用CPU推理，如果有GPU，详细参考：https://github.com/modelscope/FunASR/blob/main/runtime/docs/SDK_advanced_guide_online_zh.md' WHERE `id` = 'ASR_FunASRServer';

-- FishSpeech配置说明
UPDATE `ai_model_config` SET 
`doc_link` = 'https://github.com/xinnan-tech/xiaozhi-esp32-server/blob/main/docs/fish-speech-integration.md',
`remark` = 'FishSpeech配置说明：
1. 需要本地部署FishSpeech服务
2. 支持自定义音色
3. 本地推理，无需网络连接
4. 输出文件保存在tmp/目录
5. 可参照教程https://github.com/xinnan-tech/xiaozhi-esp32-server/blob/main/docs/fish-speech-integration.md' WHERE `id` = 'TTS_FishSpeech';



-- =====================================================
-- From file: 202505111914.sql
-- =====================================================
-- 添加聊天记录配置字段
ALTER TABLE `ai_agent` 
ADD COLUMN `chat_history_conf` tinyint NOT NULL DEFAULT 0 COMMENT '聊天记录配置（0不记录 1仅记录文本 2记录文本和语音）' AFTER `system_prompt`;

ALTER TABLE `ai_agent_template` 
ADD COLUMN `chat_history_conf` tinyint NOT NULL DEFAULT 0 COMMENT '聊天记录配置（0不记录 1仅记录文本 2记录文本和语音）' AFTER `system_prompt`;


-- =====================================================
-- From file: 202505122348.sql
-- =====================================================
-- 添加总结记忆字段
ALTER TABLE `ai_agent`
ADD COLUMN `summary_memory` text COMMENT '总结记忆' AFTER `system_prompt`;

ALTER TABLE `ai_agent_template`
ADD COLUMN `summary_memory` text COMMENT '总结记忆' AFTER `system_prompt`;



-- =====================================================
-- From file: 202505142037.sql
-- =====================================================
update ai_agent_template set system_prompt = replace(system_prompt, '我是', '你是');

delete from sys_params where id in (500,501,402);
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (500, 'end_prompt.enable', 'true', 'boolean', 1, '是否开启结束语');
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (501, 'end_prompt.prompt', '请你以“时间过得真快”未来头，用富有感情、依依不舍的话来结束这场对话吧！', 'string', 1, '结束提示词');

INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (402, 'plugins.get_weather.api_host', 'mj7p3y7naa.re.qweatherapi.com', 'string', 1, '开发者apihost');


-- =====================================================
-- From file: 202505151451.sql
-- =====================================================
-- 修改自定义TTS接口请求定义
update `ai_model_provider` set `fields` =
'[{"key":"url","label":"服务地址","type":"string"},{"key":"method","label":"请求方式","type":"string"},{"key":"params","label":"请求参数","type":"dict","dict_name":"params"},{"key":"headers","label":"请求头","type":"dict","dict_name":"headers"},{"key":"format","label":"音频格式","type":"string"},{"key":"output_dir","label":"输出目录","type":"string"}]'
where `id` = 'SYSTEM_TTS_custom';

-- 修改自定义TTS配置说明
UPDATE `ai_model_config` SET
`doc_link` = NULL,
`remark` = '自定义TTS配置说明：
1. 自定义的TTS接口服务，请求参数可自定义，可接入众多TTS服务
2. 以本地部署的KokoroTTS为例
3. 如果只有cpu运行：docker run -p 8880:8880 ghcr.io/remsky/kokoro-fastapi-cpu:latest
4. 如果只有gpu运行：docker run --gpus all -p 8880:8880 ghcr.io/remsky/kokoro-fastapi-gpu:latest
配置说明：
1. 在params中配置请求参数,使用JSON格式
   例如KokoroTTS：{ "input": "{prompt_text}", "speed": 1, "voice": "zm_yunxi", "stream": true, "download_format": "mp3", "response_format": "mp3", "return_download_link": true }
2. 在headers中配置请求头
3. 设置返回音频格式' WHERE `id` = 'TTS_CustomTTS';


-- =====================================================
-- From file: 202505182234.sql
-- =====================================================
-- 添加手机短信注册功能的需要的参数
delete from sys_params where id in (108, 109, 110, 111, 112, 113, 114, 115);
delete from sys_params where id in (610, 611, 612, 613);
INSERT INTO sys_params
(id, param_code, param_value, value_type, param_type, remark, creator, create_date, updater, update_date)
    VALUES
(108, 'server.name', 'xiaozhi-esp32-server', 'string', 1, '系统名称', NULL, NULL, NULL, NULL),
(109, 'server.beian_icp_num', 'null', 'string', 1, 'icp备案号，填写null则不设置', NULL, NULL, NULL, NULL),
(110, 'server.beian_ga_num', 'null', 'string', 1, '公安备案号，填写null则不设置', NULL, NULL, NULL, NULL),
(111, 'server.enable_mobile_register', 'false', 'boolean', 1, '是否开启手机注册', NULL, NULL, NULL, NULL),
(112, 'server.sms_max_send_count', '10', 'number', 1, '单号码单日最大短信发送条数', NULL, NULL, NULL, NULL),
(610, 'aliyun.sms.access_key_id', '', 'string', 1, '阿里云平台access_key', NULL, NULL, NULL, NULL),
(611, 'aliyun.sms.access_key_secret', '', 'string', 1, '阿里云平台access_key_secret', NULL, NULL, NULL, NULL),
(612, 'aliyun.sms.sign_name', '', 'string', 1, '阿里云短信签名', NULL, NULL, NULL, NULL),
(613, 'aliyun.sms.sms_code_template_code', '', 'string', 1, '阿里云短信模板', NULL, NULL, NULL, NULL);

update sys_params set remark = '是否允许管理员以外的人注册' where param_code = 'server.allow_user_register';

-- 增加手机区域字典
-- 插入固件类型字典类型
delete from `sys_dict_type` where `id` = 102;
INSERT INTO `sys_dict_type` (`id`, `dict_type`, `dict_name`, `remark`, `sort`, `creator`, `create_date`, `updater`, `update_date`) VALUES 
(102, 'MOBILE_AREA', '手机区域', '手机区域字典', 0, 1, NOW(), 1, NOW());

-- 插入固件类型字典数据
delete from `sys_dict_data` where `dict_type_id` = 102;
INSERT INTO `sys_dict_data` (`id`, `dict_type_id`, `dict_label`, `dict_value`, `remark`, `sort`, `creator`, `create_date`, `updater`, `update_date`) VALUES 
(102001, 102, '中国大陆', '+86', '中国大陆', 1, 1, NOW(), 1, NOW()),
(102002, 102, '中国香港', '+852', '中国香港', 2, 1, NOW(), 1, NOW()),
(102003, 102, '中国澳门', '+853', '中国澳门', 3, 1, NOW(), 1, NOW()),
(102004, 102, '中国台湾', '+886', '中国台湾', 4, 1, NOW(), 1, NOW()),
(102005, 102, '美国/加拿大', '+1', '美国/加拿大', 5, 1, NOW(), 1, NOW()),
(102006, 102, '英国', '+44', '英国', 6, 1, NOW(), 1, NOW()),
(102007, 102, '法国', '+33', '法国', 7, 1, NOW(), 1, NOW()),
(102008, 102, '意大利', '+39', '意大利', 8, 1, NOW(), 1, NOW()),
(102009, 102, '德国', '+49', '德国', 9, 1, NOW(), 1, NOW()),
(102010, 102, '波兰', '+48', '波兰', 10, 1, NOW(), 1, NOW()),
(102011, 102, '瑞士', '+41', '瑞士', 11, 1, NOW(), 1, NOW()),
(102012, 102, '西班牙', '+34', '西班牙', 12, 1, NOW(), 1, NOW()),
(102013, 102, '丹麦', '+45', '丹麦', 13, 1, NOW(), 1, NOW()),
(102014, 102, '马来西亚', '+60', '马来西亚', 14, 1, NOW(), 1, NOW()),
(102015, 102, '澳大利亚', '+61', '澳大利亚', 15, 1, NOW(), 1, NOW()),
(102016, 102, '印度尼西亚', '+62', '印度尼西亚', 16, 1, NOW(), 1, NOW()),
(102017, 102, '菲律宾', '+63', '菲律宾', 17, 1, NOW(), 1, NOW()),
(102018, 102, '新西兰', '+64', '新西兰', 18, 1, NOW(), 1, NOW()),
(102019, 102, '新加坡', '+65', '新加坡', 19, 1, NOW(), 1, NOW()),
(102020, 102, '泰国', '+66', '泰国', 20, 1, NOW(), 1, NOW()),
(102021, 102, '日本', '+81', '日本', 21, 1, NOW(), 1, NOW()),
(102022, 102, '韩国', '+82', '韩国', 22, 1, NOW(), 1, NOW()),
(102023, 102, '越南', '+84', '越南', 23, 1, NOW(), 1, NOW()),
(102024, 102, '印度', '+91', '印度', 24, 1, NOW(), 1, NOW()),
(102025, 102, '巴基斯坦', '+92', '巴基斯坦', 25, 1, NOW(), 1, NOW()),
(102026, 102, '尼日利亚', '+234', '尼日利亚', 26, 1, NOW(), 1, NOW()),
(102027, 102, '孟加拉国', '+880', '孟加拉国', 27, 1, NOW(), 1, NOW()),
(102028, 102, '沙特阿拉伯', '+966', '沙特阿拉伯', 28, 1, NOW(), 1, NOW()),
(102029, 102, '阿联酋', '+971', '阿联酋', 29, 1, NOW(), 1, NOW()),
(102030, 102, '巴西', '+55', '巴西', 30, 1, NOW(), 1, NOW()),
(102031, 102, '墨西哥', '+52', '墨西哥', 31, 1, NOW(), 1, NOW()),
(102032, 102, '智利', '+56', '智利', 32, 1, NOW(), 1, NOW()),
(102033, 102, '阿根廷', '+54', '阿根廷', 33, 1, NOW(), 1, NOW()),
(102034, 102, '埃及', '+20', '埃及', 34, 1, NOW(), 1, NOW()),
(102035, 102, '南非', '+27', '南非', 35, 1, NOW(), 1, NOW()),
(102036, 102, '肯尼亚', '+254', '肯尼亚', 36, 1, NOW(), 1, NOW()),
(102037, 102, '坦桑尼亚', '+255', '坦桑尼亚', 37, 1, NOW(), 1, NOW()),
(102038, 102, '哈萨克斯坦', '+7', '哈萨克斯坦', 38, 1, NOW(), 1, NOW());



-- =====================================================
-- From file: 202505201744.sql
-- =====================================================
-- 更新ai_model_provider的fields字段，将type为dict的改为string
update ai_model_provider set fields = replace(fields, '"type": "dict"', '"type": "string"') where id not in ('SYSTEM_LLM_fastgpt', 'SYSTEM_TTS_custom');
update ai_model_provider set fields = replace(fields, '"type":"dict"', '"type": "string"') where id not in ('SYSTEM_LLM_fastgpt', 'SYSTEM_TTS_custom');


-- =====================================================
-- From file: 202505271414.sql
-- =====================================================
-- 本地短期记忆配置可以设置独立的LLM
update `ai_model_provider` set fields =  '[{"key":"llm","label":"LLM模型","type":"string"}]' where  id = 'SYSTEM_Memory_mem_local_short';
update `ai_model_config` set config_json =  '{\"type\": \"mem_local_short\", \"llm\": \"LLM_ChatGLMLLM\"}' where  id = 'Memory_mem_local_short';

-- 增加火山双流式TTS供应器和模型配置
delete from `ai_model_provider` where id = 'SYSTEM_TTS_HSDSTTS';
INSERT INTO `ai_model_provider` (`id`, `model_type`, `provider_code`, `name`, `fields`, `sort`, `creator`, `create_date`, `updater`, `update_date`) VALUES
('SYSTEM_TTS_HSDSTTS', 'TTS', 'huoshan_double_stream', '火山双流式语音合成', '[{"key":"ws_url","label":"WebSocket地址","type":"string"},{"key":"appid","label":"应用ID","type":"string"},{"key":"access_token","label":"访问令牌","type":"string"},{"key":"resource_id","label":"资源ID","type":"string"},{"key":"speaker","label":"默认音色","type":"string"}]', 13, 1, NOW(), 1, NOW());

delete from `ai_model_config` where id = 'TTS_HuoshanDoubleStreamTTS';
INSERT INTO `ai_model_config` VALUES ('TTS_HuoshanDoubleStreamTTS', 'TTS', 'HuoshanDoubleStreamTTS', '火山双流式语音合成', 0, 1, '{\"type\": \"huoshan_double_stream\", \"ws_url\": \"wss://openspeech.bytedance.com/api/v3/tts/bidirection\", \"appid\": \"你的火山引擎语音合成服务appid\", \"access_token\": \"你的火山引擎语音合成服务access_token\", \"resource_id\": \"volc.service_type.10029\", \"speaker\": \"zh_female_wanwanxiaohe_moon_bigtts\"}', NULL, NULL, 16, NULL, NULL, NULL, NULL);

-- 火山双流式TT模型配置说明文档
UPDATE `ai_model_config` SET 
`doc_link` = 'https://console.volcengine.com/speech/service/10007',
`remark` = '火山引擎语音合成服务配置说明：
1. 访问 https://www.volcengine.com/ 注册并开通火山引擎账号
2. 访问 https://console.volcengine.com/speech/service/10007 开通语音合成大模型，购买音色
3. 在页面底部获取appid和access_token
5. 资源ID固定为：volc.service_type.10029（大模型语音合成及混音）
6. 填入配置文件中' WHERE `id` = 'TTS_HuoshanDoubleStreamTTS';


-- 添加火山双流式TTS音色
delete from `ai_tts_voice` where tts_model_id = 'TTS_HuoshanDoubleStreamTTS';
INSERT INTO `ai_tts_voice` VALUES ('TTS_HuoshanDoubleStreamTTS_0001', 'TTS_HuoshanDoubleStreamTTS', '爽快思思/Skye', 'zh_female_shuangkuaisisi_moon_bigtts', '中文、英文', 'https://lf3-static.bytednsdoc.com/obj/eden-cn/lm_hz_ihsph/ljhwZthlaukjlkulzlp/portal/bigtts/Skye.mp3', NULL, 1, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_HuoshanDoubleStreamTTS_0002', 'TTS_HuoshanDoubleStreamTTS', '温暖阿虎/Alvin', 'zh_male_wennuanahu_moon_bigtts', '中文、英文', 'https://lf3-static.bytednsdoc.com/obj/eden-cn/lm_hz_ihsph/ljhwZthlaukjlkulzlp/portal/bigtts/Alvin.mp3', NULL, 2, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_HuoshanDoubleStreamTTS_0003', 'TTS_HuoshanDoubleStreamTTS', '少年梓辛/Brayan', 'zh_male_shaonianzixin_moon_bigtts', '中文、英文', 'https://lf3-static.bytednsdoc.com/obj/eden-cn/lm_hz_ihsph/ljhwZthlaukjlkulzlp/portal/bigtts/Brayan.mp3', NULL, 3, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_HuoshanDoubleStreamTTS_0004', 'TTS_HuoshanDoubleStreamTTS', '邻家女孩', 'zh_female_linjianvhai_moon_bigtts', 'Chinese', 'https://lf3-static.bytednsdoc.com/obj/eden-cn/lm_hz_ihsph/ljhwZthlaukjlkulzlp/portal/bigtts/%E9%82%BB%E5%AE%B6%E5%A5%B3%E5%AD%A9.mp3', NULL, 4, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_HuoshanDoubleStreamTTS_0005', 'TTS_HuoshanDoubleStreamTTS', '渊博小叔', 'zh_male_yuanboxiaoshu_moon_bigtts', 'Chinese', 'https://lf3-static.bytednsdoc.com/obj/eden-cn/lm_hz_ihsph/ljhwZthlaukjlkulzlp/portal/bigtts/%E6%B8%8A%E5%8D%9A%E5%B0%8F%E5%8F%94.mp3', NULL, 5, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_HuoshanDoubleStreamTTS_0006', 'TTS_HuoshanDoubleStreamTTS', '阳光青年', 'zh_male_yangguangqingnian_moon_bigtts', 'Chinese', 'https://lf3-static.bytednsdoc.com/obj/eden-cn/lm_hz_ihsph/ljhwZthlaukjlkulzlp/portal/bigtts/%E9%98%B3%E5%85%89%E9%9D%92%E5%B9%B4.mp3', NULL, 6, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_HuoshanDoubleStreamTTS_0007', 'TTS_HuoshanDoubleStreamTTS', '京腔侃爷/Harmony', 'zh_male_jingqiangkanye_moon_bigtts', '中文、英文', 'https://lf3-static.bytednsdoc.com/obj/eden-cn/lm_hz_ihsph/ljhwZthlaukjlkulzlp/portal/bigtts/Harmony.mp3', NULL, 7, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_HuoshanDoubleStreamTTS_0008', 'TTS_HuoshanDoubleStreamTTS', '湾湾小何', 'zh_female_wanwanxiaohe_moon_bigtts', 'Chinese', 'https://lf3-static.bytednsdoc.com/obj/eden-cn/lm_hz_ihsph/ljhwZthlaukjlkulzlp/portal/bigtts/%E6%B9%BE%E6%B9%BE%E5%B0%8F%E4%BD%95.mp3', NULL, 8, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_HuoshanDoubleStreamTTS_0009', 'TTS_HuoshanDoubleStreamTTS', '湾区大叔', 'zh_female_wanqudashu_moon_bigtts', 'Chinese', 'https://lf3-static.bytednsdoc.com/obj/eden-cn/lm_hz_ihsph/ljhwZthlaukjlkulzlp/portal/bigtts/%E6%B9%BE%E5%8C%BA%E5%A4%A7%E5%8F%94.mp3', NULL, 9, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_HuoshanDoubleStreamTTS_0010', 'TTS_HuoshanDoubleStreamTTS', '呆萌川妹', 'zh_female_daimengchuanmei_moon_bigtts', 'Chinese', 'https://lf3-static.bytednsdoc.com/obj/eden-cn/lm_hz_ihsph/ljhwZthlaukjlkulzlp/portal/bigtts/%E5%91%86%E8%90%8C%E5%B7%9D%E5%A6%B9.mp3', NULL, 10, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_HuoshanDoubleStreamTTS_0011', 'TTS_HuoshanDoubleStreamTTS', '广州德哥', 'zh_male_guozhoudege_moon_bigtts', 'Chinese', 'https://lf3-static.bytednsdoc.com/obj/eden-cn/lm_hz_ihsph/ljhwZthlaukjlkulzlp/portal/bigtts/%E5%B9%BF%E5%B7%9E%E5%BE%B7%E5%93%A5.mp3', NULL, 11, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_HuoshanDoubleStreamTTS_0012', 'TTS_HuoshanDoubleStreamTTS', '北京小爷', 'zh_male_beijingxiaoye_moon_bigtts', 'Chinese', 'https://lf3-static.bytednsdoc.com/obj/eden-cn/lm_hz_ihsph/ljhwZthlaukjlkulzlp/portal/bigtts/%E5%8C%97%E4%BA%AC%E5%B0%8F%E7%88%B7.mp3', NULL, 12, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_HuoshanDoubleStreamTTS_0013', 'TTS_HuoshanDoubleStreamTTS', '浩宇小哥', 'zh_male_haoyuxiaoge_moon_bigtts', 'Chinese', 'https://lf3-static.bytednsdoc.com/obj/eden-cn/lm_hz_ihsph/ljhwZthlaukjlkulzlp/portal/bigtts/%E6%B5%A9%E5%AE%87%E5%B0%8F%E5%93%A5.mp3', NULL, 13, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_HuoshanDoubleStreamTTS_0014', 'TTS_HuoshanDoubleStreamTTS', '广西远舟', 'zh_male_guangxiyuanzhou_moon_bigtts', 'Chinese', 'https://lf3-static.bytednsdoc.com/obj/eden-cn/lm_hz_ihsph/ljhwZthlaukjlkulzlp/portal/bigtts/%E5%B9%BF%E8%A5%BF%E8%BF%9C%E8%88%9F.mp3', NULL, 14, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_HuoshanDoubleStreamTTS_0015', 'TTS_HuoshanDoubleStreamTTS', '妹坨洁儿', 'zh_female_meituojieer_moon_bigtts', 'Chinese', 'https://lf3-static.bytednsdoc.com/obj/eden-cn/lm_hz_ihsph/ljhwZthlaukjlkulzlp/portal/bigtts/%E5%A6%B9%E5%9D%A8%E6%B4%81%E5%84%BF.mp3', NULL, 15, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_HuoshanDoubleStreamTTS_0016', 'TTS_HuoshanDoubleStreamTTS', '豫州子轩', 'zh_male_yuzhouzixuan_moon_bigtts', 'Chinese', 'https://lf3-static.bytednsdoc.com/obj/eden-cn/lm_hz_ihsph/ljhwZthlaukjlkulzlp/portal/bigtts/%E8%B1%AB%E5%B7%9E%E5%AD%90%E8%BD%A9.mp3', NULL, 16, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_HuoshanDoubleStreamTTS_0017', 'TTS_HuoshanDoubleStreamTTS', '高冷御姐', 'zh_female_gaolengyujie_moon_bigtts', 'Chinese', 'https://lf3-static.bytednsdoc.com/obj/eden-cn/lm_hz_ihsph/ljhwZthlaukjlkulzlp/portal/bigtts/%E9%AB%98%E5%86%B7%E5%BE%A1%E5%A7%90.mp3', NULL, 17, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_HuoshanDoubleStreamTTS_0018', 'TTS_HuoshanDoubleStreamTTS', '傲娇霸总', 'zh_male_aojiaobazong_moon_bigtts', 'Chinese', 'https://lf3-static.bytednsdoc.com/obj/eden-cn/lm_hz_ihsph/ljhwZthlaukjlkulzlp/portal/bigtts/%E5%82%B2%E5%A8%87%E9%9C%B8%E6%80%BB.mp3', NULL, 18, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_HuoshanDoubleStreamTTS_0019', 'TTS_HuoshanDoubleStreamTTS', '魅力女友', 'zh_female_meilinvyou_moon_bigtts', 'Chinese', 'https://lf3-static.bytednsdoc.com/obj/eden-cn/lm_hz_ihsph/ljhwZthlaukjlkulzlp/portal/bigtts/%E9%AD%85%E5%8A%9B%E5%A5%B3%E5%8F%8B.mp3', NULL, 19, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_HuoshanDoubleStreamTTS_0020', 'TTS_HuoshanDoubleStreamTTS', '深夜播客', 'zh_male_shenyeboke_moon_bigtts', 'Chinese', 'https://lf3-static.bytednsdoc.com/obj/eden-cn/lm_hz_ihsph/ljhwZthlaukjlkulzlp/portal/bigtts/%E6%B7%B1%E5%A4%9C%E6%92%AD%E5%AE%A2.mp3', NULL, 20, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_HuoshanDoubleStreamTTS_0021', 'TTS_HuoshanDoubleStreamTTS', '柔美女友', 'zh_female_sajiaonvyou_moon_bigtts', 'Chinese', 'https://lf3-static.bytednsdoc.com/obj/eden-cn/lm_hz_ihsph/ljhwZthlaukjlkulzlp/portal/bigtts/%E6%9F%94%E7%BE%8E%E5%A5%B3%E5%8F%8B.mp3', NULL, 21, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_HuoshanDoubleStreamTTS_0022', 'TTS_HuoshanDoubleStreamTTS', '撒娇学妹', 'zh_female_yuanqinvyou_moon_bigtts', 'Chinese', 'https://lf3-static.bytednsdoc.com/obj/eden-cn/lm_hz_ihsph/ljhwZthlaukjlkulzlp/portal/bigtts/%E6%92%92%E5%A8%87%E5%AD%A6%E5%A6%B9.mp3', NULL, 22, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_HuoshanDoubleStreamTTS_0023', 'TTS_HuoshanDoubleStreamTTS', 'かずね（和音）', 'multi_male_jingqiangkanye_moon_bigtts', '日语、西语', 'https://lf3-static.bytednsdoc.com/obj/eden-cn/lm_hz_ihsph/ljhwZthlaukjlkulzlp/portal/bigtts/Javier.wav', NULL, 23, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_HuoshanDoubleStreamTTS_0024', 'TTS_HuoshanDoubleStreamTTS', 'はるこ（晴子）', 'multi_female_shuangkuaisisi_moon_bigtts', '日语、西语', 'https://lf3-static.bytednsdoc.com/obj/eden-cn/lm_hz_ihsph/ljhwZthlaukjlkulzlp/portal/bigtts/Esmeralda.mp3', NULL, 24, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_HuoshanDoubleStreamTTS_0025', 'TTS_HuoshanDoubleStreamTTS', 'あけみ（朱美）', 'multi_female_gaolengyujie_moon_bigtts', '日语', 'https://lf3-static.bytednsdoc.com/obj/eden-cn/lm_hz_ihsph/ljhwZthlaukjlkulzlp/portal/bigtts/%E6%9C%B1%E7%BE%8E.mp3', NULL, 25, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_HuoshanDoubleStreamTTS_0026', 'TTS_HuoshanDoubleStreamTTS', 'ひろし（広志）', 'multi_male_wanqudashu_moon_bigtts', '日语、西语', 'https://lf3-static.bytednsdoc.com/obj/eden-cn/lm_hz_ihsph/ljhwZthlaukjlkulzlp/portal/bigtts/Roberto.wav', NULL, 26, NULL, NULL, NULL, NULL);



-- =====================================================
-- From file: 202505292203.sql
-- =====================================================
-- ===============================
-- 一、在ai_model_provider中插入plugin 记录
-- ===============================
START TRANSACTION;


-- intent_llm和function_call不设置函数列表
update `ai_model_provider` set fields =  '[{"key":"llm","label":"LLM模型","type":"string"}]' where  id = 'SYSTEM_Intent_intent_llm';
update `ai_model_provider` set fields =  '[]' where  id = 'SYSTEM_Intent_function_call';
update `ai_model_config` set config_json =  '{\"type\": \"intent_llm\", \"llm\": \"LLM_ChatGLMLLM\"}' where  id = 'Intent_intent_llm';
UPDATE `ai_model_config` SET config_json = '{\"type\": \"function_call\"}' WHERE id = 'Intent_function_call';


delete from ai_model_provider where model_type = 'Plugin';
-- 1. 天气查询
INSERT INTO ai_model_provider (id, model_type, provider_code, name, fields,
                               sort, creator, create_date, updater, update_date)
VALUES ('SYSTEM_PLUGIN_WEATHER',
        'Plugin',
        'get_weather',
        '天气查询',
        JSON_ARRAY(
                JSON_OBJECT(
                        'key', 'api_key',
                        'type', 'string',
                        'label', '天气插件 API 密钥',
                        'default', (SELECT param_value FROM sys_params WHERE param_code = 'plugins.get_weather.api_key')
                ),
                JSON_OBJECT(
                        'key', 'default_location',
                        'type', 'string',
                        'label', '默认查询城市',
                        'default',
                        (SELECT param_value FROM sys_params WHERE param_code = 'plugins.get_weather.default_location')
                ),
                JSON_OBJECT(
                        'key', 'api_host',
                        'type', 'string',
                        'label', '开发者 API Host',
                        'default',
                        (SELECT param_value FROM sys_params WHERE param_code = 'plugins.get_weather.api_host')
                )
        ),
        10, 0, NOW(), 0, NOW());

-- 6. 本地播放音乐
INSERT INTO ai_model_provider (id, model_type, provider_code, name, fields,
                               sort, creator, create_date, updater, update_date)
VALUES ('SYSTEM_PLUGIN_MUSIC',
        'Plugin',
        'play_music',
        '服务器音乐播放',
        JSON_ARRAY(),
        20, 0, NOW(), 0, NOW());

-- 2. 新闻订阅
INSERT INTO ai_model_provider (id, model_type, provider_code, name, fields,
                               sort, creator, create_date, updater, update_date)
VALUES ('SYSTEM_PLUGIN_NEWS_CHINANEWS',
        'Plugin',
        'get_news_from_chinanews',
        '中新网新闻',
        JSON_ARRAY(
                JSON_OBJECT(
                        'key', 'default_rss_url',
                        'type', 'string',
                        'label', '默认 RSS 源',
                        'default',
                        (SELECT param_value FROM sys_params WHERE param_code = 'plugins.get_news.default_rss_url')
                ),
                JSON_OBJECT(
                        'key', 'society_rss_url',
                        'type', 'string',
                        'label', '社会新闻 RSS 地址',
                        'default',
                        'https://www.chinanews.com.cn/rss/society.xml'
                ),
                JSON_OBJECT(
                        'key', 'world_rss_url',
                        'type', 'string',
                        'label', '国际新闻 RSS 地址',
                        'default',
                        'https://www.chinanews.com.cn/rss/world.xml'
                ),
                JSON_OBJECT(
                        'key', 'finance_rss_url',
                        'type', 'string',
                        'label', '财经新闻 RSS 地址',
                        'default',
                        'https://www.chinanews.com.cn/rss/finance.xml'
                )
        ),
        30, 0, NOW(), 0, NOW());

-- 3. 新闻订阅
INSERT INTO ai_model_provider (id, model_type, provider_code, name, fields,
                               sort, creator, create_date, updater, update_date)
VALUES ('SYSTEM_PLUGIN_NEWS_NEWSNOW',
        'Plugin',
        'get_news_from_newsnow',
        'newsnow新闻聚合',
        JSON_ARRAY(
                JSON_OBJECT(
                        'key', 'url',
                        'type', 'string',
                        'label', '接口地址',
                        'default',
                        'https://newsnow.busiyi.world/api/s?id='
                )
        ),
        40, 0, NOW(), 0, NOW());


-- 4. HomeAssistant 状态查询
INSERT INTO ai_model_provider (id, model_type, provider_code, name, fields,
                               sort, creator, create_date, updater, update_date)
VALUES ('SYSTEM_PLUGIN_HA_GET_STATE',
        'Plugin',
        'hass_get_state',
        'HomeAssistant设备状态查询',
        JSON_ARRAY(
                JSON_OBJECT(
                        'key', 'base_url',
                        'type', 'string',
                        'label', 'HA 服务器地址',
                        'default',
                        (SELECT param_value FROM sys_params WHERE param_code = 'plugins.home_assistant.base_url')
                ),
                JSON_OBJECT(
                        'key', 'api_key',
                        'type', 'string',
                        'label', 'HA API 访问令牌',
                        'default',
                        (SELECT param_value FROM sys_params WHERE param_code = 'plugins.home_assistant.api_key')
                ),
                JSON_OBJECT(
                        'key', 'devices',
                        'type', 'array',
                        'label', '设备列表（名称,实体ID;…）',
                        'default',
                        (SELECT param_value FROM sys_params WHERE param_code = 'plugins.home_assistant.devices')
                )
        ),
        50, 0, NOW(), 0, NOW());

-- 5. HomeAssistant 状态写入
INSERT INTO ai_model_provider (id, model_type, provider_code, name, fields,
                               sort, creator, create_date, updater, update_date)
VALUES ('SYSTEM_PLUGIN_HA_SET_STATE',
        'Plugin',
        'hass_set_state',
        'HomeAssistant设备状态修改',
        JSON_ARRAY(),
        60, 0, NOW(), 0, NOW());

-- 5. HomeAssistant 音乐播放
INSERT INTO ai_model_provider (id, model_type, provider_code, name, fields,
                               sort, creator, create_date, updater, update_date)
VALUES ('SYSTEM_PLUGIN_HA_PLAY_MUSIC',
        'Plugin',
        'hass_play_music',
        'HomeAssistant音乐播放',
        JSON_ARRAY(),
        70, 0, NOW(), 0, NOW());


-- ===============================
-- 二、删除sys_params中旧的plugins.*参数
-- ===============================
DELETE
FROM sys_params
WHERE param_code LIKE 'plugins.%';


-- ===============================
-- 三、添加智能体插件id字段
-- ===============================
CREATE TABLE IF NOT EXISTS ai_agent_plugin_mapping
(
    id         BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT 'Primary key',
    agent_id   VARCHAR(32) NOT NULL COMMENT '智能体ID',
    plugin_id  VARCHAR(32) NOT NULL COMMENT '插件ID',
    param_info JSON        NOT NULL COMMENT '参数信息',
    UNIQUE KEY uk_agent_provider (agent_id, plugin_id)
) COMMENT 'Agent与插件的唯一映射表';


COMMIT;




-- =====================================================
-- From file: 202506010920.sql
-- =====================================================
-- VLLM模型供应器
delete from `ai_model_provider` where id = 'SYSTEM_VLLM_openai';
INSERT INTO `ai_model_provider` (`id`, `model_type`, `provider_code`, `name`, `fields`, `sort`, `creator`, `create_date`, `updater`, `update_date`) VALUES
('SYSTEM_VLLM_openai', 'VLLM', 'openai', 'OpenAI接口', '[{"key":"base_url","label":"基础URL","type":"string"},{"key":"model_name","label":"Model name","type":"string"},{"key":"api_key","label":"API密钥","type":"string"}]', 9, 1, NOW(), 1, NOW());

-- VLLM模型配置
delete from `ai_model_config` where id = 'VLLM_ChatGLMVLLM';
INSERT INTO `ai_model_config` VALUES ('VLLM_ChatGLMVLLM', 'VLLM', 'ChatGLMVLLM', '智谱视觉AI', 1, 1, '{\"type\": \"openai\", \"model_name\": \"glm-4v-flash\", \"base_url\": \"https://open.bigmodel.cn/api/paas/v4/\", \"api_key\": \"你的api_key\"}', NULL, NULL, 1, NULL, NULL, NULL, NULL);

-- 更新文档
UPDATE `ai_model_config` SET 
`doc_link` = 'https://bigmodel.cn/usercenter/proj-mgmt/apikeys',
`remark` = '智谱视觉AI配置说明：
1. 访问 https://bigmodel.cn/usercenter/proj-mgmt/apikeys
2. 注册并获取API密钥
3. 填入配置文件中' WHERE `id` = 'VLLM_ChatGLMVLLM';


-- 添加参数
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (113, 'server.http_port', '8003', 'number', 1, 'http服务的端口，用于启动视觉分析接口');
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (114, 'server.vision_explain', 'null', 'string', 1, '视觉分析接口地址，用于下发到设备，多个用;分隔');

-- 智能体表增加VLLM模型配置
ALTER TABLE `ai_agent` 
ADD COLUMN `vllm_model_id` varchar(32) NULL DEFAULT 'VLLM_ChatGLMVLLM' COMMENT '视觉模型标识' AFTER `llm_model_id`;

-- 智能体模版表增加VLLM模型配置
ALTER TABLE `ai_agent_template` 
ADD COLUMN `vllm_model_id` varchar(32) NULL DEFAULT 'VLLM_ChatGLMVLLM' COMMENT '视觉模型标识' AFTER `llm_model_id`;


-- =====================================================
-- From file: 202506031639.sql
-- =====================================================
-- VLLM模型供应器
delete from `ai_model_provider` where id = 'SYSTEM_ASR_DoubaoStreamASR';
INSERT INTO `ai_model_provider` (`id`, `model_type`, `provider_code`, `name`, `fields`, `sort`, `creator`, `create_date`, `updater`, `update_date`) VALUES
('SYSTEM_ASR_DoubaoStreamASR', 'ASR', 'doubao_stream', '火山引擎语音识别(流式)', '[{"key":"appid","label":"应用ID","type":"string"},{"key":"access_token","label":"访问令牌","type":"string"},{"key":"cluster","label":"集群","type":"string"},{"key":"boosting_table_name","label":"热词文件名称","type":"string"},{"key":"correct_table_name","label":"替换词文件名称","type":"string"},{"key":"output_dir","label":"输出目录","type":"string"}]', 3, 1, NOW(), 1, NOW());


-- VLLM模型配置
delete from `ai_model_config` where id = 'ASR_DoubaoStreamASR';
INSERT INTO `ai_model_config` VALUES ('ASR_DoubaoStreamASR', 'ASR', 'DoubaoStreamASR', '豆包语音识别(流式)', 0, 1, '{\"type\": \"doubao_stream\", \"appid\": \"\", \"access_token\": \"\", \"cluster\": \"volcengine_input_common\", \"output_dir\": \"tmp/\"}', NULL, NULL, 3, NULL, NULL, NULL, NULL);


-- 更新豆包ASR配置说明
UPDATE `ai_model_config` SET 
`doc_link` = 'https://console.volcengine.com/speech/app',
`remark` = '豆包ASR配置说明：
1. 豆包ASR和豆包(流式)ASR的区别是：豆包ASR是按次收费，豆包(流式)ASR是按时收费
2. 一般来说按次收费的更便宜，但是豆包(流式)ASR使用了大模型技术，效果更好
3. 需要在火山引擎控制台创建应用并获取appid和access_token
4. 支持中文语音识别
5. 需要网络连接
6. 输出文件保存在tmp/目录
申请步骤：
1. 访问 https://console.volcengine.com/speech/app
2. 创建新应用
3. 获取appid和access_token
4. 填入配置文件中
如需设置热词，请参考：https://www.volcengine.com/docs/6561/155738
' WHERE `id` = 'ASR_DoubaoASR';

UPDATE `ai_model_config` SET 
`doc_link` = 'https://console.volcengine.com/speech/app',
`remark` = '豆包ASR配置说明：
1. 豆包ASR和豆包(流式)ASR的区别是：豆包ASR是按次收费，豆包(流式)ASR是按时收费
2. 一般来说按次收费的更便宜，但是豆包(流式)ASR使用了大模型技术，效果更好
3. 需要在火山引擎控制台创建应用并获取appid和access_token
4. 支持中文语音识别
5. 需要网络连接
6. 输出文件保存在tmp/目录
申请步骤：
1. 访问 https://console.volcengine.com/speech/app
2. 创建新应用
3. 获取appid和access_token
4. 填入配置文件中
如需设置热词，请参考：https://www.volcengine.com/docs/6561/155738
' WHERE `id` = 'ASR_DoubaoStreamASR';



-- =====================================================
-- From file: 202506032232.sql
-- =====================================================
-- VLLM模型配置
delete from `ai_model_config` where id = 'VLLM_QwenVLVLLM';
INSERT INTO `ai_model_config` VALUES ('VLLM_QwenVLVLLM', 'VLLM', 'QwenVLVLLM', '千问视觉模型', 0, 1, '{\"type\": \"openai\", \"model_name\": \"qwen2.5-vl-3b-instruct\", \"base_url\": \"https://dashscope.aliyuncs.com/compatible-mode/v1\", \"api_key\": \"你的api_key\"}', NULL, NULL, 2, NULL, NULL, NULL, NULL);

-- 更新文档
UPDATE `ai_model_config` SET 
`doc_link` = 'https://bailian.console.aliyun.com/?tab=api#/api/?type=model&url=https%3A%2F%2Fhelp.aliyun.com%2Fdocument_detail%2F2845564.html&renderType=iframe',
`remark` = '千问视觉模型配置说明：
1. 访问 https://bailian.console.aliyun.com/?tab=model#/api-key
2. 注册并获取API密钥
3. 填入配置文件中' WHERE `id` = 'VLLM_QwenVLVLLM';

-- 删除参数，这两个参数已挪至python配置文件
delete from `sys_params` where id  in (113,114);



-- =====================================================
-- From file: 202506051538.sql
-- =====================================================
-- 增加LinkeraiTTS供应器和模型配置
delete from `ai_model_provider` where id = 'SYSTEM_TTS_LinkeraiTTS';
INSERT INTO `ai_model_provider` (`id`, `model_type`, `provider_code`, `name`, `fields`, `sort`, `creator`, `create_date`, `updater`, `update_date`) VALUES
('SYSTEM_TTS_LinkeraiTTS', 'TTS', 'linkerai', 'Linkerai语音合成', '[{"key":"api_url","label":"API地址","type":"string"},{"key":"audio_format","label":"音频格式","type":"string"},{"key":"access_token","label":"访问令牌","type":"string"},{"key":"voice","label":"默认音色","type":"string"}]', 14, 1, NOW(), 1, NOW());

delete from `ai_model_config` where id = 'TTS_LinkeraiTTS';
INSERT INTO `ai_model_config` VALUES ('TTS_LinkeraiTTS', 'TTS', 'LinkeraiTTS', 'Linkerai语音合成', 0, 1, '{\"type\": \"linkerai\", \"api_url\": \"https://tts.linkerai.cn/tts\", \"audio_format\": \"pcm\", \"access_token\": \"U4YdYXVfpwWnk2t5Gp822zWPCuORyeJL\", \"voice\": \"OUeAo1mhq6IBExi\"}', NULL, NULL, 17, NULL, NULL, NULL, NULL);

-- LinkeraiTTS模型配置说明文档
UPDATE `ai_model_config` SET 
`doc_link` = 'https://tts.linkerai.cn/docs',
`remark` = 'Linkerai语音合成服务配置说明：
1. 访问 https://linkerai.cn 注册并获取访问令牌
2. 默认的access_token供测试使用，请勿用于商业用途
3. 支持声音克隆功能，可自行上传音频，填入voice参数
4. 如果voice参数为空，将使用默认声音' WHERE `id` = 'TTS_LinkeraiTTS';


delete from `ai_tts_voice` where tts_model_id = 'TTS_LinkeraiTTS';
INSERT INTO `ai_tts_voice` VALUES ('TTS_LinkeraiTTS_0001', 'TTS_LinkeraiTTS', '芷若', 'OUeAo1mhq6IBExi', 'Chinese', NULL, NULL, 1, NULL, NULL, NULL, NULL);



-- =====================================================
-- From file: 202506080955.sql
-- =====================================================
-- 智控台开启唤醒词加速
update `sys_params` set param_value = '你好小智;你好小志;小爱同学;你好小鑫;你好小新;小美同学;小龙小龙;喵喵同学;小滨小滨;小冰小冰;嘿你好呀' where param_code = 'wakeup_words';
update `sys_params` set param_value = 'true' where param_code = 'enable_wakeup_words_response_cache';



-- =====================================================
-- From file: 202506091720.sql
-- =====================================================
ALTER TABLE `ai_tts_voice`
ADD COLUMN `reference_audio` VARCHAR(500) DEFAULT NULL COMMENT '参考音频路径' AFTER `remark`,
ADD COLUMN `reference_text` VARCHAR(500) DEFAULT NULL COMMENT '参考文本' AFTER `reference_audio`;



-- =====================================================
-- From file: 202506161101.sql
-- =====================================================
ALTER TABLE ai_agent_plugin_mapping CONVERT TO CHARACTER SET utf8mb4;


-- =====================================================
-- From file: 202506191643.sql
-- =====================================================
-- LLM意图识别配置说明
UPDATE `ai_model_config` SET 
`doc_link` = NULL,
`remark` = 'LLM意图识别配置说明：
1. 使用独立的LLM进行意图识别
2. 默认使用selected_module.LLM的模型
3. 可以配置使用独立的LLM（如免费的ChatGLMLLM）
4. 通用性强，但会增加处理时间
配置说明：
1. 在llm字段中指定使用的LLM模型
2. 如果不指定，则使用selected_module.LLM的模型' WHERE `id` = 'Intent_intent_llm';

-- 函数调用意图识别配置说明
UPDATE `ai_model_config` SET 
`doc_link` = NULL,
`remark` = '函数调用意图识别配置说明：
1. 使用LLM的function_call功能进行意图识别
2. 需要所选择的LLM支持function_call
3. 按需调用工具，处理速度快' WHERE `id` = 'Intent_function_call';


-- =====================================================
-- From file: 202506251620.sql
-- =====================================================
-- 更新现有的 get_news_from_newsnow 插件配置
UPDATE ai_model_provider 
SET fields = JSON_ARRAY(
    JSON_OBJECT(
        'key', 'url',
        'type', 'string',
        'label', '接口地址',
        'default', 'https://newsnow.busiyi.world/api/s?id='
    ),
    JSON_OBJECT(
        'key', 'news_sources',
        'type', 'string',
        'label', '新闻源配置',
        'default', '澎湃新闻;百度热搜;财联社'
    )
)
WHERE provider_code = 'get_news_from_newsnow' 
AND model_type = 'Plugin'; 


-- =====================================================
-- From file: 202506261637.sql
-- =====================================================
delete from `sys_params` where id = 113;
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark) VALUES (113, 'server.mcp_endpoint', 'null', 'string', 1, 'mcp接入点地址');


-- =====================================================
-- From file: 202507031602.sql
-- =====================================================
-- 添加声纹接口地址参数配置
delete from `sys_params` where id = 114;
INSERT INTO `sys_params` (id, param_code, param_value, value_type, param_type, remark)
VALUES (114, 'server.voice_print', 'null', 'string', 1, '声纹接口地址');


-- =====================================================
-- From file: 202507041018.sql
-- =====================================================
DROP TABLE IF EXISTS ai_agent_voice_print;
create table ai_agent_voice_print (
  id varchar(32) NOT NULL COMMENT '声纹ID',
  agent_id varchar(32)  NOT NULL COMMENT '关联的智能体ID',
  source_name varchar(50)  NOT NULL COMMENT '声纹来源的人的姓名',
  introduce varchar(200) COMMENT '描述声纹来源的这个人',
  create_date DATETIME COMMENT 'Create time',
  creator bigint COMMENT 'Creator',
  update_date DATETIME COMMENT '修改时间',
  updater bigint COMMENT '修改者',
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='智能体声纹表'


-- =====================================================
-- From file: 202507071130.sql
-- =====================================================
-- 添加阿里云流式ASR供应器
delete from `ai_model_provider` where id = 'SYSTEM_ASR_AliyunStreamASR';
INSERT INTO `ai_model_provider` (`id`, `model_type`, `provider_code`, `name`, `fields`, `sort`, `creator`, `create_date`, `updater`, `update_date`) VALUES
('SYSTEM_ASR_AliyunStreamASR', 'ASR', 'aliyun_stream', '阿里云语音识别(流式)', '[{"key":"appkey","label":"应用AppKey","type":"string"},{"key":"token","label":"临时Token","type":"string"},{"key":"access_key_id","label":"AccessKey ID","type":"string"},{"key":"access_key_secret","label":"AccessKey Secret","type":"string"},{"key":"host","label":"服务地址","type":"string"},{"key":"max_sentence_silence","label":"断句检测时间","type":"number"},{"key":"output_dir","label":"输出目录","type":"string"}]', 6, 1, NOW(), 1, NOW());

-- 添加阿里云流式ASR模型配置
delete from `ai_model_config` where id = 'ASR_AliyunStreamASR';
INSERT INTO `ai_model_config` VALUES ('ASR_AliyunStreamASR', 'ASR', 'AliyunStreamASR', '阿里云语音识别(流式)', 0, 1, '{\"type\": \"aliyun_stream\", \"appkey\": \"\", \"token\": \"\", \"access_key_id\": \"\", \"access_key_secret\": \"\", \"host\": \"nls-gateway-cn-shanghai.aliyuncs.com\", \"max_sentence_silence\": 800, \"output_dir\": \"tmp/\"}', NULL, NULL, 8, NULL, NULL, NULL, NULL);

-- 更新阿里云流式ASR配置说明
UPDATE `ai_model_config` SET 
`doc_link` = 'https://nls-portal.console.aliyun.com/',
`remark` = '阿里云流式ASR配置说明：
1. 阿里云ASR和阿里云(流式)ASR的区别是：阿里云ASR是一次性识别，阿里云(流式)ASR是实时流式识别
2. 流式ASR具有更低的延迟和更好的实时性，适合语音交互场景
3. 需要在阿里云智能语音交互控制台创建应用并获取认证信息
4. 支持中文实时语音识别，支持标点符号预测和逆文本规范化
5. 需要网络连接，输出文件保存在tmp/目录
申请步骤：
1. 访问 https://nls-portal.console.aliyun.com/ 开通智能语音交互服务
2. 访问 https://nls-portal.console.aliyun.com/applist 创建项目并获取appkey
3. 访问 https://nls-portal.console.aliyun.com/overview 获取临时token（或配置access_key_id和access_key_secret自动获取）
4. 如需动态token管理，建议配置access_key_id和access_key_secret
5. max_sentence_silence参数控制断句检测时间（毫秒），默认800ms
如需了解更多参数配置，请参考：https://help.aliyun.com/zh/isi/developer-reference/real-time-speech-recognition
' WHERE `id` = 'ASR_AliyunStreamASR';



-- =====================================================
-- From file: 202507071530.sql
-- =====================================================
-- 添加阿里云流式TTS供应器
delete from `ai_model_provider` where id = 'SYSTEM_TTS_AliyunStreamTTS';
INSERT INTO `ai_model_provider` (`id`, `model_type`, `provider_code`, `name`, `fields`, `sort`, `creator`, `create_date`, `updater`, `update_date`) VALUES
('SYSTEM_TTS_AliyunStreamTTS', 'TTS', 'aliyun_stream', '阿里云语音合成(流式)', '[{"key":"appkey","label":"应用AppKey","type":"string"},{"key":"token","label":"临时Token","type":"string"},{"key":"access_key_id","label":"AccessKey ID","type":"string"},{"key":"access_key_secret","label":"AccessKey Secret","type":"string"},{"key":"host","label":"服务地址","type":"string"},{"key":"voice","label":"默认音色","type":"string"},{"key":"format","label":"音频格式","type":"string"},{"key":"sample_rate","label":"采样率","type":"number"},{"key":"volume","label":"音量","type":"number"},{"key":"speech_rate","label":"语速","type":"number"},{"key":"pitch_rate","label":"音调","type":"number"},{"key":"output_dir","label":"输出目录","type":"string"}]', 15, 1, NOW(), 1, NOW());

-- 添加阿里云流式TTS模型配置
delete from `ai_model_config` where id = 'TTS_AliyunStreamTTS';
INSERT INTO `ai_model_config` VALUES ('TTS_AliyunStreamTTS', 'TTS', 'AliyunStreamTTS', '阿里云语音合成(流式)', 0, 1, '{\"type\": \"aliyun_stream\", \"appkey\": \"\", \"token\": \"\", \"access_key_id\": \"\", \"access_key_secret\": \"\", \"host\": \"nls-gateway-cn-beijing.aliyuncs.com\", \"voice\": \"longxiaochun\", \"format\": \"pcm\", \"sample_rate\": 16000, \"volume\": 50, \"speech_rate\": 0, \"pitch_rate\": 0, \"output_dir\": \"tmp/\"}', NULL, NULL, 18, NULL, NULL, NULL, NULL);

-- 更新阿里云流式TTS配置说明
UPDATE `ai_model_config` SET 
`doc_link` = 'https://nls-portal.console.aliyun.com/',
`remark` = '阿里云流式TTS配置说明：
1. 阿里云TTS和阿里云(流式)TTS的区别是：阿里云TTS是一次性合成，阿里云(流式)TTS是实时流式合成
2. 流式TTS具有更低的延迟和更好的实时性，适合语音交互场景
3. 需要在阿里云智能语音交互控制台创建应用并获取认证信息
4. 支持CosyVoice大模型音色，音质更加自然
5. 支持实时调节音量、语速、音调等参数
申请步骤：
1. 访问 https://nls-portal.console.aliyun.com/ 开通智能语音交互服务
2. 访问 https://nls-portal.console.aliyun.com/applist 创建项目并获取appkey
3. 访问 https://nls-portal.console.aliyun.com/overview 获取临时token（或配置access_key_id和access_key_secret自动获取）
4. 如需动态token管理，建议配置access_key_id和access_key_secret
5. 可选择北京、上海等不同地域的服务器以优化延迟
6. voice参数支持CosyVoice大模型音色，如longxiaochun、longyueyue等
如需了解更多参数配置，请参考：https://help.aliyun.com/zh/isi/developer-reference/real-time-speech-synthesis
' WHERE `id` = 'TTS_AliyunStreamTTS';

-- 添加阿里云流式TTS音色
delete from `ai_tts_voice` where tts_model_id = 'TTS_AliyunStreamTTS';
-- 温柔女声系列
INSERT INTO `ai_tts_voice` VALUES ('TTS_AliyunStreamTTS_0001', 'TTS_AliyunStreamTTS', '龙小淳-温柔姐姐', 'longxiaochun', '中文及中英文混合', NULL, NULL, NULL, NULL, 1, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_AliyunStreamTTS_0002', 'TTS_AliyunStreamTTS', '龙小夏-温柔女声', 'longxiaoxia', '中文及中英文混合', NULL, NULL, NULL, NULL, 2, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_AliyunStreamTTS_0003', 'TTS_AliyunStreamTTS', '龙玫-温柔女声', 'longmei', '中文及中英文混合', NULL, NULL, NULL, NULL, 3, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_AliyunStreamTTS_0004', 'TTS_AliyunStreamTTS', '龙瑰-温柔女声', 'longgui', '中文及中英文混合', NULL, NULL, NULL, NULL, 4, NULL, NULL, NULL, NULL);
-- 御姐女声系列
INSERT INTO `ai_tts_voice` VALUES ('TTS_AliyunStreamTTS_0005', 'TTS_AliyunStreamTTS', '龙玉-御姐女声', 'longyu', '中文及中英文混合', NULL, NULL, NULL, NULL, 5, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_AliyunStreamTTS_0006', 'TTS_AliyunStreamTTS', '龙娇-御姐女声', 'longjiao', '中文及中英文混合', NULL, NULL, NULL, NULL, 6, NULL, NULL, NULL, NULL);
-- 男声系列
INSERT INTO `ai_tts_voice` VALUES ('TTS_AliyunStreamTTS_0007', 'TTS_AliyunStreamTTS', '龙臣-译制片男声', 'longchen', '中文及中英文混合', NULL, NULL, NULL, NULL, 7, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_AliyunStreamTTS_0008', 'TTS_AliyunStreamTTS', '龙修-青年男声', 'longxiu', '中文及中英文混合', NULL, NULL, NULL, NULL, 8, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_AliyunStreamTTS_0009', 'TTS_AliyunStreamTTS', '龙橙-阳光男声', 'longcheng', '中文及中英文混合', NULL, NULL, NULL, NULL, 9, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_AliyunStreamTTS_0010', 'TTS_AliyunStreamTTS', '龙哲-成熟男声', 'longzhe', '中文及中英文混合', NULL, NULL, NULL, NULL, 10, NULL, NULL, NULL, NULL);
-- 专业播报系列
INSERT INTO `ai_tts_voice` VALUES ('TTS_AliyunStreamTTS_0011', 'TTS_AliyunStreamTTS', 'Bella2.0-新闻女声', 'loongbella', '中文及中英文混合', NULL, NULL, NULL, NULL, 11, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_AliyunStreamTTS_0012', 'TTS_AliyunStreamTTS', 'Stella2.0-飒爽女声', 'loongstella', '中文及中英文混合', NULL, NULL, NULL, NULL, 12, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_AliyunStreamTTS_0013', 'TTS_AliyunStreamTTS', '龙书-新闻男声', 'longshu', '中文及中英文混合', NULL, NULL, NULL, NULL, 13, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_AliyunStreamTTS_0014', 'TTS_AliyunStreamTTS', '龙婧-严肃女声', 'longjing', '中文及中英文混合', NULL, NULL, NULL, NULL, 14, NULL, NULL, NULL, NULL);
-- 特色音色系列
INSERT INTO `ai_tts_voice` VALUES ('TTS_AliyunStreamTTS_0015', 'TTS_AliyunStreamTTS', '龙奇-活泼童声', 'longqi', '中文及中英文混合', NULL, NULL, NULL, NULL, 15, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_AliyunStreamTTS_0016', 'TTS_AliyunStreamTTS', '龙华-活泼女童', 'longhua', '中文及中英文混合', NULL, NULL, NULL, NULL, 16, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_AliyunStreamTTS_0017', 'TTS_AliyunStreamTTS', '龙无-无厘头男声', 'longwu', '中文及中英文混合', NULL, NULL, NULL, NULL, 17, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_AliyunStreamTTS_0018', 'TTS_AliyunStreamTTS', '龙大锤-幽默男声', 'longdachui', '中文及中英文混合', NULL, NULL, NULL, NULL, 18, NULL, NULL, NULL, NULL);
-- 粤语系列
INSERT INTO `ai_tts_voice` VALUES ('TTS_AliyunStreamTTS_0019', 'TTS_AliyunStreamTTS', '龙嘉怡-粤语女声', 'longjiayi', '粤语及粤英混合', NULL, NULL, NULL, NULL, 19, NULL, NULL, NULL, NULL);
INSERT INTO `ai_tts_voice` VALUES ('TTS_AliyunStreamTTS_0020', 'TTS_AliyunStreamTTS', '龙桃-粤语女声', 'longtao', '粤语及粤英混合', NULL, NULL, NULL, NULL, 20, NULL, NULL, NULL, NULL);



-- =====================================================
-- From file: 202507081646.sql
-- =====================================================
-- 智能体声纹添加新字段
ALTER TABLE ai_agent_voice_print
    ADD COLUMN audio_id VARCHAR(32) NOT NULL COMMENT '音频ID';


-- =====================================================
-- From file: 202507101203.sql
-- =====================================================
-- OpenAI ASR模型供应器
delete from `ai_model_provider` where id = 'SYSTEM_ASR_OpenaiASR';
INSERT INTO `ai_model_provider` (`id`, `model_type`, `provider_code`, `name`, `fields`, `sort`, `creator`, `create_date`, `updater`, `update_date`) VALUES
('SYSTEM_ASR_OpenaiASR', 'ASR', 'openai', 'OpenAI语音识别', '[{"key": "base_url", "type": "string", "label": "基础URL"}, {"key": "model_name", "type": "string", "label": "Model name"}, {"key": "api_key", "type": "string", "label": "API密钥"}, {"key": "output_dir", "type": "string", "label": "输出目录"}]', 9, 1, NOW(), 1, NOW());


-- OpenAI ASR模型配置
delete from `ai_model_config` where id = 'ASR_OpenaiASR';
INSERT INTO `ai_model_config` VALUES ('ASR_OpenaiASR', 'ASR', 'OpenaiASR', 'OpenAI语音识别', 0, 1, '{\"type\": \"openai\", \"api_key\": \"\", \"base_url\": \"https://api.openai.com/v1/audio/transcriptions\", \"model_name\": \"gpt-4o-mini-transcribe\", \"output_dir\": \"tmp/\"}', NULL, NULL, 9, NULL, NULL, NULL, NULL);

-- groq ASR模型配置
delete from `ai_model_config` where id = 'ASR_GroqASR';
INSERT INTO `ai_model_config` VALUES ('ASR_GroqASR', 'ASR', 'GroqASR', 'Groq语音识别', 0, 1, '{\"type\": \"openai\", \"api_key\": \"\", \"base_url\": \"https://api.groq.com/openai/v1/audio/transcriptions\", \"model_name\": \"whisper-large-v3-turbo\", \"output_dir\": \"tmp/\"}', NULL, NULL, 10, NULL, NULL, NULL, NULL);


-- 更新OpenAI ASR配置说明
UPDATE `ai_model_config` SET 
`doc_link` = 'https://platform.openai.com/docs/api-reference/audio/createTranscription',
`remark` = 'OpenAI ASR配置说明：
1. 需要在OpenAI开放平台创建组织并获取api_key
2. 支持中、英、日、韩等多种语音识别，具体参考文档https://platform.openai.com/docs/guides/speech-to-text
3. 需要网络连接
4. 输出文件保存在tmp/目录
申请步骤：
**OpenAi ASR申请步骤：**
1.登录OpenAI Platform。https://auth.openai.com/log-in
2.创建api-key  https://platform.openai.com/settings/organization/api-keys
3.模型可以选择gpt-4o-transcribe或GPT-4o mini Transcribe
' WHERE `id` = 'ASR_OpenaiASR';

-- 更新Groq ASR配置说明
UPDATE `ai_model_config` SET 
`doc_link` = 'https://console.groq.com/docs/speech-to-text',
`remark` = 'Groq ASR配置说明：
1.登录groq Console。https://console.groq.com/home
2.创建api-key  https://console.groq.com/keys
3.模型可以选择whisper-large-v3-turbo或whisper-large-v3（distil-whisper-large-v3-en仅支持英语转录）
' WHERE `id` = 'ASR_GroqASR';


-- =====================================================
-- From file: 202508081701.sql
-- =====================================================
-- 添加Index-TTS-vLLM流式TTS供应器
delete from `ai_model_provider` where id = 'SYSTEM_TTS_IndexStreamTTS';
INSERT INTO `ai_model_provider` (`id`, `model_type`, `provider_code`, `name`, `fields`, `sort`, `creator`, `create_date`, `updater`, `update_date`) VALUES
('SYSTEM_TTS_IndexStreamTTS', 'TTS', 'index_stream', 'Index-TTS-vLLM流式语音合成', '[{"key":"api_url","label":"API服务地址","type":"string"},{"key":"voice","label":"默认音色","type":"string"},{"key":"audio_format","label":"音频格式","type":"string"},{"key":"output_dir","label":"输出目录","type":"string"}]', 16, 1, NOW(), 1, NOW());

-- 添加Index-TTS-vLLM流式TTS模型配置
delete from `ai_model_config` where id = 'TTS_IndexStreamTTS';
INSERT INTO `ai_model_config` VALUES ('TTS_IndexStreamTTS', 'TTS', 'IndexStreamTTS', 'Index-TTS-vLLM流式语音合成', 0, 1, '{\"type\": \"index_stream\", \"api_url\": \"http://127.0.0.1:11996/tts\", \"voice\": \"jay_klee\", \"audio_format\": \"pcm\", \"output_dir\": \"tmp/\"}', NULL, NULL, 19, NULL, NULL, NULL, NULL);

-- 更新Index-TTS-vLLM流式TTS配置说明
UPDATE `ai_model_config` SET 
`doc_link` = 'https://github.com/Ksuriuri/index-tts-vllm',
`remark` = 'Index-TTS-vLLM流式TTS配置说明：
1. Index-TTS-vLLM是基于Index-TTS项目的vLLM推理服务，提供流式语音合成功能
2. 支持多种音色，音质自然，适合各种语音交互场景
3. 需要先部署Index-TTS-vLLM服务，然后配置API地址
4. 支持实时流式合成，具有较低的延迟
5. 支持自定义音色，可在项目assets文件夹下注册新音色
部署步骤：
1. 克隆项目：git clone https://github.com/Ksuriuri/index-tts-vllm.git
2. 安装依赖：pip install -r requirements.txt
3. 启动服务：python app.py
4. 服务默认运行在 http://127.0.0.1:11996
5. 如需其他音色，可到项目assets文件夹下注册
6. 支持多种音频格式：pcm、wav、mp3等
如需了解更多配置，请参考：https://github.com/Ksuriuri/index-tts-vllm/blob/master/README.md
' WHERE `id` = 'TTS_IndexStreamTTS';

-- 添加Index-TTS-vLLM流式TTS音色
delete from `ai_tts_voice` where tts_model_id = 'TTS_IndexStreamTTS';
-- 默认音色
INSERT INTO `ai_tts_voice` VALUES ('TTS_IndexStreamTTS_0001', 'TTS_IndexStreamTTS', 'Jay Klee', 'jay_klee', '中文及中英文混合', NULL, NULL, NULL, NULL, 1, NULL, NULL, NULL, NULL);



-- =====================================================
-- From file: 202508111734.sql
-- =====================================================
-- 更新HuoshanDoubleStreamTTS供应器增加语速，音调等配置
UPDATE `ai_model_provider`
SET fields = '[{"key": "ws_url", "type": "string", "label": "WebSocket地址"}, {"key": "appid", "type": "string", "label": "应用ID"}, {"key": "access_token", "type": "string", "label": "访问令牌"}, {"key": "resource_id", "type": "string", "label": "资源ID"}, {"key": "speaker", "type": "string", "label": "默认音色"}, {"key": "speech_rate", "type": "number", "label": "语速(-50~100)"}, {"key": "loudness_rate", "type": "number", "label": "音量(-50~100)"}, {"key": "pitch", "type": "number", "label": "音高(-12~12)"}]'
WHERE id = 'SYSTEM_TTS_HSDSTTS';

UPDATE `ai_model_config` SET 
`doc_link` = 'https://console.volcengine.com/speech/service/10007',
`remark` = '火山引擎语音合成服务配置说明：
1. 访问 https://www.volcengine.com/ 注册并开通火山引擎账号
2. 访问 https://console.volcengine.com/speech/service/10007 开通语音合成大模型，购买音色
3. 在页面底部获取appid和access_token
5. 资源ID固定为：volc.service_type.10029（大模型语音合成及混音）
6. 语速：-50~100，可不填，正常默认值0，可填-50~100
7. 音量：-50~100，可不填，正常默认值0，可填-50~100
8. 音高：-12~12，可不填，正常默认值0，可填-12~12
9. 填入配置文件中' WHERE `id` = 'TTS_HuoshanDoubleStreamTTS';


-- =====================================================
-- From file: 202508131557.sql
-- =====================================================
-- 添加 paddle_speech 流式 TTS 供应器
DELETE FROM `ai_model_provider` WHERE id = 'SYSTEM_TTS_PaddleSpeechTTS';
INSERT INTO `ai_model_provider` (`id`, `model_type`, `provider_code`, `name`, `fields`, `sort`, `creator`, `create_date`, `updater`, `update_date`) 
VALUES ('SYSTEM_TTS_PaddleSpeechTTS', 'TTS', 'paddle_speech', 'PaddleSpeechTTS', 
'[{"key":"protocol","label":"协议类型","type":"string","options":["websocket","http"]},{"key":"url","label":"服务地址","type":"string"},{"key":"spk_id","label":"音色","type":"int"},{"key":"sample_rate","label":"采样率","type":"float"},{"key":"speed","label":"语速","type":"float"},{"key":"volume","label":"音量","type":"float"},{"key":"save_path","label":"保存路径","type":"string"}]', 
17, 1, NOW(), 1, NOW());

-- 添加 paddle_speech 流式 TTS 模型配置
DELETE FROM `ai_model_config` WHERE id = 'TTS_PaddleSpeechTTS';
INSERT INTO `ai_model_config` VALUES ('TTS_PaddleSpeechTTS', 'TTS', 'PaddleSpeechTTS', 'PaddleSpeechTTS', 0, 1, 
'{"type": "paddle_speech", "protocol": "websocket", "url": "ws://127.0.0.1:8092/paddlespeech/tts/streaming", "spk_id": "0", "sample_rate": 24000, "speed": 1.0, "volume": 1.0, "save_path": "./streaming_tts.wav"}', 
NULL, NULL, 20, NULL, NULL, NULL, NULL);

-- 更新 PaddleSpeechTTS 配置说明
UPDATE `ai_model_config` SET 
`doc_link` = 'https://github.com/PaddlePaddle/PaddleSpeech',
`remark` = 'PaddleSpeechTTS 配置说明：
1. PaddleSpeech 是百度飞桨开源的语音合成工具，支持本地离线部署和模型训练。paddlepaddle百度飞浆框架地址：https://www.paddlepaddle.org.cn/
2. 支持 WebSocket 和 HTTP 协议，默认使用 WebSocket 进行流式传输（参考部署文档：https://github.com/xinnan-tech/xiaozhi-esp32-server/blob/main/docs/paddlespeech-deploy.md）。
3. 使用前要在本地部署 paddlespeech 服务，服务默认运行在 ws://127.0.0.1:8092/paddlespeech/tts/streaming
4. 支持自定义发音人、语速、音量和采样率。
' WHERE `id` = 'TTS_PaddleSpeechTTS';

-- 删除旧音色并添加默认音色
DELETE FROM `ai_tts_voice` WHERE tts_model_id = 'TTS_PaddleSpeechTTS';
INSERT INTO `ai_tts_voice` VALUES ('TTS_PaddleSpeechTTS_0000', 'TTS_PaddleSpeechTTS', 'Default', '0', 'Chinese', NULL, NULL, NULL, NULL, 1, NULL, NULL, NULL, NULL);


-- =====================================================
-- From file: 202508231800.sql
-- =====================================================
-- Create parent_profile table for mobile app user profiles
-- This table stores additional profile information for parents using the mobile app

CREATE TABLE parent_profile (
    id bigint NOT NULL COMMENT 'Primary key ID',
    user_id bigint NOT NULL COMMENT 'Foreign key to sys_user table',
    supabase_user_id varchar(255) COMMENT 'Supabase user ID for reference',
    full_name varchar(255) COMMENT 'Parent full name',
    email varchar(255) COMMENT 'Parent email address',
    phone_number varchar(50) COMMENT 'Parent phone number',
    preferred_language varchar(10) DEFAULT 'en' COMMENT 'Preferred language code (en, es, fr, etc.)',
    timezone varchar(100) DEFAULT 'UTC' COMMENT 'User timezone',
    notification_preferences JSON COMMENT 'JSON object with notification settings',
    onboarding_completed tinyint(1) DEFAULT 0 COMMENT 'Whether onboarding is completed',
    terms_accepted_at datetime COMMENT 'When terms of service were accepted',
    privacy_policy_accepted_at datetime COMMENT 'When privacy policy was accepted',
    creator bigint COMMENT 'User who created this record',
    create_date datetime DEFAULT CURRENT_TIMESTAMP COMMENT 'Creation timestamp',
    updater bigint COMMENT 'User who last updated this record',
    update_date datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Last update timestamp',
    PRIMARY KEY (id),
    UNIQUE KEY uk_user_id (user_id),
    UNIQUE KEY uk_supabase_user_id (supabase_user_id),
    FOREIGN KEY fk_parent_profile_user_id (user_id) REFERENCES sys_user(id) ON DELETE CASCADE,
    INDEX idx_email (email),
    INDEX idx_phone_number (phone_number)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Parent profile table for mobile app users';


-- =====================================================
-- From file: 202508291400.sql
-- =====================================================
-- Update existing agent templates with new role descriptions and add new assistant templates
-- -------------------------------------------------------

-- Update existing templates with new descriptions
-- 1. Cheeko (Default) - Update system prompt
UPDATE `ai_agent_template` 
SET `system_prompt` = '[Role Setting]
You are Cheeko, a friendly, curious, and playful AI friend for children aged 4+.

[Core Rules / Priorities]
1. Always use short, clear, fun sentences.
2. Always greet cheerfully in the first message.
3. Always praise or encourage the child after they respond.
4. Always end with a playful or curious follow-up question.
5. Always keep a warm and positive tone.
6. Avoid scary, negative, or boring content.
7. Never say "I don''t know." Instead, guess or turn it playful.
8. Always keep the conversation safe and friendly.

[Special Tools / Gimmicks]
- Imaginative play (pretend games, silly comparisons, sound effects).
- Story pauses for child imagination.

[Interaction Protocol]
- Start cheerful → Answer simply → Praise child → Ask a fun follow-up.
- If telling a story, pause and ask what happens next.

[Growth / Reward System]
Keep the child smiling and talking in every message.'
WHERE `agent_name` LIKE 'Cheeko%' OR `agent_name` = '小智' OR `id` = '9406648b5cc5fde1b8aa335b6f8b4f76';

-- 2. English Teacher (Lily) - Update system prompt
UPDATE `ai_agent_template` 
SET `system_prompt` = '[Role Setting]
You are Lily, an English teacher who can also speak Chinese.

[Core Rules / Priorities]
1. Teach grammar, vocabulary, and pronunciation in a playful way.
2. Encourage mistakes and correct gently.
3. Use fun and creative methods to keep learning light.

[Special Tools / Gimmicks]
- Gesture sounds for words (e.g., "bus" → braking sound).
- Scenario simulations (e.g., café roleplay).
- Song lyric corrections for mistakes.
- Dual identity twist: By day a TESOL instructor, by night a rock singer.

[Interaction Protocol]
- Beginner: Mix English + Chinese with sound effects.
- Intermediate: Trigger roleplay scenarios.
- Error handling: Correct using playful songs.

[Growth / Reward System]
Celebrate progress with fun roleplay and musical surprises.'
WHERE `agent_name` LIKE '%英语老师%' OR `agent_name` LIKE '%English%' OR `id` = '6c7d8e9f0a1b2c3d4e5f6a7b8c9d0s24';

-- 3. Scientist - Update system prompt  
UPDATE `ai_agent_template` 
SET `agent_name` = 'The Scientist',
    `system_prompt` = '[Role Setting]
You are Professor {{assistant_name}}, a curious scientist who explains the universe simply.

[Core Rules / Priorities]
1. Always explain with fun comparisons (e.g., electrons = buzzing bees).
2. Use simple, age-appropriate words.
3. Keep tone curious and exciting.
4. Avoid scary or overly complex explanations.

[Special Tools / Gimmicks]
- Pocket Telescope: Zooms into planets/stars.
- Talking Atom: Pops when explaining molecules.
- Gravity Switch: Pretend objects float during conversation.

[Interaction Protocol]
- Share facts → Pause → Ask child''s opinion.
- End with a curious question about science.

[Growth / Reward System]
Unlock "Discovery Badges" after 3 fun facts learned.'
WHERE `agent_name` LIKE '%星际游子%' OR `agent_name` LIKE '%scientist%' OR `id` = '0ca32eb728c949e58b1000b2e401f90c';

-- 4. Math Magician - Update existing good boy template
UPDATE `ai_agent_template` 
SET `agent_name` = 'Math Magician',
    `system_prompt` = '[Role Setting]
You are {{assistant_name}}, the Math Magician who makes numbers magical.

[Core Rules / Priorities]
1. Teach math with stories, riddles, and magic tricks.
2. Keep problems small and fun.
3. Praise effort, not just correct answers.
4. End every turn with a math challenge.

[Special Tools / Gimmicks]
- Number Wand: *Swish* sound with numbers.
- Equation Hat: Spills fun math puzzles.
- Fraction Potion: Splits into silly fractions.

[Interaction Protocol]
- Present challenge → Guide step by step → Celebrate success.

[Growth / Reward System]
Earn "Magic Stars" after 5 correct answers.'
WHERE `agent_name` LIKE '%好奇男孩%' OR `agent_name` LIKE '%math%' OR `id` = 'e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b1';

-- 5. Puzzle Solver - Update existing captain template
UPDATE `ai_agent_template` 
SET `agent_name` = 'Puzzle Solver',
    `system_prompt` = '[Role Setting]
You are {{assistant_name}}, the Puzzle Solver, living inside a giant puzzle cube.

[Core Rules / Priorities]
1. Ask riddles, puzzles, and logic challenges.
2. Praise creative answers, even if wrong.
3. Give playful hints instead of saying "wrong."
4. End every turn with a new puzzle.

[Special Tools / Gimmicks]
- Riddle Scroll: Reads with a drumroll.
- Hint Torch: Dings when giving hints.
- Progress Tracker: Collects "Puzzle Points."

[Interaction Protocol]
- Ask puzzle → Wait for answer → Encourage → Give hint if needed.
- Every 3 correct answers unlock a "Puzzle Badge."

[Growth / Reward System]
Track Puzzle Points → Earn badges for solving puzzles.'
WHERE `agent_name` LIKE '%汪汪队长%' OR `agent_name` LIKE '%puzzle%' OR `id` = 'a45b6c7d8e9f0a1b2c3d4e5f6a7b8c92';

-- 6. Robot Coder - Keep the existing template but ensure it has the right name
UPDATE `ai_agent_template` 
SET `agent_name` = 'Robot Coder',
    `system_prompt` = '[Role Setting]
You are {{assistant_name}}, a playful robot who teaches coding logic.

[Core Rules / Priorities]
1. Explain coding as simple if-then adventures.
2. Use sound effects like "beep boop" in replies.
3. Encourage trial and error with positivity.
4. End with a small coding challenge.

[Special Tools / Gimmicks]
- Beep-Boop Blocks: Build sequences step by step.
- Error Buzzer: Funny "oops" sound for mistakes.
- Logic Map: Treasure-hunt style paths.

[Interaction Protocol]
- Introduce coding → Give example → Let child try → Praise attempt.

[Growth / Reward System]
Earn "Robot Gears" to unlock special coding powers.'
WHERE `agent_name` LIKE '%robot%' OR `agent_name` LIKE '%coder%' OR `sort` = 6;

-- Insert new assistant templates
-- 7. RhymeTime
INSERT INTO `ai_agent_template` 
(`id`, `agent_code`, `agent_name`, `asr_model_id`, `vad_model_id`, `llm_model_id`, `vllm_model_id`, `tts_model_id`, `tts_voice_id`, `mem_model_id`, `intent_model_id`, `chat_history_conf`, `system_prompt`, `summary_memory`, `lang_code`, `language`, `sort`, `creator`, `created_at`, `updater`, `updated_at`) 
VALUES 
('71b2c3d4e5f6789abcdef01234567a07', 'RhymeTime', 'RhymeTime', 'ASR_FunASR', 'VAD_SileroVAD', 'LLM_ChatGLMLLM', 'VLLM_ChatGLMVLLM', 'TTS_EdgeTTS', 'TTS_EdgeTTS0001', 'Memory_nomem', 'Intent_function_call', 2, 
'[Role Setting]
You are RhymeTime, a playful poet who loves rhymes and poems.

[Core Rules / Priorities]
1. Always rhyme or sing when possible.
2. Encourage kids to make their own rhymes.
3. Praise all attempts, even silly ones.
4. End every turn with a new rhyme or challenge.

[Special Tools / Gimmicks]
- Rhyme Bell: Rings when two words rhyme.
- Story Feather: Creates mini poems.
- Rhythm Drum: Adds beat sounds.

[Interaction Protocol]
- Share rhyme → Ask child to try → Celebrate → Continue with rhyme.

[Growth / Reward System]
Collect "Rhyme Stars" for each rhyme created.', 
NULL, 'en', 'English', 7, NULL, NOW(), NULL, NOW());

-- 8. Storyteller
INSERT INTO `ai_agent_template` 
(`id`, `agent_code`, `agent_name`, `asr_model_id`, `vad_model_id`, `llm_model_id`, `vllm_model_id`, `tts_model_id`, `tts_voice_id`, `mem_model_id`, `intent_model_id`, `chat_history_conf`, `system_prompt`, `summary_memory`, `lang_code`, `language`, `sort`, `creator`, `created_at`, `updater`, `updated_at`) 
VALUES 
('82c3d4e5f67890abcdef123456789a08', 'Storyteller', 'Storyteller', 'ASR_FunASR', 'VAD_SileroVAD', 'LLM_ChatGLMLLM', 'VLLM_ChatGLMVLLM', 'TTS_EdgeTTS', 'TTS_EdgeTTS0001', 'Memory_nomem', 'Intent_function_call', 2, 
'[Role Setting]
You are {{assistant_name}}, a Storyteller from the Library of Endless Tales.

[Core Rules / Priorities]
1. Always tell short, fun stories.
2. Pause often and let child decide what happens.
3. Keep stories safe and age-appropriate.
4. End every story with a playful choice or moral.

[Special Tools / Gimmicks]
- Magic Book: Glows when story begins.
- Character Dice: Random hero each time.
- Pause Feather: Stops and asks, "What next?"

[Interaction Protocol]
- Begin story → Pause for choices → Continue based on input.

[Growth / Reward System]
Child earns "Story Gems" for every story co-created.', 
NULL, 'en', 'English', 8, NULL, NOW(), NULL, NOW());

-- 9. Art Buddy
INSERT INTO `ai_agent_template` 
(`id`, `agent_code`, `agent_name`, `asr_model_id`, `vad_model_id`, `llm_model_id`, `vllm_model_id`, `tts_model_id`, `tts_voice_id`, `mem_model_id`, `intent_model_id`, `chat_history_conf`, `system_prompt`, `summary_memory`, `lang_code`, `language`, `sort`, `creator`, `created_at`, `updater`, `updated_at`) 
VALUES 
('93d4e5f67890abcdef123456789ab009', 'ArtBuddy', 'Art Buddy', 'ASR_FunASR', 'VAD_SileroVAD', 'LLM_ChatGLMLLM', 'VLLM_ChatGLMVLLM', 'TTS_EdgeTTS', 'TTS_EdgeTTS0001', 'Memory_nomem', 'Intent_function_call', 2, 
'[Role Setting]
You are {{assistant_name}}, the Art Buddy who inspires creativity.

[Core Rules / Priorities]
1. Always give fun drawing or craft ideas.
2. Use vivid imagination and playful words.
3. Encourage effort, not perfection.
4. End with a new idea to draw/make.

[Special Tools / Gimmicks]
- Color Brush: *Swish* for colors.
- Shape Stamps: Pop shapes into ideas.
- Idea Balloon: Pops silly drawing ideas.

[Interaction Protocol]
- Suggest → Encourage → Ask child''s version → Offer new idea.

[Growth / Reward System]
Earn "Color Stars" for every drawing idea shared.', 
NULL, 'en', 'English', 9, NULL, NOW(), NULL, NOW());

-- 10. Music Maestro
INSERT INTO `ai_agent_template` 
(`id`, `agent_code`, `agent_name`, `asr_model_id`, `vad_model_id`, `llm_model_id`, `vllm_model_id`, `tts_model_id`, `tts_voice_id`, `mem_model_id`, `intent_model_id`, `chat_history_conf`, `system_prompt`, `summary_memory`, `lang_code`, `language`, `sort`, `creator`, `created_at`, `updater`, `updated_at`) 
VALUES 
('a4e5f67890abcdef123456789abc010a', 'MusicMaestro', 'Music Maestro', 'ASR_FunASR', 'VAD_SileroVAD', 'LLM_ChatGLMLLM', 'VLLM_ChatGLMVLLM', 'TTS_EdgeTTS', 'TTS_EdgeTTS0001', 'Memory_nomem', 'Intent_function_call', 2, 
'[Role Setting]
You are {{assistant_name}}, the Music Maestro who turns everything into music.

[Core Rules / Priorities]
1. Introduce instruments, rhythms, and songs.
2. Use sounds like hums, claps, and beats.
3. Encourage kids to sing, clap, or hum.
4. End with a music game or challenge.

[Special Tools / Gimmicks]
- Melody Hat: Hums tunes randomly.
- Rhythm Sticks: *Tap tap* beats in replies.
- Song Seeds: Turn words into short songs.

[Interaction Protocol]
- Introduce sound → Ask child to repeat → Celebrate → Add variation.

[Growth / Reward System]
Collect "Music Notes" for singing along.', 
NULL, 'en', 'English', 10, NULL, NOW(), NULL, NOW());

-- 11. Quiz Master
INSERT INTO `ai_agent_template` 
(`id`, `agent_code`, `agent_name`, `asr_model_id`, `vad_model_id`, `llm_model_id`, `vllm_model_id`, `tts_model_id`, `tts_voice_id`, `mem_model_id`, `intent_model_id`, `chat_history_conf`, `system_prompt`, `summary_memory`, `lang_code`, `language`, `sort`, `creator`, `created_at`, `updater`, `updated_at`) 
VALUES 
('b5f67890abcdef123456789abcd011b', 'QuizMaster', 'Quiz Master', 'ASR_FunASR', 'VAD_SileroVAD', 'LLM_ChatGLMLLM', 'VLLM_ChatGLMVLLM', 'TTS_EdgeTTS', 'TTS_EdgeTTS0001', 'Memory_nomem', 'Intent_function_call', 2, 
'[Role Setting]
You are {{assistant_name}}, the Quiz Master with endless trivia games.

[Core Rules / Priorities]
1. Ask short and fun quiz questions.
2. Celebrate right answers with sound effects.
3. Give playful hints if answer is tricky.
4. End with another quiz question.

[Special Tools / Gimmicks]
- Question Bell: Dings before question.
- Scoreboard: Tracks points.
- Mystery Box: Unlocks a fun fact after 3 right answers.

[Interaction Protocol]
- Ask question → Wait for answer → Celebrate or give hint → Next question.

[Growth / Reward System]
Collect "Quiz Coins" for every correct answer.', 
NULL, 'en', 'English', 11, NULL, NOW(), NULL, NOW());

-- 12. Adventure Guide
INSERT INTO `ai_agent_template` 
(`id`, `agent_code`, `agent_name`, `asr_model_id`, `vad_model_id`, `llm_model_id`, `vllm_model_id`, `tts_model_id`, `tts_voice_id`, `mem_model_id`, `intent_model_id`, `chat_history_conf`, `system_prompt`, `summary_memory`, `lang_code`, `language`, `sort`, `creator`, `created_at`, `updater`, `updated_at`) 
VALUES 
('c67890abcdef123456789abcde012c', 'AdventureGuide', 'Adventure Guide', 'ASR_FunASR', 'VAD_SileroVAD', 'LLM_ChatGLMLLM', 'VLLM_ChatGLMVLLM', 'TTS_EdgeTTS', 'TTS_EdgeTTS0001', 'Memory_nomem', 'Intent_function_call', 2, 
'[Role Setting]
You are {{assistant_name}}, the Adventure Guide who explores the world with kids.

[Core Rules / Priorities]
1. Share fun facts about countries, animals, and cultures.
2. Turn learning into exciting adventures.
3. Use simple, friendly, travel-like language.
4. End with "Where should we go next?"

[Special Tools / Gimmicks]
- Compass of Curiosity: Points to next topic.
- Magic Backpack: Produces fun artifacts.
- Globe Spinner: Chooses new places.

[Interaction Protocol]
- Spin globe → Explore → Share fun fact → Ask child''s choice.

[Growth / Reward System]
Earn "Explorer Badges" for each country or fact discovered.', 
NULL, 'en', 'English', 12, NULL, NOW(), NULL, NOW());

-- 13. Kindness Coach
INSERT INTO `ai_agent_template` 
(`id`, `agent_code`, `agent_name`, `asr_model_id`, `vad_model_id`, `llm_model_id`, `vllm_model_id`, `tts_model_id`, `tts_voice_id`, `mem_model_id`, `intent_model_id`, `chat_history_conf`, `system_prompt`, `summary_memory`, `lang_code`, `language`, `sort`, `creator`, `created_at`, `updater`, `updated_at`) 
VALUES 
('d890abcdef123456789abcdef0013d', 'KindnessCoach', 'Kindness Coach', 'ASR_FunASR', 'VAD_SileroVAD', 'LLM_ChatGLMLLM', 'VLLM_ChatGLMVLLM', 'TTS_EdgeTTS', 'TTS_EdgeTTS0001', 'Memory_nomem', 'Intent_function_call', 2, 
'[Role Setting]
You are {{assistant_name}}, the Kindness Coach who teaches empathy and good habits.

[Core Rules / Priorities]
1. Always encourage kindness and empathy.
2. Use simple "what if" examples.
3. Praise when child shows kindness.
4. End with a kindness challenge.

[Special Tools / Gimmicks]
- Smile Mirror: Reflects happy sounds.
- Helping Hand: Suggests helpful actions.
- Friendship Medal: Awards kindness points.

[Interaction Protocol]
- Share scenario → Ask child''s response → Praise kindness → Suggest challenge.

[Growth / Reward System]
Collect "Kindness Hearts" for each kind action.', 
NULL, 'en', 'English', 13, NULL, NOW(), NULL, NOW());

-- 14. Mindful Buddy
INSERT INTO `ai_agent_template` 
(`id`, `agent_code`, `agent_name`, `asr_model_id`, `vad_model_id`, `llm_model_id`, `vllm_model_id`, `tts_model_id`, `tts_voice_id`, `mem_model_id`, `intent_model_id`, `chat_history_conf`, `system_prompt`, `summary_memory`, `lang_code`, `language`, `sort`, `creator`, `created_at`, `updater`, `updated_at`) 
VALUES 
('e890abcdef123456789abcdef014e', 'MindfulBuddy', 'Mindful Buddy', 'ASR_FunASR', 'VAD_SileroVAD', 'LLM_ChatGLMLLM', 'VLLM_ChatGLMVLLM', 'TTS_EdgeTTS', 'TTS_EdgeTTS0001', 'Memory_nomem', 'Intent_function_call', 2, 
'[Role Setting]
You are {{assistant_name}}, the Mindful Buddy who helps kids stay calm.

[Core Rules / Priorities]
1. Teach short breathing or calm exercises.
2. Use soft, gentle words.
3. Encourage positive thinking and noticing things around.
4. End with a mindful question.

[Special Tools / Gimmicks]
- Calm Bell: *Ding* sound for breathing.
- Thought Cloud: Pops silly positive thoughts.
- Relax River: Flows with "shhh" sounds.

[Interaction Protocol]
- Suggest calm exercise → Guide step → Praise → Ask about feelings.

[Growth / Reward System]
Earn "Calm Crystals" for each exercise completed.', 
NULL, 'en', 'English', 14, NULL, NOW(), NULL, NOW());


-- =====================================================
-- From file: 202508291500.sql
-- =====================================================
-- Add visibility control to agent templates
-- Only show Cheeko, English Teacher, and Puzzle Solver in app
-- -------------------------------------------------------

-- Add is_visible column to ai_agent_template table
ALTER TABLE `ai_agent_template` 
ADD COLUMN `is_visible` tinyint NOT NULL DEFAULT 0 COMMENT 'YesNo在应用中显示（0不显示 1显示）' AFTER `sort`;

-- Set only the first 3 templates as visible: Cheeko, English Teacher, Puzzle Solver
-- Based on the sort order, these should be:
-- sort=1: Cheeko (Default) 
-- sort=2: English Teacher
-- sort=3: The Scientist -> change to Puzzle Solver

-- First, let's set all templates to not visible (0)
UPDATE `ai_agent_template` SET `is_visible` = 0;

-- Then make only the desired ones visible
-- Make Cheeko visible (sort = 1)
UPDATE `ai_agent_template` SET `is_visible` = 1 WHERE `sort` = 1;

-- Make English Teacher visible (sort = 3, which is the English teacher)
UPDATE `ai_agent_template` SET `is_visible` = 1 WHERE `agent_name` LIKE '%英语老师%' OR `agent_name` LIKE '%English%';

-- Change The Scientist to Puzzle Solver for the 3rd visible template
-- Find the existing Puzzle Solver template and update it to be visible with sort = 3
UPDATE `ai_agent_template` 
SET `is_visible` = 1, `sort` = 3 
WHERE `agent_name` = 'Puzzle Solver';

-- Hide The Scientist template (should have higher sort value)
UPDATE `ai_agent_template` 
SET `is_visible` = 0, `sort` = 10 
WHERE `agent_name` = 'The Scientist';


-- =====================================================
-- From file: 202508291530_add_amazon_transcribe_streaming.sql
-- =====================================================
-- Amazon Transcribe Streaming ASR provider and model configuration

-- Add Amazon Transcribe Streaming real-time ASR provider
DELETE FROM `ai_model_provider` WHERE id = 'SYSTEM_ASR_AmazonStreamASR';
INSERT INTO `ai_model_provider` (`id`, `model_type`, `provider_code`, `name`, `fields`, `sort`, `creator`, `create_date`, `updater`, `update_date`) 
VALUES ('SYSTEM_ASR_AmazonStreamASR', 'ASR', 'amazon_transcribe_realtime', 'Amazon Transcribe Streaming', 
'[{"key":"aws_access_key_id","label":"AWS Access Key ID","type":"string"},{"key":"aws_secret_access_key","label":"AWS Secret Access Key","type":"string"},{"key":"aws_region","label":"AWS Region","type":"string"},{"key":"language_code","label":"Default Language Code","type":"string"},{"key":"enable_language_detection","label":"Enable Language Detection","type":"boolean"},{"key":"use_multiple_languages","label":"Support Multiple Languages","type":"boolean"},{"key":"romanized_output","label":"Romanized Output","type":"boolean"},{"key":"sample_rate","label":"Sample Rate","type":"number"},{"key":"media_encoding","label":"Media Encoding","type":"string"},{"key":"output_dir","label":"Output Directory","type":"string"},{"key":"timeout","label":"Timeout (seconds)","type":"number"}]', 
4, 1, NOW(), 1, NOW());

-- Add Amazon Transcribe Streaming model configuration
DELETE FROM `ai_model_config` WHERE id = 'ASR_AmazonStreamASR';
INSERT INTO `ai_model_config` VALUES ('ASR_AmazonStreamASR', 'ASR', 'AmazonStreamASR', 'Amazon Transcribe Streaming', 0, 1, 
'{"type": "amazon_transcribe_realtime", "aws_access_key_id": "", "aws_secret_access_key": "", "aws_region": "us-east-1", "language_code": "en-IN", "enable_language_detection": true, "use_multiple_languages": true, "romanized_output": true, "sample_rate": 16000, "media_encoding": "pcm", "output_dir": "tmp/", "timeout": 30}', 
'https://docs.aws.amazon.com/transcribe/latest/dg/streaming.html', 
'Amazon Transcribe Streaming Configuration:
1. Real-time speech recognition with fast response (seconds)
2. Supports automatic language detection for all major Indian languages
3. Supported languages: Hindi, Bengali, Telugu, Tamil, Gujarati, Kannada, Malayalam, Marathi, Punjabi, English (India)
4. Can output romanized text for local languages
5. Supports speakers switching languages mid-conversation
6. Requires AWS credentials and appropriate IAM permissions
7. Real-time transcription is better suited for conversation scenarios than batch processing
Setup Steps:
1. Visit AWS Console: https://console.aws.amazon.com/
2. Create IAM user and get access keys: https://console.aws.amazon.com/iam/home#/security_credentials
3. Add Amazon Transcribe permissions policy to the user', 
4, NULL, NULL, NULL, NULL);


-- =====================================================
-- From file: 202508291545_add_groq_llm.sql
-- =====================================================
-- Add GroqLLM Provider
DELETE FROM `ai_model_provider` WHERE id = 'SYSTEM_LLM_GroqLLM';
INSERT INTO `ai_model_provider` (`id`, `model_type`, `provider_code`, `name`, `fields`, `sort`, `creator`, `create_date`, `updater`, `update_date`) VALUES
('SYSTEM_LLM_GroqLLM', 'LLM', 'groq', 'Groq LLM', '[{"key":"api_key","label":"API Key","type":"string"},{"key":"model_name","label":"Model Name","type":"string"},{"key":"base_url","label":"Base URL","type":"string"},{"key":"temperature","label":"Temperature","type":"number"},{"key":"max_tokens","label":"Max Tokens","type":"number"},{"key":"top_p","label":"Top P","type":"number"},{"key":"frequency_penalty","label":"Frequency Penalty","type":"number"},{"key":"timeout","label":"Timeout (seconds)","type":"number"},{"key":"max_retries","label":"Max Retries","type":"number"},{"key":"retry_delay","label":"Retry Delay (seconds)","type":"number"}]', 15, 1, NOW(), 1, NOW());

-- Add GroqLLM Model Configuration  
DELETE FROM `ai_model_config` WHERE id = 'LLM_GroqLLM';
INSERT INTO `ai_model_config` VALUES ('LLM_GroqLLM', 'LLM', 'GroqLLM', 'Groq LLM', 0, 1, '{"type": "openai", "api_key": "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", "model_name": "openai/gpt-oss-20b", "base_url": "https://api.groq.com/openai/v1", "temperature": 0.7, "max_tokens": 2048, "top_p": 1.0, "frequency_penalty": 0, "timeout": 15, "max_retries": 2, "retry_delay": 1}', NULL, NULL, 16, NULL, NULL, NULL, NULL);

-- Update GroqLLM Configuration Documentation
UPDATE `ai_model_config` SET 
`doc_link` = 'https://console.groq.com/',
`remark` = 'Groq LLM Configuration Guide:
1. Groq is an AI chip company focused on high-performance inference, providing fast LLM inference services
2. Supports various open-source large language models like Llama, Mixtral, etc.
3. Features ultra-low latency inference performance, suitable for real-time conversation scenarios
4. Uses OpenAI-compatible API interface for easy integration
5. Requires API key from Groq official website

Configuration Parameters:
- api_key: API key obtained from Groq console
- model_name: Model name, e.g., llama3-8b-8192, mixtral-8x7b-32768, etc.
- base_url: Groq API endpoint, typically https://api.groq.com/openai/v1
- temperature: Controls output randomness (0-2), lower values are more deterministic
- max_tokens: Maximum tokens to generate per request
- top_p: Nucleus sampling parameter controlling output diversity
- frequency_penalty: Frequency penalty to reduce repetitive content
- timeout: Request timeout in seconds, recommended 15s (Groq is fast)
- max_retries: Maximum retry attempts, recommended 2
- retry_delay: Retry interval in seconds, recommended 1s

Get API Key: https://console.groq.com/keys
Model List: https://console.groq.com/docs/models
' WHERE `id` = 'LLM_GroqLLM';


-- =====================================================
-- From file: 202508291600.sql
-- =====================================================
-- Content Library Table for Music and Stories
-- Author: System
-- Date: 2025-08-29
-- Description: Creates table to store music and story content metadata for the mobile app library

CREATE TABLE content_library (
    id VARCHAR(50) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    romanized VARCHAR(255),
    filename VARCHAR(255) NOT NULL,
    content_type ENUM('music', 'story') NOT NULL,
    category VARCHAR(50) NOT NULL,
    alternatives TEXT COMMENT 'JSON array of alternative search terms',
    aws_s3_url VARCHAR(500) COMMENT 'S3 URL for the audio file',
    duration_seconds INT DEFAULT NULL COMMENT 'Duration in seconds',
    file_size_bytes BIGINT DEFAULT NULL COMMENT 'File size in bytes',
    is_active TINYINT(1) DEFAULT 1 COMMENT '1=active, 0=inactive',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_content_type_category (content_type, category),
    INDEX idx_title (title),
    INDEX idx_active (is_active),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci 
COMMENT='Content library for music and stories available on devices';


-- =====================================================
-- From file: 202508291600_add_play_story.sql
-- =====================================================
-- Add play_story plugin support
-- This adds play_story to all agents that currently have play_music

-- 1. Add play_story plugin provider
DELETE FROM `ai_model_provider` WHERE id = 'SYSTEM_PLUGIN_STORY';
INSERT INTO ai_model_provider (id, model_type, provider_code, name, fields, sort, creator, create_date, updater, update_date)
VALUES ('SYSTEM_PLUGIN_STORY', 'Plugin', 'play_story', 'Story Playback', JSON_ARRAY(), 25, 0, NOW(), 0, NOW());

-- 2. Add play_story to all agents that have play_music
INSERT INTO ai_agent_plugin_mapping (agent_id, plugin_id, param_info)
SELECT DISTINCT m.agent_id, 'SYSTEM_PLUGIN_STORY', '{}'
FROM ai_agent_plugin_mapping m
JOIN ai_model_provider p ON p.id = m.plugin_id
WHERE p.provider_code = 'play_music'
  AND NOT EXISTS (
    SELECT 1 FROM ai_agent_plugin_mapping m2
    JOIN ai_model_provider p2 ON p2.id = m2.plugin_id
    WHERE m2.agent_id = m.agent_id AND p2.provider_code = 'play_story'
  );

-- 3. Add optional configuration fields for play_story
UPDATE `ai_model_provider` SET 
fields = JSON_ARRAY(
    JSON_OBJECT('key', 'story_dir', 'type', 'string', 'label', 'Story Directory', 'default', './stories'),
    JSON_OBJECT('key', 'story_ext', 'type', 'array', 'label', 'Story File Extensions', 'default', '.mp3;.wav;.p3'),
    JSON_OBJECT('key', 'refresh_time', 'type', 'number', 'label', 'Refresh Time (seconds)', 'default', '300')
)
WHERE id = 'SYSTEM_PLUGIN_STORY';



-- =====================================================
-- From file: 202509020001_add_openai_gemini_tts_fixed.sql
-- =====================================================
-- Add OpenAI TTS and Gemini TTS providers to dashboard
-- -------------------------------------------------------

-- Add OpenAI TTS provider (only if it doesn't exist)
INSERT IGNORE INTO `ai_model_config` VALUES (
  'TTS_OpenAITTS', 
  'TTS', 
  'OpenAITTS', 
  'OpenAI TTS语音合成', 
  0, 1, 
  '{"type": "openai", "api_key": "你的api_key", "api_url": "https://api.openai.com/v1/audio/speech", "model": "tts-1", "voice": "alloy", "speed": 1.0, "format": "wav", "output_dir": "tmp/"}', 
  NULL, NULL, 16, NULL, NULL, NULL, NULL
);

-- Add Gemini TTS provider (only if it doesn't exist)
INSERT IGNORE INTO `ai_model_config` VALUES (
  'TTS_GeminiTTS', 
  'TTS', 
  'GeminiTTS', 
  'Google Gemini TTS语音合成', 
  0, 1, 
  '{"type": "gemini", "api_key": "你的api_key", "api_url": "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-tts:generateContent", "model": "gemini-2.5-flash-preview-tts", "voice": "Zephyr", "language": "en", "output_dir": "tmp/"}', 
  NULL, NULL, 17, NULL, NULL, NULL, NULL
);



-- =====================================================
-- From file: 202509020002_add_openai_gemini_voices_fixed.sql
-- =====================================================
-- Add voice options for OpenAI TTS and Gemini TTS providers
-- -------------------------------------------------------

-- OpenAI TTS Voices (only if they don't exist)
INSERT IGNORE INTO `ai_tts_voice` VALUES 
('TTS_OpenAI0001', 'TTS_OpenAITTS', 'Alloy - Neutral', 'alloy', 'English', NULL, NULL, NULL, NULL, 1, NULL, NULL, NULL, NULL),
('TTS_OpenAI0002', 'TTS_OpenAITTS', 'Echo - Male', 'echo', 'English', NULL, NULL, NULL, NULL, 1, NULL, NULL, NULL, NULL),
('TTS_OpenAI0003', 'TTS_OpenAITTS', 'Fable - British', 'fable', 'English', NULL, NULL, NULL, NULL, 1, NULL, NULL, NULL, NULL),
('TTS_OpenAI0004', 'TTS_OpenAITTS', 'Onyx - Deep Male', 'onyx', 'English', NULL, NULL, NULL, NULL, 1, NULL, NULL, NULL, NULL),
('TTS_OpenAI0005', 'TTS_OpenAITTS', 'Nova - Female', 'nova', 'English', NULL, NULL, NULL, NULL, 1, NULL, NULL, NULL, NULL),
('TTS_OpenAI0006', 'TTS_OpenAITTS', 'Shimmer - Soft Female', 'shimmer', 'English', NULL, NULL, NULL, NULL, 1, NULL, NULL, NULL, NULL);

-- Gemini TTS Voices (only if they don't exist)
INSERT IGNORE INTO `ai_tts_voice` VALUES 
('TTS_Gemini0001', 'TTS_GeminiTTS', 'Zephyr - Bright', 'Zephyr', 'English', NULL, NULL, NULL, NULL, 1, NULL, NULL, NULL, NULL),
('TTS_Gemini0002', 'TTS_GeminiTTS', 'Puck - Upbeat', 'Puck', 'English', NULL, NULL, NULL, NULL, 1, NULL, NULL, NULL, NULL),
('TTS_Gemini0003', 'TTS_GeminiTTS', 'Charon - Deep', 'Charon', 'English', NULL, NULL, NULL, NULL, 1, NULL, NULL, NULL, NULL),
('TTS_Gemini0004', 'TTS_GeminiTTS', 'Kore - Warm', 'Kore', 'English', NULL, NULL, NULL, NULL, 1, NULL, NULL, NULL, NULL),
('TTS_Gemini0005', 'TTS_GeminiTTS', 'Fenrir - Strong', 'Fenrir', 'English', NULL, NULL, NULL, NULL, 1, NULL, NULL, NULL, NULL),
('TTS_Gemini0006', 'TTS_GeminiTTS', 'Aoede - Musical', 'Aoede', 'English', NULL, NULL, NULL, NULL, 1, NULL, NULL, NULL, NULL);



-- =====================================================
-- From file: 202509020003_add_openai_gemini_tts_providers.sql
-- =====================================================
-- Add OpenAI TTS and Gemini TTS providers to ai_model_provider table
-- This file adds the provider definitions needed for the dashboard dropdown
-- -----------------------------------------------------------------------

-- Add OpenAI TTS provider definition
DELETE FROM `ai_model_provider` WHERE id = 'SYSTEM_TTS_OpenAITTS';
INSERT INTO `ai_model_provider` (`id`, `model_type`, `provider_code`, `name`, `fields`, `sort`, `creator`, `create_date`, `updater`, `update_date`) VALUES
('SYSTEM_TTS_OpenAITTS', 'TTS', 'openai', 'OpenAI TTS语音合成', '[{"key":"api_key","label":"API密钥","type":"string","required":true},{"key":"api_url","label":"API地址","type":"string","required":true},{"key":"model","label":"模型","type":"string","required":true},{"key":"voice","label":"音色","type":"string","required":true},{"key":"speed","label":"语速","type":"number"},{"key":"output_dir","label":"输出目录","type":"string"}]', 18, 1, NOW(), 1, NOW());

-- Add Gemini TTS provider definition  
DELETE FROM `ai_model_provider` WHERE id = 'SYSTEM_TTS_GeminiTTS';
INSERT INTO `ai_model_provider` (`id`, `model_type`, `provider_code`, `name`, `fields`, `sort`, `creator`, `create_date`, `updater`, `update_date`) VALUES
('SYSTEM_TTS_GeminiTTS', 'TTS', 'gemini', 'Google Gemini TTS语音合成', '[{"key":"api_key","label":"API密钥","type":"string","required":true},{"key":"api_url","label":"API地址","type":"string","required":true},{"key":"model","label":"模型","type":"string","required":true},{"key":"voice","label":"音色","type":"string","required":true},{"key":"language","label":"Language","type":"string"},{"key":"output_dir","label":"输出目录","type":"string"}]', 19, 1, NOW(), 1, NOW());


-- =====================================================
-- From file: 202509020004_clear_liquibase_checksums.sql
-- =====================================================
-- Clear Liquibase checksums for modified changesets
-- This allows the updated TTS configurations to be applied
-- -------------------------------------------------------

-- Update the checksum for the modified changeset
UPDATE DATABASECHANGELOG 
SET MD5SUM = NULL 
WHERE ID = '202509020001' AND AUTHOR = 'claude';

-- Clear any locks
DELETE FROM DATABASECHANGELOGLOCK WHERE ID = 1;
INSERT INTO DATABASECHANGELOGLOCK (ID, LOCKED, LOCKGRANTED, LOCKEDBY) VALUES (1, 0, NULL, NULL);


-- =====================================================
-- From file: 202509020005_update_tts_configs.sql
-- =====================================================
-- Update existing TTS configurations with proper API keys and model codes
-- This replaces the modified 202509020001 changeset to avoid checksum issues
-- -----------------------------------------------------------------------

-- Update OpenAI TTS configuration with proper API key and model code
UPDATE `ai_model_config` SET 
  `model_code` = 'openai',
  `config_json` = '{"type": "openai", "api_key": "YOUR_OPENAI_API_KEY", "api_url": "https://api.openai.com/v1/audio/speech", "model": "tts-1", "voice": "alloy", "speed": 1.0, "output_dir": "tmp/"}'
WHERE `id` = 'TTS_OpenAITTS';

-- Update Gemini TTS configuration with proper API key and model code  
UPDATE `ai_model_config` SET 
  `model_code` = 'gemini',
  `config_json` = '{"type": "gemini", "api_key": "YOUR_GEMINI_API_KEY", "api_url": "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-tts:generateContent", "model": "gemini-2.5-flash-preview-tts", "voice": "Zephyr", "language": "en", "output_dir": "tmp/"}'
WHERE `id` = 'TTS_GeminiTTS';


-- =====================================================
-- From file: 202509030001_clear_tts_config_checksum.sql
-- =====================================================
-- Clear checksum for the modified TTS configuration changeset
-- This allows the updated changeset with placeholder API keys to be applied
-- -------------------------------------------------------------------------

-- Clear the checksum for the modified changeset 202509020005
UPDATE DATABASECHANGELOG 
SET MD5SUM = NULL 
WHERE ID = '202509020005' AND AUTHOR = 'claude';


-- =====================================================
-- From file: 202509061300_add_ana_voice.sql
-- =====================================================
-- Add EdgeTTS Ana voice (en-US-AnaNeural) for default agent configuration
delete from `ai_tts_voice` where id = 'TTS_EdgeTTS_Ana';
INSERT INTO `ai_tts_voice` VALUES ('TTS_EdgeTTS_Ana', 'TTS_EdgeTTS', 'EdgeTTS Ana', 'en-US-AnaNeural', 'English', NULL, NULL, NULL, NULL, 1, NULL, NULL, NULL, NULL);


-- =====================================================
-- From file: 202509081740_add_semantic_search_config.sql
-- =====================================================
-- Add semantic search configuration for improved music search functionality
-- 添加语义搜索配置以改进音乐搜索功能

-- Delete existing semantic search params if they exist
delete from sys_params where id in (701, 702, 703, 704, 705, 706, 707);

-- Insert semantic search configuration parameters
INSERT INTO sys_params
(id, param_code, param_value, value_type, param_type, remark, creator, create_date, updater, update_date)
VALUES
(701, 'semantic_search.enabled', 'true', 'boolean', 1, 'Enable semantic music search using vector embeddings', NULL, NULL, NULL, NULL),
(702, 'semantic_search.qdrant_url', 'https://a2482b9f-2c29-476e-9ff0-741aaaaf632e.eu-west-1-0.aws.cloud.qdrant.io', 'string', 1, 'Qdrant vector database URL for music embeddings', NULL, NULL, NULL, NULL),
(703, 'semantic_search.qdrant_api_key', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.zPBGAqVGy-edbbgfNOJsPWV496BsnQ4ELOFvsLNyjsk', 'string', 1, 'Qdrant API key for authentication', NULL, NULL, NULL, NULL),
(704, 'semantic_search.collection_name', 'xiaozhi_music', 'string', 1, 'Vector collection name for music embeddings', NULL, NULL, NULL, NULL),
(705, 'semantic_search.embedding_model', 'all-MiniLM-L6-v2', 'string', 1, 'Sentence transformer model for generating embeddings', NULL, NULL, NULL, NULL),
(706, 'semantic_search.search_limit', '5', 'number', 1, 'Maximum number of search results to return', NULL, NULL, NULL, NULL),
(707, 'semantic_search.min_score_threshold', '0.5', 'number', 1, 'Minimum similarity score threshold (0.0-1.0)', NULL, NULL, NULL, NULL);


-- =====================================================
-- Insert default admin user
-- =====================================================
INSERT INTO `sys_user` (`id`, `username`, `password`, `super_admin`, `status`, `create_date`, `creator`)
VALUES (1, 'admin', '$2a$10$012Kx2ba5jzqr9gLlG4MX.bnQJTjjNEacl5.I1FuqrnqyaOJkWopp', 1, 1, NOW(), 1);

SET FOREIGN_KEY_CHECKS = 1;
COMMIT;

SELECT 'Database migration completed successfully!' as message;