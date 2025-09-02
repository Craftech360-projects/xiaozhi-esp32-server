package xiaozhi.modules.rag.service;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.*;
import java.util.concurrent.CompletableFuture;

/**
 * RAG System Testing Service
 * Comprehensive testing for Standard 6 Mathematics RAG implementation
 * 
 * @author Claude
 * @since 1.0.0
 */
@Slf4j
@Service
public class RagSystemTestService {
    
    @Autowired
    private MasterQueryRouter queryRouter;
    
    @Autowired
    private HybridRetriever hybridRetriever;
    
    @Autowired
    private EducationalIntentProvider intentProvider;
    
    @Autowired(required = false)
    private RagCacheService cacheService;
    
    // Standard 6 Mathematics test queries organized by chapter and difficulty
    private static final Map<String, List<TestQuery>> TEST_QUERIES = new HashMap<>();
    
    static {
        // Chapter 1: Patterns in Mathematics
        TEST_QUERIES.put("patterns", Arrays.asList(
            new TestQuery("What are patterns in mathematics?", "LEARN_CONCEPT", "easy", 6),
            new TestQuery("How to identify number patterns?", "HOW_TO", "medium", 6),
            new TestQuery("Find the next number in the pattern: 2, 4, 6, 8, ?", "SOLVE_PROBLEM", "easy", 6),
            new TestQuery("Explain geometric patterns with examples", "EXAMPLE", "medium", 6)
        ));
        
        // Chapter 2: Lines and Angles
        TEST_QUERIES.put("geometry", Arrays.asList(
            new TestQuery("What is an angle?", "LEARN_CONCEPT", "easy", 6),
            new TestQuery("How to measure angles using a protractor?", "HOW_TO", "medium", 6),
            new TestQuery("What are the types of angles?", "LIST", "easy", 6),
            new TestQuery("Difference between acute and obtuse angles", "COMPARE", "medium", 6)
        ));
        
        // Chapter 3: Number Play
        TEST_QUERIES.put("numbers", Arrays.asList(
            new TestQuery("What are whole numbers?", "LEARN_CONCEPT", "easy", 6),
            new TestQuery("How to arrange numbers in ascending order?", "HOW_TO", "easy", 6),
            new TestQuery("Find the largest 4-digit number", "SOLVE_PROBLEM", "medium", 6),
            new TestQuery("Explain the concept of place value", "LEARN_CONCEPT", "medium", 6)
        ));
        
        // Chapter 5: Prime Time
        TEST_QUERIES.put("prime_numbers", Arrays.asList(
            new TestQuery("What are prime numbers?", "LEARN_CONCEPT", "easy", 6),
            new TestQuery("How to check if a number is prime?", "HOW_TO", "medium", 6),
            new TestQuery("List all prime numbers between 1 and 20", "LIST", "medium", 6),
            new TestQuery("What is the difference between prime and composite numbers?", "COMPARE", "medium", 6)
        ));
        
        // Chapter 6: Perimeter and Area
        TEST_QUERIES.put("measurement", Arrays.asList(
            new TestQuery("What is perimeter?", "LEARN_CONCEPT", "easy", 6),
            new TestQuery("How to calculate the area of a rectangle?", "HOW_TO", "medium", 6),
            new TestQuery("Find the perimeter of a square with side 5 cm", "SOLVE_PROBLEM", "easy", 6),
            new TestQuery("Compare area and perimeter of different shapes", "COMPARE", "hard", 6)
        ));
        
        // Chapter 7: Fractions
        TEST_QUERIES.put("fractions", Arrays.asList(
            new TestQuery("What are fractions?", "LEARN_CONCEPT", "easy", 6),
            new TestQuery("How to add fractions with same denominator?", "HOW_TO", "medium", 6),
            new TestQuery("Add 1/4 + 2/4", "SOLVE_PROBLEM", "easy", 6),
            new TestQuery("What is the difference between proper and improper fractions?", "COMPARE", "medium", 6),
            new TestQuery("Give examples of equivalent fractions", "EXAMPLE", "medium", 6)
        ));
        
        // Chapter 9: Symmetry
        TEST_QUERIES.put("symmetry", Arrays.asList(
            new TestQuery("What is symmetry?", "LEARN_CONCEPT", "easy", 6),
            new TestQuery("How to identify lines of symmetry?", "HOW_TO", "medium", 6),
            new TestQuery("Give examples of symmetric shapes", "EXAMPLE", "medium", 6)
        ));
        
        // Chapter 10: The Other Side of Zero (Integers)
        TEST_QUERIES.put("integers", Arrays.asList(
            new TestQuery("What are negative numbers?", "LEARN_CONCEPT", "easy", 6),
            new TestQuery("How to add positive and negative numbers?", "HOW_TO", "medium", 6),
            new TestQuery("Arrange these integers in order: -3, 5, -1, 0, 2", "SOLVE_PROBLEM", "medium", 6)
        ));
        
        // Mixed complexity queries
        TEST_QUERIES.put("mixed", Arrays.asList(
            new TestQuery("Solve this fraction problem: If you eat 2/8 of a pizza and your friend eats 3/8, how much pizza is left?", "SOLVE_PROBLEM", "hard", 6),
            new TestQuery("Explain how patterns help in understanding mathematics", "LEARN_CONCEPT", "hard", 6),
            new TestQuery("What is the relationship between area and perimeter?", "COMPARE", "hard", 6)
        ));
    }
    
    /**
     * Run comprehensive RAG system test
     */
    public CompletableFuture<Map<String, Object>> runComprehensiveTest() {
        return CompletableFuture.supplyAsync(() -> {
            try {
                log.info("Starting comprehensive RAG system test for Standard 6 Mathematics");
                
                Map<String, Object> testResults = new HashMap<>();
                testResults.put("test_started_at", System.currentTimeMillis());
                testResults.put("test_type", "comprehensive_rag_system");
                testResults.put("target_subject", "mathematics");
                testResults.put("target_standard", 6);
                
                // Test different components
                Map<String, Object> componentResults = new HashMap<>();
                
                // 1. Test Query Router
                componentResults.put("query_router", testQueryRouter());
                
                // 2. Test Educational Intent Provider
                componentResults.put("intent_provider", testIntentProvider());
                
                // 3. Test Hybrid Retriever
                componentResults.put("hybrid_retriever", testHybridRetriever());
                
                // 4. Test Cache Performance
                if (cacheService != null) {
                    componentResults.put("cache_system", testCacheSystem());
                }
                
                // 5. Run end-to-end integration tests
                componentResults.put("end_to_end", runEndToEndTests());
                
                testResults.put("component_results", componentResults);
                
                // Calculate overall performance metrics
                Map<String, Object> overallMetrics = calculateOverallMetrics(componentResults);
                testResults.put("overall_performance", overallMetrics);
                
                testResults.put("test_completed_at", System.currentTimeMillis());
                
                log.info("Comprehensive RAG system test completed");
                
                return testResults;
                
            } catch (Exception e) {
                log.error("Error in comprehensive RAG system test", e);
                return Map.of(
                    "status", "error",
                    "error_message", e.getMessage()
                );
            }
        });
    }
    
    /**
     * Test Query Router component
     */
    private Map<String, Object> testQueryRouter() {
        log.info("Testing MasterQueryRouter component");
        
        Map<String, Object> results = new HashMap<>();
        List<String> testQueries = getAllTestQueries();
        
        int totalQueries = testQueries.size();
        int correctRouting = 0;
        int educationalDetected = 0;
        double totalConfidence = 0.0;
        long totalResponseTime = 0;
        
        List<Map<String, Object>> queryResults = new ArrayList<>();
        
        for (String query : testQueries) {
            try {
                long startTime = System.currentTimeMillis();
                
                MasterQueryRouter.QueryRoutingResult routingResult = queryRouter.routeQuery(query, new HashMap<>());
                
                long responseTime = System.currentTimeMillis() - startTime;
                totalResponseTime += responseTime;
                
                Map<String, Object> queryResult = new HashMap<>();
                queryResult.put("query", query);
                queryResult.put("is_educational", routingResult.isEducational());
                queryResult.put("target_subject", routingResult.getTargetSubject());
                queryResult.put("confidence", routingResult.getConfidence());
                queryResult.put("response_time_ms", responseTime);
                
                if (routingResult.isEducational()) {
                    educationalDetected++;
                    totalConfidence += routingResult.getConfidence();
                    
                    // Check if routed to mathematics (all our test queries should be)
                    if ("mathematics".equals(routingResult.getTargetSubject())) {
                        correctRouting++;
                    }
                }
                
                queryResults.add(queryResult);
                
            } catch (Exception e) {
                log.error("Error testing query routing for: {}", query, e);
                queryResults.add(Map.of(
                    "query", query,
                    "error", e.getMessage()
                ));
            }
        }
        
        results.put("total_queries", totalQueries);
        results.put("educational_detected", educationalDetected);
        results.put("correct_math_routing", correctRouting);
        results.put("routing_accuracy", totalQueries > 0 ? (correctRouting * 100.0 / totalQueries) : 0.0);
        results.put("educational_detection_rate", totalQueries > 0 ? (educationalDetected * 100.0 / totalQueries) : 0.0);
        results.put("average_confidence", educationalDetected > 0 ? (totalConfidence / educationalDetected) : 0.0);
        results.put("average_response_time_ms", totalQueries > 0 ? (totalResponseTime / totalQueries) : 0);
        results.put("query_results", queryResults);
        
        // Performance targets
        results.put("meets_routing_accuracy_target", (correctRouting * 100.0 / totalQueries) >= 95.0);
        results.put("meets_response_time_target", (totalResponseTime / totalQueries) <= 100);
        
        return results;
    }
    
    /**
     * Test Educational Intent Provider component
     */
    private Map<String, Object> testIntentProvider() {
        log.info("Testing EducationalIntentProvider component");
        
        Map<String, Object> results = new HashMap<>();
        List<TestQuery> allTestQueries = getAllDetailedTestQueries();
        
        int totalQueries = allTestQueries.size();
        int correctIntentDetection = 0;
        int correctComplexityDetection = 0;
        int correctGradeLevelDetection = 0;
        double totalConfidence = 0.0;
        
        Map<String, Integer> intentAccuracy = new HashMap<>();
        
        for (TestQuery testQuery : allTestQueries) {
            try {
                EducationalIntentProvider.EducationalIntentResult intentResult = intentProvider.analyzeQuery(
                    testQuery.getQuery(), new HashMap<>()
                );
                
                if (intentResult.isEducational()) {
                    totalConfidence += intentResult.getConfidence();
                    
                    // Check intent accuracy
                    if (testQuery.getExpectedIntent().equals(intentResult.getPrimaryIntent())) {
                        correctIntentDetection++;
                    }
                    
                    // Check complexity accuracy
                    if (testQuery.getExpectedComplexity().equals(intentResult.getComplexityLevel())) {
                        correctComplexityDetection++;
                    }
                    
                    // Check grade level accuracy (allow ±1 grade variance)
                    int gradeDiff = Math.abs(testQuery.getExpectedGradeLevel() - intentResult.getGradeLevel());
                    if (gradeDiff <= 1) {
                        correctGradeLevelDetection++;
                    }
                    
                    // Track per-intent accuracy
                    String intent = testQuery.getExpectedIntent();
                    intentAccuracy.put(intent, intentAccuracy.getOrDefault(intent, 0) + 1);
                }
                
            } catch (Exception e) {
                log.error("Error testing intent for: {}", testQuery.getQuery(), e);
            }
        }
        
        results.put("total_queries", totalQueries);
        results.put("intent_detection_accuracy", totalQueries > 0 ? (correctIntentDetection * 100.0 / totalQueries) : 0.0);
        results.put("complexity_detection_accuracy", totalQueries > 0 ? (correctComplexityDetection * 100.0 / totalQueries) : 0.0);
        results.put("grade_level_accuracy", totalQueries > 0 ? (correctGradeLevelDetection * 100.0 / totalQueries) : 0.0);
        results.put("average_confidence", totalQueries > 0 ? (totalConfidence / totalQueries) : 0.0);
        results.put("intent_distribution", intentAccuracy);
        
        // Performance targets
        results.put("meets_intent_accuracy_target", (correctIntentDetection * 100.0 / totalQueries) >= 90.0);
        results.put("meets_confidence_target", (totalConfidence / totalQueries) >= 0.8);
        
        return results;
    }
    
    /**
     * Test Hybrid Retriever component
     */
    private Map<String, Object> testHybridRetriever() {
        log.info("Testing HybridRetriever component");
        
        Map<String, Object> results = new HashMap<>();
        List<String> testQueries = Arrays.asList(
            "What are fractions?",
            "How to add fractions?",
            "What is the area of a rectangle?",
            "Explain prime numbers",
            "What are patterns in mathematics?"
        );
        
        int totalQueries = testQueries.size();
        int successfulRetrievals = 0;
        long totalResponseTime = 0;
        double totalAverageScore = 0.0;
        
        List<Map<String, Object>> retrievalResults = new ArrayList<>();
        
        for (String query : testQueries) {
            try {
                long startTime = System.currentTimeMillis();
                
                HybridRetriever.HybridSearchRequest request = new HybridRetriever.HybridSearchRequest();
                request.setQuery(query);
                request.setSubject("mathematics");
                request.setStandard(6);
                request.setLimit(5);
                
                List<HybridRetriever.HybridSearchResult> searchResults = hybridRetriever.hybridSearch(request).join();
                
                long responseTime = System.currentTimeMillis() - startTime;
                totalResponseTime += responseTime;
                
                Map<String, Object> retrievalResult = new HashMap<>();
                retrievalResult.put("query", query);
                retrievalResult.put("results_found", searchResults.size());
                retrievalResult.put("response_time_ms", responseTime);
                
                if (!searchResults.isEmpty()) {
                    successfulRetrievals++;
                    
                    double averageScore = searchResults.stream()
                        .mapToDouble(HybridRetriever.HybridSearchResult::getFinalScore)
                        .average().orElse(0.0);
                    
                    totalAverageScore += averageScore;
                    retrievalResult.put("average_score", averageScore);
                    retrievalResult.put("highest_score", searchResults.get(0).getFinalScore());
                }
                
                retrievalResults.add(retrievalResult);
                
            } catch (Exception e) {
                log.error("Error testing hybrid retrieval for: {}", query, e);
                retrievalResults.add(Map.of(
                    "query", query,
                    "error", e.getMessage()
                ));
            }
        }
        
        results.put("total_queries", totalQueries);
        results.put("successful_retrievals", successfulRetrievals);
        results.put("retrieval_success_rate", totalQueries > 0 ? (successfulRetrievals * 100.0 / totalQueries) : 0.0);
        results.put("average_response_time_ms", totalQueries > 0 ? (totalResponseTime / totalQueries) : 0);
        results.put("average_relevance_score", successfulRetrievals > 0 ? (totalAverageScore / successfulRetrievals) : 0.0);
        results.put("retrieval_results", retrievalResults);
        
        // Performance targets
        results.put("meets_success_rate_target", (successfulRetrievals * 100.0 / totalQueries) >= 90.0);
        results.put("meets_response_time_target", (totalResponseTime / totalQueries) <= 500);
        results.put("meets_relevance_target", (totalAverageScore / successfulRetrievals) >= 0.7);
        
        return results;
    }
    
    /**
     * Test Cache System performance
     */
    private Map<String, Object> testCacheSystem() {
        log.info("Testing RagCacheService component");
        
        Map<String, Object> results = new HashMap<>();
        
        try {
            // Get current cache metrics
            Map<String, Object> metrics = cacheService.getCacheMetrics();
            
            // Test cache operations
            String testQuery = "What are fractions for testing?";
            List<Map<String, Object>> testResults = Arrays.asList(
                Map.of("content", "Test fraction content", "score", 0.9),
                Map.of("content", "Another test content", "score", 0.8)
            );
            
            // Cache the test results
            cacheService.cacheSearchResults(testQuery, "mathematics", 6, testResults);
            
            // Try to retrieve from cache
            Optional<List<Map<String, Object>>> cachedResults = cacheService.getCachedSearchResults(
                testQuery, "mathematics", 6
            );
            
            results.put("cache_available", metrics.get("redis_available"));
            results.put("current_hit_rate", metrics.get("hit_rate"));
            results.put("cache_test_successful", cachedResults.isPresent());
            results.put("popular_queries_count", cacheService.getPopularQueries(10).size());
            
            // Clean up test data
            cacheService.invalidateCache("testing");
            
        } catch (Exception e) {
            log.error("Error testing cache system", e);
            results.put("cache_available", false);
            results.put("error", e.getMessage());
        }
        
        return results;
    }
    
    /**
     * Run end-to-end integration tests
     */
    private Map<String, Object> runEndToEndTests() {
        log.info("Running end-to-end RAG system integration tests");
        
        Map<String, Object> results = new HashMap<>();
        
        // Test full pipeline with representative queries
        List<String> e2eTestQueries = Arrays.asList(
            "What are fractions and how do you add them?",
            "How to find the area of a rectangle step by step?",
            "Explain prime numbers with examples",
            "What is the difference between perimeter and area?"
        );
        
        int totalTests = e2eTestQueries.size();
        int passedTests = 0;
        long totalProcessingTime = 0;
        
        List<Map<String, Object>> e2eResults = new ArrayList<>();
        
        for (String query : e2eTestQueries) {
            try {
                long startTime = System.currentTimeMillis();
                
                // Step 1: Query Routing
                MasterQueryRouter.QueryRoutingResult routingResult = queryRouter.routeQuery(query, new HashMap<>());
                
                // Step 2: Intent Analysis
                EducationalIntentProvider.EducationalIntentResult intentResult = intentProvider.analyzeQuery(
                    query, new HashMap<>()
                );
                
                // Step 3: Content Retrieval
                HybridRetriever.HybridSearchRequest searchRequest = new HybridRetriever.HybridSearchRequest();
                searchRequest.setQuery(query);
                searchRequest.setSubject("mathematics");
                searchRequest.setStandard(6);
                searchRequest.setLimit(3);
                
                List<HybridRetriever.HybridSearchResult> searchResults = hybridRetriever.hybridSearch(searchRequest).join();
                
                long processingTime = System.currentTimeMillis() - startTime;
                totalProcessingTime += processingTime;
                
                // Evaluate end-to-end success
                boolean testPassed = routingResult.isEducational() && 
                                   "mathematics".equals(routingResult.getTargetSubject()) &&
                                   intentResult.isEducational() &&
                                   routingResult.getConfidence() > 0.5 &&
                                   processingTime < 1000; // 1 second max
                
                if (testPassed) {
                    passedTests++;
                }
                
                Map<String, Object> e2eResult = new HashMap<>();
                e2eResult.put("query", query);
                e2eResult.put("test_passed", testPassed);
                e2eResult.put("processing_time_ms", processingTime);
                e2eResult.put("routing_success", routingResult.isEducational());
                e2eResult.put("intent_success", intentResult.isEducational());
                e2eResult.put("retrieval_results_count", searchResults.size());
                e2eResult.put("overall_confidence", routingResult.getConfidence());
                
                e2eResults.add(e2eResult);
                
            } catch (Exception e) {
                log.error("Error in end-to-end test for query: {}", query, e);
                e2eResults.add(Map.of(
                    "query", query,
                    "test_passed", false,
                    "error", e.getMessage()
                ));
            }
        }
        
        results.put("total_tests", totalTests);
        results.put("passed_tests", passedTests);
        results.put("success_rate", totalTests > 0 ? (passedTests * 100.0 / totalTests) : 0.0);
        results.put("average_processing_time_ms", totalTests > 0 ? (totalProcessingTime / totalTests) : 0);
        results.put("e2e_results", e2eResults);
        
        // Performance targets
        results.put("meets_success_rate_target", (passedTests * 100.0 / totalTests) >= 90.0);
        results.put("meets_processing_time_target", (totalProcessingTime / totalTests) <= 500);
        
        return results;
    }
    
    /**
     * Calculate overall performance metrics
     */
    private Map<String, Object> calculateOverallMetrics(Map<String, Object> componentResults) {
        Map<String, Object> overallMetrics = new HashMap<>();
        
        // Calculate weighted scores
        double routerScore = calculateComponentScore((Map<String, Object>) componentResults.get("query_router"));
        double intentScore = calculateComponentScore((Map<String, Object>) componentResults.get("intent_provider"));
        double retrieverScore = calculateComponentScore((Map<String, Object>) componentResults.get("hybrid_retriever"));
        double e2eScore = calculateComponentScore((Map<String, Object>) componentResults.get("end_to_end"));
        
        double overallScore = (routerScore * 0.25) + (intentScore * 0.25) + (retrieverScore * 0.25) + (e2eScore * 0.25);
        
        overallMetrics.put("overall_score", overallScore);
        overallMetrics.put("component_scores", Map.of(
            "query_router", routerScore,
            "intent_provider", intentScore,
            "hybrid_retriever", retrieverScore,
            "end_to_end", e2eScore
        ));
        
        overallMetrics.put("system_ready_for_production", overallScore >= 85.0);
        overallMetrics.put("quality_target_achieved", overallScore >= 90.0);
        
        return overallMetrics;
    }
    
    /**
     * Calculate score for individual component
     */
    private double calculateComponentScore(Map<String, Object> componentResult) {
        if (componentResult == null) return 0.0;
        
        double score = 0.0;
        int criteria = 0;
        
        // Check various performance metrics
        if (componentResult.containsKey("routing_accuracy")) {
            score += ((Number) componentResult.get("routing_accuracy")).doubleValue();
            criteria++;
        }
        
        if (componentResult.containsKey("intent_detection_accuracy")) {
            score += ((Number) componentResult.get("intent_detection_accuracy")).doubleValue();
            criteria++;
        }
        
        if (componentResult.containsKey("retrieval_success_rate")) {
            score += ((Number) componentResult.get("retrieval_success_rate")).doubleValue();
            criteria++;
        }
        
        if (componentResult.containsKey("success_rate")) {
            score += ((Number) componentResult.get("success_rate")).doubleValue();
            criteria++;
        }
        
        return criteria > 0 ? score / criteria : 0.0;
    }
    
    /**
     * Get all test queries as strings
     */
    private List<String> getAllTestQueries() {
        return TEST_QUERIES.values().stream()
            .flatMap(List::stream)
            .map(TestQuery::getQuery)
            .toList();
    }
    
    /**
     * Get all detailed test queries
     */
    private List<TestQuery> getAllDetailedTestQueries() {
        return TEST_QUERIES.values().stream()
            .flatMap(List::stream)
            .toList();
    }
    
    // Test query data class
    private static class TestQuery {
        private final String query;
        private final String expectedIntent;
        private final String expectedComplexity;
        private final int expectedGradeLevel;
        
        public TestQuery(String query, String expectedIntent, String expectedComplexity, int expectedGradeLevel) {
            this.query = query;
            this.expectedIntent = expectedIntent;
            this.expectedComplexity = expectedComplexity;
            this.expectedGradeLevel = expectedGradeLevel;
        }
        
        public String getQuery() { return query; }
        public String getExpectedIntent() { return expectedIntent; }
        public String getExpectedComplexity() { return expectedComplexity; }
        public int getExpectedGradeLevel() { return expectedGradeLevel; }
    }
}