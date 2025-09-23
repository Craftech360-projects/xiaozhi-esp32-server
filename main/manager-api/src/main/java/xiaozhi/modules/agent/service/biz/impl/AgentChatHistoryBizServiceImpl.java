package xiaozhi.modules.agent.service.biz.impl;

import java.util.Base64;
import java.util.Date;
import java.util.Objects;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import xiaozhi.common.constant.Constant;
import xiaozhi.common.redis.RedisKeys;
import xiaozhi.common.redis.RedisUtils;
import xiaozhi.modules.agent.dto.AgentChatHistoryReportDTO;
import xiaozhi.modules.agent.entity.AgentChatHistoryEntity;
import xiaozhi.modules.agent.entity.AgentEntity;
import xiaozhi.modules.agent.service.AgentChatAudioService;
import xiaozhi.modules.agent.service.AgentChatHistoryService;
import xiaozhi.modules.agent.service.AgentService;
import xiaozhi.modules.agent.service.biz.AgentChatHistoryBizService;
import xiaozhi.modules.device.entity.DeviceEntity;
import xiaozhi.modules.device.service.DeviceService;

/**
 * {@link AgentChatHistoryBizService} impl
 *
 * @author Goody
 * @version 1.0, 2025/4/30
 * @since 1.0.0
 */
@Service
@Slf4j
@RequiredArgsConstructor
public class AgentChatHistoryBizServiceImpl implements AgentChatHistoryBizService {
    private final AgentService agentService;
    private final AgentChatHistoryService agentChatHistoryService;
    private final AgentChatAudioService agentChatAudioService;
    private final RedisUtils redisUtils;
    private final DeviceService deviceService;

    /**
     * 处理聊天记录上报，包括文件上传和相关信息记录
     *
     * @param report 包含聊天上报所需信息的输入对象
     * @return 上传结果，true表示成功，false表示失败
     */
    @Override
    @Transactional(rollbackFor = Exception.class)
    public Boolean report(AgentChatHistoryReportDTO report) {
        String macAddress = report.getMacAddress();
        Byte chatType = report.getChatType();
        Long reportTimeMillis = null != report.getReportTime() ? report.getReportTime() * 1000 : System.currentTimeMillis();

        log.info("🔥 [CHAT_BIZ_SERVICE] === BUSINESS LOGIC START ===");
        log.info("🔥 [CHAT_BIZ_SERVICE] Processing chat report: macAddress={}, type={}, reportTime={}",
                macAddress, chatType, reportTimeMillis);
        log.info("🔥 [CHAT_BIZ_SERVICE] Content: {}", report.getContent());

        // 根据设备MAC地址查询对应的默认智能体，判断是否需要上报
        log.info("🔥 [CHAT_BIZ_SERVICE] Looking up default agent for MAC address: {}", macAddress);
        AgentEntity agentEntity = agentService.getDefaultAgentByMacAddress(macAddress);
        if (agentEntity == null) {
            log.warn("🔥 [CHAT_BIZ_SERVICE] ❌ No default agent found for MAC address: {} - returning FALSE", macAddress);
            log.info("🔥 [CHAT_BIZ_SERVICE] === BUSINESS LOGIC END (NO AGENT) ===");
            return Boolean.FALSE;
        }

        log.info("🔥 [CHAT_BIZ_SERVICE] ✅ Found agent: id={}, chatHistoryConf={}",
                agentEntity.getId(), agentEntity.getChatHistoryConf());

        Integer chatHistoryConf = agentEntity.getChatHistoryConf();
        String agentId = agentEntity.getId();

        log.info("🔥 [CHAT_BIZ_SERVICE] Chat history configuration: {}", chatHistoryConf);
        log.info("🔥 [CHAT_BIZ_SERVICE] RECORD_TEXT code: {}", Constant.ChatHistoryConfEnum.RECORD_TEXT.getCode());
        log.info("🔥 [CHAT_BIZ_SERVICE] RECORD_TEXT_AUDIO code: {}", Constant.ChatHistoryConfEnum.RECORD_TEXT_AUDIO.getCode());

        if (Objects.equals(chatHistoryConf, Constant.ChatHistoryConfEnum.RECORD_TEXT.getCode())) {
            log.info("🔥 [CHAT_BIZ_SERVICE] 📝 Saving TEXT ONLY chat history...");
            saveChatText(report, agentId, macAddress, null, reportTimeMillis);
        } else if (Objects.equals(chatHistoryConf, Constant.ChatHistoryConfEnum.RECORD_TEXT_AUDIO.getCode())) {
            log.info("🔥 [CHAT_BIZ_SERVICE] 🎵 Saving TEXT + AUDIO chat history...");
            String audioId = saveChatAudio(report);
            saveChatText(report, agentId, macAddress, audioId, reportTimeMillis);
        } else {
            log.warn("🔥 [CHAT_BIZ_SERVICE] ⚠️ Chat history disabled or unknown config: {} - skipping save", chatHistoryConf);
        }

        // 更新设备最后对话时间
        log.info("🔥 [CHAT_BIZ_SERVICE] Updating Redis last connected time for agent: {}", agentId);
        redisUtils.set(RedisKeys.getAgentDeviceLastConnectedAtById(agentId), new Date());

        // 更新设备最后连接时间
        log.info("🔥 [CHAT_BIZ_SERVICE] Looking up device by MAC address: {}", macAddress);
        DeviceEntity device = deviceService.getDeviceByMacAddress(macAddress);
        if (device != null) {
            log.info("🔥 [CHAT_BIZ_SERVICE] ✅ Found device: id={}, updating connection info", device.getId());
            deviceService.updateDeviceConnectionInfo(agentId, device.getId(), null);
        } else {
            log.warn("🔥 [CHAT_BIZ_SERVICE] ⚠️ Device not found for MAC address: {} - skipping device update", macAddress);
        }

        log.info("🔥 [CHAT_BIZ_SERVICE] ✅ Chat history processing completed successfully");
        log.info("🔥 [CHAT_BIZ_SERVICE] === BUSINESS LOGIC END (SUCCESS) ===");
        return Boolean.TRUE;
    }

    /**
     * base64解码report.getOpusDataBase64(),存入ai_agent_chat_audio表
     */
    private String saveChatAudio(AgentChatHistoryReportDTO report) {
        String audioId = null;

        if (report.getAudioBase64() != null && !report.getAudioBase64().isEmpty()) {
            try {
                byte[] audioData = Base64.getDecoder().decode(report.getAudioBase64());
                audioId = agentChatAudioService.saveAudio(audioData);
                log.info("音频数据保存成功，audioId={}", audioId);
            } catch (Exception e) {
                log.error("音频数据保存失败", e);
                return null;
            }
        }
        return audioId;
    }

    /**
     * 组装上报数据
     */
    private void saveChatText(AgentChatHistoryReportDTO report, String agentId, String macAddress, String audioId, Long reportTime) {
        log.info("🔥 [SAVE_CHAT_TEXT] === SAVE TO DATABASE START ===");
        log.info("🔥 [SAVE_CHAT_TEXT] Building chat history entity...");
        log.info("🔥 [SAVE_CHAT_TEXT] - agentId: {}", agentId);
        log.info("🔥 [SAVE_CHAT_TEXT] - macAddress: {}", macAddress);
        log.info("🔥 [SAVE_CHAT_TEXT] - sessionId: {}", report.getSessionId());
        log.info("🔥 [SAVE_CHAT_TEXT] - chatType: {}", report.getChatType());
        log.info("🔥 [SAVE_CHAT_TEXT] - audioId: {}", audioId);
        log.info("🔥 [SAVE_CHAT_TEXT] - reportTime: {}", new Date(reportTime));

        // 构建聊天记录实体
        AgentChatHistoryEntity entity = AgentChatHistoryEntity.builder()
                .macAddress(macAddress)
                .agentId(agentId)
                .sessionId(report.getSessionId())
                .chatType(report.getChatType())
                .content(report.getContent())
                .audioId(audioId)
                .createdAt(new Date(reportTime))
                // NOTE(haotian): 2025/5/26 updateAt可以不设置，重点是createAt，而且这样可以看到上报延迟
                .build();

        log.info("🔥 [SAVE_CHAT_TEXT] Calling agentChatHistoryService.save()...");
        try {
            // 保存数据
            agentChatHistoryService.save(entity);
            log.info("🔥 [SAVE_CHAT_TEXT] ✅ Database save successful!");
            log.info("🔥 [SAVE_CHAT_TEXT] === SAVE TO DATABASE END (SUCCESS) ===");
            log.info("设备 {} 对应智能体 {} 上报成功", macAddress, agentId);
        } catch (Exception e) {
            log.error("🔥 [SAVE_CHAT_TEXT] ❌ Database save failed!", e);
            log.error("🔥 [SAVE_CHAT_TEXT] === SAVE TO DATABASE END (ERROR) ===");
            throw e;
        }
    }
}
