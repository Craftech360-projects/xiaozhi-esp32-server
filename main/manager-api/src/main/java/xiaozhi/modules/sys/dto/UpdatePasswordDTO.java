package xiaozhi.modules.sys.dto;

import java.io.Serializable;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import lombok.Data;

/**
 * 更新密码DTO (不需要旧密码)
 */
@Data
@Schema(description = "更新密码")
public class UpdatePasswordDTO implements Serializable {

    @Schema(description = "用户名/手机号")
    @NotBlank(message = "{sysuser.username.require}")
    private String username;

    @Schema(description = "新密码")
    @NotBlank(message = "{sysuser.password.require}")
    private String newPassword;

}
