-- Add kid_id column to ai_device table to link device with child profile
-- This allows each device (toy) to be assigned to a specific kid
-- Existing devices will have NULL kid_id (no data loss)

-- Step 1: Add the column with NULL as default (safe for existing data)
ALTER TABLE `ai_device`
ADD COLUMN `kid_id` bigint DEFAULT NULL COMMENT 'FK to kid_profile table' AFTER `agent_id`;

-- Step 2: Add index for performance
ALTER TABLE `ai_device`
ADD KEY `idx_kid_id` (`kid_id`);

-- Step 3: Add foreign key constraint (only if kid_profile table exists)
-- The ON DELETE SET NULL ensures that if a kid is deleted, the device just unlinks (no data loss)
ALTER TABLE `ai_device`
ADD CONSTRAINT `fk_device_kid` FOREIGN KEY (`kid_id`) REFERENCES `kid_profile` (`id`) ON DELETE SET NULL;
