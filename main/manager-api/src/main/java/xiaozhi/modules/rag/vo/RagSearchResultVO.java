package xiaozhi.modules.rag.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.util.List;

/**
 * RAG Search Result VO
 * 
 * @author Claude
 * @since 1.0.0
 */
@Data
@Schema(description = "RAG search results")
public class RagSearchResultVO {
    
    @Schema(description = "Original search query")
    private String query;
    
    @Schema(description = "Number of results found")
    private Integer totalResults;
    
    @Schema(description = "Search results")
    private List<SearchResult> results;
    
    @Schema(description = "Search metadata")
    private SearchMetadata metadata;
    
    @Data
    @Schema(description = "Individual search result")
    public static class SearchResult {
        @Schema(description = "Content text")
        private String content;
        
        @Schema(description = "Relevance score")
        private Float score;
        
        @Schema(description = "Source information")
        private SourceInfo source;
        
        @Schema(description = "Content metadata")
        private ContentMetadata contentMetadata;
        
        @Schema(description = "Highlighted query terms")
        private List<String> highlights;
    }
    
    @Data
    @Schema(description = "Source attribution information")
    public static class SourceInfo {
        @Schema(description = "Subject")
        private String subject;
        
        @Schema(description = "Standard")
        private Integer standard;
        
        @Schema(description = "Chapter title")
        private String chapterTitle;
        
        @Schema(description = "Page number")
        private Integer pageNumber;
        
        @Schema(description = "Section title")
        private String sectionTitle;
    }
    
    @Data
    @Schema(description = "Content metadata")
    public static class ContentMetadata {
        @Schema(description = "Content type")
        private String contentType;
        
        @Schema(description = "Difficulty level")
        private String difficultyLevel;
        
        @Schema(description = "Topics covered")
        private List<String> topics;
        
        @Schema(description = "Keywords")
        private List<String> keywords;
        
        @Schema(description = "Learning objectives")
        private List<String> learningObjectives;
        
        @Schema(description = "Prerequisites")
        private List<String> prerequisites;
    }
    
    @Data
    @Schema(description = "Search metadata")
    public static class SearchMetadata {
        @Schema(description = "Query processing time in milliseconds")
        private Long queryTimeMs;
        
        @Schema(description = "Retrieval time in milliseconds")
        private Long retrievalTimeMs;
        
        @Schema(description = "Number of vectors searched")
        private Integer vectorsSearched;
        
        @Schema(description = "Cache hit")
        private Boolean cacheHit;
        
        @Schema(description = "Detected subject")
        private String detectedSubject;
        
        @Schema(description = "Detected standard")
        private Integer detectedStandard;
    }
}