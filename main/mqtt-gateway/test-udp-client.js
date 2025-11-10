const dgram = require('dgram');
const crypto = require('crypto');

/**
 * UDP Test Client for approom.js
 * Simulates an ESP32 device sending MQTT messages over UDP
 */

class UDPTestClient {
  constructor(serverHost = '192.168.1.166', serverPort = 1883) {
    this.serverHost = serverHost;
    this.serverPort = serverPort;
    this.client = dgram.createSocket('udp4');
    this.connectionId = 0;
    this.sequence = 0;
    this.macAddress = '68:25:dd:bb:f3:a0'; // Your MAC address
    this.clientId = `GID_test@@@${this.macAddress}`;
    this.sessionKey = null; // Will be set after CONNACK

    this.client.on('message', this.onMessage.bind(this));
    this.client.on('error', (err) => {
      console.error('❌ UDP Client Error:', err);
    });
  }

  onMessage(msg, rinfo) {
    console.log(`📨 Received UDP packet from ${rinfo.address}:${rinfo.port}, length: ${msg.length}`);

    if (msg.length < 16) {
      console.warn('⚠️ Packet too small');
      return;
    }

    const type = msg.readUInt8(0);
    const flag = msg.readUInt8(1);
    const payloadLength = msg.readUInt16BE(2);
    const connectionId = msg.readUInt32BE(4);
    const timestamp = msg.readUInt32BE(8);
    const sequence = msg.readUInt32BE(12);

    console.log(`   Type: ${type}, Flag: ${flag}, PayloadLen: ${payloadLength}, ConnID: ${connectionId}`);

    if (type === 2) {
      // CONNACK response
      this.connectionId = connectionId;
      console.log(`✅ Connected! Connection ID: ${this.connectionId}`);

      // Extract session key from payload if present
      if (msg.length > 16) {
        const payload = msg.slice(16);
        console.log(`   Payload (hex): ${payload.toString('hex')}`);

        // Parse MQTT CONNACK
        if (payload[0] === 0x20) { // CONNACK packet type
          console.log('   Received CONNACK from server');

          // Session key might be in the payload - for now we'll use a dummy
          // In real ESP32, this is negotiated during connection
          this.sessionKey = Buffer.alloc(16); // Dummy key
        }
      }

      // Now send the hello message
      setTimeout(() => {
        this.sendHelloMessage();
      }, 500);
    } else if (type === 1) {
      // Regular data packet
      if (msg.length > 16) {
        const payload = msg.slice(16);
        console.log(`📦 Data packet payload: ${payload.toString('hex')}`);
      }
    }
  }

  createUDPPacket(payload, encrypted = false) {
    // UDP packet format: [type: 1u, flag: 1u, payloadLength: 2u, cookie: 4u, timestamp: 4u, sequence: 4u, payload: n]
    const header = Buffer.alloc(16);
    const type = this.connectionId === 0 ? 0 : 1; // 0 = CONNECT, 1 = DATA
    const flag = encrypted ? 1 : 0;

    header.writeUInt8(type, 0);           // type
    header.writeUInt8(flag, 1);           // flag (0 = unencrypted, 1 = encrypted)
    header.writeUInt16BE(payload.length, 2); // payload length
    header.writeUInt32BE(this.connectionId, 4); // connection ID (0 for initial CONNECT)
    header.writeUInt32BE(Date.now() & 0xFFFFFFFF, 8); // timestamp
    header.writeUInt32BE(this.sequence++, 12); // sequence number

    return Buffer.concat([header, payload]);
  }

  createMQTTConnect() {
    // MQTT CONNECT packet
    const protocolName = 'MQTT';
    const protocolLevel = 4; // MQTT 3.1.1
    const connectFlags = 0xC2; // Clean session, username, password
    const keepAlive = 60;

    const clientId = this.clientId;
    const username = 'testuser';
    const password = 'testpassword';

    // Calculate packet length
    let length = 0;
    length += 2 + protocolName.length; // Protocol name
    length += 1; // Protocol level
    length += 1; // Connect flags
    length += 2; // Keep alive
    length += 2 + clientId.length; // Client ID
    length += 2 + username.length; // Username
    length += 2 + password.length; // Password

    const packet = Buffer.alloc(2 + length);
    let offset = 0;

    // Fixed header
    packet.writeUInt8(0x10, offset++); // CONNECT packet type
    packet.writeUInt8(length, offset++); // Remaining length

    // Variable header
    packet.writeUInt16BE(protocolName.length, offset);
    offset += 2;
    packet.write(protocolName, offset);
    offset += protocolName.length;
    packet.writeUInt8(protocolLevel, offset++);
    packet.writeUInt8(connectFlags, offset++);
    packet.writeUInt16BE(keepAlive, offset);
    offset += 2;

    // Payload
    packet.writeUInt16BE(clientId.length, offset);
    offset += 2;
    packet.write(clientId, offset);
    offset += clientId.length;

    packet.writeUInt16BE(username.length, offset);
    offset += 2;
    packet.write(username, offset);
    offset += username.length;

    packet.writeUInt16BE(password.length, offset);
    offset += 2;
    packet.write(password, offset);
    offset += password.length;

    return packet;
  }

  createMQTTPublish(topic, message) {
    // MQTT PUBLISH packet
    const payload = JSON.stringify(message);

    // Calculate remaining length
    let length = 0;
    length += 2 + topic.length; // Topic
    length += payload.length; // Payload

    const packet = Buffer.alloc(2 + length);
    let offset = 0;

    // Fixed header
    packet.writeUInt8(0x30, offset++); // PUBLISH packet type (QoS 0)
    packet.writeUInt8(length, offset++); // Remaining length

    // Variable header
    packet.writeUInt16BE(topic.length, offset);
    offset += 2;
    packet.write(topic, offset);
    offset += topic.length;

    // Payload
    packet.write(payload, offset);

    return packet;
  }

  connect() {
    console.log(`🔌 Connecting to ${this.serverHost}:${this.serverPort}...`);
    console.log(`   Client ID: ${this.clientId}`);

    const mqttConnect = this.createMQTTConnect();
    const udpPacket = this.createUDPPacket(mqttConnect, false);

    console.log(`📤 Sending CONNECT packet (${udpPacket.length} bytes)`);
    this.client.send(udpPacket, this.serverPort, this.serverHost, (err) => {
      if (err) {
        console.error('❌ Failed to send CONNECT:', err);
      } else {
        console.log('✅ CONNECT packet sent');
      }
    });
  }

  sendHelloMessage(roomType = 'conversation', language = null) {
    if (this.connectionId === 0) {
      console.error('❌ Not connected yet! Call connect() first.');
      return;
    }

    console.log(`\n📨 Sending hello message (room_type: ${roomType})...`);

    const topic = `GID_test/${this.macAddress}/app_to_device`;
    const message = {
      type: 'hello',
      version: 3,
      room_type: roomType
    };

    if (language) {
      message.language = language;
    }

    const mqttPublish = this.createMQTTPublish(topic, message);
    const udpPacket = this.createUDPPacket(mqttPublish, false);

    console.log(`📤 Sending PUBLISH to topic: ${topic}`);
    console.log(`   Message: ${JSON.stringify(message, null, 2)}`);

    this.client.send(udpPacket, this.serverPort, this.serverHost, (err) => {
      if (err) {
        console.error('❌ Failed to send hello:', err);
      } else {
        console.log('✅ Hello message sent');
      }
    });
  }

  close() {
    console.log('👋 Closing UDP client...');
    this.client.close();
  }
}

// Main test script
async function main() {
  const args = process.argv.slice(2);
  const roomType = args[0] || 'conversation';
  const language = args[1] || null;

  console.log('╔════════════════════════════════════════════╗');
  console.log('║   UDP Test Client for approom.js          ║');
  console.log('╚════════════════════════════════════════════╝\n');

  console.log(`🎯 Testing room type: ${roomType}`);
  if (language) {
    console.log(`🌐 Language: ${language}`);
  }
  console.log('');

  const client = new UDPTestClient();

  // Connect
  client.connect();

  // Keep alive for 60 seconds to see responses
  setTimeout(() => {
    console.log('\n⏰ Test completed, closing...');
    client.close();
    process.exit(0);
  }, 60000);
}

// Run if called directly
if (require.main === module) {
  main().catch(err => {
    console.error('❌ Test failed:', err);
    process.exit(1);
  });
}

module.exports = { UDPTestClient };
