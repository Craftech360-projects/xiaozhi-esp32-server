package xiaozhi.modules.mobile.service.impl;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.core.namedparam.MapSqlParameterSource;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import xiaozhi.modules.mobile.entity.ActivationResponse;
import xiaozhi.modules.mobile.entity.DeviceStatusResponse;
import xiaozhi.modules.mobile.entity.UserDeviceResponse;
import xiaozhi.modules.mobile.service.MobileActivationService;

import java.util.*;
import java.time.LocalDateTime;
import java.time.ZoneId;

@Service
public class MobileActivationServiceImpl implements MobileActivationService {
    
    private static final Logger logger = LoggerFactory.getLogger(MobileActivationServiceImpl.class);
    
    @Autowired
    private JdbcTemplate jdbcTemplate;
    
    @Autowired
    private NamedParameterJdbcTemplate namedParameterJdbcTemplate;

    @Override
    @Transactional
    public ActivationResponse validateAndActivateDevice(
            String activationCode,
            String supabaseUserId,
            String childName,
            Integer childAge,
            List<String> childInterests) throws IllegalArgumentException, IllegalStateException {
        
        logger.info("Validating activation code: {} for user: {}", activationCode, supabaseUserId);
        
        // Generate mapping ID
        String mappingId = "pcm_" + UUID.randomUUID().toString().replace("-", "").substring(0, 28);
        
        // Call stored procedure to create parent-child mapping
        Map<String, Object> result = jdbcTemplate.queryForMap(
            "CALL CreateSampleParentChildMapping(?, ?, ?, ?)",
            supabaseUserId,
            "68:25:dd:bc:03:7c", // This should be retrieved from activation code mapping
            childName,
            childAge
        );
        
        // Build response
        ActivationResponse response = new ActivationResponse();
        response.setSuccess(true);
        response.setActivationId(result.get("mapping_id").toString());
        response.setToySerialNumber("CHEEKO-V1-" + System.currentTimeMillis());
        response.setToyModel("CHEEKO-V1");
        response.setDeviceMac("68:25:dd:bc:03:7c");
        response.setMessage("Device activated successfully");
        
        logger.info("Device activated successfully with mapping ID: {}", response.getActivationId());
        
        return response;
    }

    @Override
    public DeviceStatusResponse getActivationStatus(String activationId, String supabaseUserId) 
            throws IllegalArgumentException, SecurityException {
        
        logger.info("Getting activation status for: {} by user: {}", activationId, supabaseUserId);
        
        // Query parent_child_mapping table
        String sql = "SELECT pcm.*, ad.is_online, ad.last_connected_at " +
                    "FROM parent_child_mapping pcm " +
                    "LEFT JOIN ai_device ad ON pcm.device_mac_address = ad.mac_address " +
                    "WHERE pcm.id = ? AND pcm.supabase_user_id = ?";
        
        try {
            Map<String, Object> result = jdbcTemplate.queryForMap(sql, activationId, supabaseUserId);
            
            DeviceStatusResponse response = new DeviceStatusResponse();
            response.setActivationId(activationId);
            response.setStatus(result.get("activation_status").toString());
            response.setDeviceOnline(result.get("is_online") != null && (Boolean) result.get("is_online"));
            Date lastConnected = (Date) result.get("last_connected_at");
            if (lastConnected != null) {
                response.setDeviceLastSeen(lastConnected.toInstant().atZone(ZoneId.systemDefault()).toLocalDateTime());
            }
            response.setSyncStatus(response.getDeviceOnline() ? "connected" : "disconnected");
            response.setLastSync(LocalDateTime.now());
            
            return response;
            
        } catch (Exception e) {
            logger.error("Error getting activation status", e);
            throw new IllegalArgumentException("Activation not found or access denied");
        }
    }

    @Override
    public List<UserDeviceResponse> getUserDevices(String supabaseUserId) {
        logger.info("Getting devices for user: {}", supabaseUserId);
        
        String sql = "SELECT pcm.*, ad.is_online, ad.last_connected_at " +
                    "FROM parent_child_mapping pcm " +
                    "LEFT JOIN ai_device ad ON pcm.device_mac_address = ad.mac_address " +
                    "WHERE pcm.supabase_user_id = ? AND pcm.activation_status = 'active'";
        
        List<Map<String, Object>> results = jdbcTemplate.queryForList(sql, supabaseUserId);
        List<UserDeviceResponse> devices = new ArrayList<>();
        
        for (Map<String, Object> row : results) {
            UserDeviceResponse device = new UserDeviceResponse();
            device.setActivationId(row.get("id").toString());
            device.setChildName(row.get("child_name").toString());
            device.setChildAge((Integer) row.get("child_age"));
            device.setToyModel("CHEEKO-V1");
            device.setDeviceMac(row.get("device_mac_address").toString());
            device.setActivationStatus(row.get("activation_status").toString());
            device.setDeviceOnline(row.get("is_online") != null && (Boolean) row.get("is_online"));
            Date activatedDate = (Date) row.get("created_at");
            if (activatedDate != null) {
                device.setActivatedAt(activatedDate.toInstant().atZone(ZoneId.systemDefault()).toLocalDateTime());
            }
            
            devices.add(device);
        }
        
        return devices;
    }

    @Override
    public List<Map<String, String>> generateActivationCodes(int batchSize, String toyModel, String batchId) {
        logger.info("Generating {} activation codes for model: {}", batchSize, toyModel);
        
        List<Map<String, String>> codes = new ArrayList<>();
        Random random = new Random();
        
        for (int i = 0; i < batchSize; i++) {
            Map<String, String> code = new HashMap<>();
            // Generate 6-digit code
            String activationCode = String.format("%06d", random.nextInt(1000000));
            String serialNumber = toyModel + "-" + System.currentTimeMillis() + "-" + String.format("%06d", i);
            
            code.put("activation_code", activationCode);
            code.put("toy_serial_number", serialNumber);
            code.put("toy_model", toyModel);
            code.put("batch_id", batchId);
            
            codes.add(code);
        }
        
        return codes;
    }

    @Override
    public boolean isDeviceAvailable(String deviceMac) {
        String sql = "SELECT COUNT(*) FROM ai_device WHERE mac_address = ?";
        Integer count = jdbcTemplate.queryForObject(sql, Integer.class, deviceMac);
        
        if (count == 0) {
            return false;
        }
        
        // Check if already activated
        sql = "SELECT COUNT(*) FROM parent_child_mapping WHERE device_mac_address = ? AND activation_status = 'active'";
        count = jdbcTemplate.queryForObject(sql, Integer.class, deviceMac);
        
        return count == 0;
    }

    @Override
    @Transactional
    public void linkToRailwayDevice(String activationId, String deviceMac, String supabaseUserId) {
        logger.info("Linking activation {} to device {}", activationId, deviceMac);
        
        String sql = "UPDATE parent_child_mapping SET device_mac_address = ?, updated_at = NOW() " +
                    "WHERE id = ? AND supabase_user_id = ?";
        
        int updated = jdbcTemplate.update(sql, deviceMac, activationId, supabaseUserId);
        
        if (updated == 0) {
            throw new IllegalArgumentException("Failed to link device - activation not found or access denied");
        }
    }
}