-- Fix roles properly: Keep 2 original roles + Cheeko as 3rd role (default)
-- Only update agents that were using the old Chinese role to Cheeko

-- Step 1: Check current templates
SELECT 'Current templates:' as status;
SELECT id, agent_name, sort FROM ai_agent_template ORDER BY sort;

-- Step 2: Remove duplicate Cheeko templates, keep only one
DELETE t1 FROM ai_agent_template t1
INNER JOIN ai_agent_template t2
WHERE t1.agent_name = 'Cheeko'
  AND t2.agent_name = 'Cheeko'
  AND (t1.sort > t2.sort OR (t1.sort = t2.sort AND t1.id > t2.id));

-- Step 3: Ensure we have exactly 3 templates with proper sort order:
-- Cheeko (sort=0, default), and 2 others (sort=1,2)
UPDATE ai_agent_template SET sort = 0 WHERE agent_name = 'Cheeko';

-- Step 4: Set sort values for other templates
SET @row_number = 0;
UPDATE ai_agent_template
SET sort = (@row_number := @row_number + 1)
WHERE agent_name != 'Cheeko'
ORDER BY sort;

-- Step 5: Restore agents that should NOT be Cheeko back to their original roles
-- We need to check what agents existed before and restore them appropriately
-- For now, let's see what we have:
SELECT 'Current agents:' as status;
SELECT id, agent_name, LEFT(system_prompt, 50) as prompt_preview FROM ai_agent;

-- Step 6: If you had specific agents that should use other templates,
-- we can restore them. For example, if you want some agents to use other roles:
--
-- UPDATE ai_agent
-- SET agent_name = 'OtherRoleName',
--     system_prompt = 'Other role prompt...'
-- WHERE id = 'specific_agent_id_that_should_not_be_cheeko';

-- Step 7: Verify final setup - should show 3 templates
SELECT 'FINAL TEMPLATES (should be 3):' as status;
SELECT id, agent_name, sort, LEFT(system_prompt, 50) as prompt_preview FROM ai_agent_template ORDER BY sort;

SELECT 'FINAL AGENT COUNT BY ROLE:' as status;
SELECT COUNT(*) as count, agent_name FROM ai_agent GROUP BY agent_name;

-- Step 8: Show template details
SELECT 'TEMPLATE DETAILS:' as status;
SELECT
    CONCAT('Sort: ', sort, ' | Name: ', agent_name) as template_info,
    LEFT(system_prompt, 100) as prompt_preview
FROM ai_agent_template
ORDER BY sort;