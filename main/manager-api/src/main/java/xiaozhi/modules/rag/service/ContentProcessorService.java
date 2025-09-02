package xiaozhi.modules.rag.service;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import xiaozhi.modules.rag.entity.RagContentChunkEntity;
import xiaozhi.modules.rag.dao.RagContentChunkDao;

import java.util.List;
import java.util.ArrayList;
import java.util.Map;
import java.util.HashMap;
import java.util.regex.Pattern;
import java.util.regex.Matcher;
import java.util.concurrent.CompletableFuture;
import java.math.BigDecimal;

/**
 * Hierarchical Content Processor for Educational Content
 * Implements 3-level chunking strategy with content type classification
 * Optimized for Standard 6 Mathematics NCERT textbook processing
 * 
 * @author Claude
 * @since 1.0.0
 */
@Slf4j
@Service
public class ContentProcessorService {
    
    @Autowired
    private RagContentChunkDao contentChunkDao;
    
    // Content type patterns for mathematical content
    private static final Pattern CONCEPT_PATTERN = Pattern.compile(
        "(?i)(definition|concept|property|rule|formula|theorem|principle|remember|note)"
    );
    
    private static final Pattern EXAMPLE_PATTERN = Pattern.compile(
        "(?i)(example|let us|consider|suppose|illustration|case study|problem solving)"
    );
    
    private static final Pattern EXERCISE_PATTERN = Pattern.compile(
        "(?i)(exercise|question|problem|practice|solve|find|calculate|determine|answer|solution)"
    );
    
    private static final Pattern CHAPTER_PATTERN = Pattern.compile(
        "(?i)^\\s*chapter\\s+([0-9]+)[:\\-\\s]+(.*?)$", Pattern.MULTILINE
    );
    
    private static final Pattern SECTION_PATTERN = Pattern.compile(
        "(?i)^\\s*([0-9]+\\.?[0-9]*)[\\s\\-]+(.*?)$", Pattern.MULTILINE
    );
    
    // Educational keywords for mathematics
    private static final String[] MATH_KEYWORDS = {
        "number", "arithmetic", "algebra", "geometry", "fraction", "decimal", "ratio", "proportion",
        "percentage", "area", "perimeter", "volume", "measurement", "data", "statistics", "graph",
        "equation", "expression", "factor", "multiple", "prime", "composite", "whole number"
    };
    
    /**
     * Process educational content with hierarchical chunking strategy
     */
    public CompletableFuture<List<RagContentChunkEntity>> processEducationalContent(
            Long textbookId, String content, Map<String, Object> metadata) {
        
        return CompletableFuture.supplyAsync(() -> {
            try {
                log.info("Processing educational content for textbook ID: {} with {} characters", 
                        textbookId, content.length());
                
                List<RagContentChunkEntity> allChunks = new ArrayList<>();
                int globalChunkIndex = 0; // Global counter to ensure unique chunk IDs
                
                // Extract document structure
                Map<String, Object> documentStructure = extractDocumentStructure(content);
                
                // Level 1: Large chunks (512 tokens) - Preserve chapter/section structure
                List<String> level1Chunks = createLevel1Chunks(content, 512);
                log.info("Created {} Level 1 chunks (512 tokens)", level1Chunks.size());
                
                for (int i = 0; i < level1Chunks.size(); i++) {
                    String chunk = level1Chunks.get(i);
                    
                    // Create Level 1 chunk entity
                    RagContentChunkEntity level1Chunk = createChunkEntity(
                        textbookId, chunk, metadata, 1, globalChunkIndex++, documentStructure
                    );
                    allChunks.add(level1Chunk);
                    
                    // Level 2: Medium chunks (256 tokens) - Preserve concept boundaries
                    List<String> level2Chunks = createLevel2Chunks(chunk, 256);
                    
                    for (int j = 0; j < level2Chunks.size(); j++) {
                        String subChunk = level2Chunks.get(j);
                        
                        RagContentChunkEntity level2Chunk = createChunkEntity(
                            textbookId, subChunk, metadata, 2, globalChunkIndex++, documentStructure
                        );
                        level2Chunk.setParentChunkId(level1Chunk.getChunkId());
                        allChunks.add(level2Chunk);
                        
                        // Level 3: Small chunks (128 tokens) - Fine-grained search
                        List<String> level3Chunks = createLevel3Chunks(subChunk, 128);
                        
                        for (int k = 0; k < level3Chunks.size(); k++) {
                            String smallChunk = level3Chunks.get(k);
                            
                            RagContentChunkEntity level3Chunk = createChunkEntity(
                                textbookId, smallChunk, metadata, 3, globalChunkIndex++, documentStructure
                            );
                            level3Chunk.setParentChunkId(level2Chunk.getChunkId());
                            allChunks.add(level3Chunk);
                        }
                    }
                }
                
                log.info("Successfully processed content into {} total chunks", allChunks.size());
                
                // Store all chunks in database
                for (RagContentChunkEntity chunk : allChunks) {
                    contentChunkDao.insert(chunk);
                }
                
                log.info("Stored {} chunks in database for textbook ID: {}", allChunks.size(), textbookId);
                return allChunks;
                
            } catch (Exception e) {
                log.error("Error processing educational content for textbook ID: {}", textbookId, e);
                throw new RuntimeException("Content processing failed", e);
            }
        });
    }
    
    /**
     * Extract document structure for metadata enrichment
     */
    private Map<String, Object> extractDocumentStructure(String content) {
        Map<String, Object> structure = new HashMap<>();
        
        // Extract chapter information
        Matcher chapterMatcher = CHAPTER_PATTERN.matcher(content);
        List<Map<String, String>> chapters = new ArrayList<>();
        
        while (chapterMatcher.find()) {
            Map<String, String> chapter = new HashMap<>();
            chapter.put("number", chapterMatcher.group(1));
            chapter.put("title", chapterMatcher.group(2).trim());
            chapters.add(chapter);
        }
        
        structure.put("chapters", chapters);
        
        // Extract section information
        Matcher sectionMatcher = SECTION_PATTERN.matcher(content);
        List<Map<String, String>> sections = new ArrayList<>();
        
        while (sectionMatcher.find()) {
            Map<String, String> section = new HashMap<>();
            section.put("number", sectionMatcher.group(1));
            section.put("title", sectionMatcher.group(2).trim());
            sections.add(section);
        }
        
        structure.put("sections", sections);
        
        return structure;
    }
    
    /**
     * Create Level 1 chunks with chapter/section preservation
     */
    private List<String> createLevel1Chunks(String content, int maxTokens) {
        List<String> chunks = new ArrayList<>();
        
        // Smart chunking that preserves educational structure
        String[] paragraphs = content.split("\n\n+");
        StringBuilder currentChunk = new StringBuilder();
        
        for (String paragraph : paragraphs) {
            // Estimate token count (rough approximation: 1 token ≈ 4 characters)
            int estimatedTokens = (currentChunk.length() + paragraph.length()) / 4;
            
            if (estimatedTokens > maxTokens && currentChunk.length() > 0) {
                chunks.add(currentChunk.toString().trim());
                currentChunk = new StringBuilder(paragraph);
            } else {
                if (currentChunk.length() > 0) {
                    currentChunk.append("\n\n");
                }
                currentChunk.append(paragraph);
            }
        }
        
        if (currentChunk.length() > 0) {
            chunks.add(currentChunk.toString().trim());
        }
        
        return chunks;
    }
    
    /**
     * Create Level 2 chunks with concept boundary preservation
     */
    private List<String> createLevel2Chunks(String content, int maxTokens) {
        List<String> chunks = new ArrayList<>();
        
        // Split by sentences while preserving mathematical concepts
        String[] sentences = content.split("(?<=[.!?])\\s+");
        StringBuilder currentChunk = new StringBuilder();
        
        for (String sentence : sentences) {
            int estimatedTokens = (currentChunk.length() + sentence.length()) / 4;
            
            if (estimatedTokens > maxTokens && currentChunk.length() > 0) {
                chunks.add(currentChunk.toString().trim());
                currentChunk = new StringBuilder(sentence);
            } else {
                if (currentChunk.length() > 0) {
                    currentChunk.append(" ");
                }
                currentChunk.append(sentence);
            }
        }
        
        if (currentChunk.length() > 0) {
            chunks.add(currentChunk.toString().trim());
        }
        
        return chunks;
    }
    
    /**
     * Create Level 3 chunks for fine-grained search
     */
    private List<String> createLevel3Chunks(String content, int maxTokens) {
        List<String> chunks = new ArrayList<>();
        
        // Simple word-based chunking for fine-grained retrieval
        String[] words = content.split("\\s+");
        StringBuilder currentChunk = new StringBuilder();
        int wordCount = 0;
        int targetWords = maxTokens; // Approximate 1:1 ratio for fine chunks
        
        for (String word : words) {
            if (wordCount >= targetWords && currentChunk.length() > 0) {
                chunks.add(currentChunk.toString().trim());
                currentChunk = new StringBuilder(word);
                wordCount = 1;
            } else {
                if (currentChunk.length() > 0) {
                    currentChunk.append(" ");
                }
                currentChunk.append(word);
                wordCount++;
            }
        }
        
        if (currentChunk.length() > 0) {
            chunks.add(currentChunk.toString().trim());
        }
        
        return chunks;
    }
    
    /**
     * Create chunk entity with educational metadata
     */
    private RagContentChunkEntity createChunkEntity(
            Long textbookId, String content, Map<String, Object> metadata, 
            int chunkLevel, int chunkIndex, Map<String, Object> documentStructure) {
        
        RagContentChunkEntity chunk = new RagContentChunkEntity();
        chunk.setTextbookId(textbookId);
        chunk.setChunkLevel(String.valueOf(chunkLevel));
        chunk.setChunkId("chunk_" + textbookId + "_" + chunkLevel + "_" + chunkIndex);
        chunk.setVectorId("vec_" + textbookId + "_" + chunkLevel + "_" + chunkIndex);
        chunk.setCollectionName("mathematics_std6");
        chunk.setChunkText(content);
        chunk.setChunkTokens(estimateTokenCount(content));
        
        // Set basic metadata (will be handled through separate metadata tracking)
        // Subject, standard, chapter info is stored in the textbook metadata table
        
        // Classify chunk type (educational purpose)
        String chunkType = classifyChunkType(content);
        chunk.setChunkType(chunkType);
        
        // Classify content type (data format)
        String contentType = classifyContentFormat(content);
        chunk.setContentType(contentType);
        
        // Extract educational metadata
        chunk.setDifficultyLevel(estimateDifficultyLevel(content, chunkType));
        chunk.setImportanceScore(BigDecimal.valueOf(calculateImportanceScore(content, chunkType)));
        
        // Extract mathematical keywords (as JSON array)
        List<String> keywords = extractMathematicalKeywords(content);
        chunk.setKeywords(convertToJsonArray(keywords));
        
        // Set topics based on content analysis (as JSON array)
        List<String> topics = identifyMathematicalTopics(content);
        chunk.setTopics(convertToJsonArray(topics));
        
        return chunk;
    }
    
    /**
     * Classify chunk type (educational purpose)
     * Returns: 'concept', 'example', 'exercise', 'definition', 'theorem', 'formula', 'diagram_description'
     */
    private String classifyChunkType(String content) {
        if (EXERCISE_PATTERN.matcher(content).find()) {
            return "exercise";
        } else if (EXAMPLE_PATTERN.matcher(content).find()) {
            return "example";
        } else if (CONCEPT_PATTERN.matcher(content).find()) {
            return "concept";
        } else {
            return "concept"; // Default to concept for educational content
        }
    }
    
    /**
     * Classify content type (data format)
     * Returns: 'text', 'formula', 'diagram_description', 'mixed'
     */
    private String classifyContentFormat(String content) {
        // Check for mathematical formulas (equations, expressions)
        if (content.matches(".*[+\\-×÷=<>≤≥∑∏∫√].*") || 
            content.matches(".*\\b\\d+\\s*[+\\-×÷]\\s*\\d+.*") ||
            content.matches(".*\\b[a-z]\\s*[=+\\-].*")) {
            return "formula";
        }
        
        // Check for diagram descriptions
        if (content.toLowerCase().matches(".*(figure|diagram|graph|chart|illustration|picture|image).*")) {
            return "diagram_description";
        }
        
        // Check for mixed content (both text and formulas)
        if (content.length() > 200 && 
            (content.matches(".*[+\\-×÷=].*") || content.toLowerCase().contains("formula"))) {
            return "mixed";
        }
        
        // Default to text
        return "text";
    }
    
    /**
     * Estimate difficulty level for Standard 6
     */
    private String estimateDifficultyLevel(String content, String chunkType) {
        // Simple heuristic based on mathematical complexity
        // Returns: 'basic', 'intermediate', 'advanced' (matching database ENUM)
        if (content.matches(".*(?i)(advanced|complex|difficult|challenging).*")) {
            return "advanced";
        } else if (content.matches(".*(?i)(basic|simple|easy|fundamental).*")) {
            return "basic";
        } else {
            return "intermediate";
        }
    }
    
    /**
     * Calculate importance score based on content characteristics
     */
    private Double calculateImportanceScore(String content, String chunkType) {
        double score = 0.5; // Base score
        
        // Boost score based on chunk type
        switch (chunkType) {
            case "concept":
                score += 0.3;
                break;
            case "example":
                score += 0.2;
                break;
            case "exercise":
                score += 0.1;
                break;
        }
        
        // Boost for mathematical keywords
        for (String keyword : MATH_KEYWORDS) {
            if (content.toLowerCase().contains(keyword)) {
                score += 0.05;
            }
        }
        
        // Cap at 1.0
        return Math.min(score, 1.0);
    }
    
    /**
     * Extract mathematical keywords from content
     */
    private List<String> extractMathematicalKeywords(String content) {
        List<String> keywords = new ArrayList<>();
        String lowerContent = content.toLowerCase();
        
        for (String keyword : MATH_KEYWORDS) {
            if (lowerContent.contains(keyword)) {
                keywords.add(keyword);
            }
        }
        
        // Add numbers if present
        if (content.matches(".*\\d+.*")) {
            keywords.add("numbers");
        }
        
        return keywords;
    }
    
    /**
     * Identify mathematical topics from content
     */
    private List<String> identifyMathematicalTopics(String content) {
        List<String> topics = new ArrayList<>();
        String lowerContent = content.toLowerCase();
        
        // Topic identification based on content analysis
        if (lowerContent.matches(".*(whole number|natural number|counting).*")) {
            topics.add("number_systems");
        }
        if (lowerContent.matches(".*(addition|subtraction|multiplication|division).*")) {
            topics.add("arithmetic_operations");
        }
        if (lowerContent.matches(".*(fraction|decimal|percentage).*")) {
            topics.add("fractions_decimals");
        }
        if (lowerContent.matches(".*(area|perimeter|length|width|height).*")) {
            topics.add("mensuration");
        }
        if (lowerContent.matches(".*(ratio|proportion|unitary method).*")) {
            topics.add("ratio_proportion");
        }
        if (lowerContent.matches(".*(algebra|expression|equation|variable).*")) {
            topics.add("algebra");
        }
        if (lowerContent.matches(".*(geometry|triangle|circle|square|rectangle).*")) {
            topics.add("geometry");
        }
        if (lowerContent.matches(".*(data|graph|chart|statistics).*")) {
            topics.add("data_handling");
        }
        
        if (topics.isEmpty()) {
            topics.add("general_mathematics");
        }
        
        return topics;
    }
    
    /**
     * Convert a list of strings to JSON array format
     */
    private String convertToJsonArray(List<String> items) {
        if (items == null || items.isEmpty()) {
            return "[]";
        }
        
        StringBuilder json = new StringBuilder("[");
        for (int i = 0; i < items.size(); i++) {
            if (i > 0) json.append(",");
            json.append("\"").append(items.get(i).replace("\"", "\\\"")).append("\"");
        }
        json.append("]");
        return json.toString();
    }
    
    /**
     * Estimate token count from text
     */
    private Integer estimateTokenCount(String content) {
        // Rough approximation: 1 token ≈ 4 characters for English text
        return content.length() / 4;
    }
}