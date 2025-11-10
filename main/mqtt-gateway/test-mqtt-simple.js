const mqtt = require('mqtt');

/**
 * Simple MQTT Test Client for approom.js
 * Connects to EMQX broker and sends hello messages
 */

class SimpleMQTTTest {
  constructor(macAddress = '68:25:dd:bb:f3:a0') {
    this.macAddress = macAddress;
    this.groupId = 'GID_test';
    this.uuid = `uuid-${Date.now()}`;
    this.clientId = `${this.groupId}@@@${this.macAddress.replace(/:/g, '_')}@@@${this.uuid}`;

    this.brokerUrl = 'mqtt://192.168.1.166:1883';
    this.username = 'testuser';
    this.password = 'testpassword';

    this.client = null;
  }

  connect() {
    return new Promise((resolve, reject) => {
      console.log('╔════════════════════════════════════════════╗');
      console.log('║   Simple MQTT Test Client                 ║');
      console.log('╚════════════════════════════════════════════╝\n');

      console.log(`🔌 Connecting to EMQX broker: ${this.brokerUrl}`);
      console.log(`   Client ID: ${this.clientId}`);
      console.log(`   Username: ${this.username}`);
      console.log(`   MAC Address: ${this.macAddress}\n`);

      this.client = mqtt.connect(this.brokerUrl, {
        clientId: this.clientId,
        username: this.username,
        password: this.password,
        clean: true,
        reconnectPeriod: 0 // Disable auto-reconnect for testing
      });

      this.client.on('connect', () => {
        console.log('✅ Connected to EMQX broker!\n');
        resolve();
      });

      this.client.on('error', (err) => {
        console.error('❌ Connection error:', err.message);
        reject(err);
      });

      this.client.on('message', (topic, message) => {
        console.log(`📨 Received message on topic: ${topic}`);
        console.log(`   Message: ${message.toString()}\n`);
      });
    });
  }

  sendHello(roomType = 'conversation', language = null) {
    return new Promise((resolve, reject) => {
      const topic = `${this.groupId}/${this.macAddress}/app_to_device`;

      const message = {
        type: 'hello',
        version: 3,
        room_type: roomType
      };

      if (language) {
        message.language = language;
      }

      console.log(`📤 Publishing to topic: ${topic}`);
      console.log(`   Message: ${JSON.stringify(message, null, 2)}\n`);

      this.client.publish(topic, JSON.stringify(message), { qos: 0 }, (err) => {
        if (err) {
          console.error('❌ Failed to publish:', err.message);
          reject(err);
        } else {
          console.log('✅ Hello message published successfully!\n');
          resolve();
        }
      });
    });
  }

  disconnect() {
    return new Promise((resolve) => {
      console.log('👋 Disconnecting from broker...');
      this.client.end(false, () => {
        console.log('✅ Disconnected\n');
        resolve();
      });
    });
  }
}

async function main() {
  const args = process.argv.slice(2);
  const roomType = args[0] || 'conversation';
  const language = args[1] || null;
  const macAddress = args[2] || '68:25:dd:bb:f3:a0';

  console.log(`🎯 Testing room type: ${roomType}`);
  if (language) {
    console.log(`🌐 Language: ${language}`);
  }
  console.log('');

  const client = new SimpleMQTTTest(macAddress);

  try {
    // Connect to broker
    await client.connect();

    // Wait a moment for connection to stabilize
    await new Promise(resolve => setTimeout(resolve, 500));

    // Send hello message
    await client.sendHello(roomType, language);

    // Wait to see any responses
    console.log('⏳ Waiting 10 seconds for responses...\n');
    await new Promise(resolve => setTimeout(resolve, 10000));

    // Disconnect
    await client.disconnect();

    console.log('✅ Test completed successfully!');
    process.exit(0);

  } catch (error) {
    console.error('❌ Test failed:', error.message);
    process.exit(1);
  }
}

// Run if called directly
if (require.main === module) {
  main();
}

module.exports = { SimpleMQTTTest };
