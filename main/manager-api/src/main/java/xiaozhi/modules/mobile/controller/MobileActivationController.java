package xiaozhi.modules.mobile.controller;

import xiaozhi.common.utils.R;
import xiaozhi.modules.mobile.entity.ActivationRequest;
import xiaozhi.modules.mobile.entity.ActivationResponse;
import xiaozhi.modules.mobile.service.MobileActivationService;
import xiaozhi.modules.mobile.service.SupabaseAuthService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import javax.servlet.http.HttpServletRequest;
import javax.validation.Valid;

/**
 * Mobile App Device Activation Controller
 * Handles device activation for Flutter parental app
 */
@RestController
@RequestMapping("/mobile/activation")
@Tag(name = "Mobile Activation", description = "Device activation for parental mobile app")
public class MobileActivationController {

    @Autowired
    private MobileActivationService activationService;

    @Autowired
    private SupabaseAuthService authService;

    /**
     * Validate and activate device with 6-digit code
     */
    @PostMapping("/validate")
    @Operation(summary = "Validate activation code and activate device")
    public R<ActivationResponse> validateActivationCode(
            @Valid @RequestBody ActivationRequest request,
            HttpServletRequest httpRequest) {
        
        try {
            // Extract and verify Supabase JWT token
            String token = extractBearerToken(httpRequest);
            if (token == null) {
                return R.error(401, "Missing authorization token").put("code", "AUTH_MISSING_TOKEN");
            }

            // Verify token with Supabase
            String supabaseUserId = authService.verifyToken(token);
            if (supabaseUserId == null) {
                return R.error(401, "Invalid or expired token").put("code", "AUTH_INVALID_TOKEN");
            }

            // Validate activation code and create device mapping
            ActivationResponse response = activationService.validateAndActivateDevice(
                request.getActivationCode(),
                supabaseUserId,
                request.getChildName(),
                request.getChildAge(),
                request.getChildInterests()
            );

            return R.ok(response);

        } catch (IllegalArgumentException e) {
            return R.error(400, e.getMessage()).put("code", "ACTIVATION_INVALID_CODE");
        } catch (IllegalStateException e) {
            return R.error(409, e.getMessage()).put("code", "DEVICE_ALREADY_ACTIVE");
        } catch (Exception e) {
            return R.error(500, "Internal server error").put("code", "INTERNAL_ERROR");
        }
    }

    /**
     * Get activation status
     */
    @GetMapping("/{activationId}/status")
    @Operation(summary = "Get device activation status")
    public R getActivationStatus(
            @PathVariable String activationId,
            HttpServletRequest httpRequest) {
        
        try {
            // Verify authentication
            String token = extractBearerToken(httpRequest);
            String supabaseUserId = authService.verifyToken(token);
            if (supabaseUserId == null) {
                return R.error(401, "Invalid token").put("code", "AUTH_INVALID_TOKEN");
            }

            // Get activation status
            var status = activationService.getActivationStatus(activationId, supabaseUserId);
            
            return R.ok(status);

        } catch (IllegalArgumentException e) {
            return R.error(404, "Activation not found").put("code", "ACTIVATION_NOT_FOUND");
        } catch (SecurityException e) {
            return R.error(403, "Insufficient permissions").put("code", "INSUFFICIENT_PERMISSIONS");
        } catch (Exception e) {
            return R.error(500, "Internal server error").put("code", "INTERNAL_ERROR");
        }
    }

    /**
     * List user's activated devices
     */
    @GetMapping("/devices")
    @Operation(summary = "List user's activated devices")
    public R getUserDevices(HttpServletRequest httpRequest) {
        try {
            // Verify authentication
            String token = extractBearerToken(httpRequest);
            String supabaseUserId = authService.verifyToken(token);
            if (supabaseUserId == null) {
                return R.error(401, "Invalid token").put("code", "AUTH_INVALID_TOKEN");
            }

            var devices = activationService.getUserDevices(supabaseUserId);
            
            return R.ok().put("devices", devices).put("total_devices", devices.size());

        } catch (Exception e) {
            return R.error(500, "Internal server error").put("code", "INTERNAL_ERROR");
        }
    }

    /**
     * Generate activation codes (admin only)
     */
    @PostMapping("/generate-codes")
    @Operation(summary = "Generate activation codes for manufacturing")
    public R generateActivationCodes(
            @RequestParam int batchSize,
            @RequestParam String toyModel,
            @RequestParam String batchId,
            HttpServletRequest httpRequest) {
        
        try {
            // Verify admin authentication (implement admin check)
            String token = extractBearerToken(httpRequest);
            if (!authService.isAdminUser(token)) {
                return R.error(403, "Admin access required").put("code", "INSUFFICIENT_PERMISSIONS");
            }

            var codes = activationService.generateActivationCodes(batchSize, toyModel, batchId);
            
            return R.ok().put("codes", codes).put("batch_size", batchSize);

        } catch (Exception e) {
            return R.error(500, "Internal server error").put("code", "INTERNAL_ERROR");
        }
    }

    /**
     * Extract Bearer token from Authorization header
     */
    private String extractBearerToken(HttpServletRequest request) {
        String authHeader = request.getHeader("Authorization");
        if (authHeader != null && authHeader.startsWith("Bearer ")) {
            return authHeader.substring(7);
        }
        return null;
    }
}