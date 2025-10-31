-- =====================================================
-- Add mode support for device-level mode switching
-- Date: 2025-01-31
-- Purpose: Enable 3-mode cycle (conversation/music/story)
-- =====================================================

-- Step 1: Add mode column to ai_device table
ALTER TABLE `ai_device` 
ADD COLUMN `mode` VARCHAR(20) DEFAULT 'conversation' 
COMMENT 'Current device mode: conversation, music, story' 
AFTER `agent_id`;

-- Step 2: Update existing devices to have default mode
UPDATE `ai_device` SET `mode` = 'conversation' WHERE `mode` IS NULL;

-- Step 3: Add index for faster mode queries
CREATE INDEX `idx_ai_device_mode` ON `ai_device` (`mode`);

-- Step 4: Add mode_category column to ai_agent_template table
ALTER TABLE `ai_agent_template`
ADD COLUMN `mode_category` VARCHAR(20) DEFAULT 'conversation'
COMMENT 'Mode category: conversation, music, story'
AFTER `agent_name`;

-- Step 5: Categorize existing templates based on agent_name
-- (Adjust these based on your actual template names)
UPDATE `ai_agent_template` SET `mode_category` = 'conversation' 
WHERE LOWER(agent_name) IN ('cheeko', 'chat', 'tutor', 'conversation', 'puzzle');

UPDATE `ai_agent_template` SET `mode_category` = 'music' 
WHERE LOWER(agent_name) IN ('music', 'musicmaestro');

UPDATE `ai_agent_template` SET `mode_category` = 'story' 
WHERE LOWER(agent_name) IN ('story', 'storyteller');

-- Step 6: Add index for faster template category queries
CREATE INDEX `idx_ai_agent_template_mode_category` ON `ai_agent_template` (`mode_category`);

-- Step 7: Verify changes
SELECT 'Migration completed successfully' AS status;
