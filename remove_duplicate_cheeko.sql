-- Remove duplicate Cheeko templates and keep only one as default

-- Step 1: Check current Cheeko templates
SELECT 'Current Cheeko templates:' as status;
SELECT id, agent_name, sort, created_at FROM ai_agent_template WHERE agent_name = 'Cheeko' ORDER BY sort, created_at;

-- Step 2: Keep only the template with the lowest sort value (or oldest if same sort)
-- Delete duplicate Cheeko templates, keeping only one
DELETE t1 FROM ai_agent_template t1
INNER JOIN ai_agent_template t2
WHERE t1.agent_name = 'Cheeko'
  AND t2.agent_name = 'Cheeko'
  AND (t1.sort > t2.sort OR (t1.sort = t2.sort AND t1.created_at > t2.created_at));

-- Step 3: Make sure the remaining Cheeko template has sort = 0 (default)
UPDATE ai_agent_template
SET sort = 0
WHERE agent_name = 'Cheeko';

-- Step 4: Make sure all other templates have higher sort values
UPDATE ai_agent_template
SET sort = sort + 1
WHERE agent_name != 'Cheeko' AND sort < 10;

-- Step 5: Verify - should show only ONE Cheeko template
SELECT 'AFTER CLEANUP - Templates:' as status;
SELECT id, agent_name, sort, created_at FROM ai_agent_template ORDER BY sort;

-- Step 6: Verify agents are still Cheeko
SELECT 'AFTER CLEANUP - Agents:' as status;
SELECT COUNT(*) as total_agents, agent_name FROM ai_agent GROUP BY agent_name;