package xiaozhi.modules.agent.service.impl;

import java.util.ArrayList;
import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import java.util.function.Function;
import java.util.stream.Collectors;

import org.apache.commons.lang3.StringUtils;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.core.conditions.update.UpdateWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;

import lombok.AllArgsConstructor;
import xiaozhi.common.constant.Constant;
import xiaozhi.common.exception.RenException;
import xiaozhi.common.page.PageData;
import xiaozhi.common.redis.RedisKeys;
import xiaozhi.common.redis.RedisUtils;
import xiaozhi.common.service.impl.BaseServiceImpl;
import xiaozhi.common.user.UserDetail;
import xiaozhi.common.utils.ConvertUtils;
import xiaozhi.common.utils.JsonUtils;
import xiaozhi.modules.agent.dao.AgentDao;
import xiaozhi.modules.agent.dto.AgentCreateDTO;
import xiaozhi.modules.agent.dto.AgentDTO;
import xiaozhi.modules.agent.dto.AgentModeCycleResponse;
import xiaozhi.modules.agent.dto.AgentUpdateDTO;
import xiaozhi.modules.agent.entity.AgentEntity;
import xiaozhi.modules.agent.entity.AgentPluginMapping;
import xiaozhi.modules.agent.entity.AgentTemplateEntity;
import xiaozhi.modules.agent.service.AgentChatHistoryService;
import xiaozhi.modules.agent.service.AgentPluginMappingService;
import xiaozhi.modules.agent.service.AgentService;
import xiaozhi.modules.agent.service.AgentTemplateService;
import xiaozhi.modules.agent.vo.AgentInfoVO;
import xiaozhi.modules.device.entity.DeviceEntity;
import xiaozhi.modules.device.service.DeviceService;
import xiaozhi.modules.model.dto.ModelProviderDTO;
import xiaozhi.modules.model.entity.ModelConfigEntity;
import xiaozhi.modules.model.service.ModelConfigService;
import xiaozhi.modules.model.service.ModelProviderService;
import xiaozhi.modules.security.user.SecurityUser;
import xiaozhi.modules.sys.enums.SuperAdminEnum;
import xiaozhi.modules.timbre.service.TimbreService;

@Service
@AllArgsConstructor
public class AgentServiceImpl extends BaseServiceImpl<AgentDao, AgentEntity> implements AgentService {
    private final AgentDao agentDao;
    private final TimbreService timbreModelService;
    private final ModelConfigService modelConfigService;
    private final RedisUtils redisUtils;
    private final DeviceService deviceService;
    private final AgentPluginMappingService agentPluginMappingService;
    private final AgentChatHistoryService agentChatHistoryService;
    private final AgentTemplateService agentTemplateService;
    private final ModelProviderService modelProviderService;

    @Override
    public PageData<AgentEntity> adminAgentList(Map<String, Object> params) {
        IPage<AgentEntity> page = agentDao.selectPage(
                getPage(params, "agent_name", true),
                new QueryWrapper<>());
        return new PageData<>(page.getRecords(), page.getTotal());
    }

    @Override
    public AgentInfoVO getAgentById(String id) {
        AgentInfoVO agent = agentDao.selectAgentInfoById(id);

        if (agent == null) {
            throw new RenException("智能体不存在");
        }

        if (agent.getMemModelId() != null && agent.getMemModelId().equals(Constant.MEMORY_NO_MEM)) {
            agent.setChatHistoryConf(Constant.ChatHistoryConfEnum.IGNORE.getCode());
        } else {
            // If memory is enabled and chatHistoryConf is null, default to RECORD_TEXT (1)
            if (agent.getChatHistoryConf() == null) {
                agent.setChatHistoryConf(Constant.ChatHistoryConfEnum.RECORD_TEXT.getCode());
            }
        }
        // 无需额外查询插件列表，已通过SQL查询出来
        return agent;
    }

    @Override
    public boolean insert(AgentEntity entity) {
        // 如果ID为空，自动生成一个UUID作为ID
        if (entity.getId() == null || entity.getId().trim().isEmpty()) {
            entity.setId(UUID.randomUUID().toString().replace("-", ""));
        }

        // 如果智能体编码为空，自动生成一个带前缀的编码
        if (entity.getAgentCode() == null || entity.getAgentCode().trim().isEmpty()) {
            entity.setAgentCode("AGT_" + UUID.randomUUID().toString().replace("-", "").substring(0, 8));
        }

        // 如果排序字段为空，设置默认值0
        if (entity.getSort() == null) {
            entity.setSort(0);
        }

        // 如果聊天记录配置为空，设置默认值1（仅记录文本）
        if (entity.getChatHistoryConf() == null) {
            entity.setChatHistoryConf(1);
        }

        // 如果记忆模型为空，设置默认值为本地短期记忆
        if (entity.getMemModelId() == null || entity.getMemModelId().trim().isEmpty()) {
            entity.setMemModelId("Memory_mem_local_short");
        }

        return super.insert(entity);
    }

    @Override
    public void deleteAgentByUserId(Long userId) {
        UpdateWrapper<AgentEntity> wrapper = new UpdateWrapper<>();
        wrapper.eq("user_id", userId);
        baseDao.delete(wrapper);
    }

    @Override
    public List<AgentDTO> getUserAgents(Long userId) {
        QueryWrapper<AgentEntity> wrapper = new QueryWrapper<>();
        wrapper.eq("user_id", userId);
        List<AgentEntity> agents = agentDao.selectList(wrapper);
        return agents.stream().map(agent -> {
            AgentDTO dto = new AgentDTO();
            dto.setId(agent.getId());
            dto.setAgentName(agent.getAgentName());
            dto.setSystemPrompt(agent.getSystemPrompt());

            // 获取 TTS 模型名称
            dto.setTtsModelName(modelConfigService.getModelNameById(agent.getTtsModelId()));

            // 获取 LLM 模型名称
            dto.setLlmModelName(modelConfigService.getModelNameById(agent.getLlmModelId()));

            // 获取 VLLM 模型名称
            dto.setVllmModelName(modelConfigService.getModelNameById(agent.getVllmModelId()));

            // 获取记忆模型名称
            dto.setMemModelId(agent.getMemModelId());

            // 获取 TTS 音色名称
            dto.setTtsVoiceName(timbreModelService.getTimbreNameById(agent.getTtsVoiceId()));

            // 获取智能体最近的最后连接时长
            dto.setLastConnectedAt(deviceService.getLatestLastConnectionTime(agent.getId()));

            // 获取设备数量
            dto.setDeviceCount(getDeviceCountByAgentId(agent.getId()));
            return dto;
        }).collect(Collectors.toList());
    }

    @Override
    public List<AgentDTO> getAllAgentsForAdmin() {
        List<Map<String, Object>> agentMaps = agentDao.getAllAgentsWithOwnerInfo();
        return agentMaps.stream().map(agentMap -> {
            AgentDTO dto = new AgentDTO();
            
            // 基础智能体信息
            String agentId = (String) agentMap.get("id");
            dto.setId(agentId);
            dto.setAgentName((String) agentMap.get("agent_name"));
            dto.setSystemPrompt((String) agentMap.get("system_prompt"));
            
            // Handle LocalDateTime to Date conversion for createDate
            Object createdAt = agentMap.get("created_at");
            if (createdAt instanceof java.time.LocalDateTime) {
                dto.setCreateDate(java.sql.Timestamp.valueOf((java.time.LocalDateTime) createdAt));
            }

            // 获取模型名称 - 同用户方法
            String ttsModelId = (String) agentMap.get("tts_model_id");
            String llmModelId = (String) agentMap.get("llm_model_id");
            String vllmModelId = (String) agentMap.get("vllm_model_id");
            String memModelId = (String) agentMap.get("mem_model_id");
            String ttsVoiceId = (String) agentMap.get("tts_voice_id");

            dto.setTtsModelName(modelConfigService.getModelNameById(ttsModelId));
            dto.setLlmModelName(modelConfigService.getModelNameById(llmModelId));
            dto.setVllmModelName(modelConfigService.getModelNameById(vllmModelId));
            dto.setMemModelId(memModelId);
            dto.setTtsVoiceName(timbreModelService.getTimbreNameById(ttsVoiceId));

            // 获取智能体最近的最后连接时长 - 同用户方法
            dto.setLastConnectedAt(deviceService.getLatestLastConnectionTime(agentId));
            
            // 获取设备MAC地址列表 - 管理员专用
            String macAddresses = (String) agentMap.get("device_mac_addresses");
            dto.setDeviceMacAddresses(macAddresses);
            
            // 计算设备数量（从MAC地址列表或使用原方法）
            if (macAddresses != null && !macAddresses.isEmpty()) {
                dto.setDeviceCount(macAddresses.split(",").length);
            } else {
                // 使用原来的方法获取设备数量
                dto.setDeviceCount(getDeviceCountByAgentId(agentId));
            }

            // 管理员专用字段 - 用户信息
            dto.setOwnerUsername((String) agentMap.get("owner_username"));
            
            return dto;
        }).collect(Collectors.toList());
    }

    @Override
    public Integer getDeviceCountByAgentId(String agentId) {
        if (StringUtils.isBlank(agentId)) {
            return 0;
        }

        // 先从Redis中获取
        Integer cachedCount = (Integer) redisUtils.get(RedisKeys.getAgentDeviceCountById(agentId));
        if (cachedCount != null) {
            return cachedCount;
        }

        // 如果Redis中没有，则从数据库查询
        Integer deviceCount = agentDao.getDeviceCountByAgentId(agentId);

        // 将结果存入Redis
        if (deviceCount != null) {
            redisUtils.set(RedisKeys.getAgentDeviceCountById(agentId), deviceCount, 60);
        }

        return deviceCount != null ? deviceCount : 0;
    }

    @Override
    public AgentEntity getDefaultAgentByMacAddress(String macAddress) {
        if (StringUtils.isEmpty(macAddress)) {
            return null;
        }
        return agentDao.getDefaultAgentByMacAddress(macAddress);
    }

    @Override
    public boolean checkAgentPermission(String agentId, Long userId) {
        // 获取智能体信息
        AgentEntity agent = getAgentById(agentId);
        if (agent == null) {
            return false;
        }

        // 如果是超级管理员，直接返回true
        if (SecurityUser.getUser().getSuperAdmin() == SuperAdminEnum.YES.value()) {
            return true;
        }

        // 检查是否是智能体的所有者
        return userId.equals(agent.getUserId());
    }

    // 根据id更新智能体信息
    @Override
    @Transactional(rollbackFor = Exception.class)
    public void updateAgentById(String agentId, AgentUpdateDTO dto) {
        // 先查询现有实体
        AgentEntity existingEntity = this.getAgentById(agentId);
        if (existingEntity == null) {
            throw new RuntimeException("智能体不存在");
        }

        // 只更新提供的非空字段
        if (dto.getAgentName() != null) {
            existingEntity.setAgentName(dto.getAgentName());
        }
        if (dto.getAgentCode() != null) {
            existingEntity.setAgentCode(dto.getAgentCode());
        }
        if (dto.getAsrModelId() != null) {
            existingEntity.setAsrModelId(dto.getAsrModelId());
        }
        if (dto.getVadModelId() != null) {
            existingEntity.setVadModelId(dto.getVadModelId());
        }
        if (dto.getLlmModelId() != null) {
            existingEntity.setLlmModelId(dto.getLlmModelId());
        }
        if (dto.getVllmModelId() != null) {
            existingEntity.setVllmModelId(dto.getVllmModelId());
        }
        if (dto.getTtsModelId() != null) {
            existingEntity.setTtsModelId(dto.getTtsModelId());
        }
        if (dto.getTtsVoiceId() != null) {
            existingEntity.setTtsVoiceId(dto.getTtsVoiceId());
        }
        if (dto.getMemModelId() != null) {
            existingEntity.setMemModelId(dto.getMemModelId());
        }
        if (dto.getIntentModelId() != null) {
            existingEntity.setIntentModelId(dto.getIntentModelId());
        }
        if (dto.getSystemPrompt() != null) {
            existingEntity.setSystemPrompt(dto.getSystemPrompt());
        }
        if (dto.getSummaryMemory() != null) {
            existingEntity.setSummaryMemory(dto.getSummaryMemory());
        }
        if (dto.getChatHistoryConf() != null) {
            existingEntity.setChatHistoryConf(dto.getChatHistoryConf());
        }
        if (dto.getLangCode() != null) {
            existingEntity.setLangCode(dto.getLangCode());
        }
        if (dto.getLanguage() != null) {
            existingEntity.setLanguage(dto.getLanguage());
        }
        if (dto.getSort() != null) {
            existingEntity.setSort(dto.getSort());
        }

        // 更新函数插件信息
        List<AgentUpdateDTO.FunctionInfo> functions = dto.getFunctions();
        if (functions != null) {
            // 1. 收集本次提交的 pluginId
            List<String> newPluginIds = functions.stream()
                    .map(AgentUpdateDTO.FunctionInfo::getPluginId)
                    .toList();

            // 2. 查询当前agent现有的所有映射
            List<AgentPluginMapping> existing = agentPluginMappingService.list(
                    new QueryWrapper<AgentPluginMapping>()
                            .eq("agent_id", agentId));
            Map<String, AgentPluginMapping> existMap = existing.stream()
                    .collect(Collectors.toMap(AgentPluginMapping::getPluginId, Function.identity()));

            // 3. 构造所有要 保存或更新 的实体
            List<AgentPluginMapping> allToPersist = functions.stream().map(info -> {
                AgentPluginMapping m = new AgentPluginMapping();
                m.setAgentId(agentId);
                m.setPluginId(info.getPluginId());
                m.setParamInfo(info.getParamInfo());
                AgentPluginMapping old = existMap.get(info.getPluginId());
                if (old != null) {
                    // 已存在，设置id表示更新
                    m.setId(old.getId());
                }
                return m;
            }).toList();

            // 4. 拆分：已有ID的走更新，无ID的走插入
            List<AgentPluginMapping> toUpdate = allToPersist.stream()
                    .filter(m -> m.getId() != null)
                    .toList();
            List<AgentPluginMapping> toInsert = allToPersist.stream()
                    .filter(m -> m.getId() == null)
                    .toList();

            if (!toUpdate.isEmpty()) {
                agentPluginMappingService.updateBatchById(toUpdate);
            }
            if (!toInsert.isEmpty()) {
                agentPluginMappingService.saveBatch(toInsert);
            }

            // 5. 删除本次不在提交列表里的插件映射
            List<Long> toDelete = existing.stream()
                    .filter(old -> !newPluginIds.contains(old.getPluginId()))
                    .map(AgentPluginMapping::getId)
                    .toList();
            if (!toDelete.isEmpty()) {
                agentPluginMappingService.removeBatchByIds(toDelete);
            }
        }

        // 设置更新者信息
        UserDetail user = SecurityUser.getUser();
        existingEntity.setUpdater(user.getId());
        existingEntity.setUpdatedAt(new Date());

        // 更新记忆策略
        if (existingEntity.getMemModelId() == null || existingEntity.getMemModelId().equals(Constant.MEMORY_NO_MEM)) {
            // 删除所有记录
            agentChatHistoryService.deleteByAgentId(existingEntity.getId(), true, true);
            existingEntity.setSummaryMemory("");
        } else if (existingEntity.getChatHistoryConf() != null && existingEntity.getChatHistoryConf() == 1) {
            // 删除音频数据
            agentChatHistoryService.deleteByAgentId(existingEntity.getId(), true, false);
        }

        boolean b = validateLLMIntentParams(dto.getLlmModelId(), dto.getIntentModelId());
        if (!b) {
            throw new RenException("LLM大模型和Intent意图识别，选择参数不匹配");
        }
        this.updateById(existingEntity);
    }

    /**
     * 验证大语言模型和意图识别的参数是否符合匹配
     * 
     * @param llmModelId    大语言模型id
     * @param intentModelId 意图识别id
     * @return T 匹配 : F 不匹配
     */
    private boolean validateLLMIntentParams(String llmModelId, String intentModelId) {
        if (StringUtils.isBlank(llmModelId)) {
            return true;
        }
        ModelConfigEntity llmModelData = modelConfigService.selectById(llmModelId);
        if (llmModelData == null || llmModelData.getConfigJson() == null) {
            return true;
        }
        String type = llmModelData.getConfigJson().get("type").toString();
        // 如果查询大语言模型是openai或者ollama，意图识别选参数都可以
        if ("openai".equals(type) || "ollama".equals(type)) {
            return true;
        }
        // 除了openai和ollama的类型，不可以选择id为Intent_function_call（函数调用）的意图识别
        return !"Intent_function_call".equals(intentModelId);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public String createAgent(AgentCreateDTO dto) {
        // 转换为实体
        AgentEntity entity = ConvertUtils.sourceToTarget(dto, AgentEntity.class);

        // 获取默认模板
        AgentTemplateEntity template = agentTemplateService.getDefaultTemplate();
        if (template != null) {
            // 设置模板中的默认值
            entity.setAsrModelId(template.getAsrModelId());
            entity.setVadModelId(template.getVadModelId());
            entity.setLlmModelId(template.getLlmModelId());
            entity.setVllmModelId(template.getVllmModelId());
            entity.setTtsModelId(template.getTtsModelId());
            entity.setTtsVoiceId(template.getTtsVoiceId());
            entity.setMemModelId(template.getMemModelId());
            entity.setIntentModelId(template.getIntentModelId());
            entity.setSystemPrompt(template.getSystemPrompt());
            entity.setSummaryMemory(template.getSummaryMemory());
            entity.setChatHistoryConf(template.getChatHistoryConf());
            entity.setLangCode(template.getLangCode());
            entity.setLanguage(template.getLanguage());
            
            // Override with Cheeko defaults
            entity.setAgentName("Cheeko");  // Always use Cheeko name
            entity.setMemModelId("Memory_mem_local_short");  // Always use Local Short Term memory
            entity.setChatHistoryConf(1);  // Always enable Report Text
            entity.setTtsModelId("TTS_EdgeTTS");  // Always use EdgeTTS model
            entity.setTtsVoiceId("TTS_EdgeTTS_Ana");  // Always use EdgeTTS Ana voice (en-US-AnaNeural)
            
            // Log the overridden values for debugging
            System.out.println("Creating agent with overridden defaults:");
            System.out.println("  Memory: " + entity.getMemModelId());
            System.out.println("  TTS Model: " + entity.getTtsModelId());
            System.out.println("  TTS Voice: " + entity.getTtsVoiceId());
        }

        // 设置用户ID和创建者信息
        UserDetail user = SecurityUser.getUser();
        entity.setUserId(user.getId());
        entity.setCreator(user.getId());
        entity.setCreatedAt(new Date());

        // 保存智能体
        insert(entity);

        // 先检查是否已存在插件映射
        List<AgentPluginMapping> existingMappings = agentPluginMappingService.list(
                new QueryWrapper<AgentPluginMapping>()
                        .eq("agent_id", entity.getId()));
        
        // 收集已存在的插件ID
        Set<String> existingPluginIds = existingMappings.stream()
                .map(AgentPluginMapping::getPluginId)
                .collect(Collectors.toSet());

        // 设置默认插件
        List<AgentPluginMapping> toInsert = new ArrayList<>();
        // 播放音乐、播放故事、查天气、查新闻
        String[] pluginIds = new String[] { "SYSTEM_PLUGIN_MUSIC", "SYSTEM_PLUGIN_STORY", 
                "SYSTEM_PLUGIN_WEATHER", "SYSTEM_PLUGIN_NEWS_NEWSNOW" };
        
        for (String pluginId : pluginIds) {
            // 跳过已存在的插件映射
            if (existingPluginIds.contains(pluginId)) {
                continue;
            }
            
            ModelProviderDTO provider = modelProviderService.getById(pluginId);
            if (provider == null) {
                continue;
            }
            AgentPluginMapping mapping = new AgentPluginMapping();
            mapping.setPluginId(pluginId);

            Map<String, Object> paramInfo = new HashMap<>();
            List<Map<String, Object>> fields = JsonUtils.parseObject(provider.getFields(), List.class);
            if (fields != null) {
                for (Map<String, Object> field : fields) {
                    paramInfo.put((String) field.get("key"), field.get("default"));
                }
            }
            mapping.setParamInfo(paramInfo);
            mapping.setAgentId(entity.getId());
            toInsert.add(mapping);
        }

        // 只有当有新插件需要插入时才保存
        if (!toInsert.isEmpty()) {
            agentPluginMappingService.saveBatch(toInsert);
        }
        return entity.getId();
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public String updateAgentMode(String agentId, String modeName) {
        // 1. 验证智能体是否存在
        AgentEntity agent = this.selectById(agentId);
        if (agent == null) {
            throw new RenException("智能体不存在");
        }

        // 2. 根据模板名称查询模板
        AgentTemplateEntity template = agentTemplateService.getTemplateByName(modeName);
        if (template == null) {
            throw new RenException("模板 '" + modeName + "' 不存在");
        }

        // Log old prompt
        String oldPrompt = agent.getSystemPrompt();
        String oldPromptPreview = oldPrompt != null && oldPrompt.length() > 100
            ? oldPrompt.substring(0, 100) + "..."
            : oldPrompt;

        // 3. 将模板配置复制到智能体（保留智能体的身份信息和审计信息）
        agent.setAsrModelId(template.getAsrModelId());
        agent.setVadModelId(template.getVadModelId());
        agent.setLlmModelId(template.getLlmModelId());
        agent.setVllmModelId(template.getVllmModelId());
        agent.setTtsModelId(template.getTtsModelId());
        agent.setTtsVoiceId(template.getTtsVoiceId());
        agent.setMemModelId(template.getMemModelId());
        agent.setIntentModelId(template.getIntentModelId());
        agent.setSystemPrompt(template.getSystemPrompt());
        agent.setChatHistoryConf(template.getChatHistoryConf());
        agent.setLangCode(template.getLangCode());
        agent.setLanguage(template.getLanguage());
        agent.setAgentName(template.getAgentName());

        // Log new prompt
        String newPrompt = template.getSystemPrompt();
        String newPromptPreview = newPrompt != null && newPrompt.length() > 100
            ? newPrompt.substring(0, 100) + "..."
            : newPrompt;

        // 4. 更新审计信息
        try {
            UserDetail user = SecurityUser.getUser();
            if (user != null) {
                agent.setUpdater(user.getId());
            }
        } catch (Exception e) {
            // Server secret filter - no user context, skip updater
        }
        agent.setUpdatedAt(new Date());

        // 5. 更新数据库
        this.updateById(agent);

        // Log update details
        System.out.println("🔄 ===== AGENT MODE UPDATE =====");
        System.out.println("Agent ID: " + agentId);
        System.out.println("Agent Name: " + agent.getAgentName());
        System.out.println("Template: " + modeName + " (" + template.getId() + ")");
        System.out.println("Old Prompt Preview: " + oldPromptPreview);
        System.out.println("New Prompt Preview: " + newPromptPreview);
        System.out.println("New LLM Model: " + template.getLlmModelId());
        System.out.println("New TTS Model: " + template.getTtsModelId());
        System.out.println("New Memory Model: " + template.getMemModelId());
        System.out.println("Database Updated: YES ✅");
        System.out.println("================================");

        // 6. Return the updated prompt
        return newPrompt;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public AgentModeCycleResponse cycleAgentModeByMac(String macAddress) {
        // 1. Get device by MAC address
        DeviceEntity device = deviceService.getDeviceByMacAddress(macAddress);
        if (device == null) {
            throw new RenException("Device not found for MAC address: " + macAddress);
        }

        // 2. Get current agent
        AgentEntity agent = this.selectById(device.getAgentId());
        if (agent == null) {
            throw new RenException("No agent associated with device");
        }

        String currentModeName = agent.getAgentName();

        // 3. Get all visible templates ordered by sort
        List<AgentTemplateEntity> allTemplates = agentTemplateService.list(
            new QueryWrapper<AgentTemplateEntity>()
                .eq("is_visible", true)
                .orderByAsc("sort")
        );

        if (allTemplates.isEmpty()) {
            throw new RenException("No templates available");
        }

        if (allTemplates.size() == 1) {
            // Only one mode available, cannot cycle
            AgentModeCycleResponse response = new AgentModeCycleResponse();
            response.setSuccess(false);
            response.setAgentId(agent.getId());
            response.setOldModeName(currentModeName);
            response.setNewModeName(currentModeName);
            response.setModeIndex(0);
            response.setTotalModes(1);
            response.setMessage("Only one mode available, cannot cycle");
            return response;
        }

        // 4. Find current template index by name
        int currentIndex = -1;
        for (int i = 0; i < allTemplates.size(); i++) {
            if (allTemplates.get(i).getAgentName().equalsIgnoreCase(currentModeName)) {
                currentIndex = i;
                break;
            }
        }

        // 5. Calculate next index (cycle to next mode)
        int nextIndex = (currentIndex + 1) % allTemplates.size();
        AgentTemplateEntity nextTemplate = allTemplates.get(nextIndex);

        // 6. Update agent with template configuration
        String oldModeName = agent.getAgentName();

        agent.setAgentName(nextTemplate.getAgentName());
        agent.setAsrModelId(nextTemplate.getAsrModelId());
        agent.setVadModelId(nextTemplate.getVadModelId());
        agent.setLlmModelId(nextTemplate.getLlmModelId());
        agent.setVllmModelId(nextTemplate.getVllmModelId());
        agent.setTtsModelId(nextTemplate.getTtsModelId());
        agent.setTtsVoiceId(nextTemplate.getTtsVoiceId());
        agent.setMemModelId(nextTemplate.getMemModelId());
        agent.setIntentModelId(nextTemplate.getIntentModelId());
        agent.setSystemPrompt(nextTemplate.getSystemPrompt());
        agent.setChatHistoryConf(nextTemplate.getChatHistoryConf());
        agent.setLangCode(nextTemplate.getLangCode());
        agent.setLanguage(nextTemplate.getLanguage());

        // 7. Update audit info
        try {
            UserDetail user = SecurityUser.getUser();
            if (user != null) {
                agent.setUpdater(user.getId());
            }
        } catch (Exception e) {
            // Server secret filter - no user context, skip updater
        }
        agent.setUpdatedAt(new Date());

        // 8. Save to database
        this.updateById(agent);

        // 9. Build response
        AgentModeCycleResponse response = new AgentModeCycleResponse();
        response.setSuccess(true);
        response.setAgentId(agent.getId());
        response.setOldModeName(oldModeName);
        response.setNewModeName(nextTemplate.getAgentName());
        response.setModeIndex(nextIndex);
        response.setTotalModes(allTemplates.size());
        response.setMessage("Mode changed successfully from " + oldModeName + " to " + nextTemplate.getAgentName());
        response.setNewSystemPrompt(nextTemplate.getSystemPrompt());

        // 10. Log the change
        System.out.println("🔘 ===== AGENT MODE CYCLE (BUTTON) =====");
        System.out.println("Device MAC: " + macAddress);
        System.out.println("Agent ID: " + agent.getId());
        System.out.println("Mode Change: " + oldModeName + " → " + nextTemplate.getAgentName());
        System.out.println("Mode Index: " + nextIndex + " / " + allTemplates.size());
        System.out.println("New LLM Model: " + nextTemplate.getLlmModelId());
        System.out.println("New TTS Model: " + nextTemplate.getTtsModelId());
        System.out.println("Database Updated: YES ✅");
        System.out.println("========================================");

        return response;
    }
}
