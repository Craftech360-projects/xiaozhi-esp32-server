#!/usr/bin/env node

/**
 * Test script for audio recording control via MQTT
 * Demonstrates how to start, stop, and check recording status
 */

const mqtt = require('mqtt');

// Configuration
const BROKER_URL = 'mqtt://192.168.1.7:1883';
const DEVICE_ID = '28:56:2f:07:c6:ec'; // Replace with your device MAC address

class RecordingController {
  constructor(brokerUrl, deviceId) {
    this.brokerUrl = brokerUrl;
    this.deviceId = deviceId;
    this.client = null;
  }

  async connect() {
    return new Promise((resolve, reject) => {
      console.log(`🔌 [CONTROL] Connecting to MQTT broker: ${this.brokerUrl}`);
      
      this.client = mqtt.connect(this.brokerUrl, {
        clientId: `recording-controller-${Date.now()}`,
        clean: true,
        connectTimeout: 4000,
      });

      this.client.on('connect', () => {
        console.log('✅ [CONTROL] Connected to MQTT broker');
        
        // Subscribe to response topics
        const responseTopic = `control/recording/${this.deviceId}/+/response`;
        this.client.subscribe(responseTopic, (err) => {
          if (err) {
            console.error(`❌ [CONTROL] Failed to subscribe to responses: ${err.message}`);
            reject(err);
          } else {
            console.log(`📡 [CONTROL] Subscribed to: ${responseTopic}`);
            resolve();
          }
        });
      });

      this.client.on('message', (topic, message) => {
        this.handleResponse(topic, message);
      });

      this.client.on('error', (err) => {
        console.error(`❌ [CONTROL] MQTT error: ${err.message}`);
        reject(err);
      });
    });
  }

  handleResponse(topic, message) {
    try {
      const response = JSON.parse(message.toString());
      const topicParts = topic.split('/');
      const command = topicParts[3];

      console.log(`📨 [RESPONSE] ${command.toUpperCase()} response:`, response);

      if (response.success) {
        switch (command) {
          case 'status':
            if (response.recording) {
              console.log(`   🎵 Recording: ${response.stats.filePath}`);
              console.log(`   ⏱️ Duration: ${response.duration.toFixed(1)}s`);
              console.log(`   📦 Size: ${response.stats.totalBytes} bytes`);
            } else {
              console.log(`   🔇 Not recording (${response.reason || 'disabled'})`);
            }
            break;
          case 'start':
            console.log(`   ✅ ${response.message}`);
            break;
          case 'stop':
            console.log(`   🛑 ${response.message}`);
            break;
        }
      } else {
        console.log(`   ❌ Error: ${response.error}`);
        if (response.available_commands) {
          console.log(`   💡 Available commands: ${response.available_commands.join(', ')}`);
        }
      }
    } catch (error) {
      console.error(`❌ [RESPONSE] Error parsing response: ${error.message}`);
      console.log(`Raw message: ${message.toString()}`);
    }
  }

  sendCommand(command) {
    const topic = `control/recording/${this.deviceId}/${command}`;
    const payload = JSON.stringify({
      timestamp: new Date().toISOString(),
      source: 'test_controller'
    });

    console.log(`📤 [COMMAND] Sending ${command.toUpperCase()} to: ${topic}`);
    
    this.client.publish(topic, payload, (err) => {
      if (err) {
        console.error(`❌ [COMMAND] Failed to send ${command}: ${err.message}`);
      } else {
        console.log(`✅ [COMMAND] ${command.toUpperCase()} sent successfully`);
      }
    });
  }

  startRecording() {
    this.sendCommand('start');
  }

  stopRecording() {
    this.sendCommand('stop');
  }

  getStatus() {
    this.sendCommand('status');
  }

  disconnect() {
    if (this.client) {
      this.client.end();
      console.log('🔌 [CONTROL] Disconnected from MQTT broker');
    }
  }
}

/**
 * Interactive test menu
 */
async function runInteractiveTest() {
  const controller = new RecordingController(BROKER_URL, DEVICE_ID);
  
  try {
    await controller.connect();
    
    console.log('\\n🎛️ [MENU] Recording Control Test Menu');
    console.log('=====================================');
    console.log('Commands:');
    console.log('  1 - Start Recording');
    console.log('  2 - Stop Recording');
    console.log('  3 - Get Status');
    console.log('  4 - Auto Test (status -> start -> wait -> status -> stop)');
    console.log('  q - Quit');
    console.log('');

    // Simple command line interface
    const readline = require('readline');
    const rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout
    });

    const askCommand = () => {
      rl.question('Enter command (1-4, q): ', (answer) => {
        switch (answer.trim().toLowerCase()) {
          case '1':
            controller.startRecording();
            setTimeout(askCommand, 1000);
            break;
          case '2':
            controller.stopRecording();
            setTimeout(askCommand, 1000);
            break;
          case '3':
            controller.getStatus();
            setTimeout(askCommand, 1000);
            break;
          case '4':
            runAutoTest(controller);
            setTimeout(askCommand, 15000); // Wait for auto test to complete
            break;
          case 'q':
            console.log('👋 [MENU] Goodbye!');
            controller.disconnect();
            rl.close();
            process.exit(0);
            break;
          default:
            console.log('❓ [MENU] Invalid command. Please enter 1-4 or q.');
            askCommand();
        }
      });
    };

    askCommand();

  } catch (error) {
    console.error(`❌ [TEST] Failed to start test: ${error.message}`);
    process.exit(1);
  }
}

/**
 * Automated test sequence
 */
async function runAutoTest(controller) {
  console.log('\\n🤖 [AUTO] Starting automated test sequence...');
  
  // Step 1: Check initial status
  console.log('\\n📊 [AUTO] Step 1: Check initial status');
  controller.getStatus();
  
  await new Promise(resolve => setTimeout(resolve, 2000));
  
  // Step 2: Start recording
  console.log('\\n🎵 [AUTO] Step 2: Start recording');
  controller.startRecording();
  
  await new Promise(resolve => setTimeout(resolve, 2000));
  
  // Step 3: Check status while recording
  console.log('\\n📊 [AUTO] Step 3: Check status while recording');
  controller.getStatus();
  
  await new Promise(resolve => setTimeout(resolve, 5000));
  
  // Step 4: Check status again (should show progress)
  console.log('\\n📊 [AUTO] Step 4: Check status again');
  controller.getStatus();
  
  await new Promise(resolve => setTimeout(resolve, 2000));
  
  // Step 5: Stop recording
  console.log('\\n🛑 [AUTO] Step 5: Stop recording');
  controller.stopRecording();
  
  await new Promise(resolve => setTimeout(resolve, 2000));
  
  // Step 6: Final status check
  console.log('\\n📊 [AUTO] Step 6: Final status check');
  controller.getStatus();
  
  console.log('\\n✅ [AUTO] Automated test sequence completed!');
}

/**
 * Command line argument handling
 */
function main() {
  const args = process.argv.slice(2);
  
  if (args.length === 0) {
    console.log('🎛️ [CONTROL] Audio Recording Control Test');
    console.log('========================================');
    console.log(`Device ID: ${DEVICE_ID}`);
    console.log(`Broker: ${BROKER_URL}`);
    console.log('');
    runInteractiveTest();
    return;
  }

  // Handle direct commands
  const command = args[0].toLowerCase();
  const controller = new RecordingController(BROKER_URL, DEVICE_ID);
  
  controller.connect().then(() => {
    switch (command) {
      case 'start':
        controller.startRecording();
        setTimeout(() => process.exit(0), 2000);
        break;
      case 'stop':
        controller.stopRecording();
        setTimeout(() => process.exit(0), 2000);
        break;
      case 'status':
        controller.getStatus();
        setTimeout(() => process.exit(0), 2000);
        break;
      case 'auto':
        runAutoTest(controller).then(() => {
          setTimeout(() => process.exit(0), 2000);
        });
        break;
      default:
        console.log('❓ [USAGE] Usage: node test_recording_control.js [start|stop|status|auto]');
        console.log('   Or run without arguments for interactive mode');
        process.exit(1);
    }
  }).catch(error => {
    console.error(`❌ [ERROR] ${error.message}`);
    process.exit(1);
  });
}

// Handle Ctrl+C gracefully
process.on('SIGINT', () => {
  console.log('\\n👋 [EXIT] Received SIGINT, exiting...');
  process.exit(0);
});

if (require.main === module) {
  main();
}

module.exports = { RecordingController };