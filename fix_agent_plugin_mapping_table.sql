-- Check current structure of ai_agent_plugin_mapping table
DESCRIBE ai_agent_plugin_mapping;

-- Add missing columns if they don't exist
ALTER TABLE ai_agent_plugin_mapping 
ADD COLUMN IF NOT EXISTS agent_id VARCHAR(32) NOT NULL COMMENT '智能体ID' AFTER id;

ALTER TABLE ai_agent_plugin_mapping 
ADD COLUMN IF NOT EXISTS plugin_id VARCHAR(32) NOT NULL COMMENT '插件ID' AFTER agent_id;

ALTER TABLE ai_agent_plugin_mapping 
ADD COLUMN IF NOT EXISTS param_info JSON NOT NULL COMMENT '参数信息' AFTER plugin_id;

-- Add unique constraint if it doesn't exist
ALTER TABLE ai_agent_plugin_mapping 
ADD UNIQUE KEY IF NOT EXISTS uk_agent_provider (agent_id, plugin_id);

-- Verify the structure after changes
DESCRIBE ai_agent_plugin_mapping;