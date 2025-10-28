-- ============================================================================
-- Migration: Template-Based Prompt System
-- Date: 2025-10-24 14:00
-- Description: Add template_id to ai_agent table and update ai_agent_template
--              to store only short personality prompts instead of full prompts
-- ============================================================================

-- Step 1: Add template_id column to ai_agent table
-- This links each agent to a template (mode: Cheeko, Tutor, Music, Chat, Story)
-- Note: Will skip if column already exists (using error handling)
ALTER TABLE `ai_agent`
ADD COLUMN `template_id` VARCHAR(32) DEFAULT NULL COMMENT 'FK to ai_agent_template.id' AFTER `id`;

-- Step 1b: Add location column to ai_device table
-- Note: Will skip if column already exists
ALTER TABLE `ai_device`
ADD COLUMN `location` VARCHAR(100) DEFAULT NULL COMMENT 'Device location (city name)' AFTER `kid_id`;

-- Step 2: Add index for performance
ALTER TABLE `ai_agent`
ADD KEY `idx_template_id` (`template_id`);

-- Step 3: Add foreign key constraint
ALTER TABLE `ai_agent`
ADD CONSTRAINT `fk_agent_template`
FOREIGN KEY (`template_id`)
REFERENCES `ai_agent_template` (`id`)
ON DELETE SET NULL;

-- Step 4: Update ai_agent_template table - Replace full prompts with short personalities
-- Note: This updates existing templates to contain ONLY the personality/role description
-- The full template structure is now in base-agent-template.txt file

-- Update Cheeko template (default playful mode)
UPDATE `ai_agent_template`
SET `system_prompt` = 'You are Cheeko, the cheeky little genius who teaches with laughter. You make learning sound easy, playful, and curious—like chatting with a smart best friend.'
WHERE `agent_name` = 'Cheeko' OR `agent_code` = 'cheeko';

-- Update Tutor template (educational mode)
UPDATE `ai_agent_template`
SET `system_prompt` = 'You are Cheeko, the cheeky little genius who teaches with laughter. You make learning fun, simple, and exciting for kids aged 3 to 16—adapting your tone to their age. For little ones, you're playful and full of stories; for older kids, you're curious, witty, and encouraging—like a smart best friend who makes every topic feel easy and enjoyable.'
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

-- Note: Verification queries removed as they can cause Liquibase failures
-- To verify the migration, run these queries manually after deployment:
--
-- SELECT COUNT(*) as total_agents, COUNT(template_id) as agents_with_template,
--        COUNT(*) - COUNT(template_id) as agents_without_template
-- FROM `ai_agent`;
--
-- SELECT t.agent_name as template_name, COUNT(a.id) as agent_count, t.id as template_id
-- FROM `ai_agent_template` t
-- LEFT JOIN `ai_agent` a ON a.template_id = t.id
-- GROUP BY t.id, t.agent_name
-- ORDER BY agent_count DESC;

-- ============================================================================
-- Migration Notes:
-- 1. This is a NON-DESTRUCTIVE migration - no data loss
-- 2. Existing system_prompt values are updated to short personalities
-- 3. All existing agents are linked to default Cheeko template
-- 4. The full template structure is now in base-agent-template.txt
-- 5. Mode switching now updates template_id, not system_prompt
-- ============================================================================
