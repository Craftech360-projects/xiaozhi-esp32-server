package xiaozhi.modules.mobile.controller;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.servlet.http.HttpServletRequest;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.bind.annotation.RequestParam;
import xiaozhi.common.utils.Result;

import java.util.ArrayList;
import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/**
 * Mobile Activation Controller
 * Handles toy activation for the mobile app
 */
@RestController
@RequestMapping("/api/mobile/activation")
@Tag(name = "Mobile Activation API")
@Slf4j
public class MobileActivationController {
    
    @Autowired
    private JdbcTemplate jdbcTemplate;
    
    @GetMapping("/check-code")
    @Operation(summary = "Check if activation code is valid (without authentication)")
    public Result<Map<String, Object>> checkActivationCode(@RequestParam String code) {
        try {
            log.info("Checking activation code: {}", code);
            
            // Check if code exists and is not yet activated
            String sql = "SELECT COUNT(*) FROM toys WHERE activation_code = ? AND is_activated = false";
            Integer count = jdbcTemplate.queryForObject(sql, Integer.class, code);
            
            Map<String, Object> data = new HashMap<>();
            data.put("valid", count != null && count > 0);
            data.put("code", code);
            
            return new Result<Map<String, Object>>().ok(data);
        } catch (Exception e) {
            log.error("Error checking activation code", e);
            return new Result<Map<String, Object>>().error("Failed to check activation code");
        }
    }
    
    @PostMapping("/validate")
    @Operation(summary = "Validate and activate a toy")
    public Result<Map<String, Object>> validateAndActivate(
            @RequestBody Map<String, Object> request,
            HttpServletRequest httpRequest) {
        try {
            String userId = (String) httpRequest.getAttribute("supabaseUserId");
            String activationCode = (String) request.get("activationCode");
            String childName = (String) request.get("childName");
            Integer childAge = (Integer) request.get("childAge");
            List<String> childInterests = (List<String>) request.get("childInterests");
            
            log.info("Validating activation code {} for user {}", activationCode, userId);
            
            // Check if toy exists and is not activated
            String checkSql = "SELECT * FROM toys WHERE activation_code = ? AND is_activated = false";
            List<Map<String, Object>> toys = jdbcTemplate.queryForList(checkSql, activationCode);
            
            if (toys.isEmpty()) {
                log.warn("Invalid or already activated code: {}", activationCode);
                return new Result<Map<String, Object>>().error("Invalid or already activated code");
            }
            
            Map<String, Object> toyData = toys.get(0);
            String toyId = (String) toyData.get("id");
            String serialNumber = (String) toyData.get("serial_number");
            String model = (String) toyData.get("model");
            String macAddress = (String) toyData.get("mac_address");
            
            // Convert childInterests to JSON
            String childInterestsJson = "[]";
            if (childInterests != null && !childInterests.isEmpty()) {
                childInterestsJson = "[" + childInterests.stream()
                    .map(s -> "\"" + s + "\"")
                    .reduce((a, b) -> a + "," + b)
                    .orElse("") + "]";
            }
            
            // Create activation record
            String activationId = UUID.randomUUID().toString();
            String insertSql = "INSERT INTO activated_toys (id, toy_id, user_id, " +
                    "child_name, child_age, child_interests) VALUES (?, ?, ?, ?, ?, ?)";
            
            jdbcTemplate.update(insertSql, 
                activationId,
                toyId,
                userId,
                childName,
                childAge,
                childInterestsJson
            );
            
            // Mark toy as activated
            String updateToySql = "UPDATE toys SET is_activated = true WHERE id = ?";
            jdbcTemplate.update(updateToySql, toyId);
            
            log.info("Successfully activated toy {} for user {}", serialNumber, userId);
            
            // Return activation details
            Map<String, Object> result = new HashMap<>();
            result.put("activationId", activationId);
            result.put("toyId", toyId);
            result.put("serialNumber", serialNumber);
            result.put("model", model);
            result.put("macAddress", macAddress);
            result.put("childName", childName);
            result.put("message", "Toy activated successfully");
            
            return new Result<Map<String, Object>>().ok(result);
            
        } catch (Exception e) {
            log.error("Error activating toy", e);
            return new Result<Map<String, Object>>().error("Failed to activate toy: " + e.getMessage());
        }
    }
    
    @GetMapping("/devices")
    @Operation(summary = "Get activated devices for current user")
    public Result<Map<String, Object>> getActivatedDevices(HttpServletRequest request) {
        try {
            String userId = (String) request.getAttribute("supabaseUserId");
            log.info("Getting activated devices for user: {}", userId);
            
            String sql = "SELECT at.*, t.serial_number, t.model, t.mac_address, t.activation_code " +
                    "FROM activated_toys at " +
                    "JOIN toys t ON at.toy_id = t.id " +
                    "WHERE at.user_id = ? AND at.is_active = true " +
                    "ORDER BY at.activated_at DESC";
            
            List<Map<String, Object>> devices = jdbcTemplate.queryForList(sql, userId);
            
            Map<String, Object> result = new HashMap<>();
            result.put("devices", devices);
            result.put("count", devices.size());
            
            return new Result<Map<String, Object>>().ok(result);
            
        } catch (Exception e) {
            log.error("Error getting activated devices", e);
            return new Result<Map<String, Object>>().error("Failed to get devices: " + e.getMessage());
        }
    }
    
    @PostMapping("/deactivate/{activationId}")
    @Operation(summary = "Deactivate a device")
    public Result<Map<String, Object>> deactivateDevice(
            @PathVariable String activationId,
            HttpServletRequest request) {
        try {
            String userId = (String) request.getAttribute("supabaseUserId");
            log.info("Deactivating device {} for user {}", activationId, userId);
            
            // Verify ownership and deactivate
            String sql = "UPDATE activated_toys SET is_active = false " +
                    "WHERE id = ? AND user_id = ?";
            int rows = jdbcTemplate.update(sql, activationId, userId);
            
            if (rows > 0) {
                Map<String, Object> result = new HashMap<>();
                result.put("message", "Device deactivated successfully");
                return new Result<Map<String, Object>>().ok(result);
            } else {
                return new Result<Map<String, Object>>().error("Device not found or unauthorized");
            }
            
        } catch (Exception e) {
            log.error("Error deactivating device", e);
            return new Result<Map<String, Object>>().error("Failed to deactivate device: " + e.getMessage());
        }
    }
    
    @GetMapping("/{activationId}")
    @Operation(summary = "Get activation details")
    public Result<Map<String, Object>> getActivationDetails(
            @PathVariable String activationId,
            HttpServletRequest request) {
        try {
            String userId = (String) request.getAttribute("supabaseUserId");
            
            String sql = "SELECT at.*, t.serial_number, t.model, t.mac_address " +
                    "FROM activated_toys at " +
                    "JOIN toys t ON at.toy_id = t.id " +
                    "WHERE at.id = ? AND at.user_id = ?";
            
            List<Map<String, Object>> results = jdbcTemplate.queryForList(sql, activationId, userId);
            
            if (!results.isEmpty()) {
                return new Result<Map<String, Object>>().ok(results.get(0));
            } else {
                return new Result<Map<String, Object>>().error("Activation not found");
            }
            
        } catch (Exception e) {
            log.error("Error getting activation details", e);
            return new Result<Map<String, Object>>().error("Failed to get activation details: " + e.getMessage());
        }
    }
    
    @PutMapping("/child-info/{activationId}")
    @Operation(summary = "Update child information for an activation")
    public Result<Map<String, Object>> updateChildInfo(
            @PathVariable String activationId,
            @RequestBody Map<String, Object> updates,
            HttpServletRequest request) {
        try {
            String userId = (String) request.getAttribute("supabaseUserId");
            String childName = (String) updates.get("childName");
            Integer childAge = (Integer) updates.get("childAge");
            List<String> childInterests = (List<String>) updates.get("childInterests");
            
            log.info("Updating child info for activation {} by user {}", activationId, userId);
            
            StringBuilder sqlBuilder = new StringBuilder("UPDATE activated_toys SET ");
            List<Object> params = new ArrayList<>();
            
            if (childName != null) {
                sqlBuilder.append("child_name = ?, ");
                params.add(childName);
            }
            if (childAge != null) {
                sqlBuilder.append("child_age = ?, ");
                params.add(childAge);
            }
            if (childInterests != null) {
                sqlBuilder.append("child_interests = ?, ");
                String childInterestsJson = "[" + childInterests.stream()
                    .map(s -> "\"" + s + "\"")
                    .reduce((a, b) -> a + "," + b)
                    .orElse("") + "]";
                params.add(childInterestsJson);
            }
            
            // Remove trailing comma and add WHERE clause
            String sql = sqlBuilder.toString().replaceAll(", $", "") + 
                    " WHERE id = ? AND user_id = ?";
            params.add(activationId);
            params.add(userId);
            
            int rows = jdbcTemplate.update(sql, params.toArray());
            
            if (rows > 0) {
                Map<String, Object> result = new HashMap<>();
                result.put("message", "Child info updated successfully");
                return new Result<Map<String, Object>>().ok(result);
            } else {
                return new Result<Map<String, Object>>().error("Activation not found or unauthorized");
            }
            
        } catch (Exception e) {
            log.error("Error updating child info", e);
            return new Result<Map<String, Object>>().error("Failed to update child info: " + e.getMessage());
        }
    }
}