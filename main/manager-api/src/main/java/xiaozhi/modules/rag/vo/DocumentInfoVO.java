package xiaozhi.modules.rag.vo;

import lombok.Data;
import java.time.LocalDateTime;

/**
 * Document Information VO
 */
@Data
public class DocumentInfoVO {
    
    private Long id;
    
    private String documentName;
    
    private String fileName;
    
    private String grade;
    
    private String subject;
    
    private Long fileSize;
    
    private String filePath;
    
    private String status; // UPLOADED, PROCESSING, PROCESSED, FAILED
    
    private Integer totalChunks;
    
    private Integer processedChunks;
    
    private String processingError;
    
    private LocalDateTime uploadTime;
    
    private LocalDateTime processedTime;
    
    private String description;
    
    private String tags;
    
    // Processing statistics
    private ProcessingStats processingStats;
    
    @Data
    public static class ProcessingStats {
        private Integer textChunks;
        private Integer tableChunks;
        private Integer imageChunks;
        private Integer totalPages;
        private String contentCategories;
    }
}