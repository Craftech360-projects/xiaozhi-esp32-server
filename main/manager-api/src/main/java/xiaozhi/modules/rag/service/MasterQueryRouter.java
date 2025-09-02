package xiaozhi.modules.rag.service;

import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.*;
import java.util.regex.Pattern;

/**
 * Master Query Router for Educational Queries
 * Routes incoming queries to appropriate educational agents and services
 * 
 * @author Claude
 * @since 1.0.0
 */
@Slf4j
@Service
public class MasterQueryRouter {
    
    // Educational keywords by subject
    private static final Map<String, Set<String>> SUBJECT_KEYWORDS = Map.of(
        "mathematics", Set.of(
            "math", "number", "add", "subtract", "multiply", "divide", "fraction", "decimal", 
            "prime", "even", "odd", "area", "perimeter", "angle", "line", "shape", "geometry",
            "algebra", "equation", "formula", "calculate", "solve", "pattern", "ratio", 
            "proportion", "percentage", "graph", "chart", "data", "statistics", "symmetry",
            "integer", "whole", "natural", "counting", "measurement", "construction", "theorem"
        ),
        "science", Set.of(
            "science", "physics", "chemistry", "biology", "experiment", "lab", "element",
            "compound", "reaction", "cell", "organism", "energy", "force", "motion", "light",
            "sound", "heat", "electricity", "magnet", "planet", "solar", "ecosystem", "habitat"
        ),
        "english", Set.of(
            "english", "grammar", "noun", "verb", "adjective", "sentence", "paragraph", "essay",
            "story", "poem", "literature", "reading", "writing", "comprehension", "vocabulary",
            "spelling", "pronunciation", "tense", "punctuation", "composition"
        ),
        "history", Set.of(
            "history", "ancient", "medieval", "modern", "civilization", "empire", "kingdom",
            "ruler", "dynasty", "war", "battle", "culture", "tradition", "monument", "artifact",
            "timeline", "period", "century", "historical", "heritage"
        ),
        "geography", Set.of(
            "geography", "map", "continent", "country", "state", "city", "river", "mountain",
            "ocean", "sea", "climate", "weather", "population", "capital", "natural", "resource",
            "physical", "political", "economic", "agriculture", "industry"
        )
    );
    
    // Query type patterns
    private static final Map<String, Pattern> QUERY_PATTERNS = Map.of(
        "what_is", Pattern.compile("\\b(what\\s+is|what\\s+are|what\\s+does|what\\s+do)\\b", Pattern.CASE_INSENSITIVE),
        "how_to", Pattern.compile("\\b(how\\s+to|how\\s+do|how\\s+can|how\\s+does)\\b", Pattern.CASE_INSENSITIVE),
        "explain", Pattern.compile("\\b(explain|describe|define|tell\\s+me\\s+about)\\b", Pattern.CASE_INSENSITIVE),
        "solve", Pattern.compile("\\b(solve|calculate|find|compute|determine)\\b", Pattern.CASE_INSENSITIVE),
        "compare", Pattern.compile("\\b(compare|difference|between|versus|vs)\\b", Pattern.CASE_INSENSITIVE),
        "list", Pattern.compile("\\b(list|enumerate|name|types\\s+of|kinds\\s+of)\\b", Pattern.CASE_INSENSITIVE)
    );
    
    // Non-educational patterns (should be filtered out)
    private static final Set<Pattern> NON_EDUCATIONAL_PATTERNS = Set.of(
        Pattern.compile("\\b(weather|temperature|forecast|rain|sunny|cloudy)\\b", Pattern.CASE_INSENSITIVE),
        Pattern.compile("\\b(hello|hi|hey|good\\s+morning|good\\s+evening|how\\s+are\\s+you)\\b", Pattern.CASE_INSENSITIVE),
        Pattern.compile("\\b(news|current\\s+events|politics|election|government)\\b", Pattern.CASE_INSENSITIVE),
        Pattern.compile("\\b(sports|football|cricket|basketball|game|match)\\b", Pattern.CASE_INSENSITIVE),
        Pattern.compile("\\b(movie|film|entertainment|celebrity|actor|actress)\\b", Pattern.CASE_INSENSITIVE),
        Pattern.compile("\\b(food|recipe|cooking|restaurant|menu)\\b", Pattern.CASE_INSENSITIVE)
    );
    
    /**
     * Route educational query to appropriate handler
     */
    public QueryRoutingResult routeQuery(String query, Map<String, Object> context) {
        try {
            log.debug("Routing query: {}", query);
            
            // Analyze the query
            QueryAnalysis analysis = analyzeQuery(query);
            
            // Check if it's educational
            if (!analysis.isEducational()) {
                log.debug("Query identified as non-educational: {}", query);
                return QueryRoutingResult.nonEducational(query, analysis);
            }
            
            // Route to appropriate subject handler
            String targetSubject = analysis.getPrimarySubject();
            String queryType = analysis.getQueryType();
            
            log.info("Routing educational query to subject: {}, type: {}", targetSubject, queryType);
            
            // Create routing result
            QueryRoutingResult result = QueryRoutingResult.educational(
                query, 
                analysis,
                targetSubject,
                queryType,
                analysis.getConfidence()
            );
            
            // Add routing context
            Map<String, Object> routingContext = new HashMap<>();
            routingContext.put("original_context", context);
            routingContext.put("detected_keywords", analysis.getDetectedKeywords());
            routingContext.put("difficulty_estimate", estimateQueryDifficulty(query, analysis));
            routingContext.put("routing_timestamp", System.currentTimeMillis());
            
            result.setRoutingContext(routingContext);
            
            return result;
            
        } catch (Exception e) {
            log.error("Error routing query: {}", query, e);
            return QueryRoutingResult.error(query, e.getMessage());
        }
    }
    
    /**
     * Analyze query to determine subject, type, and educational relevance
     */
    private QueryAnalysis analyzeQuery(String query) {
        String queryLower = query.toLowerCase().trim();
        
        // Check if non-educational
        for (Pattern pattern : NON_EDUCATIONAL_PATTERNS) {
            if (pattern.matcher(queryLower).find()) {
                return QueryAnalysis.nonEducational(query, "matched_non_educational_pattern");
            }
        }
        
        // Analyze subjects
        Map<String, Integer> subjectScores = new HashMap<>();
        Map<String, Set<String>> detectedKeywords = new HashMap<>();
        
        for (Map.Entry<String, Set<String>> entry : SUBJECT_KEYWORDS.entrySet()) {
            String subject = entry.getKey();
            Set<String> keywords = entry.getValue();
            
            Set<String> foundKeywords = new HashSet<>();
            int score = 0;
            
            for (String keyword : keywords) {
                if (queryLower.contains(keyword)) {
                    score += keyword.length(); // Longer keywords get higher scores
                    foundKeywords.add(keyword);
                }
            }
            
            if (score > 0) {
                subjectScores.put(subject, score);
                detectedKeywords.put(subject, foundKeywords);
            }
        }
        
        // If no educational keywords found, check for generic educational patterns
        if (subjectScores.isEmpty()) {
            boolean hasEducationalIntent = QUERY_PATTERNS.values().stream()
                .anyMatch(pattern -> pattern.matcher(queryLower).find());
                
            if (!hasEducationalIntent) {
                return QueryAnalysis.nonEducational(query, "no_educational_keywords_or_patterns");
            }
            
            // Default to mathematics for generic educational queries
            subjectScores.put("mathematics", 1);
            detectedKeywords.put("mathematics", Set.of("generic_educational"));
        }
        
        // Find primary subject (highest score)
        String primarySubject = subjectScores.entrySet().stream()
            .max(Map.Entry.comparingByValue())
            .map(Map.Entry::getKey)
            .orElse("mathematics");
            
        // Determine query type
        String queryType = "general";
        for (Map.Entry<String, Pattern> entry : QUERY_PATTERNS.entrySet()) {
            if (entry.getValue().matcher(queryLower).find()) {
                queryType = entry.getKey();
                break;
            }
        }
        
        // Calculate confidence
        int maxScore = subjectScores.values().stream().mapToInt(Integer::intValue).max().orElse(0);
        double confidence = Math.min(0.95, 0.5 + (maxScore * 0.05)); // Scale confidence based on keyword matches
        
        return QueryAnalysis.educational(
            query,
            primarySubject,
            queryType,
            confidence,
            subjectScores,
            detectedKeywords
        );
    }
    
    /**
     * Estimate query difficulty level
     */
    private String estimateQueryDifficulty(String query, QueryAnalysis analysis) {
        String queryLower = query.toLowerCase();
        
        // Basic difficulty indicators
        if (queryLower.contains("basic") || queryLower.contains("simple") || 
            queryLower.contains("what is") || queryLower.contains("define")) {
            return "easy";
        }
        
        if (queryLower.contains("complex") || queryLower.contains("advanced") || 
            queryLower.contains("prove") || queryLower.contains("derive")) {
            return "hard";
        }
        
        // Mathematics-specific difficulty estimation
        if ("mathematics".equals(analysis.getPrimarySubject())) {
            if (queryLower.matches(".*\\b(add|subtract|basic|count|number)\\b.*")) {
                return "easy";
            }
            if (queryLower.matches(".*\\b(multiply|divide|fraction|decimal|area|perimeter)\\b.*")) {
                return "medium";
            }
            if (queryLower.matches(".*\\b(algebra|equation|theorem|proof|construction)\\b.*")) {
                return "hard";
            }
        }
        
        return "medium"; // Default
    }
    
    /**
     * Get routing statistics for monitoring
     */
    public Map<String, Object> getRoutingStatistics() {
        // This would be implemented with actual usage tracking
        Map<String, Object> stats = new HashMap<>();
        
        stats.put("supported_subjects", SUBJECT_KEYWORDS.keySet());
        stats.put("supported_query_types", QUERY_PATTERNS.keySet());
        stats.put("total_keywords", SUBJECT_KEYWORDS.values().stream()
            .mapToInt(Set::size).sum());
        stats.put("routing_accuracy_target", 0.95);
        
        // Simulated statistics for demonstration
        stats.put("queries_routed_today", 0);
        stats.put("educational_query_percentage", 0.0);
        stats.put("mathematics_query_percentage", 0.0);
        stats.put("average_confidence_score", 0.0);
        
        return stats;
    }
    
    /**
     * Query Analysis Result
     */
    public static class QueryAnalysis {
        private final String originalQuery;
        private final boolean educational;
        private final String primarySubject;
        private final String queryType;
        private final double confidence;
        private final Map<String, Integer> subjectScores;
        private final Map<String, Set<String>> detectedKeywords;
        private final String nonEducationalReason;
        
        private QueryAnalysis(String originalQuery, boolean educational, String primarySubject, 
                            String queryType, double confidence, Map<String, Integer> subjectScores,
                            Map<String, Set<String>> detectedKeywords, String nonEducationalReason) {
            this.originalQuery = originalQuery;
            this.educational = educational;
            this.primarySubject = primarySubject;
            this.queryType = queryType;
            this.confidence = confidence;
            this.subjectScores = subjectScores != null ? subjectScores : new HashMap<>();
            this.detectedKeywords = detectedKeywords != null ? detectedKeywords : new HashMap<>();
            this.nonEducationalReason = nonEducationalReason;
        }
        
        public static QueryAnalysis educational(String query, String subject, String type, 
                                              double confidence, Map<String, Integer> scores,
                                              Map<String, Set<String>> keywords) {
            return new QueryAnalysis(query, true, subject, type, confidence, scores, keywords, null);
        }
        
        public static QueryAnalysis nonEducational(String query, String reason) {
            return new QueryAnalysis(query, false, null, null, 0.0, null, null, reason);
        }
        
        // Getters
        public String getOriginalQuery() { return originalQuery; }
        public boolean isEducational() { return educational; }
        public String getPrimarySubject() { return primarySubject; }
        public String getQueryType() { return queryType; }
        public double getConfidence() { return confidence; }
        public Map<String, Integer> getSubjectScores() { return subjectScores; }
        public Map<String, Set<String>> getDetectedKeywords() { return detectedKeywords; }
        public String getNonEducationalReason() { return nonEducationalReason; }
    }
    
    /**
     * Query Routing Result
     */
    public static class QueryRoutingResult {
        private final String originalQuery;
        private final boolean educational;
        private final QueryAnalysis analysis;
        private final String targetSubject;
        private final String queryType;
        private final double confidence;
        private final String errorMessage;
        private Map<String, Object> routingContext;
        
        private QueryRoutingResult(String originalQuery, boolean educational, QueryAnalysis analysis,
                                 String targetSubject, String queryType, double confidence, String errorMessage) {
            this.originalQuery = originalQuery;
            this.educational = educational;
            this.analysis = analysis;
            this.targetSubject = targetSubject;
            this.queryType = queryType;
            this.confidence = confidence;
            this.errorMessage = errorMessage;
            this.routingContext = new HashMap<>();
        }
        
        public static QueryRoutingResult educational(String query, QueryAnalysis analysis, 
                                                   String subject, String type, double confidence) {
            return new QueryRoutingResult(query, true, analysis, subject, type, confidence, null);
        }
        
        public static QueryRoutingResult nonEducational(String query, QueryAnalysis analysis) {
            return new QueryRoutingResult(query, false, analysis, null, null, 0.0, null);
        }
        
        public static QueryRoutingResult error(String query, String error) {
            return new QueryRoutingResult(query, false, null, null, null, 0.0, error);
        }
        
        // Getters and setters
        public String getOriginalQuery() { return originalQuery; }
        public boolean isEducational() { return educational; }
        public QueryAnalysis getAnalysis() { return analysis; }
        public String getTargetSubject() { return targetSubject; }
        public String getQueryType() { return queryType; }
        public double getConfidence() { return confidence; }
        public String getErrorMessage() { return errorMessage; }
        public Map<String, Object> getRoutingContext() { return routingContext; }
        public void setRoutingContext(Map<String, Object> routingContext) { this.routingContext = routingContext; }
    }
}