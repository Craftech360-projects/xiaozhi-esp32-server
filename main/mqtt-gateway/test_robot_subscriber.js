#!/usr/bin/env node
/**
 * Test MQTT Subscriber for Robot Control
 * 
 * This script subscribes to robot control MQTT topics and logs received messages.
 * Use this to verify that robot control commands are being sent correctly.
 * 
 * Usage:
 *   node test_robot_subscriber.js
 */

require('dotenv').config();
const mqtt = require('mqtt');

// MQTT Configuration from .env
const MQTT_HOST = process.env.MQTT_HOST || 'localhost';
const MQTT_PORT = process.env.MQTT_PORT || 1883;
const MQTT_USERNAME = process.env.MQTT_USERNAME || '';
const MQTT_PASSWORD = process.env.MQTT_PASSWORD || '';
const MQTT_CLIENT_ID = process.env.MQTT_CLIENT_ID || 'test_robot_subscriber';

console.log('🤖 Robot Control Test Subscriber');
console.log('================================');
console.log(`MQTT Broker: ${MQTT_HOST}:${MQTT_PORT}`);
console.log('');

// Connect to MQTT broker
const client = mqtt.connect(`mqtt://${MQTT_HOST}:${MQTT_PORT}`, {
  clientId: `test_robot_sub_${Date.now()}`,
  username: MQTT_USERNAME,
  password: MQTT_PASSWORD,
  clean: true,
  reconnectPeriod: 1000,
});

// Topics to subscribe to (simple topics without device ID)
const topics = [
  'robot/control',    // Main robot control topic
  'robot/status',     // Robot status updates
  'robot/#',          // All robot topics
];

client.on('connect', () => {
  console.log('✅ Connected to MQTT broker');
  console.log('');
  console.log('📡 Subscribing to topics:');
  
  topics.forEach(topic => {
    client.subscribe(topic, (err) => {
      if (err) {
        console.error(`❌ Failed to subscribe to ${topic}:`, err.message);
      } else {
        console.log(`   ✓ ${topic}`);
      }
    });
  });
  
  console.log('');
  console.log('🎧 Listening for robot control messages...');
  console.log('   (Press Ctrl+C to exit)');
  console.log('');
  console.log('─'.repeat(80));
  console.log('');
});

client.on('message', (topic, message) => {
  const timestamp = new Date().toISOString();
  
  try {
    // Try to parse as JSON
    const data = JSON.parse(message.toString());
    
    // Check if it's a robot control message
    const isRobotControl = 
      topic.includes('robot') ||
      (data.function_call && data.function_call.name === 'self_robot_control') ||
      (data.tool && data.tool.includes('robot'));
    
    if (isRobotControl) {
      console.log(`🤖 [${timestamp}] ROBOT CONTROL MESSAGE`);
      console.log(`   Topic: ${topic}`);
      console.log(`   Data:`, JSON.stringify(data, null, 2));
      console.log('');
      console.log('─'.repeat(80));
      console.log('');
    } else {
      // Log other messages briefly
      console.log(`📨 [${timestamp}] ${topic}`);
      if (data.function_call) {
        console.log(`   Function: ${data.function_call.name}`);
      }
    }
  } catch (e) {
    // Not JSON, log as raw message
    console.log(`📨 [${timestamp}] ${topic}`);
    console.log(`   Raw: ${message.toString().substring(0, 100)}...`);
  }
});

client.on('error', (err) => {
  console.error('❌ MQTT Error:', err.message);
});

client.on('close', () => {
  console.log('');
  console.log('🔌 Disconnected from MQTT broker');
});

// Handle graceful shutdown
process.on('SIGINT', () => {
  console.log('');
  console.log('');
  console.log('👋 Shutting down...');
  client.end();
  process.exit(0);
});

// Keep process alive
process.stdin.resume();
