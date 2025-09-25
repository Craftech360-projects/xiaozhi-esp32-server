package xiaozhi.modules.sys.controller;

import java.util.Map;

import org.apache.commons.lang3.StringUtils;
import org.apache.shiro.authz.annotation.RequiresPermissions;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.client.RestTemplate;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.Parameters;
import io.swagger.v3.oas.annotations.enums.ParameterIn;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.AllArgsConstructor;
import xiaozhi.common.annotation.LogOperation;
import xiaozhi.common.constant.Constant;
import xiaozhi.common.exception.RenException;
import xiaozhi.common.page.PageData;
import xiaozhi.common.utils.Result;
import xiaozhi.common.validator.AssertUtils;
import xiaozhi.common.validator.ValidatorUtils;
import xiaozhi.common.validator.group.AddGroup;
import xiaozhi.common.validator.group.DefaultGroup;
import xiaozhi.common.validator.group.UpdateGroup;
import xiaozhi.modules.config.service.ConfigService;
import xiaozhi.modules.sys.dto.SysParamsDTO;
import xiaozhi.modules.sys.service.SysParamsService;
import xiaozhi.modules.sys.utils.WebSocketValidator;

/**
 * 参数管理
 *
 * @author Mark sunlightcs@gmail.com
 * @since 1.0.0
 */
@RestController
@RequestMapping("admin/params")
@Tag(name = "Parameter Management")
@AllArgsConstructor
public class SysParamsController {
    private final SysParamsService sysParamsService;
    private final ConfigService configService;
    private final RestTemplate restTemplate;

    @GetMapping("page")
    @Operation(summary = "Pagination")
    @Parameters({
            @Parameter(name = Constant.PAGE, description = "当前页码，从1开始", in = ParameterIn.QUERY, required = true, ref = "int"),
            @Parameter(name = Constant.LIMIT, description = "每页显示记录数", in = ParameterIn.QUERY, required = true, ref = "int"),
            @Parameter(name = Constant.ORDER_FIELD, description = "排序字段", in = ParameterIn.QUERY, ref = "String"),
            @Parameter(name = Constant.ORDER, description = "排序方式，可选值(asc、desc)", in = ParameterIn.QUERY, ref = "String"),
            @Parameter(name = "paramCode", description = "参数编码或参数备注", in = ParameterIn.QUERY, ref = "String")
    })
    @RequiresPermissions("sys:role:superAdmin")
    public Result<PageData<SysParamsDTO>> page(@Parameter(hidden = true) @RequestParam Map<String, Object> params) {
        PageData<SysParamsDTO> page = sysParamsService.page(params);

        return new Result<PageData<SysParamsDTO>>().ok(page);
    }

    @GetMapping("{id}")
    @Operation(summary = "Information")
    @RequiresPermissions("sys:role:superAdmin")
    public Result<SysParamsDTO> get(@PathVariable("id") Long id) {
        SysParamsDTO data = sysParamsService.get(id);

        return new Result<SysParamsDTO>().ok(data);
    }

    @PostMapping
    @Operation(summary = "Save")
    @LogOperation("保存")
    @RequiresPermissions("sys:role:superAdmin")
    public Result<Void> save(@RequestBody SysParamsDTO dto) {
        // 效验数据
        ValidatorUtils.validateEntity(dto, AddGroup.class, DefaultGroup.class);

        sysParamsService.save(dto);
        configService.getConfig(false);
        return new Result<Void>();
    }

    @PutMapping
    @Operation(summary = "Modify")
    @LogOperation("修改")
    @RequiresPermissions("sys:role:superAdmin")
    public Result<Void> update(@RequestBody SysParamsDTO dto,
                              @RequestParam(value = "skipValidation", required = false, defaultValue = "false") Boolean skipValidation) {
        // Debug logging
        System.out.println("🔧 UPDATE PARAM - paramCode: " + dto.getParamCode() + ", skipValidation: " + skipValidation);

        // 效验数据
        ValidatorUtils.validateEntity(dto, UpdateGroup.class, DefaultGroup.class);

        // 验证WebSocket地址列表 (可选择跳过)
        validateWebSocketUrls(dto.getParamCode(), dto.getParamValue(), skipValidation);

        // 验证OTA地址
        validateOtaUrl(dto.getParamCode(), dto.getParamValue());

        // 验证MCP地址
        validateMcpUrl(dto.getParamCode(), dto.getParamValue());

        //
        validateVoicePrint(dto.getParamCode(), dto.getParamValue());

        sysParamsService.update(dto);
        configService.getConfig(false);
        return new Result<Void>();
    }

    /**
     * 验证WebSocket地址列表
     *
     * @param paramCode 参数编码
     * @param urls WebSocket地址列表，以分号分隔
     * @param skipValidation 是否跳过连接测试验证
     * @return 验证结果
     */
    private void validateWebSocketUrls(String paramCode, String urls, Boolean skipValidation) {
        if (!paramCode.equals(Constant.SERVER_WEBSOCKET)) {
            return;
        }

        System.out.println("🔧 WEBSOCKET VALIDATION - paramCode: " + paramCode + ", skipValidation: " + skipValidation);

        String[] wsUrls = urls.split("\\;");
        if (wsUrls.length == 0) {
            throw new RenException("WebSocket地址列表不能为空");
        }
        for (String url : wsUrls) {
            if (StringUtils.isNotBlank(url)) {
                // 检查是否包含localhost或127.0.0.1
                if (url.contains("localhost") || url.contains("127.0.0.1")) {
                    throw new RenException("WebSocket地址不能使用localhost或127.0.0.1");
                }

                // 验证WebSocket地址格式
                if (!WebSocketValidator.validateUrlFormat(url)) {
                    throw new RenException("WebSocket地址格式不正确: " + url);
                }

                // 测试WebSocket连接 (可选择跳过)
                if (!skipValidation && !WebSocketValidator.testConnection(url)) {
                    throw new RenException("WebSocket连接测试失败: " + url);
                } else if (skipValidation) {
                    System.out.println("🚀 SKIPPING WebSocket connection test for: " + url);
                }
            }
        }
    }

    @PostMapping("/delete")
    @Operation(summary = "Delete")
    @LogOperation("删除")
    @RequiresPermissions("sys:role:superAdmin")
    public Result<Void> delete(@RequestBody String[] ids) {
        // 效验数据
        AssertUtils.isArrayEmpty(ids, "id");

        sysParamsService.delete(ids);
        configService.getConfig(false);
        return new Result<Void>();
    }

    /**
     * 验证OTA地址
     */
    private void validateOtaUrl(String paramCode, String url) {
        if (!paramCode.equals(Constant.SERVER_OTA)) {
            return;
        }
        if (StringUtils.isBlank(url) || url.equals("null")) {
            throw new RenException("OTA地址不能为空");
        }

        // 检查是否包含localhost或127.0.0.1
        if (url.contains("localhost") || url.contains("127.0.0.1")) {
            throw new RenException("OTA地址不能使用localhost或127.0.0.1");
        }

        // 验证URL格式
        if (!url.toLowerCase().startsWith("http")) {
            throw new RenException("OTA地址必须以http或https开头");
        }
        if (!url.endsWith("/ota/")) {
            throw new RenException("OTA地址必须以/ota/结尾");
        }

        try {
            // 发送GET请求
            ResponseEntity<String> response = restTemplate.getForEntity(url, String.class);
            if (response.getStatusCode() != HttpStatus.OK) {
                throw new RenException("OTA接口访问失败，状态码：" + response.getStatusCode());
            }
            // 检查响应内容是否包含OTA相关信息
            String body = response.getBody();
            if (body == null || !body.contains("OTA")) {
                throw new RenException("OTA接口返回内容格式不正确，可能不是一个真实的OTA接口");
            }
        } catch (Exception e) {
            throw new RenException("OTA接口验证失败：" + e.getMessage());
        }
    }

    private void validateMcpUrl(String paramCode, String url) {
        if (!paramCode.equals(Constant.SERVER_MCP_ENDPOINT)) {
            return;
        }
        if (StringUtils.isBlank(url) || url.equals("null")) {
            throw new RenException("MCP地址不能为空");
        }
        if (url.contains("localhost") || url.contains("127.0.0.1")) {
            throw new RenException("MCP地址不能使用localhost或127.0.0.1");
        }
        if (!url.toLowerCase().contains("key")) {
            throw new RenException("不是正确的MCP地址");
        }

        try {
            // 发送GET请求
            ResponseEntity<String> response = restTemplate.getForEntity(url, String.class);
            if (response.getStatusCode() != HttpStatus.OK) {
                throw new RenException("MCP接口访问失败，状态码：" + response.getStatusCode());
            }
            // 检查响应内容是否包含mcp相关信息
            String body = response.getBody();
            if (body == null || !body.contains("success")) {
                throw new RenException("MCP接口返回内容格式不正确，可能不是一个真实的MCP接口");
            }
        } catch (Exception e) {
            throw new RenException("MCP接口验证失败：" + e.getMessage());
        }
    }
    // 验证声纹接口地址是否正常
    private void validateVoicePrint(String paramCode, String url) {
        if (!paramCode.equals(Constant.SERVER_VOICE_PRINT)) {
            return;
        }
        if (StringUtils.isBlank(url) || url.equals("null")) {
            throw new RenException("声纹接口地址不能为空");
        }
        if (url.contains("localhost") || url.contains("127.0.0.1")) {
            throw new RenException("声纹接口地址不能使用localhost或127.0.0.1");
        }
        if (!url.toLowerCase().contains("key")) {
            throw new RenException("不是正确的声纹接口地址");
        }
        // 验证URL格式
        if (!url.toLowerCase().startsWith("http")) {
            throw new RenException("声纹接口地址必须以http或https开头");
        }
        try {
            // 发送GET请求
            ResponseEntity<String> response = restTemplate.getForEntity(url, String.class);
            if (response.getStatusCode() != HttpStatus.OK) {
                throw new RenException("声纹接口访问失败，状态码：" + response.getStatusCode());
            }
            // 检查响应内容
            String body = response.getBody();
            if (body == null || !body.contains("healthy")) {
                throw new RenException("声纹接口返回内容格式不正确，可能不是一个真实的MCP接口");
            }
        } catch (Exception e) {
            throw new RenException("声纹接口验证失败：" + e.getMessage());
        }
    }
}
