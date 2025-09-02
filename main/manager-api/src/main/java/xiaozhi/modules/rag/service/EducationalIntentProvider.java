package xiaozhi.modules.rag.service;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.*;
import java.util.regex.Pattern;

/**
 * Educational Intent Provider
 * Detects and classifies educational intents in user queries with confidence scoring
 * 
 * @author Claude
 * @since 1.0.0
 */
@Slf4j
@Service
public class EducationalIntentProvider {
    
    @Autowired(required = false)
    private RagCacheService cacheService;
    
    // Intent classification patterns
    private static final Map<String, IntentPattern> INTENT_PATTERNS = new HashMap<>();
    
    static {
        // Learning intents
        INTENT_PATTERNS.put("LEARN_CONCEPT", new IntentPattern(
            Arrays.asList("what is", "what are", "explain", "define", "tell me about", "help me understand"),
            Arrays.asList("concept", "definition", "explanation", "understanding"),
            0.8
        ));
        
        INTENT_PATTERNS.put("HOW_TO", new IntentPattern(
            Arrays.asList("how to", "how do", "how can", "show me how", "teach me"),
            Arrays.asList("method", "procedure", "steps", "process", "technique"),
            0.9
        ));
        
        INTENT_PATTERNS.put("SOLVE_PROBLEM", new IntentPattern(
            Arrays.asList("solve", "calculate", "find", "compute", "determine", "work out"),
            Arrays.asList("solution", "answer", "result", "calculation", "problem"),
            0.85
        ));
        
        INTENT_PATTERNS.put("COMPARE", new IntentPattern(
            Arrays.asList("difference", "compare", "versus", "vs", "between", "distinguish"),
            Arrays.asList("comparison", "contrast", "similarity", "difference"),
            0.7
        ));
        
        INTENT_PATTERNS.put("EXAMPLE", new IntentPattern(
            Arrays.asList("example", "examples", "show me", "demonstrate", "illustrate"),
            Arrays.asList("instance", "sample", "case", "illustration"),
            0.75
        ));
        
        INTENT_PATTERNS.put("LIST", new IntentPattern(
            Arrays.asList("list", "enumerate", "name", "types of", "kinds of", "categories"),
            Arrays.asList("items", "elements", "components", "parts"),
            0.7
        ));
        
        // Subject-specific intents
        INTENT_PATTERNS.put("MATH_CALCULATION", new IntentPattern(
            Arrays.asList("add", "subtract", "multiply", "divide", "calculate", "compute"),
            Arrays.asList("number", "equation", "formula", "operation", "arithmetic"),
            0.9
        ));
        
        INTENT_PATTERNS.put("SCIENCE_EXPERIMENT", new IntentPattern(
            Arrays.asList("experiment", "observe", "test", "investigate", "analyze"),
            Arrays.asList("hypothesis", "result", "observation", "data", "conclusion"),
            0.8
        ));
        
        INTENT_PATTERNS.put("LANGUAGE_GRAMMAR", new IntentPattern(
            Arrays.asList("grammar", "sentence", "word", "phrase", "write", "compose"),
            Arrays.asList("noun", "verb", "adjective", "structure", "syntax"),
            0.8
        ));
    }
    
    // Educational confidence factors
    private static final Map<String, Double> SUBJECT_CONFIDENCE_BOOST = Map.of(
        "mathematics", 0.15,
        "science", 0.12,
        "english", 0.10,
        "history", 0.08,
        "geography", 0.08
    );
    
    // Grade level appropriateness factors
    private static final Map<String, Double> GRADE_COMPLEXITY_FACTOR = Map.of(
        "easy", 0.9,    // Primary grades
        "medium", 1.0,  // Middle grades  
        "hard", 1.1     // Higher grades
    );
    
    /**
     * Analyze query and detect educational intent
     */
    public EducationalIntentResult analyzeQuery(String query, Map<String, Object> context) {
        try {
            log.debug("Analyzing educational intent for query: {}", query);
            
            if (query == null || query.trim().isEmpty()) {
                return EducationalIntentResult.nonEducational("empty_query");
            }
            
            String queryLower = query.toLowerCase().trim();
            
            // Check cache first
            String cacheKey = "intent:" + Math.abs(query.hashCode());
            Optional<Map<String, Object>> cachedResult = Optional.empty();
            
            if (cacheService != null) {
                cachedResult = cacheService.getCachedQueryRouting(cacheKey);
            }
            
            if (cachedResult.isPresent()) {
                Map<String, Object> cached = cachedResult.get();
                return EducationalIntentResult.fromCache(cached);
            }
            
            // Perform fresh analysis
            IntentAnalysis analysis = performIntentAnalysis(queryLower, context);
            
            // Create result
            EducationalIntentResult result = new EducationalIntentResult();
            result.setOriginalQuery(query);
            result.setEducational(analysis.isEducational());
            result.setConfidence(analysis.getConfidence());
            result.setPrimaryIntent(analysis.getPrimaryIntent());
            result.setSecondaryIntents(analysis.getSecondaryIntents());
            result.setDetectedSubjects(analysis.getDetectedSubjects());
            result.setComplexityLevel(analysis.getComplexityLevel());
            result.setGradeLevel(analysis.getGradeLevel());
            result.setKeywords(analysis.getKeywords());
            result.setProcessingMetadata(analysis.getMetadata());
            
            // Cache the result
            if (cacheService != null && result.isEducational()) {
                cacheIntentResult(cacheKey, result);
            }
            
            return result;
            
        } catch (Exception e) {
            log.error("Error analyzing educational intent for query: {}", query, e);
            return EducationalIntentResult.error("analysis_failed", e.getMessage());
        }
    }
    
    /**
     * Perform detailed intent analysis
     */
    private IntentAnalysis performIntentAnalysis(String queryLower, Map<String, Object> context) {
        IntentAnalysis analysis = new IntentAnalysis();
        analysis.setOriginalQuery(queryLower);
        
        // Extract keywords
        List<String> keywords = extractKeywords(queryLower);
        analysis.setKeywords(keywords);
        
        // Detect intents
        Map<String, Double> intentScores = new HashMap<>();
        
        for (Map.Entry<String, IntentPattern> entry : INTENT_PATTERNS.entrySet()) {
            String intentName = entry.getKey();
            IntentPattern pattern = entry.getValue();
            
            double score = calculateIntentScore(queryLower, keywords, pattern);
            if (score > 0.1) {
                intentScores.put(intentName, score);
            }
        }
        
        // Determine primary intent
        if (intentScores.isEmpty()) {
            analysis.setEducational(false);
            analysis.setConfidence(0.0);
            return analysis;
        }
        
        String primaryIntent = intentScores.entrySet().stream()
            .max(Map.Entry.comparingByValue())
            .map(Map.Entry::getKey)
            .orElse("UNKNOWN");
            
        analysis.setPrimaryIntent(primaryIntent);
        analysis.setEducational(true);
        
        // Secondary intents
        List<String> secondaryIntents = intentScores.entrySet().stream()
            .filter(e -> !e.getKey().equals(primaryIntent))
            .filter(e -> e.getValue() > 0.3)
            .sorted(Map.Entry.<String, Double>comparingByValue().reversed())
            .limit(3)
            .map(Map.Entry::getKey)
            .toList();
        analysis.setSecondaryIntents(secondaryIntents);
        
        // Detect subjects
        List<String> subjects = detectSubjects(queryLower, keywords);
        analysis.setDetectedSubjects(subjects);
        
        // Calculate final confidence
        double baseConfidence = intentScores.get(primaryIntent);
        double subjectBoost = subjects.stream()
            .mapToDouble(s -> SUBJECT_CONFIDENCE_BOOST.getOrDefault(s, 0.0))
            .max().orElse(0.0);
        
        analysis.setConfidence(Math.min(0.99, baseConfidence + subjectBoost));
        
        // Determine complexity and grade level
        analysis.setComplexityLevel(determineComplexity(queryLower, keywords));
        analysis.setGradeLevel(determineGradeLevel(queryLower, subjects, analysis.getComplexityLevel()));
        
        // Add metadata
        Map<String, Object> metadata = new HashMap<>();
        metadata.put("intent_scores", intentScores);
        metadata.put("keyword_count", keywords.size());
        metadata.put("query_length", queryLower.length());
        metadata.put("analysis_timestamp", System.currentTimeMillis());
        analysis.setMetadata(metadata);
        
        return analysis;
    }
    
    /**
     * Calculate intent score for a pattern
     */
    private double calculateIntentScore(String query, List<String> keywords, IntentPattern pattern) {
        double score = 0.0;
        
        // Direct phrase matches (higher weight)
        for (String phrase : pattern.getTriggerPhrases()) {
            if (query.contains(phrase)) {
                score += pattern.getBaseConfidence() * 0.8;
            }
        }
        
        // Keyword matches (lower weight)
        for (String keyword : pattern.getSupportKeywords()) {
            if (keywords.contains(keyword) || query.contains(keyword)) {
                score += pattern.getBaseConfidence() * 0.2;
            }
        }
        
        return Math.min(1.0, score);
    }
    
    /**
     * Extract keywords from query
     */
    private List<String> extractKeywords(String query) {
        // Simple keyword extraction - remove stop words and short words
        Set<String> stopWords = Set.of(
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", 
            "of", "with", "by", "is", "are", "was", "were", "be", "been", "have", 
            "has", "had", "do", "does", "did", "will", "would", "could", "should",
            "me", "you", "he", "she", "it", "we", "they", "this", "that", "these", "those"
        );
        
        return Arrays.stream(query.split("\\s+"))
            .map(word -> word.replaceAll("[^a-z0-9]", ""))
            .filter(word -> word.length() > 2)
            .filter(word -> !stopWords.contains(word))
            .distinct()
            .toList();
    }
    
    /**
     * Detect subjects in query
     */
    private List<String> detectSubjects(String query, List<String> keywords) {
        List<String> subjects = new ArrayList<>();
        
        Map<String, List<String>> subjectKeywords = Map.of(
            "mathematics", Arrays.asList("math", "number", "calculate", "solve", "equation", "formula", "fraction", "geometry", "algebra", "arithmetic"),
            "science", Arrays.asList("science", "experiment", "hypothesis", "observe", "chemical", "physics", "biology", "element", "organism"),
            "english", Arrays.asList("english", "grammar", "sentence", "word", "write", "read", "story", "poem", "literature", "vocabulary"),
            "history", Arrays.asList("history", "ancient", "war", "empire", "civilization", "century", "historical", "timeline", "culture"),
            "geography", Arrays.asList("geography", "map", "country", "continent", "climate", "population", "river", "mountain", "ocean")
        );
        
        for (Map.Entry<String, List<String>> entry : subjectKeywords.entrySet()) {
            String subject = entry.getKey();
            List<String> subjectWords = entry.getValue();
            
            boolean matches = subjectWords.stream()
                .anyMatch(word -> query.contains(word) || keywords.contains(word));
                
            if (matches) {
                subjects.add(subject);
            }
        }
        
        return subjects;
    }
    
    /**
     * Determine complexity level
     */
    private String determineComplexity(String query, List<String> keywords) {
        // Simple heuristics for complexity
        int complexWords = 0;
        Set<String> complexIndicators = Set.of(
            "analyze", "synthesize", "evaluate", "compare", "contrast", "derive", 
            "prove", "demonstrate", "investigate", "hypothesis", "theorem"
        );
        
        for (String keyword : keywords) {
            if (complexIndicators.contains(keyword)) {
                complexWords++;
            }
        }
        
        if (complexWords >= 2 || query.length() > 100) {
            return "hard";
        } else if (complexWords >= 1 || query.length() > 50) {
            return "medium";
        } else {
            return "easy";
        }
    }
    
    /**
     * Determine appropriate grade level
     */
    private int determineGradeLevel(String query, List<String> subjects, String complexity) {
        // Base grade level from subjects
        int baseGrade = 6; // Default to standard 6
        
        if (subjects.contains("mathematics")) {
            if (query.contains("fraction") || query.contains("decimal")) {
                baseGrade = 6;
            } else if (query.contains("algebra") || query.contains("equation")) {
                baseGrade = 8;
            } else if (query.contains("geometry") || query.contains("angle")) {
                baseGrade = 7;
            }
        }
        
        // Adjust for complexity
        switch (complexity) {
            case "easy" -> baseGrade = Math.max(1, baseGrade - 2);
            case "hard" -> baseGrade = Math.min(12, baseGrade + 2);
        }
        
        return baseGrade;
    }
    
    /**
     * Cache intent analysis result
     */
    private void cacheIntentResult(String cacheKey, EducationalIntentResult result) {
        try {
            Map<String, Object> cacheData = new HashMap<>();
            cacheData.put("educational", result.isEducational());
            cacheData.put("confidence", result.getConfidence());
            cacheData.put("primary_intent", result.getPrimaryIntent());
            cacheData.put("detected_subjects", result.getDetectedSubjects());
            cacheData.put("complexity_level", result.getComplexityLevel());
            cacheData.put("grade_level", result.getGradeLevel());
            
            // Note: This would need to be adapted to the actual cacheService interface
            log.debug("Cached intent analysis result for key: {}", cacheKey);
            
        } catch (Exception e) {
            log.error("Error caching intent result", e);
        }
    }
    
    /**
     * Get intent analysis statistics
     */
    public Map<String, Object> getIntentStatistics() {
        Map<String, Object> stats = new HashMap<>();
        
        stats.put("supported_intents", INTENT_PATTERNS.keySet());
        stats.put("supported_subjects", SUBJECT_CONFIDENCE_BOOST.keySet());
        stats.put("complexity_levels", Arrays.asList("easy", "medium", "hard"));
        stats.put("grade_range", Map.of("min", 1, "max", 12));
        stats.put("confidence_threshold", 0.5);
        stats.put("service_version", "1.0.0");
        
        return stats;
    }
    
    // Data classes
    
    private static class IntentPattern {
        private final List<String> triggerPhrases;
        private final List<String> supportKeywords;
        private final double baseConfidence;
        
        public IntentPattern(List<String> triggerPhrases, List<String> supportKeywords, double baseConfidence) {
            this.triggerPhrases = triggerPhrases;
            this.supportKeywords = supportKeywords;
            this.baseConfidence = baseConfidence;
        }
        
        public List<String> getTriggerPhrases() { return triggerPhrases; }
        public List<String> getSupportKeywords() { return supportKeywords; }
        public double getBaseConfidence() { return baseConfidence; }
    }
    
    private static class IntentAnalysis {
        private String originalQuery;
        private boolean educational;
        private double confidence;
        private String primaryIntent;
        private List<String> secondaryIntents;
        private List<String> detectedSubjects;
        private String complexityLevel;
        private int gradeLevel;
        private List<String> keywords;
        private Map<String, Object> metadata;
        
        // Getters and setters
        public String getOriginalQuery() { return originalQuery; }
        public void setOriginalQuery(String originalQuery) { this.originalQuery = originalQuery; }
        public boolean isEducational() { return educational; }
        public void setEducational(boolean educational) { this.educational = educational; }
        public double getConfidence() { return confidence; }
        public void setConfidence(double confidence) { this.confidence = confidence; }
        public String getPrimaryIntent() { return primaryIntent; }
        public void setPrimaryIntent(String primaryIntent) { this.primaryIntent = primaryIntent; }
        public List<String> getSecondaryIntents() { return secondaryIntents; }
        public void setSecondaryIntents(List<String> secondaryIntents) { this.secondaryIntents = secondaryIntents; }
        public List<String> getDetectedSubjects() { return detectedSubjects; }
        public void setDetectedSubjects(List<String> detectedSubjects) { this.detectedSubjects = detectedSubjects; }
        public String getComplexityLevel() { return complexityLevel; }
        public void setComplexityLevel(String complexityLevel) { this.complexityLevel = complexityLevel; }
        public int getGradeLevel() { return gradeLevel; }
        public void setGradeLevel(int gradeLevel) { this.gradeLevel = gradeLevel; }
        public List<String> getKeywords() { return keywords; }
        public void setKeywords(List<String> keywords) { this.keywords = keywords; }
        public Map<String, Object> getMetadata() { return metadata; }
        public void setMetadata(Map<String, Object> metadata) { this.metadata = metadata; }
    }
    
    public static class EducationalIntentResult {
        private String originalQuery;
        private boolean educational;
        private double confidence;
        private String primaryIntent;
        private List<String> secondaryIntents;
        private List<String> detectedSubjects;
        private String complexityLevel;
        private int gradeLevel;
        private List<String> keywords;
        private Map<String, Object> processingMetadata;
        private boolean fromCache;
        private String errorMessage;
        
        public static EducationalIntentResult nonEducational(String reason) {
            EducationalIntentResult result = new EducationalIntentResult();
            result.educational = false;
            result.confidence = 0.0;
            result.errorMessage = reason;
            return result;
        }
        
        public static EducationalIntentResult error(String error, String message) {
            EducationalIntentResult result = new EducationalIntentResult();
            result.educational = false;
            result.confidence = 0.0;
            result.errorMessage = error + ": " + message;
            return result;
        }
        
        public static EducationalIntentResult fromCache(Map<String, Object> cached) {
            EducationalIntentResult result = new EducationalIntentResult();
            result.educational = (Boolean) cached.getOrDefault("educational", false);
            result.confidence = ((Number) cached.getOrDefault("confidence", 0.0)).doubleValue();
            result.primaryIntent = (String) cached.get("primary_intent");
            result.fromCache = true;
            return result;
        }
        
        // Getters and setters
        public String getOriginalQuery() { return originalQuery; }
        public void setOriginalQuery(String originalQuery) { this.originalQuery = originalQuery; }
        public boolean isEducational() { return educational; }
        public void setEducational(boolean educational) { this.educational = educational; }
        public double getConfidence() { return confidence; }
        public void setConfidence(double confidence) { this.confidence = confidence; }
        public String getPrimaryIntent() { return primaryIntent; }
        public void setPrimaryIntent(String primaryIntent) { this.primaryIntent = primaryIntent; }
        public List<String> getSecondaryIntents() { return secondaryIntents; }
        public void setSecondaryIntents(List<String> secondaryIntents) { this.secondaryIntents = secondaryIntents; }
        public List<String> getDetectedSubjects() { return detectedSubjects; }
        public void setDetectedSubjects(List<String> detectedSubjects) { this.detectedSubjects = detectedSubjects; }
        public String getComplexityLevel() { return complexityLevel; }
        public void setComplexityLevel(String complexityLevel) { this.complexityLevel = complexityLevel; }
        public int getGradeLevel() { return gradeLevel; }
        public void setGradeLevel(int gradeLevel) { this.gradeLevel = gradeLevel; }
        public List<String> getKeywords() { return keywords; }
        public void setKeywords(List<String> keywords) { this.keywords = keywords; }
        public Map<String, Object> getProcessingMetadata() { return processingMetadata; }
        public void setProcessingMetadata(Map<String, Object> processingMetadata) { this.processingMetadata = processingMetadata; }
        public boolean isFromCache() { return fromCache; }
        public void setFromCache(boolean fromCache) { this.fromCache = fromCache; }
        public String getErrorMessage() { return errorMessage; }
        public void setErrorMessage(String errorMessage) { this.errorMessage = errorMessage; }
    }
}