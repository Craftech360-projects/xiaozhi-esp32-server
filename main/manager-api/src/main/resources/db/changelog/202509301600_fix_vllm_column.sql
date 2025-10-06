-- Fix vllm_model_id column issue - ensure columns exist before any INSERT operations
-- This changeset is idempotent - it checks before adding

-- Check and add vllm_model_id to ai_agent if it doesn't exist
SET @dbname = DATABASE();
SET @tablename = 'ai_agent';
SET @columnname = 'vllm_model_id';
SET @preparedStatement = (SELECT IF(
  (
    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
    WHERE
      TABLE_SCHEMA = @dbname
      AND TABLE_NAME = @tablename
      AND COLUMN_NAME = @columnname
  ) > 0,
  'SELECT 1',
  'ALTER TABLE ai_agent ADD COLUMN vllm_model_id varchar(32) NULL DEFAULT ''VLLM_ChatGLMVLLM'' COMMENT ''视觉模型标识'' AFTER llm_model_id'
));
PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;

-- Check and add vllm_model_id to ai_agent_template if it doesn't exist
SET @tablename = 'ai_agent_template';
SET @preparedStatement = (SELECT IF(
  (
    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
    WHERE
      TABLE_SCHEMA = @dbname
      AND TABLE_NAME = @tablename
      AND COLUMN_NAME = @columnname
  ) > 0,
  'SELECT 1',
  'ALTER TABLE ai_agent_template ADD COLUMN vllm_model_id varchar(32) NULL DEFAULT ''VLLM_ChatGLMVLLM'' COMMENT ''视觉模型标识'' AFTER llm_model_id'
));
PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;
