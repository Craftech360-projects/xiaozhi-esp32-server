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
import xiaozhi.modules.rag.vo.TextbookStatusVO;
import xiaozhi.modules.rag.vo.RagSearchResultVO;

import java.util.Map;
import java.util.concurrent.CompletableFuture;

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
    
    /**
     * Upload and process NCERT textbook
     */
    @PostMapping("/textbook/upload")
    @Operation(summary = "Upload NCERT textbook for processing", description = "Upload a PDF textbook and initiate RAG processing")
    public Result<?> uploadTextbook(
        @Parameter(description = "Textbook PDF file") @RequestParam("file") MultipartFile file,
        @Parameter(description = "Upload metadata") @RequestBody TextbookUploadDTO uploadDTO
    ) {
        try {
            log.info("Received textbook upload request: {}", uploadDTO);
            
            // Validate file
            if (file.isEmpty() || !file.getOriginalFilename().toLowerCase().endsWith(".pdf")) {
                return new Result<>().error("Please upload a valid PDF file");
            }
            
            // Validate subject and standard
            if (!isValidSubject(uploadDTO.getSubject())) {
                return new Result<>().error("Invalid subject. Supported: mathematics, science, english");
            }
            
            if (uploadDTO.getStandard() < 1 || uploadDTO.getStandard() > 12) {
                return new Result<>().error("Invalid standard. Must be between 1 and 12");
            }
            
            // For MVP, only allow Standard 6 Mathematics
            if (!"mathematics".equals(uploadDTO.getSubject()) || uploadDTO.getStandard() != 6) {
                return new Result<>().error("Currently only Standard 6 Mathematics is supported in MVP version");
            }
            
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
     * Search RAG content for testing
     */
    @PostMapping("/search")
    @Operation(summary = "Search RAG content", description = "Search for educational content using RAG system")
    public Result<RagSearchResultVO> searchContent(
        @Parameter(description = "Search parameters") @RequestBody RagSearchDTO searchDTO
    ) {
        try {
            log.info("RAG search request: {}", searchDTO);
            
            // Validate search query
            if (searchDTO.getQuery() == null || searchDTO.getQuery().trim().isEmpty()) {
                return new Result<RagSearchResultVO>().error("Search query cannot be empty");
            }
            
            // Perform RAG search
            RagSearchResultVO searchResult = textbookService.searchContent(searchDTO);
            
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
     * Validate if subject is supported
     */
    private boolean isValidSubject(String subject) {
        return subject != null && 
               ("mathematics".equals(subject) || "science".equals(subject) || "english".equals(subject));
    }
}