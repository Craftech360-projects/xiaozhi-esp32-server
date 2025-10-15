-- Add FunASR service speech recognition model provider and configuration
DELETE FROM ai_model_provider WHERE id = 'SYSTEM_ASR_FunASRServer';
INSERT INTO ai_model_provider (id, model_type, provider_code, name, fields, sort, creator, create_date, updater, update_date) VALUES
('SYSTEM_ASR_FunASRServer', 'ASR', 'fun_server', 'FunASR Service Speech Recognition', '[{"key":"host","label":"Service Address","type":"string"},{"key":"port","label":"Port Number","type":"number"}]', 4, 1, NOW(), 1, NOW());

DELETE FROM ai_model_config WHERE id = 'ASR_FunASRServer';
INSERT INTO ai_model_config VALUES ('ASR_FunASRServer', 'ASR', 'FunASRServer', 'FunASR Service Speech Recognition', FALSE, TRUE, '{"type": "fun_server", "host": "127.0.0.1", "port": 10096}', NULL, NULL, 5, NULL, NULL, NULL, NULL);

-- Modify remark field type of ai_model_config table to TEXT
ALTER TABLE ai_model_config ALTER COLUMN remark TYPE TEXT;

-- Update ASR model configuration documentation
UPDATE ai_model_config SET
doc_link = 'https://github.com/modelscope/FunASR/blob/main/runtime/docs/SDK_advanced_guide_online_zh.md',
remark = 'Deploy FunASR independently, use FunASR API service, only need five steps
Step 1: mkdir -p ./funasr-runtime-resources/models
Step 2: sudo docker run -d -p 10096:10095 --privileged=true -v $PWD/funasr-runtime-resources/models:/workspace/models registry.cn-hangzhou.aliyuncs.com/funasr_repo/funasr:funasr-runtime-sdk-online-cpu-0.1.12
After previous step enters container, continue Step 3: cd FunASR/runtime
Do not exit container, continue Step 4: nohup bash run_server_2pass.sh --download-model-dir /workspace/models --vad-dir damo/speech_fsmn_vad_zh-cn-16k-common-onnx --model-dir damo/speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-onnx  --online-model-dir damo/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-online-onnx  --punc-dir damo/punc_ct-transformer_zh-cn-common-vad_realtime-vocab272727-onnx --lm-dir damo/speech_ngram_lm_zh-cn-ai-wesp-fst --itn-dir thuduj12/fst_itn_zh --hotword /workspace/models/hotwords.txt > log.txt 2>&1 &
After previous step completes, continue Step 5: tail -f log.txt
After Step 5, you will see model download logs, can connect after download completes
Above uses CPU inference, for GPU see: https://github.com/modelscope/FunASR/blob/main/runtime/docs/SDK_advanced_guide_online_zh.md' WHERE id = 'ASR_FunASRServer';

-- Update FunASR local model configuration documentation
UPDATE ai_model_config SET
doc_link = 'https://github.com/modelscope/FunASR',
remark = 'FunASR local model configuration instructions:
1. Need to download model files to xiaozhi-server/models/SenseVoiceSmall directory
2. Supports Chinese, Japanese, Korean, Cantonese speech recognition
3. Local inference, no network connection required
4. Files to be recognized saved in tmp/ directory' WHERE id = 'ASR_FunASR';

-- Update SherpaASR configuration documentation
UPDATE ai_model_config SET
doc_link = 'https://github.com/k2-fsa/sherpa-onnx',
remark = 'SherpaASR configuration instructions:
1. Automatically downloads model files to models/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17 directory at runtime
2. Supports multiple languages including Chinese, English, Japanese, Korean, Cantonese
3. Local inference, no network connection required
4. Output files saved in tmp/ directory' WHERE id = 'ASR_SherpaASR';

-- Update Doubao ASR configuration documentation
UPDATE ai_model_config SET
doc_link = 'https://console.volcengine.com/speech/app',
remark = 'Doubao ASR configuration instructions:
1. Need to create application in Volcano Engine console and obtain appid and access_token
2. Supports Chinese speech recognition
3. Requires network connection
4. Output files saved in tmp/ directory
Application steps:
1. Visit https://console.volcengine.com/speech/app
2. Create new application
3. Obtain appid and access_token
4. Fill into configuration file' WHERE id = 'ASR_DoubaoASR';

-- Update Tencent ASR configuration documentation
UPDATE ai_model_config SET
doc_link = 'https://console.cloud.tencent.com/cam/capi',
remark = 'Tencent ASR configuration instructions:
1. Need to create application in Tencent Cloud console and obtain appid, secret_id and secret_key
2. Supports Chinese speech recognition
3. Requires network connection
4. Output files saved in tmp/ directory
Application steps:
1. Visit https://console.cloud.tencent.com/cam/capi to get keys
2. Visit https://console.cloud.tencent.com/asr/resourcebundle to claim free resources
3. Obtain appid, secret_id and secret_key
4. Fill into configuration file' WHERE id = 'ASR_TencentASR';

-- Update TTS model configuration documentation
-- EdgeTTS configuration documentation
UPDATE ai_model_config SET
doc_link = 'https://github.com/rany2/edge-tts',
remark = 'EdgeTTS configuration instructions:
1. Uses Microsoft Edge TTS service
2. Supports multiple languages and voices
3. Free to use, no registration required
4. Requires network connection
5. Output files saved in tmp/ directory' WHERE id = 'TTS_EdgeTTS';

-- Doubao TTS configuration documentation
UPDATE ai_model_config SET
doc_link = 'https://console.volcengine.com/speech/service/8',
remark = 'Doubao TTS configuration instructions:
1. Visit https://console.volcengine.com/speech/service/8
2. Need to create application in Volcano Engine console and obtain appid and access_token
3. Volcano Engine Speech must be purchased, starting at 30 yuan, gives 100 concurrent connections. Free tier only has 2 concurrent connections, will frequently report tts errors
4. After purchasing service and free voices, may need to wait about half hour before use
5. Fill into configuration file' WHERE id = 'TTS_DoubaoTTS';

-- SiliconFlow TTS configuration documentation
UPDATE ai_model_config SET
doc_link = 'https://cloud.siliconflow.cn/account/ak',
remark = 'SiliconFlow TTS configuration instructions:
1. Visit https://cloud.siliconflow.cn/account/ak
2. Register and obtain API key
3. Fill into configuration file' WHERE id = 'TTS_CosyVoiceSiliconflow';

-- Coze CN TTS configuration documentation
UPDATE ai_model_config SET
doc_link = 'https://www.coze.cn/open/oauth/pats',
remark = 'Coze CN TTS configuration instructions:
1. Visit https://www.coze.cn/open/oauth/pats
2. Obtain personal token
3. Fill into configuration file' WHERE id = 'TTS_CozeCnTTS';

-- FishSpeech configuration documentation
UPDATE ai_model_config SET
doc_link = 'https://github.com/fishaudio/fish-speech',
remark = 'FishSpeech configuration instructions:
1. Need to deploy FishSpeech service locally
2. Supports custom voices
3. Local inference, no network connection required
4. Output files saved in tmp/ directory
5. Service startup example command: python -m tools.api_server --listen 0.0.0.0:8080 --llama-checkpoint-path "checkpoints/fish-speech-1.5" --decoder-checkpoint-path "checkpoints/fish-speech-1.5/firefly-gan-vq-fsq-8x1024-21hz-generator.pth" --decoder-config-name firefly_gan_vq --compile' WHERE id = 'TTS_FishSpeech';

-- GPT-SoVITS V2 configuration documentation
UPDATE ai_model_config SET
doc_link = 'https://github.com/RVC-Boss/GPT-SoVITS',
remark = 'GPT-SoVITS V2 configuration instructions:
1. Need to deploy GPT-SoVITS service locally
2. Supports custom voice cloning
3. Local inference, no network connection required
4. Output files saved in tmp/ directory
Deployment steps:
1. Service startup example command: python api_v2.py -a 127.0.0.1 -p 9880 -c GPT_SoVITS/configs/demo.yaml' WHERE id = 'TTS_GPT_SOVITS_V2';

-- GPT-SoVITS V3 configuration documentation
UPDATE ai_model_config SET
doc_link = 'https://github.com/RVC-Boss/GPT-SoVITS',
remark = 'GPT-SoVITS V3 configuration instructions:
1. Need to deploy GPT-SoVITS V3 service locally
2. Supports custom voice cloning
3. Local inference, no network connection required
4. Output files saved in tmp/ directory' WHERE id = 'TTS_GPT_SOVITS_V3';

-- MiniMax TTS configuration documentation
UPDATE ai_model_config SET
doc_link = 'https://platform.minimaxi.com/',
remark = 'MiniMax TTS configuration instructions:
1. Need to create account on MiniMax platform and recharge
2. Supports multiple voices, currently configured to use female-shaonv
3. Requires network connection
4. Output files saved in tmp/ directory
Application steps:
1. Visit https://platform.minimaxi.com/ to register account
2. Visit https://platform.minimaxi.com/user-center/payment/balance to recharge
3. Visit https://platform.minimaxi.com/user-center/basic-information to get group_id
4. Visit https://platform.minimaxi.com/user-center/basic-information/interface-key to get api_key
5. Fill into configuration file' WHERE id = 'TTS_MinimaxTTS';

-- Aliyun TTS configuration documentation
UPDATE ai_model_config SET
doc_link = 'https://nls-portal.console.aliyun.com/',
remark = 'Aliyun TTS configuration instructions:
1. Need to enable Intelligent Speech Interaction service on Aliyun platform
2. Supports multiple voices, currently configured to use xiaoyun
3. Requires network connection
4. Output files saved in tmp/ directory
Application steps:
1. Visit https://nls-portal.console.aliyun.com/ to enable service
2. Visit https://nls-portal.console.aliyun.com/applist to get appkey
3. Visit https://nls-portal.console.aliyun.com/overview to get token
4. Fill into configuration file
Note: token is temporary with 24 hour validity, for long-term use need to configure access_key_id and access_key_secret' WHERE id = 'TTS_AliyunTTS';

-- Tencent TTS configuration documentation
UPDATE ai_model_config SET
doc_link = 'https://console.cloud.tencent.com/cam/capi',
remark = 'Tencent TTS configuration instructions:
1. Need to enable Intelligent Speech Interaction service on Tencent Cloud platform
2. Supports multiple voices, currently configured to use 101001
3. Requires network connection
4. Output files saved in tmp/ directory
Application steps:
1. Visit https://console.cloud.tencent.com/cam/capi to get keys
2. Visit https://console.cloud.tencent.com/tts/resourcebundle to claim free resources
3. Create new application
4. Obtain appid, secret_id and secret_key
5. Fill into configuration file' WHERE id = 'TTS_TencentTTS';

-- 302AI TTS configuration documentation
UPDATE ai_model_config SET
doc_link = 'https://dash.302.ai/',
remark = '302AI TTS configuration instructions:
1. Need to create account on 302 platform and obtain API key
2. Supports multiple voices, currently configured to use Taiwan Xiao He voice
3. Requires network connection
4. Output files saved in tmp/ directory
Application steps:
1. Visit https://dash.302.ai/ to register account
2. Visit https://dash.302.ai/apis/list to get API key
3. Fill into configuration file
Pricing: $35/million characters' WHERE id = 'TTS_TTS302AI';

-- Gizwits TTS configuration documentation
UPDATE ai_model_config SET
doc_link = 'https://agentrouter.gizwitsapi.com/panel/token',
remark = 'Gizwits TTS configuration instructions:
1. Need to obtain API key on Gizwits platform
2. Supports multiple voices, currently configured to use Taiwan Xiao He voice
3. Requires network connection
4. Output files saved in tmp/ directory
Application steps:
1. Visit https://agentrouter.gizwitsapi.com/panel/token to get API key
2. Fill into configuration file
Note: First 10,000 registered users will receive 5 yuan trial credit' WHERE id = 'TTS_GizwitsTTS';

-- ACGN TTS configuration documentation
UPDATE ai_model_config SET
doc_link = 'https://acgn.ttson.cn/',
remark = 'ACGN TTS configuration instructions:
1. Need to purchase token on ttson platform
2. Supports multiple character voices, currently configured to use character ID: 1695
3. Requires network connection
4. Output files saved in tmp/ directory
Application steps:
1. Visit https://acgn.ttson.cn/ to view character list
2. Visit www.ttson.cn to purchase token
3. Fill into configuration file
For development questions please submit to QQ on website' WHERE id = 'TTS_ACGNTTS';

-- OpenAI TTS configuration documentation
UPDATE ai_model_config SET
doc_link = 'https://platform.openai.com/api-keys',
remark = 'OpenAI TTS configuration instructions:
1. Need to obtain API key on OpenAI platform
2. Supports multiple voices, currently configured to use onyx
3. Requires network connection
4. Output files saved in tmp/ directory
Application steps:
1. Visit https://platform.openai.com/api-keys to get API key
2. Fill into configuration file
Note: Requires proxy access from mainland China' WHERE id = 'TTS_OpenAITTS';

-- Custom TTS configuration documentation
UPDATE ai_model_config SET
doc_link = NULL,
remark = 'Custom TTS configuration instructions:
1. Supports custom TTS interface service
2. Uses GET method for requests
3. Requires network connection
4. Output files saved in tmp/ directory
Configuration instructions:
1. Configure request parameters in params
2. Configure request headers in headers
3. Set returned audio format' WHERE id = 'TTS_CustomTTS';

-- Volcano Engine Edge AI Gateway TTS configuration documentation
UPDATE ai_model_config SET
doc_link = 'https://console.volcengine.com/vei/aigateway/',
remark = 'Volcano Engine Edge AI Gateway TTS configuration instructions:
1. Visit https://console.volcengine.com/vei/aigateway/
2. Create gateway access key, search and check Doubao-Speech Synthesis
3. If need to use LLM, also check Doubao-pro-32k-functioncall
4. Visit https://console.volcengine.com/vei/aigateway/tokens-list to get key
5. Fill into configuration file
Voice list reference: https://www.volcengine.com/docs/6561/1257544' WHERE id = 'TTS_VolcesAiGatewayTTS';

-- Update LLM model configuration documentation
-- ChatGLM configuration documentation
UPDATE ai_model_config SET
doc_link = 'https://bigmodel.cn/usercenter/proj-mgmt/apikeys',
remark = 'ChatGLM configuration instructions:
1. Visit https://bigmodel.cn/usercenter/proj-mgmt/apikeys
2. Register and obtain API key
3. Fill into configuration file' WHERE id = 'LLM_ChatGLMLLM';

-- Ollama configuration documentation
UPDATE ai_model_config SET
doc_link = 'https://ollama.com/',
remark = 'Ollama configuration instructions:
1. Install Ollama service
2. Run command: ollama pull qwen2.5
3. Ensure service running at http://localhost:11434' WHERE id = 'LLM_OllamaLLM';

-- Tongyi Qianwen configuration documentation
UPDATE ai_model_config SET
doc_link = 'https://bailian.console.aliyun.com/?apiKey=1#/api-key',
remark = 'Tongyi Qianwen configuration instructions:
1. Visit https://bailian.console.aliyun.com/?apiKey=1#/api-key
2. Obtain API key
3. Fill into configuration file, currently configured to use qwen-turbo model
4. Supports custom parameters: temperature=0.7, max_tokens=500, top_p=1, top_k=50' WHERE id = 'LLM_AliLLM';

-- Tongyi Bailian configuration documentation
UPDATE ai_model_config SET
doc_link = 'https://bailian.console.aliyun.com/?apiKey=1#/api-key',
remark = 'Tongyi Bailian configuration instructions:
1. Visit https://bailian.console.aliyun.com/?apiKey=1#/api-key
2. Obtain app_id and api_key
3. Fill into configuration file' WHERE id = 'LLM_AliAppLLM';

-- Doubao LLM configuration documentation
UPDATE ai_model_config SET
doc_link = 'https://console.volcengine.com/ark/region:ark+cn-beijing/openManagement',
remark = 'Doubao LLM configuration instructions:
1. Visit https://console.volcengine.com/ark/region:ark+cn-beijing/openManagement
2. Enable Doubao-1.5-pro service
3. Visit https://console.volcengine.com/ark/region:ark+cn-beijing/apiKey to get API key
4. Fill into configuration file
5. Currently recommend using doubao-1-5-pro-32k-250115
Note: Has free quota of 500000 tokens' WHERE id = 'LLM_DoubaoLLM';

-- DeepSeek configuration documentation
UPDATE ai_model_config SET
doc_link = 'https://platform.deepseek.com/',
remark = 'DeepSeek configuration instructions:
1. Visit https://platform.deepseek.com/
2. Register and obtain API key
3. Fill into configuration file' WHERE id = 'LLM_DeepSeekLLM';

-- Dify configuration documentation
UPDATE ai_model_config SET
doc_link = 'https://cloud.dify.ai/',
remark = 'Dify configuration instructions:
1. Visit https://cloud.dify.ai/
2. Register and obtain API key
3. Fill into configuration file
4. Supports multiple conversation modes: workflows/run, chat-messages, completion-messages
5. Role definitions set on platform will be invalid, need to set in Dify console
Note: Recommend using locally deployed Dify interface, access to public cloud interface may be restricted in some regions of China' WHERE id = 'LLM_DifyLLM';

-- Gemini configuration documentation
UPDATE ai_model_config SET
doc_link = 'https://aistudio.google.com/apikey',
remark = 'Gemini configuration instructions:
1. Uses Google Gemini API service
2. Currently configured to use gemini-2.0-flash model
3. Requires network connection
4. Supports proxy configuration
Application steps:
1. Visit https://aistudio.google.com/apikey
2. Create API key
3. Fill into configuration file
Note: If using in mainland China, please comply with "Interim Measures for the Management of Generative Artificial Intelligence Services"' WHERE id = 'LLM_GeminiLLM';

-- Coze configuration documentation
UPDATE ai_model_config SET
doc_link = 'https://www.coze.cn/open/oauth/pats',
remark = 'Coze configuration instructions:
1. Uses Coze platform service
2. Requires bot_id, user_id and personal token
3. Requires network connection
Application steps:
1. Visit https://www.coze.cn/open/oauth/pats
2. Obtain personal token
3. Manually calculate bot_id and user_id
4. Fill into configuration file' WHERE id = 'LLM_CozeLLM';

-- LM Studio configuration documentation
UPDATE ai_model_config SET
doc_link = 'https://lmstudio.ai/',
remark = 'LM Studio configuration instructions:
1. Uses locally deployed LM Studio service
2. Currently configured to use deepseek-r1-distill-llama-8b@q4_k_m model
3. Local inference, no network connection required
4. Need to download model in advance
Deployment steps:
1. Install LM Studio
2. Download model from community
3. Ensure service running at http://localhost:1234/v1' WHERE id = 'LLM_LMStudioLLM';

-- FastGPT configuration documentation
UPDATE ai_model_config SET
doc_link = 'https://cloud.tryfastgpt.ai/account/apikey',
remark = 'FastGPT configuration instructions:
1. Uses FastGPT platform service
2. Requires network connection
3. Prompt in configuration file is invalid, need to set in FastGPT console
4. Supports custom variables
Application steps:
1. Visit https://cloud.tryfastgpt.ai/account/apikey
2. Obtain API key
3. Fill into configuration file' WHERE id = 'LLM_FastgptLLM';

-- Xinference configuration documentation
UPDATE ai_model_config SET
doc_link = 'https://github.com/xorbitsai/inference',
remark = 'Xinference configuration instructions:
1. Uses locally deployed Xinference service
2. Currently configured to use qwen2.5:72b-AWQ model
3. Local inference, no network connection required
4. Need to start corresponding model in advance
Deployment steps:
1. Install Xinference
2. Start service and load model
3. Ensure service running at http://localhost:9997' WHERE id = 'LLM_XinferenceLLM';

-- Xinference small model configuration documentation
UPDATE ai_model_config SET
doc_link = 'https://github.com/xorbitsai/inference',
remark = 'Xinference small model configuration instructions:
1. Uses locally deployed Xinference service
2. Currently configured to use qwen2.5:3b-AWQ model
3. Local inference, no network connection required
4. Used for intent recognition
Deployment steps:
1. Install Xinference
2. Start service and load model
3. Ensure service running at http://localhost:9997' WHERE id = 'LLM_XinferenceSmallLLM';

-- Volcano Engine Edge AI Gateway LLM configuration documentation
UPDATE ai_model_config SET
doc_link = 'https://console.volcengine.com/vei/aigateway/',
remark = 'Volcano Engine Edge AI Gateway LLM configuration instructions:
1. Uses Volcano Engine Edge AI Gateway service
2. Requires gateway access key
3. Requires network connection
4. Supports function_call capability
Application steps:
1. Visit https://console.volcengine.com/vei/aigateway/
2. Create gateway access key, search and check Doubao-pro-32k-functioncall
3. If need to use speech synthesis, also check Doubao-Speech Synthesis
4. Visit https://console.volcengine.com/vei/aigateway/tokens-list to get key
5. Fill into configuration file' WHERE id = 'LLM_VolcesAiGatewayLLM';

-- Update Memory model configuration documentation
-- No memory configuration documentation
UPDATE ai_model_config SET
doc_link = NULL,
remark = 'No memory configuration instructions:
1. Does not save conversation history
2. Each conversation is independent
3. No additional configuration required
4. Suitable for scenarios with high privacy requirements' WHERE id = 'Memory_nomem';

-- Local short-term memory configuration documentation
UPDATE ai_model_config SET
doc_link = NULL,
remark = 'Local short-term memory configuration instructions:
1. Uses local storage to save conversation history
2. Summarizes conversation content through selected_module LLM
3. Data saved locally, not uploaded to server
4. Suitable for privacy-focused scenarios
5. No additional configuration required' WHERE id = 'Memory_mem_local_short';

-- Mem0AI memory configuration documentation
UPDATE ai_model_config SET
doc_link = 'https://app.mem0.ai/dashboard/api-keys',
remark = 'Mem0AI memory configuration instructions:
1. Uses Mem0AI service to save conversation history
2. Requires API key
3. Requires network connection
4. Has 1000 free calls per month
Application steps:
1. Visit https://app.mem0.ai/dashboard/api-keys
2. Obtain API key
3. Fill into configuration file' WHERE id = 'Memory_mem0ai';

-- Update Intent model configuration documentation
-- No intent recognition configuration documentation
UPDATE ai_model_config SET
doc_link = NULL,
remark = 'No intent recognition configuration instructions:
1. Does not perform intent recognition
2. All conversations passed directly to LLM for processing
3. No additional configuration required
4. Suitable for simple conversation scenarios' WHERE id = 'Intent_nointent';

-- LLM intent recognition configuration documentation
UPDATE ai_model_config SET
doc_link = NULL,
remark = 'LLM intent recognition configuration instructions:
1. Uses independent LLM for intent recognition
2. Default uses selected_module.LLM model
3. Can configure to use independent LLM (such as free ChatGLMLLM)
4. Highly versatile, but increases processing time
5. Does not support IOT operations like volume control
Configuration instructions:
1. Specify LLM model to use in llm field
2. If not specified, uses selected_module.LLM model' WHERE id = 'Intent_intent_llm';

-- Function call intent recognition configuration documentation
UPDATE ai_model_config SET
doc_link = NULL,
remark = 'Function call intent recognition configuration instructions:
1. Uses LLM function_call capability for intent recognition
2. Requires selected LLM to support function_call
3. Calls tools on demand, fast processing speed
4. Supports all IOT commands
5. Default loaded capabilities:
   - handle_exit_intent (exit recognition)
   - play_music (music playback)
   - change_role (role switching)
   - get_weather (weather query)
   - get_news (news query)
Configuration instructions:
1. Configure capability modules to load in functions field
2. System has loaded basic capabilities by default, no need to reconfigure
3. Can add custom capability modules' WHERE id = 'Intent_function_call';

-- Update VAD model configuration documentation
-- SileroVAD configuration documentation
UPDATE ai_model_config SET
doc_link = 'https://github.com/snakers4/silero-vad',
remark = 'SileroVAD configuration instructions:
1. Uses SileroVAD model for voice activity detection
2. Local inference, no network connection required
3. Need to download model files to models/snakers4_silero-vad directory
4. Configurable parameters:
   - threshold: 0.5 (voice detection threshold)
   - min_silence_duration_ms: 700 (minimum silence duration in milliseconds)
5. If speech pauses are relatively long, can appropriately increase min_silence_duration_ms value' WHERE id = 'VAD_SileroVAD';
