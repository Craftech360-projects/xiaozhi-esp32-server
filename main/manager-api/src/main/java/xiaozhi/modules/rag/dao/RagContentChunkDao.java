package xiaozhi.modules.rag.dao;

import xiaozhi.common.dao.BaseDao;
import xiaozhi.modules.rag.entity.RagContentChunkEntity;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

/**
 * RAG Content Chunk DAO
 * 
 * @author Claude
 * @since 1.0.0
 */
@Mapper
public interface RagContentChunkDao extends BaseDao<RagContentChunkEntity> {
    
    /**
     * Find chunks by textbook ID
     */
    List<RagContentChunkEntity> findByTextbookId(@Param("textbookId") Long textbookId);
    
    /**
     * Find chunks by collection name
     */
    List<RagContentChunkEntity> findByCollectionName(@Param("collectionName") String collectionName);
    
    /**
     * Find chunks by content type and difficulty
     */
    List<RagContentChunkEntity> findByContentTypeAndDifficulty(@Param("contentType") String contentType, @Param("difficultyLevel") String difficultyLevel);
    
    /**
     * Search chunks by keywords (full-text search)
     */
    List<RagContentChunkEntity> searchByKeywords(@Param("keywords") String keywords);
    
    /**
     * Get chunk statistics by textbook
     */
    List<RagContentChunkEntity> getChunkStatsByTextbook(@Param("textbookId") Long textbookId);
    
    /**
     * Find chunks by vector ID
     */
    RagContentChunkEntity findByVectorId(@Param("vectorId") String vectorId);
    
    /**
     * Count chunks by difficulty level
     */
    Long countByDifficultyLevel(@Param("difficultyLevel") String difficultyLevel);
    
    /**
     * Find top importance chunks
     */
    List<RagContentChunkEntity> findTopImportanceChunks(@Param("limit") Integer limit, @Param("subject") String subject);
}