package xiaozhi.modules.rag.controller;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import xiaozhi.common.utils.Result;
import xiaozhi.modules.rag.service.MasterQueryRouter;
import xiaozhi.modules.rag.service.RagCacheService;

import java.util.HashMap;
import java.util.Map;

/**
 * Master Query Router Controller
 * REST API endpoints for query routing functionality
 * 
 * @author Claude
 * @since 1.0.0
 */
@Slf4j
@RestController
@RequestMapping("/api/rag/router")
public class MasterQueryRouterController {
    
    @Autowired
    private MasterQueryRouter masterQueryRouter;
    
    @Autowired
    private RagCacheService cacheService;
    
    /**
     * Route a single query for educational content processing
     * 
     * @param request Query routing request
     * @return Routing result with target subject and confidence
     */
    @PostMapping("/route")
    public ResponseEntity<Result<Map<String, Object>>> routeQuery(@RequestBody QueryRoutingRequest request) {
        try {
            log.info("Routing query: {}", request.getQuery());
            
            // Validate request
            if (request.getQuery() == null || request.getQuery().trim().isEmpty()) {
                Result<Map<String, Object>> result = new Result<>();
                result.setCode(400);
                result.setMsg("Query cannot be empty");
                return ResponseEntity.badRequest().body(result);
            }
            
            // Check cache first for routing results
            var cachedRouting = cacheService.getCachedQueryRouting(request.getQuery());
            
            MasterQueryRouter.QueryRoutingResult routingResult;
            boolean fromCache = false;
            
            if (cachedRouting.isPresent()) {
                log.debug("Cache hit for query routing: {}", request.getQuery());
                Map<String, Object> cached = cachedRouting.get();
                
                // Create routing result from cache
                MasterQueryRouter.QueryAnalysis analysis = MasterQueryRouter.QueryAnalysis.educational(
                    request.getQuery(),
                    (String) cached.get("target_subject"),
                    (String) cached.get("query_type"),
                    ((Number) cached.get("confidence")).doubleValue(),
                    new HashMap<>(),
                    new HashMap<>()
                );
                
                routingResult = MasterQueryRouter.QueryRoutingResult.educational(
                    request.getQuery(),
                    analysis,
                    (String) cached.get("target_subject"),
                    (String) cached.get("query_type"),
                    ((Number) cached.get("confidence")).doubleValue()
                );
                
                fromCache = true;
            } else {
                log.debug("Cache miss for query routing: {}, performing fresh routing", request.getQuery());
                
                // Route the query
                routingResult = masterQueryRouter.routeQuery(
                    request.getQuery(), 
                    request.getContext() != null ? request.getContext() : new HashMap<>()
                );
                
                // Cache the routing result if educational
                if (routingResult.isEducational()) {
                    cacheService.cacheQueryRouting(
                        request.getQuery(),
                        routingResult.getTargetSubject(),
                        routingResult.getQueryType(),
                        routingResult.getConfidence()
                    );
                }
            }
            
            // Prepare response
            Map<String, Object> responseData = new HashMap<>();
            responseData.put("original_query", routingResult.getOriginalQuery());
            responseData.put("is_educational", routingResult.isEducational());
            responseData.put("confidence", routingResult.getConfidence());
            responseData.put("from_cache", fromCache);
            
            if (routingResult.isEducational()) {
                responseData.put("target_subject", routingResult.getTargetSubject());
                responseData.put("query_type", routingResult.getQueryType());
                responseData.put("routing_context", routingResult.getRoutingContext());
                
                if (routingResult.getAnalysis() != null) {
                    Map<String, Object> analysisData = new HashMap<>();
                    analysisData.put("primary_subject", routingResult.getAnalysis().getPrimarySubject());
                    analysisData.put("subject_scores", routingResult.getAnalysis().getSubjectScores());
                    analysisData.put("detected_keywords", routingResult.getAnalysis().getDetectedKeywords());
                    analysisData.put("query_type", routingResult.getAnalysis().getQueryType());
                    responseData.put("analysis", analysisData);
                }
            } else {
                responseData.put("reason", routingResult.getAnalysis() != null ? 
                    routingResult.getAnalysis().getNonEducationalReason() : "unknown");
            }
            
            if (routingResult.getErrorMessage() != null) {
                responseData.put("error", routingResult.getErrorMessage());
            }
            
            Result<Map<String, Object>> result = new Result<>();
            result.setData(responseData);
            result.setMsg(routingResult.isEducational() ? "Query routed successfully" : "Non-educational query");
            
            log.info("Query routing completed - Educational: {}, Subject: {}, Confidence: {}", 
                routingResult.isEducational(), 
                routingResult.getTargetSubject(), 
                routingResult.getConfidence());
            
            return ResponseEntity.ok(result);
            
        } catch (Exception e) {
            log.error("Error routing query", e);
            
            Result<Map<String, Object>> result = new Result<>();
            result.setCode(500);
            result.setMsg("Internal server error during query routing");
            result.setData(Map.of("error", e.getMessage()));
            
            return ResponseEntity.internalServerError().body(result);
        }
    }
    
    /**
     * Batch route multiple queries
     * 
     * @param request Batch routing request
     * @return Batch routing results
     */
    @PostMapping("/route/batch")
    public ResponseEntity<Result<Map<String, Object>>> batchRouteQueries(@RequestBody BatchQueryRoutingRequest request) {
        try {
            log.info("Batch routing {} queries", request.getQueries().size());
            
            if (request.getQueries() == null || request.getQueries().isEmpty()) {
                Result<Map<String, Object>> result = new Result<>();
                result.setCode(400);
                result.setMsg("Queries list cannot be empty");
                return ResponseEntity.badRequest().body(result);
            }
            
            if (request.getQueries().size() > 50) {
                Result<Map<String, Object>> result = new Result<>();
                result.setCode(400);
                result.setMsg("Maximum 50 queries allowed per batch");
                return ResponseEntity.badRequest().body(result);
            }
            
            Map<String, Object> batchResults = new HashMap<>();
            Map<String, Object> overallStats = new HashMap<>();
            
            int educationalCount = 0;
            int totalCount = request.getQueries().size();
            Map<String, Integer> subjectCounts = new HashMap<>();
            
            for (int i = 0; i < request.getQueries().size(); i++) {
                String query = request.getQueries().get(i);
                
                try {
                    MasterQueryRouter.QueryRoutingResult routingResult = masterQueryRouter.routeQuery(
                        query, 
                        request.getContext() != null ? request.getContext() : new HashMap<>()
                    );
                    
                    Map<String, Object> queryResult = new HashMap<>();
                    queryResult.put("query", query);
                    queryResult.put("is_educational", routingResult.isEducational());
                    queryResult.put("confidence", routingResult.getConfidence());
                    
                    if (routingResult.isEducational()) {
                        educationalCount++;
                        queryResult.put("target_subject", routingResult.getTargetSubject());
                        queryResult.put("query_type", routingResult.getQueryType());
                        
                        // Count subjects
                        String subject = routingResult.getTargetSubject();
                        subjectCounts.put(subject, subjectCounts.getOrDefault(subject, 0) + 1);
                    } else {
                        queryResult.put("reason", routingResult.getAnalysis() != null ? 
                            routingResult.getAnalysis().getNonEducationalReason() : "unknown");
                    }
                    
                    batchResults.put("query_" + i, queryResult);
                    
                } catch (Exception e) {
                    log.error("Error routing query in batch: {}", query, e);
                    batchResults.put("query_" + i, Map.of(
                        "query", query,
                        "error", e.getMessage()
                    ));
                }
            }
            
            // Calculate overall statistics
            overallStats.put("total_queries", totalCount);
            overallStats.put("educational_queries", educationalCount);
            overallStats.put("non_educational_queries", totalCount - educationalCount);
            overallStats.put("educational_percentage", totalCount > 0 ? (educationalCount * 100.0 / totalCount) : 0.0);
            overallStats.put("subject_distribution", subjectCounts);
            
            Map<String, Object> responseData = new HashMap<>();
            responseData.put("batch_results", batchResults);
            responseData.put("statistics", overallStats);
            
            Result<Map<String, Object>> result = new Result<>();
            result.setData(responseData);
            result.setMsg("Batch query routing completed");
            
            log.info("Batch routing completed - {} educational out of {} total queries", educationalCount, totalCount);
            
            return ResponseEntity.ok(result);
            
        } catch (Exception e) {
            log.error("Error in batch query routing", e);
            
            Result<Map<String, Object>> result = new Result<>();
            result.setCode(500);
            result.setMsg("Internal server error during batch query routing");
            result.setData(Map.of("error", e.getMessage()));
            
            return ResponseEntity.internalServerError().body(result);
        }
    }
    
    /**
     * Get routing statistics and system information
     * 
     * @return Router statistics and configuration
     */
    @GetMapping("/statistics")
    public ResponseEntity<Result<Map<String, Object>>> getRoutingStatistics() {
        try {
            log.info("Retrieving routing statistics");
            
            Map<String, Object> statistics = masterQueryRouter.getRoutingStatistics();
            
            // Add system information
            statistics.put("router_version", "1.0.0");
            statistics.put("status", "operational");
            statistics.put("last_updated", System.currentTimeMillis());
            
            Result<Map<String, Object>> result = new Result<>();
            result.setData(statistics);
            result.setMsg("Routing statistics retrieved successfully");
            
            return ResponseEntity.ok(result);
            
        } catch (Exception e) {
            log.error("Error retrieving routing statistics", e);
            
            Result<Map<String, Object>> result = new Result<>();
            result.setCode(500);
            result.setMsg("Internal server error retrieving statistics");
            result.setData(Map.of("error", e.getMessage()));
            
            return ResponseEntity.internalServerError().body(result);
        }
    }
    
    /**
     * Health check endpoint for the router service
     * 
     * @return Service health status
     */
    @GetMapping("/health")
    public ResponseEntity<Result<Map<String, Object>>> getRouterHealth() {
        try {
            Map<String, Object> healthData = new HashMap<>();
            healthData.put("status", "healthy");
            healthData.put("service", "MasterQueryRouter");
            healthData.put("timestamp", System.currentTimeMillis());
            healthData.put("version", "1.0.0");
            
            // Test basic functionality
            try {
                MasterQueryRouter.QueryRoutingResult testResult = masterQueryRouter.routeQuery("test query", new HashMap<>());
                healthData.put("routing_functional", testResult != null);
            } catch (Exception e) {
                healthData.put("routing_functional", false);
                healthData.put("routing_error", e.getMessage());
            }
            
            Result<Map<String, Object>> result = new Result<>();
            result.setData(healthData);
            result.setMsg("Router service is healthy");
            
            return ResponseEntity.ok(result);
            
        } catch (Exception e) {
            log.error("Error checking router health", e);
            
            Result<Map<String, Object>> result = new Result<>();
            result.setCode(500);
            result.setMsg("Router health check failed");
            result.setData(Map.of(
                "status", "unhealthy",
                "error", e.getMessage()
            ));
            
            return ResponseEntity.internalServerError().body(result);
        }
    }
    
    /**
     * Query Routing Request DTO
     */
    public static class QueryRoutingRequest {
        private String query;
        private Map<String, Object> context;
        
        // Getters and setters
        public String getQuery() { return query; }
        public void setQuery(String query) { this.query = query; }
        public Map<String, Object> getContext() { return context; }
        public void setContext(Map<String, Object> context) { this.context = context; }
    }
    
    /**
     * Batch Query Routing Request DTO
     */
    public static class BatchQueryRoutingRequest {
        private java.util.List<String> queries;
        private Map<String, Object> context;
        
        // Getters and setters
        public java.util.List<String> getQueries() { return queries; }
        public void setQueries(java.util.List<String> queries) { this.queries = queries; }
        public Map<String, Object> getContext() { return context; }
        public void setContext(Map<String, Object> context) { this.context = context; }
    }
}