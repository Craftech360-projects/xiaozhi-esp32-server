package xiaozhi.modules.rag.service.impl;

import cn.hutool.core.io.FileUtil;
import cn.hutool.core.util.IdUtil;
import cn.hutool.core.util.StrUtil;
import cn.hutool.http.HttpRequest;
import cn.hutool.http.HttpResponse;
import cn.hutool.json.JSONArray;
import cn.hutool.json.JSONObject;
import cn.hutool.json.JSONUtil;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;
import xiaozhi.common.exception.RenException;
import xiaozhi.common.page.PageData;
import xiaozhi.common.service.impl.BaseServiceImpl;
import xiaozhi.modules.rag.dao.RagDocumentDao;
import xiaozhi.modules.rag.dto.DocumentQueryRequest;
import xiaozhi.modules.rag.entity.RagDocument;
import xiaozhi.modules.rag.service.RagDocumentService;
import xiaozhi.modules.rag.vo.CollectionInfoVO;
import xiaozhi.modules.rag.vo.DocumentInfoVO;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.util.HashMap;
import java.util.Map;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.concurrent.CompletableFuture;

/**
 * RAG Document Service Implementation
 */
@Slf4j
@Service
public class RagDocumentServiceImpl extends BaseServiceImpl<RagDocumentDao, RagDocument> implements RagDocumentService {
    
    @Value("${rag.upload.path:./uploads/rag}")
    private String uploadPath;
    
    @Value("${rag.xiaozhi.server.url:http://localhost:8003}")
    private String xiaozhiServerUrl;
    
    @Value("${rag.max.file.size:52428800}") // 50MB
    private Long maxFileSize;
    
    @Autowired
    private RagDocumentDao ragDocumentDao;
    
    @Override
    @Transactional
    public DocumentInfoVO uploadDocument(MultipartFile file, String grade, String subject, String documentName) {
        // Validate file
        validateFile(file);
        
        // Save file to disk
        String savedFilePath = saveFile(file, grade, subject);
        
        // Create document record
        RagDocument document = new RagDocument();
        document.setDocumentName(StrUtil.isBlank(documentName) ? file.getOriginalFilename() : documentName);
        document.setFileName(file.getOriginalFilename());
        document.setGrade(grade);
        document.setSubject(subject);
        document.setFileSize(file.getSize());
        document.setFilePath(savedFilePath);
        document.setStatus("UPLOADED");
        document.setUploadTime(LocalDateTime.now());
        
        insert(document);
        
        // Process document asynchronously
        CompletableFuture.runAsync(() -> processDocumentAsync(document));
        
        return convertToVO(document);
    }
    
    @Override
    public List<DocumentInfoVO> uploadDocumentsBatch(MultipartFile[] files, String grade, String subject) {
        List<DocumentInfoVO> results = new ArrayList<>();
        
        for (MultipartFile file : files) {
            try {
                DocumentInfoVO result = uploadDocument(file, grade, subject, null);
                results.add(result);
            } catch (Exception e) {
                log.error("Failed to upload file: {}", file.getOriginalFilename(), e);
                // Create failed result
                DocumentInfoVO failedResult = new DocumentInfoVO();
                failedResult.setFileName(file.getOriginalFilename());
                failedResult.setStatus("FAILED");
                failedResult.setProcessingError(e.getMessage());
                results.add(failedResult);
            }
        }
        
        return results;
    }
    
    @Override
    public CollectionInfoVO getCollectionInfo(String grade, String subject) {
        log.info("Getting collection info for grade: {}, subject: {}", grade, subject);
        
        CollectionInfoVO info = new CollectionInfoVO();
        info.setGrade(grade);
        info.setSubject(subject);
        info.setCollectionName(grade + "-" + subject);
        
        // Get local database statistics
        LambdaQueryWrapper<RagDocument> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(RagDocument::getGrade, grade)
               .eq(RagDocument::getSubject, subject);
        
        // Count total documents
        Long totalDocuments = baseDao.selectCount(wrapper);
        info.setTotalDocuments(totalDocuments != null ? totalDocuments : 0L);
        
        // Count processed documents
        wrapper.eq(RagDocument::getStatus, "PROCESSED");
        Long processedDocuments = baseDao.selectCount(wrapper);
        
        // Calculate total chunks
        wrapper.clear();
        wrapper.eq(RagDocument::getGrade, grade)
               .eq(RagDocument::getSubject, subject)
               .eq(RagDocument::getStatus, "PROCESSED");
        List<RagDocument> processedDocs = baseDao.selectList(wrapper);
        
        long totalChunks = processedDocs.stream()
                .mapToLong(doc -> doc.getTotalChunks() != null ? doc.getTotalChunks().longValue() : 0L)
                .sum();
        
        info.setTotalChunks(totalChunks);
        
        // Set status based on document states
        if (totalDocuments == 0) {
            info.setStatus("EMPTY");
        } else if (processedDocuments.equals(totalDocuments)) {
            info.setStatus("READY");
        } else if (processedDocuments > 0) {
            info.setStatus("PARTIAL");
        } else {
            info.setStatus("PROCESSING");
        }
        
        log.info("Collection {}-{}: {} documents, {} chunks, status: {}", 
                grade, subject, totalDocuments, totalChunks, info.getStatus());
        
        try {
            // Try to get additional info from xiaozhi-server
            String url = xiaozhiServerUrl + "/educational/collection/info";
            HttpResponse response = HttpRequest.get(url)
                    .form("grade", grade)
                    .form("subject", subject)
                    .execute();
            
            if (response.isOk()) {
                JSONObject jsonResponse = JSONUtil.parseObj(response.body());
                log.debug("Received vector DB info: {}", jsonResponse.toString());
                // Additional vector DB info is available but not stored in basic CollectionInfoVO
                // This could be extended in the future if needed
            }
        } catch (Exception e) {
            log.debug("Failed to get vector DB info for collection {}-{}: {}", grade, subject, e.getMessage());
        }
        
        return info;
    }
    
    @Override
    public List<CollectionInfoVO> listCollections() {
        List<CollectionInfoVO> collections = new ArrayList<>();
        
        // Get unique grade-subject combinations from database
        List<RagDocument> documents = baseDao.selectList(
            new LambdaQueryWrapper<RagDocument>()
                .select(RagDocument::getGrade, RagDocument::getSubject)
                .groupBy(RagDocument::getGrade, RagDocument::getSubject)
        );
        
        for (RagDocument doc : documents) {
            CollectionInfoVO collection = getCollectionInfo(doc.getGrade(), doc.getSubject());
            collections.add(collection);
        }
        
        return collections;
    }
    
    @Override
    @Transactional
    public void deleteCollection(String grade, String subject) {
        // Delete from database
        baseDao.delete(
            new LambdaQueryWrapper<RagDocument>()
                .eq(RagDocument::getGrade, grade)
                .eq(RagDocument::getSubject, subject)
        );
        
        // Call xiaozhi-server to delete collection
        try {
            String url = xiaozhiServerUrl + "/educational/collection";
            HttpRequest.delete(url)
                    .form("grade", grade)
                    .form("subject", subject)
                    .execute();
        } catch (Exception e) {
            log.error("Failed to delete collection from xiaozhi-server", e);
        }
    }
    
    @Override
    public PageData<DocumentInfoVO> getDocumentList(DocumentQueryRequest request) {
        Page<RagDocument> page = new Page<>(request.getPage(), request.getLimit());
        
        LambdaQueryWrapper<RagDocument> wrapper = new LambdaQueryWrapper<>();
        
        if (StrUtil.isNotBlank(request.getGrade())) {
            wrapper.eq(RagDocument::getGrade, request.getGrade());
        }
        if (StrUtil.isNotBlank(request.getSubject())) {
            wrapper.eq(RagDocument::getSubject, request.getSubject());
        }
        if (StrUtil.isNotBlank(request.getDocumentName())) {
            wrapper.like(RagDocument::getDocumentName, request.getDocumentName());
        }
        if (StrUtil.isNotBlank(request.getStatus())) {
            wrapper.eq(RagDocument::getStatus, request.getStatus());
        }
        
        wrapper.orderByDesc(RagDocument::getUploadTime);
        
        Page<RagDocument> resultPage = baseDao.selectPage(page, wrapper);
        
        List<DocumentInfoVO> voList = new ArrayList<>();
        for (RagDocument document : resultPage.getRecords()) {
            voList.add(convertToVO(document));
        }
        
        return new PageData<>(voList, resultPage.getTotal());
    }
    
    @Override
    @Transactional
    public void deleteDocument(Long documentId) {
        RagDocument document = selectById(documentId);
        if (document == null) {
            throw new RenException("Document not found");
        }
        
        // Delete file from disk
        try {
            Files.deleteIfExists(Paths.get(document.getFilePath()));
        } catch (IOException e) {
            log.error("Failed to delete file: {}", document.getFilePath(), e);
        }
        
        // Delete from database
        deleteById(documentId);
    }
    
    @Override
    @Transactional
    public DocumentInfoVO processDocument(Long documentId) {
        RagDocument document = selectById(documentId);
        if (document == null) {
            throw new RenException("Document not found");
        }
        
        // Update status to processing
        document.setStatus("PROCESSING");
        updateById(document);
        
        // Process document asynchronously
        CompletableFuture.runAsync(() -> processDocumentAsync(document));
        
        return convertToVO(document);
    }
    
    @Override
    public DocumentInfoVO getProcessingStatus(Long documentId) {
        RagDocument document = selectById(documentId);
        if (document == null) {
            throw new RenException("Document not found");
        }
        
        return convertToVO(document);
    }
    
    @Override
    public Object getCollectionAnalytics(String grade, String subject) {
        log.info("Getting collection analytics for grade: {}, subject: {}", grade, subject);
        
        // Get all documents for this collection
        LambdaQueryWrapper<RagDocument> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(RagDocument::getGrade, grade)
               .eq(RagDocument::getSubject, subject)
               .eq(RagDocument::getStatus, "PROCESSED");
        
        List<RagDocument> documents = baseDao.selectList(wrapper);
        
        if (documents.isEmpty()) {
            log.info("No processed documents found for collection {}-{}", grade, subject);
            return createEmptyAnalytics();
        }
        
        // Only use real-time content type counts from Qdrant - no fallback to dummy data
        return generateCollectionAnalyticsWithRealCounts(documents, grade, subject);
    }
    
    private Object createEmptyAnalytics() {
        JSONObject analytics = new JSONObject();
        analytics.put("totalTopics", 0);
        analytics.put("contentTypes", new JSONObject());
        analytics.put("chunkTypes", new JSONObject());
        analytics.put("keyTopics", new ArrayList<>());
        analytics.put("avgDifficulty", "N/A");
        analytics.put("learningObjectives", new ArrayList<>());
        return analytics;
    }
    
    
    /**
     * Generate collection analytics with real-time counts from Qdrant
     */
    private Object generateCollectionAnalyticsWithRealCounts(List<RagDocument> documents, String grade, String subject) {
        log.info("Getting real-time content type counts from Qdrant for {}-{} using xiaozhi-server: {}", grade, subject, xiaozhiServerUrl);
        
        // Get real-time counts for each content type from Qdrant - NO FALLBACK TO DUMMY DATA
        String[] contentTypes = {"concept", "example", "exercise", "definition", "formula", "table", "key_concept"};
        JSONObject realContentTypes = new JSONObject();
        int totalRealChunks = 0;
        
        for (String contentType : contentTypes) {
            try {
                String endpointUrl = xiaozhiServerUrl + "/educational/content/by-type";
                String requestUrl = String.format("%s?grade=%s&subject=%s&content_type=%s&limit=100", 
                    endpointUrl, grade, subject, contentType);
                
                log.debug("Querying real-time count: {}", requestUrl);
                
                HttpResponse response = HttpRequest.get(requestUrl)
                    .timeout(10000) // 10 second timeout for counts
                    .execute();
                
                if (response.isOk()) {
                    String responseBody = response.body();
                    log.debug("Response for {}: {}", contentType, responseBody);
                    
                    JSONObject responseJson = JSONUtil.parseObj(responseBody);
                    if (responseJson.getBool("success", false)) {
                        int count = responseJson.getInt("total", 0);
                        if (count > 0) {
                            realContentTypes.put(contentType, count);
                            totalRealChunks += count;
                            log.info("Real-time count for {}: {}", contentType, count);
                        } else {
                            log.debug("No items found for content type: {}", contentType);
                        }
                    } else {
                        log.warn("Unsuccessful response for {}: {}", contentType, responseJson);
                    }
                } else {
                    log.warn("Failed to query {} - HTTP {}: {}", contentType, response.getStatus(), response.body());
                }
            } catch (Exception e) {
                log.warn("Failed to get real-time count for content type {}: {}", contentType, e.getMessage());
            }
        }
        
        // Build analytics with real counts
        JSONObject analytics = new JSONObject();
        JSONObject chunkTypes = new JSONObject();
        List<String> keyTopics = new ArrayList<>();
        Set<Integer> allPages = new HashSet<>();
        
        int totalDocuments = documents.size();
        long totalDbChunks = 0;
        
        // Still get chunk types and pages from database stats
        for (RagDocument doc : documents) {
            totalDbChunks += doc.getTotalChunks() != null ? doc.getTotalChunks() : 0;
            
            if (StrUtil.isNotBlank(doc.getProcessingStats())) {
                try {
                    JSONObject stats = JSONUtil.parseObj(doc.getProcessingStats());
                    
                    // Aggregate chunk types from DB
                    if (stats.containsKey("chunk_types")) {
                        JSONObject types = stats.getJSONObject("chunk_types");
                        for (String key : types.keySet()) {
                            int count = types.getInt(key, 0);
                            chunkTypes.put(key, chunkTypes.getInt(key, 0) + count);
                        }
                    }
                    
                    // Collect pages processed
                    if (stats.containsKey("pages_processed")) {
                        JSONArray pages = stats.getJSONArray("pages_processed");
                        if (pages != null) {
                            for (int i = 0; i < pages.size(); i++) {
                                try {
                                    allPages.add(pages.getInt(i));
                                } catch (Exception e) {
                                    // Skip invalid page numbers
                                }
                            }
                        }
                    }
                } catch (Exception e) {
                    log.warn("Failed to parse processing stats for document {}: {}", doc.getDocumentName(), e.getMessage());
                }
            }
        }
        
        // Generate key topics from real content types (sorted by count)
        realContentTypes.entrySet().stream()
                .sorted((e1, e2) -> Integer.compare((Integer)e2.getValue(), (Integer)e1.getValue()))
                .limit(10)
                .forEach(entry -> keyTopics.add(entry.getKey()));
        
        // Generate learning objectives based on real counts
        List<String> learningObjectives = generateRealLearningObjectives(subject, realContentTypes, totalRealChunks);
        
        // Calculate difficulty based on real content
        String avgDifficulty = calculateRealDifficulty(grade, realContentTypes, totalRealChunks, totalDocuments);
        
        // Build final analytics with real-time data
        analytics.put("totalTopics", keyTopics.size());
        analytics.put("contentTypes", realContentTypes);  // Use real-time counts
        analytics.put("chunkTypes", chunkTypes);
        analytics.put("keyTopics", keyTopics);
        analytics.put("avgDifficulty", avgDifficulty);
        analytics.put("learningObjectives", learningObjectives);
        analytics.put("totalDocuments", totalDocuments);
        analytics.put("totalChunks", totalRealChunks);  // Use real total
        analytics.put("totalPages", allPages.size());
        
        // Add a flag to indicate this is real-time data
        analytics.put("isRealTimeData", true);
        analytics.put("dataSource", "Qdrant Vector Database");
        
        if (totalRealChunks == 0) {
            log.warn("No real-time content found in Qdrant for {}-{}. Check if documents are properly processed.", grade, subject);
        } else {
            log.info("Generated analytics with real-time counts for {}-{}: {} topics, {} real chunks from Qdrant", 
                    grade, subject, keyTopics.size(), totalRealChunks);
        }
        
        return analytics;
    }
    
    
    
    @Override
    public Object getContentTypeItems(String grade, String subject, String contentType) {
        log.info("Getting content items for grade: {}, subject: {}, type: {}", grade, subject, contentType);
        
        try {
            // First try to get real data from xiaozhi-server
            try {
                String endpointUrl = xiaozhiServerUrl + "/educational/content/by-type";
                String requestUrl = String.format("%s?grade=%s&subject=%s&content_type=%s&limit=100", 
                    endpointUrl, grade, subject, contentType);
                
                log.info("Querying xiaozhi-server for real content: {}", requestUrl);
                
                HttpResponse response = HttpRequest.get(requestUrl)
                    .timeout(30000) // 30 second timeout
                    .execute();
                
                if (response.isOk()) {
                    String responseBody = response.body();
                    JSONObject responseJson = JSONUtil.parseObj(responseBody);
                    
                    if (responseJson.getBool("success", false)) {
                        List<?> realContentItems = responseJson.get("data", List.class);
                        log.info("Successfully retrieved {} real content items from xiaozhi-server", realContentItems.size());
                        
                        // Clean JSONNull values before returning
                        List<Map<String, Object>> cleanedItems = cleanJSONNullValues(realContentItems);
                        log.info("Cleaned {} content items, removing JSONNull values", cleanedItems.size());
                        
                        // Return cleaned real data from vector database
                        return cleanedItems;
                    } else {
                        String errorMsg = responseJson.getStr("error", "Unknown error from xiaozhi-server");
                        log.error("xiaozhi-server returned error: {}", errorMsg);
                        throw new RenException("Educational content service error: " + errorMsg);
                    }
                } else {
                    log.error("xiaozhi-server request failed with status: {}", response.getStatus());
                    throw new RenException("Educational content service is currently unavailable. HTTP status: " + response.getStatus());
                }
                
            } catch (RenException re) {
                // Re-throw RenException as-is
                throw re;
            } catch (Exception e) {
                log.error("Failed to connect to xiaozhi-server: {}", e.getMessage());
                throw new RenException("Educational content service is currently unavailable. Please ensure xiaozhi-server is running and try again.");
            }
            
        } catch (RenException re) {
            throw re;
        } catch (Exception e) {
            log.error("Error getting content items: {}", e.getMessage(), e);
            throw new RenException("An unexpected error occurred while retrieving content items.");
        }
    }
    
    
    private String generateSampleContent(String contentType, String subject, String documentName, int index) {
        Map<String, Map<String, String[]>> subjectTemplates = new HashMap<>();
        
        // Mathematics templates
        Map<String, String[]> mathsTemplates = new HashMap<>();
        mathsTemplates.put("concept", new String[]{
            "A fundamental understanding of %s involves recognizing patterns and relationships in mathematical structures.",
            "The concept of %s demonstrates how abstract mathematical ideas connect to real-world applications.",
            "Understanding %s requires careful analysis of underlying principles and their practical implications.",
            "The theoretical framework of %s provides a foundation for advanced problem-solving techniques.",
            "Key principles of %s illustrate the interconnected nature of mathematical concepts."
        });
        mathsTemplates.put("example", new String[]{
            "Example: Consider a scenario where %s is applied to solve a practical problem involving calculation.",
            "For instance, when working with %s, we can observe how the solution process follows logical steps.",
            "A practical demonstration of %s shows the step-by-step approach to reaching the correct answer.",
            "Let's examine how %s can be used to solve real-world problems in everyday situations.",
            "This example illustrates the application of %s in a structured problem-solving context."
        });
        mathsTemplates.put("exercise", new String[]{
            "Practice Problem: Apply the principles of %s to solve the following mathematical challenge.",
            "Exercise: Use your understanding of %s to complete this problem set with increasing difficulty.",
            "Challenge yourself with this %s problem that requires critical thinking and analysis.",
            "Solve the following %s exercise to reinforce your understanding of the concept.",
            "Work through this %s problem to develop your problem-solving skills."
        });
        
        // English templates
        Map<String, String[]> englishTemplates = new HashMap<>();
        englishTemplates.put("concept", new String[]{
            "The literary concept of %s explores themes and ideas central to understanding English literature.",
            "Understanding %s helps develop critical reading and analytical skills in English language arts.",
            "The concept of %s in English involves examining language use, style, and meaning in texts.",
            "Literary analysis of %s reveals deeper meanings and cultural significance in English works.",
            "The fundamental idea of %s demonstrates how language conveys meaning and emotion."
        });
        englishTemplates.put("example", new String[]{
            "Example: The text %s illustrates how authors use literary devices to convey meaning.",
            "For instance, in %s, we can see how character development drives the narrative forward.",
            "A practical example of %s shows how vocabulary and grammar work together in communication.",
            "This passage from %s demonstrates effective use of descriptive language and imagery.",
            "The example in %s shows how different writing styles can affect reader comprehension."
        });
        englishTemplates.put("exercise", new String[]{
            "Reading Comprehension: Analyze the themes and characters in %s to improve understanding.",
            "Writing Exercise: Create your own composition inspired by the techniques used in %s.",
            "Vocabulary Challenge: Learn new words and their meanings from the context of %s.",
            "Grammar Practice: Identify and correct language patterns found in %s.",
            "Critical Thinking: Evaluate the author's purpose and message in %s."
        });
        
        // Science templates
        Map<String, String[]> scienceTemplates = new HashMap<>();
        scienceTemplates.put("concept", new String[]{
            "The scientific concept of %s explains natural phenomena through observation and experimentation.",
            "Understanding %s helps us comprehend how the natural world functions and behaves.",
            "The principle of %s demonstrates the relationships between different scientific variables.",
            "Scientific investigation of %s reveals patterns and laws that govern natural processes.",
            "The concept of %s connects theoretical knowledge with practical scientific applications."
        });
        scienceTemplates.put("example", new String[]{
            "Example: The phenomenon of %s can be observed in everyday life and laboratory settings.",
            "For instance, %s demonstrates how scientific principles apply to real-world situations.",
            "A practical example of %s shows the relationship between cause and effect in nature.",
            "This experiment with %s illustrates how scientific method leads to understanding.",
            "The example of %s connects classroom learning with observable natural phenomena."
        });
        scienceTemplates.put("exercise", new String[]{
            "Lab Activity: Investigate %s through hands-on experimentation and observation.",
            "Science Challenge: Apply your knowledge of %s to solve this scientific problem.",
            "Research Project: Explore the real-world applications of %s in modern technology.",
            "Observation Exercise: Record and analyze data related to %s in your environment.",
            "Critical Analysis: Evaluate the evidence supporting theories about %s."
        });
        
        // Add default templates for all subjects
        String[] defaultTemplates = new String[]{
            "Definition: %s is formally defined within the context of this subject area.",
            "The concept of %s encompasses several key components and characteristics.",
            "Understanding %s provides a foundation for further learning in this subject.",
            "The study of %s helps develop critical thinking and analytical skills.",
            "%s represents an important topic that connects to broader subject themes."
        };
        
        // Set up subject templates
        subjectTemplates.put("mathematics", mathsTemplates);
        subjectTemplates.put("english", englishTemplates);
        subjectTemplates.put("science", scienceTemplates);
        
        // Get templates for the subject
        Map<String, String[]> subjectSpecificTemplates = subjectTemplates.get(subject.toLowerCase());
        String[] templates;
        
        if (subjectSpecificTemplates != null && subjectSpecificTemplates.containsKey(contentType)) {
            templates = subjectSpecificTemplates.get(contentType);
        } else {
            // Fallback to default templates
            templates = defaultTemplates;
        }
        
        String template = templates[index % templates.length];
        String topic = documentName.replace(".pdf", "") + " - Section " + (index + 1);
        
        return String.format(template, topic);
    }
    
    private String determineDifficultyForItem(String grade, int index) {
        if (grade.contains("6") || grade.contains("7")) {
            return index < 5 ? "Easy" : index < 15 ? "Medium" : "Hard";
        } else {
            return index < 3 ? "Easy" : index < 10 ? "Medium" : "Hard";
        }
    }
    
    private int determineChapterForItem(String documentName, int index) {
        // Extract chapter number from document name
        if (documentName != null) {
            String lowerDoc = documentName.toLowerCase();
            
            // Handle various chapter patterns: "chapter1", "chapter 1", "ch1", "ch 1", etc.
            String[] chapterPatterns = {"chapter", "ch"};
            for (String pattern : chapterPatterns) {
                if (lowerDoc.contains(pattern)) {
                    // Find the position of the pattern
                    int patternIndex = lowerDoc.indexOf(pattern);
                    String afterPattern = lowerDoc.substring(patternIndex + pattern.length());
                    
                    // Extract first number after the pattern (skip spaces and special chars)
                    StringBuilder numberStr = new StringBuilder();
                    for (char c : afterPattern.toCharArray()) {
                        if (Character.isDigit(c)) {
                            numberStr.append(c);
                        } else if (numberStr.length() > 0) {
                            // Stop at first non-digit after we've started collecting digits
                            break;
                        }
                    }
                    
                    if (numberStr.length() > 0) {
                        try {
                            int chapterNum = Integer.parseInt(numberStr.toString());
                            if (chapterNum > 0 && chapterNum <= 50) { // Reasonable chapter range
                                return chapterNum;
                            }
                        } catch (NumberFormatException e) {
                            // Continue to next pattern
                        }
                    }
                }
            }
            
            // Try to extract any number from document name (fallback)
            String[] parts = documentName.split("\\D+");
            for (String part : parts) {
                if (!part.isEmpty() && part.length() <= 2) {
                    try {
                        int num = Integer.parseInt(part);
                        if (num > 0 && num <= 50) { // Reasonable chapter range
                            return num;
                        }
                    } catch (NumberFormatException e) {
                        // Continue to next part
                    }
                }
            }
        }
        
        // Default: distribute items across chapters based on index
        return (index / 10) + 1; // Every 10 items = new chapter
    }
    
    private void validateFile(MultipartFile file) {
        if (file == null || file.isEmpty()) {
            throw new RenException("File is empty");
        }
        
        String fileName = file.getOriginalFilename();
        if (fileName == null || !fileName.toLowerCase().endsWith(".pdf")) {
            throw new RenException("Only PDF files are supported");
        }
        
        if (file.getSize() > maxFileSize) {
            throw new RenException("File size exceeds maximum limit of " + (maxFileSize / 1024 / 1024) + "MB");
        }
    }
    
    private String saveFile(MultipartFile file, String grade, String subject) {
        try {
            // Handle relative path properly by resolving from current working directory
            File baseDir = new File(uploadPath).getAbsoluteFile();
            if (!baseDir.exists()) {
                boolean created = baseDir.mkdirs();
                log.info("Created base directory: {} - Success: {}", baseDir.getAbsolutePath(), created);
            }
            
            // Create directory structure
            File gradeDir = new File(baseDir, grade);
            File subjectDir = new File(gradeDir, subject);
            if (!subjectDir.exists()) {
                boolean created = subjectDir.mkdirs();
                log.info("Created subject directory: {} - Success: {}", subjectDir.getAbsolutePath(), created);
            }
            
            // Generate unique filename
            String fileName = IdUtil.simpleUUID() + "_" + file.getOriginalFilename();
            File targetFile = new File(subjectDir, fileName);
            
            log.info("Saving file to: {}", targetFile.getAbsolutePath());
            
            // Use getAbsoluteFile() to ensure transferTo works correctly
            file.transferTo(targetFile.getAbsoluteFile());
            
            log.info("File saved successfully: {}", targetFile.getAbsolutePath());
            
            return targetFile.getAbsolutePath();
        } catch (IOException e) {
            log.error("Failed to save file to disk: {}", e.getMessage(), e);
            throw new RenException("Failed to save file: " + e.getMessage(), e);
        } catch (Exception e) {
            log.error("Unexpected error while saving file: {}", e.getMessage(), e);
            throw new RenException("Failed to save file: " + e.getMessage(), e);
        }
    }
    
    private void processDocumentAsync(RagDocument document) {
        try {
            log.info("Processing document: {}", document.getDocumentName());
            log.info("Calling URL: {}", xiaozhiServerUrl + "/educational/document/upload");
            
            // Call xiaozhi-server to process document
            String url = xiaozhiServerUrl + "/educational/document/upload";
            
            File file = new File(document.getFilePath());
            log.info("Uploading file: {} (exists: {})", file.getAbsolutePath(), file.exists());
            
            HttpResponse response = HttpRequest.post(url)
                    .form("file", file)
                    .form("grade", document.getGrade())
                    .form("subject", document.getSubject())
                    .form("documentName", document.getDocumentName())
                    .timeout(120000) // 2 minutes timeout
                    .execute();
            
            log.info("Response status: {}, body length: {}", response.getStatus(), response.body().length());
            
            if (response.isOk()) {
                String responseBody = response.body();
                log.info("Processing response body: {}", responseBody);
                JSONObject result = JSONUtil.parseObj(responseBody);
                
                // Update document with processing results
                document.setStatus("PROCESSED");
                document.setProcessedTime(LocalDateTime.now());
                
                // Extract chunk counts from statistics object
                if (result.containsKey("statistics")) {
                    JSONObject statistics = result.getJSONObject("statistics");
                    Integer totalChunks = statistics.getInt("total_chunks", 0);
                    Integer processedChunks = statistics.getInt("embeddings_generated", 0);
                    
                    log.info("Extracted chunks - Total: {}, Processed: {}", totalChunks, processedChunks);
                    
                    document.setTotalChunks(totalChunks);
                    document.setProcessedChunks(processedChunks);
                    document.setProcessingStats(statistics.toString());
                } else {
                    log.warn("No statistics object found in response, using fallback parsing");
                    // Fallback to direct fields if statistics not present
                    document.setTotalChunks(result.getInt("totalChunks", 0));
                    document.setProcessedChunks(result.getInt("processedChunks", 0));
                }
                
                log.info("Final document status - Total chunks: {}, Processed chunks: {}", 
                        document.getTotalChunks(), document.getProcessedChunks());
            } else {
                document.setStatus("FAILED");
                document.setProcessingError("Processing failed: " + response.getStatus());
            }
            
        } catch (Exception e) {
            log.error("Failed to process document: {}", document.getDocumentName(), e);
            document.setStatus("FAILED");
            document.setProcessingError(e.getMessage());
        } finally {
            updateById(document);
        }
    }
    
    private DocumentInfoVO convertToVO(RagDocument document) {
        DocumentInfoVO vo = new DocumentInfoVO();
        vo.setId(document.getId());
        vo.setDocumentName(document.getDocumentName());
        vo.setFileName(document.getFileName());
        vo.setGrade(document.getGrade());
        vo.setSubject(document.getSubject());
        vo.setFileSize(document.getFileSize());
        vo.setFilePath(document.getFilePath());
        vo.setStatus(document.getStatus());
        vo.setTotalChunks(document.getTotalChunks());
        vo.setProcessedChunks(document.getProcessedChunks());
        vo.setProcessingError(document.getProcessingError());
        vo.setUploadTime(document.getUploadTime());
        vo.setProcessedTime(document.getProcessedTime());
        vo.setDescription(document.getDescription());
        vo.setTags(document.getTags());
        
        // Parse processing stats if available
        if (StrUtil.isNotBlank(document.getProcessingStats())) {
            try {
                JSONObject stats = JSONUtil.parseObj(document.getProcessingStats());
                DocumentInfoVO.ProcessingStats processingStats = new DocumentInfoVO.ProcessingStats();
                processingStats.setTextChunks(stats.getInt("textChunks", 0));
                processingStats.setTableChunks(stats.getInt("tableChunks", 0));
                processingStats.setImageChunks(stats.getInt("imageChunks", 0));
                processingStats.setTotalPages(stats.getInt("totalPages", 0));
                processingStats.setContentCategories(stats.getStr("contentCategories"));
                vo.setProcessingStats(processingStats);
            } catch (Exception e) {
                log.error("Failed to parse processing stats", e);
            }
        }
        
        return vo;
    }
    
    /**
     * Generate learning objectives based on real content analysis
     */
    private List<String> generateRealLearningObjectives(String subject, JSONObject contentTypes, long totalChunks) {
        List<String> objectives = new ArrayList<>();
        
        // Base objectives by subject
        switch (subject.toLowerCase()) {
            case "mathematics":
                objectives.add("Master mathematical concepts and principles");
                if (contentTypes.containsKey("example")) {
                    objectives.add("Apply mathematical methods through " + contentTypes.getInt("example", 0) + " worked examples");
                }
                if (contentTypes.containsKey("exercise")) {
                    objectives.add("Practice problem-solving with " + contentTypes.getInt("exercise", 0) + " exercises");
                }
                if (contentTypes.containsKey("definition")) {
                    objectives.add("Learn " + contentTypes.getInt("definition", 0) + " key mathematical definitions");
                }
                break;
            case "science":
                objectives.add("Understand scientific concepts and phenomena");
                if (contentTypes.containsKey("concept")) {
                    objectives.add("Explore " + contentTypes.getInt("concept", 0) + " scientific concepts");
                }
                if (contentTypes.containsKey("experiment")) {
                    objectives.add("Learn through practical experiments and observations");
                }
                break;
            default:
                objectives.add("Master key concepts in " + subject);
                if (!contentTypes.isEmpty()) {
                    objectives.add("Learn through " + totalChunks + " structured content pieces");
                }
        }
        
        return objectives;
    }
    
    /**
     * Calculate difficulty based on real content analysis
     */
    private String calculateRealDifficulty(String grade, JSONObject contentTypes, long totalChunks, int totalDocuments) {
        try {
            int gradeNum = Integer.parseInt(grade.replaceAll("[^0-9]", ""));
            
            // Base difficulty on grade
            String baseDifficulty;
            if (gradeNum <= 6) {
                baseDifficulty = "Easy";
            } else if (gradeNum <= 8) {
                baseDifficulty = "Medium";
            } else {
                baseDifficulty = "Hard";
            }
            
            // Adjust based on content complexity
            int complexityScore = 0;
            complexityScore += contentTypes.getInt("definition", 0) * 1;     // Definitions are basic
            complexityScore += contentTypes.getInt("concept", 0) * 2;       // Concepts are moderate
            complexityScore += contentTypes.getInt("example", 0) * 2;       // Examples are moderate  
            complexityScore += contentTypes.getInt("exercise", 0) * 3;      // Exercises are complex
            complexityScore += contentTypes.getInt("theorem", 0) * 4;       // Theorems are most complex
            
            // Adjust difficulty if content complexity doesn't match grade level
            double avgComplexity = totalChunks > 0 ? (double) complexityScore / totalChunks : 2.0;
            
            if (avgComplexity > 2.5 && baseDifficulty.equals("Easy")) {
                return "Medium";
            } else if (avgComplexity > 3.0 && baseDifficulty.equals("Medium")) {
                return "Hard";
            }
            
            return baseDifficulty;
            
        } catch (Exception e) {
            log.warn("Failed to calculate real difficulty: {}", e.getMessage());
            return "Medium";
        }
    }

    /**
     * Clean JSONNull values from the response data to prevent Jackson serialization errors
     */
    @SuppressWarnings("unchecked")
    private List<Map<String, Object>> cleanJSONNullValues(List<?> items) {
        List<Map<String, Object>> cleanedItems = new ArrayList<>();
        
        for (Object item : items) {
            if (item instanceof Map) {
                Map<String, Object> cleanedItem = new HashMap<>();
                Map<String, Object> originalItem = (Map<String, Object>) item;
                
                for (Map.Entry<String, Object> entry : originalItem.entrySet()) {
                    Object value = entry.getValue();
                    
                    // Replace JSONNull with actual null or appropriate default
                    if (value != null && value.getClass().getSimpleName().equals("JSONNull")) {
                        cleanedItem.put(entry.getKey(), null);
                    } else if (value instanceof List) {
                        // Recursively clean lists
                        cleanedItem.put(entry.getKey(), cleanJSONNullValues((List<?>) value));
                    } else if (value instanceof Map) {
                        // Recursively clean nested maps
                        List<Map<String, Object>> nestedList = new ArrayList<>();
                        nestedList.add((Map<String, Object>) value);
                        List<Map<String, Object>> cleanedNested = cleanJSONNullValues(nestedList);
                        cleanedItem.put(entry.getKey(), cleanedNested.isEmpty() ? new HashMap<>() : cleanedNested.get(0));
                    } else {
                        cleanedItem.put(entry.getKey(), value);
                    }
                }
                cleanedItems.add(cleanedItem);
            }
        }
        
        return cleanedItems;
    }
}