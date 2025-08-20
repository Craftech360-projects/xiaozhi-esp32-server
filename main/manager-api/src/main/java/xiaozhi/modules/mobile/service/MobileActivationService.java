package xiaozhi.modules.mobile.service;

import xiaozhi.modules.mobile.entity.ActivationResponse;
import xiaozhi.modules.mobile.entity.DeviceStatusResponse;
import xiaozhi.modules.mobile.entity.UserDeviceResponse;

import java.util.List;
import java.util.Map;

/**
 * Mobile app device activation service
 */
public interface MobileActivationService {

    /**
     * Validate activation code and create device mapping
     */
    ActivationResponse validateAndActivateDevice(
            String activationCode,
            String supabaseUserId,
            String childName,
            Integer childAge,
            List<String> childInterests
    ) throws IllegalArgumentException, IllegalStateException;

    /**
     * Get activation status for a device
     */
    DeviceStatusResponse getActivationStatus(String activationId, String supabaseUserId) 
            throws IllegalArgumentException, SecurityException;

    /**
     * Get all devices for a user
     */
    List<UserDeviceResponse> getUserDevices(String supabaseUserId);

    /**
     * Generate activation codes for manufacturing
     */
    List<Map<String, String>> generateActivationCodes(int batchSize, String toyModel, String batchId);

    /**
     * Check if device exists and is available for activation
     */
    boolean isDeviceAvailable(String deviceMac);

    /**
     * Link activation to existing device in Railway database
     */
    void linkToRailwayDevice(String activationId, String deviceMac, String supabaseUserId);
}