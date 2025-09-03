package xiaozhi.modules.rag.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

/**
 * RAG System Configuration Properties
 * 
 * @author Claude
 * @since 1.0.0
 */
@Data
@Configuration
@ConfigurationProperties(prefix = "rag")
public class RagConfig {
    
    /**
     * Qdrant configuration
     */
    private Qdrant qdrant = new Qdrant();
    
    /**
     * Embedding service configuration
     */
    private Embedding embedding = new Embedding();
    
    /**
     * Processing configuration
     */
    private Processing processing = new Processing();
    
    /**
     * Cache configuration
     */
    private Cache cache = new Cache();
    
    @Data
    public static class Qdrant {
        /**
         * Qdrant Cloud URL
         */
        private String url = "https://your-cluster.qdrant.tech:6333";
        
        /**
         * Qdrant API Key
         */
        private String apiKey;
        
        /**
         * Connection timeout in seconds
         */
        private Integer timeout = 30;
        
        /**
         * Enable TLS for cloud connections
         */
        private Boolean tls = true;
        
        /**
         * Default collection for mathematics std 6
         */
        private String defaultCollection = "mathematics_std6";
    }
    
    @Data
    public static class Embedding {
        /**
         * Embedding service URL (for BAAI/bge-large-en-v1.5)
         */
        private String serviceUrl = "http://localhost:8001/embeddings";
        
        /**
         * Model name
         */
        private String model = "BAAI/bge-large-en-v1.5";
        
        /**
         * Vector dimensions
         */
        private Integer dimensions = 768;
        
        /**
         * Batch size for processing
         */
        private Integer batchSize = 32;
        
        /**
         * Request timeout in seconds
         */
        private Integer timeout = 60;
    }
    
    @Data
    public static class Processing {
        /**
         * Maximum chunk size in tokens
         */
        private Integer maxChunkTokens = 512;
        
        /**
         * Chunk overlap in tokens
         */
        private Integer chunkOverlap = 50;
        
        /**
         * Enable hierarchical chunking
         */
        private Boolean hierarchicalChunking = true;
        
        /**
         * Minimum importance score for indexing
         */
        private Double minImportanceScore = 0.3;
        
        /**
         * Enable parallel processing
         */
        private Boolean parallelProcessing = true;
        
        /**
         * Number of processing threads
         */
        private Integer processingThreads = 4;
    }
    
    @Data
    public static class Cache {
        /**
         * Enable query result caching
         */
        private Boolean enabled = true;
        
        /**
         * Cache TTL in seconds
         */
        private Integer ttl = 3600;
        
        /**
         * Maximum cache size
         */
        private String maxSize = "100MB";
        
        /**
         * Cache key prefix
         */
        private String keyPrefix = "rag:";
    }
}