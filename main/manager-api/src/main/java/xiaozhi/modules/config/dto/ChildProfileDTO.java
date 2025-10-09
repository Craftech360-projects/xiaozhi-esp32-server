package xiaozhi.modules.config.dto;

import java.io.Serializable;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

/**
 * Child Profile DTO for LiveKit server
 */
@Data
@Schema(description = "Child Profile for Agent")
public class ChildProfileDTO implements Serializable {
    private static final long serialVersionUID = 1L;

    @Schema(description = "Child name")
    private String name;

    @Schema(description = "Child age")
    private Integer age;

    @Schema(description = "Age group")
    private String ageGroup;

    @Schema(description = "Gender")
    private String gender;

    @Schema(description = "Interests (comma-separated)")
    private String interests;
}
