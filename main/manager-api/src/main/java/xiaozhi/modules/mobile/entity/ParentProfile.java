package xiaozhi.modules.mobile.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.fasterxml.jackson.annotation.JsonFormat;
import lombok.Data;

import java.util.Date;

/**
 * Parent Profile Entity
 * Maps to parent_profiles table in Railway MySQL
 */
@Data
@TableName("parent_profiles")
public class ParentProfile {
    
    @TableId(type = IdType.ASSIGN_UUID)
    private String id;
    
    /**
     * Supabase user ID (from auth.users)
     */
    @TableField("supabase_user_id")
    private String supabaseUserId;
    
    /**
     * Parent's full name
     */
    @TableField("full_name")
    private String fullName;
    
    /**
     * Phone number
     */
    @TableField("phone_number")
    private String phoneNumber;
    
    /**
     * Email address (from Supabase auth)
     */
    private String email;
    
    /**
     * Preferred language
     */
    @TableField("preferred_language")
    private String preferredLanguage = "en";
    
    /**
     * Timezone
     */
    private String timezone = "UTC";
    
    /**
     * Notification preferences as JSON
     */
    @TableField("notification_preferences")
    private String notificationPreferences = "{\"push\": true, \"email\": true, \"daily_summary\": true}";
    
    /**
     * Whether onboarding is completed
     */
    @TableField("onboarding_completed")
    private boolean onboardingCompleted = false;
    
    /**
     * Terms acceptance timestamp
     */
    @TableField("terms_accepted_at")
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss", timezone = "GMT+8")
    private Date termsAcceptedAt;
    
    /**
     * Privacy policy acceptance timestamp
     */
    @TableField("privacy_policy_accepted_at")
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss", timezone = "GMT+8")
    private Date privacyPolicyAcceptedAt;
    
    /**
     * Created timestamp
     */
    @TableField("created_at")
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss", timezone = "GMT+8")
    private Date createdAt;
    
    /**
     * Updated timestamp
     */
    @TableField("updated_at")
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss", timezone = "GMT+8")
    private Date updatedAt;
    
    /**
     * Number of active devices
     */
    @TableField("active_devices_count")
    private Integer activeDevicesCount;
}