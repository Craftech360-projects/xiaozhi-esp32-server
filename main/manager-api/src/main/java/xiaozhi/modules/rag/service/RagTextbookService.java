package xiaozhi.modules.rag.service;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;
import xiaozhi.modules.rag.dto.TextbookUploadDTO;
import xiaozhi.modules.rag.dto.RagSearchDTO;
import xiaozhi.modules.rag.entity.RagTextbookMetadataEntity;
import xiaozhi.modules.rag.dao.RagTextbookMetadataDao;
import xiaozhi.modules.rag.vo.TextbookStatusVO;
import xiaozhi.modules.rag.vo.RagSearchResultVO;

import java.util.List;
import java.util.Map;
import java.util.HashMap;
import java.util.concurrent.CompletableFuture;

/**
 * RAG Textbook Service
 * Handles textbook processing and search operations
 * 
 * @author Claude
 * @since 1.0.0
 */
@Slf4j
@Service
public class RagTextbookService {
    
    @Autowired
    private RagTextbookMetadataDao textbookMetadataDao;
    
    @Autowired
    private QdrantService qdrantService;
    
    @Autowired
    private PdfProcessorService pdfProcessorService;
    
    @Autowired
    private VectorProcessingService vectorProcessingService;
    
    /**
     * Process uploaded textbook
     */
    public CompletableFuture<Long> processTextbook(MultipartFile file, TextbookUploadDTO uploadDTO) {
        return CompletableFuture.supplyAsync(() -> {
            try {
                log.info("Starting textbook processing for: {} Standard {}", uploadDTO.getSubject(), uploadDTO.getStandard());
                
                // Create textbook metadata entity
                RagTextbookMetadataEntity textbook = new RagTextbookMetadataEntity();
                textbook.setSubject(uploadDTO.getSubject());
                textbook.setStandard(uploadDTO.getStandard());
                textbook.setTextbookTitle(uploadDTO.getTextbookTitle());
                textbook.setLanguage(uploadDTO.getLanguage() != null ? uploadDTO.getLanguage() : "English");
                textbook.setCurriculumYear(uploadDTO.getCurriculumYear());
                textbook.setChapterNumber(uploadDTO.getChapterNumber());
                textbook.setChapterTitle(uploadDTO.getChapterTitle());
                textbook.setProcessedStatus("processing");
                
                // Debug logging
                log.debug("DTO textbookTitle: '{}'", uploadDTO.getTextbookTitle());
                log.debug("Entity textbookTitle: '{}'", textbook.getTextbookTitle());
                
                // Save to database
                textbookMetadataDao.insert(textbook);
                Long textbookId = textbook.getId();
                
                log.info("Created textbook metadata with ID: {}", textbookId);
                
                // Process PDF and generate embeddings
                processTextbookAsync(textbookId, file, uploadDTO, textbook);
                
                return textbookId;
                
            } catch (Exception e) {
                log.error("Error processing textbook", e);
                throw new RuntimeException("Textbook processing failed", e);
            }
        });
    }
    
    /**
     * Get processing status
     */
    public TextbookStatusVO getProcessingStatus(Long textbookId) {
        try {
            RagTextbookMetadataEntity textbook = textbookMetadataDao.selectById(textbookId);
            if (textbook == null) {
                throw new RuntimeException("Textbook not found: " + textbookId);
            }
            
            TextbookStatusVO status = new TextbookStatusVO();
            status.setId(textbook.getId());
            status.setSubject(textbook.getSubject());
            status.setStandard(textbook.getStandard());
            status.setTextbookTitle(textbook.getTextbookTitle());
            status.setProcessedStatus(textbook.getProcessedStatus());
            status.setVectorCount(textbook.getVectorCount());
            status.setChunkCount(textbook.getChunkCount());
            status.setProcessingStartedAt(textbook.getProcessingStartedAt());
            status.setProcessingCompletedAt(textbook.getProcessingCompletedAt());
            
            // Calculate progress percentage
            if ("completed".equals(textbook.getProcessedStatus())) {
                status.setProgressPercentage(100.0);
                status.setCurrentStep("Processing completed");
            } else if ("processing".equals(textbook.getProcessedStatus())) {
                status.setProgressPercentage(50.0);
                status.setCurrentStep("Processing content...");
            } else if ("failed".equals(textbook.getProcessedStatus())) {
                status.setProgressPercentage(0.0);
                status.setCurrentStep("Processing failed");
                status.setErrorMessage("Processing failed. Please check logs.");
            } else {
                status.setProgressPercentage(0.0);
                status.setCurrentStep("Waiting to start processing");
            }
            
            // Add processing stats
            TextbookStatusVO.ProcessingStats stats = new TextbookStatusVO.ProcessingStats();
            stats.setPagesProcessed(textbook.getTotalPages() != null ? textbook.getTotalPages() : 0);
            stats.setTotalPages(textbook.getTotalPages() != null ? textbook.getTotalPages() : 0);
            stats.setConceptsCount(0); // TODO: Calculate from chunks
            stats.setExamplesCount(0); // TODO: Calculate from chunks
            stats.setExercisesCount(0); // TODO: Calculate from chunks
            stats.setProcessingSpeed(0.0); // TODO: Calculate actual speed
            status.setStats(stats);
            
            return status;
            
        } catch (Exception e) {
            log.error("Error getting processing status for textbook ID: {}", textbookId, e);
            throw new RuntimeException("Failed to get processing status", e);
        }
    }
    
    /**
     * List textbooks with filters
     */
    public List<RagTextbookMetadataEntity> listTextbooks(String subject, Integer standard, String status) {
        try {
            if (subject != null && standard != null) {
                return textbookMetadataDao.findBySubjectAndStandard(subject, standard);
            } else if (status != null) {
                return textbookMetadataDao.findByProcessedStatus(status);
            } else {
                return textbookMetadataDao.selectList(null);
            }
        } catch (Exception e) {
            log.error("Error listing textbooks", e);
            throw new RuntimeException("Failed to list textbooks", e);
        }
    }
    
    /**
     * Search content using RAG
     */
    public RagSearchResultVO searchContent(RagSearchDTO searchDTO) {
        try {
            log.info("Performing RAG search: {}", searchDTO.getQuery());
            
            // TODO: Implement actual RAG search
            // For now, return mock results for testing
            RagSearchResultVO result = new RagSearchResultVO();
            result.setQuery(searchDTO.getQuery());
            result.setTotalResults(0);
            result.setResults(List.of());
            
            RagSearchResultVO.SearchMetadata metadata = new RagSearchResultVO.SearchMetadata();
            metadata.setQueryTimeMs(50L);
            metadata.setRetrievalTimeMs(30L);
            metadata.setVectorsSearched(0);
            metadata.setCacheHit(false);
            metadata.setDetectedSubject(searchDTO.getSubject() != null ? searchDTO.getSubject() : "mathematics");
            metadata.setDetectedStandard(searchDTO.getStandard() != null ? searchDTO.getStandard() : 6);
            
            result.setMetadata(metadata);
            
            return result;
            
        } catch (Exception e) {
            log.error("Error performing RAG search", e);
            throw new RuntimeException("Search failed", e);
        }
    }
    
    /**
     * Async processing of textbook PDF
     */
    private void processTextbookAsync(Long textbookId, MultipartFile file, 
                                    TextbookUploadDTO uploadDTO, RagTextbookMetadataEntity textbook) {
        
        // Read file bytes synchronously before async processing to avoid temp file cleanup
        String filename = file.getOriginalFilename();
        byte[] fileContent;
        
        try {
            fileContent = file.getBytes();
            log.info("Read {} bytes from file: {} before async processing", fileContent.length, filename);
        } catch (Exception e) {
            log.error("Failed to read file bytes from: {}", filename, e);
            textbook.setProcessedStatus("failed");
            textbook.setProcessingCompletedAt(java.time.LocalDateTime.now());
            textbookMetadataDao.updateById(textbook);
            return;
        }
        
        CompletableFuture.runAsync(() -> {
            try {
                log.info("Starting async processing for textbook ID: {}", textbookId);
                
                // Update status to processing
                textbook.setProcessedStatus("processing");
                textbook.setProcessingStartedAt(java.time.LocalDateTime.now());
                textbookMetadataDao.updateById(textbook);
                
                // Prepare metadata for processing
                Map<String, Object> metadata = new HashMap<>();
                metadata.put("subject", uploadDTO.getSubject());
                metadata.put("standard", uploadDTO.getStandard());
                metadata.put("textbookTitle", uploadDTO.getTextbookTitle());
                metadata.put("language", uploadDTO.getLanguage());
                metadata.put("curriculumYear", uploadDTO.getCurriculumYear());
                metadata.put("chapterNumber", uploadDTO.getChapterNumber());
                metadata.put("chapterTitle", uploadDTO.getChapterTitle());
                
                // Process PDF content using saved bytes
                Map<String, Object> pdfResult = pdfProcessorService.processPdfTextbook(
                    fileContent, filename, textbookId, metadata
                ).join();
                
                if ("error".equals(pdfResult.get("status"))) {
                    throw new RuntimeException("PDF processing failed: " + pdfResult.get("error"));
                }
                
                // Generate collection name
                String collectionName = String.format("math_std%d_%s", 
                        uploadDTO.getStandard(), 
                        uploadDTO.getSubject().toLowerCase());
                
                // Check if collection exists, create if not
                if (!qdrantService.collectionExists(collectionName).join()) {
                    Map<String, Object> collectionConfig = new HashMap<>();
                    collectionConfig.put("vectors", Map.of(
                        "size", 1024,
                        "distance", "Cosine"
                    ));
                    
                    boolean created = qdrantService.createCollection(collectionName, collectionConfig).join();
                    if (!created) {
                        throw new RuntimeException("Failed to create Qdrant collection: " + collectionName);
                    }
                }
                
                // Process chunks to vectors
                Map<String, Object> vectorResult = vectorProcessingService.processChunksToVectors(
                    textbookId, collectionName
                ).join();
                
                if ("error".equals(vectorResult.get("status"))) {
                    throw new RuntimeException("Vector processing failed: " + vectorResult.get("error"));
                }
                
                // Update textbook metadata with results
                textbook.setProcessedStatus("completed");
                textbook.setProcessingCompletedAt(java.time.LocalDateTime.now());
                textbook.setVectorCount((Integer) vectorResult.get("processed_vectors"));
                textbook.setChunkCount((Integer) vectorResult.get("total_chunks"));
                textbook.setTotalPages((Integer) pdfResult.getOrDefault("estimatedPages", 0));
                textbookMetadataDao.updateById(textbook);
                
                log.info("Successfully completed processing for textbook ID: {} with {} vectors", 
                        textbookId, vectorResult.get("processed_vectors"));
                
            } catch (Exception e) {
                log.error("Error in async textbook processing for ID: {}", textbookId, e);
                
                // Update status to failed
                textbook.setProcessedStatus("failed");
                textbook.setProcessingCompletedAt(java.time.LocalDateTime.now());
                textbookMetadataDao.updateById(textbook);
            }
        });
    }
}