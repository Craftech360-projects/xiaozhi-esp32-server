// ========================================
// Jitter Fix Test - Load-Aware Worker Selection
// ========================================
// Test that demonstrates jitter reduction through intelligent worker selection

const { Worker } = require('worker_threads');
const path = require('path');

console.log("🧪 Testing Jitter Fix - Load-Aware Worker Selection\n");

// ========================================
// Simplified WorkerPoolManager with Load Tracking
// ========================================

class WorkerPoolManager {
  constructor(workerCount = 2) {
    this.workers = [];
    this.workerPendingCount = [];
    this.requestId = 0;
    this.pendingRequests = new Map();

    this.initializeWorkers(workerCount);
  }

  initializeWorkers(count) {
    const workerPath = path.join(__dirname, 'audio-worker.js');

    for (let i = 0; i < count; i++) {
      const worker = new Worker(workerPath);

      worker.on('message', (message) => {
        const { id, success, result, error } = message;
        const pending = this.pendingRequests.get(id);

        if (pending) {
          clearTimeout(pending.timeout);
          this.pendingRequests.delete(id);

          if (success) {
            pending.resolve(result);
          } else {
            pending.reject(new Error(error || 'Worker operation failed'));
          }
        }
      });

      this.workers.push({ worker, id: i });
      this.workerPendingCount.push(0);
      console.log(`✅ Worker ${i} initialized`);
    }
  }

  getNextWorker() {
    // JITTER FIX: Use least-loaded worker instead of round-robin
    let minPending = Infinity;
    let selectedIndex = 0;

    for (let i = 0; i < this.workers.length; i++) {
      if (this.workerPendingCount[i] < minPending) {
        minPending = this.workerPendingCount[i];
        selectedIndex = i;
      }
    }

    return { worker: this.workers[selectedIndex].worker, index: selectedIndex };
  }

  async encodeOpus(pcmData, frameSize) {
    const { worker, index } = this.getNextWorker();

    // Track pending request count
    this.workerPendingCount[index]++;
    const startTime = process.hrtime.bigint();

    try {
      const result = await this.sendMessage(worker, {
        type: 'encode',
        data: { pcmData, frameSize }
      }, 150);

      const duration = Number(process.hrtime.bigint() - startTime) / 1000000;
      return { data: result.data, duration, workerIndex: index };
    } finally {
      // Always decrement pending count when done
      this.workerPendingCount[index]--;
    }
  }

  sendMessage(worker, message, timeoutMs = 150) {
    const requestId = ++this.requestId;
    message.id = requestId;

    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        this.pendingRequests.delete(requestId);
        reject(new Error(`Worker request ${requestId} timeout after ${timeoutMs}ms`));
      }, timeoutMs);

      this.pendingRequests.set(requestId, { resolve, reject, timeout });
      worker.postMessage(message);
    });
  }

  async terminate() {
    for (const w of this.workers) {
      await w.worker.terminate();
    }
  }
}

// ========================================
// Test Execution
// ========================================

async function runJitterTest() {
  console.log("\n1️⃣ Initializing Worker Pool...\n");

  const pool = new WorkerPoolManager(2);

  // Wait for workers to initialize
  await new Promise(resolve => setTimeout(resolve, 1000));

  // Initialize encoder in all workers
  console.log("\n2️⃣ Initializing Opus Encoders...\n");

  await pool.sendMessage(pool.workers[0].worker, {
    type: 'init_encoder',
    data: { sampleRate: 24000, channels: 1 }
  }, 500);

  await pool.sendMessage(pool.workers[1].worker, {
    type: 'init_encoder',
    data: { sampleRate: 24000, channels: 1 }
  }, 500);

  console.log("✅ Encoders initialized\n");

  // ========================================
  // Jitter Test: Simulate burst of audio frames
  // ========================================

  console.log("3️⃣ Running Jitter Test (20 concurrent frames)...\n");

  // Generate test PCM data (60ms @ 24kHz = 1440 samples = 2880 bytes)
  const pcmData = Buffer.alloc(2880);
  for (let i = 0; i < pcmData.length; i++) {
    pcmData[i] = Math.floor(Math.sin(i / 100) * 32767) & 0xFF;
  }

  const frameSize = 1440;
  const numFrames = 20;
  const results = [];

  // Send all frames concurrently to simulate real-world burst
  const startTime = Date.now();
  const promises = [];

  for (let i = 0; i < numFrames; i++) {
    promises.push(
      pool.encodeOpus(pcmData, frameSize)
        .then(result => {
          results.push({
            frameId: i,
            duration: result.duration,
            workerIndex: result.workerIndex,
            timestamp: Date.now() - startTime
          });
        })
        .catch(err => {
          results.push({
            frameId: i,
            error: err.message,
            timestamp: Date.now() - startTime
          });
        })
    );
  }

  await Promise.all(promises);
  const totalTime = Date.now() - startTime;

  // ========================================
  // Analyze Results
  // ========================================

  console.log("\n" + "=".repeat(70));
  console.log("📊 JITTER TEST RESULTS");
  console.log("=".repeat(70));

  // Sort by completion time
  results.sort((a, b) => a.timestamp - b.timestamp);

  const successful = results.filter(r => !r.error);
  const failed = results.filter(r => r.error);

  console.log(`\n✅ Successful: ${successful.length}/${numFrames}`);
  console.log(`❌ Failed: ${failed.length}/${numFrames}`);
  console.log(`⏱️  Total time: ${totalTime}ms`);

  if (successful.length > 0) {
    const durations = successful.map(r => r.duration);
    const avgDuration = durations.reduce((a, b) => a + b) / durations.length;
    const minDuration = Math.min(...durations);
    const maxDuration = Math.max(...durations);

    // Calculate jitter (standard deviation)
    const variance = durations.reduce((sum, d) => sum + Math.pow(d - avgDuration, 2), 0) / durations.length;
    const jitter = Math.sqrt(variance);

    console.log(`\n⏱️  Processing Time:`);
    console.log(`   Average: ${avgDuration.toFixed(2)}ms`);
    console.log(`   Min: ${minDuration.toFixed(2)}ms`);
    console.log(`   Max: ${maxDuration.toFixed(2)}ms`);
    console.log(`   Jitter (σ): ${jitter.toFixed(2)}ms`);

    // Worker distribution
    const worker0Count = successful.filter(r => r.workerIndex === 0).length;
    const worker1Count = successful.filter(r => r.workerIndex === 1).length;

    console.log(`\n👷 Worker Load Distribution:`);
    console.log(`   Worker 0: ${worker0Count} frames (${(worker0Count/successful.length*100).toFixed(1)}%)`);
    console.log(`   Worker 1: ${worker1Count} frames (${(worker1Count/successful.length*100).toFixed(1)}%)`);

    // Jitter quality assessment
    console.log(`\n🎯 Jitter Quality:`);
    if (jitter < 5) {
      console.log(`   ✅ EXCELLENT - Very low jitter (< 5ms)`);
    } else if (jitter < 10) {
      console.log(`   ✅ GOOD - Low jitter (< 10ms)`);
    } else if (jitter < 20) {
      console.log(`   ⚠️  MODERATE - Noticeable jitter (< 20ms)`);
    } else {
      console.log(`   ❌ POOR - High jitter (>= 20ms)`);
    }

    // Show timeline of first 10 frames
    console.log(`\n📈 Completion Timeline (first 10 frames):`);
    console.log(`   Frame | Time(ms) | Duration(ms) | Worker`);
    console.log(`   ` + "-".repeat(50));

    for (let i = 0; i < Math.min(10, successful.length); i++) {
      const r = successful[i];
      console.log(`   ${String(r.frameId).padStart(5)} | ${String(r.timestamp).padStart(8)} | ${r.duration.toFixed(2).padStart(12)} | Worker ${r.workerIndex}`);
    }
  }

  if (failed.length > 0) {
    console.log(`\n❌ Failed Frames:`);
    failed.forEach(r => {
      console.log(`   Frame ${r.frameId}: ${r.error}`);
    });
  }

  console.log("\n" + "=".repeat(70));

  // ========================================
  // Load Balancing Verification
  // ========================================

  console.log("\n4️⃣ Load Balancing Verification:\n");

  if (successful.length > 0) {
    const worker0Count = successful.filter(r => r.workerIndex === 0).length;
    const worker1Count = successful.filter(r => r.workerIndex === 1).length;
    const balance = Math.abs(worker0Count - worker1Count);
    const balancePercent = (balance / successful.length * 100);

    if (balancePercent < 10) {
      console.log(`   ✅ EXCELLENT load balancing - difference: ${balance} frames (${balancePercent.toFixed(1)}%)`);
    } else if (balancePercent < 20) {
      console.log(`   ✅ GOOD load balancing - difference: ${balance} frames (${balancePercent.toFixed(1)}%)`);
    } else {
      console.log(`   ⚠️  UNBALANCED - difference: ${balance} frames (${balancePercent.toFixed(1)}%)`);
    }
  }

  // Cleanup
  console.log("\n5️⃣ Cleaning up...\n");
  await pool.terminate();

  console.log("🎉 Jitter test complete!\n");
}

// Run test
runJitterTest().catch(err => {
  console.error("\n❌ Test failed:", err);
  process.exit(1);
});
