package xiaozhi.modules.mobile.controller;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.servlet.http.HttpServletRequest;
import java.util.HashMap;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import xiaozhi.common.utils.Result;
import xiaozhi.modules.mobile.entity.ParentProfile;
import xiaozhi.modules.mobile.service.ParentProfileService;

import java.util.Map;

/**
 * Mobile Parent Profile Controller
 * Handles parent profile management for the mobile app
 */
@RestController
@RequestMapping("/api/mobile/profile")
@Tag(name = "Mobile Parent Profile API")
@Slf4j
public class MobileParentProfileController {
    
    @Autowired
    private ParentProfileService parentProfileService;
    
    @GetMapping
    @Operation(summary = "Get parent profile")
    public Result<Map<String, Object>> getProfile(HttpServletRequest request) {
        try {
            String userId = (String) request.getAttribute("supabaseUserId");
            log.info("Getting profile for user: {}", userId);
            
            ParentProfile profile = parentProfileService.getProfile(userId);
            
            if (profile == null) {
                Map<String, Object> data = new HashMap<>();
                data.put("profile", null);
                data.put("exists", false);
                return new Result<Map<String, Object>>().ok(data);
            }
            
            Map<String, Object> data = new HashMap<>();
            data.put("profile", profile);
            data.put("exists", true);
            data.put("onboardingCompleted", profile.isOnboardingCompleted());
            return new Result<Map<String, Object>>().ok(data);
                
        } catch (Exception e) {
            log.error("Error getting parent profile", e);
            return new Result<Map<String, Object>>().error("Failed to get profile: " + e.getMessage());
        }
    }
    
    @PostMapping("/create")
    @Operation(summary = "Create parent profile")
    public Result<Map<String, Object>> createProfile(@RequestBody ParentProfile profile, HttpServletRequest request) {
        try {
            String userId = (String) request.getAttribute("supabaseUserId");
            String email = (String) request.getAttribute("userEmail");
            
            log.info("Creating profile for user: {}", userId);
            
            profile.setSupabaseUserId(userId);
            if (profile.getEmail() == null && email != null) {
                profile.setEmail(email);
            }
            
            ParentProfile created = parentProfileService.createProfile(profile);
            
            Map<String, Object> data = new HashMap<>();
            data.put("profile", created);
            data.put("message", "Profile created successfully");
            return new Result<Map<String, Object>>().ok(data);
                
        } catch (Exception e) {
            log.error("Error creating parent profile", e);
            return new Result<Map<String, Object>>().error("Failed to create profile: " + e.getMessage());
        }
    }
    
    @PutMapping("/update")
    @Operation(summary = "Update parent profile")
    public Result<Map<String, Object>> updateProfile(@RequestBody ParentProfile profile, HttpServletRequest request) {
        try {
            String userId = (String) request.getAttribute("supabaseUserId");
            log.info("Updating profile for user: {}", userId);
            
            profile.setSupabaseUserId(userId);
            ParentProfile updated = parentProfileService.updateProfile(profile);
            
            Map<String, Object> data = new HashMap<>();
            data.put("profile", updated);
            data.put("message", "Profile updated successfully");
            return new Result<Map<String, Object>>().ok(data);
                
        } catch (Exception e) {
            log.error("Error updating parent profile", e);
            return new Result<Map<String, Object>>().error("Failed to update profile: " + e.getMessage());
        }
    }
    
    @PostMapping("/complete-onboarding")
    @Operation(summary = "Mark onboarding as completed")
    public Result<Map<String, Object>> completeOnboarding(HttpServletRequest request) {
        try {
            String userId = (String) request.getAttribute("supabaseUserId");
            log.info("Completing onboarding for user: {}", userId);
            
            boolean success = parentProfileService.completeOnboarding(userId);
            
            if (success) {
                Map<String, Object> data = new HashMap<>();
                data.put("message", "Onboarding completed successfully");
                return new Result<Map<String, Object>>().ok(data);
            } else {
                return new Result<Map<String, Object>>().error("Failed to complete onboarding");
            }
            
        } catch (Exception e) {
            log.error("Error completing onboarding", e);
            return new Result<Map<String, Object>>().error("Failed to complete onboarding: " + e.getMessage());
        }
    }
    
    @PostMapping("/accept-terms")
    @Operation(summary = "Accept terms and privacy policy")
    public Result<Map<String, Object>> acceptTerms(@RequestBody Map<String, Boolean> acceptance, HttpServletRequest request) {
        try {
            String userId = (String) request.getAttribute("supabaseUserId");
            boolean termsAccepted = acceptance.getOrDefault("termsAccepted", false);
            boolean privacyAccepted = acceptance.getOrDefault("privacyAccepted", false);
            
            log.info("Accepting terms for user: {} - Terms: {}, Privacy: {}", 
                userId, termsAccepted, privacyAccepted);
            
            boolean success = parentProfileService.acceptTerms(userId, termsAccepted, privacyAccepted);
            
            if (success) {
                Map<String, Object> data = new HashMap<>();
                data.put("message", "Terms accepted successfully");
                return new Result<Map<String, Object>>().ok(data);
            } else {
                return new Result<Map<String, Object>>().error("Failed to accept terms");
            }
            
        } catch (Exception e) {
            log.error("Error accepting terms", e);
            return new Result<Map<String, Object>>().error("Failed to accept terms: " + e.getMessage());
        }
    }
    
    @DeleteMapping
    @Operation(summary = "Delete parent profile")
    public Result<Map<String, Object>> deleteProfile(HttpServletRequest request) {
        try {
            String userId = (String) request.getAttribute("supabaseUserId");
            log.info("Deleting profile for user: {}", userId);
            
            boolean success = parentProfileService.deleteProfile(userId);
            
            if (success) {
                Map<String, Object> data = new HashMap<>();
                data.put("message", "Profile deleted successfully");
                return new Result<Map<String, Object>>().ok(data);
            } else {
                return new Result<Map<String, Object>>().error("Failed to delete profile");
            }
            
        } catch (Exception e) {
            log.error("Error deleting parent profile", e);
            return new Result<Map<String, Object>>().error("Failed to delete profile: " + e.getMessage());
        }
    }
}