package xiaozhi.modules.rag.service;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.util.*;
import java.util.concurrent.TimeUnit;

/**
 * RAG Cache Service for Railway Redis Integration
 * Implements intelligent caching strategy for educational query results
 * 
 * @author Claude
 * @since 1.0.0
 */
@Slf4j
@Service
public class RagCacheService {
    
    @Autowired(required = false)
    private RedisTemplate<String, Object> redisTemplate;
    
    private final ObjectMapper objectMapper = new ObjectMapper();
    
    // Cache configuration constants
    private static final String CACHE_PREFIX = "rag:";
    private static final String SEARCH_CACHE_PREFIX = CACHE_PREFIX + "search:";
    private static final String QUERY_STATS_PREFIX = CACHE_PREFIX + "stats:";
    private static final String POPULAR_QUERIES_KEY = CACHE_PREFIX + "popular";
    private static final String CACHE_METRICS_KEY = CACHE_PREFIX + "metrics";
    
    // Cache TTL settings (in seconds)
    private static final long SEARCH_RESULT_TTL = 3600; // 1 hour
    private static final long POPULAR_QUERY_TTL = 86400; // 24 hours
    private static final long STATS_TTL = 1800; // 30 minutes
    private static final long METRICS_TTL = 300; // 5 minutes
    
    // Performance thresholds
    private static final int MAX_CACHE_SIZE = 10000;
    private static final int POPULAR_QUERY_THRESHOLD = 5; // Minimum hits to be considered popular
    
    /**
     * Cache search results with intelligent TTL based on query type
     */
    public void cacheSearchResults(String query, String subject, Integer standard, 
                                 List<Map<String, Object>> results) {
        try {
            if (redisTemplate == null) {
                log.warn("Redis not available - skipping cache operation");
                return;
            }
            
            String cacheKey = generateSearchCacheKey(query, subject, standard);
            
            // Create cache entry with metadata
            Map<String, Object> cacheEntry = new HashMap<>();
            cacheEntry.put("query", query);
            cacheEntry.put("subject", subject);
            cacheEntry.put("standard", standard);
            cacheEntry.put("results", results);
            cacheEntry.put("cached_at", System.currentTimeMillis());
            cacheEntry.put("result_count", results.size());
            
            String jsonValue = objectMapper.writeValueAsString(cacheEntry);
            
            // Determine TTL based on query characteristics
            long ttl = calculateCacheTTL(query, results.size());
            
            redisTemplate.opsForValue().set(cacheKey, jsonValue, ttl, TimeUnit.SECONDS);
            
            // Update query statistics
            updateQueryStatistics(query, subject, standard);
            
            log.debug("Cached search results for query: {} with TTL: {} seconds", query, ttl);
            
        } catch (Exception e) {
            log.error("Error caching search results for query: {}", query, e);
        }
    }
    
    /**
     * Retrieve cached search results
     */
    public Optional<List<Map<String, Object>>> getCachedSearchResults(String query, String subject, Integer standard) {
        try {
            if (redisTemplate == null) {
                return Optional.empty();
            }
            
            String cacheKey = generateSearchCacheKey(query, subject, standard);
            String cachedValue = (String) redisTemplate.opsForValue().get(cacheKey);
            
            if (cachedValue != null) {
                @SuppressWarnings("unchecked")
                Map<String, Object> cacheEntry = objectMapper.readValue(cachedValue, Map.class);
                
                @SuppressWarnings("unchecked")
                List<Map<String, Object>> results = (List<Map<String, Object>>) cacheEntry.get("results");
                
                // Update cache hit metrics
                updateCacheMetrics("hit", query);
                
                log.debug("Cache hit for query: {}", query);
                return Optional.of(results);
            }
            
            // Update cache miss metrics
            updateCacheMetrics("miss", query);
            
            log.debug("Cache miss for query: {}", query);
            return Optional.empty();
            
        } catch (Exception e) {
            log.error("Error retrieving cached results for query: {}", query, e);
            return Optional.empty();
        }
    }
    
    /**
     * Cache query routing results
     */
    public void cacheQueryRouting(String query, String targetSubject, String queryType, double confidence) {
        try {
            if (redisTemplate == null) {
                return;
            }
            
            String cacheKey = CACHE_PREFIX + "routing:" + generateQueryHash(query);
            
            Map<String, Object> routingResult = new HashMap<>();
            routingResult.put("target_subject", targetSubject);
            routingResult.put("query_type", queryType);
            routingResult.put("confidence", confidence);
            routingResult.put("cached_at", System.currentTimeMillis());
            
            String jsonValue = objectMapper.writeValueAsString(routingResult);
            
            // Routing results cached for shorter time as they're lightweight
            redisTemplate.opsForValue().set(cacheKey, jsonValue, STATS_TTL, TimeUnit.SECONDS);
            
            log.debug("Cached routing result for query: {}", query);
            
        } catch (Exception e) {
            log.error("Error caching routing result for query: {}", query, e);
        }
    }
    
    /**
     * Get cached query routing results
     */
    public Optional<Map<String, Object>> getCachedQueryRouting(String query) {
        try {
            if (redisTemplate == null) {
                return Optional.empty();
            }
            
            String cacheKey = CACHE_PREFIX + "routing:" + generateQueryHash(query);
            String cachedValue = (String) redisTemplate.opsForValue().get(cacheKey);
            
            if (cachedValue != null) {
                @SuppressWarnings("unchecked")
                Map<String, Object> routingResult = objectMapper.readValue(cachedValue, Map.class);
                return Optional.of(routingResult);
            }
            
            return Optional.empty();
            
        } catch (Exception e) {
            log.error("Error retrieving cached routing result for query: {}", query, e);
            return Optional.empty();
        }
    }
    
    /**
     * Get popular queries for optimization
     */
    public List<String> getPopularQueries(int limit) {
        try {
            if (redisTemplate == null) {
                return Collections.emptyList();
            }
            
            Set<Object> popularQueriesObj = redisTemplate.opsForZSet()
                .reverseRange(POPULAR_QUERIES_KEY, 0, limit - 1);
            Set<String> popularQueries = popularQueriesObj != null ? 
                popularQueriesObj.stream().map(String::valueOf).collect(java.util.stream.Collectors.toSet()) : null;
            
            return popularQueries != null ? new ArrayList<>(popularQueries) : Collections.emptyList();
            
        } catch (Exception e) {
            log.error("Error retrieving popular queries", e);
            return Collections.emptyList();
        }
    }
    
    /**
     * Get cache performance metrics
     */
    public Map<String, Object> getCacheMetrics() {
        try {
            if (redisTemplate == null) {
                return Map.of("redis_available", false);
            }
            
            String metricsJson = (String) redisTemplate.opsForValue().get(CACHE_METRICS_KEY);
            
            if (metricsJson != null) {
                @SuppressWarnings("unchecked")
                Map<String, Object> metrics = objectMapper.readValue(metricsJson, Map.class);
                
                // Calculate cache hit rate
                long hits = ((Number) metrics.getOrDefault("hits", 0)).longValue();
                long misses = ((Number) metrics.getOrDefault("misses", 0)).longValue();
                long total = hits + misses;
                
                Map<String, Object> result = new HashMap<>(metrics);
                result.put("hit_rate", total > 0 ? (hits * 100.0 / total) : 0.0);
                result.put("total_requests", total);
                result.put("redis_available", true);
                
                return result;
            }
            
            return Map.of(
                "hits", 0,
                "misses", 0,
                "hit_rate", 0.0,
                "total_requests", 0,
                "redis_available", true
            );
            
        } catch (Exception e) {
            log.error("Error retrieving cache metrics", e);
            return Map.of("error", e.getMessage(), "redis_available", false);
        }
    }
    
    /**
     * Invalidate cache for specific query patterns
     */
    public void invalidateCache(String pattern) {
        try {
            if (redisTemplate == null) {
                return;
            }
            
            Set<String> keys = redisTemplate.keys(SEARCH_CACHE_PREFIX + pattern + "*");
            if (keys != null && !keys.isEmpty()) {
                redisTemplate.delete(keys);
                log.info("Invalidated {} cache entries matching pattern: {}", keys.size(), pattern);
            }
            
        } catch (Exception e) {
            log.error("Error invalidating cache for pattern: {}", pattern, e);
        }
    }
    
    /**
     * Clear all RAG cache entries
     */
    public void clearAllCache() {
        try {
            if (redisTemplate == null) {
                return;
            }
            
            Set<String> keys = redisTemplate.keys(CACHE_PREFIX + "*");
            if (keys != null && !keys.isEmpty()) {
                redisTemplate.delete(keys);
                log.info("Cleared {} RAG cache entries", keys.size());
            }
            
        } catch (Exception e) {
            log.error("Error clearing RAG cache", e);
        }
    }
    
    /**
     * Preload popular queries into cache
     */
    public void preloadPopularQueries() {
        try {
            List<String> popularQueries = getPopularQueries(50);
            log.info("Identified {} popular queries for preloading", popularQueries.size());
            
            // This would trigger background processing to warm up the cache
            // Implementation would depend on your specific RAG services
            
        } catch (Exception e) {
            log.error("Error preloading popular queries", e);
        }
    }
    
    // Private helper methods
    
    private String generateSearchCacheKey(String query, String subject, Integer standard) {
        String key = query.toLowerCase().trim();
        if (subject != null) {
            key += ":" + subject;
        }
        if (standard != null) {
            key += ":" + standard;
        }
        return SEARCH_CACHE_PREFIX + generateQueryHash(key);
    }
    
    private String generateQueryHash(String query) {
        // Simple hash - in production, use a proper hash function
        return String.valueOf(Math.abs(query.hashCode()));
    }
    
    private long calculateCacheTTL(String query, int resultCount) {
        // Educational queries with good results get longer TTL
        if (resultCount >= 3 && isEducationalQuery(query)) {
            return SEARCH_RESULT_TTL * 2; // 2 hours for good educational results
        }
        
        // Popular queries get longer TTL
        if (isPopularQuery(query)) {
            return SEARCH_RESULT_TTL * 3; // 3 hours for popular queries
        }
        
        // Standard TTL for other queries
        return SEARCH_RESULT_TTL;
    }
    
    private boolean isEducationalQuery(String query) {
        String queryLower = query.toLowerCase();
        return queryLower.contains("what") || queryLower.contains("how") || 
               queryLower.contains("explain") || queryLower.contains("math") ||
               queryLower.contains("calculate") || queryLower.contains("solve");
    }
    
    private boolean isPopularQuery(String query) {
        try {
            if (redisTemplate == null) {
                return false;
            }
            
            Double score = redisTemplate.opsForZSet().score(POPULAR_QUERIES_KEY, query);
            return score != null && score >= POPULAR_QUERY_THRESHOLD;
            
        } catch (Exception e) {
            return false;
        }
    }
    
    private void updateQueryStatistics(String query, String subject, Integer standard) {
        try {
            if (redisTemplate == null) {
                return;
            }
            
            // Update popular queries ranking
            redisTemplate.opsForZSet().incrementScore(POPULAR_QUERIES_KEY, query, 1);
            redisTemplate.expire(POPULAR_QUERIES_KEY, POPULAR_QUERY_TTL, TimeUnit.SECONDS);
            
            // Update subject-wise statistics
            if (subject != null) {
                String subjectStatsKey = QUERY_STATS_PREFIX + "subject:" + subject;
                redisTemplate.opsForZSet().incrementScore(subjectStatsKey, query, 1);
                redisTemplate.expire(subjectStatsKey, STATS_TTL, TimeUnit.SECONDS);
            }
            
        } catch (Exception e) {
            log.error("Error updating query statistics", e);
        }
    }
    
    private void updateCacheMetrics(String type, String query) {
        try {
            if (redisTemplate == null) {
                return;
            }
            
            String metricsJson = (String) redisTemplate.opsForValue().get(CACHE_METRICS_KEY);
            Map<String, Object> metrics = new HashMap<>();
            
            if (metricsJson != null) {
                @SuppressWarnings("unchecked")
                Map<String, Object> existingMetrics = objectMapper.readValue(metricsJson, Map.class);
                metrics.putAll(existingMetrics);
            }
            
            // Update metrics
            long currentValue = ((Number) metrics.getOrDefault(type + "s", 0)).longValue();
            metrics.put(type + "s", currentValue + 1);
            metrics.put("last_updated", System.currentTimeMillis());
            
            String updatedJson = objectMapper.writeValueAsString(metrics);
            redisTemplate.opsForValue().set(CACHE_METRICS_KEY, updatedJson, METRICS_TTL, TimeUnit.SECONDS);
            
        } catch (Exception e) {
            log.error("Error updating cache metrics", e);
        }
    }
}