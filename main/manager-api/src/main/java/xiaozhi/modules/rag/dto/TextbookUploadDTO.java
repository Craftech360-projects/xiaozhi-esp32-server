package xiaozhi.modules.rag.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

/**
 * Textbook Upload DTO
 * 
 * @author Claude
 * @since 1.0.0
 */
@Data
@Schema(description = "Textbook upload request")
public class TextbookUploadDTO {
    
    @NotBlank(message = "Subject is required")
    @Schema(description = "Subject name", example = "mathematics", allowableValues = {"mathematics", "science", "english"})
    private String subject;
    
    @NotNull(message = "Standard is required")
    @Min(value = 1, message = "Standard must be between 1 and 12")
    @Max(value = 12, message = "Standard must be between 1 and 12")
    @Schema(description = "Class standard", example = "6", minimum = "1", maximum = "12")
    private Integer standard;
    
    @NotBlank(message = "Textbook title is required")
    @Schema(description = "Complete textbook title", example = "NCERT Mathematics Textbook for Class VI")
    private String textbookTitle;
    
    @Schema(description = "Content language", example = "English", defaultValue = "English")
    private String language = "English";
    
    @Schema(description = "Academic year/curriculum version", example = "2023-24")
    private String curriculumYear;
    
    @Schema(description = "Chapter number (if processing single chapter)", example = "1")
    private Integer chapterNumber;
    
    @Schema(description = "Chapter title (if processing single chapter)", example = "Knowing Our Numbers")
    private String chapterTitle;
    
    @Schema(description = "Additional processing notes")
    private String notes;
}