package com.xiaozhi.manager.service.ai;

import com.xiaozhi.manager.entity.ai.AiAgentChatHistory;
import com.xiaozhi.manager.mapper.ai.AiAgentChatHistoryMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;

/**
 * Service for managing AI Agent Chat History
 */
@Service
@Slf4j
public class AiAgentChatHistoryService {

    @Autowired
    private AiAgentChatHistoryMapper chatHistoryMapper;

    /**
     * Save chat history record
     * @param chatHistory Chat history entity to save
     * @return Saved chat history entity
     */
    @Transactional
    public AiAgentChatHistory save(AiAgentChatHistory chatHistory) {
        try {
            // Set timestamps if not already set
            if (chatHistory.getCreatedAt() == null) {
                chatHistory.setCreatedAt(LocalDateTime.now());
            }
            if (chatHistory.getUpdatedAt() == null) {
                chatHistory.setUpdatedAt(LocalDateTime.now());
            }

            // Set agent_id if not provided (use session_id as fallback)
            if (chatHistory.getAgentId() == null && chatHistory.getSessionId() != null) {
                chatHistory.setAgentId(chatHistory.getSessionId());
            }

            // Insert the record
            chatHistoryMapper.insert(chatHistory);

            log.info("💾 Chat history saved: ID={}, Device={}, Type={}, Content={}",
                    chatHistory.getId(),
                    chatHistory.getMacAddress(),
                    chatHistory.getChatType() == 1 ? "USER" : "AGENT",
                    chatHistory.getContent() != null ?
                        chatHistory.getContent().substring(0, Math.min(50, chatHistory.getContent().length())) + "..." : "null");

            return chatHistory;

        } catch (Exception e) {
            log.error("❌ Failed to save chat history: {}", e.getMessage(), e);
            throw new RuntimeException("Failed to save chat history", e);
        }
    }

    /**
     * Save chat history from LiveKit server
     * @param macAddress Device MAC address
     * @param sessionId Session ID
     * @param agentId Agent ID (optional, uses sessionId if null)
     * @param chatType Chat type (1=user, 2=agent)
     * @param content Chat content
     * @param reportTime Report timestamp
     * @return Saved chat history entity
     */
    @Transactional
    public AiAgentChatHistory saveLiveKitChat(String macAddress, String sessionId, String agentId,
                                              Integer chatType, String content, Long reportTime) {
        AiAgentChatHistory chatHistory = new AiAgentChatHistory();
        chatHistory.setMacAddress(macAddress);
        chatHistory.setSessionId(sessionId);
        chatHistory.setAgentId(agentId != null ? agentId : sessionId);
        chatHistory.setChatType(chatType);
        chatHistory.setContent(content);

        // Convert Unix timestamp to LocalDateTime if provided
        if (reportTime != null) {
            LocalDateTime dateTime = LocalDateTime.ofInstant(
                java.time.Instant.ofEpochSecond(reportTime),
                java.time.ZoneId.systemDefault()
            );
            chatHistory.setCreatedAt(dateTime);
            chatHistory.setUpdatedAt(dateTime);
        }

        return save(chatHistory);
    }
}