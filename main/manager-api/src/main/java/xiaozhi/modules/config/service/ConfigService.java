package xiaozhi.modules.config.service;

import java.util.Map;

public interface ConfigService {
    /**
     * 获取服务器配置
     * 
     * @param isCache 是否缓存
     * @return 配置信息
     */
    Object getConfig(Boolean isCache);

    /**
     * 获取智能体模型配置
     *
     * @param macAddress     MAC地址
     * @param selectedModule 客户端已实例化的模型
     * @return 模型配置信息
     */
    Map<String, Object> getAgentModels(String macAddress, Map<String, String> selectedModule);

    /**
     * 获取智能体提示词
     *
     * @param macAddress MAC地址
     * @return 智能体提示词
     */
    String getAgentPrompt(String macAddress);

    /**
     * 获取设备关联的孩子资料
     *
     * @param macAddress MAC地址
     * @return 孩子资料
     */
    xiaozhi.modules.config.dto.ChildProfileDTO getChildProfileByMac(String macAddress);

    /**
     * 获取智能体模板ID
     *
     * @param macAddress MAC地址
     * @return 模板ID
     */
    String getAgentTemplateId(String macAddress);

    /**
     * 获取模板内容（personality）
     *
     * @param templateId 模板ID
     * @return 模板内容
     */
    String getTemplateContent(String templateId);

    /**
     * 获取设备位置信息
     *
     * @param macAddress MAC地址
     * @return 位置信息（城市名称）
     */
    String getDeviceLocation(String macAddress);

    /**
     * 获取天气预报
     *
     * @param location 位置（城市名称）
     * @return 天气预报文本
     */
    String getWeatherForecast(String location);
}