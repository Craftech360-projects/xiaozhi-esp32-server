// ========================================
// EXTREME Auto-Scaling Test
// ========================================
// Forces scaling by creating sustained high load

const { Worker } = require('worker_threads');
const path = require('path');

console.log("🧪 EXTREME Auto-Scaling Test - Forces Scaling to Occur\n");

// Use the actual WorkerPoolManager from app.js (simplified version)
class PerformanceMonitor {
  constructor() {
    this.metrics = {
      startTime: Date.now(),
      processingTime: [],
      cpuUsage: [],
      memoryUsage: [],
      frameCount: 0,
      errors: 0,
      queueSize: []
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

  recordQueueSize(size) {
    this.metrics.queueSize.push(size);
    if (this.metrics.queueSize.length > this.maxHistorySize) {
      this.metrics.queueSize.shift();
    }
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

class WorkerPoolManager {
  constructor(workerCount = 2) {
    this.workers = [];
    this.workerPendingCount = [];
    this.requestId = 0;
    this.pendingRequests = new Map();
    this.performanceMonitor = new PerformanceMonitor();

    // DYNAMIC SCALING: More aggressive for testing
    this.minWorkers = 2;
    this.maxWorkers = 6;
    this.scaleUpThreshold = 0.5;     // Lower threshold - scale up earlier!
    this.scaleDownThreshold = 0.2;   // Lower threshold too
    this.scaleUpCpuThreshold = 40;   // Lower CPU threshold
    this.scaleCheckInterval = 5000;  // Check every 5 seconds
    this.scaleCheckTimer = null;
    this.lastScaleAction = Date.now() - 30000; // Allow immediate scaling
    this.scaleUpCooldown = 5000;     // Very short cooldown for testing (5s)
    this.scaleDownCooldown = 15000;  // 15s for scale down

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

      this.workers.push({ worker, id: i });
      this.workerPendingCount.push(0);
    }

    console.log(`✅ [INIT] Started with ${count} workers\n`);
  }

  startAutoScaling() {
    console.log(`🔄 [AUTO-SCALE] Starting AGGRESSIVE scaling (${this.minWorkers}-${this.maxWorkers} workers)`);
    console.log(`   Scale UP at: ${(this.scaleUpThreshold * 100).toFixed(0)}% load OR ${this.scaleUpCpuThreshold}% CPU`);
    console.log(`   Scale DOWN at: ${(this.scaleDownThreshold * 100).toFixed(0)}% load\n`);

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

    const loadPercent = Math.min(100, loadRatio * 100).toFixed(1);

    // More verbose logging
    console.log(`📊 [CHECK] Workers: ${currentWorkerCount}, Load: ${loadPercent}%, Pending: ${totalPending}, AvgPending/Worker: ${avgPendingPerWorker.toFixed(2)}, CPU: ${avgCpu.toFixed(1)}%, Latency: ${maxLatency.toFixed(2)}ms`);

    // SCALE UP CONDITIONS
    const shouldScaleUp =
      currentWorkerCount < this.maxWorkers &&
      timeSinceLastScale >= this.scaleUpCooldown &&
      (
        loadRatio > this.scaleUpThreshold ||
        avgCpu > this.scaleUpCpuThreshold ||
        maxLatency > 50 ||
        totalPending > currentWorkerCount * 2  // Lower threshold
      );

    // SCALE DOWN CONDITIONS
    const shouldScaleDown =
      currentWorkerCount > this.minWorkers &&
      timeSinceLastScale >= this.scaleDownCooldown &&
      loadRatio < this.scaleDownThreshold &&
      avgCpu < 20 &&
      maxLatency < 10 &&
      totalPending === 0;

    if (shouldScaleUp) {
      const reason = loadRatio > this.scaleUpThreshold ? 'High Load' :
                    avgCpu > this.scaleUpCpuThreshold ? 'High CPU' :
                    maxLatency > 50 ? 'High Latency' : 'Queue Buildup';
      console.log(`   ⚠️  Trigger: ${reason}`);
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
    this.performanceMonitor.recordQueueSize(this.pendingRequests.size);

    try {
      const result = await this.sendMessage(worker, {
        type: 'encode',
        data: { pcmData, frameSize }
      }, 500); // Longer timeout to allow queue buildup

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

  sendMessage(worker, message, timeoutMs = 500) {
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
// EXTREME Test Execution
// ========================================

async function runExtremeScalingTest() {
  console.log("=" .repeat(70));
  console.log("🔥 EXTREME AUTO-SCALING TEST - FORCES SCALING");
  console.log("=" .repeat(70) + "\n");

  const pool = new WorkerPoolManager(2);

  const pcmData = Buffer.alloc(2880);
  for (let i = 0; i < pcmData.length; i++) {
    pcmData[i] = Math.floor(Math.sin(i / 100) * 32767) & 0xFF;
  }
  const frameSize = 1440;

  await new Promise(resolve => setTimeout(resolve, 2000));

  console.log("🎯 Strategy: Send MANY concurrent requests to force queue buildup\n");
  console.log("=" .repeat(70) + "\n");

  // PHASE 1: MASSIVE BURST - Force scaling!
  console.log("▶️  PHASE 1: MASSIVE BURST (30 seconds) - 50 concurrent requests every 100ms\n");

  let activeRequests = [];
  let phase1Interval = setInterval(async () => {
    // Send 50 concurrent requests!
    for (let i = 0; i < 50; i++) {
      const promise = pool.encodeOpus(pcmData, frameSize).catch(err => {});
      activeRequests.push(promise);
    }

    // Clean up completed requests
    activeRequests = activeRequests.filter(p => p.isPending);
  }, 100);

  await new Promise(resolve => setTimeout(resolve, 30000));
  clearInterval(phase1Interval);

  // Wait for all requests to complete
  console.log("\n⏳ Waiting for pending requests to complete...\n");
  await Promise.all(activeRequests);

  // PHASE 2: Return to idle
  console.log("▶️  PHASE 2: Idle (20 seconds - should scale down)\n");
  await new Promise(resolve => setTimeout(resolve, 20000));

  // Summary
  console.log("\n" + "=".repeat(70));
  console.log("✅ EXTREME AUTO-SCALING TEST COMPLETE");
  console.log("=".repeat(70));
  console.log(`\nFinal worker count: ${pool.workers.length}`);
  console.log(`Peak workers: Should have scaled to 4-6 during burst\n`);

  await pool.terminate();
  console.log("🧹 Cleanup complete\n");

  process.exit(0);
}

runExtremeScalingTest().catch(err => {
  console.error("\n❌ Test failed:", err);
  process.exit(1);
});
