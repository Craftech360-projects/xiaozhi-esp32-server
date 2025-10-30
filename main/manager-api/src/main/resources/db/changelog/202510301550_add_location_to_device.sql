-- Add location column to ai_device table
ALTER TABLE ai_device ADD COLUMN location VARCHAR(100) COMMENT '设备位置（城市名称）' AFTER kid_id;

-- Create index for location for better query performance
CREATE INDEX idx_location ON ai_device(location);
