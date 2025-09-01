package xiaozhi.modules.rag.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import lombok.EqualsAndHashCode;
import xiaozhi.common.entity.BaseEntity;

import java.time.LocalDateTime;

/**
 * RAG Textbook Metadata Entity
 * Manages textbook information for the RAG system
 * 
 * @author Claude
 * @since 1.0.0
 */
@Data
@EqualsAndHashCode(callSuper = false)
@TableName("rag_textbook_metadata")
public class RagTextbookMetadataEntity extends BaseEntity {
    
    /**
     * Subject name (mathematics, science, english, etc.)
     */
    private String subject;
    
    /**
     * Class standard (1-12)
     */
    private Integer standard;
    
    /**
     * Chapter number within textbook
     */
    private Integer chapterNumber;
    
    /**
     * Chapter title
     */
    private String chapterTitle;
    
    /**
     * Complete textbook title
     */
    private String textbookTitle;
    
    /**
     * Content language
     */
    private String language;
    
    /**
     * Path to original PDF file
     */
    private String pdfPath;
    
    /**
     * Total pages in textbook
     */
    private Integer totalPages;
    
    /**
     * Academic year/curriculum version
     */
    private String curriculumYear;
    
    /**
     * Processing status: pending, processing, completed, failed
     */
    private String processedStatus;
    
    /**
     * Total vectors stored in Qdrant
     */
    private Integer vectorCount;
    
    /**
     * Total chunks processed
     */
    private Integer chunkCount;
    
    /**
     * When processing started
     */
    private LocalDateTime processingStartedAt;
    
    /**
     * When processing completed
     */
    private LocalDateTime processingCompletedAt;
    
    /**
     * User who initiated processing
     */
    private Long createdBy;
}