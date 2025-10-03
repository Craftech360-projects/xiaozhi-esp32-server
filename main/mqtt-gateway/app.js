// Description: MQTT+UDP to LiveKit bridge
// Author: terrence@tenclass.com
// Date: 2025-03-12
// Modified by: Gemini

require("dotenv").config();
const JSON5 = require("json5");

const net = require("net");
const debugModule = require("debug");
const debug = debugModule("mqtt-server");
const crypto = require("crypto");
const dgram = require("dgram");
const Emitter = require("events");
const { AccessToken } = require("livekit-server-sdk");
const {
  Room,
  RoomEvent,
  AudioSource,
  AudioFrame,
  AudioStream,
  LocalAudioTrack,
  TrackPublishOptions,
  TrackSource,
  TrackKind,
  AudioResampler,
  AudioResamplerQuality,
} = require("@livekit/rtc-node");
// Import Opus Encoder and Decoder from audify-plus
const { OpusEncoder, OpusDecoder, OpusApplication } = require("@voicehype/audify-plus");

// Initialize Opus encoder for 24kHz mono (outgoing), decoder for 16kHz mono (incoming)
let opusEncoder = null;
let opusDecoder = null;
// Define constants for audio parameters
const OUTGOING_SAMPLE_RATE = 24000;  // Hz - for LiveKit → ESP32
const INCOMING_SAMPLE_RATE = 16000;  // Hz - for ESP32 → LiveKit
const CHANNELS = 1;            // Mono
const OUTGOING_FRAME_DURATION_MS = 60;  // 60ms frames for outgoing (LiveKit → ESP32)
const INCOMING_FRAME_DURATION_MS = 60;  // 20ms frames for incoming (ESP32 → LiveKit)
const OUTGOING_FRAME_SIZE_SAMPLES = (OUTGOING_SAMPLE_RATE * OUTGOING_FRAME_DURATION_MS) / 1000; // 24000 * 60 / 1000 = 1440
const INCOMING_FRAME_SIZE_SAMPLES = (INCOMING_SAMPLE_RATE * INCOMING_FRAME_DURATION_MS) / 1000; // 16000 * 20 / 1000 = 320
const OUTGOING_FRAME_SIZE_BYTES = OUTGOING_FRAME_SIZE_SAMPLES * 2; // 1440 samples * 2 bytes/sample = 2880 bytes PCM
const INCOMING_FRAME_SIZE_BYTES = INCOMING_FRAME_SIZE_SAMPLES * 2; // 320 samples * 2 bytes/sample = 640 bytes PCM

try {
  // For outgoing: 24kHz encoder (LiveKit → ESP32), incoming: 16kHz decoder (ESP32 → LiveKit)
  opusEncoder = new OpusEncoder(24000, 1, OpusApplication.OPUS_APPLICATION_AUDIO);
  opusDecoder = new OpusDecoder(16000, 1);

  console.log(
    "✅ [OPUS] audify-plus encoder/decoder initialized successfully - encoder: 24kHz, decoder: 16kHz mono"
  );
} catch (err) {
  console.error(
    "❌ [OPUS] Failed to initialize audify-plus encoder/decoder:",
    err.message
  );
  // Fallback: Disable Opus if init fails (will fall back to PCM)
}

const mqtt = require("mqtt");
const { MQTTProtocol } = require("./mqtt-protocol");
const { ConfigManager } = require("./utils/config-manager");
const { validateMqttCredentials } = require("./utils/mqtt_config_v2");

function setDebugEnabled(enabled) {
  if (enabled) {
    debugModule.enable("mqtt-server");
  } else {
    debugModule.disable();
  }
}

const configManager = new ConfigManager("mqtt.json");
configManager.on("configChanged", (config) => {
  setDebugEnabled(false);
});
setDebugEnabled(configManager.get("debug"));

class LiveKitBridge extends Emitter {
  constructor(connection, protocolVersion, macAddress, uuid, userData) {
    super();
    this.connection = connection;
    this.macAddress = macAddress;
    this.uuid = uuid;
    this.userData = userData;
    this.room = null;
    this.audioSource = new AudioSource(16000, 1);
    this.protocolVersion = protocolVersion;
    this.isAudioPlaying = false; // Track if audio is actively playing

    // Initialize audio resampler for 48kHz -> 24kHz conversion (outgoing: LiveKit -> ESP32)
    this.audioResampler = new AudioResampler(48000, 24000, 1, AudioResamplerQuality.QUICK);

    // Frame buffer for accumulating resampled audio into proper frame sizes
    this.frameBuffer = Buffer.alloc(0);
    this.targetFrameSize = 1440; // 1440 samples = 60ms at 24kHz (outgoing)
    this.targetFrameBytes = this.targetFrameSize * 2; // 2880 bytes for 16-bit PCM

    // Initialize Opus decoder for incoming audio (device -> LiveKit)
    // this.opusDecoder = null;
    // Initialize Opus encoder for outgoing audio (LiveKit -> device)
    // this.opusEncoder = null;

    if (OpusEncoder) {
      try {
        // this.opusDecoder = new OpusEncoder(16000, 1); // 16kHz, mono
        console.log(`✅ [OPUS] Decoder initialized for ${this.macAddress}`);

        // this.opusEncoder = new OpusEncoder(16000, 1); // 16kHz, mono
        console.log(`✅ [OPUS] Encoder initialized for ${this.macAddress}`);
      } catch (err) {
        console.error(
          `❌ [OPUS] Failed to initialize encoder/decoder: ${err.message}`
        );
      }
    }

    this.initializeLiveKit();
  }

  initializeLiveKit() {
    const livekitConfig = configManager.get("livekit");
    if (!livekitConfig) {
      throw new Error("LiveKit config not found");
    }
    this.livekitConfig = livekitConfig;
  }

  // Process buffered audio frames and encode to Opus
  processBufferedFrames(timestamp, frameCount, participantIdentity) {
    while (this.frameBuffer.length >= this.targetFrameBytes) {
      // Extract one complete frame
      const frameData = this.frameBuffer.slice(0, this.targetFrameBytes);
      this.frameBuffer = this.frameBuffer.slice(this.targetFrameBytes);

      // Process this complete frame - encode to Opus before sending
      if (frameData.length > 0) {
        const samples = new Int16Array(frameData.buffer, frameData.byteOffset, frameData.length / 2);
        const isSilent = samples.every(sample => sample === 0);
        const maxAmplitude = Math.max(...samples.map(s => Math.abs(s)));
        const isNearlySilent = maxAmplitude < 10;

        if (isSilent || isNearlySilent) {
          // console.log(`🔇 [PCM] Silent frame detected, skipping`);
          continue;
        }

        if (frameCount <= 3 || frameCount % 100 === 0) {
          // Log progress every 100 frames for Opus encoding
        }

        // Encode to Opus and send to ESP32
        if (opusEncoder) {
          try {
            const alignedBuffer = Buffer.allocUnsafe(frameData.length);
            frameData.copy(alignedBuffer);
            const opusBuffer = opusEncoder.encode(alignedBuffer, this.targetFrameSize);

            if (frameCount <= 3 || frameCount % 100 === 0) {
              console.log(`🎵 [OPUS] Frame ${frameCount}: 24kHz 60ms PCM ${frameData.length}B → Opus ${opusBuffer.length}B`);
            }

            this.connection.sendUdpMessage(opusBuffer, timestamp);
          } catch (err) {
            console.error(`❌ [OPUS] Encode error: ${err.message}`);
            // Fallback to PCM if Opus encoding fails
            this.connection.sendUdpMessage(frameData, timestamp);
          }
        } else {
          // Fallback: Send PCM directly if Opus encoder not available
          console.log(`⚠️ [PCM] No Opus encoder, sending PCM directly`);
          this.connection.sendUdpMessage(frameData, timestamp);
        }
      }
    }
  }

  async connect(audio_params, features) {
    console.log(`🔍 [DEBUG] LiveKitBridge.connect() called - UUID: ${this.uuid}, MAC: ${this.macAddress}`);
    const { url, api_key, api_secret } = this.livekitConfig;
    // Include MAC address in room name for agent to extract device-specific prompt
    const macForRoom = this.macAddress.replace(/:/g, ''); // Remove colons: 00:16:3e:ac:b5:38 → 00163eacb538
    const roomName = `${this.uuid}_${macForRoom}`;
    const participantName = this.macAddress;

    console.log(`🏠 [ROOM] Creating room with name: ${roomName} (UUID: ${this.uuid}, MAC: ${this.macAddress})`);

    const at = new AccessToken(api_key, api_secret, {
      identity: participantName,
      // Add MAC address as custom attributes
      attributes: {
        device_mac: this.macAddress,
        device_uuid: this.uuid || '',
        room_type: 'device_session'
      }
    });
    at.addGrant({
      room: roomName,
      roomJoin: true,
      roomCreate: true,
      canPublish: true,
      canSubscribe: true,
    });
    const token = await at.toJwt(); // Fixed: Make this async

    this.room = new Room();

    // Add connection state monitoring
    this.room.on("connectionStateChanged", (state) => {
      console.log(`[LiveKitBridge] Connection state changed: ${state}`);
    });

    this.room.on("connected", () => {
      console.log("[LiveKitBridge] Room connected event fired");
    });

    this.room.on("disconnected", (reason) => {
      console.log(`[LiveKitBridge] Room disconnected: ${reason}`);
    });

    this.room.on(
      RoomEvent.DataReceived,
      (payload, participant, kind, topic) => {
        try {
          const str = Buffer.from(payload).toString("utf-8");
          let data;
          try {
            data = JSON5.parse(str);
            // console.log("Data:", data);
          } catch (err) {
            console.error("Invalid JSON5:", err.message);
          }
          switch (data.type) {
            case "agent_state_changed":
              // console.log(`Agent state changed: ${JSON.stringify(data.data)}`);
              if (
                data.data.old_state === "speaking" &&
                data.data.new_state === "listening"
              ) {
                // Set audio playing flag to false
                this.isAudioPlaying = false;
                console.log(`🎵 [AUDIO-STOP] TTS stopped for device: ${this.macAddress}`);
                // Send TTS stop message to device
                this.sendTtsStopMessage();
              }
              else if(
                data.data.old_state === "listening" &&
                data.data.new_state === "thinking"
              )
              {
                  this.sendLLMThinkMessage();
              }
              break;
            case "user_input_transcribed":
              // console.log(`Transcription: ${JSON.stringify(data.data)}`);
              // Send STT result back to device
              this.sendSttMessage(data.data.text || data.data.transcript);
              break;
            case "speech_created":
              // console.log(`Speech created: ${JSON.stringify(data.data)}`);
              // Set audio playing flag and reset inactivity timer
              this.isAudioPlaying = true;
              if (this.connection && this.connection.updateActivityTime) {
                this.connection.updateActivityTime();
                console.log(`🎵 [AUDIO-START] TTS started, timer reset for device: ${this.macAddress}`);
              }
              // Send TTS start message to device
              this.sendTtsStartMessage(data.data.text);
              break;
            case "device_control":
              // Convert device_control commands to MCP function calls
              console.log(`🎛️ [DEVICE CONTROL] Received action: ${data.action}`);
              this.convertDeviceControlToMcp(data);
              break;
            case "function_call":
              // Handle xiaozhi function calls (volume controls, etc.)
              console.log(`🔧 [FUNCTION CALL] Received function: ${data.function_call?.name}`);
              this.handleFunctionCall(data);
              break;
            case "music_playback_stopped":
              // Handle music playback stopped - force clear audio playing flag
              console.log(`🎵 [MUSIC-STOP] Music playback stopped for device: ${this.macAddress}`);
              this.isAudioPlaying = false;
              // Send TTS stop message to ensure device returns to listening state
              this.sendTtsStopMessage();
              break;
            // case "metrics_collected":
            //   console.log(`Metrics: ${JSON.stringify(data.data)}`);
            //   break;
            default:
            //console.log(`Unknown data type: ${data.type}`);
          }
        } catch (error) {
          console.error(`Error processing data packet: ${error}`);
        }
      }
    );

    return new Promise(async (resolve, reject) => {
      try {
        console.log(`[LiveKitBridge] Connecting to LiveKit room: ${roomName}`);
        await this.room.connect(url, token, {
          autoSubscribe: true,
          dynacast: true,
        });
        console.log(`✅ [ROOM] Connected to LiveKit room: ${roomName}`);
        console.log(`🔗 [CONNECTION] State: ${this.room.connectionState}`);
        console.log(`🟢 [STATUS] Is connected: ${this.room.isConnected}`);

        // Log existing participants in the room
        console.log(
          `👥 [PARTICIPANTS] Remote participants in room: ${this.room.remoteParticipants.size}`
        );
        this.room.remoteParticipants.forEach((participant, sid) => {
          console.log(`   - ${participant.identity} (${sid})`);

          // Log existing tracks from participants
          participant.trackPublications.forEach((pub, trackSid) => {
            console.log(
              `     📡 Track: ${trackSid}, kind: ${pub.kind}, subscribed: ${pub.isSubscribed}`
            );
          });
        });

        this.room.on(
          RoomEvent.TrackSubscribed,
          (track, publication, participant) => {
            console.log(
              `🎵 [TRACK] Subscribed to track: ${track.sid} from ${participant.identity}, kind: ${track.kind}`
            );

            // Handle audio track from agent (TTS audio)
            // Check for both string "audio" and TrackKind.KIND_AUDIO constant
            if (track.kind === "audio" || track.kind === TrackKind.KIND_AUDIO) {
              console.log(
                `🔊 [AUDIO TRACK] Starting audio stream processing for ${participant.identity}`
              );


              const stream = new AudioStream(track);
              const reader = stream.getReader();

              let frameCount = 0;
              let totalBytes = 0;
              let lastLogTime = Date.now();

              const readStream = async () => {
                try {
                  console.log(
                    `🎧 [AUDIO STREAM] Starting to read audio frames from ${participant.identity}`
                  );

                  while (true) {
                    const { done, value } = await reader.read();
                    if (done) {
                      this.sendTtsStopMessage();
                      console.log(
                        `🏁 [AUDIO STREAM] Stream ended for ${participant.identity}. Total frames: ${frameCount}, Total bytes: ${totalBytes}`
                      );

                      // Flush any remaining resampled data
                      const finalFrames = this.audioResampler.flush();
                      for (const finalFrame of finalFrames) {
                        const finalBuffer = Buffer.from(
                          finalFrame.data.buffer,
                          finalFrame.data.byteOffset,
                          finalFrame.data.byteLength
                        );
                        // Add final frames to buffer
                        this.frameBuffer = Buffer.concat([this.frameBuffer, finalBuffer]);
                      }

                      // Process any remaining complete frames in buffer
                      const finalTimestamp = (Date.now() - this.connection.udp.startTime) & 0xffffffff;
                      this.processBufferedFrames(finalTimestamp, frameCount, participant.identity);

                      // Send any remaining partial frame if it has significant data
                      if (this.frameBuffer.length > 720) { // At least 30ms worth of 24kHz audio (720 samples * 2 bytes = 1440B)
                        console.log(`🔄 [FLUSH] Processing partial 24kHz 60ms PCM frame: ${this.frameBuffer.length}B`);

                        if (opusEncoder) {
                          // Declare targetSize outside try block
                          const targetSize = this.frameBuffer.length <= 1440 ? 1440 : 2880;
                          try {
                            // Pad to nearest valid frame size for 24kHz 60ms (1440 or 2880 bytes)
                            const paddedBuffer = Buffer.alloc(targetSize);
                            this.frameBuffer.copy(paddedBuffer);

                            const opusBuffer = opusEncoder.encode(paddedBuffer, targetSize / 2);
                            this.connection.sendUdpMessage(opusBuffer, finalTimestamp);
                            console.log(`✅ [FLUSH] Encoded partial frame: ${this.frameBuffer.length}B → ${opusBuffer.length}B Opus`);
                          } catch (err) {
                            console.log(`⚠️ [FLUSH] Failed to encode partial frame: ${err.message}`);
                            console.log(`🔍 [DEBUG] Partial frame size: ${this.frameBuffer.length}B, target: ${targetSize}B`);
                            // Fallback to PCM
                            this.connection.sendUdpMessage(this.frameBuffer, finalTimestamp);
                          }
                        } else {
                          // Fallback: Send remaining PCM if no Opus encoder
                          this.connection.sendUdpMessage(this.frameBuffer, finalTimestamp);
                        }
                      }

                      // Clear the buffer
                      this.frameBuffer = Buffer.alloc(0);

                      // Notify connection that audio stream has ended
                      if (this.connection && this.connection.isEnding) {
                        console.log(`✅ [END-COMPLETE] Audio stream completed, closing connection: ${this.connection.clientId || this.connection.deviceId}`);
                        // Use setTimeout to allow TTS stop message to be sent first
                        setTimeout(() => {
                          if (this.connection && this.connection.isEnding) {
                            this.connection.close();
                          }
                        }, 1000); // 1 second delay to ensure TTS stop is processed
                      }

                      break;
                    }

                    frameCount++;

                    // value is an AudioFrame from LiveKit (48kHz)
                    // Push the frame to resampler and get resampled frames back (16kHz)
                    const resampledFrames = this.audioResampler.push(value);

                    // Add resampled frames to buffer instead of processing directly
                    for (const resampledFrame of resampledFrames) {
                      const resampledBuffer = Buffer.from(
                        resampledFrame.data.buffer,
                        resampledFrame.data.byteOffset,
                        resampledFrame.data.byteLength
                      );

                      // Append to frame buffer
                      this.frameBuffer = Buffer.concat([this.frameBuffer, resampledBuffer]);
                      totalBytes += resampledBuffer.length;
                    }

                    const timestamp = (Date.now() - this.connection.udp.startTime) & 0xffffffff;

                    // Process any complete frames from the buffer
                    this.processBufferedFrames(timestamp, frameCount, participant.identity);

                    // Log every 50 frames or every 5 seconds
                    const now = Date.now();
                    if (frameCount % 50 === 0 || now - lastLogTime > 5000) {
                      // console.log(
                      //   `🎵 [AUDIO FRAMES] Received ${frameCount} frames, ${totalBytes} total bytes from ${participant.identity}`
                      // );
                      lastLogTime = now;
                    }

                  }
                } catch (error) {
                  console.error(
                    `❌ [AUDIO STREAM] Error reading audio stream from ${participant.identity}:`,
                    error
                  );
                } finally {
                  console.log(
                    `🔒 [AUDIO STREAM] Releasing reader lock for ${participant.identity}`
                  );
                  reader.releaseLock();
                }
              };

              readStream();
            } else {
              console.log(
                `⚠️ [TRACK] Non-audio track subscribed: ${track.kind} (type: ${typeof track.kind}) from ${participant.identity}`
              );
            }
          }
        );

        // Add track unsubscription handler
        this.room.on(
          RoomEvent.TrackUnsubscribed,
          (track, publication, participant) => {
            console.log(
              `🔇 [TRACK] Unsubscribed from track: ${track.sid} from ${participant.identity}, kind: ${track.kind}`
            );
          }
        );

        // Add participant connection handlers
        this.room.on(RoomEvent.ParticipantConnected, (participant) => {
          console.log(
            `👤 [PARTICIPANT] Connected: ${participant.identity} (${participant.sid})`
          );

          // Check if this is an agent joining (agent identity typically contains "agent")
          if (participant.identity.includes('agent')) {
            console.log(`🤖 [AGENT] Agent joined the room: ${participant.identity}`);

            // Send initial greeting message to let user know agent is ready
            setTimeout(() => {
              this.sendInitialGreeting();
            }, 1000); // Small delay to ensure connection is stable
          }
        });

        this.room.on(RoomEvent.ParticipantDisconnected, (participant) => {
          console.log(
            `👤 [PARTICIPANT] Disconnected: ${participant.identity} (${participant.sid})`
          );
        });

        // Fixed: Use proper track publishing method
        const {
          LocalAudioTrack,
          TrackPublishOptions,
          TrackSource,
        } = require("@livekit/rtc-node");
        const track = LocalAudioTrack.createAudioTrack(
          "microphone",
          this.audioSource
        );
        const options = new TrackPublishOptions();
        options.source = TrackSource.SOURCE_MICROPHONE;

        const publication = await this.room.localParticipant.publishTrack(
          track,
          options
        );
        console.log(
          `🎤 [PUBLISH] Published local audio track: ${publication.trackSid}`
        );

        // Use roomName as session_id - this is consistent with how LiveKit rooms work
        // The room.sid might not be immediately available, but roomName is our session identifier
        // Include audio_params that the client expects
        resolve({
          session_id: roomName,
          audio_params: {
            sample_rate: 24000,
            channels: 1,
            frame_duration: 60,
            format: "opus"
          }
        });
      } catch (error) {
        console.error("[LiveKitBridge] Error connecting to LiveKit:", error);
        console.error("[LiveKitBridge] Error name:", error.name);
        console.error("[LiveKitBridge] Error message:", error.message);
        reject(error);
      }
    });
  }

  sendAudio(opusData, timestamp) {
    // Check if audioSource is available and room is connected
    if (!this.audioSource || !this.room || !this.room.isConnected) {
      console.warn(`⚠️ [AUDIO] Cannot send audio - audioSource or room not ready. Room connected: ${this.room?.isConnected}`);
      return;
    }

    try {
      // Audio format analysis (only log occasionally to reduce spam)
      if (Math.random() < 0.01) {
        // Log 1% of packets
        // this.analyzeAudioFormat(opusData, timestamp);
      }

      // Check if data is Opus and decode it
      const isOpus = this.checkOpusFormat(opusData);



     // console.log(`🔍 [AUDIO] Detected format for incoming data: ${isOpus ? "Opus" : "PCM or Unknown"}`);
      if (isOpus) {
        if (opusDecoder) {
          try {
            // console.log(
            //   `🎵 [OPUS DECODE] Decoding ${opusData.length}B Opus data to PCM`
            // );

            // Decode Opus to PCM
            const pcmBuffer = opusDecoder.decode(opusData, 960);
           // console.log(`✅ [OPUS DECODE] Decoded to ${pcmBuffer.length}B PCM`);
            if (pcmBuffer && pcmBuffer.length > 0) {
              // Convert Buffer to Int16Array
              const samples = new Int16Array(
                pcmBuffer.buffer,
                pcmBuffer.byteOffset,
                pcmBuffer.length / 2
              );
              const frame = new AudioFrame(samples, 16000, 1, samples.length);

              // console.log(
              //   `📤 [UDP IN] Opus->PCM->LiveKit: ${opusData.length}B opus -> ${pcmBuffer.length}B pcm -> ${samples.length} samples, ts=${timestamp}, mac=${this.macAddress}`
              // );
              
              // Safe capture with error handling
              this.safeCaptureFrame(frame);
            } else {
              // console.warn(
              //   `⚠️  [OPUS] Decoder returned empty buffer for ${opusData.length}B input`
              // );
            }
          } catch (err) {
            console.error(`❌ [OPUS] Decode error: ${err.message}`);
            console.log(
              `� [RDEBUG] Opus data: ${opusData.slice(0, 8).toString("hex")}...`
            );
          }
        } else {
          console.error(
            `❌ [ERROR] Opus decoder not available! Install with: npm install @discordjs/opus`
          );
          console.log(
            `💡 [WORKAROUND] Treating Opus as PCM (will sound garbled)`
          );

          // Fallback: treat as PCM (will sound bad but won't crash)
          const samples = new Int16Array(
            opusData.buffer,
            opusData.byteOffset,
            Math.min(opusData.length / 2, 320)
          ); // Limit to reasonable PCM size
          const frame = new AudioFrame(samples, 16000, 1, samples.length);
          
          // Safe capture with error handling
          this.safeCaptureFrame(frame);
        }
      } else {
        // Treat as PCM
        console.log(`🎤 [PCM] Processing ${opusData.length}B as raw PCM`);
        const samples = new Int16Array(
          opusData.buffer,
          opusData.byteOffset,
          opusData.length / 2
        );
        const frame = new AudioFrame(samples, 16000, 1, samples.length);
        console.log(
          `📤 [UDP IN] Device->LiveKit: ${opusData.length}B, samples=${samples.length}, ts=${timestamp}, mac=${this.macAddress}`
        );
        
        // Safe capture with error handling
        this.safeCaptureFrame(frame);
      }
    } catch (error) {
      console.error(`❌ [AUDIO] Error in sendAudio: ${error.message}`);
    }
  }

  safeCaptureFrame(frame) {
    try {
      // Validate frame before capture
      if (!frame || !frame.data || frame.data.length === 0) {
        console.warn(`⚠️ [AUDIO] Invalid frame data, skipping`);
        return;
      }

      // Check if audioSource is still valid
      if (!this.audioSource) {
        console.warn(`⚠️ [AUDIO] AudioSource is null, cannot capture frame`);
        return;
      }

      // Attempt to capture the frame
      this.audioSource.captureFrame(frame);
    } catch (error) {
      console.error(`❌ [AUDIO] Failed to capture frame: ${error.message}`);
      
      // If we get InvalidState error, try to reinitialize the audio source
      if (error.message.includes('InvalidState')) {
        console.log(`🔄 [AUDIO] Attempting to reinitialize AudioSource due to InvalidState`);
        try {
          this.audioSource = new AudioSource(16000, 1);
          console.log(`✅ [AUDIO] AudioSource reinitialized successfully`);
        } catch (reinitError) {
          console.error(`❌ [AUDIO] Failed to reinitialize AudioSource: ${reinitError.message}`);
        }
      }
    }
  }

  analyzeAudioFormat(audioData, timestamp) {
    // Check for Opus magic signature
    const isOpus = this.checkOpusFormat(audioData);
    const isPCM = this.checkPCMFormat(audioData);

    console.log(`🔍 [AUDIO ANALYSIS] Format Detection:`);
    console.log(`   📊 Size: ${audioData.length} bytes`);
    console.log(`   🎵 Timestamp: ${timestamp}`);
    console.log(
      `   📋 First 16 bytes: ${audioData.slice(0, Math.min(16, audioData.length)).toString("hex")}`
    );
    console.log(
      `   🎼 Opus signature: ${isOpus ? "✅ DETECTED" : "❌ NOT FOUND"}`
    );
    console.log(
      `   🎤 PCM characteristics: ${isPCM ? "✅ LIKELY PCM" : "❌ UNLIKELY PCM"}`
    );

    // Additional analysis
    this.analyzeAudioStatistics(audioData);
  }


  checkOpusFormat(data) {
      if (data.length < 1) return false;

      // ESP32 sends 60ms OPUS frames at 16kHz mono with complexity=0
      const MIN_OPUS_SIZE = 1;    // Minimum OPUS packet (can be very small for silence)
      const MAX_OPUS_SIZE = 400;  // Maximum OPUS packet for 60ms@16kHz

      // Validate packet size range
      if (data.length < MIN_OPUS_SIZE || data.length > MAX_OPUS_SIZE) {
          console.log(`❌ Invalid OPUS size: ${data.length}B (expected ${MIN_OPUS_SIZE}-${MAX_OPUS_SIZE}B)`);
          return false;
      }

      // Check OPUS TOC (Table of Contents) byte
      const firstByte = data[0];
      const config = (firstByte >> 3) & 0x1f;        // Bits 7-3: config (0-31)
      const stereo = (firstByte >> 2) & 0x01;        // Bit 2: stereo flag
      const frameCount = firstByte & 0x03;           // Bits 1-0: frame count

     // console.log(`🔍 OPUS TOC: config=${config}, stereo=${stereo}, frames=${frameCount}, size=${data.length}B`);

      // Validate OPUS TOC byte
      const validConfig = config >= 0 && config <= 31;
      const validStereo = stereo === 0;  // ESP32 sends mono (stereo=0)
      const validFrameCount = frameCount >= 0 && frameCount <= 3;

      // ✅ FIXED: Accept ALL valid OPUS configs (0-31) for ESP32 with complexity=0
      // ESP32 with complexity=0 can use various configs depending on audio content
      const validOpusConfigs = [
        0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15,  // NB/MB/WB configs
        16, 17, 18, 19,                                          // SWB configs
        20, 21, 22, 23,                                          // FB configs
        24, 25, 26, 27, 28, 29, 30, 31                          // Hybrid configs
      ];
      const isValidConfig = validOpusConfigs.includes(config);

      // ✅ FIXED: More lenient validation - just check basic OPUS structure
      const isValidOpus = validConfig && validStereo && validFrameCount && isValidConfig;

     // console.log(`📊 OPUS validation: config=${validConfig}(${config}), mono=${validStereo}, frames=${validFrameCount}, validConfig=${isValidConfig} → ${isValidOpus ? "✅ VALID" : "❌ INVALID"}`);

      // ✅ ADDITIONAL: Log first few bytes for debugging
      if (!isValidOpus) {
        const hexDump = data.slice(0, Math.min(8, data.length)).toString('hex');
      //  console.log(`🔍 OPUS debug - first ${Math.min(8, data.length)} bytes: ${hexDump}`);
      }

      return isValidOpus;
  }


  checkOpusMarkers(data) {
    // Look for common Opus packet patterns
    if (data.length < 4) return false;

    // Check for Opus frame size patterns (common sizes: 120, 240, 480, 960, 1920, 2880 samples)
    // At 16kHz: 120 samples = 7.5ms, 240 = 15ms, 480 = 30ms, etc.
    const commonOpusSizes = [20, 40, 60, 80, 120, 160, 240, 320, 480, 640, 960];
    const isCommonOpusSize = commonOpusSizes.includes(data.length);

    // console.log(
    //   `   📏 Common Opus size (${data.length}B): ${isCommonOpusSize ? "✅" : "❌"}`
    // );

    return isCommonOpusSize;
  }

  checkPCMFormat(data) {
    if (data.length < 32) return false;

    // PCM characteristics analysis
    const samples = new Int16Array(
      data.buffer,
      data.byteOffset,
      Math.min(data.length / 2, 16)
    );

    // Calculate basic statistics
    let sum = 0;
    let maxAbs = 0;
    let zeroCount = 0;

    for (let i = 0; i < samples.length; i++) {
      const sample = samples[i];
      sum += Math.abs(sample);
      maxAbs = Math.max(maxAbs, Math.abs(sample));
      if (sample === 0) zeroCount++;
    }

    const avgAmplitude = sum / samples.length;
    const zeroRatio = zeroCount / samples.length;

    console.log(`   📈 PCM Statistics:`);
    console.log(`      🔊 Avg amplitude: ${avgAmplitude.toFixed(1)}`);
    console.log(`      📊 Max amplitude: ${maxAbs}`);
    console.log(`      🔇 Zero ratio: ${(zeroRatio * 100).toFixed(1)}%`);
    console.log(`      📐 Sample count: ${samples.length}`);

    // PCM heuristics
    const hasReasonableAmplitude = avgAmplitude > 10 && avgAmplitude < 10000;
    const hasVariation = maxAbs > 100;
    const notTooManyZeros = zeroRatio < 0.8;
    const reasonableSize = data.length >= 160 && data.length <= 3840; // 10ms to 240ms at 16kHz

    console.log(`   ✅ PCM Checks:`);
    console.log(
      `      🔊 Reasonable amplitude: ${hasReasonableAmplitude ? "✅" : "❌"}`
    );
    console.log(`      📊 Has variation: ${hasVariation ? "✅" : "❌"}`);
    console.log(
      `      🔇 Not too many zeros: ${notTooManyZeros ? "✅" : "❌"}`
    );
    console.log(`      📏 Reasonable size: ${reasonableSize ? "✅" : "❌"}`);

    return (
      hasReasonableAmplitude &&
      hasVariation &&
      notTooManyZeros &&
      reasonableSize
    );
  }

  analyzeAudioStatistics(data) {
    // Frame size analysis for common audio formats
    const frameSizeAnalysis = this.analyzeFrameSize(data.length);
    console.log(`   ⏱️  Frame Analysis: ${frameSizeAnalysis}`);

    // Entropy analysis (compressed data has higher entropy)
    const entropy = this.calculateEntropy(data);
    console.log(
      `   🎲 Data entropy: ${entropy.toFixed(3)} (PCM: ~7-11, Opus: ~7.5-8)`
    );
  }

  analyzeFrameSize(size) {
    // Common frame sizes for different formats at 16kHz
    const formats = {
      "PCM 10ms": 320, // 160 samples * 2 bytes
      "PCM 20ms": 640, // 320 samples * 2 bytes
      "PCM 30ms": 960, // 480 samples * 2 bytes
      "PCM 60ms": 1920, // 960 samples * 2 bytes
      "Opus 20ms": 40, // Typical Opus frame
      "Opus 40ms": 80, // Typical Opus frame
      "Opus 60ms": 120, // Typical Opus frame
    };

    for (const [format, expectedSize] of Object.entries(formats)) {
      if (size === expectedSize) {
        return `${format} (exact match)`;
      }
    }

    // Check for close matches
    for (const [format, expectedSize] of Object.entries(formats)) {
      if (Math.abs(size - expectedSize) <= 10) {
        return `${format} (close match, diff: ${size - expectedSize})`;
      }
    }

    return `Unknown format (${size}B)`;
  }

  calculateEntropy(data) {
    const freq = new Array(256).fill(0);

    // Count byte frequencies
    for (let i = 0; i < data.length; i++) {
      freq[data[i]]++;
    }

    // Calculate entropy
    let entropy = 0;
    for (let i = 0; i < 256; i++) {
      if (freq[i] > 0) {
        const p = freq[i] / data.length;
        entropy -= p * Math.log2(p);
      }
    }

    return entropy;
  }

  isAlive() {
    return this.room && this.room.isConnected;
  }

  // Send TTS start message to device
  sendTtsStartMessage(text = "") {
    if (!this.connection) return;

    const message = {
      type: "tts",
      state: "start",
      session_id: this.connection.udp.session_id,
    };

    if (text) {
      message.text = text;
    }

    // console.log(
    //   `📤 [MQTT OUT] Sending TTS start to device: ${this.macAddress}`
    // );
    this.connection.sendMqttMessage(JSON.stringify(message));
  }

  // Send TTS sentence start message to device
  sendTtsSentenceStartMessage(text) {
    if (!this.connection) return;

    const message = {
      type: "tts",
      state: "sentence_start",
      session_id: this.connection.udp.session_id,
      text: text || "",
    };

    console.log(
      `📤 [MQTT OUT] Sending TTS sentence start to device: ${this.macAddress} - "${text}"`
    );
    this.connection.sendMqttMessage(JSON.stringify(message));
  }

  // Send TTS stop message to device
  sendTtsStopMessage() {
    if (!this.connection) return;

    const message = {
      type: "tts",
      state: "stop",
      session_id: this.connection.udp.session_id,
    };

    console.log(`📤 [MQTT OUT] Sending TTS stop to device: ${this.macAddress}`);
    this.connection.sendMqttMessage(JSON.stringify(message));
  }


  sendLLMThinkMessage(){
     if (!this.connection) return;
    console.log("Sending LLM think message");
    const message = {
      type: "llm",
      state: "think",
      session_id: this.connection.udp.session_id,
    };

    console.log(`📤 [MQTT OUT] Sending TTS stop to device: ${this.macAddress}`);
    this.connection.sendMqttMessage(JSON.stringify(message));
  }

  // Send STT (Speech-to-Text) result to device
  sendSttMessage(text) {
    if (!this.connection || !text) return;

    const message = {
      type: "stt",
      text: text,
      session_id: this.connection.udp.session_id,
    };

    console.log(
      `📤 [MQTT OUT] Sending STT result to device: ${this.macAddress} - "${text}"`
    );
    this.connection.sendMqttMessage(JSON.stringify(message));
  }

  // Convert device_control commands to MCP function calls
  convertDeviceControlToMcp(controlData) {
    if (!this.connection) return;

    const action = controlData.action || controlData.command;

    // Map device control actions to xiaozhi function names
    const actionToFunctionMap = {
      'set_volume': 'self_set_volume',
      'volume_up': 'self_volume_up',
      'volume_down': 'self_volume_down',
      'get_volume': 'self_get_volume',
      'mute': 'self_mute',
      'unmute': 'self_unmute',
      'set_light_color': 'self_set_light_color',
      'get_battery_status': 'self_get_battery_status',
      'set_light_mode': 'self_set_light_mode',
      'set_rainbow_speed': 'self_set_rainbow_speed'
    };

    const functionName = actionToFunctionMap[action];
    if (!functionName) {
      console.error(`❌ [DEVICE CONTROL] Unknown action: ${action}`);
      return;
    }

    // Prepare function arguments based on action type
    let functionArguments = {};
    if (action === "set_volume") {
      functionArguments.volume = controlData.volume || controlData.value;
    } else if (action === "volume_up" || action === "volume_down") {
      functionArguments.step = controlData.step || controlData.value || 10;
    }

    // Create function call data in the same format as handleFunctionCall expects
    const functionCallData = {
      function_call: {
        name: functionName,
        arguments: functionArguments
      },
      timestamp: controlData.timestamp || new Date().toISOString(),
      request_id: controlData.request_id || `req_${Date.now()}`
    };

    console.log(
      `🔄 [DEVICE CONTROL] Converting to MCP: ${action} -> ${functionName}, Args: ${JSON.stringify(functionArguments)}`
    );

    // Use existing handleFunctionCall method to send as MCP format
    this.handleFunctionCall(functionCallData);
  }

  // Handle xiaozhi function calls (volume controls, etc.)
  handleFunctionCall(functionData) {
    if (!this.connection) return;

    const functionCall = functionData.function_call;
    if (!functionCall || !functionCall.name) {
      console.error(`❌ [FUNCTION CALL] Invalid function call data:`, functionData);
      return;
    }

    // Map xiaozhi function names to MCP tool names for ESP32 firmware
    const functionToMcpToolMap = {
      'self_set_volume': 'self.audio_speaker.set_volume',
      'self_get_volume': 'self.get_device_status',
      'self_volume_up': 'self.audio_speaker.volume_up',
      'self_volume_down': 'self.audio_speaker.volume_down',
      'self_mute': 'self.audio_speaker.mute',
      'self_unmute': 'self.audio_speaker.unmute',
      'self_set_light_color': 'self.led.set_color',
      'self_get_battery_status': 'self.battery.get_status',
      'self_set_light_mode': 'self.led.set_mode',
      'self_set_rainbow_speed': 'self.led.set_rainbow_speed'
      
    };

    const mcpToolName = functionToMcpToolMap[functionCall.name];
    if (!mcpToolName) {
      console.log(`⚠️ [FUNCTION CALL] Unknown function: ${functionCall.name}, forwarding as MCP message`);
      // Forward unknown functions as MCP tool calls
      this.sendMcpMessage(functionCall.name, functionCall.arguments || {});
      return;
    }

    // Create MCP message format expected by ESP32 firmware (JSON-RPC 2.0)
    const requestId = parseInt(functionData.request_id?.replace('req_', '') || Date.now());
    const message = {
      type: "mcp",
      payload: {
        jsonrpc: "2.0",
        method: "tools/call",
        params: {
          name: mcpToolName,
          arguments: functionCall.arguments || {}
        },
        id: requestId
      },
      session_id: this.connection.udp.session_id,
      timestamp: functionData.timestamp || new Date().toISOString(),
      request_id: `req_${requestId}`
    };

    console.log(
      `🔧 [MCP] Sending to device: ${this.macAddress} - Tool: ${mcpToolName}, Args: ${JSON.stringify(functionCall.arguments)}`
    );
    this.connection.sendMqttMessage(JSON.stringify(message));

    // Simulate device response for testing (remove in production)
    // setTimeout(() => {
    //   this.simulateFunctionCallResponse(functionData);
    // }, 100);
  }

  // Send unknown function calls directly to device (deprecated - use sendMcpMessage)
  sendFunctionCallToDevice(functionData) {
    if (!this.connection) return;

    const message = {
      type: "function_call",
      function_call: functionData.function_call,
      session_id: this.connection.udp.session_id,
      timestamp: functionData.timestamp || new Date().toISOString(),
      request_id: functionData.request_id || `req_${Date.now()}`
    };

    console.log(
      `📤 [FUNCTION FORWARD] Forwarding unknown function to device: ${this.macAddress} - ${functionData.function_call?.name}`
    );
    this.connection.sendMqttMessage(JSON.stringify(message));
  }

  // Send MCP tool call message to device
  sendMcpMessage(toolName, toolArgs = {}) {
    if (!this.connection) return;

    const requestId = Date.now();
    const message = {
      type: "mcp",
      payload: {
        jsonrpc: "2.0",
        method: "tools/call",
        params: {
          name: toolName,
          arguments: toolArgs
        },
        id: requestId
      },
      session_id: this.connection.udp.session_id,
      timestamp: new Date().toISOString(),
      request_id: `req_${requestId}`
    };

    console.log(
      `📤 [MCP] Sending MCP tool call to device: ${this.macAddress} - Tool: ${toolName}, Args: ${JSON.stringify(toolArgs)}`
    );
    this.connection.sendMqttMessage(JSON.stringify(message));
  }

  // Simulate device control response (for testing - remove in production)
  simulateDeviceControlResponse(originalCommand) {
    if (!this.room || !this.room.localParticipant) return;

    try {
      let currentValue = null;
      let success = true;
      let errorMessage = null;

      // Simulate responses based on action type
      const action = originalCommand.action || originalCommand.command;
      switch (action) {
        case 'set_volume':
          currentValue = originalCommand.volume || originalCommand.value || 50;
          break;
        case 'get_volume':
          currentValue = 65; // Simulated current volume
          break;
        case 'volume_up':
          currentValue = Math.min(100, 65 + (originalCommand.step || originalCommand.value || 10));
          break;
        case 'volume_down':
          currentValue = Math.max(0, 65 - (originalCommand.step || originalCommand.value || 10));
          break;
        default:
          success = false;
          errorMessage = `Unknown action: ${action}`;
      }

      const responseMessage = {
        type: "device_control_response",
        action: action,
        success: success,
        current_value: currentValue,
        error: errorMessage,
        session_id: originalCommand.session_id || "unknown"
      };

      // Send response back to agent via data channel
      const messageString = JSON.stringify(responseMessage);
      const messageData = new Uint8Array(Buffer.from(messageString, 'utf8'));
      this.room.localParticipant.publishData(
        messageData,
        { reliable: true }
      );

      console.log(`🎛️ [DEVICE RESPONSE] Simulated response: Action ${action}, Success: ${success}, Value: ${currentValue}`);
    } catch (error) {
      console.error(`❌ [DEVICE RESPONSE] Error simulating device response:`, error);
    }
  }

  // Simulate function call response (for testing - remove in production)
  simulateFunctionCallResponse(originalFunction) {
    if (!this.room || !this.room.localParticipant) return;

    try {
      const functionCall = originalFunction.function_call;
      if (!functionCall) return;

      let success = true;
      let result = {};
      let errorMessage = null;

      // Simulate responses based on function name
      switch (functionCall.name) {
        case 'self_set_volume':
          const volume = functionCall.arguments?.volume || 50;
          result = { new_volume: volume };
          break;
        case 'self_get_volume':
          result = { current_volume: 65 }; // Simulated current volume
          break;
        case 'self_volume_up':
          result = { new_volume: Math.min(100, 65 + 10) };
          break;
        case 'self_volume_down':
          result = { new_volume: Math.max(0, 65 - 10) };
          break;
        case 'self_mute':
          result = { muted: true, previous_volume: 65 };
          break;
        case 'self_unmute':
          result = { muted: false, current_volume: 65 };
          break;
        default:
          success = false;
          errorMessage = `Unknown function: ${functionCall.name}`;
      }

      const responseMessage = {
        type: "function_response",
        request_id: originalFunction.request_id || "unknown",
        function_name: functionCall.name,
        success: success,
        result: result,
        error: errorMessage,
        timestamp: new Date().toISOString()
      };

      // Send response back to agent via data channel
      const messageString = JSON.stringify(responseMessage);
      const messageData = new Uint8Array(Buffer.from(messageString, 'utf8'));
      this.room.localParticipant.publishData(
        messageData,
        { reliable: true }
      );

      console.log(`🔧 [FUNCTION RESPONSE] Simulated response: Function ${functionCall.name}, Success: ${success}, Result: ${JSON.stringify(result)}`);
    } catch (error) {
      console.error(`❌ [FUNCTION RESPONSE] Error simulating function response:`, error);
    }
  }

  // Send LLM response to device
  sendLlmMessage(text, emotion = "neutral") {
    if (!this.connection || !text) return;

    const message = {
      type: "llm",
      text: text,
      emotion: emotion,
      session_id: this.connection.udp.session_id,
    };

    console.log(
      `📤 [MQTT OUT] Sending LLM response to device: ${this.macAddress} - "${text}"`
    );
    this.connection.sendMqttMessage(JSON.stringify(message));
  }

  // Send record stop message to device
  sendRecordStopMessage() {
    if (!this.connection) return;

    const message = {
      type: "record_stop",
      session_id: this.connection.udp.session_id,
    };

    console.log(
      `📤 [MQTT OUT] Sending record stop to device: ${this.macAddress}`
    );
    this.connection.sendMqttMessage(JSON.stringify(message));
  }

  // Send device information and initial greeting when agent joins
  async sendInitialGreeting() {
    if (!this.connection) return;

    try {
      // First send device information for prompt loading
      const deviceInfoMessage = {
        type: "device_info",
        device_mac: this.macAddress,
        device_uuid: this.uuid,
        timestamp: Date.now(),
        source: "mqtt_gateway"
      };

      // Send device info via LiveKit data channel
      if (this.room && this.room.localParticipant) {
        const deviceInfoString = JSON.stringify(deviceInfoMessage);
        const deviceInfoData = new Uint8Array(Buffer.from(deviceInfoString, 'utf8'));
        await this.room.localParticipant.publishData(
          deviceInfoData,
          { reliable: true }
        );

        console.log(
          `📱 [DEVICE INFO] Sent device MAC (${this.macAddress}) to agent via data channel`
        );

        // Then send greeting trigger
        const initialMessage = {
          type: "agent_ready",
          message: "Say hello to the user",
          timestamp: Date.now(),
          source: "mqtt_gateway"
        };

        const messageString = JSON.stringify(initialMessage);
        const messageData = new Uint8Array(Buffer.from(messageString, 'utf8'));
        await this.room.localParticipant.publishData(
          messageData,
          { reliable: true }
        );

        console.log(
          `🤖 [AGENT READY] Sent initial greeting trigger to agent for device: ${this.macAddress}`
        );
      } else {
        console.warn(
          `⚠️ [AGENT READY] Cannot send messages - room not ready for device: ${this.macAddress}`
        );
      }
    } catch (error) {
      console.error(
        `❌ [AGENT READY] Error sending messages to agent for device ${this.macAddress}:`, error
      );
    }
  }

  async sendAbortSignal(sessionId) {
    /**
     * Send abort signal to LiveKit agent via data channel
     * This tells the agent to stop current TTS/music playback
     */
    if (!this.room || !this.room.localParticipant) {
      throw new Error("Room not connected or no local participant");
    }

    try {
      const abortMessage = {
        type: "abort_playback",
        session_id: sessionId,
        timestamp: Date.now(),
        source: "mqtt_gateway"
      };

      // Send via LiveKit data channel to the agent
      // Convert to Uint8Array as required by LiveKit Node SDK
      const messageString = JSON.stringify(abortMessage);
      const messageData = new Uint8Array(Buffer.from(messageString, 'utf8'));
      await this.room.localParticipant.publishData(
        messageData,
        { reliable: true }
      );

      console.log(`🛑 [ABORT] Sent abort signal to LiveKit agent via data channel`);
    } catch (error) {
      console.error(`[LiveKitBridge] Failed to send abort signal:`, error);
      throw error;
    }
  }

  async sendEndPrompt(sessionId) {
    /**
     * Send end prompt signal to LiveKit agent via data channel
     * This tells the agent to say goodbye using the end prompt before session ends
     */
    if (!this.room || !this.room.localParticipant) {
      throw new Error("Room not connected or no local participant");
    }

    // Check if the room is still connected before trying to send data
    if (!this.room.isConnected) {
      console.log(`👋 [END-PROMPT] Room already disconnected, skipping end prompt`);
      return;
    }

    try {
      const endMessage = {
        type: "end_prompt",
        session_id: sessionId,
        prompt: "You must end this conversation now. Start with 'Time flies so fast' and say a SHORT goodbye in 1-2 sentences maximum. Do NOT ask questions or suggest activities. Just say goodbye emotionally and end the conversation.",
        timestamp: Date.now(),
        source: "mqtt_gateway"
      };

      // Send via LiveKit data channel to the agent
      // Convert to Uint8Array as required by LiveKit Node SDK
      const messageString = JSON.stringify(endMessage);
      const messageData = new Uint8Array(Buffer.from(messageString, 'utf8'));
      await this.room.localParticipant.publishData(
        messageData,
        { reliable: true }
      );

      console.log(`👋 [END-PROMPT] Sent end prompt to LiveKit agent via data channel`);
    } catch (error) {
      console.error(`[LiveKitBridge] Failed to send end prompt:`, error);
      // Don't throw the error - just log it and continue with cleanup
      console.log(`👋 [END-PROMPT] Continuing with connection cleanup despite end prompt failure`);
    }
  }

  async close() {
    if (this.room) {
      console.log("[LiveKitBridge] Disconnecting from LiveKit room");

      // First disconnect from the room
      await this.room.disconnect();

      // Send a final cleanup signal to ensure the agent side also cleans up
      try {
        const cleanupMessage = {
          type: "cleanup_request",
          session_id: this.connection.udp.session_id,
          timestamp: Date.now(),
          source: "mqtt_gateway"
        };

        if (this.room.localParticipant && this.room.isConnected) {
          const messageString = JSON.stringify(cleanupMessage);
          const messageData = new Uint8Array(Buffer.from(messageString, 'utf8'));
          await this.room.localParticipant.publishData(
            messageData,
            { reliable: true }
          );
          console.log("🧹 Sent cleanup signal to agent before disconnect");
        }
      } catch (error) {
        console.log("Note: Could not send cleanup signal (room already disconnected)");
      }

      this.room = null;
    }
  }
}

const MacAddressRegex = /^[0-9a-f]{2}(:[0-9a-f]{2}){5}$/;

/**
 * MQTT connection class
 * Responsible for application layer logic processing
 */
class MQTTConnection {
  constructor(socket, connectionId, server) {
    this.server = server;
    this.connectionId = connectionId;
    this.clientId = null;
    this.username = null;
    this.password = null;
    this.bridge = null;
    this.udp = {
      remoteAddress: null,
      cookie: null,
      localSequence: 0,
      remoteSequence: 0,
    };
    this.headerBuffer = Buffer.alloc(16);

    // Add inactivity timeout tracking
    this.lastActivityTime = Date.now();
    this.inactivityTimeoutMs = 60 * 1000; // 1 minute in milliseconds
    this.isEnding = false; // Track if end prompt has been sent
    this.endPromptSentTime = null; // Track when end prompt was sent

    // Create protocol handler and pass in socket
    this.protocol = new MQTTProtocol(socket);
    this.setupProtocolHandlers();
  }

  setupProtocolHandlers() {
    // Set protocol event handlers
    this.protocol.on("connect", (connectData) => {
      // console.log("Received CONNECT packet");
      this.handleConnect(connectData);
    });

    this.protocol.on("publish", (publishData) => {
      this.handlePublish(publishData);
    });

    this.protocol.on("subscribe", (subscribeData) => {
      this.handleSubscribe(subscribeData);
    });

    this.protocol.on("disconnect", () => {
      this.handleDisconnect();
    });

    this.protocol.on("close", () => {
      debug(`${this.clientId} client disconnected`);
      this.server.removeConnection(this);
    });

    this.protocol.on("error", (err) => {
      debug(`${this.clientId} connection error:`, err);
      this.close();
    });

    this.protocol.on("protocolError", (err) => {
      debug(`${this.clientId} protocol error:`, err);
      this.close();
    });
  }

  handleConnect(connectData) {
    this.clientId = connectData.clientId;
    this.username = connectData.username;
    this.password = connectData.password;

    debug("Client connected:", {
      clientId: this.clientId,
      username: this.username,
      password: this.password,
      protocol: connectData.protocol,
      protocolLevel: connectData.protocolLevel,
      keepAlive: connectData.keepAlive,
    });

    const parts = this.clientId.split("@@@");
    if (parts.length === 3) {
      // GID_test@@@mac_address@@@uuid
      try {
        const validated = validateMqttCredentials(
          this.clientId,
          this.username,
          this.password
        );
        this.groupId = validated.groupId;
        this.macAddress = validated.macAddress;
        this.uuid = validated.uuid;
        this.userData = validated.userData;
      } catch (error) {
        debug("MQTT credentials validation failed:", error.message);
        this.close();
        return;
      }
    } else if (parts.length === 2) {
      // GID_test@@@mac_address
      this.groupId = parts[0];
      this.macAddress = parts[1].replace(/_/g, ":");
      if (!MacAddressRegex.test(this.macAddress)) {
        debug("Invalid macAddress:", this.macAddress);
        this.close();
        return;
      }
    } else {
      debug("Invalid clientId:", this.clientId);
      this.close();
      return;
    }

    this.replyTo = `devices/p2p/${parts[1]}`;
    this.server.addConnection(this);
  }

  handleSubscribe(subscribeData) {
    debug("Client subscribed to topic:", {
      clientId: this.clientId,
      topic: subscribeData.topic,
      packetId: subscribeData.packetId,
    });
    // Send SUBACK
    this.protocol.sendSuback(subscribeData.packetId, 0);
  }

  handleDisconnect() {
    debug("Received disconnect request:", { clientId: this.clientId });
    // Clean up connection
    this.server.removeConnection(this);
  }

  close() {
    this.closing = true;
    if (this.bridge) {
      this.bridge.close();
      this.bridge = null;
    } else {
      this.protocol.close();
    }
  }

  updateActivityTime() {
    this.lastActivityTime = Date.now();

    // Don't reset ending state during goodbye sequence
    if (this.isEnding) {
      console.log(`📱 [ENDING-IGNORE] Activity during goodbye sequence ignored for device: ${this.clientId}`);
      return; // Don't log timer reset during ending
    }

    console.log(`⏱️ [TIMER-RESET] Activity timer reset for device: ${this.clientId} at ${new Date().toISOString()}`);
  }

  async checkKeepAlive() {
    // Don't check keepalive if connection is closing
    if (this.closing) {
      return;
    }

    const now = Date.now();

    // If we're in ending phase, check for final timeout
    if (this.isEnding && this.endPromptSentTime) {
      const timeSinceEndPrompt = now - this.endPromptSentTime;
      const maxEndWaitTime = 30 * 1000; // 30 seconds max wait for end prompt audio

      if (timeSinceEndPrompt > maxEndWaitTime) {
        console.log(`🕒 [END-TIMEOUT] End prompt timeout reached, force closing connection: ${this.clientId} (waited ${Math.round(timeSinceEndPrompt / 1000)}s)`);
        this.close();
        return;
      }

      // Show countdown for end prompt completion
      if (timeSinceEndPrompt % 5000 < 1000) {
        const remainingSeconds = Math.round((maxEndWaitTime - timeSinceEndPrompt) / 1000);
        console.log(`⏳ [END-WAIT] Device ${this.clientId}: ${remainingSeconds}s until force disconnect`);
      }
      return; // Don't do normal timeout check while ending
    }

    // Check for inactivity timeout (1 minute of no communication)
    const timeSinceLastActivity = now - this.lastActivityTime;

    // Skip timeout check if audio is actively playing
    if (this.bridge && this.bridge.isAudioPlaying) {
      // Reset the timer while audio is playing to prevent timeout
      this.lastActivityTime = now;
      console.log(`🎵 [AUDIO-ACTIVE] Resetting timer - audio is playing for device: ${this.clientId}`);
      return;
    }

    if (timeSinceLastActivity > this.inactivityTimeoutMs) {
      // Send end prompt instead of immediate close
      if (!this.isEnding && this.bridge) {
        this.isEnding = true;
        this.endPromptSentTime = now;
        console.log(`👋 [END-PROMPT] Sending goodbye message before timeout: ${this.clientId} (inactive for ${Math.round(timeSinceLastActivity / 1000)}s) - Last activity: ${new Date(this.lastActivityTime).toISOString()}, Now: ${new Date(now).toISOString()}`);

        try {
          await this.bridge.sendEndPrompt(this.udp.session_id);
        } catch (error) {
          console.error(`Failed to send end prompt: ${error.message}`);
          // If end prompt fails, close immediately
          this.close();
        }
        return;
      } else {
        // No bridge available, close immediately
        console.log(`🕒 [TIMEOUT] Closing connection due to 1-minute inactivity: ${this.clientId} (inactive for ${Math.round(timeSinceLastActivity / 1000)}s)`);
        this.close();
        return;
      }
    }

    // Log remaining time until timeout (only show every 30 seconds to avoid spam)
    if (timeSinceLastActivity % 30000 < 1000) {
      const remainingSeconds = Math.round((this.inactivityTimeoutMs - timeSinceLastActivity) / 1000);
      console.log(`⏰ [TIMER-CHECK] Device ${this.clientId}: ${remainingSeconds}s until timeout`);
    }

    // Original keep-alive check
    const keepAliveInterval = this.protocol.getKeepAliveInterval();
    // If keepAliveInterval is 0, heartbeat check is not needed
    if (keepAliveInterval === 0 || !this.protocol.isConnected) return;

    const protocolLastActivity = this.protocol.getLastActivity();
    const timeSinceProtocolActivity = now - protocolLastActivity;

    // If heartbeat interval is exceeded, close connection
    if (timeSinceProtocolActivity > keepAliveInterval) {
      debug("Heartbeat timeout, closing connection:", this.clientId);
      this.close();
    }
  }

  handlePublish(publishData) {
    // Update activity timestamp on any MQTT message receipt
    console.log(`📨 [ACTIVITY] MQTT message received from ${this.clientId}, resetting inactivity timer`);
    this.updateActivityTime();

    debug("Received publish message:", {
      clientId: this.clientId,
      topic: publishData.topic,
      payload: publishData.payload,
      qos: publishData.qos,
    });

    if (publishData.qos !== 0) {
      debug("Unsupported QoS level:", publishData.qos, "closing connection");
      this.close();
      return;
    }

    const json = JSON.parse(publishData.payload);
    if (json.type === "hello") {
      if (json.version !== 3) {
        debug(
          "Unsupported protocol version:",
          json.version,
          "closing connection"
        );
        this.close();
        return;
      }

      this.parseHelloMessage(json).catch((error) => {
        debug("Failed to process hello message:", error);
        this.close();
      });
    } else {
      this.parseOtherMessage(json).catch((error) => {
        debug("Failed to process other message:", error);
        this.close();
      });
    }
  }

  sendMqttMessage(payload) {
    debug(`Sending message to ${this.replyTo}: ${payload}`);
    this.protocol.sendPublish(this.replyTo, payload, 0, false, false);
  }

  sendUdpMessage(payload, timestamp) {
    if (!this.udp.remoteAddress) {
      debug(`Device ${this.clientId} not connected, cannot send UDP message`);
      return;
    }

    this.udp.localSequence++;
    const header = this.generateUdpHeader(
      payload.length,
      timestamp,
      this.udp.localSequence
    );
    // console.log(
    //   `📡 [UDP SEND] To ${this.udp.remoteAddress.address}:${this.udp.remoteAddress.port} - payload=${payload.length}B, ts=${timestamp}, seq=${this.udp.localSequence}`
    // );
    // console.log(
    //   `🔐 Encrypting: payload=${payload.length}B, timestamp=${timestamp}, seq=${this.udp.localSequence}`
    // );
    // console.log(`🔐 Header: ${header.toString("hex")}`);
    // console.log(`🔐 Key: ${this.udp.key.toString("hex")}`);
    // console.log(
    //   `🔐 Payload first 8 bytes: ${payload.subarray(0, 8).toString("hex")}`
    // );
    const cipher = crypto.createCipheriv(
      this.udp.encryption,
      this.udp.key,
      header
    );
    const encryptedPayload = Buffer.concat([
      cipher.update(payload),
      cipher.final(),
    ]);
    // console.log(
    //   `🔐 Encrypted first 8 bytes: ${encryptedPayload
    //     .subarray(0, 8)
    //     .toString("hex")}`
    // );
    const message = Buffer.concat([header, encryptedPayload]);
    this.server.sendUdpMessage(message, this.udp.remoteAddress);
  }

  generateUdpHeader(length, timestamp, sequence) {
    // Reuse pre-allocated buffer
    this.headerBuffer.writeUInt8(1, 0); // packet_type
    this.headerBuffer.writeUInt8(0, 1); // flags
    this.headerBuffer.writeUInt16BE(length, 2); // payload_len
    this.headerBuffer.writeUInt32BE(this.connectionId, 4); // ssrc/connection_id
    this.headerBuffer.writeUInt32BE(timestamp, 8); // timestamp
    this.headerBuffer.writeUInt32BE(sequence, 12); // sequence
    return Buffer.from(this.headerBuffer); // Return copy to avoid concurrency issues
  }

  async parseHelloMessage(json) {
    this.udp = {
      ...this.udp,
      key: crypto.randomBytes(16),
      nonce: this.generateUdpHeader(0, 0, 0),
      encryption: "aes-128-ctr",
      remoteSequence: 0,
      localSequence: 0,
      startTime: Date.now(),
    };

    if (this.bridge) {
      debug(
        `${this.clientId} received duplicate hello message, closing previous bridge`
      );
      this.bridge.close();
      await new Promise((resolve) => setTimeout(resolve, 100));
    }

    this.bridge = new LiveKitBridge(
      this,
      json.version,
      this.macAddress,
      this.uuid,
      this.userData
    );
    this.bridge.on("close", () => {
      const seconds = (Date.now() - this.udp.startTime) / 1000;
      console.log(
        `Call ended: ${this.clientId} Session: ${this.udp.session_id} Duration: ${seconds}s`
      );

      // Send goodbye to device
      this.sendMqttMessage(
        JSON.stringify({ type: "goodbye", session_id: this.udp.session_id })
      );

      // Clean up the bridge reference
      this.bridge = null;

      // Log room cleanup
      console.log(`🧹 LiveKit room cleanup initiated for session: ${this.udp.session_id}`);

      if (this.closing) {
        this.protocol.close();
      }
    });

    try {
      console.log(`Call started: ${this.clientId} Protocol: ${json.version}`);
      const helloReply = await this.bridge.connect(
        json.audio_params,
        json.features
      );
      this.udp.session_id = helloReply.session_id;

      this.sendMqttMessage(
        JSON.stringify({
          type: "hello",
          version: json.version,
          session_id: this.udp.session_id,
          transport: "udp",
          udp: {
            server: this.server.publicIp,
            port: this.server.udpPort,
            encryption: this.udp.encryption,
            key: this.udp.key.toString("hex"),
            nonce: this.udp.nonce.toString("hex"),
          },
          audio_params: helloReply.audio_params,
        })
      );
    } catch (error) {
      this.sendMqttMessage(
        JSON.stringify({
          type: "error",
          message: "Failed to process hello message",
        })
      );
      console.error(
        `${this.clientId} failed to process hello message: ${error}`
      );
    }
  }

  async parseOtherMessage(json) {
    if (!this.bridge) {
      if (json.type !== "goodbye") {
        this.sendMqttMessage(
          JSON.stringify({ type: "goodbye", session_id: json.session_id })
        );
      }
      return;
    }

    if (json.type === "goodbye") {
      console.log(`👋 [GOODBYE-MAC] Received goodbye message from device: ${this.macAddress}, session: ${json.session_id}`);
      this.bridge.close();
      this.bridge = null;
      return;
    }

    // Handle abort message - forward to LiveKit agent via data channel
    if (json.type === "abort") {
      try {
        console.log(`🛑 [ABORT] Received abort signal from device: ${this.macAddress}`);
        await this.bridge.sendAbortSignal(json.session_id);
        debug("Successfully forwarded abort signal to LiveKit agent");
      } catch (error) {
        debug("Failed to forward abort signal to LiveKit:", error);
      }
      return;
    }

    // Not sending other messages to LiveKit for now
    debug("Received other message, not forwarding to LiveKit:", json);
  }

  onUdpMessage(rinfo, message, payloadLength, timestamp, sequence) {
    // UDP messages do not reset inactivity timer - only MQTT messages do

    if (!this.bridge) {
      // console.log(
      //   `📡 [UDP RECV] No bridge available for ${this.clientId}, dropping message`
      // );
      return;
    }

    if (this.udp.remoteAddress !== rinfo) {
      // console.log(
      //   `📡 [UDP RECV] New remote address: ${rinfo.address}:${rinfo.port} for ${this.clientId}`
      // );
      this.udp.remoteAddress = rinfo;
    }

    if (sequence < this.udp.remoteSequence) {
      // console.log(
      //   `📡 [UDP RECV] Out of order packet: seq=${sequence}, expected>=${this.udp.remoteSequence}, dropping`
      // );
      return;
    }

    // console.log(
    //   `📡 [UDP RECV] From ${rinfo.address}:${rinfo.port} - payload=${payloadLength}B, ts=${timestamp}, seq=${sequence}`
    // );

    // Process encrypted data
    const header = message.slice(0, 16);
    const encryptedPayload = message.slice(16, 16 + payloadLength);
    const cipher = crypto.createDecipheriv(
      this.udp.encryption,
      this.udp.key,
      header
    );
    const payload = Buffer.concat([
      cipher.update(encryptedPayload),
      cipher.final(),
    ]);

    // Check if this is a ping message
    const payloadStr = payload.toString();
    if (payloadStr.startsWith("ping:")) {
      console.log(
        `🏓 [UDP PING] Received ping: ${payloadStr} from ${rinfo.address}:${rinfo.port}`
      );
      // Ping message received, connection is now established
      return;
    }

    //console.log(
    // `🔊 [AUDIO RECV] Decrypted ${payload.length}B audio data, forwarding to LiveKit`
    //);
    this.bridge.sendAudio(payload, timestamp);
    this.udp.remoteSequence = sequence;
  }

  isAlive() {
    return this.bridge && this.bridge.isAlive();
  }
}

/**
 * Virtual MQTT connection class for EMQX broker connections
 * Simulates the original MQTTConnection interface but works through EMQX
 */
class VirtualMQTTConnection {
  constructor(deviceId, connectionId, gateway, helloPayload) {
    this.deviceId = deviceId;
    this.connectionId = connectionId;
    this.gateway = gateway;
    this.clientId = helloPayload.clientId || deviceId;
    this.username = helloPayload.username;
    this.password = helloPayload.password;
     this.fullClientId = helloPayload.clientId;

    this.bridge = null;
    this.udp = {
      remoteAddress: null,
      cookie: null,
      localSequence: 0,
      remoteSequence: 0,
    };
    this.headerBuffer = Buffer.alloc(16);
    this.closing = false;

    // Add inactivity timeout tracking
    this.lastActivityTime = Date.now();
    this.inactivityTimeoutMs = 60 * 1000; // 1 minute in milliseconds
    this.isEnding = false; // Track if end prompt has been sent
    this.endPromptSentTime = null; // Track when end prompt was sent

    // Parse device info from hello message
    if (helloPayload.clientId) {
      const parts = helloPayload.clientId.split("@@@");
      if (parts.length === 3) {
        // GID_test@@@mac_address@@@uuid format
        this.groupId = parts[0];
        this.macAddress = parts[1].replace(/_/g, ":");
        this.uuid = parts[2];
        this.userData = null; // Set to null since we don't have user data

        console.log(`📱 [VIRTUAL] Parsed client info:`);
        console.log(`   - Group ID: ${this.groupId}`);
        console.log(`   - MAC Address: ${this.macAddress}`);
        console.log(`   - UUID: ${this.uuid}`);

        // Validate MAC address format
        if (!MacAddressRegex.test(this.macAddress)) {
          console.error(`❌ [VIRTUAL] Invalid macAddress: ${this.macAddress}`);
          this.close();
          return;
        }

        // For virtual connections, we can skip the full credential validation
        // since we're working with EMQX and not the original MQTT protocol

      } else if (parts.length === 2) {
        this.groupId = parts[0];
        this.macAddress = parts[1].replace(/_/g, ":");
        this.uuid = `virtual-${Date.now()}`; // Generate a virtual UUID
        this.userData = null;

        if (!MacAddressRegex.test(this.macAddress)) {
          console.error(`❌ [VIRTUAL] Invalid macAddress: ${this.macAddress}`);
          this.close();
          return;
        }
      } else {
        console.error(`❌ [VIRTUAL] Invalid clientId format: ${helloPayload.clientId}`);
        this.close();
        return;
      }

      this.replyTo = `devices/p2p/${parts[1]}`;
      console.log(`📱 [VIRTUAL] Reply topic set to: ${this.replyTo}`);
    } else {
      console.error(`❌ [VIRTUAL] No clientId provided in hello payload`);
      this.close();
      return;
    }

    debug(`Virtual connection created for device: ${this.deviceId}`);
  }

  updateActivityTime() {
    this.lastActivityTime = Date.now();

    // Don't reset ending state during goodbye sequence
    if (this.isEnding) {
      console.log(`📱 [ENDING-IGNORE] Activity during goodbye sequence ignored for virtual device: ${this.deviceId}`);
      return; // Don't log timer reset during ending
    }

    console.log(`⏱️ [TIMER-RESET] Activity timer reset for virtual device: ${this.deviceId} at ${new Date().toISOString()}`);
  }

  handlePublish(publishData) {
    // Update activity timestamp on any MQTT message receipt
    console.log(`📨 [ACTIVITY] MQTT message received from virtual device ${this.deviceId}, resetting inactivity timer`);
    this.updateActivityTime();

    try {
      const json = JSON.parse(publishData.payload);
      if (json.type === "hello") {
        if (json.version !== 3) {
          debug(
            "Unsupported protocol version:",
            json.version,
            "closing connection"
          );
          this.close();
          return;
        }

        this.parseHelloMessage(json).catch((error) => {
          debug("Failed to process hello message:", error);
          this.close();
        });
      } else {
        this.parseOtherMessage(json).catch((error) => {
          debug("Failed to process other message:", error);
          this.close();
        });
      }
    } catch (error) {
      debug("Error parsing message:", error);
    }
  }

  sendMqttMessage(payload) {
    console.log(`📤 [VIRTUAL] sendMqttMessage called for device: ${this.deviceId}`);
    console.log(`📤 [VIRTUAL] Payload: ${payload}`);
    debug(`Sending message to ${this.deviceId}: ${payload}`);

    try {
      const parsedPayload = JSON.parse(payload);
      console.log(`📤 [VIRTUAL] Parsed payload:`, parsedPayload);
      this.gateway.publishToDevice(this.fullClientId, parsedPayload)
      console.log(`📤 [VIRTUAL] Called publishToDevice for device: ${this.deviceId}`);
    } catch (error) {
      console.error(`❌ [VIRTUAL] Error in sendMqttMessage for device ${this.deviceId}:`, error);
    }
  }

  sendUdpMessage(payload, timestamp) {
    if (!this.udp.remoteAddress) {
      debug(`Device ${this.deviceId} not connected, cannot send UDP message`);
      return;
    }

    this.udp.localSequence++;
    const header = this.generateUdpHeader(
      payload.length,
      timestamp,
      this.udp.localSequence
    );

    const cipher = crypto.createCipheriv(
      this.udp.encryption,
      this.udp.key,
      header
    );
    const encryptedPayload = Buffer.concat([
      cipher.update(payload),
      cipher.final(),
    ]);
    const message = Buffer.concat([header, encryptedPayload]);
    this.gateway.sendUdpMessage(message, this.udp.remoteAddress);
  }

  generateUdpHeader(length, timestamp, sequence) {
    this.headerBuffer.writeUInt8(1, 0);
    this.headerBuffer.writeUInt8(0, 1);
    this.headerBuffer.writeUInt16BE(length, 2);
    this.headerBuffer.writeUInt32BE(this.connectionId, 4);
    this.headerBuffer.writeUInt32BE(timestamp, 8);
    this.headerBuffer.writeUInt32BE(sequence, 12);
    return Buffer.from(this.headerBuffer);
  }

  async parseHelloMessage(json) {
    this.udp = {
      ...this.udp,
      key: crypto.randomBytes(16),
      nonce: this.generateUdpHeader(0, 0, 0),
      encryption: "aes-128-ctr",
      remoteSequence: 0,
      localSequence: 0,
      startTime: Date.now(),
    };

    if (this.bridge) {
      debug(
        `${this.deviceId} received duplicate hello message, closing previous bridge`
      );
      this.bridge.close();
      await new Promise((resolve) => setTimeout(resolve, 100));
    }

    this.bridge = new LiveKitBridge(
      this,
      json.version,
      this.macAddress,
      this.uuid,
      this.userData
    );
    this.bridge.on("close", () => {
      const seconds = (Date.now() - this.udp.startTime) / 1000;
      console.log(
        `Call ended: ${this.deviceId} Session: ${this.udp.session_id} Duration: ${seconds}s`
      );

      // Send goodbye to device
      this.sendMqttMessage(
        JSON.stringify({ type: "goodbye", session_id: this.udp.session_id })
      );

      // Clean up the bridge reference
      this.bridge = null;

      // Log room cleanup
      console.log(`🧹 LiveKit room cleanup initiated for virtual session: ${this.udp.session_id}`);

      if (this.closing) {
        // Remove from gateway connections
        this.gateway.connections.delete(this.connectionId);
        this.gateway.deviceConnections.delete(this.deviceId);
      }
    });

    try {
      console.log(`Call started: ${this.deviceId} Protocol: ${json.version}`);
      const helloReply = await this.bridge.connect(
        json.audio_params,
        json.features
      );
      console.log(`📡 [HELLO REPLY] Bridge connect response:`, helloReply);

      this.udp.session_id = helloReply.session_id;
      console.log(`📡 [SESSION ID] Set session_id to: ${this.udp.session_id}`);

      this.sendMqttMessage(
        JSON.stringify({
          type: "hello",
          version: json.version,
          session_id: this.udp.session_id,
          transport: "udp",
          udp: {
            server: this.gateway.publicIp,
            port: this.gateway.udpPort,
            encryption: this.udp.encryption,
            key: this.udp.key.toString("hex"),
            nonce: this.udp.nonce.toString("hex"),
          },
          audio_params: helloReply.audio_params,
        })
      );
    } catch (error) {
      this.sendMqttMessage(
        JSON.stringify({
          type: "error",
          message: "Failed to process hello message",
        })
      );
      console.error(
        `${this.deviceId} failed to process hello message: ${error}`
      );
    }
  }

  async parseOtherMessage(json) {
    if (!this.bridge) {
      if (json.type !== "goodbye") {
        this.sendMqttMessage(
          JSON.stringify({ type: "goodbye", session_id: json.session_id })
        );
      }
      return;
    }

    if (json.type === "goodbye") {
      console.log(`👋 [GOODBYE-DEVICEID] Received goodbye message from device: ${this.deviceId}, session: ${json.session_id}`);
      // this.bridge.close();
      // this.bridge = null;
      //commet temporarly, dgoodby message is not working well
      
      return;
    }

    // Handle abort message - forward to LiveKit agent via data channel
    if (json.type === "abort") {
      try {
        console.log(`🛑 [ABORT] Received abort signal from device: ${this.deviceId}`);
        await this.bridge.sendAbortSignal(json.session_id);
        debug("Successfully forwarded abort signal to LiveKit agent");
      } catch (error) {
        debug("Failed to forward abort signal to LiveKit:", error);
      }
      return;
    }

    debug("Received other message, not forwarding to LiveKit:", json);
  }

  onUdpMessage(rinfo, message, payloadLength, timestamp, sequence) {
    // UDP messages do not reset inactivity timer - only MQTT messages do

    if (!this.bridge) {
      return;
    }

    if (this.udp.remoteAddress !== rinfo) {
      this.udp.remoteAddress = rinfo;
    }

    if (sequence < this.udp.remoteSequence) {
      return;
    }

    const header = message.slice(0, 16);
    const encryptedPayload = message.slice(16, 16 + payloadLength);
    const cipher = crypto.createDecipheriv(
      this.udp.encryption,
      this.udp.key,
      header
    );
    const payload = Buffer.concat([
      cipher.update(encryptedPayload),
      cipher.final(),
    ]);

    const payloadStr = payload.toString();
    if (payloadStr.startsWith("ping:")) {
      console.log(
        `🏓 [UDP PING] Received ping: ${payloadStr} from ${rinfo.address}:${rinfo.port}`
      );
      return;
    }

    this.bridge.sendAudio(payload, timestamp);
    this.udp.remoteSequence = sequence;
  }

  async checkKeepAlive() {
    // Don't check keepalive if connection is closing
    if (this.closing) {
      return;
    }

    const now = Date.now();

    // If we're in ending phase, check for final timeout
    if (this.isEnding && this.endPromptSentTime) {
      const timeSinceEndPrompt = now - this.endPromptSentTime;
      const maxEndWaitTime = 30 * 1000; // 30 seconds max wait for end prompt audio

      if (timeSinceEndPrompt > maxEndWaitTime) {
        console.log(`🕒 [END-TIMEOUT] End prompt timeout reached, force closing virtual connection: ${this.deviceId} (waited ${Math.round(timeSinceEndPrompt / 1000)}s)`);
        this.close();
        return;
      }

      // Show countdown for end prompt completion
      if (timeSinceEndPrompt % 5000 < 1000) {
        const remainingSeconds = Math.round((maxEndWaitTime - timeSinceEndPrompt) / 1000);
        console.log(`⏳ [END-WAIT] Virtual device ${this.deviceId}: ${remainingSeconds}s until force disconnect`);
      }
      return; // Don't do normal timeout check while ending
    }

    // Check for inactivity timeout (1 minute of no communication)
    const timeSinceLastActivity = now - this.lastActivityTime;

    // Skip timeout check if audio is actively playing
    if (this.bridge && this.bridge.isAudioPlaying) {
      // Reset the timer while audio is playing to prevent timeout
      this.lastActivityTime = now;
      console.log(`🎵 [AUDIO-ACTIVE] Resetting timer - audio is playing for virtual device: ${this.deviceId}`);
      return;
    }

    if (timeSinceLastActivity > this.inactivityTimeoutMs) {
      // Send end prompt instead of immediate close
      if (!this.isEnding && this.bridge) {
        this.isEnding = true;
        this.endPromptSentTime = now;
        console.log(`👋 [END-PROMPT] Sending goodbye message before timeout: ${this.deviceId} (inactive for ${Math.round(timeSinceLastActivity / 1000)}s) - Last activity: ${new Date(this.lastActivityTime).toISOString()}, Now: ${new Date(now).toISOString()}`);

        try {
          await this.bridge.sendEndPrompt(this.udp.session_id);
        } catch (error) {
          console.error(`Failed to send end prompt: ${error.message}`);
          // If end prompt fails, close immediately
          this.close();
        }
        return;
      } else {
        // No bridge available, close immediately
        console.log(`🕒 [TIMEOUT] Closing virtual connection due to 1-minute inactivity: ${this.deviceId} (inactive for ${Math.round(timeSinceLastActivity / 1000)}s)`);
        this.close();
        return;
      }
    }

    // Log remaining time until timeout (only show every 30 seconds to avoid spam)
    if (timeSinceLastActivity % 30000 < 1000) {
      const remainingSeconds = Math.round((this.inactivityTimeoutMs - timeSinceLastActivity) / 1000);
      console.log(`⏰ [TIMER-CHECK] Virtual device ${this.deviceId}: ${remainingSeconds}s until timeout`);
    }

    // Virtual connections don't need traditional keep-alive since EMQX handles it
  }

  close() {
    this.closing = true;
    if (this.bridge) {
      this.bridge.close();
      this.bridge = null;
    }
    // Remove from gateway maps
    this.gateway.connections.delete(this.connectionId);
    this.gateway.deviceConnections.delete(this.deviceId);
  }

  isAlive() {
    return this.bridge && this.bridge.isAlive();
  }
}

class MQTTGateway {
  constructor() {
    this.udpPort = parseInt(process.env.UDP_PORT) || 1883;
    this.publicIp = process.env.PUBLIC_IP || "127.0.0.1";
    this.connections = new Map(); // clientId -> MQTTConnection
    this.keepAliveTimer = null;
    this.keepAliveCheckInterval = 15000; // Check every 15 seconds
    this.headerBuffer = Buffer.alloc(16);
    this.mqttClient = null;
    this.deviceConnections = new Map(); // deviceId -> connection info
    this.clientConnections = new Map(); // clientId -> device info (for tracking EMQX clients)
  }

  generateNewConnectionId() {
    // Generate a unique 32-bit integer
    let id;
    do {
      id = Math.floor(Math.random() * 0xffffffff);
    } while (this.connections.has(id));
    return id;
  }

  start() {
    // Connect to EMQX broker
    this.connectToEmqxBroker();

    this.udpServer = dgram.createSocket("udp4");
    this.udpServer.on("message", this.onUdpMessage.bind(this));
    this.udpServer.on("error", (err) => {
      console.error("UDP error", err);
      setTimeout(() => {
        process.exit(1);
      }, 1000);
    });

    this.udpServer.bind(this.udpPort, () => {
      console.warn(`UDP server listening on ${this.publicIp}:${this.udpPort}`);
    });

    // Start global heartbeat check timer
    this.setupKeepAliveTimer();
  }

  connectToEmqxBroker() {
    const brokerConfig = configManager.get("mqtt_broker");
    if (!brokerConfig) {
      console.error("MQTT broker configuration not found in config");
      process.exit(1);
    }

    const clientId = `mqtt-gateway-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    const brokerUrl = `${brokerConfig.protocol}://${brokerConfig.host}:${brokerConfig.port}`;

    console.log(`Connecting to EMQX broker: ${brokerUrl}`);

    this.mqttClient = mqtt.connect(brokerUrl, {
      clientId: clientId,
      keepalive: brokerConfig.keepalive || 60,
      clean: brokerConfig.clean !== false,
      reconnectPeriod: brokerConfig.reconnectPeriod || 1000,
      connectTimeout: brokerConfig.connectTimeout || 30000
    });

    this.mqttClient.on('connect', () => {
      console.log(`✅ Connected to EMQX broker: ${brokerUrl}`);
      // Subscribe to gateway control topics
      this.mqttClient.subscribe('devices/+/hello', (err) => {
        if (err) {
          console.error('Failed to subscribe to device hello topic:', err);
        } else {
          console.log('📡 Subscribed to devices/+/hello');
        }
      });
      this.mqttClient.subscribe('devices/+/data', (err) => {
        if (err) {
          console.error('Failed to subscribe to device data topic:', err);
        } else {
          console.log('📡 Subscribed to devices/+/data');
        }
      });
      // Subscribe to the internal topic where EMQX republishes with client info
      this.mqttClient.subscribe('internal/server-ingest', (err) => {
        if (err) {
          console.error('Failed to subscribe to internal/server-ingest topic:', err);
        } else {
          console.log('📡 Subscribed to internal/server-ingest');
        }
      });
    });

    this.mqttClient.on('error', (err) => {
      console.error('MQTT connection error:', err);
    });

    this.mqttClient.on('offline', () => {
      console.warn('MQTT client went offline');
    });

    this.mqttClient.on('reconnect', () => {
      console.log('MQTT client reconnecting...');
    });

    this.mqttClient.on('message', (topic, message) => {
      this.handleMqttMessage(topic, message);
    });
  }

  handleMqttMessage(topic, message) {
    // Add detailed logging for all incoming MQTT messages
    console.log(`📨 [MQTT IN] Received message on topic: ${topic}`);
    console.log(`📨 [MQTT IN] Message length: ${message.length} bytes`);

    try {
      const payload = JSON.parse(message.toString());
      const topicParts = topic.split('/');

      console.log(`📨 [MQTT IN] Parsed payload:`, JSON.stringify(payload, null, 2));
      console.log(`📨 [MQTT IN] Topic parts:`, topicParts);

      if (topic === 'internal/server-ingest') {
        // Handle messages republished by EMQX with client ID info
        console.log(`📨 [MQTT IN] Message from internal/server-ingest topic`);

        // Extract client ID and original payload from EMQX republish rule
        const clientId = payload.sender_client_id;
        const originalPayload = payload.orginal_payload;

        if (!clientId || !originalPayload) {
          console.error(`❌ [MQTT IN] Invalid republished message format - missing clientId or originalPayload`);
          return;
        }

        console.log(`📨 [MQTT IN] Client ID: ${clientId}`);
        console.log(`📨 [MQTT IN] Original payload:`, JSON.stringify(originalPayload, null, 2));

        // Extract device MAC from client ID
        let deviceId = 'unknown-device';
        const parts = clientId.split('@@@');
        if (parts.length >= 2) {
          deviceId = parts[1].replace(/_/g, ':'); // Convert MAC format
        }

        console.log(`📨 [MQTT IN] Device message from internal/server-ingest - Device: ${deviceId}, Message type: ${originalPayload.type}`);

        // Create enhanced payload with client connection info for VirtualMQTTConnection
        const enhancedPayload = {
          ...originalPayload,
          clientId: clientId,
          username: 'extracted_from_emqx',
          password: 'extracted_from_emqx'
        };

        if (originalPayload.type === 'hello') {
          console.log(`👋 [HELLO] Processing hello message from internal/server-ingest: ${deviceId}`);
          this.handleDeviceHello(deviceId, enhancedPayload);
        } else {
          console.log(`📊 [DATA] Processing data message from internal/server-ingest: ${deviceId}`);
          this.handleDeviceData(deviceId, enhancedPayload);
        }
      } else if (topicParts.length >= 3 && topicParts[0] === 'devices') {
        const deviceId = topicParts[1];
        const messageType = topicParts[2];

        console.log(`📨 [MQTT IN] Device message - Device: ${deviceId}, Type: ${messageType}`);
        debug(`📨 Received MQTT message from device ${deviceId}: ${messageType}`);

        if (messageType === 'hello') {
          console.log(`👋 [HELLO] Processing hello message from device: ${deviceId}`);
          this.handleDeviceHello(deviceId, payload);
        } else if (messageType === 'data') {
          console.log(`📊 [DATA] Processing data message from device: ${deviceId}`);
          this.handleDeviceData(deviceId, payload);
        } else {
          console.log(`❓ [UNKNOWN] Unknown message type '${messageType}' from device: ${deviceId}`);
        }
      } else {
        console.log(`❓ [MQTT IN] Message on unexpected topic format: ${topic}`);
      }
    } catch (error) {
      console.error('❌ [MQTT IN] Error processing MQTT message:', error);
      console.log(`📨 [MQTT IN] Raw message:`, message.toString());
    }
  }

  handleDeviceHello(deviceId, payload) {
    console.log(`📱 [HELLO] handleDeviceHello called for device: ${deviceId}`);

    // Create a virtual connection for this device
    const connectionId = this.generateNewConnectionId();
    console.log(`📱 [HELLO] Generated connection ID: ${connectionId}`);

    const virtualConnection = new VirtualMQTTConnection(deviceId, connectionId, this, payload);
    console.log(`📱 [HELLO] Created VirtualMQTTConnection for device: ${deviceId}`);

    this.connections.set(connectionId, virtualConnection);
    this.deviceConnections.set(deviceId, { connectionId, connection: virtualConnection });

    console.log(`📱 [HELLO] Device ${deviceId} connected via EMQX`);
    console.log(`📱 [HELLO] Now calling handlePublish to process hello message...`);

    // Manually trigger the hello message processing
    try {
      virtualConnection.handlePublish({ payload: JSON.stringify(payload) });
      console.log(`📱 [HELLO] Successfully called handlePublish for device: ${deviceId}`);
    } catch (error) {
      console.error(`❌ [HELLO] Error in handlePublish for device ${deviceId}:`, error);
    }
  }

  handleDeviceData(deviceId, payload) {
    const deviceInfo = this.deviceConnections.get(deviceId);
    if (deviceInfo && deviceInfo.connection) {
      deviceInfo.connection.handlePublish({ payload: JSON.stringify(payload) });
    } else {
      console.warn(`📱 Received data from unknown device: ${deviceId}`);
    }
  }

  publishToDevice(clientIdOrDeviceId, message) {
  console.log(`📤 [MQTT OUT] publishToDevice called - Client/Device: ${clientIdOrDeviceId}`);
  console.log(`📤 [MQTT OUT] Message:`, JSON.stringify(message, null, 2));

  if (this.mqttClient && this.mqttClient.connected) {
    // Use the full client ID directly in the topic
    const topic = `devices/p2p/${clientIdOrDeviceId}`;
    console.log(`📤 [MQTT OUT] Publishing to topic: ${topic}`);

    this.mqttClient.publish(topic, JSON.stringify(message), (err) => {
      if (err) {
        console.error(`❌ [MQTT OUT] Failed to publish to client ${clientIdOrDeviceId}:`, err);
      } else {
        console.log(`✅ [MQTT OUT] Successfully published to client ${clientIdOrDeviceId} on topic ${topic}`);
        debug(`📤 Published to client ${clientIdOrDeviceId}: ${JSON.stringify(message)}`);
      }
    });
  } else {
    console.error('❌ [MQTT OUT] MQTT client not connected, cannot publish message');
    console.log(`📊 [MQTT OUT] Client connected: ${this.mqttClient ? this.mqttClient.connected : 'null'}`);
  }
}

  /**
   * Set up global heartbeat check timer
   */
  setupKeepAliveTimer() {
    // Clear existing timer
    this.clearKeepAliveTimer();
    this.lastConnectionCount = 0;
    this.lastActiveConnectionCount = 0;

    // Set new timer
    this.keepAliveTimer = setInterval(async () => {
      // Check heartbeat status of all connections
      for (const connection of this.connections.values()) {
        await connection.checkKeepAlive();
      }

      const activeCount = Array.from(this.connections.values()).filter(
        (connection) => connection.isAlive()
      ).length;
      if (
        activeCount !== this.lastActiveConnectionCount ||
        this.connections.size !== this.lastConnectionCount
      ) {
        // console.log(
        //   `Connections: ${this.connections.size}, Active: ${activeCount}`
        // );
        this.lastActiveConnectionCount = activeCount;
        this.lastConnectionCount = this.connections.size;
      }
    }, this.keepAliveCheckInterval);
  }

  /**
   * Clear heartbeat check timer
   */
  clearKeepAliveTimer() {
    if (this.keepAliveTimer) {
      clearInterval(this.keepAliveTimer);
      this.keepAliveTimer = null;
    }
  }

  addConnection(connection) {
    // Check if a connection with the same clientId already exists
    for (const [key, value] of this.connections.entries()) {
      if (value.clientId === connection.clientId) {
        debug(
          `${connection.clientId} connection already exists, closing old connection`
        );
        value.close();
      }
    }
    this.connections.set(connection.connectionId, connection);
  }

  removeConnection(connection) {
    debug(`Closing connection: ${connection.connectionId}`);
    if (this.connections.has(connection.connectionId)) {
      this.connections.delete(connection.connectionId);
    }
  }

  sendUdpMessage(message, remoteAddress) {
    this.udpServer.send(message, remoteAddress.port, remoteAddress.address);
  }

  onUdpMessage(message, rinfo) {
    // message format: [type: 1u, flag: 1u, payloadLength: 2u, cookie: 4u, timestamp: 4u, sequence: 4u, payload: n]
    if (message.length < 16) {
      //console.warn(
      //`📡 [UDP SERVER] Received incomplete UDP header from ${rinfo.address}:${rinfo.port}, length=${message.length}`
      // );
      return;
    }

    try {
      const type = message.readUInt8(0);
      if (type !== 1) {
        // console.warn(
        //   `📡 [UDP SERVER] Invalid packet type: ${type} from ${rinfo.address}:${rinfo.port}`
        // );
        return;
      }

      const payloadLength = message.readUInt16BE(2);
      if (message.length < 16 + payloadLength) {
        // console.warn(
        //   `📡 [UDP SERVER] Incomplete message from ${rinfo.address}:${rinfo.port}, expected=${16 + payloadLength}, got=${message.length}`
        // );
        return;
      }

      const connectionId = message.readUInt32BE(4);
      const connection = this.connections.get(connectionId);
      if (!connection) {
        // console.warn(`📡 [UDP SERVER] No connection found for ID: ${connectionId} from ${rinfo.address}:${rinfo.port}`);
        return;
      }

      const timestamp = message.readUInt32BE(8);
      const sequence = message.readUInt32BE(12);

      // console.log(
      //   `📡 [UDP SERVER] Routing message to connection ${connectionId} (${connection.clientId})`
      // );
      connection.onUdpMessage(
        rinfo,
        message,
        payloadLength,
        timestamp,
        sequence
      );
    } catch (error) {
      // console.error(
      //   `📡 [UDP SERVER] Message processing error from ${rinfo.address}:${rinfo.port}:`,
      //   error
      // );
    }
  }

  /**
   * Stop server
   */
  async stop() {
    if (this.stopping) {
      return;
    }

    this.stopping = true;
    // Clear heartbeat check timer
    this.clearKeepAliveTimer();

    if (this.connections.size > 0) {
      console.warn(`Waiting for ${this.connections.size} connections to close`);
      for (const connection of this.connections.values()) {
        connection.close();
      }
    }

    await new Promise((resolve) => setTimeout(resolve, 300));
    debug("Waiting for connections to close");
    this.connections.clear();
    this.deviceConnections.clear();

    if (this.udpServer) {
      this.udpServer.close();
      this.udpServer = null;
      console.warn("UDP server stopped");
    }

    // Close MQTT client
    if (this.mqttClient) {
      this.mqttClient.end();
      this.mqttClient = null;
      console.warn("MQTT client disconnected");
    }

    process.exit(0);
  }
}

// Create and start gateway
const gateway = new MQTTGateway();
gateway.start();

process.on("SIGINT", () => {
  console.warn("Received SIGINT signal, starting shutdown");
  gateway.stop();
});
