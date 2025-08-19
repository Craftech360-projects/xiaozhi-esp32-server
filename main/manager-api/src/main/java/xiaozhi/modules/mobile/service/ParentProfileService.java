package xiaozhi.modules.mobile.service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.core.conditions.update.UpdateWrapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import xiaozhi.modules.mobile.dao.ParentProfileDao;
import xiaozhi.modules.mobile.entity.ParentProfile;

import java.util.Date;

/**
 * Parent Profile Service
 * Handles parent profile management
 */
@Service
@Slf4j
public class ParentProfileService {
    
    @Autowired
    private ParentProfileDao parentProfileDao;
    
    /**
     * Get parent profile by Supabase user ID
     */
    public ParentProfile getProfile(String supabaseUserId) {
        QueryWrapper<ParentProfile> wrapper = new QueryWrapper<>();
        wrapper.eq("supabase_user_id", supabaseUserId);
        
        ParentProfile profile = parentProfileDao.selectOne(wrapper);
        
        // Get active devices count
        if (profile != null) {
            int activeDevices = getActiveDevicesCount(supabaseUserId);
            profile.setActiveDevicesCount(activeDevices);
        }
        
        return profile;
    }
    
    /**
     * Create new parent profile
     */
    @Transactional
    public ParentProfile createProfile(ParentProfile profile) {
        // Check if profile already exists
        ParentProfile existing = getProfile(profile.getSupabaseUserId());
        if (existing != null) {
            log.warn("Profile already exists for user: {}", profile.getSupabaseUserId());
            return existing;
        }
        
        // Set timestamps
        profile.setCreatedAt(new Date());
        profile.setUpdatedAt(new Date());
        
        // Insert profile
        parentProfileDao.insert(profile);
        
        log.info("Created profile for user: {}", profile.getSupabaseUserId());
        return profile;
    }
    
    /**
     * Update parent profile
     */
    @Transactional
    public ParentProfile updateProfile(ParentProfile profile) {
        // Get existing profile
        ParentProfile existing = getProfile(profile.getSupabaseUserId());
        if (existing == null) {
            log.error("Profile not found for user: {}", profile.getSupabaseUserId());
            throw new RuntimeException("Profile not found");
        }
        
        // Preserve ID and timestamps
        profile.setId(existing.getId());
        profile.setCreatedAt(existing.getCreatedAt());
        profile.setUpdatedAt(new Date());
        
        // Update profile
        UpdateWrapper<ParentProfile> wrapper = new UpdateWrapper<>();
        wrapper.eq("supabase_user_id", profile.getSupabaseUserId());
        
        parentProfileDao.update(profile, wrapper);
        
        log.info("Updated profile for user: {}", profile.getSupabaseUserId());
        return profile;
    }
    
    /**
     * Complete onboarding for user
     */
    @Transactional
    public boolean completeOnboarding(String supabaseUserId) {
        UpdateWrapper<ParentProfile> wrapper = new UpdateWrapper<>();
        wrapper.eq("supabase_user_id", supabaseUserId)
               .set("onboarding_completed", true)
               .set("updated_at", new Date());
        
        int rows = parentProfileDao.update(null, wrapper);
        
        if (rows > 0) {
            log.info("Completed onboarding for user: {}", supabaseUserId);
            return true;
        } else {
            log.error("Failed to complete onboarding for user: {}", supabaseUserId);
            return false;
        }
    }
    
    /**
     * Accept terms and privacy policy
     */
    @Transactional
    public boolean acceptTerms(String supabaseUserId, boolean termsAccepted, boolean privacyAccepted) {
        UpdateWrapper<ParentProfile> wrapper = new UpdateWrapper<>();
        wrapper.eq("supabase_user_id", supabaseUserId)
               .set("updated_at", new Date());
        
        if (termsAccepted) {
            wrapper.set("terms_accepted_at", new Date());
        }
        
        if (privacyAccepted) {
            wrapper.set("privacy_policy_accepted_at", new Date());
        }
        
        int rows = parentProfileDao.update(null, wrapper);
        
        if (rows > 0) {
            log.info("Accepted terms for user: {} - Terms: {}, Privacy: {}", 
                supabaseUserId, termsAccepted, privacyAccepted);
            return true;
        } else {
            log.error("Failed to accept terms for user: {}", supabaseUserId);
            return false;
        }
    }
    
    /**
     * Delete parent profile
     */
    @Transactional
    public boolean deleteProfile(String supabaseUserId) {
        QueryWrapper<ParentProfile> wrapper = new QueryWrapper<>();
        wrapper.eq("supabase_user_id", supabaseUserId);
        
        int rows = parentProfileDao.delete(wrapper);
        
        if (rows > 0) {
            log.info("Deleted profile for user: {}", supabaseUserId);
            return true;
        } else {
            log.error("Failed to delete profile for user: {}", supabaseUserId);
            return false;
        }
    }
    
    /**
     * Get count of active devices for user
     */
    private int getActiveDevicesCount(String supabaseUserId) {
        // TODO: Query device_activations table
        // For now, return 0
        return 0;
    }
}