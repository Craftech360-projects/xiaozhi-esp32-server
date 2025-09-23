package xiaozhi.modules.config.service.impl;

import lombok.AllArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import xiaozhi.modules.agent.entity.AgentChatHistoryEntity;
import xiaozhi.modules.agent.service.AgentChatHistoryService;
import xiaozhi.modules.config.dto.LiveKitChatDataDTO;
import xiaozhi.modules.config.service.LiveKitChatService;
import xiaozhi.modules.sys.service.SysParamsService;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;

import java.util.*;
import java.util.stream.Collectors;

/**
 * LiveKit Chat Service Implementation
 * Handles fetching chat data from LiveKit server and storing to MySQL
 *
 * @author Claude Code
 * @version 1.0
 * @since 1.0.0
 */
@Slf4j
@Service
@AllArgsConstructor
public class LiveKitChatServiceImpl implements LiveKitChatService {

    private final RestTemplate restTemplate;
    private final AgentChatHistoryService agentChatHistoryService;
    private final SysParamsService sysParamsService;

    @Override
    public List<LiveKitChatDataDTO> fetchChatDataFromLiveKit(String agentId, String sessionId) {
        try {
            // Get LiveKit server URL from system parameters
            String liveKitServerUrl = getLiveKitServerUrl();
            if (liveKitServerUrl == null) {
                log.error("LiveKit server URL not configured in system parameters");
                return Collections.emptyList();
            }

            // Build the API endpoint URL
            String apiUrl = liveKitServerUrl + "/api/chat-data";

            // Add query parameters
            Map<String, String> params = new HashMap<>();
            params.put("agent_id", agentId);
            if (sessionId != null && !sessionId.isEmpty()) {
                params.put("session_id", sessionId);
            }

            // Build URL with parameters
            StringBuilder urlBuilder = new StringBuilder(apiUrl);
            if (!params.isEmpty()) {
                urlBuilder.append("?");
                String queryString = params.entrySet().stream()
                        .map(entry -> entry.getKey() + "=" + entry.getValue())
                        .collect(Collectors.joining("&"));
                urlBuilder.append(queryString);
            }

            // Set up headers
            HttpHeaders headers = new HttpHeaders();
            headers.set("Content-Type", "application/json");

            // Add authentication if configured
            String apiKey = getLiveKitApiKey();
            if (apiKey != null) {
                headers.set("Authorization", "Bearer " + apiKey);
            }

            HttpEntity<String> entity = new HttpEntity<>(headers);

            // Make the HTTP request
            log.info("Fetching chat data from LiveKit: {}", urlBuilder.toString());
            ResponseEntity<List<LiveKitChatDataDTO>> response = restTemplate.exchange(
                    urlBuilder.toString(),
                    HttpMethod.GET,
                    entity,
                    new ParameterizedTypeReference<List<LiveKitChatDataDTO>>() {}
            );

            if (response.getStatusCode().is2xxSuccessful() && response.getBody() != null) {
                log.info("Successfully fetched {} chat records from LiveKit for agent {}",
                         response.getBody().size(), agentId);
                return response.getBody();
            } else {
                log.warn("Failed to fetch chat data from LiveKit. Status: {}", response.getStatusCode());
                return Collections.emptyList();
            }

        } catch (Exception e) {
            log.error("Error fetching chat data from LiveKit for agent {}: {}", agentId, e.getMessage(), e);
            return Collections.emptyList();
        }
    }

    @Override
    public boolean storeChatDataToMySQL(List<LiveKitChatDataDTO> chatDataList, String agentId) {
        if (chatDataList == null || chatDataList.isEmpty()) {
            log.info("No chat data to store for agent {}", agentId);
            return true;
        }

        try {
            List<AgentChatHistoryEntity> entitiesToSave = new ArrayList<>();

            for (LiveKitChatDataDTO chatData : chatDataList) {
                // Convert LiveKit chat data to AgentChatHistoryEntity
                AgentChatHistoryEntity entity = convertToAgentChatHistoryEntity(chatData, agentId);
                if (entity != null) {
                    entitiesToSave.add(entity);
                }
            }

            if (!entitiesToSave.isEmpty()) {
                // Log entities before saving for debugging
                log.info("Attempting to save {} entities to database for agent {}", entitiesToSave.size(), agentId);
                for (AgentChatHistoryEntity entity : entitiesToSave) {
                    log.debug("Entity to save: agentId={}, sessionId={}, macAddress={}, chatType={}, content={}",
                             entity.getAgentId(), entity.getSessionId(), entity.getMacAddress(),
                             entity.getChatType(), entity.getContent());
                }

                // Save all entities in batch
                boolean success = agentChatHistoryService.saveBatch(entitiesToSave);
                if (success) {
                    log.info("Successfully stored {} chat records to MySQL for agent {}",
                             entitiesToSave.size(), agentId);
                } else {
                    log.error("Failed to save chat records to MySQL for agent {}", agentId);
                }
                return success;
            } else {
                log.info("No valid chat data to store after conversion for agent {}", agentId);
                return true;
            }

        } catch (Exception e) {
            log.error("Error storing chat data to MySQL for agent {}: {}", agentId, e.getMessage(), e);
            return false;
        }
    }

    @Override
    public boolean syncChatDataFromLiveKit(String agentId, String sessionId) {
        log.info("Starting chat data sync from LiveKit for agent: {}, session: {}", agentId, sessionId);

        try {
            // Step 1: Fetch chat data from LiveKit
            List<LiveKitChatDataDTO> chatDataList = fetchChatDataFromLiveKit(agentId, sessionId);

            // Step 2: Store to MySQL
            boolean success = storeChatDataToMySQL(chatDataList, agentId);

            if (success) {
                log.info("Successfully synced chat data from LiveKit for agent: {}", agentId);
            } else {
                log.error("Failed to sync chat data from LiveKit for agent: {}", agentId);
            }

            return success;

        } catch (Exception e) {
            log.error("Error during chat data sync for agent {}: {}", agentId, e.getMessage(), e);
            return false;
        }
    }

    /**
     * Convert LiveKit chat data to AgentChatHistoryEntity
     */
    private AgentChatHistoryEntity convertToAgentChatHistoryEntity(LiveKitChatDataDTO chatData, String agentId) {
        try {
            log.debug("Converting LiveKit chat data: type={}, sessionId={}, macAddress={}, agentId={}",
                     chatData.getType(), chatData.getSessionId(), chatData.getMacAddress(), agentId);

            // Determine chat type based on LiveKit message type
            Byte chatType = determineChatType(chatData.getType());
            if (chatType == null) {
                log.warn("Skipping unsupported message type: {}", chatData.getType());
                return null;
            }

            // Build the entity
            AgentChatHistoryEntity entity = AgentChatHistoryEntity.builder()
                    .agentId(agentId)
                    .sessionId(chatData.getSessionId())
                    .chatType(chatType)
                    .content(chatData.getContent())
                    .macAddress(chatData.getMacAddress())
                    .audioId(chatData.getSpeechId()) // Use speech_id as audio reference
                    .createdAt(chatData.getTimestamp() != null ?
                               new Date(chatData.getTimestamp()) : new Date())
                    .updatedAt(new Date())
                    .build();

            return entity;

        } catch (Exception e) {
            log.error("Error converting LiveKit chat data to entity: {}", e.getMessage(), e);
            return null;
        }
    }

    /**
     * Determine chat type from LiveKit message type
     */
    private Byte determineChatType(String liveKitType) {
        if (liveKitType == null) {
            return null;
        }

        switch (liveKitType.toLowerCase()) {
            case "user_input_transcribed":
                return (byte) 1; // User message
            case "speech_created":
            case "agent_state_changed":
                return (byte) 2; // Agent message
            default:
                return null; // Skip unsupported types
        }
    }

    /**
     * Get LiveKit server URL from system parameters
     */
    private String getLiveKitServerUrl() {
        try {
            String url = sysParamsService.getValue("livekit.server.url", false);
            return url != null ? url : "http://localhost:8000"; // Default fallback
        } catch (Exception e) {
            log.warn("Failed to get LiveKit server URL from system parameters, using default");
            return "http://localhost:8000";
        }
    }

    /**
     * Get LiveKit API key from system parameters
     */
    private String getLiveKitApiKey() {
        try {
            return sysParamsService.getValue("livekit.api.key", false);
        } catch (Exception e) {
            log.debug("No LiveKit API key configured");
            return null;
        }
    }

    @Override
    public Map<String, Object> getChatHistoryFromMySQL(String agentId, String sessionId) {
        try {
            QueryWrapper<AgentChatHistoryEntity> queryWrapper = new QueryWrapper<>();
            queryWrapper.eq("agent_id", agentId);

            if (sessionId != null && !sessionId.isEmpty()) {
                queryWrapper.eq("session_id", sessionId);
            }

            queryWrapper.orderByAsc("created_at");

            List<AgentChatHistoryEntity> chatHistory = agentChatHistoryService.list(queryWrapper);

            Map<String, Object> result = new HashMap<>();
            result.put("agentId", agentId);
            result.put("sessionId", sessionId);
            result.put("totalRecords", chatHistory.size());

            // Group by session for easier frontend consumption
            Map<String, List<AgentChatHistoryEntity>> sessionGroups = chatHistory.stream()
                    .collect(Collectors.groupingBy(
                            entity -> entity.getSessionId() != null ? entity.getSessionId() : "default",
                            LinkedHashMap::new,
                            Collectors.toList()
                    ));

            List<Map<String, Object>> sessions = new ArrayList<>();
            for (Map.Entry<String, List<AgentChatHistoryEntity>> entry : sessionGroups.entrySet()) {
                Map<String, Object> sessionData = new HashMap<>();
                sessionData.put("sessionId", entry.getKey());
                sessionData.put("messageCount", entry.getValue().size());
                sessionData.put("messages", entry.getValue());
                sessions.add(sessionData);
            }

            result.put("sessions", sessions);

            log.info("Retrieved {} chat records for agent {} from MySQL", chatHistory.size(), agentId);
            return result;

        } catch (Exception e) {
            log.error("Error retrieving chat history for agent {}: {}", agentId, e.getMessage(), e);
            Map<String, Object> errorResult = new HashMap<>();
            errorResult.put("error", "Failed to retrieve chat history: " + e.getMessage());
            errorResult.put("agentId", agentId);
            errorResult.put("sessionId", sessionId);
            return errorResult;
        }
    }
}