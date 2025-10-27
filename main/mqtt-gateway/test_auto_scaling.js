// ========================================
// Auto-Scaling Test
// ========================================
// Test dynamic worker scaling under various load conditions

const { Worker } = require('worker_threads');
const path = require('path');

console.log("🧪 Testing Dynamic Worker Auto-Scaling\n");

// Simplified PerformanceMonitor for testing
class PerformanceMonitor {
  constructor() {
    this.metrics = {
      startTime: Date.now(),
      processingTime: [],
      cpuUsage: [],
      memoryUsage: [],
      frameCount: 0,
      errors: 0
    };
    this.lastCpuUsage = process.cpuUsage();
    this.lastCpuTime = Date.now();
    this.maxHistorySize = 100;

    this.startResourceMonitoring();
  }

  startResourceMonitoring() {
    this.resourceInterval = setInterval(() => {
      this.recordCpuUsage();
      this.recordMemoryUsage();
    }, 1000);
  }

  recordCpuUsage() {
    const currentTime = Date.now();
    const currentCpuUsage = process.cpuUsage(this.lastCpuUsage);
    const timeDelta = currentTime - this.lastCpuTime;

    if (timeDelta > 0) {
      const cpuPercent = ((currentCpuUsage.user + currentCpuUsage.system) / 1000) / timeDelta * 100;
      this.metrics.cpuUsage.push(cpuPercent);
      if (this.metrics.cpuUsage.length > this.maxHistorySize) {
        this.metrics.cpuUsage.shift();
      }
      this.lastCpuUsage = process.cpuUsage();
      this.lastCpuTime = currentTime;
    }
  }

  recordMemoryUsage() {
    const mem = process.memoryUsage();
    const memoryData = {
      rss: mem.rss / 1024 / 1024,
      heapUsed: mem.heapUsed / 1024 / 1024,
      timestamp: Date.now()
    };
    this.metrics.memoryUsage.push(memoryData);
    if (this.metrics.memoryUsage.length > this.maxHistorySize) {
      this.metrics.memoryUsage.shift();
    }
  }

  recordProcessingTime(startTime) {
    const duration = Number(process.hrtime.bigint() - startTime) / 1000000;
    this.metrics.processingTime.push(duration);
    if (this.metrics.processingTime.length > this.maxHistorySize) {
      this.metrics.processingTime.shift();
    }
    return duration;
  }

  recordFrame() {
    this.metrics.frameCount++;
  }

  recordError() {
    this.metrics.errors++;
  }

  getAverageCpuUsage() {
    if (this.metrics.cpuUsage.length === 0) return 0;
    return this.metrics.cpuUsage.reduce((a, b) => a + b) / this.metrics.cpuUsage.length;
  }

  getMaxProcessingTime() {
    if (this.metrics.processingTime.length === 0) return 0;
    return Math.max(...this.metrics.processingTime);
  }

  stop() {
    if (this.resourceInterval) {
      clearInterval(this.resourceInterval);
    }
  }
}

// Simplified WorkerPoolManager with Auto-Scaling
class WorkerPoolManager {
  constructor(workerCount = 2) {
    this.workers = [];
    this.workerPendingCount = [];
    this.requestId = 0;
    this.pendingRequests = new Map();
    this.performanceMonitor = new PerformanceMonitor();

    // DYNAMIC SCALING: Configuration
    this.minWorkers = 2;
    this.maxWorkers = 6;
    this.scaleUpThreshold = 0.7;
    this.scaleDownThreshold = 0.3;
    this.scaleUpCpuThreshold = 60;
    this.scaleCheckInterval = 5000; // Check every 5 seconds for demo
    this.scaleCheckTimer = null;
    this.lastScaleAction = Date.now();
    this.scaleUpCooldown = 10000; // 10s for demo
    this.scaleDownCooldown = 20000; // 20s for demo

    this.initializeWorkers(workerCount);
    this.startAutoScaling();
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

      worker.on('error', (error) => {
        console.error(`❌ [WORKER-${i}] Error:`, error);
      });

      this.workers.push({ worker, id: i });
      this.workerPendingCount.push(0);
    }

    console.log(`✅ [INIT] Started with ${count} workers\n`);
  }

  startAutoScaling() {
    console.log(`🔄 [AUTO-SCALE] Starting dynamic scaling (${this.minWorkers}-${this.maxWorkers} workers)\n`);

    this.scaleCheckTimer = setInterval(() => {
      this.checkAndScale();
    }, this.scaleCheckInterval);
  }

  checkAndScale() {
    const currentWorkerCount = this.workers.length;
    const timeSinceLastScale = Date.now() - this.lastScaleAction;

    const avgPendingPerWorker = this.workerPendingCount.reduce((a, b) => a + b, 0) / currentWorkerCount;
    const totalPending = this.pendingRequests.size;
    const avgCpu = this.performanceMonitor.getAverageCpuUsage();
    const maxLatency = this.performanceMonitor.getMaxProcessingTime();
    const loadRatio = avgPendingPerWorker / 5;

    // Log current state
    const loadPercent = Math.min(100, loadRatio * 100).toFixed(1);
    console.log(`📊 [CHECK] Workers: ${currentWorkerCount}, Load: ${loadPercent}%, CPU: ${avgCpu.toFixed(1)}%, Latency: ${maxLatency.toFixed(2)}ms, Pending: ${totalPending}`);

    // SCALE UP CONDITIONS
    const shouldScaleUp =
      currentWorkerCount < this.maxWorkers &&
      timeSinceLastScale >= this.scaleUpCooldown &&
      (
        loadRatio > this.scaleUpThreshold ||
        avgCpu > this.scaleUpCpuThreshold ||
        maxLatency > 50 ||
        totalPending > currentWorkerCount * 3
      );

    // SCALE DOWN CONDITIONS
    const shouldScaleDown =
      currentWorkerCount > this.minWorkers &&
      timeSinceLastScale >= this.scaleDownCooldown &&
      loadRatio < this.scaleDownThreshold &&
      avgCpu < 30 &&
      maxLatency < 10 &&
      totalPending === 0;

    if (shouldScaleUp) {
      const newWorkerCount = Math.min(currentWorkerCount + 1, this.maxWorkers);
      this.scaleUp(newWorkerCount);
    } else if (shouldScaleDown) {
      const newWorkerCount = Math.max(currentWorkerCount - 1, this.minWorkers);
      this.scaleDown(newWorkerCount);
    }
  }

  async scaleUp(targetCount) {
    const currentCount = this.workers.length;
    const workersToAdd = targetCount - currentCount;

    console.log(`\n📈 [AUTO-SCALE] Scaling UP: ${currentCount} → ${targetCount} workers (+${workersToAdd})`);

    const workerPath = path.join(__dirname, 'audio-worker.js');

    for (let i = 0; i < workersToAdd; i++) {
      const workerId = this.workers.length;
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

      this.workers.push({ worker, id: workerId });
      this.workerPendingCount.push(0);

      console.log(`   ✅ Worker ${workerId} added`);
    }

    this.lastScaleAction = Date.now();

    // Initialize new workers
    await this.initializeNewWorkers(currentCount, targetCount);
    console.log(`   🎉 Scale up complete!\n`);
  }

  async scaleDown(targetCount) {
    const currentCount = this.workers.length;
    const workersToRemove = currentCount - targetCount;

    console.log(`\n📉 [AUTO-SCALE] Scaling DOWN: ${currentCount} → ${targetCount} workers (-${workersToRemove})`);

    for (let i = 0; i < workersToRemove; i++) {
      const workerIndex = this.workers.length - 1;
      const workerInfo = this.workers[workerIndex];

      // Wait for pending operations
      const maxWaitTime = 3000;
      const startWait = Date.now();

      while (this.workerPendingCount[workerIndex] > 0 && (Date.now() - startWait) < maxWaitTime) {
        await new Promise(resolve => setTimeout(resolve, 100));
      }

      try {
        await workerInfo.worker.terminate();
        console.log(`   🗑️  Worker ${workerInfo.id} removed`);
      } catch (error) {
        console.error(`   ❌ Error terminating worker ${workerInfo.id}`);
      }

      this.workers.pop();
      this.workerPendingCount.pop();
    }

    this.lastScaleAction = Date.now();
    console.log(`   🎉 Scale down complete!\n`);
  }

  async initializeNewWorkers(startIndex, endIndex) {
    const workersToInit = this.workers.slice(startIndex, endIndex);

    try {
      await Promise.all(workersToInit.map(w =>
        this.sendMessage(w.worker, {
          type: 'init_encoder',
          data: { sampleRate: 24000, channels: 1 }
        }, 500)
      ));
      console.log(`   ✅ New workers initialized`);
    } catch (error) {
      console.error(`   ❌ Failed to initialize new workers:`, error);
    }
  }

  getNextWorker() {
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
    const startTime = process.hrtime.bigint();

    this.workerPendingCount[index]++;

    try {
      const result = await this.sendMessage(worker, {
        type: 'encode',
        data: { pcmData, frameSize }
      }, 150);

      this.performanceMonitor.recordProcessingTime(startTime);
      this.performanceMonitor.recordFrame();

      return result.data;
    } catch (error) {
      this.performanceMonitor.recordError();
      throw error;
    } finally {
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
    if (this.scaleCheckTimer) {
      clearInterval(this.scaleCheckTimer);
    }
    this.performanceMonitor.stop();

    for (const w of this.workers) {
      await w.worker.terminate();
    }
  }
}

// ========================================
// Test Execution
// ========================================

async function runAutoScalingTest() {
  console.log("=" .repeat(70));
  console.log("🧪 AUTO-SCALING TEST");
  console.log("=" .repeat(70) + "\n");

  const pool = new WorkerPoolManager(2);

  // Generate test PCM data
  const pcmData = Buffer.alloc(2880);
  for (let i = 0; i < pcmData.length; i++) {
    pcmData[i] = Math.floor(Math.sin(i / 100) * 32767) & 0xFF;
  }
  const frameSize = 1440;

  // Wait for workers to initialize
  await new Promise(resolve => setTimeout(resolve, 2000));

  console.log("📝 Test Phases:\n");
  console.log("   Phase 1: Low load (5 frames/s) - should maintain 2 workers");
  console.log("   Phase 2: High load (100 frames/s burst) - should scale UP");
  console.log("   Phase 3: Return to low load - should scale DOWN after cooldown\n");
  console.log("=" .repeat(70) + "\n");

  // PHASE 1: Low load (should stay at 2 workers)
  console.log("▶️  PHASE 1: Low Load (20 seconds)\n");

  let phase1Interval = setInterval(async () => {
    try {
      await pool.encodeOpus(pcmData, frameSize);
    } catch (err) {
      // Ignore errors
    }
  }, 200); // 5 frames/second

  await new Promise(resolve => setTimeout(resolve, 20000));
  clearInterval(phase1Interval);

  // PHASE 2: High load (should scale up)
  console.log("\n▶️  PHASE 2: High Load Burst (15 seconds)\n");

  let phase2Interval = setInterval(async () => {
    // Send 10 frames concurrently
    const promises = [];
    for (let i = 0; i < 10; i++) {
      promises.push(pool.encodeOpus(pcmData, frameSize).catch(err => {}));
    }
    await Promise.all(promises);
  }, 100); // 100 frames/second burst

  await new Promise(resolve => setTimeout(resolve, 15000));
  clearInterval(phase2Interval);

  // PHASE 3: Return to low load (should scale down after cooldown)
  console.log("\n▶️  PHASE 3: Return to Low Load (30 seconds - waiting for scale down cooldown)\n");

  let phase3Interval = setInterval(async () => {
    try {
      await pool.encodeOpus(pcmData, frameSize);
    } catch (err) {
      // Ignore errors
    }
  }, 200); // 5 frames/second

  await new Promise(resolve => setTimeout(resolve, 30000));
  clearInterval(phase3Interval);

  // PHASE 4: No load (idle)
  console.log("\n▶️  PHASE 4: Idle (10 seconds - should scale down to minimum)\n");
  await new Promise(resolve => setTimeout(resolve, 10000));

  // Summary
  console.log("\n" + "=".repeat(70));
  console.log("✅ AUTO-SCALING TEST COMPLETE");
  console.log("=".repeat(70));
  console.log(`\nFinal worker count: ${pool.workers.length}`);
  console.log(`Expected: ${pool.minWorkers} (minimum)\n`);

  // Cleanup
  await pool.terminate();
  console.log("🧹 Cleanup complete\n");

  process.exit(0);
}

// Run test
runAutoScalingTest().catch(err => {
  console.error("\n❌ Test failed:", err);
  process.exit(1);
});
