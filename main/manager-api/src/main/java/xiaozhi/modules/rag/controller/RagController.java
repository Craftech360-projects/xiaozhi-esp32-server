package xiaozhi.modules.rag.controller;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;
import xiaozhi.common.utils.Result;
import xiaozhi.modules.rag.dto.TextbookUploadDTO;
import xiaozhi.modules.rag.dto.RagSearchDTO;
import xiaozhi.modules.rag.service.RagTextbookService;
import xiaozhi.modules.rag.service.QdrantService;
import xiaozhi.modules.rag.service.EmbeddingService;
import xiaozhi.modules.rag.service.VectorProcessingService;
import xiaozhi.modules.rag.service.TextbookProcessingDemoService;
import xiaozhi.modules.rag.service.RagCacheService;
import xiaozhi.modules.rag.vo.TextbookStatusVO;
import xiaozhi.modules.rag.vo.RagSearchResultVO;

import java.util.Map;
import java.util.List;
import java.util.HashMap;
import java.util.concurrent.CompletableFuture;
import java.util.stream.Collectors;

/**
 * RAG System API Controller
 * Handles textbook upload, processing status, and search operations
 * 
 * @author Claude
 * @since 1.0.0
 */
@Slf4j
@RestController
@RequestMapping("/api/rag")
@Tag(name = "RAG System", description = "Educational RAG system management")
public class RagController {
    
    @Autowired
    private RagTextbookService textbookService;
    
    @Autowired
    private QdrantService qdrantService;
    
    @Autowired
    private EmbeddingService embeddingService;
    
    @Autowired  
    private VectorProcessingService vectorProcessingService;
    
    @Autowired
    private TextbookProcessingDemoService demoService;
    
    @Autowired
    private RagCacheService cacheService;
    
    /**
     * Upload and process NCERT textbook
     */
    @PostMapping("/textbook/upload")
    @Operation(summary = "Upload NCERT textbook for processing", description = "Upload a PDF textbook and initiate RAG processing")
    public Result<?> uploadTextbook(
        @Parameter(description = "Textbook PDF file") @RequestParam("file") MultipartFile file,
        @Parameter(description = "Subject") @RequestParam("subject") String subject,
        @Parameter(description = "Standard") @RequestParam("standard") Integer standard,
        @Parameter(description = "Chapter number") @RequestParam("chapterNumber") Integer chapterNumber,
        @Parameter(description = "Chapter title") @RequestParam("chapterTitle") String chapterTitle,
        @Parameter(description = "Language (optional)") @RequestParam(value = "language", defaultValue = "English") String language
    ) {
        try {
            log.info("Received textbook upload request: subject={}, standard={}, chapterNumber={}, chapterTitle={}", 
                subject, standard, chapterNumber, chapterTitle);
            
            // Validate file
            if (file.isEmpty() || !file.getOriginalFilename().toLowerCase().endsWith(".pdf")) {
                return new Result<>().error("Please upload a valid PDF file");
            }
            
            // Validate subject and standard
            if (!isValidSubject(subject)) {
                return new Result<>().error("Invalid subject. Supported: mathematics, science, english");
            }
            
            if (standard < 1 || standard > 12) {
                return new Result<>().error("Invalid standard. Must be between 1 and 12");
            }
            
            // Validate chapter parameters
            if (chapterNumber == null || chapterNumber < 1 || chapterNumber > 20) {
                return new Result<>().error("Invalid chapter number. Must be between 1 and 20");
            }
            
            if (chapterTitle == null || chapterTitle.trim().isEmpty()) {
                return new Result<>().error("Chapter title cannot be empty");
            }
            
            // For MVP, only allow Standard 6 Mathematics
            if (!"mathematics".equals(subject) || standard != 6) {
                return new Result<>().error("Currently only Standard 6 Mathematics is supported in MVP version");
            }
            
            // Create DTO from parameters
            TextbookUploadDTO uploadDTO = new TextbookUploadDTO();
            uploadDTO.setSubject(subject);
            uploadDTO.setStandard(standard);
            uploadDTO.setChapterNumber(chapterNumber);
            uploadDTO.setChapterTitle(chapterTitle);
            uploadDTO.setLanguage(language);
            
            // Generate textbook title based on parameters
            String textbookTitle = String.format("NCERT %s Chapter %d - %s (Standard %d)", 
                    subject.substring(0, 1).toUpperCase() + subject.substring(1), 
                    chapterNumber, 
                    chapterTitle, 
                    standard);
            uploadDTO.setTextbookTitle(textbookTitle);
            
            log.info("Generated textbook title: '{}'", textbookTitle);
            
            // Process textbook asynchronously
            CompletableFuture<Long> processingFuture = textbookService.processTextbook(file, uploadDTO);
            
            Long textbookId = processingFuture.get();
            
            Result<Object> result = new Result<>();
            result.setData(Map.of(
                "textbook_id", textbookId,
                "message", "Textbook upload initiated successfully. Processing will continue in background.",
                "status", "processing"
            ));
            return result;
            
        } catch (Exception e) {
            log.error("Error uploading textbook", e);
            return new Result<>().error("Failed to upload textbook: " + e.getMessage());
        }
    }
    
    /**
     * Get textbook processing status
     */
    @GetMapping("/textbook/{id}/status")
    @Operation(summary = "Get textbook processing status", description = "Check the processing status of an uploaded textbook")
    public Result<TextbookStatusVO> getTextbookStatus(
        @Parameter(description = "Textbook ID") @PathVariable Long id
    ) {
        try {
            TextbookStatusVO status = textbookService.getProcessingStatus(id);
            Result<TextbookStatusVO> result = new Result<>();
            result.setData(status);
            return result;
        } catch (Exception e) {
            log.error("Error getting textbook status for ID: {}", id, e);
            return new Result<TextbookStatusVO>().error("Failed to get processing status");
        }
    }
    
    /**
     * List all textbooks with their status
     */
    @GetMapping("/textbooks")
    @Operation(summary = "List all textbooks", description = "Get a list of all uploaded textbooks with their processing status")
    public Result<?> listTextbooks(
        @Parameter(description = "Subject filter") @RequestParam(required = false) String subject,
        @Parameter(description = "Standard filter") @RequestParam(required = false) Integer standard,
        @Parameter(description = "Status filter") @RequestParam(required = false) String status
    ) {
        try {
            var textbooks = textbookService.listTextbooks(subject, standard, status);
            Result<Object> result = new Result<>();
            result.setData(textbooks);
            return result;
        } catch (Exception e) {
            log.error("Error listing textbooks", e);
            return new Result<>().error("Failed to list textbooks");
        }
    }
    
    /**
     * Search RAG content with intelligent caching
     */
    @PostMapping("/search")
    @Operation(summary = "Search RAG content", description = "Search for educational content using RAG system with intelligent caching")
    public Result<RagSearchResultVO> searchContent(
        @Parameter(description = "Search parameters") @RequestBody RagSearchDTO searchDTO
    ) {
        try {
            log.info("RAG search request: {}", searchDTO);
            
            // Validate search query
            if (searchDTO.getQuery() == null || searchDTO.getQuery().trim().isEmpty()) {
                return new Result<RagSearchResultVO>().error("Search query cannot be empty");
            }
            
            // Check cache first
            var cachedResults = cacheService.getCachedSearchResults(
                searchDTO.getQuery(), 
                searchDTO.getSubject(), 
                searchDTO.getStandard()
            );
            
            RagSearchResultVO searchResult;
            
            if (cachedResults.isPresent()) {
                log.info("Cache hit for query: {}", searchDTO.getQuery());
                
                // Create result from cached data
                searchResult = new RagSearchResultVO();
                searchResult.setQuery(searchDTO.getQuery());
                searchResult.setResults(cachedResults.get());
                searchResult.setFromCache(true);
                searchResult.setProcessingTime(5L); // Minimal processing time for cached results
                
            } else {
                log.info("Cache miss for query: {}, performing fresh search", searchDTO.getQuery());
                
                // Perform fresh RAG search
                long startTime = System.currentTimeMillis();
                searchResult = textbookService.searchContent(searchDTO);
                long processingTime = System.currentTimeMillis() - startTime;
                
                searchResult.setFromCache(false);
                searchResult.setProcessingTime(processingTime);
                
                // Cache the results for future use
                if (searchResult.getResults() != null && !searchResult.getResults().isEmpty()) {
                    // Convert SearchResult objects to Maps for caching
                    List<Map<String, Object>> resultMaps = searchResult.getResults().stream()
                        .map(result -> {
                            Map<String, Object> map = new HashMap<>();
                            map.put("content", result.getContent());
                            map.put("score", result.getScore());
                            map.put("source", result.getSource());
                            map.put("metadata", result.getContentMetadata());
                            return map;
                        })
                        .collect(Collectors.toList());
                    
                    cacheService.cacheSearchResults(
                        searchDTO.getQuery(),
                        searchDTO.getSubject(),
                        searchDTO.getStandard(),
                        resultMaps
                    );
                    
                    log.info("Cached search results for query: {} ({} results)", 
                        searchDTO.getQuery(), searchResult.getResults().size());
                }
            }
            
            Result<RagSearchResultVO> result = new Result<>();
            result.setData(searchResult);
            return result;
            
        } catch (Exception e) {
            log.error("Error performing RAG search", e);
            return new Result<RagSearchResultVO>().error("Search failed: " + e.getMessage());
        }
    }
    
    /**
     * Get collection information
     */
    @GetMapping("/collections/{collectionName}/info")
    @Operation(summary = "Get collection information", description = "Get detailed information about a Qdrant collection")
    public Result<?> getCollectionInfo(
        @Parameter(description = "Collection name") @PathVariable String collectionName
    ) {
        try {
            CompletableFuture<Map<String, Object>> infoFuture = qdrantService.getCollectionInfo(collectionName);
            Map<String, Object> info = infoFuture.get();
            
            Result<Object> result = new Result<>();
            result.setData(info);
            return result;
        } catch (Exception e) {
            log.error("Error getting collection info for: {}", collectionName, e);
            return new Result<>().error("Failed to get collection information");
        }
    }
    
    /**
     * Initialize Standard 6 Mathematics collection
     */
    @PostMapping("/collections/init-math-std6")
    @Operation(summary = "Initialize Mathematics Standard 6 collection", description = "Create and configure the mathematics_std6 collection in Qdrant")
    public Result<?> initializeMathStd6Collection() {
        try {
            log.info("Initializing mathematics_std6 collection...");
            
            String collectionName = "mathematics_std6";
            
            // Check if collection already exists
            CompletableFuture<Boolean> existsFuture = qdrantService.collectionExists(collectionName);
            boolean exists = existsFuture.get();
            
            if (exists) {
                Result<Object> result = new Result<>();
                result.setData(Map.of(
                    "message", "Collection already exists",
                    "collection_name", collectionName,
                    "status", "exists"
                ));
                return result;
            }
            
            // Create collection with production configuration
            CompletableFuture<Boolean> createFuture = qdrantService.createCollection(collectionName, Map.of());
            boolean success = createFuture.get();
            
            if (success) {
                Result<Object> result = new Result<>();
                result.setData(Map.of(
                    "message", "Collection created successfully",
                    "collection_name", collectionName,
                    "status", "created"
                ));
                return result;
            } else {
                return new Result<>().error("Failed to create collection");
            }
            
        } catch (Exception e) {
            log.error("Error initializing mathematics_std6 collection", e);
            return new Result<>().error("Failed to initialize collection: " + e.getMessage());
        }
    }
    
    /**
     * Get system health status
     */
    @GetMapping("/health")
    @Operation(summary = "Get RAG system health", description = "Check the health status of RAG system components")
    public Result<?> getSystemHealth() {
        try {
            // Check Qdrant connectivity
            boolean qdrantHealthy = true;
            try {
                qdrantService.getClient().healthCheckAsync().get();
            } catch (Exception e) {
                qdrantHealthy = false;
                log.warn("Qdrant health check failed", e);
            }
            
            // Check collection status for mathematics_std6
            Map<String, Object> collectionInfo = null;
            try {
                collectionInfo = qdrantService.getCollectionInfo("mathematics_std6").get();
            } catch (Exception e) {
                log.warn("Could not get mathematics_std6 collection info", e);
            }
            
            Result<Object> result = new Result<>();
            result.setData(Map.of(
                "qdrant_healthy", qdrantHealthy,
                "mathematics_std6_collection", collectionInfo != null ? "available" : "not_found",
                "collection_info", collectionInfo != null ? collectionInfo : Map.of(),
                "timestamp", System.currentTimeMillis()
            ));
            return result;
            
        } catch (Exception e) {
            log.error("Error checking system health", e);
            return new Result<>().error("Health check failed: " + e.getMessage());
        }
    }
    
    /**
     * Get embedding service information
     */
    @GetMapping("/embedding/info")
    @Operation(summary = "Get embedding service info", description = "Get information about the embedding service and model")
    public Result<?> getEmbeddingInfo() {
        try {
            Map<String, Object> info = embeddingService.getModelInfo();
            Result<Object> result = new Result<>();
            result.setData(info);
            return result;
        } catch (Exception e) {
            log.error("Error getting embedding info", e);
            return new Result<>().error("Failed to get embedding info");
        }
    }
    
    /**
     * Get embedding cache statistics
     */
    @GetMapping("/embedding/cache/stats")
    @Operation(summary = "Get embedding cache stats", description = "Get statistics about the embedding cache")
    public Result<?> getEmbeddingCacheStats() {
        try {
            Map<String, Object> stats = embeddingService.getCacheStats();
            Result<Object> result = new Result<>();
            result.setData(stats);
            return result;
        } catch (Exception e) {
            log.error("Error getting embedding cache stats", e);
            return new Result<>().error("Failed to get cache stats");
        }
    }
    
    /**
     * Clear embedding cache
     */
    @PostMapping("/embedding/cache/clear")
    @Operation(summary = "Clear embedding cache", description = "Clear all cached embeddings")
    public Result<?> clearEmbeddingCache() {
        try {
            embeddingService.clearCache();
            Result<Object> result = new Result<>();
            result.setData(Map.of("message", "Embedding cache cleared successfully"));
            return result;
        } catch (Exception e) {
            log.error("Error clearing embedding cache", e);
            return new Result<>().error("Failed to clear cache");
        }
    }
    
    /**
     * Get vector processing statistics
     */
    @GetMapping("/vectors/stats/{collectionName}")
    @Operation(summary = "Get vector processing stats", description = "Get statistics about vector processing for a collection")
    public Result<?> getVectorProcessingStats(
        @Parameter(description = "Collection name") @PathVariable String collectionName
    ) {
        try {
            Map<String, Object> stats = vectorProcessingService.getProcessingStats(collectionName);
            Result<Object> result = new Result<>();
            result.setData(stats);
            return result;
        } catch (Exception e) {
            log.error("Error getting vector processing stats for collection: {}", collectionName, e);
            return new Result<>().error("Failed to get processing stats");
        }
    }
    
    /**
     * Test embedding generation
     */
    @PostMapping("/embedding/test")
    @Operation(summary = "Test embedding generation", description = "Generate embedding for test text")
    public Result<?> testEmbedding(
        @Parameter(description = "Test text") @RequestParam String text
    ) {
        try {
            if (text == null || text.trim().isEmpty()) {
                return new Result<>().error("Text cannot be empty");
            }
            
            var embedding = embeddingService.generateEmbedding(text).join();
            boolean isValid = embeddingService.validateEmbedding(embedding);
            
            Result<Object> result = new Result<>();
            result.setData(Map.of(
                "text", text,
                "embedding_dimension", embedding.size(),
                "is_valid", isValid,
                "sample_values", embedding.subList(0, Math.min(5, embedding.size())),
                "model_info", embeddingService.getModelInfo()
            ));
            return result;
            
        } catch (Exception e) {
            log.error("Error testing embedding generation", e);
            return new Result<>().error("Embedding test failed: " + e.getMessage());
        }
    }
    
    /**
     * Process NCERT Standard 6 Mathematics textbook (demonstration)
     */
    @PostMapping("/demo/process-std6-math")
    @Operation(summary = "Process Standard 6 Math textbook", description = "Comprehensive demonstration of NCERT Standard 6 Mathematics textbook processing")
    public Result<?> processStandard6MathTextbook() {
        try {
            log.info("Starting Standard 6 Mathematics textbook processing demonstration");
            
            var processingResult = demoService.processStandard6MathTextbook().join();
            
            Result<Object> result = new Result<>();
            result.setData(processingResult);
            return result;
            
        } catch (Exception e) {
            log.error("Error in Standard 6 Math textbook processing demo", e);
            return new Result<>().error("Demo processing failed: " + e.getMessage());
        }
    }
    
    /**
     * Get comprehensive processing statistics
     */
    @GetMapping("/statistics/processing")
    @Operation(summary = "Get processing statistics", description = "Get comprehensive statistics about textbook processing")
    public Result<?> getProcessingStatistics() {
        try {
            Map<String, Object> statistics = demoService.getProcessingStatistics();
            Result<Object> result = new Result<>();
            result.setData(statistics);
            return result;
        } catch (Exception e) {
            log.error("Error getting processing statistics", e);
            return new Result<>().error("Failed to get statistics");
        }
    }
    
    /**
     * Test mathematics search functionality
     */
    @PostMapping("/demo/test-math-search")
    @Operation(summary = "Test mathematics search", description = "Test comprehensive search functionality across Standard 6 Mathematics content")
    public Result<?> testMathematicsSearch() {
        try {
            Map<String, Object> searchResults = demoService.testMathematicsSearch();
            Result<Object> result = new Result<>();
            result.setData(searchResults);
            return result;
        } catch (Exception e) {
            log.error("Error testing mathematics search", e);
            return new Result<>().error("Search test failed: " + e.getMessage());
        }
    }
    
    /**
     * Get curriculum coverage information
     */
    @GetMapping("/curriculum/std6-math")
    @Operation(summary = "Get Standard 6 Math curriculum", description = "Get comprehensive curriculum coverage information for Standard 6 Mathematics")
    public Result<?> getStandard6MathCurriculum() {
        try {
            Map<String, Object> curriculum = Map.of(
                "subject", "Mathematics",
                "standard", 6,
                "total_chapters", 10,
                "chapters", List.of(
                    Map.of("number", 1, "title", "Patterns in Mathematics", "page", 1, "topics", List.of("Number patterns", "Shape patterns", "Logical thinking")),
                    Map.of("number", 2, "title", "Lines and Angles", "page", 13, "topics", List.of("Types of lines", "Parallel lines", "Angles", "Angle types")),
                    Map.of("number", 3, "title", "Number Play", "page", 55, "topics", List.of("Factors", "Multiples", "Prime numbers", "Composite numbers")),
                    Map.of("number", 4, "title", "Data Handling and Presentation", "page", 74, "topics", List.of("Data collection", "Pictographs", "Bar graphs", "Tally marks")),
                    Map.of("number", 5, "title", "Prime Time", "page", 107, "topics", List.of("Prime numbers", "Prime factorization", "HCF", "LCM")),
                    Map.of("number", 6, "title", "Perimeter and Area", "page", 129, "topics", List.of("Perimeter", "Area", "Rectangle", "Square", "Measurement")),
                    Map.of("number", 7, "title", "Fractions", "page", 151, "topics", List.of("Types of fractions", "Equivalent fractions", "Operations", "Mixed numbers")),
                    Map.of("number", 8, "title", "Playing with Constructions", "page", 187, "topics", List.of("Geometric constructions", "Angles", "Perpendiculars", "Bisectors")),
                    Map.of("number", 9, "title", "Symmetry", "page", 217, "topics", List.of("Line symmetry", "Lines of symmetry", "Symmetry in nature", "Common shapes")),
                    Map.of("number", 10, "title", "The Other Side of Zero", "page", 242, "topics", List.of("Negative numbers", "Integers", "Number line", "Integer operations"))
                ),
                "learning_objectives", List.of(
                    "Develop number sense and operations",
                    "Understand basic geometric concepts", 
                    "Introduction to algebraic thinking",
                    "Data interpretation skills",
                    "Problem solving abilities",
                    "Mathematical reasoning"
                ),
                "difficulty_progression", Map.of(
                    "basic_concepts", List.of(1, 2, 4, 6, 9),
                    "intermediate_concepts", List.of(3, 5, 7, 8),
                    "advanced_concepts", List.of(10)
                )
            );
            
            Result<Object> result = new Result<>();
            result.setData(curriculum);
            return result;
            
        } catch (Exception e) {
            log.error("Error getting curriculum information", e);
            return new Result<>().error("Failed to get curriculum info");
        }
    }
    
    /**
     * Validate if subject is supported
     */
    private boolean isValidSubject(String subject) {
        return subject != null && 
               ("mathematics".equals(subject) || "science".equals(subject) || "english".equals(subject));
    }
}