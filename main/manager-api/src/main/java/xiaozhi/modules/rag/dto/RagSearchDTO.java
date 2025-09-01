package xiaozhi.modules.rag.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.Max;

/**
 * RAG Search Request DTO
 * 
 * @author Claude
 * @since 1.0.0
 */
@Data
@Schema(description = "RAG search request")
public class RagSearchDTO {
    
    @NotBlank(message = "Query is required")
    @Schema(description = "Search query", example = "What is the area of a rectangle?")
    private String query;
    
    @Schema(description = "Subject filter", example = "mathematics", allowableValues = {"mathematics", "science", "english"})
    private String subject;
    
    @Min(value = 1, message = "Standard must be between 1 and 12")
    @Max(value = 12, message = "Standard must be between 1 and 12")
    @Schema(description = "Standard filter", example = "6", minimum = "1", maximum = "12")
    private Integer standard;
    
    @Schema(description = "Number of results to return", example = "5", minimum = "1", maximum = "20")
    private Integer limit = 5;
    
    @Schema(description = "Minimum relevance score", example = "0.7", minimum = "0.0", maximum = "1.0")
    private Float minScore = 0.7f;
    
    @Schema(description = "Content type filter", allowableValues = {"concept", "example", "exercise", "definition", "theorem"})
    private String contentType;
    
    @Schema(description = "Difficulty level filter", allowableValues = {"basic", "intermediate", "advanced"})
    private String difficultyLevel;
    
    @Schema(description = "Include metadata in response", example = "true")
    private Boolean includeMetadata = true;
    
    @Schema(description = "Include source attribution", example = "true")
    private Boolean includeSource = true;
}