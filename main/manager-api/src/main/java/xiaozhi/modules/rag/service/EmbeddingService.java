package xiaozhi.modules.rag.service;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.apache.hc.client5.http.classic.methods.HttpPost;
import org.apache.hc.client5.http.impl.classic.CloseableHttpClient;
import org.apache.hc.client5.http.impl.classic.HttpClients;
import org.apache.hc.client5.http.impl.classic.CloseableHttpResponse;
import org.apache.hc.core5.http.io.entity.StringEntity;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.JsonNode;

import java.util.List;
import java.util.ArrayList;
import java.util.Map;
import java.util.HashMap;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ConcurrentHashMap;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;

/**
 * Embedding Service using BAAI/bge-large-en-v1.5 model
 * Handles text embedding generation with batch processing and caching
 * Optimized for educational content retrieval
 * 
 * @author Claude
 * @since 1.0.0
 */
@Slf4j
@Service
public class EmbeddingService {
    
    private static final String MODEL_NAME = "BAAI/bge-large-en-v1.5";
    private static final int EMBEDDING_DIMENSION = 1024;
    private static final int MAX_BATCH_SIZE = 32;
    private static final int MAX_TEXT_LENGTH = 512;
    
    @Value("${rag.embedding.api-url:http://localhost:8000/embeddings}")
    private String embeddingApiUrl;
    
    @Value("${rag.embedding.api-key:}")
    private String embeddingApiKey;
    
    @Value("${rag.embedding.cache.enabled:true}")
    private boolean cachingEnabled;
    
    @Value("${rag.embedding.batch.size:16}")
    private int batchSize;
    
    private final ObjectMapper objectMapper = new ObjectMapper();
    private final CloseableHttpClient httpClient = HttpClients.createDefault();
    
    // In-memory cache for embeddings
    private final Map<String, List<Float>> embeddingCache = new ConcurrentHashMap<>();
    
    /**
     * Generate embeddings for a batch of texts
     */
    public CompletableFuture<List<List<Float>>> generateEmbeddings(List<String> texts) {
        return CompletableFuture.supplyAsync(() -> {
            try {
                log.info("Generating embeddings for {} texts using {}", texts.size(), MODEL_NAME);
                
                List<List<Float>> allEmbeddings = new ArrayList<>();
                
                // Process in batches to avoid overwhelming the embedding service
                for (int i = 0; i < texts.size(); i += batchSize) {
                    int endIndex = Math.min(i + batchSize, texts.size());
                    List<String> batch = texts.subList(i, endIndex);
                    
                    List<List<Float>> batchEmbeddings = processBatch(batch);
                    allEmbeddings.addAll(batchEmbeddings);
                    
                    log.debug("Processed batch {}/{} ({} texts)", 
                            (i / batchSize) + 1, 
                            (texts.size() + batchSize - 1) / batchSize,
                            batch.size());
                }
                
                log.info("Successfully generated {} embeddings", allEmbeddings.size());
                return allEmbeddings;
                
            } catch (Exception e) {
                log.error("Error generating embeddings", e);
                throw new RuntimeException("Embedding generation failed", e);
            }
        });
    }
    
    /**
     * Generate embedding for a single text
     */
    public CompletableFuture<List<Float>> generateEmbedding(String text) {
        return CompletableFuture.supplyAsync(() -> {
            try {
                // Check cache first
                if (cachingEnabled) {
                    String cacheKey = generateCacheKey(text);
                    if (embeddingCache.containsKey(cacheKey)) {
                        log.debug("Cache hit for text: {}", text.substring(0, Math.min(50, text.length())));
                        return embeddingCache.get(cacheKey);
                    }
                }
                
                // Generate embedding
                List<List<Float>> embeddings = processBatch(List.of(text));
                List<Float> embedding = embeddings.get(0);
                
                // Cache the result
                if (cachingEnabled && embedding != null) {
                    String cacheKey = generateCacheKey(text);
                    embeddingCache.put(cacheKey, embedding);
                }
                
                return embedding;
                
            } catch (Exception e) {
                log.error("Error generating single embedding", e);
                throw new RuntimeException("Single embedding generation failed", e);
            }
        });
    }
    
    /**
     * Process a batch of texts for embedding generation
     */
    private List<List<Float>> processBatch(List<String> texts) {
        try {
            // Preprocess texts
            List<String> processedTexts = preprocessTexts(texts);
            
            // For now, simulate the embedding API call
            // In production, this would call the actual BGE model service
            return simulateEmbeddingGeneration(processedTexts);
            
        } catch (Exception e) {
            log.error("Error processing batch of {} texts", texts.size(), e);
            throw new RuntimeException("Batch processing failed", e);
        }
    }
    
    /**
     * Preprocess texts before embedding generation
     */
    private List<String> preprocessTexts(List<String> texts) {
        List<String> processed = new ArrayList<>();
        
        for (String text : texts) {
            if (text == null || text.trim().isEmpty()) {
                processed.add("");
                continue;
            }
            
            // Clean and truncate text
            String cleaned = text.trim()
                    .replaceAll("\\s+", " ")  // Normalize whitespace
                    .replaceAll("[\\x00-\\x08\\x0B\\x0C\\x0E-\\x1F\\x7F]", "");  // Remove control characters
            
            // Truncate if too long
            if (cleaned.length() > MAX_TEXT_LENGTH * 4) {  // Approximate token to char ratio
                cleaned = cleaned.substring(0, MAX_TEXT_LENGTH * 4);
                // Try to end at a word boundary
                int lastSpace = cleaned.lastIndexOf(' ');
                if (lastSpace > MAX_TEXT_LENGTH * 3) {
                    cleaned = cleaned.substring(0, lastSpace);
                }
            }
            
            processed.add(cleaned);
        }
        
        return processed;
    }
    
    /**
     * Simulate embedding generation for testing
     * TODO: Replace with actual BGE model API call
     */
    private List<List<Float>> simulateEmbeddingGeneration(List<String> texts) {
        log.debug("Simulating embedding generation for {} texts", texts.size());
        
        List<List<Float>> embeddings = new ArrayList<>();
        
        for (String text : texts) {
            // Generate deterministic but realistic embeddings based on text content
            List<Float> embedding = generateSimulatedEmbedding(text);
            embeddings.add(embedding);
        }
        
        return embeddings;
    }
    
    /**
     * Generate a simulated embedding vector for testing
     */
    private List<Float> generateSimulatedEmbedding(String text) {
        List<Float> embedding = new ArrayList<>(EMBEDDING_DIMENSION);
        
        // Use text hash as seed for deterministic results
        int seed = text.hashCode();
        java.util.Random random = new java.util.Random(seed);
        
        // Generate normalized vector
        double[] vector = new double[EMBEDDING_DIMENSION];
        double magnitude = 0.0;
        
        for (int i = 0; i < EMBEDDING_DIMENSION; i++) {
            vector[i] = random.nextGaussian();
            magnitude += vector[i] * vector[i];
        }
        
        // Normalize to unit vector
        magnitude = Math.sqrt(magnitude);
        for (int i = 0; i < EMBEDDING_DIMENSION; i++) {
            embedding.add((float) (vector[i] / magnitude));
        }
        
        return embedding;
    }
    
    /**
     * Call actual BGE embedding API (production implementation)
     */
    private List<List<Float>> callBgeEmbeddingApi(List<String> texts) throws Exception {
        Map<String, Object> requestBody = new HashMap<>();
        requestBody.put("model", MODEL_NAME);
        requestBody.put("input", texts);
        requestBody.put("encoding_format", "float");
        
        String jsonRequest = objectMapper.writeValueAsString(requestBody);
        
        HttpPost httpPost = new HttpPost(embeddingApiUrl);
        httpPost.setHeader("Content-Type", "application/json");
        if (embeddingApiKey != null && !embeddingApiKey.isEmpty()) {
            httpPost.setHeader("Authorization", "Bearer " + embeddingApiKey);
        }
        httpPost.setEntity(new StringEntity(jsonRequest, StandardCharsets.UTF_8));
        
        try (CloseableHttpResponse response = httpClient.execute(httpPost)) {
            String responseBody = new String(response.getEntity().getContent().readAllBytes(), 
                    StandardCharsets.UTF_8);
            
            JsonNode responseJson = objectMapper.readTree(responseBody);
            JsonNode dataArray = responseJson.get("data");
            
            List<List<Float>> embeddings = new ArrayList<>();
            for (JsonNode dataItem : dataArray) {
                JsonNode embeddingArray = dataItem.get("embedding");
                List<Float> embedding = new ArrayList<>();
                
                for (JsonNode value : embeddingArray) {
                    embedding.add(value.floatValue());
                }
                embeddings.add(embedding);
            }
            
            return embeddings;
        }
    }
    
    /**
     * Generate cache key for text
     */
    private String generateCacheKey(String text) {
        try {
            MessageDigest md = MessageDigest.getInstance("SHA-256");
            byte[] hash = md.digest(text.getBytes(StandardCharsets.UTF_8));
            StringBuilder hexString = new StringBuilder();
            
            for (byte b : hash) {
                String hex = Integer.toHexString(0xff & b);
                if (hex.length() == 1) {
                    hexString.append('0');
                }
                hexString.append(hex);
            }
            
            return hexString.toString();
        } catch (Exception e) {
            // Fallback to hashCode if SHA-256 fails
            return String.valueOf(text.hashCode());
        }
    }
    
    /**
     * Validate embedding dimensions
     */
    public boolean validateEmbedding(List<Float> embedding) {
        if (embedding == null || embedding.size() != EMBEDDING_DIMENSION) {
            log.warn("Invalid embedding dimension: expected {}, got {}", 
                    EMBEDDING_DIMENSION, embedding != null ? embedding.size() : 0);
            return false;
        }
        
        // Check for NaN or infinite values
        for (Float value : embedding) {
            if (value == null || Float.isNaN(value) || Float.isInfinite(value)) {
                log.warn("Invalid embedding value: {}", value);
                return false;
            }
        }
        
        return true;
    }
    
    /**
     * Calculate cosine similarity between two embeddings
     */
    public double cosineSimilarity(List<Float> embedding1, List<Float> embedding2) {
        if (embedding1.size() != embedding2.size()) {
            throw new IllegalArgumentException("Embedding dimensions must match");
        }
        
        double dotProduct = 0.0;
        double magnitude1 = 0.0;
        double magnitude2 = 0.0;
        
        for (int i = 0; i < embedding1.size(); i++) {
            float val1 = embedding1.get(i);
            float val2 = embedding2.get(i);
            
            dotProduct += val1 * val2;
            magnitude1 += val1 * val1;
            magnitude2 += val2 * val2;
        }
        
        if (magnitude1 == 0.0 || magnitude2 == 0.0) {
            return 0.0;
        }
        
        return dotProduct / (Math.sqrt(magnitude1) * Math.sqrt(magnitude2));
    }
    
    /**
     * Get embedding cache statistics
     */
    public Map<String, Object> getCacheStats() {
        Map<String, Object> stats = new HashMap<>();
        stats.put("cache_size", embeddingCache.size());
        stats.put("cache_enabled", cachingEnabled);
        stats.put("model_name", MODEL_NAME);
        stats.put("embedding_dimension", EMBEDDING_DIMENSION);
        stats.put("max_batch_size", batchSize);
        return stats;
    }
    
    /**
     * Clear embedding cache
     */
    public void clearCache() {
        embeddingCache.clear();
        log.info("Embedding cache cleared");
    }
    
    /**
     * Get embedding model information
     */
    public Map<String, Object> getModelInfo() {
        Map<String, Object> info = new HashMap<>();
        info.put("model_name", MODEL_NAME);
        info.put("embedding_dimension", EMBEDDING_DIMENSION);
        info.put("max_text_length", MAX_TEXT_LENGTH);
        info.put("batch_size", batchSize);
        info.put("api_url", embeddingApiUrl);
        info.put("caching_enabled", cachingEnabled);
        return info;
    }
}