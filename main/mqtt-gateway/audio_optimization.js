/**
 * Audio Processing Optimization for ESP32 → LiveKit
 * 
 * This file contains optimized audio processing methods to improve
 * quality and reduce latency in the MQTT gateway.
 */

/**
 * Optimized sendAudio method with reduced processing overhead
 * Key improvements:
 * 1. Skip Opus detection for known devices
 * 2. Direct Opus passthrough when possible
 * 3. Reduced buffer copying
 * 4. Streamlined error handling
 */
async function sendAudioOptimized(opusData, timestamp) {
  // Quick validation
  if (!this.audioSource || !this.room || !this.room.isConnected) {
    return;
  }

  try {
    // OPTIMIZATION 1: Cache audio format after first detection
    if (!this.cachedAudioFormat) {
      this.cachedAudioFormat = this.detectAudioFormat(opusData);
      console.log(`🎵 [CACHE] Detected audio format: ${this.cachedAudioFormat} for device ${this.macAddress}`);
    }

    const startTime = process.hrtime.bigint();

    if (this.cachedAudioFormat === 'opus') {
      // OPTIMIZATION 2: Direct Opus processing (skip worker thread for simple decode)
      const pcmBuffer = await this.decodeOpusDirect(opusData);
      
      if (pcmBuffer && pcmBuffer.length > 0) {
        // OPTIMIZATION 3: Minimal buffer operations
        this.saveToWAVOptimized(pcmBuffer);
        await this.captureAudioFrameOptimized(pcmBuffer);
      }
    } else {
      // PCM path (minimal processing)
      this.saveToWAVOptimized(opusData);
      await this.captureAudioFrameOptimized(opusData);
    }

    // Performance tracking
    const processingTime = Number(process.hrtime.bigint() - startTime) / 1000000;
    if (processingTime > 5) {
      console.warn(`⚠️ [PERF] Slow audio processing: ${processingTime.toFixed(2)}ms`);
    }

  } catch (error) {
    console.error(`❌ [AUDIO] Processing error: ${error.message}`);
  }
}

/**
 * Simplified audio format detection (runs only once per device)
 */
function detectAudioFormat(data) {
  if (data.length < 1) return 'pcm';

  // Quick Opus detection (simplified)
  const firstByte = data[0];
  const config = (firstByte >> 3) & 0x1f;
  const stereo = (firstByte >> 2) & 0x01;
  
  // Basic validation for ESP32 Opus (16kHz mono)
  const isLikelyOpus = (
    data.length >= 10 && 
    data.length <= 400 && 
    config >= 0 && config <= 31 && 
    stereo === 0
  );

  return isLikelyOpus ? 'opus' : 'pcm';
}

/**
 * Direct Opus decoding without worker thread overhead
 * Use this for low-latency scenarios
 */
async function decodeOpusDirect(opusData) {
  if (!this.directOpusDecoder) {
    const { OpusEncoder } = require('@discordjs/opus');
    this.directOpusDecoder = new OpusEncoder(16000, 1);
    console.log(`🎵 [DIRECT] Created direct Opus decoder for ${this.macAddress}`);
  }

  try {
    return this.directOpusDecoder.decode(opusData);
  } catch (error) {
    console.error(`❌ [DIRECT] Opus decode error: ${error.message}`);
    return null;
  }
}

/**
 * Optimized audio frame capture with minimal buffer operations
 */
async function captureAudioFrameOptimized(audioBuffer) {
  try {
    // Create Int16Array view directly (no buffer copy)
    const samples = new Int16Array(
      audioBuffer.buffer,
      audioBuffer.byteOffset,
      audioBuffer.length / 2
    );

    // Create AudioFrame with minimal overhead
    const frame = new (require('@livekit/rtc-node').AudioFrame)(samples, 16000, 1, samples.length);
    
    // Direct capture (no intermediate processing)
    await this.audioSource.captureFrame(frame);
    
  } catch (error) {
    // Simplified error handling
    if (!error.message.includes('InvalidState')) {
      console.error(`❌ [CAPTURE] Frame capture error: ${error.message}`);
    }
  }
}

/**
 * Optimized WAV recording with reduced overhead
 */
function saveToWAVOptimized(pcmData) {
  if (this.isRecording && this.wavWriter && pcmData && pcmData.length > 0) {
    // Direct write without validation overhead
    this.wavWriter.audioData.push(pcmData);
    this.wavWriter.totalBytes += pcmData.length;
  }
}

/**
 * Batch audio processing for multiple frames
 * Process multiple audio packets together to reduce per-packet overhead
 */
class BatchAudioProcessor {
  constructor(batchSize = 5, maxWaitMs = 10) {
    this.batchSize = batchSize;
    this.maxWaitMs = maxWaitMs;
    this.audioQueue = [];
    this.batchTimer = null;
  }

  addAudioData(opusData, timestamp) {
    this.audioQueue.push({ opusData, timestamp, receivedAt: Date.now() });

    // Process batch when full or after timeout
    if (this.audioQueue.length >= this.batchSize) {
      this.processBatch();
    } else if (!this.batchTimer) {
      this.batchTimer = setTimeout(() => this.processBatch(), this.maxWaitMs);
    }
  }

  async processBatch() {
    if (this.batchTimer) {
      clearTimeout(this.batchTimer);
      this.batchTimer = null;
    }

    if (this.audioQueue.length === 0) return;

    const batch = this.audioQueue.splice(0);
    const startTime = process.hrtime.bigint();

    try {
      // Process all frames in batch
      for (const { opusData, timestamp } of batch) {
        await this.sendAudioOptimized(opusData, timestamp);
      }

      const batchTime = Number(process.hrtime.bigint() - startTime) / 1000000;
      console.log(`🚀 [BATCH] Processed ${batch.length} frames in ${batchTime.toFixed(2)}ms`);

    } catch (error) {
      console.error(`❌ [BATCH] Batch processing error: ${error.message}`);
    }
  }
}

/**
 * Audio quality monitoring
 */
class AudioQualityMonitor {
  constructor() {
    this.metrics = {
      packetsReceived: 0,
      packetsProcessed: 0,
      processingTimes: [],
      errors: 0,
      lastQualityCheck: Date.now()
    };
  }

  recordPacket(processingTimeMs, hasError = false) {
    this.metrics.packetsReceived++;
    if (!hasError) {
      this.metrics.packetsProcessed++;
      this.metrics.processingTimes.push(processingTimeMs);
    } else {
      this.metrics.errors++;
    }

    // Keep only last 100 measurements
    if (this.metrics.processingTimes.length > 100) {
      this.metrics.processingTimes.shift();
    }

    // Report quality every 30 seconds
    if (Date.now() - this.metrics.lastQualityCheck > 30000) {
      this.reportQuality();
      this.metrics.lastQualityCheck = Date.now();
    }
  }

  reportQuality() {
    const times = this.metrics.processingTimes;
    if (times.length === 0) return;

    const avgTime = times.reduce((a, b) => a + b) / times.length;
    const maxTime = Math.max(...times);
    const successRate = (this.metrics.packetsProcessed / this.metrics.packetsReceived) * 100;

    console.log(`📊 [QUALITY] Audio Processing Report:`);
    console.log(`   📦 Packets: ${this.metrics.packetsReceived} received, ${this.metrics.packetsProcessed} processed`);
    console.log(`   ✅ Success Rate: ${successRate.toFixed(1)}%`);
    console.log(`   ⏱️ Processing Time: ${avgTime.toFixed(2)}ms avg, ${maxTime.toFixed(2)}ms max`);
    console.log(`   ❌ Errors: ${this.metrics.errors}`);

    // Quality warnings
    if (avgTime > 10) {
      console.warn(`⚠️ [QUALITY] High processing latency detected: ${avgTime.toFixed(2)}ms`);
    }
    if (successRate < 95) {
      console.warn(`⚠️ [QUALITY] Low success rate detected: ${successRate.toFixed(1)}%`);
    }
  }

  getStats() {
    const times = this.metrics.processingTimes;
    return {
      packetsReceived: this.metrics.packetsReceived,
      packetsProcessed: this.metrics.packetsProcessed,
      successRate: (this.metrics.packetsProcessed / this.metrics.packetsReceived) * 100,
      avgProcessingTime: times.length > 0 ? times.reduce((a, b) => a + b) / times.length : 0,
      maxProcessingTime: times.length > 0 ? Math.max(...times) : 0,
      errors: this.metrics.errors
    };
  }
}

module.exports = {
  sendAudioOptimized,
  detectAudioFormat,
  decodeOpusDirect,
  captureAudioFrameOptimized,
  saveToWAVOptimized,
  BatchAudioProcessor,
  AudioQualityMonitor
};