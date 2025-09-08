package xiaozhi.modules.device.service;

import org.eclipse.paho.client.mqttv3.MqttClient;
import org.eclipse.paho.client.mqttv3.MqttCallback;
import org.eclipse.paho.client.mqttv3.MqttConnectOptions;
import org.eclipse.paho.client.mqttv3.MqttException;
import org.eclipse.paho.client.mqttv3.MqttMessage;
import org.eclipse.paho.client.mqttv3.IMqttDeliveryToken;
import org.eclipse.paho.client.mqttv3.persist.MemoryPersistence;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import lombok.extern.slf4j.Slf4j;
import jakarta.annotation.PostConstruct;
import jakarta.annotation.PreDestroy;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

@Slf4j
@Service
public class MqttPublisherService implements MqttCallback {
    
    @Value("${mqtt.broker:tcp://64.227.170.31:1883}")
    private String broker;
    
    @Value("${mqtt.username:}")
    private String username;
    
    @Value("${mqtt.password:}")
    private String password;
    
    private MqttClient mqttClient;
    private ObjectMapper objectMapper = new ObjectMapper();
    
    @PostConstruct
    public void init() {
        connectToMqtt();
    }
    
    private synchronized void connectToMqtt() {
        try {
            if (mqttClient != null && mqttClient.isConnected()) {
                return;
            }
            
            String clientId = "JavaBackend_" + UUID.randomUUID().toString();
            mqttClient = new MqttClient(broker, clientId, new MemoryPersistence());
            mqttClient.setCallback(this);
            
            MqttConnectOptions options = new MqttConnectOptions();
            options.setCleanSession(true);
            options.setAutomaticReconnect(true);
            options.setConnectionTimeout(30);
            options.setKeepAliveInterval(60);
            options.setMaxInflight(10);
            
            if (username != null && !username.isEmpty()) {
                options.setUserName(username);
            }
            if (password != null && !password.isEmpty()) {
                options.setPassword(password.toCharArray());
            }
            
            mqttClient.connect(options);
            log.info("Connected to MQTT broker: {}", broker);
            log.info("MQTT Client ID: {}", clientId);
            
        } catch (MqttException e) {
            log.error("Failed to connect to MQTT broker: {}", e.getMessage(), e);
        }
    }
    
    public boolean sendPlayCommand(String deviceMacAddress, String contentTitle) {
        try {
            // IMPORTANT: Publish to device-server topic, NOT P2P topic
            // The xiaozhi-server listens on device-server and processes commands
            String topic = "device-server";
            
            // Create listen message that will trigger play_music function
            // This mimics what happens when user says "play a song" via voice
            Map<String, Object> message = new HashMap<>();
            message.put("type", "listen");
            message.put("session_id", "mobile_" + System.currentTimeMillis());
            message.put("state", "detect");
            message.put("text", "play " + contentTitle);
            
            // Add device identifier so server knows which device this is for
            message.put("device_mac", deviceMacAddress);
            
            String jsonMessage = objectMapper.writeValueAsString(message);
            
            MqttMessage mqttMessage = new MqttMessage(jsonMessage.getBytes());
            mqttMessage.setQos(1);
            
            // Ensure connection before publishing
            if (!ensureConnected()) {
                log.error("Failed to establish MQTT connection for device {}", deviceMacAddress);
                return false;
            }
            
            try {
                mqttClient.publish(topic, mqttMessage);
                log.info("✅ Successfully published MQTT message to topic: {}", topic);
                log.info("📨 Message details - Device: {}, Content: {}, Message: {}", 
                    deviceMacAddress, contentTitle, jsonMessage);
                return true;
            } catch (MqttException publishEx) {
                log.error("Failed to publish MQTT message to topic {}: {}", topic, publishEx.getMessage());
                return false;
            }
            
        } catch (Exception e) {
            log.error("Failed to send play command via MQTT: {}", e.getMessage(), e);
            return false;
        }
    }
    
    private synchronized boolean ensureConnected() {
        try {
            if (mqttClient == null || !mqttClient.isConnected()) {
                log.info("MQTT client not connected, attempting to reconnect...");
                connectToMqtt();
                Thread.sleep(500); // Give it a moment to connect
            }
            return mqttClient != null && mqttClient.isConnected();
        } catch (Exception e) {
            log.error("Error ensuring MQTT connection: {}", e.getMessage());
            return false;
        }
    }
    
    // MqttCallback implementation
    @Override
    public void connectionLost(Throwable cause) {
        log.warn("MQTT connection lost: {}", cause.getMessage());
        log.info("Attempting to reconnect to MQTT broker...");
        connectToMqtt();
    }
    
    @Override
    public void messageArrived(String topic, MqttMessage message) throws Exception {
        // Not subscribing to any topics, so this won't be called
    }
    
    @Override
    public void deliveryComplete(IMqttDeliveryToken token) {
        try {
            log.debug("Message delivery complete for message ID: {}", token.getMessageId());
        } catch (Exception e) {
            log.debug("Message delivery complete");
        }
    }
    
    @PreDestroy
    public void cleanup() {
        try {
            if (mqttClient != null && mqttClient.isConnected()) {
                mqttClient.disconnect();
                mqttClient.close();
                log.info("Disconnected from MQTT broker");
            }
        } catch (MqttException e) {
            log.error("Error disconnecting from MQTT broker", e);
        }
    }
}