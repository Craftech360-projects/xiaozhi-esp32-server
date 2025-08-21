package xiaozhi.modules.security.controller;

import java.io.IOException;
import java.util.Calendar;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
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
import xiaozhi.modules.sys.service.SysDictDataService;
import xiaozhi.modules.sys.service.SysParamsService;
import xiaozhi.modules.sys.service.SysUserService;
import xiaozhi.modules.sys.vo.SysDictDataItem;

/**
 * 登录控制层
 */
@AllArgsConstructor
@RestController
@RequestMapping("/user")
@Tag(name = "登录管理")
public class LoginController {
    private static final Logger logger = LoggerFactory.getLogger(LoginController.class);
    
    private final SysUserService sysUserService;
    private final SysUserTokenService sysUserTokenService;
    private final CaptchaService captchaService;
    private final SysParamsService sysParamsService;
    private final SysDictDataService sysDictDataService;

    @GetMapping("/captcha")
    @Operation(summary = "验证码")
    public void captcha(HttpServletResponse response, String uuid) throws IOException {
        // uuid不能为空
        AssertUtils.isBlank(uuid, ErrorCode.IDENTIFIER_NOT_NULL);
        // 生成验证码
        captchaService.create(response, uuid);
    }

    @PostMapping("/smsVerification")
    @Operation(summary = "短信验证码")
    public Result<Void> smsVerification(@RequestBody SmsVerificationDTO dto) {
        // 验证图形验证码
        boolean validate = captchaService.validate(dto.getCaptchaId(), dto.getCaptcha(), true);
        if (!validate) {
            throw new RenException("Incorrect verification code");
        }
        Boolean isMobileRegister = sysParamsService
                .getValueObject(Constant.SysMSMParam.SERVER_ENABLE_MOBILE_REGISTER.getValue(), Boolean.class);
        if (!isMobileRegister) {
            throw new RenException("Mobile registration is disabled, SMS verification is not available");
        }
        // 发送短信验证码
        captchaService.sendSMSValidateCode(dto.getPhone());
        return new Result<>();
    }

    @PostMapping("/login")
    @Operation(summary = "登录")
    public Result<TokenDTO> login(@RequestBody LoginDTO login) {
        logger.info("=== Login attempt started ===");
        logger.info("Username: {}", login.getUsername());
        logger.info("CaptchaId: {}", login.getCaptchaId());
        logger.info("Captcha: {}", login.getCaptcha());
        
        // 验证是否正确输入验证码
        logger.info("Step 1: Validating captcha...");
        boolean validate = captchaService.validate(login.getCaptchaId(), login.getCaptcha(), true);
        logger.info("Captcha validation result: {}", validate);
        
        if (!validate) {
            logger.error("Login failed: Captcha validation failed for user: {}", login.getUsername());
            throw new RenException("Incorrect verification code, please try again");
        }
        
        // 按照用户名获取用户
        logger.info("Step 2: Looking up user in database...");
        SysUserDTO userDTO = sysUserService.getByUsername(login.getUsername());
        
        // 判断用户是否存在
        if (userDTO == null) {
            logger.error("Login failed: User not found in database: {}", login.getUsername());
            throw new RenException("Please check if username and password are correct");
        }
        
        logger.info("User found in database - ID: {}, Username: {}, Status: {}, SuperAdmin: {}", 
                    userDTO.getId(), userDTO.getUsername(), userDTO.getStatus(), userDTO.getSuperAdmin());
        
        // 判断密码是否正确，不一样则进入if
        logger.info("Step 3: Validating password...");
        boolean passwordMatch = PasswordUtils.matches(login.getPassword(), userDTO.getPassword());
        logger.info("Password match result: {}", passwordMatch);
        
        if (!passwordMatch) {
            logger.error("Login failed: Password mismatch for user: {}", login.getUsername());
            logger.debug("Entered password length: {}, Stored password hash: {}", 
                        login.getPassword().length(), userDTO.getPassword());
            throw new RenException("Please check if username and password are correct");
        }
        
        // 创建token
        logger.info("Step 4: Creating authentication token...");
        Result<TokenDTO> tokenResult = sysUserTokenService.createToken(userDTO.getId());
        
        logger.info("=== Login successful for user: {} ===", login.getUsername());
        logger.info("Token created: {}", tokenResult.getData().getToken());
        
        return tokenResult;
    }

    @PostMapping("/register")
    @Operation(summary = "注册")
    public Result<Void> register(@RequestBody LoginDTO login) {
        if (!sysUserService.getAllowUserRegister()) {
            throw new RenException("User registration is currently disabled");
        }
        // 是否开启手机注册
        Boolean isMobileRegister = sysParamsService
                .getValueObject(Constant.SysMSMParam.SERVER_ENABLE_MOBILE_REGISTER.getValue(), Boolean.class);
        boolean validate;
        if (isMobileRegister) {
            // 验证用户是否是手机号码
            boolean validPhone = ValidatorUtils.isValidPhone(login.getUsername());
            if (!validPhone) {
                throw new RenException("Username is not a valid phone number, please re-enter");
            }
            // 验证短信验证码是否正常
            validate = captchaService.validateSMSValidateCode(login.getUsername(), login.getMobileCaptcha(), false);
            if (!validate) {
                throw new RenException("Incorrect SMS verification code, please try again");
            }
        } else {
            // 验证是否正确输入验证码
            validate = captchaService.validate(login.getCaptchaId(), login.getCaptcha(), true);
            if (!validate) {
                throw new RenException("Incorrect verification code, please try again");
            }
        }

        // 按照用户名获取用户
        SysUserDTO userDTO = sysUserService.getByUsername(login.getUsername());
        if (userDTO != null) {
            throw new RenException("This phone number is already registered");
        }
        userDTO = new SysUserDTO();
        userDTO.setUsername(login.getUsername());
        userDTO.setPassword(login.getPassword());
        sysUserService.save(userDTO);
        return new Result<>();
    }

    @GetMapping("/info")
    @Operation(summary = "用户信息获取")
    public Result<UserDetail> info() {
        UserDetail user = SecurityUser.getUser();
        Result<UserDetail> result = new Result<>();
        result.setData(user);
        return result;
    }

    @PutMapping("/change-password")
    @Operation(summary = "修改用户密码")
    public Result<?> changePassword(@RequestBody PasswordDTO passwordDTO) {
        // 判断非空
        ValidatorUtils.validateEntity(passwordDTO);
        Long userId = SecurityUser.getUserId();
        sysUserTokenService.changePassword(userId, passwordDTO);
        return new Result<>();
    }

    @PutMapping("/retrieve-password")
    @Operation(summary = "找回密码")
    public Result<?> retrievePassword(@RequestBody RetrievePasswordDTO dto) {
        // 是否开启手机注册
        Boolean isMobileRegister = sysParamsService
                .getValueObject(Constant.SysMSMParam.SERVER_ENABLE_MOBILE_REGISTER.getValue(), Boolean.class);
        if (!isMobileRegister) {
            throw new RenException("Mobile registration is disabled, password recovery is not available");
        }
        // 判断非空
        ValidatorUtils.validateEntity(dto);
        // 验证用户是否是手机号码
        boolean validPhone = ValidatorUtils.isValidPhone(dto.getPhone());
        if (!validPhone) {
            throw new RenException("Invalid phone number format");
        }

        // 按照用户名获取用户
        SysUserDTO userDTO = sysUserService.getByUsername(dto.getPhone());
        if (userDTO == null) {
            throw new RenException("This phone number is not registered");
        }
        // 验证短信验证码是否正常
        boolean validate = captchaService.validateSMSValidateCode(dto.getPhone(), dto.getCode(), false);
        // 判断是否通过验证
        if (!validate) {
            throw new RenException("Incorrect SMS verification code");
        }

        sysUserService.changePasswordDirectly(userDTO.getId(), dto.getPassword());
        return new Result<>();
    }

    @GetMapping("/pub-config")
    @Operation(summary = "公共配置")
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