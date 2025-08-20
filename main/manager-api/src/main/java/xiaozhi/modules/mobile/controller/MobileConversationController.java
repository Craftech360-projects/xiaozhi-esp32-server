package xiaozhi.modules.mobile.controller;

import xiaozhi.common.annotation.LogOperation;
import xiaozhi.common.utils.Result;
import io.swagger.v3.oas.annotations.tags.Tag;
import io.swagger.v3.oas.annotations.Operation;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.web.bind.annotation.*;
import xiaozhi.modules.mobile.service.SupabaseAuthService;

import java.text.SimpleDateFormat;
import java.util.*;

@RestController
@RequestMapping("/api/mobile/conversations")
@Tag(name = "Mobile Conversation History API")
public class MobileConversationController {
    
    private static final Logger logger = LoggerFactory.getLogger(MobileConversationController.class);
    
    @Autowired
    private JdbcTemplate jdbcTemplate;
    
    @Autowired
    private SupabaseAuthService supabaseAuthService;
    
    @GetMapping("/{activationId}")
    @Operation(summary = "Get conversation history")
    @LogOperation("Get conversation history")
    public Result getConversationHistory(
            @PathVariable String activationId,
            @RequestHeader("Authorization") String authHeader,
            @RequestParam(required = false) String date,
            @RequestParam(defaultValue = "20") int limit,
            @RequestParam(defaultValue = "0") int offset,
            @RequestParam(required = false) String category) {
        
        try {
            String token = authHeader.replace("Bearer ", "");
            String supabaseUserId = supabaseAuthService.validateTokenAndGetUserId(token);
            
            logger.info("Getting conversation history for activation: {}", activationId);
            
            String targetDate = date != null ? date : new SimpleDateFormat("yyyy-MM-dd").format(new Date());
            
            // Call stored procedure
            List<Map<String, Object>> conversations = jdbcTemplate.queryForList(
                "CALL GetMobileConversationHistory(?, ?, ?, ?)",
                supabaseUserId, targetDate, targetDate, limit
            );
            
            // Transform conversations to response format
            List<Map<String, Object>> formattedConversations = new ArrayList<>();
            String currentSessionId = null;
            Map<String, Object> currentConversation = null;
            List<Map<String, Object>> currentMessages = null;
            
            for (Map<String, Object> row : conversations) {
                String sessionId = row.get("session_id").toString();
                
                if (!sessionId.equals(currentSessionId)) {
                    // Save previous conversation if exists
                    if (currentConversation != null) {
                        currentConversation.put("messages", currentMessages);
                        currentConversation.put("message_count", currentMessages.size());
                        formattedConversations.add(currentConversation);
                    }
                    
                    // Start new conversation
                    currentSessionId = sessionId;
                    currentConversation = new HashMap<>();
                    currentConversation.put("id", row.get("id"));
                    currentConversation.put("session_id", sessionId);
                    currentConversation.put("timestamp", row.get("created_at"));
                    currentConversation.put("category", row.get("primary_category"));
                    currentConversation.put("sub_category", row.get("sub_category"));
                    currentConversation.put("sentiment_score", row.get("sentiment_score"));
                    currentConversation.put("educational_value", row.get("educational_value"));
                    
                    currentMessages = new ArrayList<>();
                }
                
                // Add message
                Map<String, Object> message = new HashMap<>();
                Integer chatType = (Integer) row.get("chat_type");
                message.put("type", chatType == 1 ? "child" : "ai");
                message.put("content", row.get("content"));
                message.put("timestamp", row.get("created_at"));
                currentMessages.add(message);
            }
            
            // Save last conversation
            if (currentConversation != null) {
                currentConversation.put("messages", currentMessages);
                currentConversation.put("message_count", currentMessages.size());
                formattedConversations.add(currentConversation);
            }
            
            // Build response with pagination
            Map<String, Object> response = new HashMap<>();
            response.put("conversations", formattedConversations);
            
            Map<String, Object> pagination = new HashMap<>();
            pagination.put("total", getTotalConversations(supabaseUserId, targetDate));
            pagination.put("limit", limit);
            pagination.put("offset", offset);
            pagination.put("has_more", formattedConversations.size() == limit);
            response.put("pagination", pagination);
            
            return new Result().ok(response);
            
        } catch (Exception e) {
            logger.error("Error getting conversation history", e);
            return new Result().error("Failed to get conversation history");
        }
    }
    
    @GetMapping("/{activationId}/{conversationId}")
    @Operation(summary = "Get conversation details")
    @LogOperation("Get conversation details")
    public Result getConversationDetails(
            @PathVariable String activationId,
            @PathVariable String conversationId,
            @RequestHeader("Authorization") String authHeader) {
        
        try {
            String token = authHeader.replace("Bearer ", "");
            String supabaseUserId = supabaseAuthService.validateTokenAndGetUserId(token);
            
            logger.info("Getting conversation details for ID: {}", conversationId);
            
            // Get conversation messages
            String sql = "SELECT ch.*, ic.primary_category, ic.sub_category, ic.sentiment_score, " +
                        "ic.educational_value, ic.keywords_extracted, ic.vocabulary_used " +
                        "FROM ai_agent_chat_history ch " +
                        "LEFT JOIN interaction_categories ic ON ch.id = ic.chat_history_id " +
                        "JOIN parent_child_mapping pcm ON ch.mac_address = pcm.device_mac_address " +
                        "WHERE ch.session_id = ? AND pcm.supabase_user_id = ? " +
                        "ORDER BY ch.created_at";
            
            List<Map<String, Object>> messages = jdbcTemplate.queryForList(sql, conversationId, supabaseUserId);
            
            if (messages.isEmpty()) {
                return new Result().error("Conversation not found");
            }
            
            // Build response
            Map<String, Object> response = new HashMap<>();
            response.put("id", conversationId);
            response.put("session_id", conversationId);
            response.put("started_at", messages.get(0).get("created_at"));
            response.put("ended_at", messages.get(messages.size() - 1).get("created_at"));
            response.put("message_count", messages.size());
            
            // Format messages
            List<Map<String, Object>> formattedMessages = new ArrayList<>();
            for (Map<String, Object> msg : messages) {
                Map<String, Object> message = new HashMap<>();
                message.put("id", msg.get("id"));
                Integer chatType = (Integer) msg.get("chat_type");
                message.put("type", chatType == 1 ? "child" : "ai");
                message.put("content", msg.get("content"));
                message.put("timestamp", msg.get("created_at"));
                message.put("audio_available", msg.get("audio_id") != null);
                formattedMessages.add(message);
            }
            response.put("messages", formattedMessages);
            
            // Add analytics if available
            Map<String, Object> analytics = new HashMap<>();
            Map<String, Object> firstMsg = messages.get(0);
            analytics.put("category", firstMsg.get("primary_category"));
            analytics.put("sub_category", firstMsg.get("sub_category"));
            analytics.put("sentiment_score", firstMsg.get("sentiment_score"));
            analytics.put("educational_value", firstMsg.get("educational_value"));
            analytics.put("keywords", firstMsg.get("keywords_extracted"));
            analytics.put("vocabulary_used", firstMsg.get("vocabulary_used"));
            response.put("analytics", analytics);
            
            return new Result().ok(response);
            
        } catch (Exception e) {
            logger.error("Error getting conversation details", e);
            return new Result().error("Failed to get conversation details");
        }
    }
    
    private int getTotalConversations(String supabaseUserId, String date) {
        try {
            String sql = "SELECT COUNT(DISTINCT session_id) as total " +
                        "FROM ai_agent_chat_history ch " +
                        "JOIN parent_child_mapping pcm ON ch.mac_address = pcm.device_mac_address " +
                        "WHERE pcm.supabase_user_id = ? AND DATE(ch.created_at) = ?";
            
            Map<String, Object> result = jdbcTemplate.queryForMap(sql, supabaseUserId, date);
            return ((Number) result.get("total")).intValue();
        } catch (Exception e) {
            logger.warn("Could not get total conversations", e);
            return 0;
        }
    }
}