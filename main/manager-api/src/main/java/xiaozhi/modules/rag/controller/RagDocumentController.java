package xiaozhi.modules.rag.controller;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;
import xiaozhi.common.page.PageData;
import xiaozhi.common.utils.Result;
import xiaozhi.modules.rag.dto.DocumentUploadRequest;
import xiaozhi.modules.rag.dto.DocumentQueryRequest;
import xiaozhi.modules.rag.service.RagDocumentService;
import xiaozhi.modules.rag.vo.DocumentInfoVO;
import xiaozhi.modules.rag.vo.CollectionInfoVO;

import jakarta.validation.Valid;
import java.util.List;

/**
 * RAG Document Management Controller
 * Handles PDF upload and processing for educational content
 */
@Tag(name = "RAG Document Management")
@RestController
@RequestMapping("/rag/document")
public class RagDocumentController {

    @Autowired
    private RagDocumentService ragDocumentService;

    @Operation(summary = "Upload PDF document")
    @PostMapping(value = "/upload", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public Result<DocumentInfoVO> uploadDocument(
            @RequestPart("file") MultipartFile file,
            @RequestParam(value = "grade", defaultValue = "class-6") String grade,
            @RequestParam(value = "subject", defaultValue = "mathematics") String subject,
            @RequestParam(value = "documentName", required = false) String documentName) {
        
        return new Result<DocumentInfoVO>().ok(ragDocumentService.uploadDocument(file, grade, subject, documentName));
    }

    @Operation(summary = "Upload multiple PDF documents")
    @PostMapping(value = "/upload-batch", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public Result<List<DocumentInfoVO>> uploadDocumentsBatch(
            @RequestPart("files") MultipartFile[] files,
            @RequestParam(value = "grade", defaultValue = "class-6") String grade,
            @RequestParam(value = "subject", defaultValue = "mathematics") String subject) {
        
        return new Result<List<DocumentInfoVO>>().ok(ragDocumentService.uploadDocumentsBatch(files, grade, subject));
    }

    @Operation(summary = "Get collection information")
    @GetMapping("/collection/info")
    public Result<CollectionInfoVO> getCollectionInfo(
            @RequestParam(value = "grade", defaultValue = "class-6") String grade,
            @RequestParam(value = "subject", defaultValue = "mathematics") String subject) {
        
        return new Result<CollectionInfoVO>().ok(ragDocumentService.getCollectionInfo(grade, subject));
    }

    @Operation(summary = "List all collections")
    @GetMapping("/collection/list")
    public Result<List<CollectionInfoVO>> listCollections() {
        return new Result<List<CollectionInfoVO>>().ok(ragDocumentService.listCollections());
    }

    @Operation(summary = "Delete collection")
    @DeleteMapping("/collection")
    public Result<Void> deleteCollection(
            @RequestParam("grade") String grade,
            @RequestParam("subject") String subject) {
        
        ragDocumentService.deleteCollection(grade, subject);
        return new Result<Void>().ok(null);
    }

    @Operation(summary = "Get document list")
    @GetMapping("/list")
    public Result<PageData<DocumentInfoVO>> getDocumentList(@Valid DocumentQueryRequest request) {
        return new Result<PageData<DocumentInfoVO>>().ok(ragDocumentService.getDocumentList(request));
    }

    @Operation(summary = "Delete document")
    @DeleteMapping("/{documentId}")
    public Result<Void> deleteDocument(@PathVariable Long documentId) {
        ragDocumentService.deleteDocument(documentId);
        return new Result<Void>().ok(null);
    }

    @Operation(summary = "Process existing document")
    @PostMapping("/process/{documentId}")
    public Result<DocumentInfoVO> processDocument(@PathVariable Long documentId) {
        return new Result<DocumentInfoVO>().ok(ragDocumentService.processDocument(documentId));
    }

    @Operation(summary = "Get processing status")
    @GetMapping("/status/{documentId}")
    public Result<DocumentInfoVO> getProcessingStatus(@PathVariable Long documentId) {
        return new Result<DocumentInfoVO>().ok(ragDocumentService.getProcessingStatus(documentId));
    }

    @Operation(summary = "Get collection analytics")
    @GetMapping("/collection/analytics")
    public Result<Object> getCollectionAnalytics(
            @RequestParam("grade") String grade,
            @RequestParam("subject") String subject) {
        
        return new Result<Object>().ok(ragDocumentService.getCollectionAnalytics(grade, subject));
    }

    @Operation(summary = "Get content type items")
    @GetMapping("/content/items")
    public Result<Object> getContentTypeItems(
            @RequestParam("grade") String grade,
            @RequestParam("subject") String subject,
            @RequestParam("contentType") String contentType) {
        
        return new Result<Object>().ok(ragDocumentService.getContentTypeItems(grade, subject, contentType));
    }
}