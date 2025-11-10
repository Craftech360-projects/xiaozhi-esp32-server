const mqtt = require('mqtt');

/**
 * Direct MQTT Test Client for approom.js
 * Publishes directly to internal/server-ingest topic (bypasses EMQX rule)
 */

class DirectMQTTTest {
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
      console.log('║   Direct MQTT Test Client                 ║');
      console.log('║   (Bypasses EMQX rule)                     ║');
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
        reconnectPeriod: 0
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
      // Publish directly to internal/server-ingest with EMQX format
      const topic = 'internal/server-ingest';

      const originalPayload = {
        type: 'hello',
        version: 3,
        room_type: roomType
      };

      if (language) {
        originalPayload.language = language;
      }

      // Format expected by approom.js from EMQX rule
      const emqxPayload = {
        sender_client_id: this.clientId,
        orginal_payload: originalPayload  // Note: typo "orginal" is intentional (matches EMQX)
      };

      console.log(`📤 Publishing directly to: ${topic}`);
      console.log(`   Sender Client ID: ${this.clientId}`);
      console.log(`   Room Type: ${roomType}`);
      if (language) {
        console.log(`   Language: ${language}`);
      }
      console.log(`   Full payload: ${JSON.stringify(emqxPayload, null, 2)}\n`);

      this.client.publish(topic, JSON.stringify(emqxPayload), { qos: 0 }, (err) => {
        if (err) {
          console.error('❌ Failed to publish:', err.message);
          reject(err);
        } else {
          console.log('✅ Hello message published successfully to internal/server-ingest!\n');
          console.log('📋 Expected behavior in approom.js:');
          console.log(`   1. Should see: "📨 [MQTT IN] Received message on topic: internal/server-ingest"`);
          console.log(`   2. Should see: "📱 [ROOM-TYPE] Device ${this.macAddress} requesting ${roomType} room"`);
          console.log(`   3. Should see: "🏠 [ROOM-NAME] Room will be: <uuid>_${this.macAddress.replace(/:/g, '')}_${roomType}"`);

          if (roomType === 'conversation') {
            console.log(`   4. Should see: "🗣️ [CONVERSATION] Waiting for agent dispatch..."`);
          } else if (roomType === 'music') {
            console.log(`   4. Should see: "🎵 [MUSIC] Spawning music bot via Python API..."`);
          } else if (roomType === 'story') {
            console.log(`   4. Should see: "📖 [STORY] Spawning story bot via Python API..."`);
          }
          console.log('');

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

  const client = new DirectMQTTTest(macAddress);

  try {
    // Connect to broker
    await client.connect();

    // Wait a moment for connection to stabilize
    await new Promise(resolve => setTimeout(resolve, 500));

    // Send hello message
    await client.sendHello(roomType, language);

    // Wait to see any responses
    console.log('⏳ Waiting 15 seconds to observe approom.js logs...\n');
    await new Promise(resolve => setTimeout(resolve, 15000));

    // Disconnect
    await client.disconnect();

    console.log('✅ Test completed!');
    console.log('\n💡 Check approom.js terminal for the expected logs above.');
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

module.exports = { DirectMQTTTest };
