// ========================================
// Phase 2 Worker Thread Test
// ========================================
// Test worker pool functionality independently

const { Worker } = require('worker_threads');
const path = require('path');

console.log("🧪 Testing Phase 2 Worker Thread Implementation\n");

// Test 1: Worker creation and initialization
console.log("1️⃣ Testing Worker Creation...");
const workerPath = path.join(__dirname, 'audio-worker.js');

try {
  const testWorker = new Worker(workerPath);
  console.log("✅ Worker created successfully");

  // Test message handling
  let messageReceived = false;
  testWorker.on('message', (msg) => {
    messageReceived = true;
    console.log("✅ Received message from worker:", msg);

    if (msg.success) {
      console.log("✅ Worker initialization successful\n");
    } else {
      console.error("❌ Worker returned error:", msg.error);
    }

    // Cleanup
    testWorker.terminate().then(() => {
      console.log("✅ Worker terminated successfully");
      runEncodingTest();
    });
  });

  testWorker.on('error', (error) => {
    console.error("❌ Worker error:", error);
    process.exit(1);
  });

  // Send init message
  console.log("📤 Sending encoder init message to worker...");
  testWorker.postMessage({
    id: 1,
    type: 'init_encoder',
    data: {
      sampleRate: 24000,
      channels: 1
    }
  });

  // Timeout if no response
  setTimeout(() => {
    if (!messageReceived) {
      console.error("❌ No response from worker after 3s");
      process.exit(1);
    }
  }, 3000);

} catch (error) {
  console.error("❌ Failed to create worker:", error);
  process.exit(1);
}

// Test 2: Encoding functionality
function runEncodingTest() {
  console.log("\n2️⃣ Testing Opus Encoding with Worker...");

  const worker = new Worker(workerPath);

  // Initialize encoder
  worker.postMessage({
    id: 1,
    type: 'init_encoder',
    data: { sampleRate: 24000, channels: 1 }
  });

  // Create test PCM data (1440 samples @ 24kHz = 60ms)
  const testSamples = 1440;
  const testPCM = Buffer.alloc(testSamples * 2);
  const int16View = new Int16Array(testPCM.buffer);
  for (let i = 0; i < testSamples; i++) {
    int16View[i] = Math.floor(Math.sin(i / 10) * 10000);
  }

  let encodeDone = false;
  worker.on('message', (msg) => {
    if (msg.id === 2 && msg.success) {
      console.log(`✅ Encoded ${testPCM.length}B PCM → ${msg.result.data.length}B Opus`);
      console.log(`   Processing time: ${msg.result.processingTime.toFixed(2)}ms`);
      encodeDone = true;

      worker.terminate().then(() => {
        runDecodingTest();
      });
    }
  });

  // Send encoding request after init
  setTimeout(() => {
    console.log("📤 Sending encode request...");
    worker.postMessage({
      id: 2,
      type: 'encode',
      data: {
        pcmData: testPCM,
        frameSize: testSamples
      }
    });
  }, 100);

  setTimeout(() => {
    if (!encodeDone) {
      console.error("❌ Encoding timeout");
      process.exit(1);
    }
  }, 3000);
}

// Test 3: Decoding functionality
function runDecodingTest() {
  console.log("\n3️⃣ Testing Opus Decoding with Worker...");

  const worker = new Worker(workerPath);

  // Initialize both encoder and decoder
  worker.postMessage({
    id: 1,
    type: 'init_encoder',
    data: { sampleRate: 16000, channels: 1 }
  });

  worker.postMessage({
    id: 2,
    type: 'init_decoder',
    data: { sampleRate: 16000, channels: 1 }
  });

  // Create test PCM data (960 samples @ 16kHz = 60ms)
  const testSamples = 960;
  const testPCM = Buffer.alloc(testSamples * 2);
  const int16View = new Int16Array(testPCM.buffer);
  for (let i = 0; i < testSamples; i++) {
    int16View[i] = Math.floor(Math.sin(i / 10) * 10000);
  }

  let encodedOpus = null;
  let decodeDone = false;

  worker.on('message', (msg) => {
    if (msg.id === 3 && msg.success) {
      // Encode done
      encodedOpus = msg.result.data;
      console.log(`✅ Encoded for decode test: ${testPCM.length}B → ${encodedOpus.length}B`);

      // Now decode it
      console.log("📤 Sending decode request...");
      worker.postMessage({
        id: 4,
        type: 'decode',
        data: { opusData: encodedOpus }
      });
    } else if (msg.id === 4 && msg.success) {
      // Decode done
      console.log(`✅ Decoded ${encodedOpus.length}B Opus → ${msg.result.data.length}B PCM`);
      console.log(`   Processing time: ${msg.result.processingTime.toFixed(2)}ms`);
      decodeDone = true;

      worker.terminate().then(() => {
        runPerformanceTest();
      });
    }
  });

  // Send encoding request
  setTimeout(() => {
    console.log("📤 Sending encode request for decode test...");
    worker.postMessage({
      id: 3,
      type: 'encode',
      data: {
        pcmData: testPCM,
        frameSize: testSamples
      }
    });
  }, 200);

  setTimeout(() => {
    if (!decodeDone) {
      console.error("❌ Decoding timeout");
      process.exit(1);
    }
  }, 3000);
}

// Test 4: Performance test
function runPerformanceTest() {
  console.log("\n4️⃣ Testing Performance (100 encode operations)...");

  const worker = new Worker(workerPath);

  // Initialize
  worker.postMessage({
    id: 1,
    type: 'init_encoder',
    data: { sampleRate: 24000, channels: 1 }
  });

  const testSamples = 1440;
  const testPCM = Buffer.alloc(testSamples * 2);
  const int16View = new Int16Array(testPCM.buffer);
  for (let i = 0; i < testSamples; i++) {
    int16View[i] = Math.floor(Math.sin(i / 10) * 10000);
  }

  const iterations = 100;
  let completed = 0;
  const times = [];
  const startTime = Date.now();

  worker.on('message', (msg) => {
    if (msg.id > 1 && msg.success) {
      completed++;
      times.push(msg.result.processingTime);

      if (completed === iterations) {
        const totalTime = Date.now() - startTime;
        const avgTime = times.reduce((a, b) => a + b) / times.length;
        const maxTime = Math.max(...times);
        const minTime = Math.min(...times);

        console.log(`✅ Completed ${iterations} operations in ${totalTime}ms`);
        console.log(`   Avg processing time: ${avgTime.toFixed(2)}ms`);
        console.log(`   Min/Max: ${minTime.toFixed(2)}ms / ${maxTime.toFixed(2)}ms`);
        console.log(`   Throughput: ${(iterations / (totalTime / 1000)).toFixed(1)} ops/sec`);

        worker.terminate().then(() => {
          console.log("\n🎉 All Phase 2 Worker Tests Passed!");
          process.exit(0);
        });
      }
    }
  });

  // Send 100 encode requests
  setTimeout(() => {
    console.log(`📤 Sending ${iterations} encode requests...`);
    for (let i = 0; i < iterations; i++) {
      worker.postMessage({
        id: i + 2,
        type: 'encode',
        data: {
          pcmData: testPCM,
          frameSize: testSamples
        }
      });
    }
  }, 200);

  setTimeout(() => {
    if (completed < iterations) {
      console.error(`❌ Performance test timeout (${completed}/${iterations} completed)`);
      process.exit(1);
    }
  }, 10000);
}
