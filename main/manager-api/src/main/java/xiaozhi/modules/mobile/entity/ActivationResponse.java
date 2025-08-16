package xiaozhi.modules.mobile.entity;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * Device activation response
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Schema(description = "Device activation response")
public class ActivationResponse {

    @Schema(description = "Activation was successful", example = "true")
    private Boolean success;

    @Schema(description = "Unique activation ID", example = "uuid-string")
    private String activationId;

    @Schema(description = "Toy serial number", example = "CHEEKO-20250816-000001")
    private String toySerialNumber;

    @Schema(description = "Toy model", example = "CHEEKO-V1")
    private String toyModel;

    @Schema(description = "Device MAC address", example = "68:25:dd:bc:03:7c")
    private String deviceMac;

    @Schema(description = "Success message", example = "Device activated successfully")
    private String message;

    // Static factory methods for common responses
    public static ActivationResponse success(String activationId, String toySerialNumber, 
                                           String toyModel, String deviceMac) {
        return ActivationResponse.builder()
                .success(true)
                .activationId(activationId)
                .toySerialNumber(toySerialNumber)
                .toyModel(toyModel)
                .deviceMac(deviceMac)
                .message("Device activated successfully")
                .build();
    }

    public static ActivationResponse error(String message) {
        return ActivationResponse.builder()
                .success(false)
                .message(message)
                .build();
    }
}