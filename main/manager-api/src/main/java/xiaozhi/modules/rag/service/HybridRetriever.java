package xiaozhi.modules.rag.service;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import xiaozhi.modules.rag.entity.RagContentChunkEntity;
import xiaozhi.modules.rag.dao.RagContentChunkDao;

import java.util.*;
import java.util.concurrent.CompletableFuture;
import java.util.stream.Collectors;

/**
 * Hybrid Retriever for Semantic + Keyword Search
 * Combines vector similarity search with keyword matching and cross-encoder reranking
 * 
 * @author Claude
 * @since 1.0.0
 */
@Slf4j
@Service
public class HybridRetriever {
    
    @Autowired
    private QdrantService qdrantService;
    
    @Autowired
    private EmbeddingService embeddingService;
    
    @Autowired
    private RagContentChunkDao contentChunkDao;
    
    // Configuration constants
    private static final double SEMANTIC_WEIGHT = 0.7;
    private static final double KEYWORD_WEIGHT = 0.3;
    private static final double MIN_CONFIDENCE_THRESHOLD = 0.6;
    private static final int MAX_SEMANTIC_RESULTS = 20;
    private static final int MAX_KEYWORD_RESULTS = 10;
    private static final int MAX_FINAL_RESULTS = 5;
    
    // Keyword boosting factors
    private static final Map<String, Double> KEYWORD_BOOST_FACTORS = Map.of(
        "exact_match", 2.0,
        "stem_match", 1.5,
        "partial_match", 1.2,
        "synonym_match", 1.1
    );
    
    /**
     * Perform hybrid search combining semantic and keyword approaches
     */
    public CompletableFuture<List<HybridSearchResult>> hybridSearch(HybridSearchRequest request) {
        return CompletableFuture.supplyAsync(() -> {
            try {
                log.info("Performing hybrid search for query: {}", request.getQuery());
                
                // Step 1: Semantic search using vector embeddings
                CompletableFuture<List<SemanticResult>> semanticFuture = performSemanticSearch(request);
                
                // Step 2: Keyword-based search
                CompletableFuture<List<KeywordResult>> keywordFuture = performKeywordSearch(request);
                
                // Step 3: Wait for both searches to complete
                List<SemanticResult> semanticResults = semanticFuture.join();
                List<KeywordResult> keywordResults = keywordFuture.join();
                
                log.debug("Retrieved {} semantic results and {} keyword results", 
                    semanticResults.size(), keywordResults.size());
                
                // Step 4: Merge and score results
                List<HybridSearchResult> mergedResults = mergeResults(
                    request, semanticResults, keywordResults);
                
                // Step 5: Apply cross-encoder reranking
                List<HybridSearchResult> rerankedResults = applyReranking(
                    request.getQuery(), mergedResults);
                
                // Step 6: Apply final filtering and limit
                List<HybridSearchResult> finalResults = applyFinalFiltering(
                    rerankedResults, request);
                
                log.info("Hybrid search completed - {} final results for query: {}", 
                    finalResults.size(), request.getQuery());
                
                return finalResults;
                
            } catch (Exception e) {
                log.error("Error in hybrid search for query: {}", request.getQuery(), e);
                return Collections.emptyList();
            }
        });
    }
    
    /**
     * Perform semantic search using vector embeddings
     */
    private CompletableFuture<List<SemanticResult>> performSemanticSearch(HybridSearchRequest request) {
        return CompletableFuture.supplyAsync(() -> {
            try {
                log.debug("Performing semantic search for: {}", request.getQuery());
                
                // Generate query embedding
                List<Float> queryEmbedding = embeddingService.generateEmbedding(request.getQuery()).join();
                
                // Prepare search filters
                Map<String, Object> filters = new HashMap<>();
                if (request.getSubject() != null) {
                    filters.put("subject", request.getSubject());
                }
                if (request.getStandard() != null) {
                    filters.put("standard", request.getStandard());
                }
                if (request.getContentTypes() != null && !request.getContentTypes().isEmpty()) {
                    filters.put("content_type", request.getContentTypes());
                }
                if (request.getDifficultyLevels() != null && !request.getDifficultyLevels().isEmpty()) {
                    filters.put("difficulty_level", request.getDifficultyLevels());
                }
                
                // Perform vector search
                List<Map<String, Object>> vectorResults = qdrantService.searchVectors(
                    getCollectionName(request.getSubject(), request.getStandard()),
                    queryEmbedding,
                    MAX_SEMANTIC_RESULTS,
                    0.5, // minimum similarity score
                    filters
                ).join();
                
                // Convert to semantic results
                return vectorResults.stream()
                    .map(result -> new SemanticResult(
                        (String) result.get("chunk_id"),
                        ((Number) result.get("score")).doubleValue(),
                        (String) result.get("content"),
                        (Map<String, Object>) result.get("metadata")
                    ))
                    .collect(Collectors.toList());
                    
            } catch (Exception e) {
                log.error("Error in semantic search", e);
                return Collections.emptyList();
            }
        });
    }
    
    /**
     * Perform keyword-based search
     */
    private CompletableFuture<List<KeywordResult>> performKeywordSearch(HybridSearchRequest request) {
        return CompletableFuture.supplyAsync(() -> {
            try {
                log.debug("Performing keyword search for: {}", request.getQuery());
                
                // Extract keywords from query
                List<String> keywords = extractKeywords(request.getQuery());
                
                // Build database query conditions
                Map<String, Object> searchConditions = new HashMap<>();
                searchConditions.put("keywords", keywords);
                
                if (request.getSubject() != null) {
                    searchConditions.put("subject", request.getSubject());
                }
                if (request.getStandard() != null) {
                    searchConditions.put("standard", request.getStandard());
                }
                
                // Perform keyword search in database
                List<RagContentChunkEntity> dbResults = contentChunkDao.searchByKeywords(
                    searchConditions, MAX_KEYWORD_RESULTS);
                
                // Score keyword matches
                List<KeywordResult> keywordResults = dbResults.stream()
                    .map(chunk -> {
                        double keywordScore = calculateKeywordScore(
                            request.getQuery(), keywords, chunk);
                        
                        return new KeywordResult(
                            chunk.getChunkId(),
                            keywordScore,
                            chunk.getChunkText(),
                            createMetadataMap(chunk)
                        );
                    })
                    .filter(result -> result.getScore() > 0.1) // Filter out very low scores
                    .sorted((a, b) -> Double.compare(b.getScore(), a.getScore()))
                    .collect(Collectors.toList());
                
                return keywordResults;
                    
            } catch (Exception e) {
                log.error("Error in keyword search", e);
                return Collections.emptyList();
            }
        });
    }
    
    /**
     * Merge semantic and keyword results with hybrid scoring
     */
    private List<HybridSearchResult> mergeResults(HybridSearchRequest request,
                                                  List<SemanticResult> semanticResults,
                                                  List<KeywordResult> keywordResults) {
        
        Map<String, HybridSearchResult> resultMap = new HashMap<>();
        
        // Add semantic results
        for (SemanticResult semantic : semanticResults) {
            HybridSearchResult hybrid = new HybridSearchResult(
                semantic.getChunkId(),
                semantic.getContent(),
                semantic.getMetadata()
            );
            hybrid.setSemanticScore(semantic.getScore());
            hybrid.setKeywordScore(0.0);
            resultMap.put(semantic.getChunkId(), hybrid);
        }
        
        // Add or enhance with keyword results
        for (KeywordResult keyword : keywordResults) {
            HybridSearchResult existing = resultMap.get(keyword.getChunkId());
            if (existing != null) {
                // Enhance existing result
                existing.setKeywordScore(keyword.getScore());
            } else {
                // Add new result
                HybridSearchResult hybrid = new HybridSearchResult(
                    keyword.getChunkId(),
                    keyword.getContent(),
                    keyword.getMetadata()
                );
                hybrid.setSemanticScore(0.0);
                hybrid.setKeywordScore(keyword.getScore());
                resultMap.put(keyword.getChunkId(), hybrid);
            }
        }
        
        // Calculate hybrid scores
        for (HybridSearchResult result : resultMap.values()) {
            double hybridScore = (result.getSemanticScore() * SEMANTIC_WEIGHT) + 
                               (result.getKeywordScore() * KEYWORD_WEIGHT);
            result.setHybridScore(hybridScore);
        }
        
        // Return sorted by hybrid score
        return resultMap.values().stream()
            .filter(result -> result.getHybridScore() > MIN_CONFIDENCE_THRESHOLD)
            .sorted((a, b) -> Double.compare(b.getHybridScore(), a.getHybridScore()))
            .collect(Collectors.toList());
    }
    
    /**
     * Apply cross-encoder reranking for final relevance scoring
     */
    private List<HybridSearchResult> applyReranking(String query, List<HybridSearchResult> results) {
        try {
            log.debug("Applying reranking for {} results", results.size());
            
            // For now, implement a simple reranking based on content relevance
            // In production, this would use a cross-encoder model
            
            for (HybridSearchResult result : results) {
                double rerankingScore = calculateRerankingScore(query, result.getContent());
                result.setRerankingScore(rerankingScore);
                
                // Combine hybrid score with reranking score
                double finalScore = (result.getHybridScore() * 0.7) + (rerankingScore * 0.3);
                result.setFinalScore(finalScore);
            }
            
            return results.stream()
                .sorted((a, b) -> Double.compare(b.getFinalScore(), a.getFinalScore()))
                .collect(Collectors.toList());
                
        } catch (Exception e) {
            log.error("Error in reranking", e);
            // Fall back to hybrid score only
            results.forEach(result -> result.setFinalScore(result.getHybridScore()));
            return results;
        }
    }
    
    /**
     * Apply final filtering and result limiting
     */
    private List<HybridSearchResult> applyFinalFiltering(List<HybridSearchResult> results,
                                                        HybridSearchRequest request) {
        
        return results.stream()
            .filter(result -> result.getFinalScore() > MIN_CONFIDENCE_THRESHOLD)
            .limit(request.getLimit() != null ? request.getLimit() : MAX_FINAL_RESULTS)
            .collect(Collectors.toList());
    }
    
    /**
     * Extract meaningful keywords from query
     */
    private List<String> extractKeywords(String query) {
        // Simple keyword extraction - in production, use NLP libraries
        return Arrays.stream(query.toLowerCase()
            .replaceAll("[^a-z0-9\\s]", "")
            .split("\\s+"))
            .filter(word -> word.length() > 2)
            .filter(word -> !isStopWord(word))
            .collect(Collectors.toList());
    }
    
    /**
     * Calculate keyword matching score
     */
    private double calculateKeywordScore(String query, List<String> keywords, RagContentChunkEntity chunk) {
        String content = chunk.getChunkText().toLowerCase();
        String title = chunk.getSectionTitle() != null ? chunk.getSectionTitle().toLowerCase() : "";
        
        double score = 0.0;
        
        for (String keyword : keywords) {
            // Exact match in title (highest weight)
            if (title.contains(keyword)) {
                score += KEYWORD_BOOST_FACTORS.get("exact_match") * 2.0;
            }
            
            // Exact match in content
            if (content.contains(keyword)) {
                score += KEYWORD_BOOST_FACTORS.get("exact_match");
            }
            
            // Count frequency
            long frequency = content.split(keyword, -1).length - 1;
            score += frequency * 0.1;
        }
        
        // Normalize by content length
        return score / Math.log(content.length() + 1);
    }
    
    /**
     * Calculate reranking score based on content relevance
     */
    private double calculateRerankingScore(String query, String content) {
        // Simple relevance scoring - in production, use cross-encoder model
        String queryLower = query.toLowerCase();
        String contentLower = content.toLowerCase();
        
        double score = 0.0;
        
        // Query words present in content
        String[] queryWords = queryLower.split("\\s+");
        for (String word : queryWords) {
            if (contentLower.contains(word)) {
                score += 1.0;
            }
        }
        
        // Normalize by query length
        return score / queryWords.length;
    }
    
    /**
     * Create metadata map from entity
     */
    private Map<String, Object> createMetadataMap(RagContentChunkEntity chunk) {
        Map<String, Object> metadata = new HashMap<>();
        metadata.put("chunk_id", chunk.getChunkId());
        metadata.put("textbook_id", chunk.getTextbookId());
        // Note: Subject and standard are stored in the related textbook metadata
        // For now, we'll leave these as null and fetch them from the textbook entity if needed
        metadata.put("subject", null);  // TODO: Fetch from textbook metadata
        metadata.put("standard", null); // TODO: Fetch from textbook metadata
        metadata.put("chapter", null);  // TODO: Implement chapter extraction
        metadata.put("content_type", chunk.getContentType());
        metadata.put("difficulty_level", chunk.getDifficultyLevel());
        metadata.put("title", chunk.getSectionTitle());
        metadata.put("page_number", chunk.getPageNumber());
        return metadata;
    }
    
    /**
     * Get collection name for vector search
     */
    private String getCollectionName(String subject, Integer standard) {
        if (subject != null && standard != null) {
            return String.format("%s_std%d_%s", "math", standard, subject);
        }
        return "math_std6_mathematics"; // Default collection
    }
    
    /**
     * Check if word is a stop word
     */
    private boolean isStopWord(String word) {
        Set<String> stopWords = Set.of(
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", 
            "of", "with", "by", "is", "are", "was", "were", "be", "been", "have", 
            "has", "had", "do", "does", "did", "will", "would", "could", "should"
        );
        return stopWords.contains(word);
    }
    
    /**
     * Get hybrid search statistics
     */
    public Map<String, Object> getSearchStatistics() {
        Map<String, Object> stats = new HashMap<>();
        stats.put("semantic_weight", SEMANTIC_WEIGHT);
        stats.put("keyword_weight", KEYWORD_WEIGHT);
        stats.put("confidence_threshold", MIN_CONFIDENCE_THRESHOLD);
        stats.put("max_semantic_results", MAX_SEMANTIC_RESULTS);
        stats.put("max_keyword_results", MAX_KEYWORD_RESULTS);
        stats.put("max_final_results", MAX_FINAL_RESULTS);
        stats.put("supported_boost_factors", KEYWORD_BOOST_FACTORS);
        return stats;
    }
    
    // Data classes
    
    public static class HybridSearchRequest {
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
    
    public static class HybridSearchResult {
        private String chunkId;
        private String content;
        private Map<String, Object> metadata;
        private double semanticScore = 0.0;
        private double keywordScore = 0.0;
        private double hybridScore = 0.0;
        private double rerankingScore = 0.0;
        private double finalScore = 0.0;
        
        public HybridSearchResult(String chunkId, String content, Map<String, Object> metadata) {
            this.chunkId = chunkId;
            this.content = content;
            this.metadata = metadata;
        }
        
        // Getters and setters
        public String getChunkId() { return chunkId; }
        public String getContent() { return content; }
        public Map<String, Object> getMetadata() { return metadata; }
        public double getSemanticScore() { return semanticScore; }
        public void setSemanticScore(double semanticScore) { this.semanticScore = semanticScore; }
        public double getKeywordScore() { return keywordScore; }
        public void setKeywordScore(double keywordScore) { this.keywordScore = keywordScore; }
        public double getHybridScore() { return hybridScore; }
        public void setHybridScore(double hybridScore) { this.hybridScore = hybridScore; }
        public double getRerankingScore() { return rerankingScore; }
        public void setRerankingScore(double rerankingScore) { this.rerankingScore = rerankingScore; }
        public double getFinalScore() { return finalScore; }
        public void setFinalScore(double finalScore) { this.finalScore = finalScore; }
    }
    
    private static class SemanticResult {
        private final String chunkId;
        private final double score;
        private final String content;
        private final Map<String, Object> metadata;
        
        public SemanticResult(String chunkId, double score, String content, Map<String, Object> metadata) {
            this.chunkId = chunkId;
            this.score = score;
            this.content = content;
            this.metadata = metadata;
        }
        
        public String getChunkId() { return chunkId; }
        public double getScore() { return score; }
        public String getContent() { return content; }
        public Map<String, Object> getMetadata() { return metadata; }
    }
    
    private static class KeywordResult {
        private final String chunkId;
        private final double score;
        private final String content;
        private final Map<String, Object> metadata;
        
        public KeywordResult(String chunkId, double score, String content, Map<String, Object> metadata) {
            this.chunkId = chunkId;
            this.score = score;
            this.content = content;
            this.metadata = metadata;
        }
        
        public String getChunkId() { return chunkId; }
        public double getScore() { return score; }
        public String getContent() { return content; }
        public Map<String, Object> getMetadata() { return metadata; }
    }
}