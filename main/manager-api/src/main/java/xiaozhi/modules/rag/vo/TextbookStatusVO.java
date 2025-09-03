package xiaozhi.modules.rag.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * Textbook Processing Status VO
 * 
 * @author Claude
 * @since 1.0.0
 */
@Data
@Schema(description = "Textbook processing status")
public class TextbookStatusVO {
    
    @Schema(description = "Textbook ID")
    private Long id;
    
    @Schema(description = "Subject name")
    private String subject;
    
    @Schema(description = "Class standard")
    private Integer standard;
    
    @Schema(description = "Textbook title")
    private String textbookTitle;
    
    @Schema(description = "Processing status", allowableValues = {"pending", "processing", "completed", "failed"})
    private String processedStatus;
    
    @Schema(description = "Processing progress percentage")
    private Double progressPercentage;
    
    @Schema(description = "Current processing step")
    private String currentStep;
    
    @Schema(description = "Total vectors stored")
    private Integer vectorCount;
    
    @Schema(description = "Total chunks processed")
    private Integer chunkCount;
    
    @Schema(description = "Processing started time")
    private LocalDateTime processingStartedAt;
    
    @Schema(description = "Processing completed time")
    private LocalDateTime processingCompletedAt;
    
    @Schema(description = "Error message if failed")
    private String errorMessage;
    
    @Schema(description = "Estimated time remaining in minutes")
    private Integer estimatedMinutesRemaining;
    
    @Schema(description = "Processing statistics")
    private ProcessingStats stats;
    
    @Data
    @Schema(description = "Processing statistics")
    public static class ProcessingStats {
        @Schema(description = "Total pages processed")
        private Integer pagesProcessed;
        
        @Schema(description = "Total pages in textbook")
        private Integer totalPages;
        
        @Schema(description = "Concepts extracted")
        private Integer conceptsCount;
        
        @Schema(description = "Examples extracted")
        private Integer examplesCount;
        
        @Schema(description = "Exercises extracted")
        private Integer exercisesCount;
        
        @Schema(description = "Processing speed (chunks per minute)")
        private Double processingSpeed;
    }
}