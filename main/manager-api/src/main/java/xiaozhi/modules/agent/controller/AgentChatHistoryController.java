package xiaozhi.modules.agent.controller;

import org.springframework.web.bind.annotation.*;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import xiaozhi.common.utils.Result;
import xiaozhi.modules.agent.dto.AgentChatHistoryReportDTO;
import xiaozhi.modules.agent.service.biz.AgentChatHistoryBizService;
import xiaozhi.modules.agent.service.AgentChatHistoryService;
import xiaozhi.modules.agent.entity.AgentChatHistoryEntity;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;

import java.util.*;
import java.util.stream.Collectors;

@Tag(name = "Agent Chat History Management")
@RequiredArgsConstructor
@RestController
@RequestMapping("/agent/chat-history")
@Slf4j
public class AgentChatHistoryController {
    private final AgentChatHistoryBizService agentChatHistoryBizService;

    /**
     * 小智服务聊天上报请求
     * <p>
     * 小智服务聊天上报请求，包含Base64编码的音频数据和相关信息。
     *
     * @param request 包含上传文件及相关信息的请求对象
     */
    @Operation(summary = "Xiaozhi service chat report request")
    @PostMapping("/report")
    public Result<Boolean> uploadFile(@Valid @RequestBody AgentChatHistoryReportDTO request) {
        long startTime = System.currentTimeMillis();

        log.info("🔥 [CHAT_HISTORY_ENDPOINT] === REQUEST START ===");
        log.info("🔥 [CHAT_HISTORY_ENDPOINT] Request received: macAddress={}, sessionId={}, chatType={}",
                request.getMacAddress(), request.getSessionId(), request.getChatType());
        log.info("🔥 [CHAT_HISTORY_ENDPOINT] Content preview: {}",
                request.getContent() != null ?
                    request.getContent().substring(0, Math.min(50, request.getContent().length())) + "..." : "null");
        log.info("🔥 [CHAT_HISTORY_ENDPOINT] Report time: {}", request.getReportTime());
        log.info("🔥 [CHAT_HISTORY_ENDPOINT] Has audio: {}", request.getAudioBase64() != null && !request.getAudioBase64().isEmpty());

        try {
            log.info("🔥 [CHAT_HISTORY_ENDPOINT] Calling AgentChatHistoryBizService.report()...");
            Boolean result = agentChatHistoryBizService.report(request);

            long processingTime = System.currentTimeMillis() - startTime;
            log.info("🔥 [CHAT_HISTORY_ENDPOINT] Service returned: {} (Processing time: {}ms)", result, processingTime);

            if (result != null && result) {
                log.info("🔥 [CHAT_HISTORY_ENDPOINT] ✅ SUCCESS: Chat history saved successfully");
            } else {
                log.warn("🔥 [CHAT_HISTORY_ENDPOINT] ⚠️ WARNING: Service returned false - check business logic");
            }

            log.info("🔥 [CHAT_HISTORY_ENDPOINT] === REQUEST END ===");
            return new Result<Boolean>().ok(result);

        } catch (Exception e) {
            long processingTime = System.currentTimeMillis() - startTime;
            log.error("🔥 [CHAT_HISTORY_ENDPOINT] ❌ ERROR: Exception in chat history processing (Processing time: {}ms)", processingTime, e);
            log.error("🔥 [CHAT_HISTORY_ENDPOINT] === REQUEST END WITH ERROR ===");
            throw e;
        }
    }
}
