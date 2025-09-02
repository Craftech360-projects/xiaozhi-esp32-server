package xiaozhi.modules.rag.controller;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import xiaozhi.common.utils.Result;
import xiaozhi.modules.rag.service.RagCacheService;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * RAG Cache Controller
 * REST API endpoints for cache management and monitoring
 * 
 * @author Claude
 * @since 1.0.0
 */
@Slf4j
@RestController
@RequestMapping("/api/rag/cache")
public class RagCacheController {
    
    @Autowired
    private RagCacheService ragCacheService;
    
    /**
     * Get cache performance metrics and statistics
     * 
     * @return Cache performance data including hit rate and popular queries
     */
    @GetMapping("/metrics")
    public ResponseEntity<Result<Map<String, Object>>> getCacheMetrics() {
        try {
            log.info("Retrieving RAG cache metrics");
            
            Map<String, Object> metrics = ragCacheService.getCacheMetrics();
            
            // Add system information
            metrics.put("service", "RAG Cache Service");
            metrics.put("timestamp", System.currentTimeMillis());
            
            // Add performance targets
            Map<String, Object> targets = new HashMap<>();
            targets.put("target_hit_rate", 70.0);
            targets.put("target_response_time_improvement", 50.0);
            targets.put("cache_strategy", "intelligent_ttl_with_popularity");
            metrics.put("performance_targets", targets);
            
            Result<Map<String, Object>> result = new Result<>();
            result.setData(metrics);
            result.setMsg("Cache metrics retrieved successfully");
            
            return ResponseEntity.ok(result);
            
        } catch (Exception e) {
            log.error("Error retrieving cache metrics", e);
            
            Result<Map<String, Object>> result = new Result<>();
            result.setCode(500);
            result.setMsg("Internal server error retrieving cache metrics");
            result.setData(Map.of("error", e.getMessage()));
            
            return ResponseEntity.internalServerError().body(result);
        }
    }
    
    /**
     * Get popular queries for cache optimization
     * 
     * @param limit Maximum number of popular queries to return
     * @return List of most frequently queried educational content
     */
    @GetMapping("/popular-queries")
    public ResponseEntity<Result<Map<String, Object>>> getPopularQueries(@RequestParam(defaultValue = "20") int limit) {
        try {
            log.info("Retrieving top {} popular queries", limit);
            
            if (limit <= 0 || limit > 100) {
                Result<Map<String, Object>> result = new Result<>();
                result.setCode(400);
                result.setMsg("Limit must be between 1 and 100");
                return ResponseEntity.badRequest().body(result);
            }
            
            List<String> popularQueries = ragCacheService.getPopularQueries(limit);
            
            Map<String, Object> responseData = new HashMap<>();
            responseData.put("popular_queries", popularQueries);
            responseData.put("count", popularQueries.size());
            responseData.put("limit", limit);
            responseData.put("generated_at", System.currentTimeMillis());
            
            // Add insights about popular queries
            Map<String, Object> insights = new HashMap<>();
            if (!popularQueries.isEmpty()) {
                insights.put("most_popular", popularQueries.get(0));
                
                // Analyze query patterns
                long mathQueries = popularQueries.stream()
                    .filter(q -> q.toLowerCase().contains("math") || q.toLowerCase().contains("number") || 
                               q.toLowerCase().contains("calculate") || q.toLowerCase().contains("solve"))
                    .count();
                
                insights.put("math_query_percentage", (mathQueries * 100.0 / popularQueries.size()));
                insights.put("cache_optimization_potential", "high");
            }
            responseData.put("insights", insights);
            
            Result<Map<String, Object>> result = new Result<>();
            result.setData(responseData);
            result.setMsg("Popular queries retrieved successfully");
            
            return ResponseEntity.ok(result);
            
        } catch (Exception e) {
            log.error("Error retrieving popular queries", e);
            
            Result<Map<String, Object>> result = new Result<>();
            result.setCode(500);
            result.setMsg("Internal server error retrieving popular queries");
            result.setData(Map.of("error", e.getMessage()));
            
            return ResponseEntity.internalServerError().body(result);
        }
    }
    
    /**
     * Invalidate cache entries matching a pattern
     * 
     * @param request Cache invalidation request
     * @return Invalidation result
     */
    @PostMapping("/invalidate")
    public ResponseEntity<Result<Map<String, Object>>> invalidateCache(@RequestBody CacheInvalidationRequest request) {
        try {
            log.info("Invalidating cache for pattern: {}", request.getPattern());
            
            if (request.getPattern() == null || request.getPattern().trim().isEmpty()) {
                Result<Map<String, Object>> result = new Result<>();
                result.setCode(400);
                result.setMsg("Pattern cannot be empty");
                return ResponseEntity.badRequest().body(result);
            }
            
            ragCacheService.invalidateCache(request.getPattern());
            
            Map<String, Object> responseData = new HashMap<>();
            responseData.put("pattern", request.getPattern());
            responseData.put("invalidated_at", System.currentTimeMillis());
            responseData.put("reason", request.getReason());
            responseData.put("status", "success");
            
            Result<Map<String, Object>> result = new Result<>();
            result.setData(responseData);
            result.setMsg("Cache invalidated successfully");
            
            log.info("Successfully invalidated cache for pattern: {}", request.getPattern());
            
            return ResponseEntity.ok(result);
            
        } catch (Exception e) {
            log.error("Error invalidating cache for pattern: {}", request.getPattern(), e);
            
            Result<Map<String, Object>> result = new Result<>();
            result.setCode(500);
            result.setMsg("Internal server error during cache invalidation");
            result.setData(Map.of("error", e.getMessage()));
            
            return ResponseEntity.internalServerError().body(result);
        }
    }
    
    /**
     * Clear all RAG cache entries (admin operation)
     * 
     * @return Cache clearing result
     */
    @PostMapping("/clear-all")
    public ResponseEntity<Result<Map<String, Object>>> clearAllCache() {
        try {
            log.warn("Clearing all RAG cache entries - admin operation");
            
            ragCacheService.clearAllCache();
            
            Map<String, Object> responseData = new HashMap<>();
            responseData.put("operation", "clear_all_cache");
            responseData.put("executed_at", System.currentTimeMillis());
            responseData.put("status", "success");
            responseData.put("warning", "All cached search results have been cleared");
            
            Result<Map<String, Object>> result = new Result<>();
            result.setData(responseData);
            result.setMsg("All cache entries cleared successfully");
            
            return ResponseEntity.ok(result);
            
        } catch (Exception e) {
            log.error("Error clearing all cache", e);
            
            Result<Map<String, Object>> result = new Result<>();
            result.setCode(500);
            result.setMsg("Internal server error during cache clearing");
            result.setData(Map.of("error", e.getMessage()));
            
            return ResponseEntity.internalServerError().body(result);
        }
    }
    
    /**
     * Preload popular queries into cache for performance optimization
     * 
     * @return Preloading operation result
     */
    @PostMapping("/preload")
    public ResponseEntity<Result<Map<String, Object>>> preloadCache() {
        try {
            log.info("Starting cache preloading operation");
            
            ragCacheService.preloadPopularQueries();
            
            Map<String, Object> responseData = new HashMap<>();
            responseData.put("operation", "preload_cache");
            responseData.put("started_at", System.currentTimeMillis());
            responseData.put("status", "initiated");
            responseData.put("note", "Cache preloading has been initiated in the background");
            
            Result<Map<String, Object>> result = new Result<>();
            result.setData(responseData);
            result.setMsg("Cache preloading initiated successfully");
            
            return ResponseEntity.ok(result);
            
        } catch (Exception e) {
            log.error("Error initiating cache preloading", e);
            
            Result<Map<String, Object>> result = new Result<>();
            result.setCode(500);
            result.setMsg("Internal server error during cache preloading");
            result.setData(Map.of("error", e.getMessage()));
            
            return ResponseEntity.internalServerError().body(result);
        }
    }
    
    /**
     * Get cache health status
     * 
     * @return Cache service health information
     */
    @GetMapping("/health")
    public ResponseEntity<Result<Map<String, Object>>> getCacheHealth() {
        try {
            Map<String, Object> healthData = new HashMap<>();
            
            // Get basic metrics to test Redis connectivity
            Map<String, Object> metrics = ragCacheService.getCacheMetrics();
            boolean redisAvailable = (Boolean) metrics.getOrDefault("redis_available", false);
            
            healthData.put("service", "RAG Cache Service");
            healthData.put("status", redisAvailable ? "healthy" : "degraded");
            healthData.put("redis_available", redisAvailable);
            healthData.put("timestamp", System.currentTimeMillis());
            healthData.put("version", "1.0.0");
            
            if (redisAvailable) {
                double hitRate = ((Number) metrics.getOrDefault("hit_rate", 0.0)).doubleValue();
                healthData.put("cache_hit_rate", hitRate);
                healthData.put("performance_status", hitRate >= 70.0 ? "optimal" : "suboptimal");
            }
            
            Result<Map<String, Object>> result = new Result<>();
            result.setData(healthData);
            result.setMsg(redisAvailable ? "Cache service is healthy" : "Cache service is degraded - Redis unavailable");
            
            return ResponseEntity.ok(result);
            
        } catch (Exception e) {
            log.error("Error checking cache health", e);
            
            Result<Map<String, Object>> result = new Result<>();
            result.setCode(500);
            result.setMsg("Cache health check failed");
            result.setData(Map.of(
                "status", "unhealthy",
                "error", e.getMessage()
            ));
            
            return ResponseEntity.internalServerError().body(result);
        }
    }
    
    /**
     * Cache Invalidation Request DTO
     */
    public static class CacheInvalidationRequest {
        private String pattern;
        private String reason;
        
        // Getters and setters
        public String getPattern() { return pattern; }
        public void setPattern(String pattern) { this.pattern = pattern; }
        public String getReason() { return reason; }
        public void setReason(String reason) { this.reason = reason; }
    }
}