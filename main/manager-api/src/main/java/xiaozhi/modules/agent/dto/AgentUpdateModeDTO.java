package xiaozhi.modules.agent.dto;

import java.io.Serializable;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import lombok.Data;

/**
 * 智能体模式更新DTO
 * 用于根据模板名称更新智能体配置
 */
@Data
@Schema(description = "智能体模式更新对象")
public class AgentUpdateModeDTO implements Serializable {
    private static final long serialVersionUID = 1L;

    @Schema(description = "智能体ID", example = "abc123def456", required = true)
    @NotBlank(message = "智能体ID不能为空")
    private String agentId;

    @Schema(description = "模板模式名称", example = "Cheeko", required = true)
    @NotBlank(message = "模式名称不能为空")
    private String modeName;
}
