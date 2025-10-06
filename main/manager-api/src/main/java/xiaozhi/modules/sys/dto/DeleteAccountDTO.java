package xiaozhi.modules.sys.dto;

import java.io.Serializable;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import lombok.Data;

/**
 * 删除账户DTO
 */
@Data
@Schema(description = "删除账户")
public class DeleteAccountDTO implements Serializable {

    @Schema(description = "用户名/手机号")
    @NotBlank(message = "{sysuser.username.require}")
    private String username;

}
