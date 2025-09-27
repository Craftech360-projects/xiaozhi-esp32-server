-- SAFE: Only add Cheeko template without affecting existing functionality

-- Step 1: Check current state (NO CHANGES)
SELECT 'Current templates (before changes):' as status;
SELECT id, agent_name, sort FROM ai_agent_template ORDER BY sort;

SELECT 'Current agents (before changes):' as status;
SELECT COUNT(*) as count, agent_name FROM ai_agent GROUP BY agent_name;

-- Step 2: SAFELY add Cheeko template (only if it doesn't exist)
INSERT INTO ai_agent_template (
    id,
    agent_code,
    agent_name,
    asr_model_id,
    vad_model_id,
    llm_model_id,
    vllm_model_id,
    tts_model_id,
    tts_voice_id,
    mem_model_id,
    intent_model_id,
    chat_history_conf,
    system_prompt,
    summary_memory,
    lang_code,
    language,
    sort,
    creator,
    created_at,
    updater,
    updated_at
)
SELECT
    'cheeko_safe_template',
    'Cheeko',
    'Cheeko',
    'ASR_FunASR',
    'VAD_SileroVAD',
    'LLM_ChatGLMLLM',
    'TTS_EdgeTTS',
    'TTS_EdgeTTS',
    'TTS_EdgeTTS0001',
    'Memory_mem_local_short',
    'Intent_function_call',
    1,
    '<identity>
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
    '',
    'en',
    'English',
    -1,  -- Negative sort to make it first/default
    1,
    NOW(),
    1,
    NOW()
WHERE NOT EXISTS (SELECT 1 FROM ai_agent_template WHERE agent_name = 'Cheeko');

-- Step 3: SAFELY make Cheeko default by giving it the lowest sort value
UPDATE ai_agent_template
SET sort = -1
WHERE agent_name = 'Cheeko';

-- Step 4: Verify changes (shows what was added)
SELECT 'After adding Cheeko:' as status;
SELECT id, agent_name, sort, mem_model_id, chat_history_conf FROM ai_agent_template ORDER BY sort;

SELECT 'Agents unchanged:' as status;
SELECT COUNT(*) as count, agent_name FROM ai_agent GROUP BY agent_name;

-- Step 5: Show what the backend will now use as default
SELECT 'DEFAULT TEMPLATE (what new agents will get):' as status;
SELECT agent_name, LEFT(system_prompt, 60) as prompt_preview
FROM ai_agent_template
ORDER BY sort ASC
LIMIT 1;