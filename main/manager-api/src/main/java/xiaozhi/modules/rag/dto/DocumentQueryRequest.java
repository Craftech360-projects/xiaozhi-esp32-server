package xiaozhi.modules.rag.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.io.Serializable;

/**
 * Document Query Request DTO
 */
@Data
@Schema(description = "Document Query Parameters")
public class DocumentQueryRequest implements Serializable {
    private static final long serialVersionUID = 1L;
    
    @Schema(description = "Grade filter", example = "class-6")
    private String grade;
    
    @Schema(description = "Subject filter", example = "mathematics")
    private String subject;
    
    @Schema(description = "Document name filter", example = "algebra textbook")
    private String documentName;
    
    @Schema(description = "Processing status filter", example = "PROCESSED")
    private String status;
    
    @Schema(description = "Start date for filtering", example = "2023-01-01")
    private String startDate;
    
    @Schema(description = "End date for filtering", example = "2023-12-31")
    private String endDate;
    
    @Schema(description = "Page number (1-based)", example = "1")
    private Integer page = 1;
    
    @Schema(description = "Number of items per page", example = "20")
    private Integer limit = 20;
    
    /**
     * Validate and set defaults for pagination
     */
    public void validateAndSetDefaults() {
        if (page == null || page < 1) {
            page = 1;
        }
        if (limit == null || limit < 1) {
            limit = 20;
        }
        if (limit > 100) {
            limit = 100; // Maximum limit to prevent abuse
        }
    }
    
    /**
     * Get calculated offset for pagination
     */
    public int getOffset() {
        return (page - 1) * limit;
    }
}