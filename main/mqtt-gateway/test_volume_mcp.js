const mqtt = require('mqtt');

// Connect to MQTT broker
const client = mqtt.connect('mqtt://192.168.1.101:1883');

client.on('connect', () => {
  console.log('Connected to MQTT broker for testing');

  // Subscribe to all device messages to see what gets sent
  client.subscribe('devices/+/+', (err) => {
    if (err) {
      console.error('Subscribe error:', err);
    } else {
      console.log('Subscribed to all device messages');
    }
  });

  // Simulate a function call from LiveKit (volume control)
  const functionCallMessage = {
    type: "function_call",
    function_call: {
      name: "self_set_volume",
      arguments: {
        volume: 50
      }
    },
    timestamp: new Date().toISOString(),
    request_id: "test_req_123"
  };

  console.log('\n🧪 [TEST] Sending function call message to internal/server-ingest:');
  console.log(JSON.stringify(functionCallMessage, null, 2));

  // Send the message to the gateway
  client.publish('internal/server-ingest', JSON.stringify(functionCallMessage), (err) => {
    if (err) {
      console.error('Publish error:', err);
    } else {
      console.log('✅ Function call message sent');
    }
  });
});

client.on('message', (topic, message) => {
  try {
    const data = JSON.parse(message.toString());
    console.log(`\n📨 [RECEIVED] Topic: ${topic}`);
    console.log('Message:', JSON.stringify(data, null, 2));
  } catch (e) {
    console.log(`\n📨 [RECEIVED] Topic: ${topic}`);
    console.log('Raw message:', message.toString());
  }
});

client.on('error', (err) => {
  console.error('MQTT error:', err);
});

// Exit after 10 seconds
setTimeout(() => {
  console.log('\n🔚 Test completed');
  client.end();
  process.exit(0);
}, 10000);