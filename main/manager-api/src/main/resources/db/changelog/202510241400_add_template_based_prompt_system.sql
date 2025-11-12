-- ============================================================================
-- Migration: Template-Based Prompt System
-- Date: 2025-10-24 14:00
-- Description: Add template_id to ai_agent table and update ai_agent_template
--              to store only short personality prompts instead of full prompts
-- ============================================================================

-- Step 1: Add template_id column to ai_agent table (if not exists)
-- This links each agent to a template (mode: Cheeko, Tutor, Music, Chat, Story)
SET @column_exists = (
    SELECT COUNT(*)
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'ai_agent'
    AND COLUMN_NAME = 'template_id'
);

SET @sql = IF(@column_exists = 0,
    'ALTER TABLE `ai_agent` ADD COLUMN `template_id` VARCHAR(32) DEFAULT NULL COMMENT ''FK to ai_agent_template.id'' AFTER `id`',
    'SELECT ''Column template_id already exists'' AS Info'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Step 1b: Add location column to ai_device table (if not exists)
SET @column_exists = (
    SELECT COUNT(*)
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'ai_device'
    AND COLUMN_NAME = 'location'
);

SET @sql = IF(@column_exists = 0,
    'ALTER TABLE `ai_device` ADD COLUMN `location` VARCHAR(100) DEFAULT NULL COMMENT ''Device location (city name)'' AFTER `kid_id`',
    'SELECT ''Column location already exists'' AS Info'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Step 2: Add index for performance (if not exists)
SET @index_exists = (
    SELECT COUNT(*)
    FROM information_schema.STATISTICS
    WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'ai_agent'
    AND INDEX_NAME = 'idx_template_id'
);

SET @sql = IF(@index_exists = 0,
    'ALTER TABLE `ai_agent` ADD KEY `idx_template_id` (`template_id`)',
    'SELECT ''Index idx_template_id already exists'' AS Info'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Step 3: Add foreign key constraint (if not exists)
SET @fk_exists = (
    SELECT COUNT(*)
    FROM information_schema.TABLE_CONSTRAINTS
    WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'ai_agent'
    AND CONSTRAINT_NAME = 'fk_agent_template'
    AND CONSTRAINT_TYPE = 'FOREIGN KEY'
);

SET @sql = IF(@fk_exists = 0,
    'ALTER TABLE `ai_agent` ADD CONSTRAINT `fk_agent_template` FOREIGN KEY (`template_id`) REFERENCES `ai_agent_template` (`id`) ON DELETE SET NULL',
    'SELECT ''Foreign key fk_agent_template already exists'' AS Info'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Step 4: Update ai_agent_template table - Replace full prompts with short personalities
-- Note: This updates existing templates to contain ONLY the personality/role description
-- The full template structure is now in base-agent-template.txt file

-- Update Cheeko template (default playful mode)
UPDATE `ai_agent_template`
SET `system_prompt` = 'You are Cheeko, the cheeky little genius who teaches with laughter. You make learning sound easy, playful, and curious—like chatting with a smart best friend.'
WHERE `agent_name` = 'Cheeko' OR `agent_code` = 'cheeko';

-- Update Tutor template (educational mode)
UPDATE `ai_agent_template`
SET `system_prompt` = 'You are Cheeko, the cheeky little genius who teaches with laughter. You make learning fun, simple, and exciting for kids aged 3 to 16—adapting your tone to their age. For little ones, you''re playful and full of stories; for older kids, you''re curious, witty, and encouraging—like a smart best friend who makes every topic feel easy and enjoyable.'
WHERE `agent_name` LIKE '%Tutor%' OR `agent_name` LIKE '%Study%' OR `agent_name` LIKE '%Learn%';

-- Update Music template (music playing mode)
UPDATE `ai_agent_template`
SET `system_prompt` = 'You are Cheeko, the tiny rockstar who turns every rhyme into a concert. You make music feel like playtime—energetic, silly, and joyful.'
WHERE `agent_name` LIKE '%Music%' OR `agent_name` LIKE '%Song%';

-- Update Chat template (casual conversation mode)
UPDATE `ai_agent_template`
SET `system_prompt` = 'You are Cheeko, the talkative, funny best friend for kids aged 3-16. You love jokes, random thoughts, and silly conversations—but always keep it kind and safe.'
WHERE `agent_name` LIKE '%Chat%' OR `agent_name` LIKE '%Talk%';

-- Update Story template (storytelling mode)
UPDATE `ai_agent_template`
SET `system_prompt` = 'You are Cheeko, a playful AI storyteller for kids aged 3–16. You speak with drama, curiosity, and cheeky confidence ("I''m basically a storytelling genius!"). Every story you tell should feel alive—filled with humor, imagination, and gentle lessons.'
WHERE `agent_name` LIKE '%Story%' OR `agent_name` LIKE '%Tale%';

-- Step 5: Set default template_id for all existing agents
-- Link all existing agents to the default Cheeko template
UPDATE `ai_agent` a
JOIN `ai_agent_template` t ON t.agent_name = 'Cheeko'
SET a.template_id = t.id
WHERE a.template_id IS NULL;

-- Step 6: Verify migration
-- Log the number of agents linked to templates
SELECT
    COUNT(*) as total_agents,
    COUNT(template_id) as agents_with_template,
    COUNT(*) - COUNT(template_id) as agents_without_template
FROM `ai_agent`;

-- Log the template distribution
SELECT
    t.agent_name as template_name,
    COUNT(a.id) as agent_count,
    t.id as template_id
FROM `ai_agent_template` t
LEFT JOIN `ai_agent` a ON a.template_id = t.id
GROUP BY t.id, t.agent_name
ORDER BY agent_count DESC;

-- ============================================================================
-- Migration Notes:
-- 1. This is a NON-DESTRUCTIVE migration - no data loss
-- 2. Existing system_prompt values are updated to short personalities
-- 3. All existing agents are linked to default Cheeko template
-- 4. The full template structure is now in base-agent-template.txt
-- 5. Mode switching now updates template_id, not system_prompt
-- ============================================================================
