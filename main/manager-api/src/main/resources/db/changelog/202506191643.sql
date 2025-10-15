-- LLM intent recognition configuration documentation
UPDATE ai_model_config SET
doc_link = NULL,
remark = 'LLM intent recognition configuration instructions:
1. Uses independent LLM for intent recognition
2. Default uses selected_module.LLM model
3. Can configure to use independent LLM (such as free ChatGLMLLM)
4. Highly versatile, but increases processing time
Configuration instructions:
1. Specify LLM model to use in llm field
2. If not specified, uses selected_module.LLM model' WHERE id = 'Intent_intent_llm';

-- Function call intent recognition configuration documentation
UPDATE ai_model_config SET
doc_link = NULL,
remark = 'Function call intent recognition configuration instructions:
1. Uses LLM function_call capability for intent recognition
2. Requires selected LLM to support function_call
3. Calls tools on demand, fast processing speed' WHERE id = 'Intent_function_call';
