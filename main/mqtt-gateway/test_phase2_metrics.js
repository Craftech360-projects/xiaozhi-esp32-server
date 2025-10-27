// ========================================
// Phase 2 Metrics Test
// ========================================
// Test CPU and memory usage tracking functionality

const { Worker } = require('worker_threads');
const path = require('path');

console.log("🧪 Testing Phase 2 CPU & Memory Metrics\n");

// Simulate the PerformanceMonitor class from app.js
class PerformanceMonitor {
  constructor() {
    this.metrics = {
      startTime: Date.now(),
      processingTime: [],
      cpuUsage: [],
      memoryUsage: [],
      frameCount: 0
    };
    this.lastCpuUsage = process.cpuUsage();
    this.lastCpuTime = Date.now();
    this.maxHistorySize = 100;

    console.log("✅ PerformanceMonitor initialized");
    this.startResourceMonitoring();
  }

  startResourceMonitoring() {
    this.resourceInterval = setInterval(() => {
      this.recordCpuUsage();
      this.recordMemoryUsage();
    }, 1000); // Sample every 1 second
    console.log("✅ Resource monitoring started (1s interval)");
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

      return cpuPercent;
    }
    return 0;
  }

  recordMemoryUsage() {
    const mem = process.memoryUsage();
    const memoryData = {
      rss: mem.rss / 1024 / 1024,
      heapTotal: mem.heapTotal / 1024 / 1024,
      heapUsed: mem.heapUsed / 1024 / 1024,
      external: mem.external / 1024 / 1024,
      timestamp: Date.now()
    };

    this.metrics.memoryUsage.push(memoryData);

    if (this.metrics.memoryUsage.length > this.maxHistorySize) {
      this.metrics.memoryUsage.shift();
    }

    return memoryData;
  }

  getAverageCpuUsage() {
    if (this.metrics.cpuUsage.length === 0) return 0;
    const sum = this.metrics.cpuUsage.reduce((a, b) => a + b, 0);
    return sum / this.metrics.cpuUsage.length;
  }

  getMaxCpuUsage() {
    if (this.metrics.cpuUsage.length === 0) return 0;
    return Math.max(...this.metrics.cpuUsage);
  }

  getAverageMemoryUsage() {
    if (this.metrics.memoryUsage.length === 0) return 0;
    const sum = this.metrics.memoryUsage.reduce((a, b) => a + b.heapUsed, 0);
    return sum / this.metrics.memoryUsage.length;
  }

  getMaxMemoryUsage() {
    if (this.metrics.memoryUsage.length === 0) return 0;
    return Math.max(...this.metrics.memoryUsage.map(m => m.heapUsed));
  }

  getCurrentMemoryUsage() {
    if (this.metrics.memoryUsage.length === 0) return null;
    return this.metrics.memoryUsage[this.metrics.memoryUsage.length - 1];
  }

  recordProcessingTime(duration) {
    this.metrics.processingTime.push(duration);
    this.metrics.frameCount++;

    if (this.metrics.processingTime.length > this.maxHistorySize) {
      this.metrics.processingTime.shift();
    }
  }

  getStats() {
    const runtime = Date.now() - this.metrics.startTime;
    const currentMem = this.getCurrentMemoryUsage() || { rss: 0, heapUsed: 0, heapTotal: 0 };

    return {
      runtime: (runtime / 1000).toFixed(1) + 's',
      framesProcessed: this.metrics.frameCount,
      avgLatency: this.metrics.processingTime.length > 0
        ? (this.metrics.processingTime.reduce((a, b) => a + b) / this.metrics.processingTime.length).toFixed(2) + 'ms'
        : '0ms',
      avgCpuUsage: this.getAverageCpuUsage().toFixed(2) + '%',
      maxCpuUsage: this.getMaxCpuUsage().toFixed(2) + '%',
      currentCpuUsage: this.metrics.cpuUsage.length > 0
        ? this.metrics.cpuUsage[this.metrics.cpuUsage.length - 1].toFixed(2) + '%'
        : '0%',
      avgMemoryUsage: this.getAverageMemoryUsage().toFixed(2) + 'MB',
      maxMemoryUsage: this.getMaxMemoryUsage().toFixed(2) + 'MB',
      currentMemory: {
        rss: currentMem.rss.toFixed(2) + 'MB',
        heapUsed: currentMem.heapUsed.toFixed(2) + 'MB',
        heapTotal: currentMem.heapTotal.toFixed(2) + 'MB'
      },
      cpuSamples: this.metrics.cpuUsage.length,
      memorySamples: this.metrics.memoryUsage.length
    };
  }

  stop() {
    if (this.resourceInterval) {
      clearInterval(this.resourceInterval);
      console.log("✅ Resource monitoring stopped");
    }
  }
}

// ========================================
// Test Execution
// ========================================

console.log("1️⃣ Testing CPU & Memory Tracking...\n");

const monitor = new PerformanceMonitor();

// Simulate some CPU load to generate measurable metrics
function cpuIntensiveWork(duration) {
  const start = Date.now();
  let result = 0;
  while (Date.now() - start < duration) {
    result += Math.sqrt(Math.random() * 1000000);
  }
  return result;
}

// Run workload in phases
let testPhase = 0;
const testInterval = setInterval(() => {
  testPhase++;

  switch (testPhase) {
    case 1:
      console.log("\n📊 Phase 1: Idle baseline (2s)...");
      break;

    case 3:
      console.log("\n📊 Phase 2: Light CPU load (2s)...");
      cpuIntensiveWork(100);
      monitor.recordProcessingTime(2.5);
      break;

    case 5:
      console.log("\n📊 Phase 3: Heavy CPU load (2s)...");
      cpuIntensiveWork(200);
      monitor.recordProcessingTime(5.0);
      // Allocate some memory
      const buffer = Buffer.alloc(10 * 1024 * 1024); // 10MB
      buffer.fill(0);
      break;

    case 7:
      console.log("\n📊 Phase 4: Return to idle (2s)...");
      break;

    case 9:
      // Print final stats
      console.log("\n" + "=".repeat(60));
      console.log("📊 FINAL METRICS REPORT");
      console.log("=".repeat(60));

      const stats = monitor.getStats();
      console.log("\n⏱️  Runtime:");
      console.log(`   Total: ${stats.runtime}`);
      console.log(`   Frames Processed: ${stats.framesProcessed}`);
      console.log(`   Avg Latency: ${stats.avgLatency}`);

      console.log("\n🖥️  CPU Usage:");
      console.log(`   Current: ${stats.currentCpuUsage}`);
      console.log(`   Average: ${stats.avgCpuUsage}`);
      console.log(`   Peak: ${stats.maxCpuUsage}`);
      console.log(`   Samples: ${stats.cpuSamples}`);

      console.log("\n💾 Memory Usage:");
      console.log(`   Current RSS: ${stats.currentMemory.rss}`);
      console.log(`   Current Heap Used: ${stats.currentMemory.heapUsed}`);
      console.log(`   Current Heap Total: ${stats.currentMemory.heapTotal}`);
      console.log(`   Average Heap Used: ${stats.avgMemoryUsage}`);
      console.log(`   Peak Heap Used: ${stats.maxMemoryUsage}`);
      console.log(`   Samples: ${stats.memorySamples}`);

      console.log("\n" + "=".repeat(60));

      // Validation
      console.log("\n✅ Validation:");

      if (stats.cpuSamples >= 8) {
        console.log(`   ✅ CPU samples collected: ${stats.cpuSamples} (expected >= 8)`);
      } else {
        console.log(`   ❌ CPU samples insufficient: ${stats.cpuSamples} (expected >= 8)`);
      }

      if (stats.memorySamples >= 8) {
        console.log(`   ✅ Memory samples collected: ${stats.memorySamples} (expected >= 8)`);
      } else {
        console.log(`   ❌ Memory samples insufficient: ${stats.memorySamples} (expected >= 8)`);
      }

      const maxCpu = parseFloat(stats.maxCpuUsage);
      if (maxCpu > 0) {
        console.log(`   ✅ CPU usage detected: ${stats.maxCpuUsage} (expected > 0%)`);
      } else {
        console.log(`   ❌ No CPU usage detected`);
      }

      const maxMem = parseFloat(stats.maxMemoryUsage);
      if (maxMem > 0) {
        console.log(`   ✅ Memory usage tracked: ${stats.maxMemoryUsage} (expected > 0MB)`);
      } else {
        console.log(`   ❌ No memory usage tracked`);
      }

      console.log("\n🎉 Phase 2 Metrics Test Complete!\n");

      // Cleanup
      clearInterval(testInterval);
      monitor.stop();

      // Exit after cleanup
      setTimeout(() => {
        process.exit(0);
      }, 500);
      break;
  }
}, 1000);

// Safety timeout
setTimeout(() => {
  console.error("\n❌ Test timeout after 15s");
  monitor.stop();
  process.exit(1);
}, 15000);
