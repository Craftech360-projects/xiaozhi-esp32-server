package xiaozhi.modules.rag.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.Data;
import java.time.LocalDateTime;

/**
 * RAG Document Entity
 */
@Data
@TableName("rag_document")
public class RagDocument {
    
    @TableId(type = IdType.AUTO)
    private Long id;
    
    private String documentName;
    
    private String fileName;
    
    private String grade;
    
    private String subject;
    
    private Long fileSize;
    
    private String filePath;
    
    private String status;
    
    private Integer totalChunks;
    
    private Integer processedChunks;
    
    private String processingError;
    
    private String processingStats;
    
    private LocalDateTime uploadTime;
    
    private LocalDateTime processedTime;
    
    private String description;
    
    private String tags;
    
    @TableField(fill = FieldFill.INSERT)
    private LocalDateTime createTime;
    
    @TableField(fill = FieldFill.INSERT_UPDATE)
    private LocalDateTime updateTime;
    
    @TableLogic
    private Integer deleted;
}