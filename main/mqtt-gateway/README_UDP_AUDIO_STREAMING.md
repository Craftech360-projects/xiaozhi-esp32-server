# UDP Audio Streaming Documentation

This document describes how audio is streamed via UDP in the MQTT Gateway, including format specifications, packet structure, encryption, and the streaming pipeline.

## Table of Contents
- [Audio Format & Specifications](#audio-format--specifications)
- [UDP Packet Structure](#udp-packet-structure)
- [Encryption](#encryption)
- [Streaming Process](#streaming-process)
- [Key Characteristics](#key-characteristics)
- [Code References](#code-references)

---

## Audio Format & Specifications

### Outgoing Audio (LiveKit → ESP32)

| Parameter | Value |
|-----------|-------|
| **Format** | Opus-encoded audio |
| **Sample Rate** | 24 kHz |
| **Channels** | Mono (1 channel) |
| **Frame Duration** | 60ms |
| **Frame Size** | 1440 samples per frame |
| **PCM Frame Size** | 2880 bytes (1440 samples × 2 bytes/sample) |
| **Sample Format** | 16-bit signed PCM (Int16) |
| **Resampling** | 48 kHz (LiveKit) → 24 kHz (ESP32) |
| **Resampler Quality** | QUICK |

**Code Location**: `app.js:66-74, 141-147`

### Incoming Audio (ESP32 → LiveKit)

| Parameter | Value |
|-----------|-------|
| **Format** | Opus-encoded (fallback to PCM) |
| **Sample Rate** | 16 kHz |
| **Channels** | Mono (1 channel) |
| **Frame Duration** | 60ms |
| **Decode Frame Size** | 960 samples per frame |
| **Sample Format** | 16-bit signed PCM (Int16) |

**Code Location**: `app.js:649-704`

---

## UDP Packet Structure

### Header Format (16 bytes)

```
┌─────────────┬──────────┬────────────────────────────────────┐
│ Byte Offset │   Size   │           Description              │
├─────────────┼──────────┼────────────────────────────────────┤
│      0      │  1 byte  │  packet_type (0x01 for audio)     │
│      1      │  1 byte  │  flags (0x00)                     │
│     2-3     │  2 bytes │  payload_len (uint16 BE)          │
│     4-7     │  4 bytes │  connection_id (uint32 BE)        │
│     8-11    │  4 bytes │  timestamp (uint32 BE, ms)        │
│    12-15    │  4 bytes │  sequence (uint32 BE)             │
└─────────────┴──────────┴────────────────────────────────────┘
```

**Notes**:
- `timestamp`: Milliseconds since session start (wraps at 32-bit max)
- `sequence`: Incrementing packet counter starting from 0
- All multi-byte values use Big Endian byte order

**Code Location**: `app.js:1983-1992`

### Complete UDP Packet Structure

```
┌────────────────────┬──────────────────────────────┐
│   16-byte header   │  Encrypted audio payload     │
└────────────────────┴──────────────────────────────┘
```

Total packet size varies based on Opus compression:
- Typical size: ~116-216 bytes (16-byte header + 100-200 byte Opus payload)

---

## Encryption

### Algorithm Details

| Parameter | Value |
|-----------|-------|
| **Algorithm** | AES-128-CTR |
| **Key Size** | 128 bits (16 bytes) |
| **Key Generation** | Random bytes generated on hello handshake |
| **IV/Nonce** | UDP header (16 bytes) - reused as initialization vector |
| **Encrypted Data** | Opus-encoded audio payload only (header is plaintext) |

**Code Location**: `app.js:1965-1980, 1999`

### Encryption Process

```javascript
// Generate random 16-byte key during session initialization
const key = crypto.randomBytes(16);

// Use the UDP header itself as the IV/nonce (16 bytes)
const cipher = crypto.createCipheriv(
  "aes-128-ctr",  // AES-128 in CTR mode
  key,             // 16-byte encryption key
  header           // 16-byte header used as IV
);

// Encrypt the audio payload
const encryptedPayload = Buffer.concat([
  cipher.update(payload),
  cipher.final()
]);

// Final packet: plaintext header + encrypted payload
const packet = Buffer.concat([header, encryptedPayload]);
```

**Security Notes**:
- Each packet has a unique IV (header changes with each timestamp/sequence)
- Key is transmitted during initial handshake over MQTT
- Connection ID ensures packets are routed to correct session

---

## Streaming Process

### Outgoing Flow (LiveKit → ESP32)

```
┌──────────────┐
│   LiveKit    │ 48 kHz AudioFrame objects
└──────┬───────┘
       │
       ↓
┌──────────────────┐
│ Audio Resampler  │ 48 kHz → 24 kHz (QUICK quality)
└──────┬───────────┘
       │
       ↓
┌──────────────────┐
│ Frame Buffer     │ Accumulate until 2880 bytes (60ms @ 24kHz)
└──────┬───────────┘
       │
       ↓
┌──────────────────┐
│ Opus Encoder     │ PCM (2880 bytes) → Opus (~100-200 bytes)
└──────┬───────────┘
       │
       ↓
┌──────────────────┐
│ AES-128-CTR      │ Encrypt Opus payload
└──────┬───────────┘
       │
       ↓
┌──────────────────┐
│ UDP Transmission │ Send [header + encrypted payload]
└──────────────────┘
```

**Detailed Steps**:

1. **Receive from LiveKit** (`app.js:506-527`)
   - Audio arrives at 48 kHz from LiveKit participants
   - Received as AudioFrame objects

2. **Resample** (`app.js:141-142, 508`)
   - AudioResampler converts 48 kHz → 24 kHz
   - Uses QUICK quality for low latency

3. **Buffer Accumulation** (`app.js:144-147, 519`)
   - Resampled frames buffered until reaching 2880 bytes
   - Ensures consistent 60ms frame duration

4. **Encode to Opus** (`app.js:217-227`)
   - 2880 bytes PCM (1440 samples × 2 bytes) encoded to Opus
   - Typical output: 100-200 bytes per frame

5. **Encrypt & Send** (`app.js:1942-1981`)
   - Generate 16-byte header with timestamp & sequence
   - Encrypt Opus payload using AES-128-CTR
   - Concatenate header + encrypted payload
   - Transmit via UDP socket

### Incoming Flow (ESP32 → LiveKit)

```
┌──────────────────┐
│ UDP Socket       │ Receive encrypted packet
└──────┬───────────┘
       │
       ↓
┌──────────────────┐
│ Parse Header     │ Extract metadata (timestamp, sequence, etc.)
└──────┬───────────┘
       │
       ↓
┌──────────────────┐
│ AES-128-CTR      │ Decrypt payload
└──────┬───────────┘
       │
       ↓
┌──────────────────┐
│ Format Detection │ Detect Opus vs PCM
└──────┬───────────┘
       │
       ↓
┌──────────────────┐
│ Opus Decoder     │ Opus → PCM @ 16 kHz (if Opus detected)
└──────┬───────────┘
       │
       ↓
┌──────────────────┐
│ AudioFrame       │ Create frame (16 kHz, mono)
└──────┬───────────┘
       │
       ↓
┌──────────────────┐
│ LiveKit Room     │ audioSource.captureFrame()
└──────────────────┘
```

**Detailed Steps**:

1. **Receive UDP Packet** (`app.js:2123-2177`)
   - UDP server receives packet
   - Parse 16-byte header
   - Extract connection_id, timestamp, sequence

2. **Decrypt** (`app.js:2154-2161`)
   - Use header as IV/nonce
   - Decrypt payload using AES-128-CTR
   - Verify packet is not out of order

3. **Format Detection** (`app.js:658-663`)
   - Analyze payload to determine if Opus or PCM
   - Check for Opus magic bytes and structure

4. **Decode** (`app.js:664-699`)
   - **If Opus**: Decode to 16 kHz PCM (960 samples expected)
   - **If PCM**: Use directly without decoding

5. **Send to LiveKit** (`app.js:721`)
   - Convert to AudioFrame (16 kHz, mono, Int16 samples)
   - Call `audioSource.captureFrame()` to inject into LiveKit room

---

## Key Characteristics

### Timing & Sequencing

- **Real-time streaming**: 60ms frames sent continuously
- **Frame rate**: ~16.67 frames per second (1000ms / 60ms)
- **Sequence numbers**: Increment by 1 for each packet
- **Timestamps**: Relative to session start time (milliseconds)
- **Out-of-order rejection**: Packets with `sequence < expected` are dropped

**Code Location**: `app.js:2139-2146`

### Quality Controls

- **Silent frame detection**: Frames with max amplitude < 10 are skipped
  - Saves bandwidth by not sending silence
  - **Location**: `app.js:196-210`

- **Opus encoder fallback**: Falls back to raw PCM if Opus unavailable
  - **Location**: `app.js:233-237`

### Library Support

The system supports multiple Opus libraries with automatic fallback:

1. **Primary**: `audify-plus` (preferred)
2. **Fallback**: `@discordjs/opus`
3. **Final fallback**: Raw PCM mode (no compression)

**Code Location**: `app.js:28-60`

### Session Management

- **Session ID**: Generated during hello handshake
- **Start time**: Recorded when UDP session begins
- **Encryption key**: Generated per session (16 random bytes)
- **Connection tracking**: Each device has unique connection_id

**Code Location**: `app.js:1995-2002, 2048`

---

## Code References

### Key Functions

| Function | Location | Purpose |
|----------|----------|---------|
| `processBufferedFrames()` | `app.js:179-240` | Process audio buffer, encode to Opus, send via UDP |
| `sendUdpMessage()` | `app.js:1942-1981` | Encrypt and send UDP packet |
| `generateUdpHeader()` | `app.js:1983-1992` | Create 16-byte UDP header |
| `sendAudio()` | `app.js:649-704` | Receive incoming audio, decode, forward to LiveKit |
| `onUdpMessage()` | `app.js:2123-2178` | Handle incoming UDP packets (decrypt, decode) |
| `parseHelloMessage()` | `app.js:1994-2075` | Initialize UDP session with encryption keys |

### Key Constants

```javascript
// Defined at app.js:65-74
const OUTGOING_SAMPLE_RATE = 24000;      // Hz (LiveKit → ESP32)
const INCOMING_SAMPLE_RATE = 16000;      // Hz (ESP32 → LiveKit)
const CHANNELS = 1;                      // Mono
const OUTGOING_FRAME_DURATION_MS = 60;   // 60ms frames
const INCOMING_FRAME_DURATION_MS = 60;   // 60ms frames
const OUTGOING_FRAME_SIZE_SAMPLES = 1440; // 24000 * 60 / 1000
const INCOMING_FRAME_SIZE_SAMPLES = 960;  // For Opus decode
const OUTGOING_FRAME_SIZE_BYTES = 2880;   // 1440 samples * 2 bytes
const INCOMING_FRAME_SIZE_BYTES = 640;    // 320 samples * 2 bytes
```

### Architecture Components

```
┌─────────────────────────────────────────────────────────────┐
│                        MQTTGateway                          │
│  ┌───────────────┐          ┌──────────────────────────┐   │
│  │ UDP Server    │◄────────►│  MQTTConnection /        │   │
│  │ (dgram)       │          │  VirtualMQTTConnection   │   │
│  └───────────────┘          └──────────┬───────────────┘   │
│                                        │                    │
│                             ┌──────────▼───────────┐        │
│                             │   LiveKitBridge      │        │
│                             │  - AudioSource       │        │
│                             │  - AudioResampler    │        │
│                             │  - Opus Enc/Dec      │        │
│                             └──────────┬───────────┘        │
│                                        │                    │
│                             ┌──────────▼───────────┐        │
│                             │   LiveKit Room       │        │
│                             └──────────────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

---

## Troubleshooting

### Common Issues

**No audio received**:
- Check UDP port is open and accessible
- Verify encryption key matches between sender/receiver
- Confirm connection_id is correctly routed

**Choppy or garbled audio**:
- Check for packet loss (monitor sequence numbers)
- Verify sample rate matches (24kHz out, 16kHz in)
- Ensure Opus encoder/decoder are properly initialized

**High latency**:
- 60ms frame duration provides baseline latency
- Additional latency from buffering, resampling
- Check network conditions

### Debug Logging

Enable debug logs by setting environment variables or config:
```javascript
// Enable MQTT server debug logs
debug.enable("mqtt-server");
```

Key log prefixes:
- `🎵 [AUDIO FRAMES]` - Frame processing
- `📡 [UDP SEND/RECV]` - UDP transmission
- `🔐` - Encryption operations
- `✅ [OPUS]` - Opus codec operations
- `❌` - Errors

---

## Performance Considerations

- **Bandwidth**: ~100-200 bytes per 60ms frame = ~1.3-2.7 KB/s per stream
- **CPU**: Opus encoding/decoding + AES encryption
- **Latency**: Minimum ~60ms + network + processing overhead
- **Memory**: Frame buffering requires minimal memory (~3KB per connection)

---

## Future Improvements

Potential optimizations:
- Dynamic frame duration based on network conditions
- Adaptive bitrate for Opus encoding
- FEC (Forward Error Correction) for packet loss resilience
- Jitter buffer for smoother playback
- Opus DTX (Discontinuous Transmission) for silence suppression
