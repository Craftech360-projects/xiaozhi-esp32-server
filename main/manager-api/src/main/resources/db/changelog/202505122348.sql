-- Add summary memory field
ALTER TABLE ai_agent
ADD COLUMN summary_memory TEXT;

COMMENT ON COLUMN ai_agent.summary_memory IS 'Summary memory';

ALTER TABLE ai_agent_template
ADD COLUMN summary_memory TEXT;

COMMENT ON COLUMN ai_agent_template.summary_memory IS 'Summary memory';
