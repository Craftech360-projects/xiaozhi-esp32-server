package xiaozhi.modules.device.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import lombok.Data;

import java.io.Serializable;

@Data
@Schema(description = "Remote play request")
public class RemotePlayDTO implements Serializable {
    private static final long serialVersionUID = 1L;

    @Schema(description = "Device MAC address")
    @NotBlank(message = "Device MAC address is required")
    private String deviceMacAddress;

    @Schema(description = "Content title to play")
    @NotBlank(message = "Content title is required")
    private String contentTitle;

    @Schema(description = "Content type (music/story)")
    private String contentType = "music";
}