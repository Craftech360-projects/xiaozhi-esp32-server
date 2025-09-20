package xiaozhi.modules.config.controller;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.AllArgsConstructor;
import org.apache.shiro.authz.annotation.RequiresPermissions;
import org.springframework.web.bind.annotation.*;
import xiaozhi.common.utils.Result;
import xiaozhi.modules.config.service.LiveKitConfigService;

import java.util.Map;

@AllArgsConstructor
@RestController
@RequestMapping("/config/livekit")
@Tag(name = "LiveKit Configuration")
public class LiveKitConfigController {

    private final LiveKitConfigService liveKitConfigService;

    @GetMapping("/current")
    @Operation(summary = "Get current LiveKit configuration")
    public Result<Map<String, Object>> getCurrentConfig() {
        Map<String, Object> config = liveKitConfigService.getCurrentConfig();
        return new Result<Map<String, Object>>().ok(config);
    }

    @GetMapping("/default-models")
    @Operation(summary = "Get default models from database for LiveKit sync")
    public Result<Map<String, Object>> getDefaultModels() {
        Map<String, Object> models = liveKitConfigService.getDefaultModels();
        return new Result<Map<String, Object>>().ok(models);
    }

    @PostMapping("/sync")
    @Operation(summary = "Sync configuration to LiveKit agent")
    @RequiresPermissions("sys:role:superAdmin")
    public Result<Map<String, Object>> syncConfig() {
        Map<String, Object> result = liveKitConfigService.syncToLiveKit();
        return new Result<Map<String, Object>>().ok(result);
    }

    @PostMapping("/notify")
    @Operation(summary = "Notify LiveKit agent of config changes")
    public Result<Void> notifyConfigChange() {
        liveKitConfigService.notifyConfigChange();
        return new Result<Void>();
    }
}