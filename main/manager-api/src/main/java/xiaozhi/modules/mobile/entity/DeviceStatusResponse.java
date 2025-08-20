package xiaozhi.modules.mobile.entity;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * Device status response for mobile app
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Schema(description = "Device activation status")
public class DeviceStatusResponse {

    @Schema(description = "Activation ID", example = "uuid-string")
    private String activationId;

    @Schema(description = "Activation status", example = "active", allowableValues = {"pending", "active", "inactive", "error"})
    private String status;

    @Schema(description = "Device is currently online", example = "true")
    private Boolean deviceOnline;

    @Schema(description = "Device last seen timestamp")
    private LocalDateTime deviceLastSeen;

    @Schema(description = "Sync status with Railway backend", example = "connected", allowableValues = {"connected", "disconnected", "syncing", "error"})
    private String syncStatus;

    @Schema(description = "Last successful sync timestamp")
    private LocalDateTime lastSync;

    @Schema(description = "Total conversations synced", example = "156")
    private Integer totalConversationsSynced;

    @Schema(description = "Last conversation timestamp")
    private LocalDateTime lastConversationTimestamp;

    @Schema(description = "Any sync errors")
    private String syncErrors;
}