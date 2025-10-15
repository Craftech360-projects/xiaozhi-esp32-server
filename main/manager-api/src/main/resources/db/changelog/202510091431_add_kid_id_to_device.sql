-- Add kid_id column to ai_device table to link device with child profile
-- This allows each device (toy) to be assigned to a specific kid
-- Existing devices will have NULL kid_id (no data loss)

-- Step 1: Add the column with NULL as default (safe for existing data)
ALTER TABLE ai_device
ADD COLUMN IF NOT EXISTS kid_id BIGINT DEFAULT NULL;

-- Step 2: Add index for performance
CREATE INDEX IF NOT EXISTS idx_ai_device_kid_id ON ai_device (kid_id);

-- Step 3: Add foreign 
-- The ON DELETE SET NULL ensures that if a kid is deleted, the device just unlinks (no data loss)
ALTER TABLE ai_device
ADD CONSTRAINT fk_device_kid FOREIGN KEY (kid_id) REFERENCES kid_profile (id) ON DELETE SET NULL;

COMMENT ON COLUMN ai_device.kid_id IS 'FK to kid_profile table';
