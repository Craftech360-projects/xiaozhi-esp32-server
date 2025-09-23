package xiaozhi.modules.agent.service.impl;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;

import xiaozhi.common.constant.Constant;
import xiaozhi.common.page.PageData;
import xiaozhi.common.utils.ConvertUtils;
import xiaozhi.common.utils.JsonUtils;
import xiaozhi.modules.agent.Enums.AgentChatHistoryType;
import xiaozhi.modules.agent.dao.AiAgentChatHistoryDao;
import xiaozhi.modules.agent.dto.AgentChatHistoryDTO;
import xiaozhi.modules.agent.dto.AgentChatSessionDTO;
import xiaozhi.modules.agent.entity.AgentChatHistoryEntity;
import xiaozhi.modules.agent.service.AgentChatHistoryService;
import xiaozhi.modules.agent.vo.AgentChatHistoryUserVO;
import lombok.extern.slf4j.Slf4j;

/**
 * 智能体聊天记录表处理service {@link AgentChatHistoryService} impl
 *
 * @author Goody
 * @version 1.0, 2025/4/30
 * @since 1.0.0
 */
@Slf4j
@Service
public class AgentChatHistoryServiceImpl extends ServiceImpl<AiAgentChatHistoryDao, AgentChatHistoryEntity>
        implements AgentChatHistoryService {

    @Override
    public PageData<AgentChatSessionDTO> getSessionListByAgentId(Map<String, Object> params) {
        log.info("=== getSessionListByAgentId START ===");
        log.info("Input params: {}", params);

        String agentId = (String) params.get("agentId");
        String macAddress = (String) params.get("macAddress");
        log.info("Extracted agentId: {}, macAddress: {}", agentId, macAddress);

        // Safe parameter parsing with defaults
        int page = 1;
        int limit = 20;

        try {
            Object pageParam = params.get(Constant.PAGE);
            Object limitParam = params.get(Constant.LIMIT);
            log.info("Raw parameters - page: {}, limit: {}", pageParam, limitParam);

            if (pageParam != null && !pageParam.toString().isEmpty()) {
                page = Integer.parseInt(pageParam.toString());
            }
            if (limitParam != null && !limitParam.toString().isEmpty()) {
                limit = Integer.parseInt(limitParam.toString());
            }

            // Validate bounds
            if (page < 1) page = 1;
            if (limit < 1) limit = 20;
            if (limit > 100) limit = 100; // Prevent excessive queries

            log.info("Final parsed parameters - page: {}, limit: {}", page, limit);

        } catch (NumberFormatException e) {
            log.error("Invalid page/limit parameters: {}", e.getMessage());
            page = 1;
            limit = 20;
        }

        // 构建查询条件
        log.info("Building database query...");
        QueryWrapper<AgentChatHistoryEntity> wrapper = new QueryWrapper<>();
        wrapper.select("session_id", "ANY_VALUE(mac_address) as mac_address", "MAX(created_at) as created_at", "COUNT(*) as chat_count");

        // Support filtering by either agent_id OR mac_address for dynamic sessions
        if (macAddress != null && !macAddress.isEmpty()) {
            log.info("Filtering by MAC address: {}", macAddress);
            wrapper.eq("mac_address", macAddress);
        } else {
            log.info("Filtering by agent_id: {}", agentId);
            wrapper.eq("agent_id", agentId);
        }

        wrapper.groupBy("session_id")
                .orderByDesc("created_at");

        log.info("Query wrapper: {}", wrapper.getSqlSelect());

        try {
            // 执行分页查询
            log.info("Executing database query with page: {}, limit: {}", page, limit);
            Page<Map<String, Object>> pageParam = new Page<>(page, limit);
            IPage<Map<String, Object>> result = this.baseMapper.selectMapsPage(pageParam, wrapper);

            log.info("Database query completed. Total records: {}, Records returned: {}",
                result.getTotal(), result.getRecords().size());

            List<AgentChatSessionDTO> records = result.getRecords().stream().map(map -> {
                log.debug("Processing record: {}", map);
                AgentChatSessionDTO dto = new AgentChatSessionDTO();
                dto.setSessionId((String) map.get("session_id"));
                dto.setMacAddress((String) map.get("mac_address"));
                dto.setCreatedAt((LocalDateTime) map.get("created_at"));
                dto.setChatCount(((Number) map.get("chat_count")).intValue());
                return dto;
            }).collect(Collectors.toList());

            log.info("Successfully processed {} session records", records.size());
            log.info("=== getSessionListByAgentId END ===");
            return new PageData<>(records, result.getTotal());

        } catch (Exception e) {
            log.error("DATABASE ERROR in getSessionListByAgentId: {}", e.getMessage(), e);
            throw e;
        }
    }

    @Override
    public List<AgentChatHistoryDTO> getChatHistoryBySessionId(String agentId, String sessionId) {
        // 构建查询条件
        QueryWrapper<AgentChatHistoryEntity> wrapper = new QueryWrapper<>();

        // For dynamic sessions where agent_id equals session_id, just filter by session_id
        // For traditional sessions, filter by both agent_id and session_id
        if (agentId != null && !agentId.equals(sessionId)) {
            wrapper.eq("agent_id", agentId);
        }

        wrapper.eq("session_id", sessionId)
                .orderByAsc("created_at");

        // 查询聊天记录
        List<AgentChatHistoryEntity> historyList = list(wrapper);

        // 转换为DTO
        return ConvertUtils.sourceToTarget(historyList, AgentChatHistoryDTO.class);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void deleteByAgentId(String agentId, Boolean deleteAudio, Boolean deleteText) {
        if (deleteAudio) {
            baseMapper.deleteAudioByAgentId(agentId);
        }
        if (deleteAudio && !deleteText) {
            baseMapper.deleteAudioIdByAgentId(agentId);
        }
        if (deleteText) {
            baseMapper.deleteHistoryByAgentId(agentId);
        }

    }

    @Override
    public List<AgentChatHistoryUserVO> getRecentlyFiftyByAgentId(String agentId) {
        // 构建查询条件(不添加按照创建时间排序，数据本来就是主键越大创建时间越大
        // 不添加这样可以减少排序全部数据在分页的全盘扫描消耗)
        LambdaQueryWrapper<AgentChatHistoryEntity> wrapper = new LambdaQueryWrapper<>();
        wrapper.select(AgentChatHistoryEntity::getContent, AgentChatHistoryEntity::getAudioId)
                .eq(AgentChatHistoryEntity::getAgentId, agentId)
                .eq(AgentChatHistoryEntity::getChatType, AgentChatHistoryType.USER.getValue())
                .isNotNull(AgentChatHistoryEntity::getAudioId)
                // 添加此行，确保查询结果按照创建时间降序排列
                // 使用id的原因：数据形式，id越大的创建时间就越晚，所以使用id的结果和创建时间降序排列结果一样
                // id作为降序排列的优势，性能高，有主键索引，不用在排序的时候重新进行排除扫描比较
                .orderByDesc(AgentChatHistoryEntity::getId); 

        // 构建分页查询，查询前50页数据
        Page<AgentChatHistoryEntity> pageParam = new Page<>(0, 50);
        IPage<AgentChatHistoryEntity> result = this.baseMapper.selectPage(pageParam, wrapper);
        return result.getRecords().stream().map(item -> {
            AgentChatHistoryUserVO vo = ConvertUtils.sourceToTarget(item, AgentChatHistoryUserVO.class);
            // 处理 content 字段，确保只返回聊天内容
            if (vo != null && vo.getContent() != null) {
                vo.setContent(extractContentFromString(vo.getContent()));
            }
            return vo;
        }).toList();
    }

    /**
     * 从 content 字段中提取聊天内容
     * 如果 content 是 JSON 格式（如 {"speaker": "未知说话人", "content": "现在几点了。"}），则提取 content
     * 字段
     * 如果 content 是普通字符串，则直接返回
     * 
     * @param content 原始内容
     * @return 提取的聊天内容
     */
    private String extractContentFromString(String content) {
        if (content == null || content.trim().isEmpty()) {
            return content;
        }

        // 尝试解析为 JSON
        try {
            Map<String, Object> jsonMap = JsonUtils.parseObject(content, Map.class);
            if (jsonMap != null && jsonMap.containsKey("content")) {
                Object contentObj = jsonMap.get("content");
                return contentObj != null ? contentObj.toString() : content;
            }
        } catch (Exception e) {
            // 如果不是有效的 JSON，直接返回原内容
        }

        // 如果不是 JSON 格式或没有 content 字段，直接返回原内容
        return content;
    }

    @Override
    public String getContentByAudioId(String audioId) {
        AgentChatHistoryEntity agentChatHistoryEntity = baseMapper
                .selectOne(new LambdaQueryWrapper<AgentChatHistoryEntity>()
                        .select(AgentChatHistoryEntity::getContent)
                        .eq(AgentChatHistoryEntity::getAudioId, audioId));
        return agentChatHistoryEntity == null ? null : agentChatHistoryEntity.getContent();
    }

    @Override
    public boolean isAudioOwnedByAgent(String audioId, String agentId) {
        // 查询是否有指定音频id和智能体id的数据，如果有且只有一条说明此数据属性此智能体
        Long row = baseMapper.selectCount(new LambdaQueryWrapper<AgentChatHistoryEntity>()
                .eq(AgentChatHistoryEntity::getAudioId, audioId)
                .eq(AgentChatHistoryEntity::getAgentId, agentId));
        return row == 1;
    }
}
