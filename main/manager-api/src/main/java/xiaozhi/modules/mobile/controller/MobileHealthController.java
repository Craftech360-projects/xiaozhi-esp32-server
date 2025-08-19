package xiaozhi.modules.mobile.controller;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import xiaozhi.common.utils.Result;

import java.util.HashMap;
import java.util.Map;

/**
 * Mobile API Health Check Controller
 * Provides health check endpoints that don't require authentication
 */
@RestController
@RequestMapping("/api/mobile")
@Tag(name = "Mobile Health Check")
@Slf4j
public class MobileHealthController {
    
    @GetMapping("/health")
    @Operation(summary = "Health check endpoint")
    public Result<Map<String, Object>> health() {
        Map<String, Object> data = new HashMap<>();
        data.put("status", "healthy");
        data.put("message", "Mobile API is running");
        data.put("timestamp", System.currentTimeMillis());
        data.put("version", "1.0.0");
        
        log.info("Health check requested");
        return new Result<Map<String, Object>>().ok(data);
    }
    
    @GetMapping("/test")
    @Operation(summary = "Test endpoint without authentication")
    public Result<Map<String, Object>> test() {
        Map<String, Object> data = new HashMap<>();
        data.put("message", "Test endpoint working - no authentication required");
        data.put("info", "Use this endpoint to verify API connectivity");
        
        return new Result<Map<String, Object>>().ok(data);
    }
    
}