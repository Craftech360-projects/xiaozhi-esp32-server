// Simple test client to trigger PCM streaming test
// This will help you isolate jitter issues by bypassing LiveKit

const mqtt = require('mqtt');

class PCMTestClient {
  constructor(brokerUrl, deviceMac, deviceUuid) {
    this.brokerUrl = brokerUrl || 'mqtt://localhost:1883';
    this.deviceMac = deviceMac || '00:16:3e:ac:b5:38'; // Default test MAC
    this.deviceUuid = deviceUuid || 'test-uuid-123';
    this.clientId = `GID_test@@@${this.deviceMac.replace(/:/g, '_')}@@@${this.deviceUuid}`;
    this.client = null;
    this.sessionId = null;
  }

  async connect() {
    console.log(`🔌 [TEST-CLIENT] Connecting to MQTT broker: ${this.brokerUrl}`);
    console.log(`📱 [TEST-CLIENT] Client ID: ${this.clientId}`);
    
    this.client = mqtt.connect(this.brokerUrl, {
      clientId: this.clientId,
      clean: true,
      keepalive: 60,
      reconnectPeriod: 1000,
    });

    return new Promise((resolve, reject) => {
      this.client.on('connect', () => {
        console.log(`✅ [TEST-CLIENT] Connected to MQTT broker`);
        
        // Subscribe to device response topic
        const responseTopic = `devices/p2p/${this.deviceMac.replace(/:/g, '_')}`;
        this.client.subscribe(responseTopic, (err) => {
          if (err) {
            console.error(`❌ [TEST-CLIENT] Failed to subscribe to ${responseTopic}:`, err);
            reject(err);
          } else {
            console.log(`📡 [TEST-CLIENT] Subscribed to response topic: ${responseTopic}`);
            resolve();
          }
        });
      });

      this.client.on('error', (err) => {
        console.error(`❌ [TEST-CLIENT] MQTT connection error:`, err);
        reject(err);
      });

      this.client.on('message', (topic, message) => {
        this.handleMessage(topic, message);
      });
    });
  }

  handleMessage(topic, message) {
    try {
      const data = JSON.parse(message.toString());
      console.log(`📨 [TEST-CLIENT] Received message on ${topic}:`, data);

      switch (data.type) {
        case 'hello':
          this.sessionId = data.session_id;
          console.log(`🤝 [TEST-CLIENT] Hello received, session ID: ${this.sessionId}`);
          console.log(`🔊 [TEST-CLIENT] Audio params:`, data.audio_params);
          console.log(`🔐 [TEST-CLIENT] UDP config:`, data.udp);
          break;
          
        case 'test_pcm_ack':
          console.log(`✅ [TEST-CLIENT] PCM test acknowledged: ${data.message}`);
          break;
          
        case 'test_pcm_error':
          console.error(`❌ [TEST-CLIENT] PCM test error: ${data.message}`);
          break;
          
        case 'goodbye':
          console.log(`👋 [TEST-CLIENT] Goodbye received: ${data.reason || 'No reason'}`);
          break;
          
        default:
          console.log(`📝 [TEST-CLIENT] Other message type: ${data.type}`);
      }
    } catch (err) {
      console.error(`❌ [TEST-CLIENT] Error parsing message:`, err);
    }
  }

  async sendHello() {
    console.log(`🤝 [TEST-CLIENT] Sending hello message...`);
    
    const helloMessage = {
      type: "hello",
      version: 3,
      audio_params: {
        sample_rate: 16000,
        channels: 1,
        frame_duration: 60,
        format: "opus"
      },
      features: ["audio_streaming", "pcm_test"]
    };

    const topic = `devices/p2p/${this.deviceMac.replace(/:/g, '_')}/tx`;
    
    return new Promise((resolve, reject) => {
      this.client.publish(topic, JSON.stringify(helloMessage), (err) => {
        if (err) {
          console.error(`❌ [TEST-CLIENT] Failed to send hello:`, err);
          reject(err);
        } else {
          console.log(`✅ [TEST-CLIENT] Hello message sent to ${topic}`);
          resolve();
        }
      });
    });
  }

  async sendPCMTest() {
    if (!this.sessionId) {
      console.error(`❌ [TEST-CLIENT] No session ID available, send hello first`);
      return;
    }

    console.log(`🧪 [TEST-CLIENT] Sending PCM test command...`);
    
    const testMessage = {
      type: "test_pcm",
      session_id: this.sessionId,
      timestamp: Date.now()
    };

    const topic = `devices/p2p/${this.deviceMac.replace(/:/g, '_')}/tx`;
    
    return new Promise((resolve, reject) => {
      this.client.publish(topic, JSON.stringify(testMessage), (err) => {
        if (err) {
          console.error(`❌ [TEST-CLIENT] Failed to send PCM test:`, err);
          reject(err);
        } else {
          console.log(`✅ [TEST-CLIENT] PCM test command sent to ${topic}`);
          resolve();
        }
      });
    });
  }

  async sendGoodbye() {
    if (!this.sessionId) {
      console.error(`❌ [TEST-CLIENT] No session ID available`);
      return;
    }

    console.log(`👋 [TEST-CLIENT] Sending goodbye message...`);
    
    const goodbyeMessage = {
      type: "goodbye",
      session_id: this.sessionId,
      timestamp: Date.now()
    };

    const topic = `devices/p2p/${this.deviceMac.replace(/:/g, '_')}/tx`;
    
    return new Promise((resolve, reject) => {
      this.client.publish(topic, JSON.stringify(goodbyeMessage), (err) => {
        if (err) {
          console.error(`❌ [TEST-CLIENT] Failed to send goodbye:`, err);
          reject(err);
        } else {
          console.log(`✅ [TEST-CLIENT] Goodbye message sent to ${topic}`);
          resolve();
        }
      });
    });
  }

  disconnect() {
    if (this.client) {
      this.client.end();
      console.log(`🔌 [TEST-CLIENT] Disconnected from MQTT broker`);
    }
  }
}

// Main test function
async function runPCMTest() {
  const client = new PCMTestClient();
  
  try {
    // Connect to MQTT broker
    await client.connect();
    
    // Wait a moment for connection to stabilize
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // Send hello to establish session
    await client.sendHello();
    
    // Wait for hello response
    await new Promise(resolve => setTimeout(resolve, 3000));
    
    // Send PCM test command
    await client.sendPCMTest();
    
    // Wait for test to complete (adjust based on your PCM file length)
    console.log(`⏳ [TEST-CLIENT] Waiting for PCM streaming test to complete...`);
    await new Promise(resolve => setTimeout(resolve, 30000)); // 30 seconds
    
    // Send goodbye
    await client.sendGoodbye();
    
    // Wait a moment then disconnect
    await new Promise(resolve => setTimeout(resolve, 2000));
    client.disconnect();
    
    console.log(`✅ [TEST-CLIENT] PCM test completed successfully`);
    
  } catch (error) {
    console.error(`❌ [TEST-CLIENT] Test failed:`, error);
    client.disconnect();
  }
}

// Export for use as module or run directly
if (require.main === module) {
  runPCMTest();
}

module.exports = { PCMTestClient, runPCMTest };