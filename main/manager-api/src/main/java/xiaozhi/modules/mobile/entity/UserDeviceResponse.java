package xiaozhi.modules.mobile.entity;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.List;

/**
 * User device response for mobile app
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Schema(description = "User's activated device information")
public class UserDeviceResponse {

    @Schema(description = "Activation ID", example = "uuid-string")
    private String activationId;

    @Schema(description = "Child's name", example = "Emma")
    private String childName;

    @Schema(description = "Child's age", example = "5")
    private Integer childAge;

    @Schema(description = "Child's interests", example = "[\"animals\", \"stories\", \"counting\"]")
    private List<String> childInterests;

    @Schema(description = "Toy model", example = "CHEEKO-V1")
    private String toyModel;

    @Schema(description = "Toy serial number", example = "CHEEKO-20250816-000001")
    private String toySerialNumber;

    @Schema(description = "Device MAC address", example = "68:25:dd:bc:03:7c")
    private String deviceMac;

    @Schema(description = "Activation status", example = "active")
    private String activationStatus;

    @Schema(description = "Device is currently online", example = "true")
    private Boolean deviceOnline;

    @Schema(description = "Device last seen timestamp")
    private LocalDateTime deviceLastSeen;

    @Schema(description = "Device activation timestamp")
    private LocalDateTime activatedAt;

    @Schema(description = "Last activity timestamp")
    private LocalDateTime lastActivity;

    @Schema(description = "Total conversations this week", example = "45")
    private Integer weekConversations;

    @Schema(description = "Total minutes this week", example = "120")
    private Integer weekMinutes;
}