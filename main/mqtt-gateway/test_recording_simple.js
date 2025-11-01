#!/usr/bin/env node

/**
 * Simple test script to send recording control messages to a device
 * This simulates what the client.py would send to control recording
 */

const mqtt = require('mqtt');

// Configuration - update these to match your setup
const BROKER_URL = 'mqtt://192.168.1.7:1883';
const DEVICE_MAC = '00:16:3e:ac:b5:38'; // Match the MAC from client.py

// Generate client ID similar to client.py
const CLIENT_ID = `GID_test@@@${DEVICE_MAC}@@@test-recording-control`;

console.log('🎛️ [TEST] Recording Control Test');
console.log('================================');
console.log(`Device MAC: ${DEVICE_MAC}`);
console.log(`Client ID: ${CLIENT_ID}`);
console.log(`Broker: ${BROKER_URL}`);
console.log('');

// Connect to MQTT broker
const client = mqtt.connect(BROKER_URL, {
  clientId: CLIENT_ID,
  clean: true,
  connectTimeout: 4000,
});

client.on('connect', () => {
  console.log('✅ [MQTT] Connected to broker');
  
  // Subscribe to responses (if any)
  const responseTopic = `devices/p2p/${CLIENT_ID}`;
  client.subscribe(responseTopic, (err) => {
    if (err) {
      console.error(`❌ [MQTT] Failed to subscribe: ${err.message}`);
    } else {
      console.log(`📡 [MQTT] Subscribed to: ${responseTopic}`);
      console.log('');
      showMenu();
    }
  });
});

client.on('message', (topic, message) => {
  try {
    const payload = JSON.parse(message.toString());
    console.log(`📨 [RESPONSE] Received on ${topic}:`);
    console.log(JSON.stringify(payload, null, 2));
    console.log('');
  } catch (error) {
    console.log(`📨 [RESPONSE] Raw message: ${message.toString()}`);
  }
});

client.on('error', (err) => {
  console.error(`❌ [MQTT] Connection error: ${err.message}`);
  process.exit(1);
});

function sendRecordingControl(command) {
  const topic = 'device-server';
  const payload = {
    type: 'recording_control',
    command: command,
    session_id: 'test-session',
    timestamp: new Date().toISOString()
  };

  console.log(`📤 [SEND] Sending ${command.toUpperCase()} command...`);
  client.publish(topic, JSON.stringify(payload), (err) => {
    if (err) {
      console.error(`❌ [SEND] Failed to send: ${err.message}`);
    } else {
      console.log(`✅ [SEND] Command sent successfully`);
    }
  });
}

function showMenu() {
  console.log('🎛️ [MENU] Available Commands:');
  console.log('  1 - Start Recording');
  console.log('  2 - Stop Recording');
  console.log('  3 - Get Status');
  console.log('  q - Quit');
  console.log('');
  console.log('Enter command (1-3, q): ');
}

// Simple command line interface
const readline = require('readline');
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

function askCommand() {
  rl.question('> ', (answer) => {
    switch (answer.trim().toLowerCase()) {
      case '1':
        sendRecordingControl('start');
        setTimeout(askCommand, 1000);
        break;
      case '2':
        sendRecordingControl('stop');
        setTimeout(askCommand, 1000);
        break;
      case '3':
        sendRecordingControl('status');
        setTimeout(askCommand, 1000);
        break;
      case 'q':
        console.log('👋 [EXIT] Goodbye!');
        client.end();
        rl.close();
        process.exit(0);
        break;
      case 'help':
      case 'h':
        showMenu();
        askCommand();
        break;
      default:
        console.log('❓ [MENU] Invalid command. Enter 1-3 or q (or "help" for menu)');
        askCommand();
    }
  });
}

// Handle Ctrl+C gracefully
process.on('SIGINT', () => {
  console.log('\\n👋 [EXIT] Received SIGINT, exiting...');
  client.end();
  rl.close();
  process.exit(0);
});

// Auto-test mode if command line argument provided
if (process.argv[2]) {
  const command = process.argv[2].toLowerCase();
  
  client.on('connect', () => {
    console.log('✅ [MQTT] Connected for auto-test');
    
    setTimeout(() => {
      switch (command) {
        case 'start':
          sendRecordingControl('start');
          break;
        case 'stop':
          sendRecordingControl('stop');
          break;
        case 'status':
          sendRecordingControl('status');
          break;
        default:
          console.log('❓ [USAGE] Usage: node test_recording_simple.js [start|stop|status]');
          console.log('   Or run without arguments for interactive mode');
      }
      
      setTimeout(() => {
        client.end();
        process.exit(0);
      }, 2000);
    }, 1000);
  });
}