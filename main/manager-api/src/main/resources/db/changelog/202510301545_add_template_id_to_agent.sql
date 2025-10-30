-- Add template_id column to ai_agent table
ALTER TABLE ai_agent ADD COLUMN template_id VARCHAR(32) COMMENT '模板ID，关联ai_agent_template表' AFTER id;

-- Create index for template_id for better query performance
CREATE INDEX idx_template_id ON ai_agent(template_id);
