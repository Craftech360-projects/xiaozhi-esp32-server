package xiaozhi.modules.rag.vo;

import lombok.Data;

/**
 * Collection Information VO
 */
@Data
public class CollectionInfoVO {
    
    private String collectionName;
    
    private String grade;
    
    private String subject;
    
    private Long totalDocuments;
    
    private Long totalChunks;
    
    private Integer vectorSize;
    
    private String distanceMetric;
    
    private String status;
    
    private Long storageSize;
    
    private String lastUpdated;
}