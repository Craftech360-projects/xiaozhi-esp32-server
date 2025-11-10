-- Add mode column to ai_device table
-- Mode can be: conversation, music, story

ALTER TABLE ai_device
ADD COLUMN mode VARCHAR(20) DEFAULT 'conversation'
COMMENT '设备模式: conversation/music/story';

-- Add index for faster mode queries
CREATE INDEX idx_device_mode ON ai_device(mode);

-- Update existing devices to default mode
UPDATE ai_device SET mode = 'conversation' WHERE mode IS NULL;
