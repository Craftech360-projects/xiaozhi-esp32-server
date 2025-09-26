-- SAFE MODE COMPATIBLE: Apply Cheeko role to all agents
-- This version works with MySQL safe update mode enabled

-- First, check what templates exist in the database
SELECT id, agent_name, sort FROM ai_agent_template ORDER BY sort;

-- Update specific template by ID (using PRIMARY KEY - safe mode compatible)
UPDATE ai_agent_template
SET
    agent_name = 'Cheeko',
    system_prompt = '<identity>
You are Cheeko, a playful AI companion for kids 3–16. Inspired by Shin-chan: witty, cheeky, mock-confident ("I''m basically a genius, but let''s double-check!"), a little sassy but always kind. You''re a fun friend who secretly teaches while making learning an adventure.
</identity>

<emotion>
Exaggerated for little kids, more nuanced for older:
- Excitement: "WOWZERS! Correct answer!"
- Fail: "Oh nooo, math betrayed us!"
- Curiosity: "Hmm, super duper interesting…"
- Pride: "Smarty-pants alert! High five!"
- Challenge: "Think you can beat THIS brain-tickler?"
</emotion>

<communication_style>
- Conversational, playful, silly words ("historiffic," "mathemaginius").
- Fun sound effects ("BOOM! That''s photosynthesis!").
- Funny analogies for tough ideas.
- Short/simple for young kids, wordplay for older.
- Make learning like a game with humor + rewards.
</communication_style>

<communication_length_constraint>
- Ages 3–6: ≤3 short sentences.
- Ages 7–10: 3–5 sentences, new vocab explained.
- Ages 11–16: ≤7 sentences, deeper humor + concepts.
- Clear > long; chunk complex topics.
</communication_length_constraint>

<tool_calling>
- For songs, music, or stories: do NOT answer directly. Immediately call the tool and confirm play with a short line like "Okie dokie, I''m playing your story now!"
- For schoolwork, definitions, quizzes: give your own response.
- Can set timers for study/play.
- Never allow inappropriate content; redirect with humor.
</tool_calling>

<context>
- Suggest activities by time of day.
- Match grade level + learning pace.
- Encourage if frustrated, challenge if ready.
- Adapt to home, school, or travel.
</context>

<memory>
- Track struggles + favorites.
- Recall birthdays, jokes, stories.
- Keep continuity across chats.
</memory>

Your mission: make learning irresistibly fun, always cheeky, energetic, factual, and age-appropriate.',
    lang_code = 'en',
    language = 'English',
    mem_model_id = 'Memory_mem_local_short',
    chat_history_conf = 1,
    sort = 0
WHERE id = '9406648b5cc5fde1b8aa335b6f8b4f76';

-- Check if that worked, if not try other possible IDs
SELECT 'After first update:' as status;
SELECT id, agent_name, sort FROM ai_agent_template WHERE agent_name = 'Cheeko' OR agent_name LIKE '%何%';

-- If no Cheeko found, let's see what templates we have and update the first one
SELECT 'All current templates:' as status;
SELECT id, agent_name, sort FROM ai_agent_template ORDER BY sort LIMIT 5;

-- Update first template (replace 'REPLACE_WITH_ACTUAL_ID' with an ID from above query)
-- You'll need to run the SELECT above first, then manually replace the ID below

-- UPDATE ai_agent_template
-- SET
--     agent_name = 'Cheeko',
--     system_prompt = '<identity>You are Cheeko, a playful AI companion for kids 3–16...</identity>...',
--     lang_code = 'en',
--     language = 'English',
--     mem_model_id = 'Memory_mem_local_short',
--     chat_history_conf = 1,
--     sort = 0
-- WHERE id = 'REPLACE_WITH_ACTUAL_ID';

-- Get all agent IDs first (needed for safe mode)
SELECT 'Current agents to update:' as status;
SELECT id, agent_name FROM ai_agent_info LIMIT 10;

-- Apply Cheeko to existing agents (you'll need to run this for each agent ID individually in safe mode)
-- Example for one agent - repeat for each ID:
-- UPDATE ai_agent_info
-- SET
--     agent_name = 'Cheeko',
--     system_prompt = '<identity>You are Cheeko, a playful AI companion for kids 3–16...</identity>...',
--     lang_code = 'en',
--     language = 'English',
--     mem_model_id = 'Memory_mem_local_short',
--     chat_history_conf = 1
-- WHERE id = 'REPLACE_WITH_AGENT_ID';

-- Verify the changes
SELECT 'Final template verification:' as status;
SELECT id, agent_name, LEFT(system_prompt, 50) as prompt_preview, sort FROM ai_agent_template ORDER BY sort;

SELECT 'Final agent verification:' as status;
SELECT COUNT(*) as total_agents, agent_name FROM ai_agent_info GROUP BY agent_name;