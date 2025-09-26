-- Update chat_history_conf default value from 0 to 1 (Report Text by default)
ALTER TABLE `ai_agent_info`
ALTER COLUMN `chat_history_conf` SET DEFAULT 1;

ALTER TABLE `ai_agent_template`
ALTER COLUMN `chat_history_conf` SET DEFAULT 1;

-- Update existing agents that have chat_history_conf = 0 to 1 (if memory is not disabled)
UPDATE `ai_agent_info`
SET `chat_history_conf` = 1
WHERE `chat_history_conf` = 0
AND `mem_model_id` != 'Memory_nomem';

UPDATE `ai_agent_template`
SET `chat_history_conf` = 1
WHERE `chat_history_conf` = 0;