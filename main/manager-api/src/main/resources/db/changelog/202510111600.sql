-- Add force_update column to ai_ota table for firmware force update feature
-- This allows admins to force all devices to a specific firmware version (upgrade or downgrade)

ALTER TABLE ai_ota ADD COLUMN force_update TINYINT(1) DEFAULT 0 COMMENT '是否强制更新: 0-否, 1-是';

-- Create index for faster queries when checking force update status
CREATE INDEX idx_force_update_type ON ai_ota(type, force_update);
