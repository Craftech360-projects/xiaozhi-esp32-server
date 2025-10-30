// ========================================
// Unit Tests for Audio Worker
// ========================================
// Tests worker initialization, encoding, and error handling

const { Worker } = require("worker_threads");
const path = require("path");

console.log("🧪 Testing Audio Worker Unit Tests\n");

let testsPassed = 0;
let testsFailed = 0;

function testPassed(message) {
  console.log(`✅ ${message}`);
  testsPassed++;
}

function testFailed(message, error) {
  console.error(`❌ ${message}`);
  if (error) {
    console.error(`   Error: ${error}`);
  }
  testsFailed++;
}

// Test 1: Worker initialization
async function testWorkerInitialization() {
  console.log("1️⃣ Test worker initialization");

  return new Promise((resolve) => {
    const workerPath = path.join(__dirname, "audio-worker.js");

    try {
      const worker = new Worker(workerPath);
      testPassed("Worker created successfully");

      let initReceived = false;

      worker.on("message", (msg) => {
        if (msg.id === 1 && msg.success) {
          testPassed("Worker encoder initialization successful");
          initReceived = true;

          worker.terminate().then(() => {
            testPassed("Worker terminated successfully");
            console.log("");
            resolve();
          });
        }
      });

      worker.on("error", (error) => {
        testFailed("Worker error during initialization", error.message);
        resolve();
      });

      // Send init message
      worker.postMessage({
        id: 1,
        type: "init_encoder",
        data: { sampleRate: 24000, channels: 1 },
      });

      // Timeout
      setTimeout(() => {
        if (!initReceived) {
          testFailed("Worker initialization timeout");
          worker.terminate();
          resolve();
        }
      }, 3000);
    } catch (error) {
      testFailed("Failed to create worker", error.message);
      resolve();
    }
  });
}

// Test 2: Opus encoding in worker thread
async function testOpusEncoding() {
  console.log("2️⃣ Test Opus encoding in worker thread");

  return new Promise((resolve) => {
    const workerPath = path.join(__dirname, "audio-worker.js");
    const worker = new Worker(workerPath);

    let encodingDone = false;

    worker.on("message", (msg) => {
      if (msg.id === 1 && msg.success) {
        // Init done, send encode request
        const testSamples = 1440; // 60ms @ 24kHz
        const testPCM = Buffer.alloc(testSamples * 2);
        const int16View = new Int16Array(testPCM.buffer);

        // Generate sine wave
        for (let i = 0; i < testSamples; i++) {
          int16View[i] = Math.floor(Math.sin(i / 10) * 10000);
        }

        worker.postMessage({
          id: 2,
          type: "encode",
          data: { pcmData: testPCM, frameSize: testSamples },
        });
      } else if (msg.id === 2) {
        if (msg.success) {
          testPassed(
            `Encoded ${msg.result.inputSize}B PCM → ${msg.result.outputSize}B Opus`
          );
          testPassed(
            `Processing time: ${msg.result.processingTime.toFixed(2)}ms`
          );

          if (
            msg.result.outputSize > 0 &&
            msg.result.outputSize < msg.result.inputSize
          ) {
            testPassed("Opus compression working (output < input)");
          } else {
            testFailed("Opus compression not working properly");
          }

          encodingDone = true;
        } else {
          testFailed("Encoding failed", msg.error);
        }

        worker.terminate().then(() => {
          console.log("");
          resolve();
        });
      }
    });

    worker.on("error", (error) => {
      testFailed("Worker error during encoding", error.message);
      worker.terminate();
      resolve();
    });

    // Initialize encoder
    worker.postMessage({
      id: 1,
      type: "init_encoder",
      data: { sampleRate: 24000, channels: 1 },
    });

    setTimeout(() => {
      if (!encodingDone) {
        testFailed("Encoding timeout");
        worker.terminate();
        resolve();
      }
    }, 3000);
  });
}

// Test 3: Worker error handling
async function testWorkerErrorHandling() {
  console.log("3️⃣ Test worker error handling");

  return new Promise((resolve) => {
    const workerPath = path.join(__dirname, "audio-worker.js");
    const worker = new Worker(workerPath);

    let errorHandled = false;

    worker.on("message", (msg) => {
      if (msg.id === 1) {
        // Try to encode without initializing encoder
        worker.postMessage({
          id: 2,
          type: "encode",
          data: { pcmData: Buffer.alloc(100), frameSize: 50 },
        });
      } else if (msg.id === 2) {
        if (!msg.success) {
          testPassed(
            "Worker correctly returned error for uninitialized encoder"
          );
          testPassed(`Error message: ${msg.error}`);
          errorHandled = true;
        } else {
          testFailed(
            "Worker should have returned error for uninitialized encoder"
          );
        }

        worker.terminate().then(() => {
          console.log("");
          resolve();
        });
      }
    });

    worker.on("error", (error) => {
      testPassed("Worker error event fired correctly");
      worker.terminate();
      resolve();
    });

    // Send invalid init (skip encoder init)
    worker.postMessage({
      id: 1,
      type: "init_decoder",
      data: { sampleRate: 16000, channels: 1 },
    });

    setTimeout(() => {
      if (!errorHandled) {
        testFailed("Error handling timeout");
        worker.terminate();
        resolve();
      }
    }, 3000);
  });
}

// Test 4: Multiple workers
async function testMultipleWorkers() {
  console.log("4️⃣ Test multiple workers");

  return new Promise((resolve) => {
    const workerPath = path.join(__dirname, "audio-worker.js");
    const workers = [];
    const workerCount = 3;
    let completedWorkers = 0;

    for (let i = 0; i < workerCount; i++) {
      const worker = new Worker(workerPath);
      workers.push(worker);

      worker.on("message", (msg) => {
        if (msg.id === 1 && msg.success) {
          completedWorkers++;

          if (completedWorkers === workerCount) {
            testPassed(`All ${workerCount} workers initialized successfully`);

            // Terminate all workers
            Promise.all(workers.map((w) => w.terminate())).then(() => {
              testPassed("All workers terminated successfully");
              console.log("");
              resolve();
            });
          }
        }
      });

      worker.on("error", (error) => {
        testFailed(`Worker ${i} error`, error.message);
      });

      // Initialize each worker
      worker.postMessage({
        id: 1,
        type: "init_encoder",
        data: { sampleRate: 24000, channels: 1 },
      });
    }

    setTimeout(() => {
      if (completedWorkers < workerCount) {
        testFailed(
          `Only ${completedWorkers}/${workerCount} workers initialized`
        );
        workers.forEach((w) => w.terminate());
        resolve();
      }
    }, 3000);
  });
}

// Test 5: Performance test
async function testPerformance() {
  console.log("5️⃣ Test performance (50 encode operations)");

  return new Promise((resolve) => {
    const workerPath = path.join(__dirname, "audio-worker.js");
    const worker = new Worker(workerPath);

    const testSamples = 1440;
    const testPCM = Buffer.alloc(testSamples * 2);
    const int16View = new Int16Array(testPCM.buffer);
    for (let i = 0; i < testSamples; i++) {
      int16View[i] = Math.floor(Math.sin(i / 10) * 10000);
    }

    const iterations = 50;
    let completed = 0;
    const times = [];
    const startTime = Date.now();

    worker.on("message", (msg) => {
      if (msg.id === 1 && msg.success) {
        // Init done, send encode requests
        for (let i = 0; i < iterations; i++) {
          worker.postMessage({
            id: i + 2,
            type: "encode",
            data: { pcmData: testPCM, frameSize: testSamples },
          });
        }
      } else if (msg.id > 1 && msg.success) {
        completed++;
        times.push(msg.result.processingTime);

        if (completed === iterations) {
          const totalTime = Date.now() - startTime;
          const avgTime = times.reduce((a, b) => a + b) / times.length;
          const maxTime = Math.max(...times);
          const minTime = Math.min(...times);

          testPassed(`Completed ${iterations} operations in ${totalTime}ms`);
          testPassed(`Avg processing time: ${avgTime.toFixed(2)}ms`);
          testPassed(
            `Min/Max: ${minTime.toFixed(2)}ms / ${maxTime.toFixed(2)}ms`
          );
          testPassed(
            `Throughput: ${(iterations / (totalTime / 1000)).toFixed(
              1
            )} ops/sec`
          );

          worker.terminate().then(() => {
            console.log("");
            resolve();
          });
        }
      }
    });

    worker.on("error", (error) => {
      testFailed("Worker error during performance test", error.message);
      worker.terminate();
      resolve();
    });

    // Initialize encoder
    worker.postMessage({
      id: 1,
      type: "init_encoder",
      data: { sampleRate: 24000, channels: 1 },
    });

    setTimeout(() => {
      if (completed < iterations) {
        testFailed(
          `Performance test timeout (${completed}/${iterations} completed)`
        );
        worker.terminate();
        resolve();
      }
    }, 10000);
  });
}

// Run all tests
async function runAllTests() {
  await testWorkerInitialization();
  await testOpusEncoding();
  await testWorkerErrorHandling();
  await testMultipleWorkers();
  await testPerformance();

  // Summary
  console.log("=".repeat(50));
  console.log(`📊 Test Results: ${testsPassed} passed, ${testsFailed} failed`);
  console.log("=".repeat(50));

  if (testsFailed === 0) {
    console.log("🎉 All Audio Worker tests passed!");
    process.exit(0);
  } else {
    console.error("❌ Some tests failed");
    process.exit(1);
  }
}

runAllTests().catch((error) => {
  console.error("❌ Test suite error:", error);
  process.exit(1);
});
