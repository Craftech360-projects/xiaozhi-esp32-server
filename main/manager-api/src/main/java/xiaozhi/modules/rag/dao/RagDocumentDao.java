package xiaozhi.modules.rag.dao;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import xiaozhi.common.dao.BaseDao;
import org.apache.ibatis.annotations.Mapper;
import xiaozhi.modules.rag.entity.RagDocument;

/**
 * RAG Document DAO
 */
@Mapper
public interface RagDocumentDao extends BaseDao<RagDocument> {
}