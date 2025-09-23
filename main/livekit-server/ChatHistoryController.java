package com.xiaozhi.manager.controller.config;

import com.xiaozhi.manager.common.result.Result;
import com.xiaozhi.manager.entity.ai.AiAgentChatHistory;
import com.xiaozhi.manager.service.ai.AiAgentChatHistoryService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.time.Instant;
import java.time.ZoneId;

/**
 * Chat History Controller for LiveKit Server
 * Handles chat history reporting from livekit-server
 */
@RestController
@RequestMapping("/agent/chat-history")
@Tag(name = "Chat History", description = "Chat history management for LiveKit agents")
@Slf4j
public class ChatHistoryController {

    @Autowired
    private AiAgentChatHistoryService chatHistoryService;

    @PostMapping("/report")
    @Operation(summary = "Report chat history", description = "Save chat history from LiveKit agent")
    public Result<String> reportChatHistory(@RequestBody ChatHistoryRequest request) {
        log.info("📝 Received chat history report: macAddress={}, sessionId={}, chatType={}, content={}",
                request.getMacAddress(), request.getSessionId(), request.getChatType(),
                request.getContent() != null ? request.getContent().substring(0, Math.min(50, request.getContent().length())) + "..." : "null");

        try {
            // Create chat history entity
            AiAgentChatHistory chatHistory = new AiAgentChatHistory();
            chatHistory.setMacAddress(request.getMacAddress());
            chatHistory.setSessionId(request.getSessionId());
            chatHistory.setChatType(request.getChatType());
            chatHistory.setContent(request.getContent());

            // Convert Unix timestamp to LocalDateTime
            if (request.getReportTime() != null) {
                LocalDateTime dateTime = LocalDateTime.ofInstant(
                    Instant.ofEpochSecond(request.getReportTime()),
                    ZoneId.systemDefault()
                );
                chatHistory.setCreatedAt(dateTime);
                chatHistory.setUpdatedAt(dateTime);
            } else {
                LocalDateTime now = LocalDateTime.now();
                chatHistory.setCreatedAt(now);
                chatHistory.setUpdatedAt(now);
            }

            // Save to database
            chatHistoryService.save(chatHistory);

            log.info("✅ Chat history saved successfully for device: {}", request.getMacAddress());
            return Result.ok("Chat history saved successfully");

        } catch (Exception e) {
            log.error("❌ Failed to save chat history: {}", e.getMessage(), e);
            return Result.error("Failed to save chat history: " + e.getMessage());
        }
    }

    /**
     * Request DTO for chat history reporting
     */
    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class ChatHistoryRequest {
        private String macAddress;
        private String sessionId;
        private Integer chatType;  // 1=user, 2=agent
        private String content;
        private Long reportTime;   // Unix timestamp
        private String audioBase64; // Optional, for future audio support
    }
}