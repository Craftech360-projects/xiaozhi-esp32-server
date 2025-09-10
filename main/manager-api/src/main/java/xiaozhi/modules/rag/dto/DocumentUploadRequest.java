package xiaozhi.modules.rag.dto;

import lombok.Data;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;

/**
 * Document Upload Request DTO
 */
@Data
public class DocumentUploadRequest {
    
    @NotBlank(message = "Grade is required")
    @Pattern(regexp = "^class-[6-9]|class-10$", message = "Grade must be class-6 to class-10")
    private String grade;
    
    @NotBlank(message = "Subject is required")
    @Pattern(regexp = "^(mathematics|science|english|social-studies|hindi)$", 
             message = "Subject must be one of: mathematics, science, english, social-studies, hindi")
    private String subject;
    
    private String documentName;
    
    private String description;
    
    private String tags;
}