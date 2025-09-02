package xiaozhi.modules.rag.controller;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import xiaozhi.common.utils.Result;
import xiaozhi.modules.rag.service.QualityValidationService;

import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.CompletableFuture;

/**
 * Quality Validation Controller
 * REST API endpoints for RAG system quality validation and accuracy metrics
 * 
 * @author Claude
 * @since 1.0.0
 */
@Slf4j
@RestController
@RequestMapping("/api/rag/quality")
public class QualityValidationController {
    
    @Autowired
    private QualityValidationService qualityValidationService;
    
    /**
     * Run comprehensive quality validation for RAG system
     * 
     * @return Complete quality validation results with metrics and recommendations
     */
    @PostMapping("/validate")
    public ResponseEntity<Result<Map<String, Object>>> validateSystemQuality() {
        try {
            log.info("Starting comprehensive RAG system quality validation");
            
            // Run quality validation
            CompletableFuture<QualityValidationService.ValidationResult> validationFuture = 
                qualityValidationService.validateSystemQuality();
            
            QualityValidationService.ValidationResult validationResult = validationFuture.join();
            
            // Prepare response
            Map<String, Object> responseData = new HashMap<>();
            responseData.put("validation_id", "quality_" + System.currentTimeMillis());
            responseData.put("validation_started_at", validationResult.getValidationStartTime());
            responseData.put("validation_completed_at", validationResult.getValidationEndTime());
            responseData.put("validation_duration_ms", 
                validationResult.getValidationEndTime() - validationResult.getValidationStartTime());
            
            // Overall results
            responseData.put("overall_quality_score", validationResult.getOverallQualityScore());
            responseData.put("passed_validation", validationResult.isPassedValidation());
            responseData.put("production_ready", validationResult.getOverallQualityScore() >= 85.0);
            
            // Detailed metrics
            if (validationResult.getQualityMetrics() != null) {
                Map<String, Object> detailedMetrics = new HashMap<>();
                
                validationResult.getQualityMetrics().forEach((component, metrics) -> {
                    Map<String, Object> componentMetrics = new HashMap<>();
                    componentMetrics.put("score", metrics.getScore());
                    componentMetrics.put("target", metrics.getTarget());
                    componentMetrics.put("passed", metrics.isMetsPassed());
                    componentMetrics.put("details", metrics.getDetails());
                    
                    detailedMetrics.put(component, componentMetrics);
                });
                
                responseData.put("quality_metrics", detailedMetrics);
            }
            
            // Recommendations
            responseData.put("recommendations", validationResult.getRecommendations());
            
            // Quality standards reference
            Map<String, Object> qualityStandards = new HashMap<>();
            qualityStandards.put("response_accuracy_target", 92.0);
            qualityStandards.put("educational_appropriateness_target", 90.0);
            qualityStandards.put("source_attribution_target", 95.0);
            qualityStandards.put("curriculum_alignment_target", 100.0);
            qualityStandards.put("max_response_time_ms", 500);
            responseData.put("quality_standards", qualityStandards);
            
            // Error handling
            if (validationResult.getErrorMessage() != null) {
                responseData.put("error_message", validationResult.getErrorMessage());
            }
            
            Result<Map<String, Object>> result = new Result<>();
            result.setData(responseData);
            result.setMsg(validationResult.isPassedValidation() ? 
                "Quality validation passed - system ready for production" : 
                "Quality validation completed with issues - see recommendations");
            
            log.info("Quality validation completed - Overall score: {}, Passed: {}", 
                validationResult.getOverallQualityScore(), validationResult.isPassedValidation());
            
            return ResponseEntity.ok(result);
            
        } catch (Exception e) {
            log.error("Error running quality validation", e);
            
            Result<Map<String, Object>> result = new Result<>();
            result.setCode(500);
            result.setMsg("Internal server error during quality validation");
            result.setData(Map.of("error", e.getMessage()));
            
            return ResponseEntity.internalServerError().body(result);
        }
    }
    
    /**
     * Get quality validation standards and criteria
     * 
     * @return Quality standards used for RAG system validation
     */
    @GetMapping("/standards")
    public ResponseEntity<Result<Map<String, Object>>> getQualityStandards() {
        try {
            log.info("Retrieving RAG system quality standards");
            
            Map<String, Object> standards = new HashMap<>();
            
            // Response accuracy standards
            standards.put("response_accuracy", Map.of(
                "minimum_score", 0.92,
                "target_percentage", 92.0,
                "evaluation_criteria", java.util.Arrays.asList(
                    "Mathematical correctness",
                    "Concept coverage completeness",
                    "Answer relevance to query",
                    "Factual accuracy verification"
                )
            ));
            
            // Educational appropriateness standards
            standards.put("educational_appropriateness", Map.of(
                "minimum_score", 0.90,
                "target_percentage", 90.0,
                "age_group", "Standard 6 (Ages 11-12)",
                "evaluation_criteria", java.util.Arrays.asList(
                    "Age-appropriate vocabulary",
                    "Sentence complexity suitable for grade level",
                    "Content difficulty appropriate for Standard 6",
                    "No inappropriate or confusing concepts"
                )
            ));
            
            // Source attribution standards
            standards.put("source_attribution", Map.of(
                "minimum_score", 0.95,
                "target_percentage", 95.0,
                "evaluation_criteria", java.util.Arrays.asList(
                    "Correct NCERT textbook attribution",
                    "Accurate chapter references",
                    "Page number citations when available",
                    "Proper educational source identification"
                )
            ));
            
            // Curriculum alignment standards
            standards.put("curriculum_alignment", Map.of(
                "minimum_score", 1.0,
                "target_percentage", 100.0,
                "curriculum_source", "NCERT Standard 6 Mathematics Textbook",
                "evaluation_criteria", java.util.Arrays.asList(
                    "Content matches NCERT syllabus",
                    "Concepts appropriate for Standard 6",
                    "Learning objectives alignment",
                    "No content beyond curriculum scope"
                )
            ));
            
            // Performance standards
            standards.put("performance", Map.of(
                "max_response_time_ms", 500,
                "target_score", 0.8,
                "evaluation_criteria", java.util.Arrays.asList(
                    "Query processing speed",
                    "Content retrieval efficiency",
                    "Overall system responsiveness",
                    "Concurrent user support capability"
                )
            ));
            
            // Overall quality thresholds
            standards.put("overall_quality", Map.of(
                "minimum_passing_score", 85.0,
                "production_ready_score", 90.0,
                "excellent_quality_score", 95.0,
                "scoring_weights", Map.of(
                    "response_accuracy", 0.30,
                    "educational_appropriateness", 0.25,
                    "source_attribution", 0.20,
                    "curriculum_alignment", 0.15,
                    "performance", 0.10
                )
            ));
            
            Map<String, Object> responseData = new HashMap<>();
            responseData.put("quality_standards", standards);
            responseData.put("validation_framework", "Comprehensive Educational RAG Validation");
            responseData.put("target_subject", "Mathematics");
            responseData.put("target_standard", 6);
            responseData.put("standards_version", "1.0.0");
            responseData.put("last_updated", System.currentTimeMillis());
            
            Result<Map<String, Object>> result = new Result<>();
            result.setData(responseData);
            result.setMsg("Quality standards retrieved successfully");
            
            return ResponseEntity.ok(result);
            
        } catch (Exception e) {
            log.error("Error retrieving quality standards", e);
            
            Result<Map<String, Object>> result = new Result<>();
            result.setCode(500);
            result.setMsg("Internal server error retrieving quality standards");
            result.setData(Map.of("error", e.getMessage()));
            
            return ResponseEntity.internalServerError().body(result);
        }
    }
    
    /**
     * Get sample validation queries for manual testing
     * 
     * @return Sample queries with expected quality outcomes
     */
    @GetMapping("/sample-validation")
    public ResponseEntity<Result<Map<String, Object>>> getSampleValidationQueries() {
        try {
            log.info("Retrieving sample validation queries");
            
            Map<String, Object> sampleValidation = new HashMap<>();
            
            // High-quality response examples
            sampleValidation.put("high_quality_examples", java.util.Arrays.asList(
                Map.of(
                    "query", "What are fractions?",
                    "expected_chapter", "Chapter 7: Fractions",
                    "expected_concepts", java.util.Arrays.asList("fraction", "numerator", "denominator", "part", "whole"),
                    "expected_grade_level", 6,
                    "quality_criteria", "Should use simple language, provide clear examples, cite NCERT source"
                ),
                Map.of(
                    "query", "How to find the area of a rectangle?",
                    "expected_chapter", "Chapter 6: Perimeter and Area",
                    "expected_concepts", java.util.Arrays.asList("area", "rectangle", "length", "width", "formula"),
                    "expected_grade_level", 6,
                    "quality_criteria", "Should include step-by-step method, use appropriate vocabulary"
                )
            ));
            
            // Medium complexity examples
            sampleValidation.put("medium_complexity_examples", java.util.Arrays.asList(
                Map.of(
                    "query", "Compare prime and composite numbers",
                    "expected_chapter", "Chapter 5: Prime Time",
                    "expected_concepts", java.util.Arrays.asList("prime", "composite", "factors", "divisible"),
                    "expected_grade_level", 6,
                    "quality_criteria", "Should clearly distinguish concepts with examples"
                ),
                Map.of(
                    "query", "Explain symmetry with examples",
                    "expected_chapter", "Chapter 9: Symmetry",
                    "expected_concepts", java.util.Arrays.asList("symmetry", "line of symmetry", "reflection"),
                    "expected_grade_level", 6,
                    "quality_criteria", "Should include visual examples appropriate for grade 6"
                )
            ));
            
            // Edge case examples
            sampleValidation.put("edge_case_examples", java.util.Arrays.asList(
                Map.of(
                    "query", "What is calculus?",
                    "expected_response", "Not in Standard 6 curriculum",
                    "quality_criteria", "Should redirect to appropriate grade 6 content or indicate out of scope"
                ),
                Map.of(
                    "query", "Solve advanced algebraic equations",
                    "expected_response", "Simplified to Standard 6 level",
                    "quality_criteria", "Should simplify to age-appropriate problem solving"
                )
            ));
            
            // Quality validation checklist
            sampleValidation.put("validation_checklist", java.util.Arrays.asList(
                "Response uses vocabulary appropriate for 11-12 year olds",
                "Mathematical concepts are explained clearly and simply",
                "Examples are relevant and easy to understand",
                "Source attribution includes NCERT reference",
                "Content aligns with Standard 6 Mathematics curriculum",
                "No advanced concepts beyond grade level",
                "Response length is appropriate (not too long)",
                "Calculations and facts are mathematically correct",
                "Language is encouraging and supportive for learning"
            ));
            
            Map<String, Object> responseData = new HashMap<>();
            responseData.put("sample_validation", sampleValidation);
            responseData.put("validation_purpose", "Manual quality testing for educational appropriateness");
            responseData.put("target_audience", "Standard 6 Mathematics students");
            responseData.put("validation_scope", "NCERT curriculum alignment");
            
            Result<Map<String, Object>> result = new Result<>();
            result.setData(responseData);
            result.setMsg("Sample validation queries retrieved successfully");
            
            return ResponseEntity.ok(result);
            
        } catch (Exception e) {
            log.error("Error retrieving sample validation queries", e);
            
            Result<Map<String, Object>> result = new Result<>();
            result.setCode(500);
            result.setMsg("Internal server error retrieving sample validation");
            result.setData(Map.of("error", e.getMessage()));
            
            return ResponseEntity.internalServerError().body(result);
        }
    }
    
    /**
     * Health check for quality validation service
     * 
     * @return Quality validation service health status
     */
    @GetMapping("/health")
    public ResponseEntity<Result<Map<String, Object>>> getQualityValidationHealth() {
        try {
            Map<String, Object> healthData = new HashMap<>();
            healthData.put("service", "Quality Validation Service");
            healthData.put("status", "healthy");
            healthData.put("timestamp", System.currentTimeMillis());
            healthData.put("version", "1.0.0");
            
            // Test validation service availability
            boolean validationServiceHealthy = qualityValidationService != null;
            healthData.put("validation_service_available", validationServiceHealthy);
            
            if (validationServiceHealthy) {
                healthData.put("ready_for_quality_validation", true);
                healthData.put("supported_validation_types", java.util.Arrays.asList(
                    "response_accuracy", "educational_appropriateness", 
                    "source_attribution", "curriculum_alignment", "performance"
                ));
            }
            
            Result<Map<String, Object>> result = new Result<>();
            result.setData(healthData);
            result.setMsg("Quality validation service is healthy");
            
            return ResponseEntity.ok(result);
            
        } catch (Exception e) {
            log.error("Error checking quality validation health", e);
            
            Result<Map<String, Object>> result = new Result<>();
            result.setCode(500);
            result.setMsg("Quality validation health check failed");
            result.setData(Map.of(
                "status", "unhealthy",
                "error", e.getMessage()
            ));
            
            return ResponseEntity.internalServerError().body(result);
        }
    }
}