package xiaozhi.modules.security.controller;

import java.io.IOException;
import java.util.Calendar;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.servlet.http.HttpServletResponse;
import lombok.AllArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import xiaozhi.common.constant.Constant;
import xiaozhi.common.exception.ErrorCode;
import xiaozhi.common.exception.RenException;
import xiaozhi.common.page.TokenDTO;
import xiaozhi.common.user.UserDetail;
import xiaozhi.common.utils.Result;
import xiaozhi.common.validator.AssertUtils;
import xiaozhi.common.validator.ValidatorUtils;
import xiaozhi.modules.security.dto.LoginDTO;
import xiaozhi.modules.security.dto.SmsVerificationDTO;
import xiaozhi.modules.security.password.PasswordUtils;
import xiaozhi.modules.security.service.CaptchaService;
import xiaozhi.modules.security.service.SysUserTokenService;
import xiaozhi.modules.security.user.SecurityUser;
import xiaozhi.modules.sys.dto.PasswordDTO;
import xiaozhi.modules.sys.dto.RetrievePasswordDTO;
import xiaozhi.modules.sys.dto.SysUserDTO;
import xiaozhi.modules.sys.dto.UpdatePasswordDTO;
import xiaozhi.modules.sys.service.SysDictDataService;
import xiaozhi.modules.sys.service.SysParamsService;
import xiaozhi.modules.sys.service.SysUserService;
import xiaozhi.modules.sys.vo.SysDictDataItem;

/**
 * 登录控制层
 */
@Slf4j
@AllArgsConstructor
@RestController
@RequestMapping("/user")
@Tag(name = "Login Management")
public class LoginController {
    private final SysUserService sysUserService;
    private final SysUserTokenService sysUserTokenService;
    private final CaptchaService captchaService;
    private final SysParamsService sysParamsService;
    private final SysDictDataService sysDictDataService;

    @GetMapping("/captcha")
    @Operation(summary = "Captcha")
    public void captcha(HttpServletResponse response, String uuid) throws IOException {
        // uuid不能为空
        AssertUtils.isBlank(uuid, ErrorCode.IDENTIFIER_NOT_NULL);
        // 生成验证码
        captchaService.create(response, uuid);
    }

    @PostMapping("/smsVerification")
    @Operation(summary = "SMS verification code")
    public Result<Void> smsVerification(@RequestBody SmsVerificationDTO dto) {
        // 验证图形验证码
        boolean validate = captchaService.validate(dto.getCaptchaId(), dto.getCaptcha(), true);
        if (!validate) {
            throw new RenException("图形验证码错误");
        }
        Boolean isMobileRegister = sysParamsService
                .getValueObject(Constant.SysMSMParam.SERVER_ENABLE_MOBILE_REGISTER.getValue(), Boolean.class);
        if (!isMobileRegister) {
            throw new RenException("没有开启手机注册，没法使用短信验证码功能");
        }
        // 发送短信验证码
        captchaService.sendSMSValidateCode(dto.getPhone());
        return new Result<>();
    }

    @PostMapping("/login")
    @Operation(summary = "Login")
    public Result<TokenDTO> login(@RequestBody LoginDTO login) {
        // 验证是否正确输入验证码
        boolean validate = captchaService.validate(login.getCaptchaId(), login.getCaptcha(), true);
        if (!validate) {
            throw new RenException("图形验证码错误，请重新获取");
        }
        // 按照用户名获取用户
        SysUserDTO userDTO = sysUserService.getByUsername(login.getUsername());
        // 判断用户是否存在
        if (userDTO == null) {
            throw new RenException("请检测用户和密码是否输入错误");
        }
        // 判断密码是否正确，不一样则进入if
        if (!PasswordUtils.matches(login.getPassword(), userDTO.getPassword())) {
            throw new RenException("请检测用户和密码是否输入错误");
        }
        return sysUserTokenService.createToken(userDTO.getId());
    }

    @PostMapping("/register")

    @Operation(summary = "Register")
    public Result<TokenDTO> register(@RequestBody LoginDTO login) {
      
        if (!sysUserService.getAllowUserRegister()) {
            throw new RenException("当前不允许普通用户注册");
        }
        // 是否开启手机注册
        Boolean isMobileRegister = sysParamsService
                .getValueObject(Constant.SysMSMParam.SERVER_ENABLE_MOBILE_REGISTER.getValue(), Boolean.class);
        boolean validate;
        if (isMobileRegister) {
            // 验证用户是否是手机号码
            boolean validPhone = ValidatorUtils.isValidPhone(login.getUsername());
            if (!validPhone) {
                throw new RenException("用户名不是手机号码，请重新输入");
            }
            // 验证短信验证码是否正常
            validate = captchaService.validateSMSValidateCode(login.getUsername(), login.getMobileCaptcha(), false);
            if (!validate) {
                throw new RenException("手机验证码错误，请重新获取");
            }
        } else {
            // 验证是否正确输入验证码
            validate = captchaService.validate(login.getCaptchaId(), login.getCaptcha(), true);
            if (!validate) {
                throw new RenException("图形验证码错误，请重新获取");
            }
        }

        // 按照用户名获取用户
        SysUserDTO userDTO = sysUserService.getByUsername(login.getUsername());
        if (userDTO != null) {
            throw new RenException("此手机号码已经注册过");
        }
        userDTO = new SysUserDTO();
        userDTO.setUsername(login.getUsername());
        userDTO.setPassword(login.getPassword());
        sysUserService.save(userDTO);
        
        // Get the saved user to get the ID for token creation
        SysUserDTO savedUser = sysUserService.getByUsername(login.getUsername());
        if (savedUser == null) {
            throw new RenException("用户注册失败，请重试");
        }
        
        // Create and return token for the newly registered user
        return sysUserTokenService.createToken(savedUser.getId());
    }

    @GetMapping("/info")
    @Operation(summary = "Get user information")
    public Result<UserDetail> info() {
        UserDetail user = SecurityUser.getUser();
        Result<UserDetail> result = new Result<>();
        result.setData(user);
        return result;
    }

    @PutMapping("/change-password")
    @Operation(summary = "Change user password")
    public Result<?> changePassword(@RequestBody PasswordDTO passwordDTO) {
        // 判断非空
        ValidatorUtils.validateEntity(passwordDTO);
        Long userId = SecurityUser.getUserId();
        sysUserTokenService.changePassword(userId, passwordDTO);
        return new Result<>();
    }

    @PutMapping("/update-password")
    @Operation(summary = "Update user password without old password (no login required)")
    public Result<?> updatePassword(@RequestBody UpdatePasswordDTO updatePasswordDTO) {
        log.info("Password update request initiated for username: {}", updatePasswordDTO.getUsername());

        // Validate DTO
        ValidatorUtils.validateEntity(updatePasswordDTO);
        log.debug("UpdatePasswordDTO validation passed for username: {}", updatePasswordDTO.getUsername());

        try {
            // Get user information by username
            SysUserDTO userDTO = sysUserService.getByUsername(updatePasswordDTO.getUsername());
            if (userDTO == null) {
                log.error("User not found for username: {}", updatePasswordDTO.getUsername());
                throw new RenException("账户不存在");
            }
            log.info("User found: username={}, userId={}", userDTO.getUsername(), userDTO.getId());

            // Update password directly without verifying old password or login status
            log.debug("Calling changePasswordDirectly for userId: {}, username: {}", userDTO.getId(), userDTO.getUsername());
            sysUserService.changePasswordDirectly(userDTO.getId(), updatePasswordDTO.getNewPassword());

            log.info("Password updated successfully for userId: {}, username: {}", userDTO.getId(), userDTO.getUsername());
            return new Result<>();
        } catch (RenException e) {
            log.error("Password update failed for username: {} - Error: {}", updatePasswordDTO.getUsername(), e.getMessage());
            throw e;
        } catch (Exception e) {
            log.error("Unexpected error during password update for username: {}", updatePasswordDTO.getUsername(), e);
            throw new RenException("Password update failed, please try again later");
        }
    }

    @DeleteMapping("/delete-account")
    @Operation(summary = "Delete user account (no login or password verification required)")
    public Result<?> deleteAccount(@RequestBody UpdatePasswordDTO deleteAccountDTO) {
        log.info("Account deletion request initiated for username: {}", deleteAccountDTO.getUsername());

        // Validate DTO
        ValidatorUtils.validateEntity(deleteAccountDTO);
        log.debug("DeleteAccountDTO validation passed for username: {}", deleteAccountDTO.getUsername());

        try {
            // Get user information by username
            SysUserDTO userDTO = sysUserService.getByUsername(deleteAccountDTO.getUsername());
            if (userDTO == null) {
                log.error("User not found for username: {}", deleteAccountDTO.getUsername());
                throw new RenException("账户不存在");
            }
            log.info("User found for deletion: username={}, userId={}", userDTO.getUsername(), userDTO.getId());

            // Delete user account (including associated devices and agents)
            log.info("Deleting user account and associated data for userId: {}, username: {}", userDTO.getId(), userDTO.getUsername());
            sysUserService.deleteById(userDTO.getId());

            log.info("Account deleted successfully for userId: {}, username: {}", userDTO.getId(), userDTO.getUsername());
            return new Result<>();
        } catch (RenException e) {
            log.error("Account deletion failed for username: {} - Error: {}", deleteAccountDTO.getUsername(), e.getMessage());
            throw e;
        } catch (Exception e) {
            log.error("Unexpected error during account deletion for username: {}", deleteAccountDTO.getUsername(), e);
            throw new RenException("Account deletion failed, please try again later");
        }
    }

    @PutMapping("/retrieve-password")
    @Operation(summary = "Retrieve password")
    public Result<?> retrievePassword(@RequestBody RetrievePasswordDTO dto) {
        // 是否开启手机注册
        Boolean isMobileRegister = sysParamsService
                .getValueObject(Constant.SysMSMParam.SERVER_ENABLE_MOBILE_REGISTER.getValue(), Boolean.class);
        if (!isMobileRegister) {
            throw new RenException("没有开启手机注册，没法使用找回密码功能");
        }
        // 判断非空
        ValidatorUtils.validateEntity(dto);
        // 验证用户是否是手机号码
        boolean validPhone = ValidatorUtils.isValidPhone(dto.getPhone());
        if (!validPhone) {
            throw new RenException("输入的手机号码格式不正确");
        }

        // 按照用户名获取用户
        SysUserDTO userDTO = sysUserService.getByUsername(dto.getPhone());
        if (userDTO == null) {
            throw new RenException("输入的手机号码未注册");
        }
        // 验证短信验证码是否正常
        boolean validate = captchaService.validateSMSValidateCode(dto.getPhone(), dto.getCode(), false);
        // 判断是否通过验证
        if (!validate) {
            throw new RenException("输入的手机验证码错误");
        }

        sysUserService.changePasswordDirectly(userDTO.getId(), dto.getPassword());
        return new Result<>();
    }

    @GetMapping("/pub-config")
    @Operation(summary = "Public configuration")
    public Result<Map<String, Object>> pubConfig() {
        Map<String, Object> config = new HashMap<>();
        config.put("enableMobileRegister", sysParamsService
                .getValueObject(Constant.SysMSMParam.SERVER_ENABLE_MOBILE_REGISTER.getValue(), Boolean.class));
        config.put("version", Constant.VERSION);
        config.put("year", "©" + Calendar.getInstance().get(Calendar.YEAR));
        config.put("allowUserRegister", sysUserService.getAllowUserRegister());
        List<SysDictDataItem> list = sysDictDataService.getDictDataByType(Constant.DictType.MOBILE_AREA.getValue());
        config.put("mobileAreaList", list);
        config.put("beianIcpNum", sysParamsService.getValue(Constant.SysBaseParam.BEIAN_ICP_NUM.getValue(), true));
        config.put("beianGaNum", sysParamsService.getValue(Constant.SysBaseParam.BEIAN_GA_NUM.getValue(), true));
        config.put("name", sysParamsService.getValue(Constant.SysBaseParam.SERVER_NAME.getValue(), true));

        return new Result<Map<String, Object>>().ok(config);
    }
}