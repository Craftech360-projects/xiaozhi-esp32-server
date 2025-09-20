package xiaozhi.modules.config.service;

import java.util.Map;

public interface LiveKitConfigService {
    /**
     * Get current LiveKit configuration
     * @return Current configuration
     */
    Map<String, Object> getCurrentConfig();

    /**
     * Sync configuration to LiveKit agent
     * @return Sync result
     */
    Map<String, Object> syncToLiveKit();

    /**
     * Notify LiveKit agent of configuration changes
     */
    void notifyConfigChange();

    /**
     * Get default models from database for LiveKit configuration
     * @return Default models map
     */
    Map<String, Object> getDefaultModels();
}