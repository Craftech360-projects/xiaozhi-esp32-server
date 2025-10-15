-- Modify custom TTS interface request definition
UPDATE ai_model_provider SET fields =
'[{"key":"url","label":"Service Address","type":"string"},{"key":"method","label":"Request Method","type":"string"},{"key":"params","label":"Request Parameters","type":"dict","dict_name":"params"},{"key":"headers","label":"Request Headers","type":"dict","dict_name":"headers"},{"key":"format","label":"Audio Format","type":"string"},{"key":"output_dir","label":"Output Directory","type":"string"}]'
WHERE id = 'SYSTEM_TTS_custom';

-- Modify custom TTS configuration documentation
UPDATE ai_model_config SET
doc_link = NULL,
remark = 'Custom TTS configuration instructions:
1. Custom TTS interface service, request parameters customizable, can integrate with many TTS services
2. Taking locally deployed KokoroTTS as example
3. For CPU only: docker run -p 8880:8880 ghcr.io/remsky/kokoro-fastapi-cpu:latest
4. For GPU: docker run --gpus all -p 8880:8880 ghcr.io/remsky/kokoro-fastapi-gpu:latest
Configuration instructions:
1. Configure request parameters in params, use JSON format
   Example for KokoroTTS: { "input": "{prompt_text}", "speed": 1, "voice": "zm_yunxi", "stream": true, "download_format": "mp3", "response_format": "mp3", "return_download_link": true }
2. Configure request headers in headers
3. Set returned audio format' WHERE id = 'TTS_CustomTTS';
