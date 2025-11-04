# Design Document

## Overview

The design addresses the core issue where LiveKit's voice activity detection (VAD) fails to recognize children's voices when audio is processed through the MQTT gateway, while the same voices are successfully detected via direct React app connections. The solution focuses on identifying and eliminating audio quality degradation in the MQTT gateway pipeline that specifically impacts LiveKit's voice detection algorithms.

## Architecture

### Current Audio Pipeline Analysis

**MQTT Gateway Pipeline:**
```
ESP32 (16kHz Opus) → UDP → Decrypt → checkOpusFormat() → WorkerPool.decodeOpus() → PCM → AudioFrame → LiveKit AudioSource
```

**React App Pipeline (Actual):**
```
Browser Microphone → WebRTC (with AGC/NS/AEC) → RoomAudioRenderer → LiveKit Room
```

**Key Difference**: The React app uses browser WebRTC with built-in audio processing (Automatic Gain Control, Noise Suppression, Echo Cancellation) that enhances voice detection, while the MQTT gateway bypasses these optimizations by sending raw PCM data directly to LiveKit AudioSource.

### Root Cause Analysis

The MQTT gateway bypasses browser WebRTC audio processing that is critical for children's voice detection:

1. **Missing Audio Processing**: React app uses browser WebRTC with AGC/NS/AEC, MQTT gateway sends raw audio
2. **Different LiveKit Integration**: React app uses `RoomAudioRenderer` + microphone, MQTT gateway uses `AudioSource.captureFrame()`
3. **Audio Quality Degradation**: Multiple processing steps in MQTT gateway degrade audio quality
4. **Frequency Response Issues**: Children's voices (200-4000Hz) may be affected by processing artifacts
5. **LiveKit VAD Sensitivity**: LiveKit's voice activity detection expects WebRTC-processed audio characteristics

## Components and Interfaces

### 1. Audio Quality Analyzer Component

**Purpose**: Compare audio characteristics between MQTT gateway and React app
**Location**: New module `audio-quality-analyzer.js`

```javascript
class AudioQualityAnalyzer {
  // Analyze frequency spectrum, amplitude, and timing
  analyzeAudioCharacteristics(audioBuffer)
  
  // Compare two audio sources
  compareAudioSources(mqttAudio, reactAudio)
  
  // Detect LiveKit VAD-specific requirements
  validateVADRequirements(audioBuffer)
}
```

### 2. Optimized Audio Processor

**Purpose**: Minimize audio processing overhead
**Location**: Enhanced `sendAudio()` method in app.js

```javascript
class OptimizedAudioProcessor {
  // Bypass unnecessary processing for known formats
  processKnownOpusFormat(opusData)
  
  // Direct PCM conversion without worker threads
  directOpusDecode(opusData)
  
  // Match React app audio parameters exactly
  createLiveKitCompatibleFrame(pcmData)
}
```

### 3. Audio Format Matcher

**Purpose**: Ensure MQTT gateway output matches React app format
**Location**: New module `audio-format-matcher.js`

```javascript
class AudioFormatMatcher {
  // Detect React app audio parameters
  detectReactAppFormat()
  
  // Configure MQTT gateway to match
  configureMatchingFormat(targetFormat)
  
  // Validate format compatibility
  validateFormatMatch()
}
```

### 4. WebRTC Audio Processor

**Purpose**: Apply browser-like WebRTC audio processing to ESP32 audio
**Location**: New module `webrtc-audio-processor.js`

```javascript
class WebRTCAudioProcessor {
  // Apply automatic gain control like browser WebRTC
  applyAutomaticGainControl(pcmData)
  
  // Apply noise suppression for voice clarity
  applyNoiseSuppression(pcmData)
  
  // Enhance frequency response for children's voices
  enhanceVoiceFrequencies(pcmData)
  
  // Process audio to match browser WebRTC characteristics
  processLikeBrowserWebRTC(pcmData)
}
```

### 5. LiveKit Integration Matcher

**Purpose**: Use LiveKit integration method identical to React app
**Location**: Enhanced LiveKitBridge class

```javascript
class LiveKitIntegrationMatcher {
  // Switch from AudioSource to microphone-like integration
  enableMicrophoneLikeMode()
  
  // Use RoomAudioRenderer approach if possible
  configureRoomAudioRenderer()
  
  // Match React app's setMicrophoneEnabled() behavior
  simulateMicrophoneInput(processedAudio)
}
```

## Data Models

### Audio Quality Metrics

```javascript
interface AudioQualityMetrics {
  sampleRate: number;           // 16000 Hz
  bitDepth: number;             // 16 bits
  channels: number;             // 1 (mono)
  frequencyResponse: Float32Array; // 0-8000 Hz spectrum
  amplitude: {
    peak: number;               // Peak amplitude
    rms: number;                // RMS level
    snr: number;                // Signal-to-noise ratio
  };
  timing: {
    frameSize: number;          // Samples per frame
    frameDuration: number;      // Duration in ms
    jitter: number;             // Timing variance
  };
}
```

### Audio Processing Configuration

```javascript
interface AudioProcessingConfig {
  bypassOpusDetection: boolean;    // Skip checkOpusFormat() for known devices
  useDirectDecoding: boolean;      // Bypass worker threads
  matchReactAppFormat: boolean;    // Use identical format parameters
  enableQualityMonitoring: boolean; // Log quality metrics
  vadOptimization: boolean;        // Optimize for LiveKit VAD
}
```

### Voice Detection Test Results

```javascript
interface VoiceDetectionResults {
  source: 'mqtt-gateway' | 'react-app';
  testSamples: {
    childAge: number;              // Age of child in test sample
    detectionSuccess: boolean;     // Whether LiveKit detected voice
    confidence: number;            // Detection confidence (0-1)
    latency: number;              // Detection latency in ms
  }[];
  overallSuccessRate: number;      // Percentage of successful detections
  averageLatency: number;          // Average detection latency
}
```

## Error Handling

### Audio Quality Degradation Detection

```javascript
class AudioQualityMonitor {
  detectQualityDegradation(audioMetrics) {
    // Check for frequency loss in children's voice range (200-4000 Hz)
    if (audioMetrics.frequencyResponse.slice(200, 4000).some(level => level < -20)) {
      return { degraded: true, reason: 'frequency_loss' };
    }
    
    // Check for amplitude issues
    if (audioMetrics.amplitude.snr < -20) {
      return { degraded: true, reason: 'low_snr' };
    }
    
    // Check for timing issues
    if (audioMetrics.timing.jitter > 10) {
      return { degraded: true, reason: 'timing_jitter' };
    }
    
    return { degraded: false };
  }
}
```

### Fallback Processing Modes

1. **High Quality Mode**: Full processing with quality monitoring
2. **Optimized Mode**: Bypass worker threads, direct processing
3. **Compatibility Mode**: Match React app processing exactly
4. **Debug Mode**: Extensive logging and audio capture

### Error Recovery Strategies

```javascript
class AudioErrorRecovery {
  handleVADFailure(audioData) {
    // Try different processing modes
    const modes = ['optimized', 'compatibility', 'debug'];
    
    for (const mode of modes) {
      try {
        const result = this.processWithMode(audioData, mode);
        if (this.validateVADSuccess(result)) {
          this.switchToMode(mode);
          return result;
        }
      } catch (error) {
        console.warn(`Mode ${mode} failed:`, error.message);
      }
    }
    
    // Ultimate fallback: raw audio passthrough
    return this.passthroughMode(audioData);
  }
}
```

## Testing Strategy

### 1. Audio Quality Comparison Tests

**Objective**: Compare MQTT gateway vs React app audio reaching LiveKit

```javascript
describe('Audio Quality Comparison', () => {
  test('Frequency response matches React app', async () => {
    const mqttAudio = await captureAudioFromMQTTGateway();
    const reactAudio = await captureAudioFromReactApp();
    
    const comparison = audioAnalyzer.compareFrequencyResponse(mqttAudio, reactAudio);
    expect(comparison.similarity).toBeGreaterThan(0.95);
  });
  
  test('Amplitude levels match React app', async () => {
    // Test amplitude preservation
  });
  
  test('Timing characteristics match React app', async () => {
    // Test frame timing and jitter
  });
});
```

### 2. LiveKit VAD Detection Tests

**Objective**: Verify children's voice detection parity

```javascript
describe('LiveKit VAD Detection', () => {
  test('Children voice detection via MQTT gateway', async () => {
    const childVoiceSamples = loadTestSamples('children_voices');
    
    for (const sample of childVoiceSamples) {
      const mqttResult = await testVADViaMQTTGateway(sample);
      const reactResult = await testVADViaReactApp(sample);
      
      expect(mqttResult.detected).toBe(reactResult.detected);
      expect(Math.abs(mqttResult.latency - reactResult.latency)).toBeLessThan(50);
    }
  });
  
  test('Voice detection success rate parity', async () => {
    const results = await runVoiceDetectionBenchmark();
    expect(results.mqttSuccessRate).toBeGreaterThan(0.95 * results.reactSuccessRate);
  });
});
```

### 3. Performance Regression Tests

**Objective**: Ensure optimizations don't break existing functionality

```javascript
describe('Performance Regression', () => {
  test('Adult voice detection still works', async () => {
    // Ensure adult voices continue to work
  });
  
  test('Audio latency within acceptable limits', async () => {
    // Verify processing latency < 100ms
  });
  
  test('Memory usage remains stable', async () => {
    // Check for memory leaks in optimized processing
  });
});
```

### 4. Integration Tests

**Objective**: Test complete ESP32 → MQTT Gateway → LiveKit flow

```javascript
describe('End-to-End Integration', () => {
  test('ESP32 children voice detection', async () => {
    // Test with real ESP32 device and children's voices
    const esp32Audio = await captureFromESP32();
    const vadResult = await processViaLiveKit(esp32Audio);
    
    expect(vadResult.voiceDetected).toBe(true);
    expect(vadResult.confidence).toBeGreaterThan(0.7);
  });
});
```

## Implementation Phases

### Phase 1: Audio Quality Analysis (Week 1)
- Implement AudioQualityAnalyzer
- Capture and compare MQTT vs React audio
- Identify specific quality differences
- Document findings

### Phase 2: Processing Optimization (Week 2)
- Implement OptimizedAudioProcessor
- Bypass unnecessary processing steps
- Add direct decoding path
- Optimize buffer operations

### Phase 3: Format Matching (Week 3)
- Implement AudioFormatMatcher
- Configure MQTT gateway to match React app exactly
- Validate format compatibility
- Test with children's voice samples

### Phase 4: Integration & Testing (Week 4)
- Comprehensive testing with real ESP32 devices
- Performance validation
- Regression testing
- Documentation and deployment

## Success Metrics

1. **Voice Detection Parity**: 95%+ success rate match between MQTT gateway and React app for children's voices
2. **Audio Quality**: Frequency response similarity > 95% in 200-4000 Hz range
3. **Latency**: Total processing latency < 100ms per audio frame
4. **Reliability**: Zero voice detection regressions for adult voices
5. **Performance**: CPU usage reduction of 30%+ through optimizations

## Risk Mitigation

### Technical Risks
- **LiveKit SDK Limitations**: May not support identical processing to browser WebRTC
  - *Mitigation*: Implement custom audio processing to match browser behavior
  
- **ESP32 Audio Quality**: Hardware limitations may affect audio quality
  - *Mitigation*: Test with multiple ESP32 devices and audio configurations
  
- **Network Latency**: UDP transmission may introduce timing issues
  - *Mitigation*: Implement adaptive buffering and jitter compensation

### Implementation Risks
- **Breaking Existing Functionality**: Optimizations may affect adult voice detection
  - *Mitigation*: Comprehensive regression testing and gradual rollout
  
- **Performance Degradation**: Quality improvements may increase CPU usage
  - *Mitigation*: Implement configurable processing modes and monitoring