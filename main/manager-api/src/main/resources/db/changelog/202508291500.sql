-- Add visibility control to agent templates
-- Only show Cheeko, English Teacher, and Puzzle Solver in app
-- -------------------------------------------------------

-- Add is_visible column to ai_agent_template table
ALTER TABLE ai_agent_template
ADD COLUMN is_visible BOOLEAN NOT NULL DEFAULT false;

COMMENT ON COLUMN ai_agent_template.is_visible IS 'Whether to display in application (false=not display, true=display)';

-- Set only the first 3 templates as visible: Cheeko, English Teacher, Puzzle Solver
-- Based on the sort order, these should be:
-- sort=1: Cheeko (Default)
-- sort=2: English Teacher
-- sort=3: The Scientist -> change to Puzzle Solver

-- First, set all templates to not visible (false)
UPDATE ai_agent_template SET is_visible = false;

-- Then make only the desired ones visible
-- Make Cheeko visible (sort = 1)
UPDATE ai_agent_template SET is_visible = true WHERE sort = 1;

-- Make English Teacher visible (sort = 3, which is the English teacher)
UPDATE ai_agent_template SET is_visible = true WHERE agent_name LIKE '%English%';

-- Change The Scientist to Puzzle Solver for the 3rd visible template
-- Find the existing Puzzle Solver template and update it to be visible with sort = 3
UPDATE ai_agent_template
SET is_visible = true, sort = 3
WHERE agent_name = 'Puzzle Solver';

-- Hide The Scientist template (should have higher sort value)
UPDATE ai_agent_template
SET is_visible = false, sort = 10
WHERE agent_name = 'The Scientist';