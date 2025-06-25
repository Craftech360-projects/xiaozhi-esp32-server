package xiaozhi.modules.agent.controller;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;
import xiaozhi.common.utils.Result;
import xiaozhi.modules.agent.service.AgentMcpAccessPointService;

@Tag(name = "智能体Mcp接入点管理")
@RequiredArgsConstructor
@RestController
@RequestMapping("/agent/mcp")
public class AgentMcpAccessPointController {
    private final AgentMcpAccessPointService agentMcpAccessPointService;

    /**
     * 获取智能体的Mcp接入点地址
     * @param audioId 智能体id
     * @return 返回错误提醒或者Mcp接入点地址
     */
    @Operation(summary = "获取智能体的Mcp接入点地址")
    @GetMapping("/address/{audioId}")
    public Result<String> getAgentMcpAccessAddress(@PathVariable("audioId") String audioId) {
        String agentMcpAccessAddress = agentMcpAccessPointService.getAgentMcpAccessAddress(audioId);
        if (agentMcpAccessAddress == null) {
           return new Result<String>().error("请进入参数管理配置mcp接入点地址");
        }
        return new Result<String>().ok(agentMcpAccessAddress);
    }
}
