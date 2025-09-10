package xiaozhi.modules.rag.service;

import org.springframework.web.multipart.MultipartFile;
import xiaozhi.common.page.PageData;
import xiaozhi.modules.rag.dto.DocumentQueryRequest;
import xiaozhi.modules.rag.vo.CollectionInfoVO;
import xiaozhi.modules.rag.vo.DocumentInfoVO;

import java.util.List;

/**
 * RAG Document Service Interface
 */
public interface RagDocumentService {
    
    /**
     * Upload single document
     */
    DocumentInfoVO uploadDocument(MultipartFile file, String grade, String subject, String documentName);
    
    /**
     * Upload multiple documents
     */
    List<DocumentInfoVO> uploadDocumentsBatch(MultipartFile[] files, String grade, String subject);
    
    /**
     * Get collection information
     */
    CollectionInfoVO getCollectionInfo(String grade, String subject);
    
    /**
     * List all collections
     */
    List<CollectionInfoVO> listCollections();
    
    /**
     * Delete collection
     */
    void deleteCollection(String grade, String subject);
    
    /**
     * Get document list with pagination
     */
    PageData<DocumentInfoVO> getDocumentList(DocumentQueryRequest request);
    
    /**
     * Delete document
     */
    void deleteDocument(Long documentId);
    
    /**
     * Process existing document
     */
    DocumentInfoVO processDocument(Long documentId);
    
    /**
     * Get processing status
     */
    DocumentInfoVO getProcessingStatus(Long documentId);
    
    /**
     * Get collection analytics
     */
    Object getCollectionAnalytics(String grade, String subject);
    
    /**
     * Get content type items
     */
    Object getContentTypeItems(String grade, String subject, String contentType);
}