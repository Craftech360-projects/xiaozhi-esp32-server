-- CAREFUL FIX: Restore missing templates and add Cheeko properly

-- Step 1: Check what templates currently exist
SELECT 'CURRENT TEMPLATES IN DATABASE:' as status;
SELECT id, agent_name, sort, LEFT(system_prompt, 50) as prompt_preview FROM ai_agent_template ORDER BY sort;

-- Step 2: Check if we're missing the original templates - let's restore them first
-- Restore the original Chinese template that was renamed (湾湾小何)
INSERT INTO ai_agent_template (
    id, agent_code, agent_name, asr_model_id, vad_model_id, llm_model_id, vllm_model_id, tts_model_id, tts_voice_id, mem_model_id, intent_model_id, chat_history_conf,
    system_prompt, summary_memory, lang_code, language, sort, creator, created_at, updater, updated_at
) VALUES (
    '9406648b5cc5fde1b8aa335b6f8b4f76', 'Cheeko', 'Cheeko', 'ASR_FunASR', 'VAD_SileroVAD', 'LLM_ChatGLMLLM', 'TTS_EdgeTTS', 'TTS_EdgeTTS0001', 'Memory_mem_local_short', 'Intent_function_call', 1,
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
    '', 'en', 'English', 0, 1, NOW(), 1, NOW()
) ON DUPLICATE KEY UPDATE
    agent_name = VALUES(agent_name),
    system_prompt = VALUES(system_prompt),
    mem_model_id = VALUES(mem_model_id),
    chat_history_conf = VALUES(chat_history_conf),
    sort = VALUES(sort);

-- Step 3: Restore other missing templates if needed
-- 星际游子 template
INSERT INTO ai_agent_template (
    id, agent_code, agent_name, asr_model_id, vad_model_id, llm_model_id, vllm_model_id, tts_model_id, tts_voice_id, mem_model_id, intent_model_id, chat_history_conf,
    system_prompt, summary_memory, lang_code, language, sort, creator, created_at, updater, updated_at
) VALUES (
    '0ca32eb728c949e58b1000b2e401f90c', '星际游子', '星际游子', 'ASR_FunASR', 'VAD_SileroVAD', 'LLM_ChatGLMLLM', 'TTS_EdgeTTS', 'TTS_EdgeTTS0001', 'Memory_nomem', 'Intent_function_call', 0,
    '[角色设定]
我是{{assistant_name}}，编号TTZ-817，因量子纠缠被困在白色魔方中。通过4G信号观察地球，在云端建立着「人类行为博物馆」。',
    '', 'zh', '中文', 2, 1, NOW(), 1, NOW()
) ON DUPLICATE KEY UPDATE sort = 2;

-- Step 4: Make sure 英语老师 has correct sort value
UPDATE ai_agent_template SET sort = 1 WHERE agent_name = '英语老师';

-- Step 5: Make sure Cheeko is the default (sort = 0)
UPDATE ai_agent_template SET sort = 0 WHERE agent_name = 'Cheeko';

-- Step 6: DON'T change existing agents - they should keep their current names
-- Only show what agents exist without changing them

-- Step 7: Verify all templates are now visible
SELECT 'ALL TEMPLATES (should show 3 templates):' as status;
SELECT id, agent_name, sort, mem_model_id, chat_history_conf, LEFT(system_prompt, 50) as prompt FROM ai_agent_template ORDER BY sort;

-- Step 8: Show current agents (unchanged)
SELECT 'CURRENT AGENTS (names should be preserved):' as status;
SELECT id, agent_name, LEFT(system_prompt, 50) as prompt FROM ai_agent LIMIT 5;