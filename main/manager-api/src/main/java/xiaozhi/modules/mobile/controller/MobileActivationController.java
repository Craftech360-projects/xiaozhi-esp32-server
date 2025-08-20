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
            
            // Extract additional fields from request
            String toyName = (String) request.get("toyName");
            String toyRole = (String) request.get("toyRole");
            String toyLanguage = (String) request.get("toyLanguage");
            String toyVoice = (String) request.get("toyVoice");
            String additionalInstructions = (String) request.get("additionalInstructions");
            
            // Apply default values if not provided
            if (childName == null || childName.trim().isEmpty() || "My Child".equals(childName)) {
                childName = "Buddy";
            }
            if (childAge == null) {
                childAge = 5;
            }
            if (toyName == null || toyName.trim().isEmpty()) {
                toyName = "Cheeko";
            }
            if (toyRole == null || toyRole.trim().isEmpty()) {
                toyRole = "Story Teller";
            }
            if (toyLanguage == null || toyLanguage.trim().isEmpty()) {
                toyLanguage = "English";
            }
            if (toyVoice == null || toyVoice.trim().isEmpty()) {
                toyVoice = "Sparkles for Kids";
            }
            
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
            
            // Check if new columns exist by trying to query them
            boolean hasNewColumns = false;
            try {
                jdbcTemplate.queryForObject(
                    "SELECT toy_name FROM activated_toys LIMIT 1", String.class);
                hasNewColumns = true;
            } catch (Exception e) {
                // New columns don't exist yet
                log.info("New columns not yet available, using legacy schema");
            }
            
            if (hasNewColumns) {
                // Use new schema with all fields
                String insertSql = "INSERT INTO activated_toys (id, toy_id, user_id, " +
                        "toy_name, toy_role, toy_language, toy_voice, " +
                        "child_name, child_age, child_interests, additional_instructions) " +
                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)";
                
                jdbcTemplate.update(insertSql, 
                    activationId,
                    toyId,
                    userId,
                    toyName,
                    toyRole,
                    toyLanguage,
                    toyVoice,
                    childName,
                    childAge,
                    childInterestsJson,
                    additionalInstructions
                );
            } else {
                // Use legacy schema - store toy name in child_name for now
                String insertSql = "INSERT INTO activated_toys (id, toy_id, user_id, " +
                        "child_name, child_age, child_interests) VALUES (?, ?, ?, ?, ?, ?)";
                
                // Store "Cheeko" as child_name temporarily until migration runs
                jdbcTemplate.update(insertSql, 
                    activationId,
                    toyId,
                    userId,
                    childName,  // This will be "Buddy" by default
                    childAge,
                    childInterestsJson
                );
            }
            
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
            // Always return both fields for compatibility
            result.put("toyName", toyName);
            result.put("toy_name", toyName); // Include both formats
            result.put("childName", childName);
            result.put("child_name", childName); // Include both formats
            result.put("toy_role", toyRole);
            result.put("toy_language", toyLanguage);
            result.put("toy_voice", toyVoice);
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
            
            // Transform devices to include toy_name if not present
            for (Map<String, Object> device : devices) {
                // If new columns don't exist, provide defaults
                if (!device.containsKey("toy_name")) {
                    device.put("toy_name", "Cheeko");
                    device.put("toy_role", "Story Teller");
                    device.put("toy_language", "English");
                    device.put("toy_voice", "Sparkles for Kids");
                }
                // Ensure child_name has a default
                if (device.get("child_name") == null || 
                    device.get("child_name").toString().isEmpty()) {
                    device.put("child_name", "Buddy");
                }
            }
            
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
    
    @PutMapping("/toy-details/{activationId}")
    @Operation(summary = "Update toy and child details for an activation")
    public Result<Map<String, Object>> updateToyDetails(
            @PathVariable String activationId,
            @RequestBody Map<String, Object> updates,
            HttpServletRequest request) {
        try {
            String userId = (String) request.getAttribute("supabaseUserId");
            
            // Extract toy configuration fields
            String toyName = (String) updates.get("toyName");
            String toyRole = (String) updates.get("toyRole");
            String toyLanguage = (String) updates.get("toyLanguage");
            String toyVoice = (String) updates.get("toyVoice");
            String additionalInstructions = (String) updates.get("additionalInstructions");
            
            // Extract child fields
            String childName = (String) updates.get("childName");
            Integer childAge = (Integer) updates.get("childAge");
            
            log.info("Updating toy details for activation {} by user {}", activationId, userId);
            
            StringBuilder sqlBuilder = new StringBuilder("UPDATE activated_toys SET ");
            List<Object> params = new ArrayList<>();
            
            // Add toy fields
            if (toyName != null && !toyName.trim().isEmpty()) {
                sqlBuilder.append("toy_name = ?, ");
                params.add(toyName);
            }
            if (toyRole != null && !toyRole.trim().isEmpty()) {
                sqlBuilder.append("toy_role = ?, ");
                params.add(toyRole);
            }
            if (toyLanguage != null && !toyLanguage.trim().isEmpty()) {
                sqlBuilder.append("toy_language = ?, ");
                params.add(toyLanguage);
            }
            if (toyVoice != null && !toyVoice.trim().isEmpty()) {
                sqlBuilder.append("toy_voice = ?, ");
                params.add(toyVoice);
            }
            if (additionalInstructions != null) {
                sqlBuilder.append("additional_instructions = ?, ");
                params.add(additionalInstructions);
            }
            
            // Add child fields
            if (childName != null && !childName.trim().isEmpty()) {
                sqlBuilder.append("child_name = ?, ");
                params.add(childName);
            }
            if (childAge != null) {
                sqlBuilder.append("child_age = ?, ");
                params.add(childAge);
            }
            
            // Remove trailing comma and add WHERE clause
            String sql = sqlBuilder.toString().replaceAll(", $", "") + 
                    " WHERE id = ? AND user_id = ?";
            params.add(activationId);
            params.add(userId);
            
            int rows = jdbcTemplate.update(sql, params.toArray());
            
            if (rows > 0) {
                Map<String, Object> result = new HashMap<>();
                result.put("message", "Toy details updated successfully");
                result.put("success", true);
                return new Result<Map<String, Object>>().ok(result);
            } else {
                return new Result<Map<String, Object>>().error("Toy not found or unauthorized");
            }
            
        } catch (Exception e) {
            log.error("Error updating toy details", e);
            return new Result<Map<String, Object>>().error("Failed to update toy details: " + e.getMessage());
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