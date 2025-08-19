package xiaozhi.modules.mobile.entity;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import jakarta.validation.constraints.*;
import java.util.List;

/**
 * Device activation request from mobile app
 */
@Data
@Schema(description = "Device activation request")
public class ActivationRequest {

    @NotBlank(message = "Activation code is required")
    @Pattern(regexp = "^[0-9]{6}$", message = "Activation code must be exactly 6 digits")
    @Schema(description = "6-digit activation code", example = "123456")
    private String activationCode;

    @NotBlank(message = "Child name is required")
    @Size(max = 100, message = "Child name cannot exceed 100 characters")
    @Schema(description = "Child's name", example = "Emma")
    private String childName;

    @NotNull(message = "Child age is required")
    @Min(value = 3, message = "Child age must be at least 3")
    @Max(value = 12, message = "Child age cannot exceed 12")
    @Schema(description = "Child's age", example = "5")
    private Integer childAge;

    @Size(max = 10, message = "Cannot have more than 10 interests")
    @Schema(description = "Child's interests", example = "[\"animals\", \"stories\", \"counting\"]")
    private List<String> childInterests;

    @Schema(description = "Device MAC address (if known)", example = "68:25:dd:bc:03:7c")
    private String deviceMacAddress;
}