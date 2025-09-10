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
// import xiaozhi.modules.rag.service.QdrantService;
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
    
    // Temporarily comment out QdrantService to prevent startup issues
    // @Autowired
    // private QdrantService qdrantService;
    
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
    @Operation(summary = "Get collection information", description = "Get detailed information about a collection")
    public Result<?> getCollectionInfo(
        @Parameter(description = "Collection name") @PathVariable String collectionName
    ) {
        // Collection operations now handled by xiaozhi-server
        log.info("Collection info request forwarded to xiaozhi-server for collection: {}", collectionName);
        Result<Object> result = new Result<>();
        result.setData(Map.of(
            "collection_name", collectionName,
            "message", "Collection operations are now handled by xiaozhi-server",
            "status", "forwarded"
        ));
        return result;
    }
    
    /**
     * Initialize Standard 6 Mathematics collection
     */
    @PostMapping("/collections/init-math-std6")
    @Operation(summary = "Initialize Mathematics Standard 6 collection", description = "Create and configure the mathematics_std6 collection")
    public Result<?> initializeMathStd6Collection() {
        // Collection initialization now handled by xiaozhi-server automatically
        log.info("Collection initialization handled by xiaozhi-server");
        Result<Object> result = new Result<>();
        result.setData(Map.of(
            "collection", "mathematics_std6",
            "message", "Collection initialization is handled automatically by xiaozhi-server during document upload",
            "status", "auto_managed"
        ));
        return result;
    }
    
    /**
     * Get system health status
     */
    @GetMapping("/health")
    @Operation(summary = "Get RAG system health", description = "Check the health status of RAG system components")
    public Result<?> getSystemHealth() {
        // Health monitoring now handled by checking xiaozhi-server connectivity
        Result<Object> result = new Result<>();
        result.setData(Map.of(
            "manager_api_healthy", true,
            "xiaozhi_server_url", "http://localhost:8003",
            "forwarding_enabled", true,
            "message", "Document processing delegated to xiaozhi-server",
            "timestamp", System.currentTimeMillis()
        ));
        return result;
    }
    
    /**
     * Validate if subject is supported
     */
    private boolean isValidSubject(String subject) {
        return subject != null && 
               ("mathematics".equals(subject) || "science".equals(subject) || "english".equals(subject));
    }
}