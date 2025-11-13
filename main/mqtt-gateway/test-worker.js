#!/usr/bin/env node

// Test worker thread Opus encoding
const { Worker } = require('worker_threads');

console.log('🧪 Testing worker thread Opus encoding...');

async function testWorker() {
  const worker = new Worker('./audio-worker.js');
  
  // Initialize encoder
  console.log('📤 Initializing encoder...');
  worker.postMessage({ 
    id: 1, 
    type: 'init_encoder', 
    data: { sampleRate: 24000, channels: 1 } 
  });

  // Wait for initialization
  await new Promise((resolve, reject) => {
    const timeout = setTimeout(() => reject(new Error('Init timeout')), 5000);
    worker.on('message', (msg) => {
      if (msg.id === 1) {
        clearTimeout(timeout);
        if (msg.success) {
          console.log('✅ Encoder initialized');
          resolve();
        } else {
          reject(new Error(msg.error));
        }
      }
    });
  });

  // Create test PCM data
  const frameSize = 1440; // 60ms at 24kHz
  const pcmData = Buffer.alloc(frameSize * 2); // 2880 bytes
  
  // Fill with test audio data
  for (let i = 0; i < frameSize; i++) {
    const sample = Math.sin(2 * Math.PI * 440 * i / 24000) * 16384;
    pcmData.writeInt16LE(Math.round(sample), i * 2);
  }

  console.log(`✅ Created test PCM data: ${pcmData.length} bytes`);

  // Test encoding multiple times
  for (let i = 0; i < 10; i++) {
    try {
      const requestId = i + 2;
      
      worker.postMessage({
        id: requestId,
        type: 'encode',
        data: { pcmData, frameSize }
      });

      const result = await new Promise((resolve, reject) => {
        const timeout = setTimeout(() => reject(new Error('Encode timeout')), 1000);
        
        const messageHandler = (msg) => {
          if (msg.id === requestId) {
            clearTimeout(timeout);
            worker.off('message', messageHandler);
            if (msg.success) {
              resolve(msg.result);
            } else {
              reject(new Error(msg.error));
            }
          }
        };
        
        worker.on('message', messageHandler);
      });

      console.log(`✅ Encode ${i + 1}: ${pcmData.length}B → ${result.data.length}B (${result.processingTime.toFixed(2)}ms)`);
      
    } catch (err) {
      console.error(`❌ Encode ${i + 1} failed:`, err.message);
      break;
    }
  }

  worker.terminate();
  console.log('✅ All worker encoding tests passed!');
}

testWorker().catch(err => {
  console.error('❌ Worker test failed:', err.message);
  process.exit(1);
});