package xiaozhi.modules.rag.entity;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import lombok.EqualsAndHashCode;
import xiaozhi.common.entity.BaseEntity;

import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * RAG Qdrant Collection Entity
 * Manages Qdrant collections for different subjects
 * 
 * @author Claude
 * @since 1.0.0
 */
@Data
@EqualsAndHashCode(callSuper = false)
@TableName("rag_qdrant_collections")
public class RagQdrantCollectionEntity extends BaseEntity {
    
    /**
     * Qdrant collection name
     */
    private String collectionName;
    
    /**
     * Subject this collection handles
     */
    private String subject;
    
    /**
     * Array of standards covered (JSON array like [1,2,3,4,5,6])
     */
    private String standards;
    
    /**
     * Vector dimension
     */
    private Integer vectorDimension;
    
    /**
     * Distance metric (Cosine, Dot, Euclidean)
     */
    private String distanceMetric;
    
    /**
     * Total number of vectors in collection
     */
    private Long totalVectors;
    
    /**
     * Qdrant collection configuration (JSON)
     */
    private String collectionConfig;
    
    /**
     * Performance optimization settings (JSON)
     */
    private String optimizationConfig;
    
    /**
     * Collection status: active, inactive, optimizing, error
     */
    private String status;
    
    /**
     * When collection was last optimized
     */
    private LocalDateTime lastOptimized;
    
    /**
     * Collection health score (0.0-1.0)
     */
    private BigDecimal healthScore;
}