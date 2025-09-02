package xiaozhi.modules.rag.service;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import xiaozhi.modules.rag.entity.RagContentChunkEntity;
import xiaozhi.modules.rag.dao.RagContentChunkDao;

import java.util.List;
import java.util.ArrayList;
import java.util.Map;
import java.util.HashMap;
import java.util.concurrent.CompletableFuture;
import java.util.stream.Collectors;

/**
 * Vector Processing Service
 * Integrates content chunks with embedding generation and vector storage
 * Handles the complete pipeline from text chunks to searchable vectors
 * 
 * @author Claude
 * @since 1.0.0
 */
@Slf4j
@Service
public class VectorProcessingService {
    
    @Autowired
    private EmbeddingService embeddingService;
    
    @Autowired
    private QdrantService qdrantService;
    
    @Autowired
    private RagContentChunkDao contentChunkDao;
    
    /**
     * Process content chunks and store as vectors
     */
    public CompletableFuture<Map<String, Object>> processChunksToVectors(
            Long textbookId, String collectionName) {
        
        return CompletableFuture.supplyAsync(() -> {
            try {
                log.info("Processing chunks to vectors for textbook ID: {} in collection: {}", 
                        textbookId, collectionName);
                
                // Get all chunks for the textbook
                List<RagContentChunkEntity> chunks = contentChunkDao.findByTextbookId(textbookId);
                
                if (chunks.isEmpty()) {
                    log.warn("No chunks found for textbook ID: {}", textbookId);
                    return Map.of("status", "error", "message", "No chunks found");
                }
                
                log.info("Found {} chunks to process for textbook ID: {}", chunks.size(), textbookId);
                
                // Extract text content for embedding generation
                List<String> texts = chunks.stream()
                        .map(RagContentChunkEntity::getChunkText)
                        .collect(Collectors.toList());
                
                // Generate embeddings in batches
                List<List<Float>> embeddings = embeddingService.generateEmbeddings(texts).join();
                
                if (embeddings.size() != chunks.size()) {
                    throw new RuntimeException("Embedding count mismatch: expected " + 
                            chunks.size() + ", got " + embeddings.size());
                }
                
                // Prepare points for Qdrant storage
                List<Map<String, Object>> points = new ArrayList<>();
                
                for (int i = 0; i < chunks.size(); i++) {
                    RagContentChunkEntity chunk = chunks.get(i);
                    List<Float> embedding = embeddings.get(i);
                    
                    // Validate embedding
                    if (!embeddingService.validateEmbedding(embedding)) {
                        log.error("Invalid embedding for chunk ID: {}", chunk.getChunkId());
                        continue;
                    }
                    
                    // Create Qdrant point
                    Map<String, Object> point = createQdrantPoint(chunk, embedding);
                    points.add(point);
                    
                    // Update chunk with vector information
                    updateChunkWithVectorInfo(chunk, collectionName, embedding.size());
                }
                
                log.info("Prepared {} valid points for Qdrant storage", points.size());
                
                // Store vectors in Qdrant
                boolean success = qdrantService.upsertVectors(collectionName, points).join();
                
                if (!success) {
                    throw new RuntimeException("Failed to store vectors in Qdrant collection: " + collectionName);
                }
                
                // Update all chunks in database
                for (RagContentChunkEntity chunk : chunks) {
                    if (chunk.getVectorId() != null) {
                        contentChunkDao.updateById(chunk);
                    }
                }
                
                // Return processing results
                Map<String, Object> result = new HashMap<>();
                result.put("status", "success");
                result.put("textbook_id", textbookId);
                result.put("collection_name", collectionName);
                result.put("total_chunks", chunks.size());
                result.put("processed_vectors", points.size());
                result.put("embedding_dimension", embeddings.get(0).size());
                
                log.info("Successfully processed {} chunks to vectors for textbook ID: {}", 
                        points.size(), textbookId);
                
                return result;
                
            } catch (Exception e) {
                log.error("Error processing chunks to vectors for textbook ID: {}", textbookId, e);
                
                Map<String, Object> errorResult = new HashMap<>();
                errorResult.put("status", "error");
                errorResult.put("error", e.getMessage());
                errorResult.put("textbook_id", textbookId);
                return errorResult;
            }
        });
    }
    
    /**
     * Create Qdrant point from chunk and embedding
     */
    private Map<String, Object> createQdrantPoint(RagContentChunkEntity chunk, List<Float> embedding) {
        Map<String, Object> point = new HashMap<>();
        
        // Set point ID
        point.put("id", chunk.getChunkId());
        
        // Set vector
        point.put("vector", embedding);
        
        // Set payload with educational metadata
        Map<String, Object> payload = new HashMap<>();
        payload.put("textbook_id", chunk.getTextbookId());
        payload.put("chunk_text", chunk.getChunkText());
        payload.put("chunk_type", chunk.getChunkType());
        payload.put("content_type", chunk.getContentType());
        payload.put("page_number", chunk.getPageNumber());
        payload.put("section_title", chunk.getSectionTitle());
        payload.put("topics", chunk.getTopics());
        payload.put("keywords", chunk.getKeywords());
        payload.put("difficulty_level", chunk.getDifficultyLevel());
        payload.put("importance_score", chunk.getImportanceScore());
        payload.put("cognitive_level", chunk.getCognitiveLevel());
        payload.put("chunk_level", chunk.getChunkLevel());
        payload.put("parent_chunk_id", chunk.getParentChunkId());
        payload.put("chunk_tokens", chunk.getChunkTokens());
        
        point.put("payload", payload);
        
        return point;
    }
    
    /**
     * Update chunk entity with vector information
     */
    private void updateChunkWithVectorInfo(RagContentChunkEntity chunk, String collectionName, int embeddingDimension) {
        chunk.setVectorId(chunk.getChunkId());
        chunk.setCollectionName(collectionName);
        chunk.setEmbeddingModel("BAAI/bge-large-en-v1.5");
        chunk.setEmbeddingDimension(embeddingDimension);
        chunk.setProcessedAt(java.time.LocalDateTime.now());
    }
    
    /**
     * Search for similar content using vector similarity
     */
    public CompletableFuture<List<Map<String, Object>>> searchSimilarContent(
            String query, String collectionName, Map<String, Object> filters, 
            int limit, float scoreThreshold) {
        
        return CompletableFuture.supplyAsync(() -> {
            try {
                log.info("Searching for similar content: '{}' in collection: {}", query, collectionName);
                
                // Generate query embedding
                List<Float> queryEmbedding = embeddingService.generateEmbedding(query).join();
                
                if (!embeddingService.validateEmbedding(queryEmbedding)) {
                    throw new RuntimeException("Invalid query embedding generated");
                }
                
                // Search in Qdrant
                List<Map<String, Object>> searchResults = qdrantService.search(
                    collectionName, queryEmbedding, filters, limit, scoreThreshold
                ).join();
                
                // Enhance results with additional metadata
                List<Map<String, Object>> enhancedResults = new ArrayList<>();
                
                for (Map<String, Object> result : searchResults) {
                    Map<String, Object> enhanced = new HashMap<>(result);
                    
                    // Add search metadata
                    enhanced.put("query", query);
                    enhanced.put("collection", collectionName);
                    enhanced.put("embedding_model", "BAAI/bge-large-en-v1.5");
                    
                    enhancedResults.add(enhanced);
                }
                
                log.info("Found {} similar content results for query: '{}'", 
                        enhancedResults.size(), query);
                
                return enhancedResults;
                
            } catch (Exception e) {
                log.error("Error searching for similar content: '{}'", query, e);
                return new ArrayList<>();
            }
        });
    }
    
    /**
     * Batch update embeddings for existing chunks
     */
    public CompletableFuture<Map<String, Object>> updateEmbeddings(
            List<Long> chunkIds, String collectionName) {
        
        return CompletableFuture.supplyAsync(() -> {
            try {
                log.info("Updating embeddings for {} chunks", chunkIds.size());
                
                List<RagContentChunkEntity> chunks = new ArrayList<>();
                for (Long id : chunkIds) {
                    RagContentChunkEntity chunk = contentChunkDao.selectById(id);
                    if (chunk != null) {
                        chunks.add(chunk);
                    }
                }
                
                if (chunks.isEmpty()) {
                    return Map.of("status", "error", "message", "No valid chunks found");
                }
                
                // Extract texts and generate new embeddings
                List<String> texts = chunks.stream()
                        .map(RagContentChunkEntity::getChunkText)
                        .collect(Collectors.toList());
                
                List<List<Float>> embeddings = embeddingService.generateEmbeddings(texts).join();
                
                // Prepare updated points
                List<Map<String, Object>> points = new ArrayList<>();
                
                for (int i = 0; i < chunks.size(); i++) {
                    RagContentChunkEntity chunk = chunks.get(i);
                    List<Float> embedding = embeddings.get(i);
                    
                    if (embeddingService.validateEmbedding(embedding)) {
                        Map<String, Object> point = createQdrantPoint(chunk, embedding);
                        points.add(point);
                        
                        updateChunkWithVectorInfo(chunk, collectionName, embedding.size());
                        contentChunkDao.updateById(chunk);
                    }
                }
                
                // Update vectors in Qdrant
                boolean success = qdrantService.upsertVectors(collectionName, points).join();
                
                Map<String, Object> result = new HashMap<>();
                result.put("status", success ? "success" : "error");
                result.put("updated_chunks", points.size());
                result.put("total_requested", chunkIds.size());
                
                return result;
                
            } catch (Exception e) {
                log.error("Error updating embeddings for chunks", e);
                return Map.of("status", "error", "error", e.getMessage());
            }
        });
    }
    
    /**
     * Get vector processing statistics
     */
    public Map<String, Object> getProcessingStats(String collectionName) {
        try {
            Map<String, Object> stats = new HashMap<>();
            
            // Get collection info from Qdrant
            Map<String, Object> collectionInfo = qdrantService.getCollectionInfo(collectionName).join();
            
            // Get embedding service stats
            Map<String, Object> embeddingStats = embeddingService.getCacheStats();
            
            // Combine statistics
            stats.put("collection_info", collectionInfo);
            stats.put("embedding_service", embeddingStats);
            stats.put("processing_service", "VectorProcessingService");
            
            return stats;
            
        } catch (Exception e) {
            log.error("Error getting processing stats for collection: {}", collectionName, e);
            return Map.of("error", e.getMessage());
        }
    }
}