package xiaozhi.modules.device.service;

import java.util.Map;

import xiaozhi.common.page.PageData;
import xiaozhi.common.service.BaseService;
import xiaozhi.modules.device.entity.OtaEntity;

/**
 * OTA固件管理
 */
public interface OtaService extends BaseService<OtaEntity> {
    PageData<OtaEntity> page(Map<String, Object> params);

    boolean save(OtaEntity entity);

    void update(OtaEntity entity);

    void delete(String[] ids);

    OtaEntity getLatestOta(String type);

    /**
     * Get force update firmware by type
     * @param type Firmware type
     * @return Force update firmware or null if no force update is set
     */
    OtaEntity getForceUpdateFirmware(String type);

    /**
     * Set force update for a specific firmware
     * Automatically disables force update for other firmwares of the same type
     * @param id Firmware ID
     * @param type Firmware type
     * @param forceUpdate 0-disable, 1-enable
     */
    void setForceUpdate(String id, String type, Integer forceUpdate);
}