-- Translate provider field labels from Chinese to English
-- This will update the field labels shown in the Call Information section

-- Update common field labels across all providers
UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"API密钥"', '"label":"API Key"')::json
WHERE fields::text LIKE '%"label":"API密钥"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"服务地址"', '"label":"Service URL"')::json
WHERE fields::text LIKE '%"label":"服务地址"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"基础URL"', '"label":"Base URL"')::json
WHERE fields::text LIKE '%"label":"基础URL"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"模型名称"', '"label":"Model Name"')::json
WHERE fields::text LIKE '%"label":"模型名称"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"输出目录"', '"label":"Output Directory"')::json
WHERE fields::text LIKE '%"label":"输出目录"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"端口号"', '"label":"Port"')::json
WHERE fields::text LIKE '%"label":"端口号"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"服务类型"', '"label":"Service Type"')::json
WHERE fields::text LIKE '%"label":"服务类型"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"是否使用SSL"', '"label":"Use SSL"')::json
WHERE fields::text LIKE '%"label":"是否使用SSL"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"请求方式"', '"label":"Request Method"')::json
WHERE fields::text LIKE '%"label":"请求方式"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"请求参数"', '"label":"Request Parameters"')::json
WHERE fields::text LIKE '%"label":"请求参数"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"请求头"', '"label":"Request Headers"')::json
WHERE fields::text LIKE '%"label":"请求头"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"音频格式"', '"label":"Audio Format"')::json
WHERE fields::text LIKE '%"label":"音频格式"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"访问令牌"', '"label":"Access Token"')::json
WHERE fields::text LIKE '%"label":"访问令牌"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"响应格式"', '"label":"Response Format"')::json
WHERE fields::text LIKE '%"label":"响应格式"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"音色"', '"label":"Voice"')::json
WHERE fields::text LIKE '%"label":"音色"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"应用密钥"', '"label":"App Key"')::json
WHERE fields::text LIKE '%"label":"应用密钥"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"访问密钥ID"', '"label":"Access Key ID"')::json
WHERE fields::text LIKE '%"label":"访问密钥ID"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"访问密钥密码"', '"label":"Access Key Secret"')::json
WHERE fields::text LIKE '%"label":"访问密钥密码"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"授权"', '"label":"Authorization"')::json
WHERE fields::text LIKE '%"label":"授权"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"速度"', '"label":"Speed"')::json
WHERE fields::text LIKE '%"label":"速度"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"温度"', '"label":"Temperature"')::json
WHERE fields::text LIKE '%"label":"温度"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"音色ID"', '"label":"Voice ID"')::json
WHERE fields::text LIKE '%"label":"音色ID"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"采样率"', '"label":"Sample Rate"')::json
WHERE fields::text LIKE '%"label":"采样率"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"参考音频"', '"label":"Reference Audio"')::json
WHERE fields::text LIKE '%"label":"参考音频"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"参考文本"', '"label":"Reference Text"')::json
WHERE fields::text LIKE '%"label":"参考文本"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"是否标准化"', '"label":"Normalize"')::json
WHERE fields::text LIKE '%"label":"是否标准化"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"最大新令牌数"', '"label":"Max New Tokens"')::json
WHERE fields::text LIKE '%"label":"最大新令牌数"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"块长度"', '"label":"Chunk Length"')::json
WHERE fields::text LIKE '%"label":"块长度"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"重复惩罚"', '"label":"Repetition Penalty"')::json
WHERE fields::text LIKE '%"label":"重复惩罚"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"是否流式"', '"label":"Streaming"')::json
WHERE fields::text LIKE '%"label":"是否流式"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"是否使用内存缓存"', '"label":"Use Memory Cache"')::json
WHERE fields::text LIKE '%"label":"是否使用内存缓存"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"种子"', '"label":"Seed"')::json
WHERE fields::text LIKE '%"label":"种子"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"通道数"', '"label":"Channels"')::json
WHERE fields::text LIKE '%"label":"通道数"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"参考ID"', '"label":"Reference ID"')::json
WHERE fields::text LIKE '%"label":"参考ID"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"组ID"', '"label":"Group ID"')::json
WHERE fields::text LIKE '%"label":"组ID"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"文本语言"', '"label":"Text Language"')::json
WHERE fields::text LIKE '%"label":"文本语言"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"参考音频路径"', '"label":"Reference Audio Path"')::json
WHERE fields::text LIKE '%"label":"参考音频路径"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"提示文本"', '"label":"Prompt Text"')::json
WHERE fields::text LIKE '%"label":"提示文本"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"提示语言"', '"label":"Prompt Language"')::json
WHERE fields::text LIKE '%"label":"提示语言"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"文本分割方法"', '"label":"Text Split Method"')::json
WHERE fields::text LIKE '%"label":"文本分割方法"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"批处理大小"', '"label":"Batch Size"')::json
WHERE fields::text LIKE '%"label":"批处理大小"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"批处理阈值"', '"label":"Batch Threshold"')::json
WHERE fields::text LIKE '%"label":"批处理阈值"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"是否分桶"', '"label":"Split Bucket"')::json
WHERE fields::text LIKE '%"label":"是否分桶"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"是否返回片段"', '"label":"Return Fragment"')::json
WHERE fields::text LIKE '%"label":"是否返回片段"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"速度因子"', '"label":"Speed Factor"')::json
WHERE fields::text LIKE '%"label":"速度因子"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"是否流式模式"', '"label":"Streaming Mode"')::json
WHERE fields::text LIKE '%"label":"是否流式模式"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"是否并行推理"', '"label":"Parallel Inference"')::json
WHERE fields::text LIKE '%"label":"是否并行推理"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"辅助参考音频路径"', '"label":"Auxiliary Reference Audio Paths"')::json
WHERE fields::text LIKE '%"label":"辅助参考音频路径"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"切分标点"', '"label":"Cut Punctuation"')::json
WHERE fields::text LIKE '%"label":"切分标点"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"输入参考"', '"label":"Input References"')::json
WHERE fields::text LIKE '%"label":"输入参考"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"采样步数"', '"label":"Sample Steps"')::json
WHERE fields::text LIKE '%"label":"采样步数"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"是否使用SR"', '"label":"Use SR"')::json
WHERE fields::text LIKE '%"label":"是否使用SR"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"音调因子"', '"label":"Pitch Factor"')::json
WHERE fields::text LIKE '%"label":"音调因子"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"音量变化"', '"label":"Volume Change dB"')::json
WHERE fields::text LIKE '%"label":"音量变化"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"目标语言"', '"label":"Target Language"')::json
WHERE fields::text LIKE '%"label":"目标语言"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"格式"', '"label":"Format"')::json
WHERE fields::text LIKE '%"label":"格式"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"情感"', '"label":"Emotion"')::json
WHERE fields::text LIKE '%"label":"情感"%';

-- Additional field translations
UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"应用ID"', '"label":"App ID"')::json
WHERE fields::text LIKE '%"label":"应用ID"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"应用AppID"', '"label":"App ID"')::json
WHERE fields::text LIKE '%"label":"应用AppID"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"应用AppKey"', '"label":"App Key"')::json
WHERE fields::text LIKE '%"label":"应用AppKey"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"临时Token"', '"label":"Temporary Token"')::json
WHERE fields::text LIKE '%"label":"临时Token"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"AccessKey ID"', '"label":"Access Key ID"')::json
WHERE fields::text LIKE '%"label":"AccessKey ID"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"AccessKey Secret"', '"label":"Access Key Secret"')::json
WHERE fields::text LIKE '%"label":"AccessKey Secret"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"API服务地址"', '"label":"API Service URL"')::json
WHERE fields::text LIKE '%"label":"API服务地址"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"API地址"', '"label":"API URL"')::json
WHERE fields::text LIKE '%"label":"API地址"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"WebSocket地址"', '"label":"WebSocket URL"')::json
WHERE fields::text LIKE '%"label":"WebSocket地址"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"资源ID"', '"label":"Resource ID"')::json
WHERE fields::text LIKE '%"label":"资源ID"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"默认音色"', '"label":"Default Voice"')::json
WHERE fields::text LIKE '%"label":"默认音色"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"断句检测时间"', '"label":"Sentence Silence Detection Time"')::json
WHERE fields::text LIKE '%"label":"断句检测时间"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"集群"', '"label":"Cluster"')::json
WHERE fields::text LIKE '%"label":"集群"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"热词文件名称"', '"label":"Hotword File Name"')::json
WHERE fields::text LIKE '%"label":"热词文件名称"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"替换词文件名称"', '"label":"Replacement File Name"')::json
WHERE fields::text LIKE '%"label":"替换词文件名称"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"区域"', '"label":"Region"')::json
WHERE fields::text LIKE '%"label":"区域"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"语言参数"', '"label":"Language Parameter"')::json
WHERE fields::text LIKE '%"label":"语言参数"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"音量"', '"label":"Volume"')::json
WHERE fields::text LIKE '%"label":"音量"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"语速"', '"label":"Speech Rate"')::json
WHERE fields::text LIKE '%"label":"语速"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"音调"', '"label":"Pitch"')::json
WHERE fields::text LIKE '%"label":"音调"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"检测阈值"', '"label":"Detection Threshold"')::json
WHERE fields::text LIKE '%"label":"检测阈值"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"模型目录"', '"label":"Model Directory"')::json
WHERE fields::text LIKE '%"label":"模型目录"%';

UPDATE ai_model_provider 
SET fields = REPLACE(fields::text, '"label":"最小静音时长"', '"label":"Min Silence Duration"')::json
WHERE fields::text LIKE '%"label":"最小静音时长"%';

-- Update placeholder values in ai_model_config
UPDATE ai_model_config 
SET config_json = REPLACE(config_json::text, '"你的api_key"', '"your_api_key"')::json
WHERE config_json::text LIKE '%"你的api_key"%';

UPDATE ai_model_config 
SET config_json = REPLACE(config_json::text, '"你的网关访问密钥"', '"your_gateway_access_key"')::json
WHERE config_json::text LIKE '%"你的网关访问密钥"%';

UPDATE ai_model_config 
SET config_json = REPLACE(config_json::text, '"你的app_id"', '"your_app_id"')::json
WHERE config_json::text LIKE '%"你的app_id"%';

UPDATE ai_model_config 
SET config_json = REPLACE(config_json::text, '"你的bot_id"', '"your_bot_id"')::json
WHERE config_json::text LIKE '%"你的bot_id"%';

UPDATE ai_model_config 
SET config_json = REPLACE(config_json::text, '"你的user_id"', '"your_user_id"')::json
WHERE config_json::text LIKE '%"你的user_id"%';

UPDATE ai_model_config 
SET config_json = REPLACE(config_json::text, '"你的personal_access_token"', '"your_personal_access_token"')::json
WHERE config_json::text LIKE '%"你的personal_access_token"%';

UPDATE ai_model_config 
SET config_json = REPLACE(config_json::text, '"你的home assistant api访问令牌"', '"your_home_assistant_api_token"')::json
WHERE config_json::text LIKE '%"你的home assistant api访问令牌"%';

UPDATE ai_model_config 
SET config_json = REPLACE(config_json::text, '"你的Secret ID"', '"your_secret_id"')::json
WHERE config_json::text LIKE '%"你的Secret ID"%';

UPDATE ai_model_config 
SET config_json = REPLACE(config_json::text, '"你的Secret Key"', '"your_secret_key"')::json
WHERE config_json::text LIKE '%"你的Secret Key"%';

UPDATE ai_model_config 
SET config_json = REPLACE(config_json::text, '"你的appkey"', '"your_appkey"')::json
WHERE config_json::text LIKE '%"你的appkey"%';

UPDATE ai_model_config 
SET config_json = REPLACE(config_json::text, '"你的access_key_id"', '"your_access_key_id"')::json
WHERE config_json::text LIKE '%"你的access_key_id"%';

UPDATE ai_model_config 
SET config_json = REPLACE(config_json::text, '"你的access_key_secret"', '"your_access_key_secret"')::json
WHERE config_json::text LIKE '%"你的access_key_secret"%';

UPDATE ai_model_config 
SET config_json = REPLACE(config_json::text, '"你的API Key"', '"your_api_key"')::json
WHERE config_json::text LIKE '%"你的API Key"%';

UPDATE ai_model_config 
SET config_json = REPLACE(config_json::text, '"你的应用ID"', '"your_app_id"')::json
WHERE config_json::text LIKE '%"你的应用ID"%';

UPDATE ai_model_config 
SET config_json = REPLACE(config_json::text, '"你的音色ID"', '"your_voice_id"')::json
WHERE config_json::text LIKE '%"你的音色ID"%';

UPDATE ai_model_config 
SET config_json = REPLACE(config_json::text, '"你的访问令牌"', '"your_access_token"')::json
WHERE config_json::text LIKE '%"你的访问令牌"%';

UPDATE ai_model_config 
SET config_json = REPLACE(config_json::text, '"你的资源ID"', '"your_resource_id"')::json
WHERE config_json::text LIKE '%"你的资源ID"%';

UPDATE ai_model_config 
SET config_json = REPLACE(config_json::text, '"你的默认音色"', '"your_default_voice"')::json
WHERE config_json::text LIKE '%"你的默认音色"%';

UPDATE ai_model_config 
SET config_json = REPLACE(config_json::text, '"你的集群"', '"your_cluster"')::json
WHERE config_json::text LIKE '%"你的集群"%';