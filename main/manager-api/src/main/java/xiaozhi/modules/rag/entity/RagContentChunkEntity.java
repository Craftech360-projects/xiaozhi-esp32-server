package xiaozhi.modules.rag.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import lombok.EqualsAndHashCode;
import xiaozhi.common.entity.BaseEntity;

import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * RAG Content Chunk Entity
 * Manages individual content chunks with educational metadata
 * 
 * @author Claude
 * @since 1.0.0
 */
@Data
@EqualsAndHashCode(callSuper = false)
@TableName("rag_content_chunks")
public class RagContentChunkEntity extends BaseEntity {
    
    /**
     * Reference to textbook metadata
     */
    private Long textbookId;
    
    /**
     * Unique chunk identifier for Qdrant
     */
    private String chunkId;
    
    /**
     * Actual text content of the chunk
     */
    private String chunkText;
    
    /**
     * Chunk type: concept, example, exercise, definition, theorem, formula, diagram_description
     */
    private String chunkType;
    
    /**
     * Content type: text, formula, diagram_description, mixed
     */
    private String contentType;
    
    /**
     * Page number in original textbook
     */
    private Integer pageNumber;
    
    /**
     * Section/subsection title
     */
    private String sectionTitle;
    
    /**
     * Paragraph position within section
     */
    private Integer paragraphIndex;
    
    /**
     * Array of main topics covered (JSON)
     */
    private String topics;
    
    /**
     * Array of detailed subtopics (JSON)
     */
    private String subtopics;
    
    /**
     * Array of educational keywords (JSON)
     */
    private String keywords;
    
    /**
     * Array of learning objectives addressed (JSON)
     */
    private String learningObjectives;
    
    /**
     * Array of prerequisite concepts (JSON)
     */
    private String prerequisites;
    
    /**
     * Array of related topics for cross-referencing (JSON)
     */
    private String relatedConcepts;
    
    /**
     * Difficulty level: basic, intermediate, advanced
     */
    private String difficultyLevel;
    
    /**
     * Curriculum importance (0.0-1.0)
     */
    private BigDecimal importanceScore;
    
    /**
     * Bloom's taxonomy level: remember, understand, apply, analyze, evaluate, create
     */
    private String cognitiveLevel;
    
    /**
     * Token count for the chunk
     */
    private Integer chunkTokens;
    
    /**
     * Hierarchical chunk level: primary, secondary, micro
     */
    private String chunkLevel;
    
    /**
     * Parent chunk for hierarchical structure
     */
    private String parentChunkId;
    
    /**
     * Array of child chunk IDs (JSON)
     */
    private String childChunkIds;
    
    /**
     * Vector ID in Qdrant collection
     */
    private String vectorId;
    
    /**
     * Embedding model used
     */
    private String embeddingModel;
    
    /**
     * Embedding dimension
     */
    private Integer embeddingDimension;
    
    /**
     * Qdrant collection name
     */
    private String collectionName;
    
    /**
     * Additional processing information (JSON)
     */
    private String processingMetadata;
    
    /**
     * Content quality assessment (0.0-1.0)
     */
    private BigDecimal qualityScore;
    
    /**
     * How content was extracted (pdf, ocr, manual)
     */
    private String extractionMethod;
    
    /**
     * When content was processed
     */
    private LocalDateTime processedAt;
}