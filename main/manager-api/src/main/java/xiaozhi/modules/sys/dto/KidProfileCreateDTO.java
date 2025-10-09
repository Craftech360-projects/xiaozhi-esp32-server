package xiaozhi.modules.sys.dto;

import java.io.Serializable;
import java.util.Date;

import com.fasterxml.jackson.annotation.JsonFormat;
import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

/**
 * Kid Profile Create DTO
 */
@Data
@Schema(description = "Create Kid Profile Request")
public class KidProfileCreateDTO implements Serializable {
    private static final long serialVersionUID = 1L;

    @Schema(description = "Child name", required = true)
    @NotBlank(message = "Child name cannot be empty")
    private String name;

    @Schema(description = "Date of birth", required = true, example = "2015-10-12")
    @NotNull(message = "Date of birth cannot be empty")
    @JsonFormat(pattern = "yyyy-MM-dd", timezone = "UTC")
    private Date dateOfBirth;

    @Schema(description = "Gender (male/female/other)")
    private String gender;

    @Schema(description = "Interests (JSON array string)")
    private String interests;

    @Schema(description = "Avatar URL")
    private String avatarUrl;
}
