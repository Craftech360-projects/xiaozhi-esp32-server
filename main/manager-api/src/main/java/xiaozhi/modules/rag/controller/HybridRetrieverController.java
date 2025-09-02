package xiaozhi.modules.rag.controller;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import xiaozhi.common.utils.Result;
import xiaozhi.modules.rag.service.HybridRetriever;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Hybrid Retriever Controller
 * REST API endpoints for hybrid search functionality
 * 
 * @author Claude
 * @since 1.0.0
 */
@Slf4j
@RestController
@RequestMapping("/api/rag/hybrid")
public class HybridRetrieverController {
    
    @Autowired
    private HybridRetriever hybridRetriever;
    
    /**
     * Perform hybrid search combining semantic and keyword approaches
     * 
     * @param request Hybrid search request
     * @return Search results with relevance scores
     */
    @PostMapping("/search")
    public ResponseEntity<Result<Map<String, Object>>> hybridSearch(@RequestBody HybridSearchRequestDTO request) {
        try {
            log.info("Performing hybrid search for query: {}", request.getQuery());
            
            // Validate request
            if (request.getQuery() == null || request.getQuery().trim().isEmpty()) {
                Result<Map<String, Object>> result = new Result<>();
                result.setCode(400);
                result.setMsg("Query cannot be empty");
                return ResponseEntity.badRequest().body(result);
            }
            
            // Convert DTO to service request
            HybridRetriever.HybridSearchRequest serviceRequest = new HybridRetriever.HybridSearchRequest();
            serviceRequest.setQuery(request.getQuery());
            serviceRequest.setSubject(request.getSubject());
            serviceRequest.setStandard(request.getStandard());
            serviceRequest.setContentTypes(request.getContentTypes());
            serviceRequest.setDifficultyLevels(request.getDifficultyLevels());
            serviceRequest.setLimit(request.getLimit() != null ? request.getLimit() : 5);
            serviceRequest.setIncludeMetadata(request.isIncludeMetadata());
            
            // Perform hybrid search
            List<HybridRetriever.HybridSearchResult> searchResults = 
                hybridRetriever.hybridSearch(serviceRequest).join();
            
            // Prepare response
            Map<String, Object> responseData = new HashMap<>();
            responseData.put("query", request.getQuery());
            responseData.put("results_count", searchResults.size());
            responseData.put("search_results", searchResults.stream().map(result -> {
                Map<String, Object> resultMap = new HashMap<>();
                resultMap.put("chunk_id", result.getChunkId());
                resultMap.put("content", result.getContent());
                resultMap.put("final_score", result.getFinalScore());
                resultMap.put("semantic_score", result.getSemanticScore());
                resultMap.put("keyword_score", result.getKeywordScore());
                resultMap.put("hybrid_score", result.getHybridScore());
                resultMap.put("reranking_score", result.getRerankingScore());
                
                if (request.isIncludeMetadata() && result.getMetadata() != null) {
                    resultMap.put("metadata", result.getMetadata());
                }
                
                return resultMap;
            }).toList());
            
            // Add search statistics
            Map<String, Object> searchStats = new HashMap<>();
            if (!searchResults.isEmpty()) {
                searchStats.put("highest_score", searchResults.get(0).getFinalScore());
                searchStats.put("lowest_score", searchResults.get(searchResults.size() - 1).getFinalScore());
                searchStats.put("average_semantic_score", searchResults.stream()
                    .mapToDouble(HybridRetriever.HybridSearchResult::getSemanticScore)
                    .average().orElse(0.0));
                searchStats.put("average_keyword_score", searchResults.stream()
                    .mapToDouble(HybridRetriever.HybridSearchResult::getKeywordScore)
                    .average().orElse(0.0));
            }
            responseData.put("search_statistics", searchStats);
            
            Result<Map<String, Object>> result = new Result<>();
            result.setData(responseData);
            result.setMsg("Hybrid search completed successfully");
            
            log.info("Hybrid search completed - {} results for query: {}", 
                searchResults.size(), request.getQuery());
            
            return ResponseEntity.ok(result);
            
        } catch (Exception e) {
            log.error("Error performing hybrid search", e);
            
            Result<Map<String, Object>> result = new Result<>();
            result.setCode(500);
            result.setMsg("Internal server error during hybrid search");
            result.setData(Map.of("error", e.getMessage()));
            
            return ResponseEntity.internalServerError().body(result);
        }
    }
    
    /**
     * Get hybrid search system statistics
     * 
     * @return Search system configuration and performance metrics
     */
    @GetMapping("/statistics")
    public ResponseEntity<Result<Map<String, Object>>> getSearchStatistics() {
        try {
            log.info("Retrieving hybrid search statistics");
            
            Map<String, Object> statistics = hybridRetriever.getSearchStatistics();
            
            // Add system information
            statistics.put("service_version", "1.0.0");
            statistics.put("status", "operational");
            statistics.put("last_updated", System.currentTimeMillis());
            
            // Add performance targets
            Map<String, Object> performanceTargets = new HashMap<>();
            performanceTargets.put("retrieval_precision_target", 0.90);
            performanceTargets.put("response_time_target_ms", 500);
            performanceTargets.put("max_concurrent_searches", 50);
            statistics.put("performance_targets", performanceTargets);
            
            Result<Map<String, Object>> result = new Result<>();
            result.setData(statistics);
            result.setMsg("Search statistics retrieved successfully");
            
            return ResponseEntity.ok(result);
            
        } catch (Exception e) {
            log.error("Error retrieving search statistics", e);
            
            Result<Map<String, Object>> result = new Result<>();
            result.setCode(500);
            result.setMsg("Internal server error retrieving statistics");
            result.setData(Map.of("error", e.getMessage()));
            
            return ResponseEntity.internalServerError().body(result);
        }
    }
    
    /**
     * Health check endpoint for the hybrid search service
     * 
     * @return Service health status
     */
    @GetMapping("/health")
    public ResponseEntity<Result<Map<String, Object>>> getSearchHealth() {
        try {
            Map<String, Object> healthData = new HashMap<>();
            healthData.put("status", "healthy");
            healthData.put("service", "HybridRetriever");
            healthData.put("timestamp", System.currentTimeMillis());
            healthData.put("version", "1.0.0");
            
            // Test basic functionality
            try {
                HybridRetriever.HybridSearchRequest testRequest = new HybridRetriever.HybridSearchRequest();
                testRequest.setQuery("test query");
                testRequest.setLimit(1);
                
                List<HybridRetriever.HybridSearchResult> testResults = hybridRetriever.hybridSearch(testRequest).join();
                healthData.put("search_functional", true);
                healthData.put("test_results_count", testResults.size());
            } catch (Exception e) {
                healthData.put("search_functional", false);
                healthData.put("search_error", e.getMessage());
            }
            
            Result<Map<String, Object>> result = new Result<>();
            result.setData(healthData);
            result.setMsg("Hybrid search service is healthy");
            
            return ResponseEntity.ok(result);
            
        } catch (Exception e) {
            log.error("Error checking search health", e);
            
            Result<Map<String, Object>> result = new Result<>();
            result.setCode(500);
            result.setMsg("Search health check failed");
            result.setData(Map.of(
                "status", "unhealthy",
                "error", e.getMessage()
            ));
            
            return ResponseEntity.internalServerError().body(result);
        }
    }
    
    /**
     * Test hybrid search with sample educational queries
     * 
     * @return Test results for various mathematical queries
     */
    @PostMapping("/test")
    public ResponseEntity<Result<Map<String, Object>>> testHybridSearch() {
        try {
            log.info("Running hybrid search tests with sample queries");
            
            String[] testQueries = {
                "What are fractions?",
                "How to add fractions?", 
                "What is the area of a rectangle?",
                "Explain prime numbers",
                "How to calculate perimeter?",
                "What are angles?",
                "How to solve equations?",
                "What is symmetry?",
                "Explain data handling",
                "What are patterns in mathematics?"
            };
            
            Map<String, Object> testResults = new HashMap<>();
            testResults.put("total_test_queries", testQueries.length);
            
            Map<String, Object> queryResults = new HashMap<>();
            double totalAverageScore = 0.0;
            int successfulQueries = 0;
            
            for (int i = 0; i < testQueries.length; i++) {
                String query = testQueries[i];
                
                try {
                    long startTime = System.currentTimeMillis();
                    
                    HybridRetriever.HybridSearchRequest request = new HybridRetriever.HybridSearchRequest();
                    request.setQuery(query);
                    request.setSubject("mathematics");
                    request.setStandard(6);
                    request.setLimit(5);
                    
                    List<HybridRetriever.HybridSearchResult> results = hybridRetriever.hybridSearch(request).join();
                    
                    long responseTime = System.currentTimeMillis() - startTime;
                    
                    Map<String, Object> queryResult = new HashMap<>();
                    queryResult.put("query", query);
                    queryResult.put("results_count", results.size());
                    queryResult.put("response_time_ms", responseTime);
                    queryResult.put("status", "success");
                    
                    if (!results.isEmpty()) {
                        double averageScore = results.stream()
                            .mapToDouble(HybridRetriever.HybridSearchResult::getFinalScore)
                            .average().orElse(0.0);
                        queryResult.put("average_score", averageScore);
                        totalAverageScore += averageScore;
                        successfulQueries++;
                    }
                    
                    queryResults.put("test_" + i, queryResult);
                    
                } catch (Exception e) {
                    log.error("Error testing query: {}", query, e);
                    queryResults.put("test_" + i, Map.of(
                        "query", query,
                        "status", "error",
                        "error", e.getMessage()
                    ));
                }
            }
            
            testResults.put("query_results", queryResults);
            
            // Calculate overall performance metrics
            Map<String, Object> overallMetrics = new HashMap<>();
            overallMetrics.put("success_rate", (successfulQueries * 100.0 / testQueries.length));
            overallMetrics.put("average_relevance_score", successfulQueries > 0 ? (totalAverageScore / successfulQueries) : 0.0);
            overallMetrics.put("target_success_rate", 95.0);
            overallMetrics.put("target_relevance_score", 0.85);
            
            testResults.put("performance_metrics", overallMetrics);
            
            Result<Map<String, Object>> result = new Result<>();
            result.setData(testResults);
            result.setMsg("Hybrid search tests completed");
            
            log.info("Hybrid search tests completed - {}/{} successful queries", 
                successfulQueries, testQueries.length);
            
            return ResponseEntity.ok(result);
            
        } catch (Exception e) {
            log.error("Error running hybrid search tests", e);
            
            Result<Map<String, Object>> result = new Result<>();
            result.setCode(500);
            result.setMsg("Error running search tests");
            result.setData(Map.of("error", e.getMessage()));
            
            return ResponseEntity.internalServerError().body(result);
        }
    }
    
    /**
     * Hybrid Search Request DTO
     */
    public static class HybridSearchRequestDTO {
        private String query;
        private String subject;
        private Integer standard;
        private List<String> contentTypes;
        private List<String> difficultyLevels;
        private Integer limit;
        private boolean includeMetadata = true;
        
        // Getters and setters
        public String getQuery() { return query; }
        public void setQuery(String query) { this.query = query; }
        public String getSubject() { return subject; }
        public void setSubject(String subject) { this.subject = subject; }
        public Integer getStandard() { return standard; }
        public void setStandard(Integer standard) { this.standard = standard; }
        public List<String> getContentTypes() { return contentTypes; }
        public void setContentTypes(List<String> contentTypes) { this.contentTypes = contentTypes; }
        public List<String> getDifficultyLevels() { return difficultyLevels; }
        public void setDifficultyLevels(List<String> difficultyLevels) { this.difficultyLevels = difficultyLevels; }
        public Integer getLimit() { return limit; }
        public void setLimit(Integer limit) { this.limit = limit; }
        public boolean isIncludeMetadata() { return includeMetadata; }
        public void setIncludeMetadata(boolean includeMetadata) { this.includeMetadata = includeMetadata; }
    }
}