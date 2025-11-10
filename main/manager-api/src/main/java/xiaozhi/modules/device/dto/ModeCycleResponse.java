package xiaozhi.modules.device.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

/**
 * 设备模式切换响应
 */
@Data
@Schema(description = "设备模式切换响应")
public class ModeCycleResponse {

    @Schema(description = "是否成功")
    private boolean success;

    @Schema(description = "设备ID")
    private String deviceId;

    @Schema(description = "旧模式")
    private String oldMode;

    @Schema(description = "新模式")
    private String newMode;

    @Schema(description = "消息")
    private String message;
}
