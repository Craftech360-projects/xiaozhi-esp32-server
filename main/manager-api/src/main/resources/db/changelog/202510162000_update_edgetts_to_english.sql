-- Update EdgeTTS default voice from Chinese (zh-CN-XiaoxiaoNeural) to English (en-US-AnaNeural)
-- This migration updates existing installations to use English by default
-- Date: 2025-10-16

UPDATE `ai_model_config`
SET `config_json` = JSON_SET(`config_json`, '$.voice', 'en-US-AnaNeural')
WHERE `id` = 'TTS_EdgeTTS'
  AND JSON_EXTRACT(`config_json`, '$.voice') = 'zh-CN-XiaoxiaoNeural';
