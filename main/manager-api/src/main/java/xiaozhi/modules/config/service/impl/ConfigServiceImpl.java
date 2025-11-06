package xiaozhi.modules.config.service.impl;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;

import org.apache.commons.lang3.StringUtils;
import org.springframework.stereotype.Service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;

import lombok.AllArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import xiaozhi.common.constant.Constant;
import xiaozhi.common.exception.ErrorCode;
import xiaozhi.common.exception.RenException;
import xiaozhi.common.redis.RedisKeys;
import xiaozhi.common.redis.RedisUtils;
import xiaozhi.common.utils.ConvertUtils;
import xiaozhi.common.utils.JsonUtils;
import xiaozhi.modules.agent.dao.AgentVoicePrintDao;
import xiaozhi.modules.agent.entity.AgentEntity;
import xiaozhi.modules.agent.entity.AgentPluginMapping;
import xiaozhi.modules.agent.entity.AgentTemplateEntity;
import xiaozhi.modules.agent.entity.AgentVoicePrintEntity;
import xiaozhi.modules.agent.service.AgentMcpAccessPointService;
import xiaozhi.modules.agent.service.AgentPluginMappingService;
import xiaozhi.modules.agent.service.AgentService;
import xiaozhi.modules.agent.service.AgentTemplateService;
import xiaozhi.modules.agent.vo.AgentVoicePrintVO;
import xiaozhi.modules.config.service.ConfigService;
import xiaozhi.modules.device.entity.DeviceEntity;
import xiaozhi.modules.device.service.DeviceService;
import xiaozhi.modules.model.entity.ModelConfigEntity;
import xiaozhi.modules.model.service.ModelConfigService;
import xiaozhi.modules.sys.dto.SysParamsDTO;
import xiaozhi.modules.sys.service.SysParamsService;
import xiaozhi.modules.timbre.service.TimbreService;
import xiaozhi.modules.timbre.vo.TimbreDetailsVO;
import xiaozhi.modules.sys.service.KidProfileService;
import xiaozhi.modules.sys.dto.KidProfileDTO;
import xiaozhi.modules.config.dto.ChildProfileDTO;

@Slf4j
@Service
@AllArgsConstructor
public class ConfigServiceImpl implements ConfigService {
    private final SysParamsService sysParamsService;
    private final DeviceService deviceService;
    private final ModelConfigService modelConfigService;
    private final AgentService agentService;
    private final AgentTemplateService agentTemplateService;
    private final RedisUtils redisUtils;
    private final TimbreService timbreService;
    private final AgentPluginMappingService agentPluginMappingService;
    private final AgentMcpAccessPointService agentMcpAccessPointService;
    private final AgentVoicePrintDao agentVoicePrintDao;
    private final KidProfileService kidProfileService;

    @Override
    public Object getConfig(Boolean isCache) {
        if (isCache) {
            // 先从Redis获取配置
            Object cachedConfig = redisUtils.get(RedisKeys.getServerConfigKey());
            if (cachedConfig != null) {
                return cachedConfig;
            }
        }

        // 构建配置信息
        Map<String, Object> result = new HashMap<>();
        buildConfig(result);

        // 查询默认智能体
        AgentTemplateEntity agent = agentTemplateService.getDefaultTemplate();
        if (agent == null) {
            throw new RenException("默认智能体未找到");
        }

        // 构建模块配置
        buildModuleConfig(
                null,
                null,
                null,
                null,
                null,
                null,
                agent.getVadModelId(),
                agent.getAsrModelId(),
                agent.getLlmModelId(),    // Add this
                agent.getVllmModelId(),   // Add this
                agent.getTtsModelId(),    // Add this
                agent.getMemModelId(),    // Add this
                agent.getIntentModelId(), // Add this
                result,
                isCache);

        // 将配置存入Redis
        redisUtils.set(RedisKeys.getServerConfigKey(), result);

        return result;
    }

    @Override
    public Map<String, Object> getAgentModels(String macAddress, Map<String, String> selectedModule) {
        // 根据MAC地址查找设备
        DeviceEntity device = deviceService.getDeviceByMacAddress(macAddress);
        if (device == null) {
            // 如果设备，去redis里看看有没有需要连接的设备
            String cachedCode = deviceService.geCodeByDeviceId(macAddress);
            if (StringUtils.isNotBlank(cachedCode)) {
                throw new RenException(ErrorCode.OTA_DEVICE_NEED_BIND, cachedCode);
            }
            throw new RenException(ErrorCode.OTA_DEVICE_NOT_FOUND, "not found device");
        }

        // 获取智能体信息
        AgentEntity agent = agentService.getAgentById(device.getAgentId());
        if (agent == null) {
            throw new RenException("智能体未找到");
        }
        // 获取音色信息
        String voice = null;
        String referenceAudio = null;
        String referenceText = null;
        TimbreDetailsVO timbre = timbreService.get(agent.getTtsVoiceId());
        if (timbre != null) {
            voice = timbre.getTtsVoice();
            referenceAudio = timbre.getReferenceAudio();
            referenceText = timbre.getReferenceText();
        }
        // 构建返回数据
        Map<String, Object> result = new HashMap<>();
        // 获取单台设备每天最多输出字数
        String deviceMaxOutputSize = sysParamsService.getValue("device_max_output_size", true);
        result.put("device_max_output_size", deviceMaxOutputSize);

        // 获取聊天记录配置
        Integer chatHistoryConf = agent.getChatHistoryConf();
        if (agent.getMemModelId() != null && agent.getMemModelId().equals(Constant.MEMORY_NO_MEM)) {
            chatHistoryConf = Constant.ChatHistoryConfEnum.IGNORE.getCode();
        } else if (agent.getMemModelId() != null
                && !agent.getMemModelId().equals(Constant.MEMORY_NO_MEM)
                && agent.getChatHistoryConf() == null) {
            chatHistoryConf = Constant.ChatHistoryConfEnum.RECORD_TEXT.getCode();
        }
        result.put("chat_history_conf", chatHistoryConf);
        // 如果客户端已实例化模型，则不返回
        String alreadySelectedVadModelId = (String) selectedModule.get("VAD");
        if (alreadySelectedVadModelId != null && alreadySelectedVadModelId.equals(agent.getVadModelId())) {
            agent.setVadModelId(null);
        }
        String alreadySelectedAsrModelId = (String) selectedModule.get("ASR");
        if (alreadySelectedAsrModelId != null && alreadySelectedAsrModelId.equals(agent.getAsrModelId())) {
            agent.setAsrModelId(null);
        }

        // 添加函数调用参数信息
        if (!Objects.equals(agent.getIntentModelId(), "Intent_nointent")) {
            String agentId = agent.getId();
            List<AgentPluginMapping> pluginMappings = agentPluginMappingService.agentPluginParamsByAgentId(agentId);
            if (pluginMappings != null && !pluginMappings.isEmpty()) {
                Map<String, Object> pluginParams = new HashMap<>();
                for (AgentPluginMapping pluginMapping : pluginMappings) {
                    pluginParams.put(pluginMapping.getProviderCode(), pluginMapping.getParamInfo());
                }
                result.put("plugins", pluginParams);
            }
        }
        // 获取mcp接入点地址
        String mcpEndpoint = agentMcpAccessPointService.getAgentMcpAccessAddress(agent.getId());
        if (StringUtils.isNotBlank(mcpEndpoint) && mcpEndpoint.startsWith("ws")) {
            mcpEndpoint = mcpEndpoint.replace("/mcp/", "/call/");
            result.put("mcp_endpoint", mcpEndpoint);
        }
        // 获取声纹信息
        buildVoiceprintConfig(agent.getId(), result);

        // 构建模块配置
        buildModuleConfig(
                agent.getAgentName(),
                agent.getSystemPrompt(),
                agent.getSummaryMemory(),
                voice,
                referenceAudio,
                referenceText,
                agent.getVadModelId(),
                agent.getAsrModelId(),
                agent.getLlmModelId(),
                agent.getVllmModelId(),
                agent.getTtsModelId(),
                agent.getMemModelId(),
                agent.getIntentModelId(),
                result,
                true);

        return result;
    }

    /**
     * 构建配置信息
     * 
     * @param config 系统参数列表
     * @return 配置信息
     */
    private Object buildConfig(Map<String, Object> config) {

        // 查询所有系统参数
        List<SysParamsDTO> paramsList = sysParamsService.list(new HashMap<>());

        for (SysParamsDTO param : paramsList) {
            String[] keys = param.getParamCode().split("\\.");
            Map<String, Object> current = config;

            // 遍历除最后一个key之外的所有key
            for (int i = 0; i < keys.length - 1; i++) {
                String key = keys[i];
                if (!current.containsKey(key)) {
                    current.put(key, new HashMap<String, Object>());
                }
                current = (Map<String, Object>) current.get(key);
            }

            // 处理最后一个key
            String lastKey = keys[keys.length - 1];
            String value = param.getParamValue();

            // 根据valueType转换值
            switch (param.getValueType().toLowerCase()) {
                case "number":
                    try {
                        double doubleValue = Double.parseDouble(value);
                        // 如果数值是整数形式，则转换为Integer
                        if (doubleValue == (int) doubleValue) {
                            current.put(lastKey, (int) doubleValue);
                        } else {
                            current.put(lastKey, doubleValue);
                        }
                    } catch (NumberFormatException e) {
                        current.put(lastKey, value);
                    }
                    break;
                case "boolean":
                    current.put(lastKey, Boolean.parseBoolean(value));
                    break;
                case "array":
                    // 将分号分隔的字符串转换为数字数组
                    List<String> list = new ArrayList<>();
                    for (String num : value.split(";")) {
                        if (StringUtils.isNotBlank(num)) {
                            list.add(num.trim());
                        }
                    }
                    current.put(lastKey, list);
                    break;
                case "json":
                    try {
                        current.put(lastKey, JsonUtils.parseObject(value, Object.class));
                    } catch (Exception e) {
                        current.put(lastKey, value);
                    }
                    break;
                default:
                    current.put(lastKey, value);
            }
        }

        return config;
    }

    /**
     * 构建声纹配置信息
     * 
     * @param agentId 智能体ID
     * @param result  结果Map
     */
    private void buildVoiceprintConfig(String agentId, Map<String, Object> result) {
        try {
            // 获取声纹接口地址
            String voiceprintUrl = sysParamsService.getValue("server.voice_print", true);
            if (StringUtils.isBlank(voiceprintUrl) || "null".equals(voiceprintUrl)) {
                return;
            }

            // 获取智能体关联的声纹信息（不需要用户权限验证）
            List<AgentVoicePrintVO> voiceprints = getVoiceprintsByAgentId(agentId);
            if (voiceprints == null || voiceprints.isEmpty()) {
                return;
            }

            // 构建speakers列表
            List<String> speakers = new ArrayList<>();
            for (AgentVoicePrintVO voiceprint : voiceprints) {
                String speakerStr = String.format("%s,%s,%s",
                        voiceprint.getId(),
                        voiceprint.getSourceName(),
                        voiceprint.getIntroduce() != null ? voiceprint.getIntroduce() : "");
                speakers.add(speakerStr);
            }

            // 构建声纹配置
            Map<String, Object> voiceprintConfig = new HashMap<>();
            voiceprintConfig.put("url", voiceprintUrl);
            voiceprintConfig.put("speakers", speakers);

            result.put("voiceprint", voiceprintConfig);
        } catch (Exception e) {
            // 声纹配置获取失败时不影响其他功能
            System.err.println("获取声纹配置失败: " + e.getMessage());
        }
    }

    /**
     * 获取智能体关联的声纹信息
     * 
     * @param agentId 智能体ID
     * @return 声纹信息列表
     */
    private List<AgentVoicePrintVO> getVoiceprintsByAgentId(String agentId) {
        LambdaQueryWrapper<AgentVoicePrintEntity> queryWrapper = new LambdaQueryWrapper<>();
        queryWrapper.eq(AgentVoicePrintEntity::getAgentId, agentId);
        queryWrapper.orderByAsc(AgentVoicePrintEntity::getCreateDate);
        List<AgentVoicePrintEntity> entities = agentVoicePrintDao.selectList(queryWrapper);
        return ConvertUtils.sourceToTarget(entities, AgentVoicePrintVO.class);
    }

    /**
     * 构建模块配置
     * 
     * @param prompt         提示词
     * @param voice          音色
     * @param referenceAudio 参考音频路径
     * @param referenceText  参考文本
     * @param vadModelId     VAD模型ID
     * @param asrModelId     ASR模型ID
     * @param llmModelId     LLM模型ID
     * @param ttsModelId     TTS模型ID
     * @param memModelId     记忆模型ID
     * @param intentModelId  意图模型ID
     * @param result         结果Map
     */
    private void buildModuleConfig(
            String assistantName,
            String prompt,
            String summaryMemory,
            String voice,
            String referenceAudio,
            String referenceText,
            String vadModelId,
            String asrModelId,
            String llmModelId,
            String vllmModelId,
            String ttsModelId,
            String memModelId,
            String intentModelId,
            Map<String, Object> result,
            boolean isCache) {
        Map<String, String> selectedModule = new HashMap<>();

        String[] modelTypes = { "VAD", "ASR", "TTS", "Memory", "Intent", "LLM", "VLLM" };
        String[] modelIds = { vadModelId, asrModelId, ttsModelId, memModelId, intentModelId, llmModelId, vllmModelId };
        String intentLLMModelId = null;
        String memLocalShortLLMModelId = null;

        for (int i = 0; i < modelIds.length; i++) {
            if (modelIds[i] == null) {
                continue;
            }
            ModelConfigEntity model = modelConfigService.getModelById(modelIds[i], isCache);
            if (model == null) {
                continue;
            }
            Map<String, Object> typeConfig = new HashMap<>();
            if (model.getConfigJson() != null) {
                typeConfig.put(model.getId(), model.getConfigJson());
                // 如果是TTS类型，添加private_voice属性
                if ("TTS".equals(modelTypes[i])) {
                    if (voice != null)
                        ((Map<String, Object>) model.getConfigJson()).put("private_voice", voice);
                    if (referenceAudio != null)
                        ((Map<String, Object>) model.getConfigJson()).put("ref_audio", referenceAudio);
                    if (referenceText != null)
                        ((Map<String, Object>) model.getConfigJson()).put("ref_text", referenceText);
                }
                // 如果是Intent类型，且type=intent_llm，则给他添加附加模型
                if ("Intent".equals(modelTypes[i])) {
                    Map<String, Object> map = (Map<String, Object>) model.getConfigJson();
                    if ("intent_llm".equals(map.get("type"))) {
                        intentLLMModelId = (String) map.get("llm");
                        if (StringUtils.isNotBlank(intentLLMModelId) && intentLLMModelId.equals(llmModelId)) {
                            intentLLMModelId = null;
                        }
                    }
                    if (map.get("functions") != null) {
                        String functionStr = (String) map.get("functions");
                        if (StringUtils.isNotBlank(functionStr)) {
                            String[] functions = functionStr.split("\\;");
                            map.put("functions", functions);
                        }
                    }
                    System.out.println("map: " + map);
                }
                if ("Memory".equals(modelTypes[i])) {
                    Map<String, Object> map = (Map<String, Object>) model.getConfigJson();
                    
                    // Fix for Memory configuration API key
                    if ("mem0ai".equals(map.get("type"))) {
                        // Always use the actual API key from system parameters for mem0
                        String mem0ApiKey = sysParamsService.getValue("mem0.api_key", false);
                        if (StringUtils.isNotBlank(mem0ApiKey)) {
                            map.put("api_key", mem0ApiKey);
                            System.out.println("[DEBUG] Using mem0 API key from system parameters");
                        } else {
                            // Fallback to the original logic
                            String apiKey = (String) map.get("api_key");
                            System.out.println("[DEBUG] No system parameter for mem0.api_key, using config value: " + 
                                             (apiKey != null ? "(length: " + apiKey.length() + ")" : "null"));
                        }
                    }
                    
                    if ("mem_local_short".equals(map.get("type"))) {
                        memLocalShortLLMModelId = (String) map.get("llm");
                        if (StringUtils.isNotBlank(memLocalShortLLMModelId)
                                && memLocalShortLLMModelId.equals(llmModelId)) {
                            memLocalShortLLMModelId = null;
                        }
                    }
                }
                // 如果是LLM类型，且intentLLMModelId不为空，则添加附加模型
                if ("LLM".equals(modelTypes[i])) {
                    if (StringUtils.isNotBlank(intentLLMModelId)) {
                        if (!typeConfig.containsKey(intentLLMModelId)) {
                            ModelConfigEntity intentLLM = modelConfigService.getModelById(intentLLMModelId, isCache);
                            if (intentLLM != null) {
                                typeConfig.put(intentLLM.getId(), intentLLM.getConfigJson());
                            }
                        }
                    }
                    if (StringUtils.isNotBlank(memLocalShortLLMModelId)) {
                        if (!typeConfig.containsKey(memLocalShortLLMModelId)) {
                            ModelConfigEntity memLocalShortLLM = modelConfigService
                                    .getModelById(memLocalShortLLMModelId, isCache);
                            if (memLocalShortLLM != null) {
                                typeConfig.put(memLocalShortLLM.getId(), memLocalShortLLM.getConfigJson());
                            }
                        }
                    }
                }
            }
            result.put(modelTypes[i], typeConfig);

            selectedModule.put(modelTypes[i], model.getId());
        }

        result.put("selected_module", selectedModule);
        if (StringUtils.isNotBlank(prompt)) {
            prompt = prompt.replace("{{assistant_name}}", StringUtils.isBlank(assistantName) ? "小智" : assistantName);
        }
        result.put("prompt", prompt);
        result.put("summaryMemory", summaryMemory);
    }

    @Override
    public String getAgentPrompt(String macAddress) {
        log.info("📡 [PROMPT SERVICE] Fetching prompt from database for MAC: {}", macAddress);

        // 根据MAC地址查找设备
        DeviceEntity device = deviceService.getDeviceByMacAddress(macAddress);
        if (device == null) {
            log.error("❌ [PROMPT SERVICE] Device not found for MAC: {}", macAddress);
            throw new RenException(ErrorCode.OTA_DEVICE_NOT_FOUND, "Device not found for MAC: " + macAddress);
        }
        log.debug("✓ [PROMPT SERVICE] Found device ID: {} for MAC: {}", device.getId(), macAddress);

        // 获取智能体信息
        AgentEntity agent = agentService.selectById(device.getAgentId());
        if (agent == null) {
            log.error("❌ [PROMPT SERVICE] Agent not found for device: {}, agentId: {}",
                macAddress, device.getAgentId());
            throw new RenException("Agent not found for device: " + macAddress);
        }
        log.debug("✓ [PROMPT SERVICE] Found agent: {} (ID: {}) for MAC: {}",
            agent.getAgentName(), agent.getId(), macAddress);

        // 返回系统提示词 (now contains Jinja2 templates directly in database)
        String systemPrompt = agent.getSystemPrompt();
        if (StringUtils.isBlank(systemPrompt)) {
            log.error("❌ [PROMPT SERVICE] No system prompt configured for agent: {} (MAC: {})",
                agent.getAgentName(), macAddress);
            throw new RenException("No system prompt configured for agent: " + agent.getAgentName());
        }

        log.info("✅ [PROMPT SERVICE] Successfully retrieved prompt from DB for MAC: {} - Agent: {} (length: {} chars)",
            macAddress, agent.getAgentName(), systemPrompt.length());

        // Simply return the prompt as-is (templates already in database)
        return systemPrompt;
    }

    @Override
    public ChildProfileDTO getChildProfileByMac(String macAddress) {
        // 根据MAC地址查找设备
        DeviceEntity device = deviceService.getDeviceByMacAddress(macAddress);
        if (device == null) {
            throw new RenException(ErrorCode.OTA_DEVICE_NOT_FOUND, "Device not found for MAC: " + macAddress);
        }

        // 获取设备关联的孩子ID
        Long kidId = device.getKidId();
        if (kidId == null) {
            throw new RenException("No child assigned to this device");
        }

        // 获取孩子资料
        KidProfileDTO kid = kidProfileService.get(kidId);
        if (kid == null) {
            throw new RenException("Child profile not found");
        }

        // 转换为LiveKit使用的ChildProfileDTO
        ChildProfileDTO childProfile = new ChildProfileDTO();
        childProfile.setName(kid.getName());
        childProfile.setAge(kid.getAge());
        childProfile.setAgeGroup(kid.getAgeGroup());
        childProfile.setGender(kid.getGender());
        childProfile.setInterests(kid.getInterests());

        return childProfile;
    }

    @Override
    public String getAgentTemplateId(String macAddress) {
        // 根据MAC地址查找设备
        DeviceEntity device = deviceService.getDeviceByMacAddress(macAddress);
        if (device == null) {
            throw new RenException(ErrorCode.OTA_DEVICE_NOT_FOUND, "Device not found for MAC: " + macAddress);
        }

        // 获取智能体信息
        AgentEntity agent = agentService.selectById(device.getAgentId());
        if (agent == null) {
            throw new RenException("Agent not found for device: " + macAddress);
        }

        // 返回智能体ID（不再使用模板ID）
        return agent.getId();
    }

    @Override
    public String getTemplateContent(String templateId) {
        // templateId 现在实际上是 agentId，直接获取智能体的system_prompt
        AgentEntity agent = agentService.selectById(templateId);
        if (agent == null) {
            throw new RenException("Agent not found for ID: " + templateId);
        }

        // 返回智能体的system_prompt
        String systemPrompt = agent.getSystemPrompt();
        if (StringUtils.isBlank(systemPrompt)) {
            throw new RenException("No system_prompt configured for agent: " + agent.getAgentName());
        }

        return systemPrompt;
    }

    @Override
    public String getDeviceLocation(String macAddress) {
        // 根据MAC地址查找设备
        DeviceEntity device = deviceService.getDeviceByMacAddress(macAddress);
        if (device == null) {
            throw new RenException(ErrorCode.OTA_DEVICE_NOT_FOUND, "Device not found for MAC: " + macAddress);
        }

        // TODO: 实现位置获取逻辑（可以调用第三方IP定位服务）
        // 目前返回默认值
        return "Mumbai";  // 默认印度孟买
    }

    @Override
    public String getWeatherForecast(String location) {
        // TODO: 集成天气API (如OpenWeatherMap, WeatherAPI.com等)
        // 目前返回模拟数据
        if (StringUtils.isBlank(location)) {
            return "Weather information not available";
        }

        // 返回模拟的7天天气预报
        return String.format(
            "7-Day Weather Forecast for %s:\n" +
            "Today: Sunny, 28°C\n" +
            "Tomorrow: Partly Cloudy, 27°C\n" +
            "Day 3: Light Rain, 25°C\n" +
            "Day 4: Cloudy, 26°C\n" +
            "Day 5: Sunny, 29°C\n" +
            "Day 6: Partly Cloudy, 28°C\n" +
            "Day 7: Sunny, 30°C",
            location
        );
    }
}
