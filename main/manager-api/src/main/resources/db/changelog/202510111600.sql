-- Add force_update column to ai_ota table for firmware force update feature
-- This allows admins to force all devices to a specific firmware version (upgrade or downgrade)

ALTER TABLE ai_ota ADD COLUMN IF NOT EXISTS force_update SMALLINT DEFAULT 0;

-- Create index for faster queries when checking force update status
CREATE INDEX IF NOT EXISTS idx_ai_ota_force_update_type ON ai_ota(type, force_update);

COMMENT ON COLUMN ai_ota.force_update IS 'Force update flag: 0=No, 1=Yes';
