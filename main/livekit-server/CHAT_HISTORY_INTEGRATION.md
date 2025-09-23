# Chat History Integration for Manager API

## Overview
This document provides the Java code to add chat history support to your Spring Boot manager-api application.

## Files to Add

### 1. Controller: ChatHistoryController.java
**Location**: `src/main/java/com/xiaozhi/manager/controller/config/ChatHistoryController.java`

```java
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
            AiAgentChatHistory chatHistory = new AiAgentChatHistory();
            chatHistory.setMacAddress(request.getMacAddress());
            chatHistory.setSessionId(request.getSessionId());
            chatHistory.setChatType(request.getChatType());
            chatHistory.setContent(request.getContent());

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

            chatHistoryService.save(chatHistory);

            log.info("✅ Chat history saved successfully for device: {}", request.getMacAddress());
            return Result.ok("Chat history saved successfully");

        } catch (Exception e) {
            log.error("❌ Failed to save chat history: {}", e.getMessage(), e);
            return Result.error("Failed to save chat history: " + e.getMessage());
        }
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class ChatHistoryRequest {
        private String macAddress;
        private String sessionId;
        private Integer chatType;
        private String content;
        private Long reportTime;
        private String audioBase64;
    }
}
```

### 2. Service: AiAgentChatHistoryService.java
**Location**: `src/main/java/com/xiaozhi/manager/service/ai/AiAgentChatHistoryService.java`

```java
package com.xiaozhi.manager.service.ai;

import com.xiaozhi.manager.entity.ai.AiAgentChatHistory;
import com.xiaozhi.manager.mapper.ai.AiAgentChatHistoryMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;

@Service
@Slf4j
public class AiAgentChatHistoryService {

    @Autowired
    private AiAgentChatHistoryMapper chatHistoryMapper;

    @Transactional
    public AiAgentChatHistory save(AiAgentChatHistory chatHistory) {
        try {
            if (chatHistory.getCreatedAt() == null) {
                chatHistory.setCreatedAt(LocalDateTime.now());
            }
            if (chatHistory.getUpdatedAt() == null) {
                chatHistory.setUpdatedAt(LocalDateTime.now());
            }

            if (chatHistory.getAgentId() == null && chatHistory.getSessionId() != null) {
                chatHistory.setAgentId(chatHistory.getSessionId());
            }

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
}
```

## Integration Steps

1. **Add the files** to your manager-api Spring Boot project in the specified locations
2. **Restart your manager-api server** (port 8002)
3. **Test the endpoint** - Your livekit-server will automatically start using it

## Expected Behavior

After integration, you should see in the livekit-server logs:
```
✅ Chat history sent successfully: {...}
```

Instead of:
```
❌ Chat history reporting failed: Client error '404'
```

## Database

The endpoint uses the existing `ai_agent_chat_history` table:
- ✅ Table structure verified
- ✅ Test insert successful (ID: 49)
- ✅ Authentication compatible

## Current Status

- ✅ LiveKit-server configuration updated
- ✅ MAC address detection fixed (`68:25:dd:bc:03:7c`)
- ✅ Database connectivity verified
- ✅ Authentication using Bearer token
- ⏳ **Next**: Add endpoint to manager-api and restart server

The chat history feature is **ready to go** once the endpoint is added!