# Implementation Plan

- [ ] 1. Analyze current audio processing differences between MQTT gateway and React app
  - Compare audio characteristics reaching LiveKit from both sources
  - Identify specific processing steps that degrade children's voice detection
  - Document frequency response and amplitude differences
  - _Requirements: 2.1, 2.2, 2.5_

- [ ] 1.1 Create audio quality comparison tool
  - Write script to capture audio from both MQTT gateway and React app
  - Implement frequency spectrum analysis for children's voice range (200-4000Hz)
  - Add amplitude and timing measurement capabilities
  - _Requirements: 2.1, 2.2_

- [ ] 1.2 Implement audio capture and logging system
  - Add detailed audio logging to MQTT gateway sendAudio() method
  - Capture raw ESP32 audio, processed PCM, and final AudioFrame data
  - Log audio characteristics that affect LiveKit VAD sensitivity
  - _Requirements: 2.2, 2.3_

- [ ]* 1.3 Create test suite for audio quality validation
  - Write automated tests comparing MQTT vs React audio quality
  - Add regression tests for children's voice detection
  - Implement performance benchmarks for audio processing
  - _Requirements: 4.1, 4.2_

- [ ] 2. Implement WebRTC-like audio processing for ESP32 audio
  - Apply automatic gain control, noise suppression, and frequency enhancement
  - Process ESP32 audio to match browser WebRTC characteristics
  - Optimize for children's voice frequency range
  - _Requirements: 1.1, 1.2, 3.2_

- [ ] 2.1 Create WebRTC audio processor module
  - Implement automatic gain control algorithm for consistent audio levels
  - Add noise suppression to improve voice clarity
  - Create frequency enhancement for children's voices (200-4000Hz boost)
  - _Requirements: 1.2, 3.2_

- [ ] 2.2 Integrate WebRTC processing into MQTT gateway pipeline
  - Modify sendAudio() method to apply WebRTC-like processing
  - Add processing between Opus decode and AudioFrame creation
  - Ensure processing maintains real-time performance requirements
  - _Requirements: 1.1, 1.5, 3.2_

- [ ] 2.3 Optimize processing performance for real-time audio
  - Implement efficient audio processing algorithms
  - Add configurable processing modes (high quality vs low latency)
  - Monitor CPU usage and optimize bottlenecks
  - _Requirements: 1.5, 2.4_

- [ ]* 2.4 Add audio processing unit tests
  - Test automatic gain control with various input levels
  - Validate noise suppression effectiveness
  - Verify frequency enhancement preserves audio quality
  - _Requirements: 2.1, 2.2_

- [ ] 3. Optimize MQTT gateway audio pipeline to reduce quality degradation
  - Eliminate unnecessary processing steps that degrade audio quality
  - Optimize buffer operations and reduce memory allocations
  - Implement direct processing path for known ESP32 devices
  - _Requirements: 2.1, 2.4, 3.1_

- [ ] 3.1 Implement cached format detection for ESP32 devices
  - Skip checkOpusFormat() validation after initial device detection
  - Cache audio format results per device MAC address
  - Reduce per-packet processing overhead
  - _Requirements: 2.1, 3.1_

- [ ] 3.2 Optimize worker thread usage for audio processing
  - Implement direct Opus decoding for low-latency processing
  - Add fallback to worker threads only for heavy processing
  - Reduce message passing overhead between threads
  - _Requirements: 2.2, 2.4_

- [ ] 3.3 Streamline AudioFrame creation and buffer operations
  - Optimize Int16Array conversions in sendAudio() method
  - Reduce buffer copying and memory allocations
  - Implement zero-copy audio processing where possible
  - _Requirements: 2.4, 3.2_

- [ ]* 3.4 Add performance monitoring and optimization tests
  - Monitor processing latency and CPU usage
  - Test memory allocation patterns and garbage collection impact
  - Validate optimization effectiveness with performance benchmarks
  - _Requirements: 2.2, 2.4_

- [ ] 4. Implement LiveKit integration matching React app behavior
  - Configure MQTT gateway to use LiveKit integration identical to React app
  - Match audio parameters, encoding settings, and transmission methods
  - Ensure LiveKit receives audio in the same format as browser WebRTC
  - _Requirements: 3.1, 3.3, 3.4_

- [ ] 4.1 Analyze React app LiveKit integration method
  - Study how React app uses setMicrophoneEnabled() and RoomAudioRenderer
  - Document exact LiveKit SDK methods and parameters used
  - Identify differences from current MQTT gateway AudioSource approach
  - _Requirements: 3.1, 3.3_

- [ ] 4.2 Implement microphone simulation for ESP32 audio
  - Create virtual microphone input that accepts ESP32 processed audio
  - Use LiveKit SDK methods identical to React app microphone handling
  - Ensure audio reaches LiveKit through same code path as browser
  - _Requirements: 3.3, 3.4_

- [ ] 4.3 Configure identical audio parameters and encoding
  - Match sample rate, bit depth, and frame size to React app
  - Use same LiveKit AudioSource configuration as browser WebRTC
  - Ensure encoding parameters match browser WebRTC settings
  - _Requirements: 3.2, 3.3_

- [ ]* 4.4 Add integration compatibility tests
  - Test LiveKit integration parity between MQTT gateway and React app
  - Validate audio parameter matching and encoding compatibility
  - Verify microphone simulation works correctly
  - _Requirements: 3.1, 3.3_

- [ ] 5. Implement comprehensive voice detection testing and validation
  - Create automated testing for children's voice detection parity
  - Validate LiveKit VAD performance with processed ESP32 audio
  - Ensure detection rates match React app performance
  - _Requirements: 4.1, 4.2, 4.3_

- [ ] 5.1 Create children's voice detection test suite
  - Implement automated tests with children's voice samples (ages 3-12)
  - Test voice detection success rates for both MQTT gateway and React app
  - Add timing and confidence measurement for detection events
  - _Requirements: 4.1, 4.2_

- [ ] 5.2 Implement LiveKit VAD performance validation
  - Test LiveKit voice activity detection with processed ESP32 audio
  - Validate detection timing and sensitivity match React app behavior
  - Add diagnostic logging for failed detection cases
  - _Requirements: 4.1, 4.3, 4.4_

- [ ] 5.3 Add regression testing and monitoring
  - Implement continuous testing to prevent voice detection regressions
  - Add automated alerts for detection rate drops below thresholds
  - Create performance monitoring dashboard for audio quality metrics
  - _Requirements: 4.4, 4.5_

- [ ]* 5.4 Create comprehensive test documentation and reports
  - Document test procedures and expected results
  - Generate automated test reports with detection statistics
  - Add troubleshooting guide for voice detection issues
  - _Requirements: 4.4, 4.5_

- [ ] 6. Deploy and validate complete solution
  - Integrate all optimizations into production MQTT gateway
  - Validate children's voice detection works reliably with real ESP32 devices
  - Monitor performance and audio quality in production environment
  - _Requirements: 1.1, 1.3, 4.1_

- [ ] 6.1 Integrate optimized audio processing pipeline
  - Combine WebRTC processing, pipeline optimization, and LiveKit integration
  - Add configuration options for different processing modes
  - Ensure backward compatibility with existing ESP32 devices
  - _Requirements: 1.1, 1.2, 1.3_

- [ ] 6.2 Deploy with gradual rollout and monitoring
  - Deploy optimized MQTT gateway with feature flags for gradual rollout
  - Monitor voice detection success rates and audio quality metrics
  - Add rollback capability if issues are detected
  - _Requirements: 1.3, 4.1, 4.5_

- [ ] 6.3 Validate with real ESP32 devices and children's voices
  - Test complete solution with actual ESP32 hardware and children users
  - Validate voice detection parity with React app in real-world conditions
  - Document any remaining issues and create improvement plan
  - _Requirements: 1.1, 1.3, 4.1_

- [ ]* 6.4 Create production monitoring and maintenance procedures
  - Set up automated monitoring for voice detection performance
  - Create maintenance procedures for audio quality optimization
  - Document troubleshooting procedures for voice detection issues
  - _Requirements: 4.4, 4.5_