// Test MQTT connection with the same credentials format as the toy
const mqtt = require('mqtt');
const crypto = require('crypto');

// Configuration
const MQTT_BROKER = '192.168.1.235';
const MQTT_PORT = 1883;
const SIGNATURE_KEY = 'test-signature-key-12345';

// Simulate device credentials
const macAddress = '28:56:2f:00:10:58';
const clientUuid = crypto.randomUUID();
const groupId = 'GID_test';
const clientId = `${groupId}@@@${macAddress.replace(/:/g, '_')}@@@${clientUuid}`;

// Generate username (base64 encoded JSON with IP)
const clientIp = '192.168.1.235';
const userData = JSON.stringify({ ip: clientIp });
const username = Buffer.from(userData).toString('base64');

// Generate password (HMAC-SHA256 signature)
const content = `${clientId}|${username}`;
const hmac = crypto.createHmac('sha256', SIGNATURE_KEY);
hmac.update(content);
const password = hmac.digest('base64');

console.log('🔐 MQTT Connection Details:');
console.log('  Broker:', `${MQTT_BROKER}:${MQTT_PORT}`);
console.log('  Client ID:', clientId);
console.log('  Username:', username);
console.log('  Password:', password);
console.log('');

// Connect to MQTT
const client = mqtt.connect(`mqtt://${MQTT_BROKER}:${MQTT_PORT}`, {
    clientId: clientId,
    username: username,
    password: password,
    clean: true,
    keepalive: 60,
    reconnectPeriod: 5000
});

client.on('connect', () => {
    console.log('✅ Successfully connected to MQTT broker!');
    console.log('');

    // Publish a test message
    const testMessage = JSON.stringify({
        type: 'test',
        device_id: macAddress,
        timestamp: Date.now(),
        message: 'Test message from Node.js client'
    });

    console.log('📤 Publishing test message to topic: device-server');
    client.publish('device-server', testMessage, { qos: 0 }, (err) => {
        if (err) {
            console.error('❌ Failed to publish:', err);
        } else {
            console.log('✅ Message published successfully!');
            console.log('   Message:', testMessage);
        }

        // Disconnect after 2 seconds
        setTimeout(() => {
            console.log('');
            console.log('Disconnecting...');
            client.end();
        }, 2000);
    });
});

client.on('error', (err) => {
    console.error('❌ Connection error:', err.message);
    client.end();
});

client.on('close', () => {
    console.log('🔌 Connection closed');
    process.exit(0);
});

client.on('offline', () => {
    console.log('⚠️  Client went offline');
});

// Timeout after 10 seconds
setTimeout(() => {
    if (!client.connected) {
        console.error('❌ Connection timeout - could not connect to MQTT broker');
        client.end(true);
        process.exit(1);
    }
}, 10000);