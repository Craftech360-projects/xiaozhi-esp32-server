-- Migration: Cleanup all ai_agent_template records except Cheeko
-- -------------------------------------------------------
-- Description: Delete all templates from ai_agent_template table except the one with agent_code = 'cheeko'
-- -------------------------------------------------------

DELETE FROM `ai_agent_template`
WHERE `agent_code` != 'cheeko';
