package xiaozhi.modules.rag.controller;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import xiaozhi.common.utils.Result;
import xiaozhi.modules.rag.service.EducationalIntentProvider;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Educational Intent Provider Controller
 * REST API endpoints for educational intent detection and analysis
 * 
 * @author Claude
 * @since 1.0.0
 */
@Slf4j
@RestController
@RequestMapping("/api/rag/intent")
public class EducationalIntentController {
    
    @Autowired
    private EducationalIntentProvider intentProvider;
    
    /**
     * Analyze single query for educational intent
     * 
     * @param request Intent analysis request
     * @return Educational intent analysis result
     */
    @PostMapping("/analyze")
    public ResponseEntity<Result<Map<String, Object>>> analyzeIntent(@RequestBody IntentAnalysisRequest request) {
        try {
            log.info("Analyzing educational intent for query: {}", request.getQuery());
            
            // Validate request
            if (request.getQuery() == null || request.getQuery().trim().isEmpty()) {
                Result<Map<String, Object>> result = new Result<>();
                result.setCode(400);
                result.setMsg("Query cannot be empty");
                return ResponseEntity.badRequest().body(result);
            }
            
            // Perform intent analysis
            EducationalIntentProvider.EducationalIntentResult intentResult = intentProvider.analyzeQuery(
                request.getQuery(),
                request.getContext() != null ? request.getContext() : new HashMap<>()
            );
            
            // Prepare response
            Map<String, Object> responseData = new HashMap<>();
            responseData.put("original_query", intentResult.getOriginalQuery());
            responseData.put("is_educational", intentResult.isEducational());
            responseData.put("confidence", intentResult.getConfidence());
            responseData.put("from_cache", intentResult.isFromCache());
            
            if (intentResult.isEducational()) {
                responseData.put("primary_intent", intentResult.getPrimaryIntent());
                responseData.put("secondary_intents", intentResult.getSecondaryIntents());
                responseData.put("detected_subjects", intentResult.getDetectedSubjects());
                responseData.put("complexity_level", intentResult.getComplexityLevel());
                responseData.put("recommended_grade_level", intentResult.getGradeLevel());
                responseData.put("keywords", intentResult.getKeywords());
                responseData.put("processing_metadata", intentResult.getProcessingMetadata());
            } else {
                responseData.put("reason", intentResult.getErrorMessage());
            }
            
            Result<Map<String, Object>> result = new Result<>();
            result.setData(responseData);
            result.setMsg(intentResult.isEducational() ? "Educational intent detected successfully" : "Non-educational query");
            
            log.info("Intent analysis completed - Educational: {}, Intent: {}, Confidence: {}", 
                intentResult.isEducational(), 
                intentResult.getPrimaryIntent(), 
                intentResult.getConfidence());
            
            return ResponseEntity.ok(result);
            
        } catch (Exception e) {
            log.error("Error analyzing educational intent", e);
            
            Result<Map<String, Object>> result = new Result<>();
            result.setCode(500);
            result.setMsg("Internal server error during intent analysis");
            result.setData(Map.of("error", e.getMessage()));
            
            return ResponseEntity.internalServerError().body(result);
        }
    }
    
    /**
     * Batch analyze multiple queries for educational intent
     * 
     * @param request Batch intent analysis request
     * @return Batch analysis results
     */
    @PostMapping("/analyze/batch")
    public ResponseEntity<Result<Map<String, Object>>> batchAnalyzeIntent(@RequestBody BatchIntentAnalysisRequest request) {
        try {
            log.info("Batch analyzing educational intent for {} queries", request.getQueries().size());
            
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
            Map<String, Integer> intentCounts = new HashMap<>();
            Map<String, Integer> subjectCounts = new HashMap<>();
            double totalConfidence = 0.0;
            
            for (int i = 0; i < request.getQueries().size(); i++) {
                String query = request.getQueries().get(i);
                
                try {
                    EducationalIntentProvider.EducationalIntentResult intentResult = intentProvider.analyzeQuery(
                        query,
                        request.getContext() != null ? request.getContext() : new HashMap<>()
                    );
                    
                    Map<String, Object> queryResult = new HashMap<>();
                    queryResult.put("query", query);
                    queryResult.put("is_educational", intentResult.isEducational());
                    queryResult.put("confidence", intentResult.getConfidence());
                    
                    if (intentResult.isEducational()) {
                        educationalCount++;
                        totalConfidence += intentResult.getConfidence();
                        
                        queryResult.put("primary_intent", intentResult.getPrimaryIntent());
                        queryResult.put("complexity_level", intentResult.getComplexityLevel());
                        queryResult.put("grade_level", intentResult.getGradeLevel());
                        
                        // Count intents and subjects
                        String intent = intentResult.getPrimaryIntent();
                        intentCounts.put(intent, intentCounts.getOrDefault(intent, 0) + 1);
                        
                        if (intentResult.getDetectedSubjects() != null) {
                            for (String subject : intentResult.getDetectedSubjects()) {
                                subjectCounts.put(subject, subjectCounts.getOrDefault(subject, 0) + 1);
                            }
                        }
                    } else {
                        queryResult.put("reason", intentResult.getErrorMessage());
                    }
                    
                    batchResults.put("query_" + i, queryResult);
                    
                } catch (Exception e) {
                    log.error("Error analyzing query in batch: {}", query, e);
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
            overallStats.put("average_confidence", educationalCount > 0 ? (totalConfidence / educationalCount) : 0.0);
            overallStats.put("intent_distribution", intentCounts);
            overallStats.put("subject_distribution", subjectCounts);
            
            Map<String, Object> responseData = new HashMap<>();
            responseData.put("batch_results", batchResults);
            responseData.put("statistics", overallStats);
            
            Result<Map<String, Object>> result = new Result<>();
            result.setData(responseData);
            result.setMsg("Batch intent analysis completed");
            
            log.info("Batch intent analysis completed - {} educational out of {} total queries", educationalCount, totalCount);
            
            return ResponseEntity.ok(result);
            
        } catch (Exception e) {
            log.error("Error in batch intent analysis", e);
            
            Result<Map<String, Object>> result = new Result<>();
            result.setCode(500);
            result.setMsg("Internal server error during batch intent analysis");
            result.setData(Map.of("error", e.getMessage()));
            
            return ResponseEntity.internalServerError().body(result);
        }
    }
    
    /**
     * Get intent provider statistics and configuration
     * 
     * @return Intent provider system information
     */
    @GetMapping("/statistics")
    public ResponseEntity<Result<Map<String, Object>>> getIntentStatistics() {
        try {
            log.info("Retrieving educational intent provider statistics");
            
            Map<String, Object> statistics = intentProvider.getIntentStatistics();
            
            // Add runtime information
            statistics.put("provider_version", "1.0.0");
            statistics.put("status", "operational");
            statistics.put("last_updated", System.currentTimeMillis());
            
            // Add performance targets
            Map<String, Object> targets = new HashMap<>();
            targets.put("detection_accuracy_target", 0.90);
            targets.put("confidence_threshold", 0.5);
            targets.put("response_time_target_ms", 50);
            statistics.put("performance_targets", targets);
            
            Result<Map<String, Object>> result = new Result<>();
            result.setData(statistics);
            result.setMsg("Intent provider statistics retrieved successfully");
            
            return ResponseEntity.ok(result);
            
        } catch (Exception e) {
            log.error("Error retrieving intent statistics", e);
            
            Result<Map<String, Object>> result = new Result<>();
            result.setCode(500);
            result.setMsg("Internal server error retrieving statistics");
            result.setData(Map.of("error", e.getMessage()));
            
            return ResponseEntity.internalServerError().body(result);
        }
    }
    
    /**
     * Test intent provider with sample educational queries
     * 
     * @return Test results for various educational intents
     */
    @PostMapping("/test")
    public ResponseEntity<Result<Map<String, Object>>> testIntentProvider() {
        try {
            log.info("Running educational intent provider tests");
            
            String[] testQueries = {
                // Learn concept intents
                "What is a fraction?",
                "Explain photosynthesis",
                "Define democracy",
                
                // How-to intents
                "How to add fractions?",
                "How do plants make food?",
                "Show me how to write a sentence",
                
                // Problem solving intents
                "Solve 2x + 5 = 15",
                "Calculate the area of a rectangle",
                "Find the prime numbers between 1 and 20",
                
                // Comparison intents
                "What's the difference between mammals and reptiles?",
                "Compare fractions and decimals",
                
                // Example intents
                "Give me examples of chemical reactions",
                "Show examples of adjectives",
                
                // Non-educational queries (should be rejected)
                "What's the weather today?",
                "How are you?",
                "Tell me a joke"
            };
            
            Map<String, Object> testResults = new HashMap<>();
            testResults.put("total_test_queries", testQueries.length);
            
            Map<String, Object> queryResults = new HashMap<>();
            int correctDetections = 0;
            int totalEducationalQueries = 15; // First 15 are educational, last 3 are not
            
            for (int i = 0; i < testQueries.length; i++) {
                String query = testQueries[i];
                boolean shouldBeEducational = i < totalEducationalQueries;
                
                try {
                    long startTime = System.currentTimeMillis();
                    
                    EducationalIntentProvider.EducationalIntentResult intentResult = intentProvider.analyzeQuery(
                        query, new HashMap<>()
                    );
                    
                    long responseTime = System.currentTimeMillis() - startTime;
                    
                    Map<String, Object> queryResult = new HashMap<>();
                    queryResult.put("query", query);
                    queryResult.put("expected_educational", shouldBeEducational);
                    queryResult.put("detected_educational", intentResult.isEducational());
                    queryResult.put("correct_detection", shouldBeEducational == intentResult.isEducational());
                    queryResult.put("confidence", intentResult.getConfidence());
                    queryResult.put("response_time_ms", responseTime);
                    queryResult.put("primary_intent", intentResult.getPrimaryIntent());
                    
                    if (shouldBeEducational == intentResult.isEducational()) {
                        correctDetections++;
                    }
                    
                    queryResults.put("test_" + i, queryResult);
                    
                } catch (Exception e) {
                    log.error("Error testing query: {}", query, e);
                    queryResults.put("test_" + i, Map.of(
                        "query", query,
                        "error", e.getMessage()
                    ));
                }
            }
            
            testResults.put("query_results", queryResults);
            
            // Calculate performance metrics
            double accuracy = (correctDetections * 100.0 / testQueries.length);
            
            Map<String, Object> performanceMetrics = new HashMap<>();
            performanceMetrics.put("detection_accuracy", accuracy);
            performanceMetrics.put("correct_detections", correctDetections);
            performanceMetrics.put("target_accuracy", 90.0);
            performanceMetrics.put("test_passed", accuracy >= 90.0);
            
            testResults.put("performance_metrics", performanceMetrics);
            
            Result<Map<String, Object>> result = new Result<>();
            result.setData(testResults);
            result.setMsg("Intent provider tests completed");
            
            log.info("Intent provider tests completed - Accuracy: {}%", accuracy);
            
            return ResponseEntity.ok(result);
            
        } catch (Exception e) {
            log.error("Error running intent provider tests", e);
            
            Result<Map<String, Object>> result = new Result<>();
            result.setCode(500);
            result.setMsg("Error running intent tests");
            result.setData(Map.of("error", e.getMessage()));
            
            return ResponseEntity.internalServerError().body(result);
        }
    }
    
    /**
     * Health check for educational intent provider
     * 
     * @return Service health status
     */
    @GetMapping("/health")
    public ResponseEntity<Result<Map<String, Object>>> getIntentHealth() {
        try {
            Map<String, Object> healthData = new HashMap<>();
            healthData.put("service", "Educational Intent Provider");
            healthData.put("status", "healthy");
            healthData.put("timestamp", System.currentTimeMillis());
            healthData.put("version", "1.0.0");
            
            // Test basic functionality
            try {
                EducationalIntentProvider.EducationalIntentResult testResult = intentProvider.analyzeQuery(
                    "What is mathematics?", new HashMap<>()
                );
                healthData.put("intent_detection_functional", testResult != null);
                healthData.put("test_detection_result", testResult.isEducational());
            } catch (Exception e) {
                healthData.put("intent_detection_functional", false);
                healthData.put("detection_error", e.getMessage());
            }
            
            Result<Map<String, Object>> result = new Result<>();
            result.setData(healthData);
            result.setMsg("Educational intent provider is healthy");
            
            return ResponseEntity.ok(result);
            
        } catch (Exception e) {
            log.error("Error checking intent provider health", e);
            
            Result<Map<String, Object>> result = new Result<>();
            result.setCode(500);
            result.setMsg("Intent provider health check failed");
            result.setData(Map.of(
                "status", "unhealthy",
                "error", e.getMessage()
            ));
            
            return ResponseEntity.internalServerError().body(result);
        }
    }
    
    /**
     * Intent Analysis Request DTO
     */
    public static class IntentAnalysisRequest {
        private String query;
        private Map<String, Object> context;
        
        // Getters and setters
        public String getQuery() { return query; }
        public void setQuery(String query) { this.query = query; }
        public Map<String, Object> getContext() { return context; }
        public void setContext(Map<String, Object> context) { this.context = context; }
    }
    
    /**
     * Batch Intent Analysis Request DTO
     */
    public static class BatchIntentAnalysisRequest {
        private List<String> queries;
        private Map<String, Object> context;
        
        // Getters and setters
        public List<String> getQueries() { return queries; }
        public void setQueries(List<String> queries) { this.queries = queries; }
        public Map<String, Object> getContext() { return context; }
        public void setContext(Map<String, Object> context) { this.context = context; }
    }
}