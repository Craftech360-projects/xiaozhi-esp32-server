# Audio Processing Optimization Plan

## Overview

This document outlines strategies to add back audio resampling, Opus encoding, and AES encryption to the simplified audio pipeline without introducing jitter or performance issues.

## Current State Analysis

### What We Removed (and why it caused jitter):
- **AudioResampler** - Was doing Float32→Int16 conversion + resampling
- **Opus Encoder/Decoder** - CPU-intensive codec operations
- **AES Encryption/Decryption** - Cryptographic overhead
- **Complex Buffering Logic** - Buffer accumulation causing delays

### Root Causes of Original Jitter:
1. **Synchronous Processing** - All operations in main thread
2. **Buffer Accumulation** - Complex buffering logic caused delays  
3. **Multiple Format Conversions** - Float32→Int16→Resampled→Opus→Encrypted
4. **JavaScript Single-Threading** - CPU-intensive operations blocked event loop
5. **Memory Allocations** - Frequent Buffer.concat() operations

## Optimization Strategies

### Strategy 1: Asynchronous Processing with Worker Threads

#### Implementation Plan:

**Audio Worker (main/mqtt-gateway/audio-worker.js):**
```javascript
const { Worker, isMainThread, parentPort, workerData } = require('worker_threads');
const { AudioResampler } = require('@livekit/rtc-node');
const OpusEncoder = require('@discordjs/opus').OpusEncoder;
const crypto = require('crypto');

class AudioProcessor {
  constructor() {
    this.resampler = new AudioResampler(48000, 24000, 1, AudioResamplerQuality.QUICK);
    this.opusEncoder = new OpusEncoder(24000, 1);
  }

  processAudioChunk(float32Data, encryptionKey, header) {
    // 1. Convert Float32 to Int16 (optimized)
    const int16Data = this.convertFloat32ToInt16Fast(float32Data);
    
    // 2. Resample (if needed)
    const resampledData = this.resampler.process(int16Data);
    
    // 3. Encode to Opus (chunked processing)
    const opusData = this.opusEncoder.encode(resampledData);
    
    // 4. Encrypt (streaming cipher)
    const encryptedData = this.encryptStreaming(opusData, encryptionKey, header);
    
    return encryptedData;
  }

  convertFloat32ToInt16Fast(float32Array) {
    const int16Array = new Int16Array(float32Array.length);
    for (let i = 0; i < float32Array.length; i++) {
      int16Array[i] = Math.max(-32768, Math.min(32767, float32Array[i] * 32767));
    }
    return Buffer.from(int16Array.buffer);
  }

  encryptStreaming(data, key, header) {
    const cipher = crypto.createCipheriv('aes-256-ctr', key, header);
    return Buffer.concat([cipher.update(data), cipher.final()]);
  }
}

if (!isMainThread) {
  const processor = new AudioProcessor();
  
  parentPort.on('message', ({ audioData, encryptionKey, header, id }) => {
    try {
      const result = processor.processAudioChunk(audioData, encryptionKey, header);
      parentPort.postMessage({ id, result, success: true });
    } catch (error) {
      parentPort.postMessage({ id, error: error.message, success: false });
    }
  });
}

module.exports = AudioProcessor;
```

**Main Thread Integration:**
```javascript
class LiveKitBridge {
  constructor() {
    // Create worker pool for audio processing
    this.audioWorkers = [];
    this.workerIndex = 0;
    this.pendingRequests = new Map();
    this.requestId = 0;
    
    for (let i = 0; i < 2; i++) { // 2 workers for load balancing
      const worker = new Worker('./audio-worker.js');
      worker.on('message', this.handleWorkerMessage.bind(this));
      this.audioWorkers.push(worker);
    }
  }

  async processAudioFrame(audioFrame) {
    const worker = this.audioWorkers[this.workerIndex];
    this.workerIndex = (this.workerIndex + 1) % this.audioWorkers.length;
    
    const requestId = ++this.requestId;
    
    return new Promise((resolve, reject) => {
      this.pendingRequests.set(requestId, { resolve, reject });
      
      worker.postMessage({
        id: requestId,
        audioData: audioFrame.data,
        encryptionKey: this.udp.key,
        header: this.generateUdpHeader(),
        timestamp: Date.now()
      });
      
      // Timeout after 50ms to prevent hanging
      setTimeout(() => {
        if (this.pendingRequests.has(requestId)) {
          this.pendingRequests.delete(requestId);
          reject(new Error('Audio processing timeout'));
        }
      }, 50);
    });
  }

  handleWorkerMessage({ id, result, error, success }) {
    const request = this.pendingRequests.get(id);
    if (request) {
      this.pendingRequests.delete(id);
      if (success) {
        request.resolve(result);
      } else {
        request.reject(new Error(error));
      }
    }
  }
}
```

### Strategy 2: Optimized Native Modules

#### Option A: Use Native Opus Implementation
```bash
# Install native Opus library (faster than JS implementation)
npm install @discordjs/opus  # Uses native libopus
# OR
npm install node-opus       # Direct libopus bindings
```

#### Option B: Use Native Crypto (Faster AES)
```javascript
const crypto = require('crypto');

class OptimizedCrypto {
  constructor(key) {
    this.key = key;
    // Pre-create cipher instances for reuse
    this.cipherPool = [];
    this.maxPoolSize = 4;
  }

  encryptFast(data, iv) {
    // Reuse cipher instances to avoid creation overhead
    let cipher = this.cipherPool.pop();
    if (!cipher) {
      cipher = crypto.createCipher('aes-256-ctr', this.key);
    }
    
    const encrypted = cipher.update(data);
    
    // Return to pool if not full
    if (this.cipherPool.length < this.maxPoolSize) {
      this.cipherPool.push(cipher);
    }
    
    return encrypted;
  }

  // Streaming encryption for large data
  createStreamingCipher(iv) {
    return crypto.createCipheriv('aes-256-ctr', this.key, iv);
  }
}
```

### Strategy 3: Streaming Pipeline Architecture

#### Eliminate Buffer Accumulation:
```javascript
const { Transform } = require('stream');

class StreamingAudioPipeline extends Transform {
  constructor(options = {}) {
    super({
      objectMode: true,
      transform: this.processChunk.bind(this),
      highWaterMark: 1 // Minimize buffering
    });
    
    this.resampler = new AudioResampler(48000, 24000, 1);
    this.opusEncoder = new OpusEncoder(24000, 1);
    this.crypto = new OptimizedCrypto(options.encryptionKey);
  }

  processChunk(audioFrame, encoding, callback) {
    // Process immediately without accumulation
    setImmediate(() => {
      try {
        const processed = this.processAudioImmediate(audioFrame);
        callback(null, processed);
      } catch (error) {
        callback(error);
      }
    });
  }

  processAudioImmediate(frame) {
    // Direct processing without intermediate buffers
    const int16 = this.convertFloat32ToInt16Vectorized(frame.data);
    const resampled = this.resampleInPlace(int16);
    const opus = this.encodeOpusStreaming(resampled);
    const encrypted = this.encryptInPlace(opus);
    return encrypted;
  }

  convertFloat32ToInt16Vectorized(float32Array) {
    // Optimized conversion using typed arrays
    const length = float32Array.length;
    const int16Array = new Int16Array(length);
    
    // Vectorized operation - much faster than loop
    for (let i = 0; i < length; i += 4) {
      // Process 4 samples at once
      const end = Math.min(i + 4, length);
      for (let j = i; j < end; j++) {
        const sample = Math.max(-1, Math.min(1, float32Array[j]));
        int16Array[j] = Math.round(sample * 32767);
      }
    }
    
    return Buffer.from(int16Array.buffer);
  }

  resampleInPlace(int16Buffer) {
    // Use resampler with minimal memory allocation
    const audioFrame = new AudioFrame(
      new Int16Array(int16Buffer.buffer), 
      48000, 1, int16Buffer.length / 2
    );
    
    const resampled = this.resampler.push(audioFrame);
    return resampled[0] ? Buffer.from(resampled[0].data.buffer) : Buffer.alloc(0);
  }

  encodeOpusStreaming(pcmBuffer) {
    // Encode with error handling
    try {
      return this.opusEncoder.encode(pcmBuffer, pcmBuffer.length / 2);
    } catch (error) {
      console.warn('Opus encoding failed, falling back to PCM:', error.message);
      return pcmBuffer; // Fallback to PCM
    }
  }

  encryptInPlace(data) {
    // Streaming encryption
    return this.crypto.encryptFast(data, this.generateIV());
  }

  generateIV() {
    // Generate IV based on timestamp for uniqueness
    const timestamp = Date.now();
    const iv = Buffer.alloc(16);
    iv.writeUInt32BE(timestamp, 0);
    return iv;
  }
}
```

### Strategy 4: Alternative High-Performance Platforms

#### Option A: Rust-based Audio Processing

**Cargo.toml:**
```toml
[package]
name = "audio-processor"
version = "0.1.0"
edition = "2021"

[dependencies]
napi = "2.0"
napi-derive = "2.0"
opus = "0.3"
aes = "0.8"
rubato = "0.12"  # High-performance resampler

[lib]
crate-type = ["cdylib"]

[build-dependencies]
napi-build = "2.0"
```

**src/lib.rs:**
```rust
use napi::bindgen_prelude::*;
use opus::{Encoder, Application, Channels};
use aes::cipher::{KeyIvInit, StreamCipher};
use aes::Aes256;
use aes::cipher::generic_array::GenericArray;
use rubato::{Resampler, SincFixedIn, InterpolationType, InterpolationParameters, WindowFunction};

#[napi]
pub struct AudioProcessor {
    resampler: SincFixedIn<f32>,
    opus_encoder: Encoder,
    cipher_key: [u8; 32],
}

#[napi]
impl AudioProcessor {
    #[napi(constructor)]
    pub fn new(encryption_key: Buffer) -> Result<Self> {
        let mut key = [0u8; 32];
        key.copy_from_slice(&encryption_key[..32]);
        
        let params = InterpolationParameters {
            sinc_len: 256,
            f_cutoff: 0.95,
            interpolation: InterpolationType::Linear,
            oversampling_factor: 256,
            window: WindowFunction::BlackmanHarris2,
        };
        
        Ok(AudioProcessor {
            resampler: SincFixedIn::new(
                48000.0 / 24000.0, // Ratio
                2.0,               // Max ratio change
                params,
                1024,              // Chunk size
                1,                 // Channels
            )?,
            opus_encoder: Encoder::new(24000, Channels::Mono, Application::Audio)?,
            cipher_key: key,
        })
    }

    #[napi]
    pub fn process_audio(&mut self, input: Float32Array, iv: Buffer) -> Result<Buffer> {
        // Convert Float32 to Vec<f32>
        let input_vec: Vec<f32> = input.to_vec();
        
        // Resample (ultra-fast Rust implementation)
        let resampled = self.resampler.process(&[input_vec], None)?;
        
        // Convert to i16 for Opus
        let int16_samples: Vec<i16> = resampled[0]
            .iter()
            .map(|&sample| (sample.clamp(-1.0, 1.0) * 32767.0) as i16)
            .collect();
        
        // Encode with Opus
        let opus_data = self.opus_encoder.encode_vec(&int16_samples, 960)?;
        
        // Encrypt with AES
        let mut cipher = aes::Aes256Ctr::new(
            GenericArray::from_slice(&self.cipher_key),
            GenericArray::from_slice(&iv[..16])
        );
        
        let mut encrypted_data = opus_data.clone();
        cipher.apply_keystream(&mut encrypted_data);
        
        Ok(encrypted_data.into())
    }
}
```

**Build script:**
```bash
# Build Rust module
npm install -g @napi-rs/cli
napi build --platform --release

# Install in Node.js project
npm install ./audio-processor.node
```

#### Option B: WebAssembly (WASM) Audio Processing

**audio-processor.wat (WebAssembly Text Format):**
```wat
(module
  (memory (export "memory") 256)
  
  (func $process_audio (export "process_audio")
    (param $input_ptr i32) (param $input_len i32)
    (result i32)
    
    ;; Ultra-fast WASM audio processing
    ;; Direct memory operations - no JS overhead
    (local $i i32)
    (local $sample f32)
    (local $output_ptr i32)
    
    ;; Allocate output buffer
    (local.set $output_ptr (call $allocate (i32.mul (local.get $input_len) (i32.const 2))))
    
    ;; Process samples
    (loop $process_loop
      ;; Load float32 sample
      (local.set $sample (f32.load (i32.add (local.get $input_ptr) (i32.mul (local.get $i) (i32.const 4)))))
      
      ;; Convert to int16 and store
      (i32.store16 
        (i32.add (local.get $output_ptr) (i32.mul (local.get $i) (i32.const 2)))
        (i32.trunc_f32_s (f32.mul (local.get $sample) (f32.const 32767.0)))
      )
      
      ;; Increment counter
      (local.set $i (i32.add (local.get $i) (i32.const 1)))
      
      ;; Continue if not done
      (br_if $process_loop (i32.lt_u (local.get $i) (local.get $input_len)))
    )
    
    (local.get $output_ptr)
  )
  
  (func $allocate (export "allocate") (param $size i32) (result i32)
    ;; Simple allocator
    (i32.const 1024) ;; Return fixed offset for simplicity
  )
)
```

**JavaScript Integration:**
```javascript
class WASMAudioProcessor {
  constructor() {
    this.wasmModule = null;
    this.memory = null;
  }

  async initialize() {
    // Load WASM module
    const wasmBytes = await fs.readFile('./audio-processor.wasm');
    this.wasmModule = await WebAssembly.instantiate(wasmBytes);
    this.memory = new Float32Array(this.wasmModule.instance.exports.memory.buffer);
  }

  processAudio(audioData) {
    if (!this.wasmModule) {
      throw new Error('WASM module not initialized');
    }

    // Direct memory operations - no JS overhead
    const inputPtr = this.wasmModule.instance.exports.allocate(audioData.length * 4);
    this.memory.set(audioData, inputPtr / 4);
    
    const outputPtr = this.wasmModule.instance.exports.process_audio(
      inputPtr, audioData.length
    );
    
    const outputSize = audioData.length * 2; // int16 output
    return new Uint8Array(
      this.wasmModule.instance.exports.memory.buffer, 
      outputPtr, 
      outputSize
    );
  }
}
```

## Implementation Phases

### Phase 1: Immediate Optimizations (Low Risk)

**Timeline: 1-2 days**

1. **Use Native Opus Library:**
```bash
npm uninstall @voicehype/audify-plus
npm install @discordjs/opus
```

2. **Implement Streaming Crypto:**
```javascript
class StreamingCrypto {
  constructor(key) {
    this.key = key;
    this.cipherCache = new Map();
  }
  
  encryptChunk(data, iv) {
    const cacheKey = iv.toString('hex');
    let cipher = this.cipherCache.get(cacheKey);
    
    if (!cipher) {
      cipher = crypto.createCipheriv('aes-256-ctr', this.key, iv);
      this.cipherCache.set(cacheKey, cipher);
    }
    
    return cipher.update(data);
  }
}
```

3. **Optimize Float32→Int16 Conversion:**
```javascript
function convertFloat32ToInt16Fast(float32Array) {
  const length = float32Array.length;
  const int16Array = new Int16Array(length);
  
  // Unrolled loop for better performance
  let i = 0;
  for (; i < length - 3; i += 4) {
    int16Array[i] = Math.round(Math.max(-1, Math.min(1, float32Array[i])) * 32767);
    int16Array[i + 1] = Math.round(Math.max(-1, Math.min(1, float32Array[i + 1])) * 32767);
    int16Array[i + 2] = Math.round(Math.max(-1, Math.min(1, float32Array[i + 2])) * 32767);
    int16Array[i + 3] = Math.round(Math.max(-1, Math.min(1, float32Array[i + 3])) * 32767);
  }
  
  // Handle remaining samples
  for (; i < length; i++) {
    int16Array[i] = Math.round(Math.max(-1, Math.min(1, float32Array[i])) * 32767);
  }
  
  return Buffer.from(int16Array.buffer);
}
```

### Phase 2: Architecture Improvements (Medium Risk)

**Timeline: 3-5 days**

4. **Implement Worker Thread Processing:**
   - Move audio processing to separate threads
   - Use message passing for coordination
   - Implement worker pool for load balancing

5. **Add Streaming Pipeline:**
   - Eliminate buffer accumulation
   - Process frames immediately
   - Use Transform streams for flow control

6. **Add Performance Monitoring:**
```javascript
class PerformanceMonitor {
  constructor() {
    this.metrics = {
      processingTime: [],
      queueSize: [],
      cpuUsage: [],
      memoryUsage: []
    };
  }

  recordProcessingTime(startTime) {
    const duration = Number(process.hrtime.bigint() - startTime) / 1000000;
    this.metrics.processingTime.push(duration);
    
    // Keep only last 100 measurements
    if (this.metrics.processingTime.length > 100) {
      this.metrics.processingTime.shift();
    }
    
    return duration;
  }

  getAverageProcessingTime() {
    const times = this.metrics.processingTime;
    return times.length > 0 ? times.reduce((a, b) => a + b) / times.length : 0;
  }

  shouldDowngrade() {
    return this.getAverageProcessingTime() > 10; // 10ms threshold
  }
}
```

### Phase 3: Advanced Optimizations (Higher Risk)

**Timeline: 1-2 weeks**

7. **Consider Rust/WASM Module:**
   - For maximum performance
   - If JavaScript optimizations aren't sufficient
   - Requires more development time

8. **Implement Adaptive Quality:**
```javascript
class AdaptiveAudioProcessor {
  constructor() {
    this.performanceMode = 'full'; // full, medium, minimal
    this.monitor = new PerformanceMonitor();
  }

  processAudio(frame) {
    const startTime = process.hrtime.bigint();
    
    let result;
    switch (this.performanceMode) {
      case 'full':
        result = this.processWithAllFeatures(frame);
        break;
      case 'medium':
        result = this.processWithOpusOnly(frame);
        break;
      case 'minimal':
        result = this.processDirectPCM(frame);
        break;
    }
    
    const processingTime = this.monitor.recordProcessingTime(startTime);
    this.adaptPerformanceMode(processingTime);
    
    return result;
  }

  processWithAllFeatures(frame) {
    // Full pipeline: Resample + Opus + Encrypt
    const int16 = this.convertFloat32ToInt16(frame.data);
    const resampled = this.resampler.process(int16);
    const opus = this.opusEncoder.encode(resampled);
    const encrypted = this.crypto.encrypt(opus);
    return encrypted;
  }

  processWithOpusOnly(frame) {
    // Skip resampling, keep Opus + Encrypt
    const int16 = this.convertFloat32ToInt16(frame.data);
    const opus = this.opusEncoder.encode(int16);
    const encrypted = this.crypto.encrypt(opus);
    return encrypted;
  }

  processDirectPCM(frame) {
    // Minimal processing: just convert and encrypt
    const int16 = this.convertFloat32ToInt16(frame.data);
    const encrypted = this.crypto.encrypt(int16);
    return encrypted;
  }

  adaptPerformanceMode(latency) {
    if (latency > 15 && this.performanceMode === 'full') {
      this.performanceMode = 'medium';
      console.log('🔄 Downgraded to medium performance mode');
    } else if (latency > 25 && this.performanceMode === 'medium') {
      this.performanceMode = 'minimal';
      console.log('🔄 Downgraded to minimal performance mode');
    } else if (latency < 5 && this.performanceMode === 'medium') {
      this.performanceMode = 'full';
      console.log('🔄 Upgraded to full performance mode');
    } else if (latency < 10 && this.performanceMode === 'minimal') {
      this.performanceMode = 'medium';
      console.log('🔄 Upgraded to medium performance mode');
    }
  }
}
```

## Performance Targets

### Benchmarks to Achieve:
- **Audio Processing Latency:** < 5ms per frame
- **CPU Usage:** < 10% per audio stream
- **Memory Usage:** < 50MB total
- **Jitter:** < 1ms variance
- **Throughput:** > 100 concurrent streams

### Monitoring Metrics:
```javascript
class AudioMetrics {
  constructor() {
    this.startTime = Date.now();
    this.frameCount = 0;
    this.totalProcessingTime = 0;
    this.maxLatency = 0;
    this.minLatency = Infinity;
  }

  recordFrame(processingTime) {
    this.frameCount++;
    this.totalProcessingTime += processingTime;
    this.maxLatency = Math.max(this.maxLatency, processingTime);
    this.minLatency = Math.min(this.minLatency, processingTime);
  }

  getStats() {
    const runtime = Date.now() - this.startTime;
    return {
      framesPerSecond: (this.frameCount / runtime) * 1000,
      averageLatency: this.totalProcessingTime / this.frameCount,
      maxLatency: this.maxLatency,
      minLatency: this.minLatency,
      jitter: this.maxLatency - this.minLatency
    };
  }
}
```

## Fallback Strategy

### Graceful Degradation:
1. **Full Features** → Resample + Opus + Encrypt
2. **Medium Quality** → Opus + Encrypt (skip resampling)
3. **Minimal Processing** → Direct PCM + Encrypt
4. **Emergency Mode** → Direct PCM (no encryption)

### Implementation:
```javascript
class FallbackAudioProcessor {
  constructor() {
    this.currentMode = 'full';
    this.fallbackChain = ['full', 'medium', 'minimal', 'emergency'];
    this.upgradeTimer = null;
  }

  processWithFallback(frame) {
    for (let i = this.fallbackChain.indexOf(this.currentMode); i < this.fallbackChain.length; i++) {
      try {
        const mode = this.fallbackChain[i];
        const startTime = process.hrtime.bigint();
        
        const result = this.processWithMode(frame, mode);
        
        const processingTime = Number(process.hrtime.bigint() - startTime) / 1000000;
        
        if (processingTime < 10) { // Success within 10ms
          if (mode !== this.currentMode) {
            console.log(`✅ Switched to ${mode} mode`);
            this.currentMode = mode;
          }
          
          // Schedule upgrade attempt
          this.scheduleUpgrade();
          
          return result;
        }
      } catch (error) {
        console.warn(`❌ ${this.fallbackChain[i]} mode failed:`, error.message);
        continue;
      }
    }
    
    throw new Error('All audio processing modes failed');
  }

  scheduleUpgrade() {
    if (this.upgradeTimer) return;
    
    this.upgradeTimer = setTimeout(() => {
      const currentIndex = this.fallbackChain.indexOf(this.currentMode);
      if (currentIndex > 0) {
        // Try to upgrade to better quality
        const betterMode = this.fallbackChain[currentIndex - 1];
        console.log(`🔄 Attempting upgrade to ${betterMode} mode`);
        // Next frame will try the better mode
      }
      this.upgradeTimer = null;
    }, 5000); // Try upgrade every 5 seconds
  }
}
```

## Testing Strategy

### Performance Tests:
```javascript
// test/audio-performance.test.js
const AudioProcessor = require('../audio-processor');

describe('Audio Performance Tests', () => {
  let processor;
  
  beforeEach(() => {
    processor = new AudioProcessor();
  });

  test('should process 1000 frames under 5ms average', async () => {
    const frameData = new Float32Array(960); // 20ms at 48kHz
    frameData.fill(0.5); // Test signal
    
    const times = [];
    
    for (let i = 0; i < 1000; i++) {
      const start = process.hrtime.bigint();
      await processor.processAudio(frameData);
      const duration = Number(process.hrtime.bigint() - start) / 1000000;
      times.push(duration);
    }
    
    const avgTime = times.reduce((a, b) => a + b) / times.length;
    const maxTime = Math.max(...times);
    const jitter = Math.max(...times) - Math.min(...times);
    
    expect(avgTime).toBeLessThan(5);
    expect(maxTime).toBeLessThan(15);
    expect(jitter).toBeLessThan(10);
  });

  test('should handle concurrent streams', async () => {
    const streamCount = 10;
    const frameData = new Float32Array(960);
    frameData.fill(0.5);
    
    const promises = [];
    const startTime = Date.now();
    
    for (let i = 0; i < streamCount; i++) {
      promises.push(processor.processAudio(frameData));
    }
    
    await Promise.all(promises);
    
    const totalTime = Date.now() - startTime;
    expect(totalTime).toBeLessThan(100); // All streams in under 100ms
  });
});
```

### Load Tests:
```javascript
// test/load-test.js
const cluster = require('cluster');
const numCPUs = require('os').cpus().length;

if (cluster.isMaster) {
  console.log(`Master ${process.pid} is running`);
  
  // Fork workers
  for (let i = 0; i < numCPUs; i++) {
    cluster.fork();
  }
  
  cluster.on('exit', (worker, code, signal) => {
    console.log(`Worker ${worker.process.pid} died`);
  });
} else {
  // Worker process - simulate audio processing load
  const AudioProcessor = require('../audio-processor');
  const processor = new AudioProcessor();
  
  setInterval(async () => {
    const frameData = new Float32Array(960);
    frameData.fill(Math.random() * 0.5);
    
    try {
      await processor.processAudio(frameData);
    } catch (error) {
      console.error(`Worker ${process.pid} error:`, error.message);
    }
  }, 20); // Process frame every 20ms
  
  console.log(`Worker ${process.pid} started`);
}
```

## Conclusion

This plan provides a comprehensive approach to adding back audio features without jitter:

1. **Start with Phase 1** - Low risk, immediate improvements
2. **Monitor performance** - Use metrics to guide decisions  
3. **Implement fallbacks** - Graceful degradation under load
4. **Consider advanced options** - Rust/WASM for maximum performance

The key is to implement incrementally and measure performance at each step, ensuring we maintain the jitter-free experience while adding back the desired features.

---

**Document Version:** 1.0  
**Last Updated:** October 25, 2025  
**Author:** AI Assistant  
**Status:** Ready for Implementation