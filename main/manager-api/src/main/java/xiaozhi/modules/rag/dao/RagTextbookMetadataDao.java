package xiaozhi.modules.rag.dao;

import xiaozhi.common.dao.BaseDao;
import xiaozhi.modules.rag.entity.RagTextbookMetadataEntity;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

/**
 * RAG Textbook Metadata DAO
 * 
 * @author Claude
 * @since 1.0.0
 */
@Mapper
public interface RagTextbookMetadataDao extends BaseDao<RagTextbookMetadataEntity> {
    
    /**
     * Find textbooks by subject and standard
     */
    List<RagTextbookMetadataEntity> findBySubjectAndStandard(@Param("subject") String subject, @Param("standard") Integer standard);
    
    /**
     * Find textbooks by processing status
     */
    List<RagTextbookMetadataEntity> findByProcessedStatus(@Param("status") String status);
    
    /**
     * Get processing statistics
     */
    List<RagTextbookMetadataEntity> getProcessingStats();
    
    /**
     * Update processing status
     */
    void updateProcessingStatus(@Param("id") Long id, @Param("status") String status);
    
    /**
     * Update vector and chunk counts
     */
    void updateCounts(@Param("id") Long id, @Param("vectorCount") Integer vectorCount, @Param("chunkCount") Integer chunkCount);
}