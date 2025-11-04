# Requirements Document

## Introduction

This specification addresses the critical issue where LiveKit's voice activity detection (VAD) and speech recognition systems fail to detect children's voices when audio is transmitted through the MQTT gateway from ESP32 devices, while the same children's voices are successfully detected when using a React app direct connection to LiveKit. The problem indicates that the MQTT gateway's audio processing pipeline is degrading audio quality in ways that specifically impact LiveKit's ability to recognize higher-pitched voices.

## Glossary

- **MQTT_Gateway**: The Node.js application that processes ESP32 audio before sending to LiveKit
- **ESP32_Device**: Hardware device capturing and transmitting audio via Opus encoding
- **LiveKit_VAD**: LiveKit's voice activity detection system that determines when speech is present
- **LiveKit_Room**: The LiveKit room where audio detection and processing occurs
- **React_App**: Direct browser-based connection to LiveKit that successfully detects children's voices
- **Audio_Quality_Degradation**: Loss of audio characteristics that impair LiveKit's voice detection algorithms
- **Voice_Detection_Failure**: When LiveKit fails to recognize speech input from children
- **Audio_Pipeline_Processing**: The series of audio transformations in the MQTT gateway before reaching LiveKit

## Requirements

### Requirement 1

**User Story:** As a parent using the ESP32 device, I want my child's voice to be detected by LiveKit with the same reliability as when using a React app, so that the child can interact with the voice assistant effectively.

#### Acceptance Criteria

1. WHEN a child speaks through ESP32 via MQTT gateway, THE LiveKit_Room SHALL detect voice activity with the same sensitivity as React app connections
2. WHEN MQTT gateway processes children's audio, THE MQTT_Gateway SHALL preserve audio characteristics that LiveKit_VAD requires for detection
3. WHEN comparing detection rates, THE MQTT_Gateway SHALL achieve equivalent LiveKit voice detection success for children's voices as React_App
4. WHERE audio reaches LiveKit through MQTT gateway, THE LiveKit_Room SHALL recognize speech patterns from children aged 3-12 years
5. IF LiveKit fails to detect children's voices via MQTT gateway, THEN THE MQTT_Gateway SHALL provide diagnostic audio samples for comparison

### Requirement 2

**User Story:** As a developer, I want to identify what specific audio processing differences cause LiveKit to fail detecting children's voices through MQTT gateway, so that I can fix the root cause.

#### Acceptance Criteria

1. WHEN comparing React app vs MQTT gateway audio reaching LiveKit, THE MQTT_Gateway SHALL identify specific audio parameter differences
2. WHEN MQTT gateway processes audio, THE MQTT_Gateway SHALL measure and log audio quality metrics that affect LiveKit_VAD sensitivity
3. WHEN LiveKit receives audio from MQTT gateway, THE LiveKit_Room SHALL receive audio with identical sample rate, bit depth, and frequency response as React_App
4. WHERE audio processing introduces artifacts, THE MQTT_Gateway SHALL detect and eliminate processing steps that degrade voice detection
5. IF audio quality differs between sources, THEN THE MQTT_Gateway SHALL provide side-by-side audio analysis showing the differences

### Requirement 3

**User Story:** As a system integrator, I want the MQTT gateway to send audio to LiveKit in the exact same format and quality as the React app, so that LiveKit's voice detection works consistently.

#### Acceptance Criteria

1. WHEN React app sends audio to LiveKit, THE MQTT_Gateway SHALL replicate the exact audio format, encoding parameters, and transmission method
2. WHEN MQTT gateway processes ESP32 audio, THE MQTT_Gateway SHALL avoid any processing that the React_App does not perform
3. WHEN sending audio to LiveKit_Room, THE MQTT_Gateway SHALL use identical LiveKit SDK methods and parameters as React_App
4. WHERE audio format conversion is necessary, THE MQTT_Gateway SHALL use the same audio processing libraries and settings as React_App
5. IF MQTT gateway cannot match React app audio quality, THEN THE MQTT_Gateway SHALL implement a bypass mode that sends raw audio directly

### Requirement 4

**User Story:** As a quality assurance engineer, I want automated testing to verify that LiveKit detects children's voices equally well through both MQTT gateway and React app connections, so that regressions can be prevented.

#### Acceptance Criteria

1. WHEN test audio samples of children's voices are played, THE LiveKit_Room SHALL detect voice activity with equal success rates from both MQTT_Gateway and React_App sources
2. WHEN running automated voice detection tests, THE MQTT_Gateway SHALL achieve 95% or higher detection parity with React_App for children aged 3-12
3. WHEN LiveKit_VAD processes audio from MQTT gateway, THE LiveKit_Room SHALL trigger voice detection events with the same timing and sensitivity as React_App
4. WHERE voice detection fails through MQTT gateway but succeeds through React app, THE MQTT_Gateway SHALL log detailed audio characteristics for analysis
5. IF detection rates fall below parity thresholds, THEN THE MQTT_Gateway SHALL automatically alert administrators and provide diagnostic information