package xiaozhi.modules.config.controller;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.AllArgsConstructor;
import org.apache.shiro.authz.annotation.RequiresPermissions;
import org.springframework.web.bind.annotation.*;
import xiaozhi.common.utils.Result;
import xiaozhi.modules.config.dto.LiveKitChatDataDTO;
import xiaozhi.modules.config.service.LiveKitChatService;

import java.util.List;
import java.util.Map;

/**
 * LiveKit Chat Controller
 * API endpoints for managing LiveKit chat data integration
 *
 * @author Claude Code
 * @version 1.0
 * @since 1.0.0
 */
@AllArgsConstructor
@RestController
@RequestMapping("/config/livekit/chat")
@Tag(name = "LiveKit Chat Management")
public class LiveKitChatController {

    private final LiveKitChatService liveKitChatService;

    @GetMapping("/fetch/{agentId}")
    @Operation(summary = "Fetch chat data from LiveKit server for specific agent")
    public Result<List<LiveKitChatDataDTO>> fetchChatData(
            @Parameter(description = "Agent ID", required = true)
            @PathVariable String agentId,
            @Parameter(description = "Session ID (optional)")
            @RequestParam(required = false) String sessionId) {

        List<LiveKitChatDataDTO> chatData = liveKitChatService.fetchChatDataFromLiveKit(agentId, sessionId);
        return new Result<List<LiveKitChatDataDTO>>().ok(chatData);
    }

    @PostMapping("/sync/{agentId}")
    @Operation(summary = "Sync chat data from LiveKit to MySQL for specific agent")
    @RequiresPermissions("sys:role:superAdmin")
    public Result<Map<String, Object>> syncChatData(
            @Parameter(description = "Agent ID", required = true)
            @PathVariable String agentId,
            @Parameter(description = "Session ID (optional)")
            @RequestParam(required = false) String sessionId) {

        boolean success = liveKitChatService.syncChatDataFromLiveKit(agentId, sessionId);

        Map<String, Object> result = Map.of(
                "success", success,
                "message", success ?
                        "Chat data synced successfully from LiveKit to MySQL" :
                        "Failed to sync chat data from LiveKit to MySQL",
                "agentId", agentId,
                "sessionId", sessionId != null ? sessionId : "all"
        );

        return new Result<Map<String, Object>>().ok(result);
    }

    @PostMapping("/store/{agentId}")
    @Operation(summary = "Store provided chat data to MySQL with agent binding")
    // @RequiresPermissions("sys:role:normal") // Disabled for LiveKit server API calls
    public Result<Map<String, Object>> storeChatData(
            @Parameter(description = "Agent ID", required = true)
            @PathVariable String agentId,
            @RequestBody List<LiveKitChatDataDTO> chatDataList) {

        boolean success = liveKitChatService.storeChatDataToMySQL(chatDataList, agentId);

        Map<String, Object> result = Map.of(
                "success", success,
                "message", success ?
                        "Chat data stored successfully to MySQL" :
                        "Failed to store chat data to MySQL",
                "agentId", agentId,
                "recordCount", chatDataList != null ? chatDataList.size() : 0
        );

        return new Result<Map<String, Object>>().ok(result);
    }

    @GetMapping("/history/{agentId}")
    @Operation(summary = "Get chat history from MySQL for specific agent")
    @RequiresPermissions("sys:role:normal")
    public Result<Map<String, Object>> getChatHistory(
            @Parameter(description = "Agent ID", required = true)
            @PathVariable String agentId,
            @Parameter(description = "Session ID (optional)")
            @RequestParam(required = false) String sessionId) {

        Map<String, Object> result = liveKitChatService.getChatHistoryFromMySQL(agentId, sessionId);
        return new Result<Map<String, Object>>().ok(result);
    }
}