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
const { AccessToken, RoomServiceClient } = require("livekit-server-sdk");
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
// Import Opus Encoder and Decoder with fallback chain
let OpusEncoder, OpusDecoder, OpusApplication;
let opusLib = null;

// Try @voicehype/audify-plus first
try {
  const audifyPlus = require("@voicehype/audify-plus");
  OpusEncoder = audifyPlus.OpusEncoder;
  OpusDecoder = audifyPlus.OpusDecoder;
  OpusApplication = audifyPlus.OpusApplication;
  opusLib = "audify-plus";
  console.log("✅ [OPUS] audify-plus package loaded successfully");
} catch (err) {
  console.log("⚠️ [OPUS] audify-plus not available:", err.message);

  // Fallback to @discordjs/opus
  try {
    const discordOpus = require("@discordjs/opus");
    // Discord opus has OpusEncoder class
    OpusEncoder = discordOpus.OpusEncoder;
    OpusDecoder = discordOpus.OpusEncoder; // Discord opus uses same class for encoding/decoding
    OpusApplication = { OPUS_APPLICATION_AUDIO: "audio" }; // Discord opus doesn't expose this
    opusLib = "@discordjs/opus";
    console.log("✅ [OPUS] @discordjs/opus package loaded successfully");
  } catch (err2) {
    console.log("⚠️ [OPUS] @discordjs/opus not available:", err2.message);
    console.log(
      "⚠️ [OPUS] No Opus library available, operating in PCM mode only"
    );
    OpusEncoder = null;
    OpusDecoder = null;
    OpusApplication = null;
  }
}

// Initialize Opus encoder for 24kHz mono (outgoing), decoder for 16kHz mono (incoming)
let opusEncoder = null;
let opusDecoder = null;
// Define constants for audio parameters
const OUTGOING_SAMPLE_RATE = 24000; // Hz - for LiveKit → ESP32
const INCOMING_SAMPLE_RATE = 16000; // Hz - for ESP32 → LiveKit
const CHANNELS = 1; // Mono
const OUTGOING_FRAME_DURATION_MS = 60; // 60ms frames for outgoing (LiveKit → ESP32)
const INCOMING_FRAME_DURATION_MS = 60; // 20ms frames for incoming (ESP32 → LiveKit)
const OUTGOING_FRAME_SIZE_SAMPLES =
  (OUTGOING_SAMPLE_RATE * OUTGOING_FRAME_DURATION_MS) / 1000; // 24000 * 60 / 1000 = 1440
const INCOMING_FRAME_SIZE_SAMPLES =
  (INCOMING_SAMPLE_RATE * INCOMING_FRAME_DURATION_MS) / 1000; // 16000 * 20 / 1000 = 320
const OUTGOING_FRAME_SIZE_BYTES = OUTGOING_FRAME_SIZE_SAMPLES * 2; // 1440 samples * 2 bytes/sample = 2880 bytes PCM
const INCOMING_FRAME_SIZE_BYTES = INCOMING_FRAME_SIZE_SAMPLES * 2; // 320 samples * 2 bytes/sample = 640 bytes PCM

if (OpusEncoder && OpusDecoder) {
  try {
    if (opusLib === "audify-plus") {
      // audify-plus API: new OpusEncoder(sampleRate, channels, application)
      opusEncoder = new OpusEncoder(
        24000,
        1,
        OpusApplication.OPUS_APPLICATION_AUDIO
      );
      opusDecoder = new OpusDecoder(16000, 1);
      console.log(
        "✅ [OPUS] audify-plus encoder/decoder initialized - encoder: 24kHz, decoder: 16kHz mono"
      );
    } else if (opusLib === "@discordjs/opus") {
      // @discordjs/opus API: new OpusEncoder(sampleRate, channels)
      opusEncoder = new OpusEncoder(24000, 1);
      opusDecoder = new OpusDecoder(16000, 1);
      console.log(
        "✅ [OPUS] @discordjs/opus encoder/decoder initialized - encoder: 24kHz, decoder: 16kHz mono"
      );
    }
  } catch (err) {
    console.error(
      `❌ [OPUS] Failed to initialize ${opusLib} encoder/decoder:`,
      err.message
    );
    opusEncoder = null;
    opusDecoder = null;
    // Fallback: Disable Opus if init fails (will fall back to PCM)
  }
} else {
  console.log(
    "⚠️ [OPUS] Opus classes not available, operating in PCM mode only"
  );
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

// Loop State Manager for continuous playback (plays ANY random content)
class LoopStateManager {
  constructor() {
    this.loopStates = new Map(); // macAddress -> { loopEnabled, contentType }
  }

  setLoopState(macAddress, loopEnabled, contentType) {
    if (loopEnabled) {
      this.loopStates.set(macAddress, {
        loopEnabled: true,
        contentType,
        timestamp: Date.now(),
      });
      console.log(
        `🔁 [LOOP] Loop state enabled for ${macAddress} - Type: ${contentType} (ANY random content)`
      );
    } else {
      this.loopStates.delete(macAddress);
      console.log(`🔁 [LOOP] Loop state cleared for ${macAddress}`);
    }
  }

  getLoopState(macAddress) {
    return this.loopStates.get(macAddress) || null;
  }

  clearLoopState(macAddress) {
    this.loopStates.delete(macAddress);
    console.log(`🔁 [LOOP] Loop state cleared for ${macAddress}`);
  }

  isLoopEnabled(macAddress) {
    const state = this.loopStates.get(macAddress);
    return state?.loopEnabled || false;
  }
}

// Global loop state manager instance
const loopStateManager = new LoopStateManager();

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

    // Add agent join tracking
    this.agentJoined = false;
    this.agentJoinPromise = null;
    this.agentJoinResolve = null;
    this.agentJoinTimeout = null;

    // Create a promise that resolves when agent joins
    this.agentJoinPromise = new Promise((resolve) => {
      this.agentJoinResolve = resolve;
    });

    // Initialize audio resampler for 48kHz -> 24kHz conversion (outgoing: LiveKit -> ESP32)
    this.audioResampler = new AudioResampler(
      48000,
      24000,
      1,
      AudioResamplerQuality.QUICK
    );

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
    // console.log(`🔍 [PROCESS] processBufferedFrames called: buffer=${this.frameBuffer.length}B, target=${this.targetFrameBytes}B, connection=${this.connection ? 'exists' : 'null'}`);

    if (!this.connection) {
      console.error(`❌ [PROCESS] No connection available, cannot send audio`);
      return;
    }

    while (this.frameBuffer.length >= this.targetFrameBytes) {
      // Extract one complete frame
      const frameData = this.frameBuffer.slice(0, this.targetFrameBytes);
      this.frameBuffer = this.frameBuffer.slice(this.targetFrameBytes);

      // Process this complete frame - encode to Opus before sending
      if (frameData.length > 0) {
        const samples = new Int16Array(
          frameData.buffer,
          frameData.byteOffset,
          frameData.length / 2
        );
        const isSilent = samples.every((sample) => sample === 0);
        const maxAmplitude = Math.max(...samples.map((s) => Math.abs(s)));
        const isNearlySilent = maxAmplitude < 10;

        // DEBUG: Log first few samples to see what we're receiving
        if (frameCount <= 5) {
          console.log(
            `🔍 [DEBUG] Frame ${frameCount}: samples=${
              samples.length
            }, max=${maxAmplitude}, first10=[${Array.from(
              samples.slice(0, 10)
            ).join(",")}]`
          );
        }

        if (isSilent || isNearlySilent) {
          if (frameCount <= 5) {
            console.log(
              `🔇 [PCM] Silent frame ${frameCount} detected (max=${maxAmplitude}), skipping`
            );
          }
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
            const opusBuffer = opusEncoder.encode(
              alignedBuffer,
              this.targetFrameSize
            );

            if (frameCount <= 3 || frameCount % 100 === 0) {
              console.log(
                `🎵 [OPUS] Frame ${frameCount}: 24kHz 60ms PCM ${frameData.length}B → Opus ${opusBuffer.length}B`
              );
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
    const connectStartTime = Date.now();
    console.log(
      `🔍 [DEBUG] LiveKitBridge.connect() called - UUID: ${this.uuid}, MAC: ${this.macAddress}`
    );
    console.log(
      `⏱️ [TIMING-START] Connection initiated at ${connectStartTime}`
    );
    const { url, api_key, api_secret } = this.livekitConfig;
    // Include MAC address in room name for agent to extract device-specific prompt
    const macForRoom = this.macAddress.replace(/:/g, ""); // Remove colons: 00:16:3e:ac:b5:38 → 00163eacb538
    const roomName = `${this.uuid}_${macForRoom}`;
    const participantName = this.macAddress;

    console.log(
      `🏠 [ROOM] Creating room with name: ${roomName} (UUID: ${this.uuid}, MAC: ${this.macAddress})`
    );

    const at = new AccessToken(api_key, api_secret, {
      identity: participantName,
      // Add MAC address as custom attributes
      attributes: {
        device_mac: this.macAddress,
        device_uuid: this.uuid || "",
        room_type: "device_session",
      },
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
      // CRITICAL: Clear audio flag on disconnect to prevent stuck state
      this.isAudioPlaying = false;
      console.log(
        `🎵 [CLEANUP] Cleared audio flag on room disconnect for device: ${this.macAddress}`
      );
      // Clear loop state on disconnect
      loopStateManager.clearLoopState(this.macAddress);
    });

    this.room.on(
      RoomEvent.DataReceived,
      (payload, participant, kind, topic) => {
        try {
          const str = Buffer.from(payload).toString("utf-8");
          let data;
          try {
            data = JSON5.parse(str);
            console.log(
              `📨 [DATA RECEIVED] Topic: ${topic}, Type: ${data?.type}, Data:`,
              data
            );
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
                console.log(
                  `🎵 [AUDIO-STOP] TTS stopped for device: ${this.macAddress}`
                );
                // Send TTS stop message to device
                this.sendTtsStopMessage();

                // If we're in ending phase, send goodbye MQTT message now that TTS finished
                if (
                  this.connection &&
                  this.connection.isEnding &&
                  !this.connection.goodbyeSent
                ) {
                  console.log(
                    `👋 [END-COMPLETE] TTS goodbye finished, sending goodbye MQTT message to device: ${this.macAddress}`
                  );
                  this.connection.goodbyeSent = true;
                  this.connection.sendMqttMessage(
                    JSON.stringify({
                      type: "goodbye",
                      session_id: this.connection.udp
                        ? this.connection.udp.session_id
                        : null,
                      reason: "inactivity_timeout",
                      timestamp: Date.now(),
                    })
                  );
                  console.log(
                    `👋 [GOODBYE-MQTT] Sent goodbye MQTT message after TTS completed: ${this.macAddress}`
                  );

                  // Close connection shortly after goodbye message
                  setTimeout(() => {
                    if (this.connection) {
                      this.connection.close();
                    }
                  }, 500); // Small delay to ensure goodbye message is delivered
                }
              } else if (
                data.data.old_state === "listening" &&
                data.data.new_state === "thinking"
              ) {
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
                console.log(
                  `🎵 [AUDIO-START] TTS started, timer reset for device: ${this.macAddress}`
                );
              }
              // Send TTS start message to device
              this.sendTtsStartMessage(data.data.text);
              break;
            case "device_control":
              // Convert device_control commands to MCP function calls
              console.log(
                `🎛️ [DEVICE CONTROL] Received action: ${data.action}`
              );
              this.convertDeviceControlToMcp(data);
              break;
            case "function_call":
              // Handle xiaozhi function calls (volume controls, etc.)
              console.log(
                `🔧 [FUNCTION CALL] Received function: ${data.function_call?.name}`
              );
              this.handleFunctionCall(data);
              break;
            case "mobile_music_request":
              // Handle music play request from mobile app
              console.log(
                `🎵 [MOBILE] Music play request received from mobile app`
              );
              console.log(`   📱 Device: ${this.macAddress}`);
              console.log(`   🎵 Song: ${data.song_name}`);
              console.log(`   🗂️ Type: ${data.content_type}`);
              console.log(
                `   🌐 Language: ${data.language || "Not specified"}`
              );
              this.handleMobileMusicRequest(data);
              break;
            case "music_playback_started":
              // Handle music playback started
              console.log(
                `🎵 [MUSIC-START] Music playback started for device: ${this.macAddress}`
              );
              // Forward to mobile app
              this.forwardPlaybackStatusToMobile("playing", data.title || "");
              break;
            case "music_playback_stopped":
              // Handle music playback stopped - force clear audio playing flag
              console.log(
                `🎵 [MUSIC-STOP] Music playback stopped for device: ${this.macAddress}`
              );
              this.isAudioPlaying = false;
              // Send TTS stop message to ensure device returns to listening state
              this.sendTtsStopMessage();
              // Forward to mobile app
              this.forwardPlaybackStatusToMobile("stopped");
              break;
            case "mobile_stop_loop":
            case "stop_loop":
              // Handle stop loop request from mobile app
              console.log(
                `🔁 [LOOP-STOP] Stop loop request received for device: ${this.macAddress}`
              );
              // Clear loop state
              loopStateManager.clearLoopState(this.macAddress);
              // Forward stop_audio function call to LiveKit agent
              this.handleStopLoopRequest();
              break;
            case "llm":
              // Handle emotion from LLM response
              console.log(
                `😊 [EMOTION] Received: ${data.emotion} (${data.text})`
              );
              this.sendEmotionMessage(data.text, data.emotion);
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
        const roomConnectedTime = Date.now();
        console.log(`✅ [ROOM] Connected to LiveKit room: ${roomName}`);
        console.log(
          `⏱️ [TIMING-ROOM] Room connection took ${
            roomConnectedTime - connectStartTime
          }ms`
        );
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

              // Proactively send TTS start when agent audio track appears
              try {
                console.log(
                  `🔊 [TRACK] Agent audio track ready, sending TTS start to device: ${this.macAddress}`
                );
                this.sendTtsStartMessage();
                this.isAudioPlaying = true;
              } catch (error) {
                console.error(`❌ [TTS START] Error in track handler: ${error.message}`);
              }

              const stream = new AudioStream(track);
              const reader = stream.getReader();

              let frameCount = 0;
              let totalBytes = 0;
              let lastLogTime = Date.now();

              // Silence detection for TTS stop
              const SILENCE_TIMEOUT = 1500; // 1.5 seconds of silence = agent done speaking
              const AUDIO_THRESHOLD = 0.01; // RMS amplitude threshold for detecting actual audio
              let silenceTimer = null;

              // Detect if audio buffer contains actual audio vs silence
              const hasAudioContent = (audioBuffer) => {
                try {
                  if (!audioBuffer || audioBuffer.length === 0) return false;

                  const samples = new Int16Array(
                    audioBuffer.buffer,
                    audioBuffer.byteOffset,
                    audioBuffer.byteLength / 2
                  );

                  let sumSquares = 0;
                  for (let i = 0; i < samples.length; i++) {
                    const normalized = samples[i] / 32768.0;
                    sumSquares += normalized * normalized;
                  }

                  const rms = Math.sqrt(sumSquares / samples.length);
                  return rms > AUDIO_THRESHOLD;
                } catch (error) {
                  console.error(`❌ [AUDIO DETECT] Error: ${error.message}`);
                  return false;
                }
              };

              const sendTtsStopAfterSilence = () => {
                try {
                  if (silenceTimer) clearTimeout(silenceTimer);

                  silenceTimer = setTimeout(() => {
                    try {
                      if (this.isAudioPlaying) {
                        console.log(
                          `🔇 [SILENCE] No audio for ${SILENCE_TIMEOUT}ms, sending TTS stop to device: ${this.macAddress}`
                        );
                        this.sendTtsStopMessage();
                        this.isAudioPlaying = false;
                      }
                    } catch (error) {
                      console.error(`❌ [SILENCE] Error in timeout: ${error.message}`);
                    }
                  }, SILENCE_TIMEOUT);
                } catch (error) {
                  console.error(`❌ [SILENCE] Error setting timeout: ${error.message}`);
                }
              };

              const readStream = async () => {
                try {
                  console.log(
                    `🎧 [AUDIO STREAM] Starting to read audio frames from ${participant.identity}`
                  );

                  while (true) {
                    const { done, value } = await reader.read();
                    if (done) {
                      try {
                        if (silenceTimer) clearTimeout(silenceTimer);
                        this.sendTtsStopMessage();
                      } catch (error) {
                        console.error(`❌ [STREAM END] Error: ${error.message}`);
                      }
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
                        this.frameBuffer = Buffer.concat([
                          this.frameBuffer,
                          finalBuffer,
                        ]);
                      }

                      // Process any remaining complete frames in buffer
                      const finalTimestamp =
                        (Date.now() - this.connection.udp.startTime) &
                        0xffffffff;
                      this.processBufferedFrames(
                        finalTimestamp,
                        frameCount,
                        participant.identity
                      );

                      // SKIP partial frames - they cause Opus encoder to crash
                      // Opus encoder requires exact frame sizes, partial frames will be dropped
                      if (this.frameBuffer.length > 0) {
                        console.log(
                          `⏭️ [FLUSH] Skipping partial frame (${this.frameBuffer.length}B) - would cause Opus crash`
                        );
                      }

                      // Clear the buffer
                      this.frameBuffer = Buffer.alloc(0);

                      // Notify connection that audio stream has ended
                      if (this.connection && this.connection.isEnding) {
                        console.log(
                          `✅ [END-COMPLETE] Audio stream completed, closing connection: ${
                            this.connection.clientId || this.connection.deviceId
                          }`
                        );
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
                      this.frameBuffer = Buffer.concat([
                        this.frameBuffer,
                        resampledBuffer,
                      ]);
                      totalBytes += resampledBuffer.length;
                    }

                    // Reset silence timer - but only for actual audio, not silence frames
                    try {
                      if (resampledFrames.length > 0) {
                        // Check if ANY of the resampled frames contain actual audio
                        let hasRealAudio = false;
                        for (const frame of resampledFrames) {
                          if (hasAudioContent(frame.data)) {
                            hasRealAudio = true;
                            break;
                          }
                        }

                        if (hasRealAudio) {
                          // If agent just started speaking (after silence), send TTS start
                          if (!this.isAudioPlaying) {
                            console.log(`🔊 [AUDIO] Agent started speaking, sending TTS start`);
                            this.sendTtsStartMessage();
                            this.isAudioPlaying = true;
                          }

                          console.log(`🔊 [AUDIO] Real audio detected, resetting silence timer`);
                          sendTtsStopAfterSilence();
                        }
                        // If no real audio, timer continues and will fire after timeout
                      }
                    } catch (error) {
                      console.error(`❌ [SILENCE CHECK] Error: ${error.message}`);
                    }

                    const timestamp =
                      (Date.now() - this.connection.udp.startTime) & 0xffffffff;

                    // Process any complete frames from the buffer
                    this.processBufferedFrames(
                      timestamp,
                      frameCount,
                      participant.identity
                    );

                    // Log every 50 frames or every 5 seconds
                    // const now = Date.now();
                    // if (frameCount % 50 === 0 || now - lastLogTime > 5000) {
                    //   console.log(
                    //     `🎵 [AUDIO FRAMES] Received ${frameCount} frames, ${totalBytes} total bytes from ${participant.identity}, buffer: ${this.frameBuffer.length}B`
                    //   );
                    //   lastLogTime = now;
                    // }
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
                `⚠️ [TRACK] Non-audio track subscribed: ${
                  track.kind
                } (type: ${typeof track.kind}) from ${participant.identity}`
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
          if (participant.identity.includes("agent")) {
            console.log(
              `🤖 [AGENT] Agent joined the room: ${participant.identity}`
            );

            // Set agent joined flag and resolve promise
            this.agentJoined = true;
            if (this.agentJoinResolve) {
              this.agentJoinResolve();
              console.log(`✅ [AGENT-READY] Agent join promise resolved`);
            }

            // Clear timeout if set
            if (this.agentJoinTimeout) {
              clearTimeout(this.agentJoinTimeout);
              this.agentJoinTimeout = null;
            }

            // Send initial greeting message to let user know agent is ready
            const greetingStartTime = Date.now();
            setTimeout(() => {
              const greetingEndTime = Date.now();
              console.log(
                `⏱️ [TIMING-GREETING] Greeting delay took ${
                  greetingEndTime - greetingStartTime
                }ms`
              );
              this.sendInitialGreeting();
            }, 300); // Reduced delay for faster response (optimized from 1000ms)
          }
        });

        this.room.on(RoomEvent.ParticipantDisconnected, (participant) => {
          console.log(
            `👤 [PARTICIPANT] Disconnected: ${participant.identity} (${participant.sid})`
          );
        });

        // Fixed: Use proper track publishing method (simplified to match dev branch)
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
        const trackPublishedTime = Date.now();
        console.log(
          `🎤 [PUBLISH] Published local audio track: ${
            publication.trackSid || publication.sid
          }`
        );
        console.log(
          `⏱️ [TIMING-TRACK] Track publish took ${
            trackPublishedTime - roomConnectedTime
          }ms`
        );

        // Use roomName as session_id - this is consistent with how LiveKit rooms work
        // The room.sid might not be immediately available, but roomName is our session identifier
        // Include audio_params that the client expects
        const totalConnectTime = Date.now() - connectStartTime;
        console.log(
          `⏱️ [TIMING-TOTAL] Total connection setup took ${totalConnectTime}ms`
        );
        resolve({
          session_id: roomName,
          audio_params: {
            sample_rate: 24000,
            channels: 1,
            frame_duration: 60,
            format: "opus",
          },
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
      console.warn(
        `⚠️ [AUDIO] Cannot send audio - audioSource or room not ready. Room connected: ${this.room?.isConnected}`
      );
      return;
    }

    try {
      // Check if data is Opus and decode it
      const isOpus = this.checkOpusFormat(opusData);

      // console.log(`🔍 [AUDIO] Detected format for incoming data: ${isOpus ? "Opus" : "PCM or Unknown"}`);
      if (isOpus) {
        if (opusDecoder) {
          try {
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

              // Safe capture with error handling
              this.safeCaptureFrame(frame).catch((err) => {
                console.error(
                  `❌ [AUDIO] Unhandled error in safeCaptureFrame: ${err.message}`
                );
              });
            }
          } catch (err) {
            console.error(`❌ [OPUS] Decode error: ${err.message}`);
          }
        } else {
          console.error(`❌ [ERROR] Opus decoder not available!`);
        }
      } else {
        // Treat as PCM
        const samples = new Int16Array(
          opusData.buffer,
          opusData.byteOffset,
          opusData.length / 2
        );
        const frame = new AudioFrame(samples, 16000, 1, samples.length);

        // Safe capture with error handling
        this.safeCaptureFrame(frame).catch((err) => {
          console.error(
            `❌ [AUDIO] Unhandled error in safeCaptureFrame: ${err.message}`
          );
        });
      }
    } catch (error) {
      console.error(`❌ [AUDIO] Error in sendAudio: ${error.message}`);
    }
  }

  async safeCaptureFrame(frame) {
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
      await this.audioSource.captureFrame(frame);
    } catch (error) {
      console.error(`❌ [AUDIO] Failed to capture frame: ${error.message}`);

      // If we get InvalidState error, try to reinitialize the audio source
      if (error.message.includes("InvalidState")) {
        console.log(
          `🔄 [AUDIO] Attempting to reinitialize AudioSource due to InvalidState`
        );
        try {
          this.audioSource = new AudioSource(16000, 1);
          console.log(`✅ [AUDIO] AudioSource reinitialized successfully`);
        } catch (reinitError) {
          console.error(
            `❌ [AUDIO] Failed to reinitialize AudioSource: ${reinitError.message}`
          );
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
      `   📋 First 16 bytes: ${audioData
        .slice(0, Math.min(16, audioData.length))
        .toString("hex")}`
    );
    console.log(
      `   🎼 Opus signature: ${isOpus ? "✅ DETECTED" : "❌ NOT FOUND"}`
    );
    console.log(
      `   🎤 PCM characteristics: ${
        isPCM ? "✅ LIKELY PCM" : "❌ UNLIKELY PCM"
      }`
    );

    // Additional analysis
    this.analyzeAudioStatistics(audioData);
  }

  checkOpusFormat(data) {
    if (data.length < 1) return false;

    // ESP32 sends 60ms OPUS frames at 16kHz mono with complexity=0
    const MIN_OPUS_SIZE = 1; // Minimum OPUS packet (can be very small for silence)
    const MAX_OPUS_SIZE = 400; // Maximum OPUS packet for 60ms@16kHz

    // Validate packet size range
    if (data.length < MIN_OPUS_SIZE || data.length > MAX_OPUS_SIZE) {
      console.log(
        `❌ Invalid OPUS size: ${data.length}B (expected ${MIN_OPUS_SIZE}-${MAX_OPUS_SIZE}B)`
      );
      return false;
    }

    // Check OPUS TOC (Table of Contents) byte
    const firstByte = data[0];
    const config = (firstByte >> 3) & 0x1f; // Bits 7-3: config (0-31)
    const stereo = (firstByte >> 2) & 0x01; // Bit 2: stereo flag
    const frameCount = firstByte & 0x03; // Bits 1-0: frame count

    // console.log(`🔍 OPUS TOC: config=${config}, stereo=${stereo}, frames=${frameCount}, size=${data.length}B`);

    // Validate OPUS TOC byte
    const validConfig = config >= 0 && config <= 31;
    const validStereo = stereo === 0; // ESP32 sends mono (stereo=0)
    const validFrameCount = frameCount >= 0 && frameCount <= 3;

    // ✅ FIXED: Accept ALL valid OPUS configs (0-31) for ESP32 with complexity=0
    // ESP32 with complexity=0 can use various configs depending on audio content
    const validOpusConfigs = [
      0,
      1,
      2,
      3,
      4,
      5,
      6,
      7,
      8,
      9,
      10,
      11,
      12,
      13,
      14,
      15, // NB/MB/WB configs
      16,
      17,
      18,
      19, // SWB configs
      20,
      21,
      22,
      23, // FB configs
      24,
      25,
      26,
      27,
      28,
      29,
      30,
      31, // Hybrid configs
    ];
    const isValidConfig = validOpusConfigs.includes(config);

    // ✅ FIXED: More lenient validation - just check basic OPUS structure
    const isValidOpus =
      validConfig && validStereo && validFrameCount && isValidConfig;

    // console.log(`📊 OPUS validation: config=${validConfig}(${config}), mono=${validStereo}, frames=${validFrameCount}, validConfig=${isValidConfig} → ${isValidOpus ? "✅ VALID" : "❌ INVALID"}`);

    // ✅ ADDITIONAL: Log first few bytes for debugging
    if (!isValidOpus) {
      const hexDump = data.slice(0, Math.min(8, data.length)).toString("hex");
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
  sendTtsStartMessage() {
    try {
      if (!this.connection) {
        console.warn(`⚠️ [TTS START] No connection for device: ${this.macAddress}`);
        return;
      }

      const message = {
        type: "tts",
        state: "start",
        session_id: this.connection.udp.session_id,
        timestamp: Date.now()
      };

      console.log(`📢 [TTS START] Transition device to SPEAKING state: ${this.macAddress}`);
      this.connection.sendMqttMessage(JSON.stringify(message));
    } catch (error) {
      console.error(`❌ [TTS START] Error sending message: ${error.message}`);
    }
  }

  sendTtsStopMessage() {
    try {
      if (!this.connection) {
        console.warn(`⚠️ [TTS STOP] No connection for device: ${this.macAddress}`);
        return;
      }

      const message = {
        type: "tts",
        state: "stop",
        session_id: this.connection.udp.session_id,
      };

      console.log(`📤 [MQTT OUT] Sending TTS stop to device: ${this.macAddress}`);
      this.connection.sendMqttMessage(JSON.stringify(message));
    } catch (error) {
      console.error(`❌ [TTS STOP] Error sending message: ${error.message}`);
    }
  }

  sendLLMThinkMessage() {
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

  // Send emotion message to device (from LLM response)
  sendEmotionMessage(emoji, emotion) {
    if (!this.connection) return;

    const message = {
      type: "llm",
      text: emoji,
      emotion: emotion,
      session_id: this.connection.udp.session_id,
    };

    console.log(
      `📤 [MQTT OUT] Sending emotion to device: ${this.macAddress} - ${emotion} (${emoji})`
    );
    this.connection.sendMqttMessage(JSON.stringify(message));
  }

  // Forward playback status to mobile app via MQTT
  forwardPlaybackStatusToMobile(status, title = "") {
    if (!this.connection || !this.connection.server) return;

    const appTopic = `app/p2p/${this.macAddress}`;
    const statusMessage = {
      type: "playback_status",
      status: status,
      title: title,
      timestamp: Date.now(),
    };

    // Access the MQTT client from the server instance
    const mqttClient = this.connection.server.mqttClient;
    if (mqttClient && mqttClient.connected) {
      mqttClient.publish(appTopic, JSON.stringify(statusMessage), (err) => {
        if (err) {
          console.error(`❌ [MOBILE] Failed to send playback status: ${err}`);
        } else {
          console.log(`📱 [MOBILE] Sent playback ${status} to ${appTopic}`);
        }
      });
    }
  }

  // Convert device_control commands to MCP function calls
  convertDeviceControlToMcp(controlData) {
    if (!this.connection) return;

    const action = controlData.action || controlData.command;

    // Map device control actions to xiaozhi function names
    const actionToFunctionMap = {
      set_volume: "self_set_volume",
      volume_up: "self_volume_up",
      volume_down: "self_volume_down",
      get_volume: "self_get_volume",
      mute: "self_mute",
      unmute: "self_unmute",
      set_light_color: "self_set_light_color",
      get_battery_status: "self_get_battery_status",
      set_light_mode: "self_set_light_mode",
      set_rainbow_speed: "self_set_rainbow_speed",
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
        arguments: functionArguments,
      },
      timestamp: controlData.timestamp || new Date().toISOString(),
      request_id: controlData.request_id || `req_${Date.now()}`,
    };

    console.log(
      `🔄 [DEVICE CONTROL] Converting to MCP: ${action} -> ${functionName}, Args: ${JSON.stringify(
        functionArguments
      )}`
    );

    // Use existing handleFunctionCall method to send as MCP format
    this.handleFunctionCall(functionCallData);
  }

  // Handle xiaozhi function calls (volume controls, etc.)
  handleFunctionCall(functionData) {
    if (!this.connection) return;

    const functionCall = functionData.function_call;
    if (!functionCall || !functionCall.name) {
      console.error(
        `❌ [FUNCTION CALL] Invalid function call data:`,
        functionData
      );
      return;
    }

    // Map xiaozhi function names to MCP tool names for ESP32 firmware
    const functionToMcpToolMap = {
      self_set_volume: "self.audio_speaker.set_volume",
      self_get_volume: "self.get_device_status",
      self_volume_up: "self.audio_speaker.volume_up",
      self_volume_down: "self.audio_speaker.volume_down",
      self_mute: "self.audio_speaker.mute",
      self_unmute: "self.audio_speaker.unmute",
      self_set_light_color: "self.led.set_color",
      self_get_battery_status: "self.battery.get_status",
      self_set_light_mode: "self.led.set_mode",
      self_set_rainbow_speed: "self.led.set_rainbow_speed",
    };

    const mcpToolName = functionToMcpToolMap[functionCall.name];
    if (!mcpToolName) {
      console.log(
        `⚠️ [FUNCTION CALL] Unknown function: ${functionCall.name}, forwarding as MCP message`
      );
      // Forward unknown functions as MCP tool calls
      this.sendMcpMessage(functionCall.name, functionCall.arguments || {});
      return;
    }

    // Create MCP message format expected by ESP32 firmware (JSON-RPC 2.0)
    const requestId = parseInt(
      functionData.request_id?.replace("req_", "") || Date.now()
    );
    const message = {
      type: "mcp",
      payload: {
        jsonrpc: "2.0",
        method: "tools/call",
        params: {
          name: mcpToolName,
          arguments: functionCall.arguments || {},
        },
        id: requestId,
      },
      session_id: this.connection.udp.session_id,
      timestamp: functionData.timestamp || new Date().toISOString(),
      request_id: `req_${requestId}`,
    };

    console.log(
      `🔧 [MCP] Sending to device: ${
        this.macAddress
      } - Tool: ${mcpToolName}, Args: ${JSON.stringify(functionCall.arguments)}`
    );
    this.connection.sendMqttMessage(JSON.stringify(message));

    // Simulate device response for testing (remove in production)
    // setTimeout(() => {
    //   this.simulateFunctionCallResponse(functionData);
    // }, 100);
  }

  // Handle mobile app music play requests
  async handleMobileMusicRequest(requestData) {
    try {
      console.log(`🎵 [MOBILE] Processing music request...`);

      if (!this.room || !this.room.localParticipant) {
        console.error(`❌ [MOBILE] Room not connected, cannot forward request`);
        return;
      }

      // Determine function name based on content type
      const functionName =
        requestData.content_type === "story" ? "play_story" : "play_music";

      // Extract loop_enabled parameter (default to false)
      const loopEnabled = requestData.loop_enabled === true;

      // Prepare function arguments
      const functionArguments = {};

      if (requestData.content_type === "music") {
        // For music: song_name and language
        if (requestData.song_name) {
          functionArguments.song_name = requestData.song_name;
        }
        if (requestData.language) {
          functionArguments.language = requestData.language;
        }
        // Add loop_enabled parameter
        functionArguments.loop_enabled = loopEnabled;

        // Update loop state manager (will play ANY random music)
        loopStateManager.setLoopState(this.macAddress, loopEnabled, "music");
      } else if (requestData.content_type === "story") {
        // For stories: story_name and category
        if (requestData.song_name) {
          functionArguments.story_name = requestData.song_name;
        }
        if (requestData.language) {
          functionArguments.category = requestData.language;
        }
        // Add loop_enabled parameter
        functionArguments.loop_enabled = loopEnabled;

        // Update loop state manager (will play ANY random stories)
        loopStateManager.setLoopState(this.macAddress, loopEnabled, "story");
      }

      // Create function call message for LiveKit agent
      const functionCallMessage = {
        type: "function_call",
        function_call: {
          name: functionName,
          arguments: functionArguments,
        },
        source: "mobile_app",
        timestamp: Date.now(),
        request_id: `mobile_req_${Date.now()}`,
      };

      // Forward to LiveKit agent via data channel
      const messageString = JSON.stringify(functionCallMessage);
      const messageData = new Uint8Array(Buffer.from(messageString, "utf8"));

      await this.room.localParticipant.publishData(messageData, {
        reliable: true,
      });

      console.log(`✅ [MOBILE] Music request forwarded to LiveKit agent`);
      console.log(`   🎯 Function: ${functionName}`);
      console.log(`   📝 Arguments: ${JSON.stringify(functionArguments)}`);
      if (loopEnabled) {
        console.log(`   🔁 Loop mode: ENABLED`);
      }
    } catch (error) {
      console.error(
        `❌ [MOBILE] Failed to forward music request: ${error.message}`
      );
      console.error(`   Stack: ${error.stack}`);
    }
  }

  // Handle stop loop request from mobile app
  async handleStopLoopRequest() {
    try {
      console.log(`🔁 [LOOP-STOP] Processing stop loop request...`);

      if (!this.room || !this.room.localParticipant) {
        console.error(
          `❌ [LOOP-STOP] Room not connected, cannot forward request`
        );
        return;
      }

      // Create function call message to call stop_audio on LiveKit agent
      const functionCallMessage = {
        type: "function_call",
        function_call: {
          name: "stop_audio",
          arguments: {},
        },
        source: "mobile_app",
        timestamp: Date.now(),
        request_id: `stop_loop_${Date.now()}`,
      };

      // Forward to LiveKit agent via data channel
      const messageString = JSON.stringify(functionCallMessage);
      const messageData = new Uint8Array(Buffer.from(messageString, "utf8"));

      await this.room.localParticipant.publishData(messageData, {
        reliable: true,
      });

      console.log(`✅ [LOOP-STOP] Stop request forwarded to LiveKit agent`);
    } catch (error) {
      console.error(
        `❌ [LOOP-STOP] Failed to forward stop request: ${error.message}`
      );
      console.error(`   Stack: ${error.stack}`);
    }
  }

  // Send unknown function calls directly to device (deprecated - use sendMcpMessage)
  sendFunctionCallToDevice(functionData) {
    if (!this.connection) return;

    const message = {
      type: "function_call",
      function_call: functionData.function_call,
      session_id: this.connection.udp.session_id,
      timestamp: functionData.timestamp || new Date().toISOString(),
      request_id: functionData.request_id || `req_${Date.now()}`,
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
          arguments: toolArgs,
        },
        id: requestId,
      },
      session_id: this.connection.udp.session_id,
      timestamp: new Date().toISOString(),
      request_id: `req_${requestId}`,
    };

    console.log(
      `📤 [MCP] Sending MCP tool call to device: ${
        this.macAddress
      } - Tool: ${toolName}, Args: ${JSON.stringify(toolArgs)}`
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
        case "set_volume":
          currentValue = originalCommand.volume || originalCommand.value || 50;
          break;
        case "get_volume":
          currentValue = 65; // Simulated current volume
          break;
        case "volume_up":
          currentValue = Math.min(
            100,
            65 + (originalCommand.step || originalCommand.value || 10)
          );
          break;
        case "volume_down":
          currentValue = Math.max(
            0,
            65 - (originalCommand.step || originalCommand.value || 10)
          );
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
        session_id: originalCommand.session_id || "unknown",
      };

      // Send response back to agent via data channel
      const messageString = JSON.stringify(responseMessage);
      const messageData = new Uint8Array(Buffer.from(messageString, "utf8"));
      this.room.localParticipant.publishData(messageData, { reliable: true });

      console.log(
        `🎛️ [DEVICE RESPONSE] Simulated response: Action ${action}, Success: ${success}, Value: ${currentValue}`
      );
    } catch (error) {
      console.error(
        `❌ [DEVICE RESPONSE] Error simulating device response:`,
        error
      );
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
        case "self_set_volume":
          const volume = functionCall.arguments?.volume || 50;
          result = { new_volume: volume };
          break;
        case "self_get_volume":
          result = { current_volume: 65 }; // Simulated current volume
          break;
        case "self_volume_up":
          result = { new_volume: Math.min(100, 65 + 10) };
          break;
        case "self_volume_down":
          result = { new_volume: Math.max(0, 65 - 10) };
          break;
        case "self_mute":
          result = { muted: true, previous_volume: 65 };
          break;
        case "self_unmute":
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
        timestamp: new Date().toISOString(),
      };

      // Send response back to agent via data channel
      const messageString = JSON.stringify(responseMessage);
      const messageData = new Uint8Array(Buffer.from(messageString, "utf8"));
      this.room.localParticipant.publishData(messageData, { reliable: true });

      console.log(
        `🔧 [FUNCTION RESPONSE] Simulated response: Function ${
          functionCall.name
        }, Success: ${success}, Result: ${JSON.stringify(result)}`
      );
    } catch (error) {
      console.error(
        `❌ [FUNCTION RESPONSE] Error simulating function response:`,
        error
      );
    }
  }

  // Forward MCP response to LiveKit agent
  async forwardMcpResponse(mcpPayload, sessionId, requestId) {
    console.log(
      `🔋 [MCP-FORWARD] Forwarding MCP response for device ${this.macAddress}`
    );

    if (!this.room || !this.room.localParticipant) {
      console.error(
        `❌ [MCP-FORWARD] No room available for device ${this.macAddress}`
      );
      return false;
    }

    try {
      const responseMessage = {
        type: "mcp",
        payload: mcpPayload,
        session_id: sessionId,
        request_id: requestId,
        timestamp: new Date().toISOString(),
      };

      const messageString = JSON.stringify(responseMessage);
      const messageData = new Uint8Array(Buffer.from(messageString, "utf8"));

      await this.room.localParticipant.publishData(messageData, {
        reliable: true,
      });

      console.log(
        `✅ [MCP-FORWARD] Successfully forwarded MCP response to LiveKit agent`
      );
      console.log(`✅ [MCP-FORWARD] Request ID: ${requestId}`);
      return true;
    } catch (error) {
      console.error(`❌ [MCP-FORWARD] Error forwarding MCP response:`, error);
      return false;
    }
  }

  // Send LLM response to device
  sendLlmMessage(text) {
    if (!this.connection || !text) return;

    const message = {
      type: "llm",
      text: text,
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
        source: "mqtt_gateway",
      };

      // Send device info via LiveKit data channel
      if (this.room && this.room.localParticipant) {
        const deviceInfoString = JSON.stringify(deviceInfoMessage);
        const deviceInfoData = new Uint8Array(
          Buffer.from(deviceInfoString, "utf8")
        );
        await this.room.localParticipant.publishData(deviceInfoData, {
          reliable: true,
        });

        console.log(
          `📱 [DEVICE INFO] Sent device MAC (${this.macAddress}) to agent via data channel`
        );

        // Then send greeting trigger
        const initialMessage = {
          type: "agent_ready",
          message: "Say hello to the user",
          timestamp: Date.now(),
          source: "mqtt_gateway",
        };

        const messageString = JSON.stringify(initialMessage);
        const messageData = new Uint8Array(Buffer.from(messageString, "utf8"));
        await this.room.localParticipant.publishData(messageData, {
          reliable: true,
        });

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
        `❌ [AGENT READY] Error sending messages to agent for device ${this.macAddress}:`,
        error
      );
    }
  }

  /**
   * Wait for agent to join the room with timeout
   * @param {number} timeoutMs - Timeout in milliseconds (default: 4000)
   * @returns {Promise<boolean>} - true if agent joined, false if timeout
   */
  async waitForAgentJoin(timeoutMs = 4000) {
    // If agent already joined, return immediately
    if (this.agentJoined) {
      console.log(`✅ [AGENT-WAIT] Agent already joined`);
      return true;
    }

    console.log(
      `⏳ [AGENT-WAIT] Waiting for agent to join (timeout: ${timeoutMs}ms)...`
    );

    // Race between agent join and timeout
    const timeoutPromise = new Promise((resolve) => {
      this.agentJoinTimeout = setTimeout(() => {
        console.log(`⏰ [AGENT-WAIT] Timeout reached, proceeding anyway`);
        resolve(false);
      }, timeoutMs);
    });

    const result = await Promise.race([
      this.agentJoinPromise.then(() => true),
      timeoutPromise,
    ]);

    return result;
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
        source: "mqtt_gateway",
      };

      // Send via LiveKit data channel to the agent
      // Convert to Uint8Array as required by LiveKit Node SDK
      const messageString = JSON.stringify(abortMessage);
      const messageData = new Uint8Array(Buffer.from(messageString, "utf8"));
      await this.room.localParticipant.publishData(messageData, {
        reliable: true,
      });

      console.log(
        `🛑 [ABORT] Sent abort signal to LiveKit agent via data channel`
      );

      // CRITICAL: Clear the audio playing flag immediately when abort is sent
      this.isAudioPlaying = false;
      console.log(
        `🎵 [ABORT-CLEAR] Cleared audio playing flag for device: ${this.macAddress}`
      );
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
      console.log(
        `👋 [END-PROMPT] Room already disconnected, skipping end prompt`
      );
      return;
    }

    try {
      const endMessage = {
        type: "end_prompt",
        session_id: sessionId,
        prompt:
          "You must end this conversation now. Start with 'Time flies so fast' and say a SHORT goodbye in 1-2 sentences maximum. Do NOT ask questions or suggest activities. Just say goodbye emotionally and end the conversation.",
        timestamp: Date.now(),
        source: "mqtt_gateway",
      };

      // Send via LiveKit data channel to the agent
      // Convert to Uint8Array as required by LiveKit Node SDK
      const messageString = JSON.stringify(endMessage);
      const messageData = new Uint8Array(Buffer.from(messageString, "utf8"));
      await this.room.localParticipant.publishData(messageData, {
        reliable: true,
      });

      console.log(
        `👋 [END-PROMPT] Sent end prompt to LiveKit agent via data channel`
      );
    } catch (error) {
      console.error(`[LiveKitBridge] Failed to send end prompt:`, error);
      // Don't throw the error - just log it and continue with cleanup
      console.log(
        `👋 [END-PROMPT] Continuing with connection cleanup despite end prompt failure`
      );
    }
  }

  async close() {
    if (this.room) {
      console.log("[LiveKitBridge] Disconnecting from LiveKit room");

      // CRITICAL: Clear audio flag before disconnect to prevent stuck state
      this.isAudioPlaying = false;
      console.log(
        `🎵 [CLEANUP] Cleared audio flag on bridge close for device: ${this.macAddress}`
      );

      // Clear loop state on close
      loopStateManager.clearLoopState(this.macAddress);

      // First disconnect from the room
      await this.room.disconnect();

      // Send a final cleanup signal to ensure the agent side also cleans up
      try {
        const cleanupMessage = {
          type: "cleanup_request",
          session_id: this.connection.udp.session_id,
          timestamp: Date.now(),
          source: "mqtt_gateway",
        };

        if (this.room.localParticipant && this.room.isConnected) {
          const messageString = JSON.stringify(cleanupMessage);
          const messageData = new Uint8Array(
            Buffer.from(messageString, "utf8")
          );
          await this.room.localParticipant.publishData(messageData, {
            reliable: true,
          });
          console.log("🧹 Sent cleanup signal to agent before disconnect");
        }
      } catch (error) {
        console.log(
          "Note: Could not send cleanup signal (room already disconnected)"
        );
      }

      this.room = null;
    }
  }

  /**
   * Clean up all old LiveKit rooms for a specific MAC address
   * Finds and deletes ALL rooms ending with the MAC address pattern
   * This ensures no ghost sessions exist before creating a new one
   *
   * @param {string} macAddress - MAC address with colons (e.g., "28:56:2f:07:c6:ec")
   * @param {RoomServiceClient} roomService - LiveKit room service client
   */
  static async cleanupOldSessionsForDevice(
    macAddress,
    roomService,
    currentRoomName = null
  ) {
    try {
      // Convert MAC address format: "28:56:2f:07:c6:ec" → "28562f07c6ec"
      const macForRoom = macAddress.replace(/:/g, "");
      console.log(
        `🧹 [CLEANUP] Searching for old sessions for MAC: ${macAddress} (${macForRoom})`
      );
      if (currentRoomName) {
        console.log(
          `🔒 [CLEANUP] Protecting current room from deletion: ${currentRoomName}`
        );
      }

      // Safety check: Ensure roomService is available
      if (!roomService) {
        console.log(`⚠️ [CLEANUP] RoomService not available, skipping cleanup`);
        return;
      }

      // Get ALL active rooms from LiveKit server
      const allRooms = await roomService.listRooms();
      console.log(`📊 [CLEANUP] Found ${allRooms.length} total active rooms`);

      // Filter rooms belonging to this device (pattern: *_28562f07c6ec)
      // BUT exclude the current room being created
      const deviceRooms = allRooms.filter((room) => {
        if (!room.name || !room.name.endsWith(`_${macForRoom}`)) {
          return false;
        }

        // CRITICAL: Never delete the room we're currently creating
        if (currentRoomName && room.name === currentRoomName) {
          console.log(
            `   🔒 Skipping current room: ${room.name} (actively being used)`
          );
          return false;
        }

        return true;
      });

      if (deviceRooms.length > 0) {
        console.log(
          `🗑️ [CLEANUP] Found ${deviceRooms.length} old session(s) for MAC ${macAddress}:`
        );

        // Delete each old room
        for (const room of deviceRooms) {
          const roomCreationTime = Number(room.creationTime);
          const roomAge = now - roomCreationTime;
          console.log(
            `   - Deleting room: ${room.name} (${
              room.numParticipants
            } participants, age: ${roomAge.toFixed(0)}s)`
          );
          try {
            await roomService.deleteRoom(room.name);
            console.log(`   ✅ Successfully deleted room: ${room.name}`);
          } catch (deleteError) {
            console.error(
              `   ❌ Failed to delete room ${room.name}:`,
              deleteError.message
            );
            // Continue with other rooms even if one fails
          }
        }

        console.log(`✅ [CLEANUP] Completed cleanup for MAC ${macAddress}`);

        // Wait for cleanup to propagate on LiveKit server
        await new Promise((resolve) => setTimeout(resolve, 500));
      } else {
        console.log(`✓ [CLEANUP] No old sessions found for MAC: ${macAddress}`);
      }
    } catch (error) {
      console.error(
        `❌ [CLEANUP] Error cleaning up sessions for MAC ${macAddress}:`,
        error.message
      );
      // Don't throw - continue with connection attempt even if cleanup fails
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

    // CRITICAL: Clear audio playing flag to prevent stuck state
    if (this.bridge) {
      this.bridge.isAudioPlaying = false;
      console.log(
        `🎵 [CLEANUP] Cleared audio flag on close for device: ${this.clientId}`
      );
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
      console.log(
        `📱 [ENDING-IGNORE] Activity during goodbye sequence ignored for device: ${this.clientId}`
      );
      return; // Don't log timer reset during ending
    }

    console.log(
      `⏱️ [TIMER-RESET] Activity timer reset for device: ${
        this.clientId
      } at ${new Date().toISOString()}`
    );
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
        console.log(
          `🕒 [END-TIMEOUT] End prompt timeout reached, force closing connection: ${
            this.clientId
          } (waited ${Math.round(timeSinceEndPrompt / 1000)}s)`
        );

        // Send goodbye MQTT message before force closing
        try {
          this.sendMqttMessage(
            JSON.stringify({
              type: "goodbye",
              session_id: this.udp ? this.udp.session_id : null,
              reason: "end_prompt_timeout",
              timestamp: Date.now(),
            })
          );
          console.log(
            `👋 [GOODBYE-MQTT] Sent goodbye MQTT message to device on timeout: ${this.clientId}`
          );
        } catch (error) {
          console.error(
            `Failed to send goodbye MQTT message: ${error.message}`
          );
        }

        this.close();
        return;
      }

      // Show countdown for end prompt completion
      if (timeSinceEndPrompt % 5000 < 1000) {
        const remainingSeconds = Math.round(
          (maxEndWaitTime - timeSinceEndPrompt) / 1000
        );
        console.log(
          `⏳ [END-WAIT] Device ${this.clientId}: ${remainingSeconds}s until force disconnect`
        );
      }
      return; // Don't do normal timeout check while ending
    }

    // Check for inactivity timeout (1 minute of no communication)
    const timeSinceLastActivity = now - this.lastActivityTime;

    // Skip timeout check if audio is actively playing
    if (this.bridge && this.bridge.isAudioPlaying) {
      // Reset the timer while audio is playing to prevent timeout
      this.lastActivityTime = now;
      console.log(
        `🎵 [AUDIO-ACTIVE] Resetting timer - audio is playing for device: ${this.clientId}`
      );
      return;
    }

    if (timeSinceLastActivity > this.inactivityTimeoutMs) {
      // Send end prompt instead of immediate close
      if (!this.isEnding && this.bridge) {
        this.isEnding = true;
        this.endPromptSentTime = now;
        console.log(
          `👋 [END-PROMPT] Sending goodbye message before timeout: ${
            this.clientId
          } (inactive for ${Math.round(
            timeSinceLastActivity / 1000
          )}s) - Last activity: ${new Date(
            this.lastActivityTime
          ).toISOString()}, Now: ${new Date(now).toISOString()}`
        );

        try {
          // Send end prompt to agent for voice goodbye (TTS "Time flies fast...")
          // Note: Goodbye MQTT will be sent AFTER TTS finishes (in agent_state_changed handler)
          this.goodbyeSent = false; // Flag to track if goodbye MQTT was sent
          await this.bridge.sendEndPrompt(this.udp.session_id);
          console.log(
            `👋 [END-PROMPT-SENT] Waiting for TTS goodbye to complete before sending goodbye MQTT: ${this.clientId}`
          );
        } catch (error) {
          console.error(`Failed to send end prompt: ${error.message}`);
          // If end prompt fails, close immediately
          this.close();
        }
        return;
      } else {
        // No bridge available, send goodbye message and close immediately
        console.log(
          `🕒 [TIMEOUT] Closing connection due to 1-minute inactivity: ${
            this.clientId
          } (inactive for ${Math.round(timeSinceLastActivity / 1000)}s)`
        );

        // Send goodbye MQTT message before closing
        try {
          this.sendMqttMessage(
            JSON.stringify({
              type: "goodbye",
              session_id: this.udp ? this.udp.session_id : null,
              reason: "inactivity_timeout",
              timestamp: Date.now(),
            })
          );
          console.log(
            `👋 [GOODBYE-MQTT] Sent goodbye MQTT message to device: ${this.clientId}`
          );
        } catch (error) {
          console.error(
            `Failed to send goodbye MQTT message: ${error.message}`
          );
        }

        this.close();
        return;
      }
    }

    // Log remaining time until timeout (only show every 30 seconds to avoid spam)
    if (timeSinceLastActivity % 30000 < 1000) {
      const remainingSeconds = Math.round(
        (this.inactivityTimeoutMs - timeSinceLastActivity) / 1000
      );
      console.log(
        `⏰ [TIMER-CHECK] Device ${this.clientId}: ${remainingSeconds}s until timeout`
      );
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
    console.log(
      `📨 [ACTIVITY] MQTT message received from ${this.clientId}, resetting inactivity timer`
    );
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
        console.error(
          `❌ [HELLO-ERROR] Failed to process hello message for ${this.clientId}:`,
          error
        );
        console.error(`❌ [HELLO-ERROR] Error stack:`, error.stack);
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
    console.log(
      `🔍 [PARSE-HELLO] Starting parseHelloMessage for ${this.clientId}`
    );
    console.log(
      `🔍 [PARSE-HELLO] JSON version: ${json.version}, has bridge: ${!!this
        .bridge}`
    );

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

    // CRITICAL FIX: Generate new UUID for each session to create new room
    // This prevents device from reconnecting to the same room after session end
    const newSessionUuid = crypto.randomUUID();
    console.log(
      `🔄 [NEW-SESSION] Generated fresh UUID for new session: ${newSessionUuid} (old: ${this.uuid})`
    );

    // Generate the new room name that will be created (must match LiveKitBridge.connect() logic)
    const macForRoom = this.macAddress.replace(/:/g, "");
    const newRoomName = `${newSessionUuid}_${macForRoom}`; // Use new UUID
    console.log(`🔐 [HELLO] New room will be: ${newRoomName}`);

    // Clean up ALL old sessions for this MAC address EXCEPT the new room
    // Check if server has roomService (for legacy MQTTConnection support)
    if (this.server && this.server.roomService) {
      console.log(
        `🧹 [HELLO] Cleaning up old sessions for MAC: ${this.macAddress}`
      );
      await LiveKitBridge.cleanupOldSessionsForDevice(
        this.macAddress,
        this.server.roomService,
        newRoomName
      );
    }

    this.bridge = new LiveKitBridge(
      this,
      json.version,
      this.macAddress,
      newSessionUuid, // Use fresh UUID instead of this.uuid
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
      console.log(
        `🧹 LiveKit room cleanup initiated for session: ${this.udp.session_id}`
      );

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

      // Wait for agent to join before sending hello response
      console.log(
        `⏳ [HELLO] Waiting for agent to join before sending hello response to ${this.clientId}`
      );
      const agentWaitStartTime = Date.now();
      const agentReady = await this.bridge.waitForAgentJoin(4000); // Reduced timeout from 7000ms to 4000ms
      const agentWaitEndTime = Date.now();
      console.log(
        `⏱️ [TIMING-AGENT] Agent wait took ${
          agentWaitEndTime - agentWaitStartTime
        }ms`
      );

      if (agentReady) {
        console.log(
          `✅ [HELLO] Agent ready, sending hello response to ${this.clientId}`
        );
      } else {
        console.log(
          `⚠️ [HELLO] Agent join timeout, sending hello response anyway to ${this.clientId}`
        );
      }

      // Reset activity timer after bridge is fully connected and ready
      // This prevents timeout during the initialization phase (cleanup + agent join)
      this.lastActivityTime = Date.now();
      console.log(
        `⏱️ [HELLO] Reset activity timer after bridge connection for device: ${this.clientId}`
      );

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
      console.log(
        `👋 [GOODBYE-MAC] Received goodbye message from device: ${this.macAddress}, session: ${json.session_id}`
      );
      this.bridge.close();
      this.bridge = null;
      return;
    }

    // Handle abort message - forward to LiveKit agent via data channel
    if (json.type === "abort") {
      try {
        console.log(
          `🛑 [ABORT] Received abort signal from device: ${this.macAddress}`
        );
        await this.bridge.sendAbortSignal(json.session_id);
        debug("Successfully forwarded abort signal to LiveKit agent");

        // IMPORTANT: Also notify mobile app that playback was stopped by toy
        this.bridge.forwardPlaybackStatusToMobile("stopped", "");
        console.log(
          `📱 [ABORT] Notified mobile app that playback was stopped by toy`
        );
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

    // Track target toy for mobile-initiated connections
    this.targetToyMac = null; // MAC address of the toy to route audio to
    this.isMobileConnection = false; // Flag to identify mobile connections

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
        console.error(
          `❌ [VIRTUAL] Invalid clientId format: ${helloPayload.clientId}`
        );
        this.close();
        return;
      }

      // Use the MAC address for the reply topic (toy subscribes to devices/p2p/{MAC})
      this.replyTo = `devices/p2p/${this.macAddress}`;
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
      console.log(
        `📱 [ENDING-IGNORE] Activity during goodbye sequence ignored for virtual device: ${this.deviceId}`
      );
      return; // Don't log timer reset during ending
    }

    console.log(
      `⏱️ [TIMER-RESET] Activity timer reset for virtual device: ${
        this.deviceId
      } at ${new Date().toISOString()}`
    );
  }

  handlePublish(publishData) {
    // Update activity timestamp on any MQTT message receipt
    console.log(
      `📨 [ACTIVITY] MQTT message received from virtual device ${this.deviceId}, resetting inactivity timer`
    );
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
          console.error(
            `❌ [HELLO-ERROR] Failed to process hello message for ${this.deviceId}:`,
            error
          );
          console.error(`❌ [HELLO-ERROR] Error stack:`, error.stack);
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
    console.log(
      `📤 [VIRTUAL] sendMqttMessage called for device: ${this.deviceId}`
    );
    console.log(`📤 [VIRTUAL] Payload: ${payload}`);
    debug(`Sending message to ${this.deviceId}: ${payload}`);

    try {
      const parsedPayload = JSON.parse(payload);
      console.log(`📤 [VIRTUAL] Parsed payload:`, parsedPayload);
      this.gateway.publishToDevice(this.fullClientId, parsedPayload);
      console.log(
        `📤 [VIRTUAL] Called publishToDevice for device: ${this.deviceId}`
      );
    } catch (error) {
      console.error(
        `❌ [VIRTUAL] Error in sendMqttMessage for device ${this.deviceId}:`,
        error
      );
    }
  }

  // Forward MCP response to LiveKit agent
  async forwardMcpResponse(mcpPayload, sessionId, requestId) {
    console.log(
      `🔋 [MCP-FORWARD] Forwarding MCP response for device ${this.deviceId}`
    );

    if (
      !this.bridge ||
      !this.bridge.room ||
      !this.bridge.room.localParticipant
    ) {
      console.error(
        `❌ [MCP-FORWARD] No LiveKit room available for device ${this.deviceId}`
      );
      return false;
    }

    try {
      const responseMessage = {
        type: "mcp",
        payload: mcpPayload,
        session_id: sessionId,
        request_id: requestId,
        timestamp: new Date().toISOString(),
      };

      const messageString = JSON.stringify(responseMessage);
      const messageData = new Uint8Array(Buffer.from(messageString, "utf8"));

      await this.bridge.room.localParticipant.publishData(messageData, {
        reliable: true,
      });

      console.log(
        `✅ [MCP-FORWARD] Successfully forwarded MCP response to LiveKit agent`
      );
      console.log(`✅ [MCP-FORWARD] Request ID: ${requestId}`);
      return true;
    } catch (error) {
      console.error(`❌ [MCP-FORWARD] Error forwarding MCP response:`, error);
      return false;
    }
  }

  sendUdpMessage(payload, timestamp) {
    // Check if this is a mobile-initiated connection that needs routing to a physical toy
    if (!this.udp.remoteAddress && this.isMobileConnection && this.macAddress) {
      // Find the real toy connection with UDP endpoint
      const toyConnection = this.findRealToyConnection(this.macAddress);
      if (
        toyConnection &&
        toyConnection.udp &&
        toyConnection.udp.remoteAddress
      ) {
        console.log(
          `🎯 [MOBILE->TOY] Routing audio from mobile to toy: ${this.macAddress}`
        );
        // Route audio through the real toy's UDP connection
        toyConnection.sendUdpMessage(payload, timestamp);
        return;
      } else {
        // Log but don't fail - toy might not be connected yet
        console.log(
          `⚠️ [MOBILE->TOY] No active toy connection found for MAC: ${this.macAddress}`
        );
        return;
      }
    }

    // Original implementation for direct UDP connections
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

  findRealToyConnection(macAddress) {
    // Search through all gateway connections for the real toy with UDP
    for (const [connectionId, connection] of this.gateway.connections) {
      // Check if this is a real MQTTConnection (not VirtualMQTTConnection)
      // and matches the MAC address and has UDP endpoint
      if (
        connection &&
        connection.macAddress === macAddress &&
        connection.udp &&
        connection.udp.remoteAddress &&
        connection.constructor.name === "MQTTConnection"
      ) {
        console.log(
          `✅ [FIND-TOY] Found real toy connection for MAC ${macAddress}`
        );
        return connection;
      }
    }

    // Also check deviceConnections map
    const deviceInfo = this.gateway.deviceConnections.get(macAddress);
    if (deviceInfo && deviceInfo.connection) {
      const conn = deviceInfo.connection;
      if (
        conn.udp &&
        conn.udp.remoteAddress &&
        conn.constructor.name === "MQTTConnection"
      ) {
        console.log(
          `✅ [FIND-TOY] Found real toy in deviceConnections for MAC ${macAddress}`
        );
        return conn;
      }
    }

    console.log(
      `❌ [FIND-TOY] No real toy connection found for MAC ${macAddress}`
    );
    return null;
  }

  async parseHelloMessage(json) {
    console.log(
      `🔍 [PARSE-HELLO] Starting parseHelloMessage for ${this.deviceId}`
    );
    console.log(
      `🔍 [PARSE-HELLO] JSON version: ${json.version}, has bridge: ${!!this
        .bridge}`
    );

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

    // CRITICAL FIX: Generate new UUID for each session to create new room
    // This prevents device from reconnecting to the same room after session end
    const newSessionUuid = crypto.randomUUID();
    console.log(
      `🔄 [NEW-SESSION] Generated fresh UUID for new session: ${newSessionUuid} (old: ${this.uuid})`
    );

    // Generate the new room name that will be created (must match LiveKitBridge.connect() logic)
    const macForRoom = this.macAddress.replace(/:/g, "");
    const newRoomName = `${newSessionUuid}_${macForRoom}`; // Use new UUID
    console.log(`🔐 [HELLO] New room will be: ${newRoomName}`);

    // Clean up ALL old sessions for this MAC address EXCEPT the new room
    console.log(
      `🧹 [HELLO] Cleaning up old sessions for MAC: ${this.macAddress}`
    );
    await LiveKitBridge.cleanupOldSessionsForDevice(
      this.macAddress,
      this.gateway.roomService,
      newRoomName
    );

    this.bridge = new LiveKitBridge(
      this,
      json.version,
      this.macAddress,
      newSessionUuid, // Use fresh UUID instead of this.uuid
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
      console.log(
        `🧹 LiveKit room cleanup initiated for virtual session: ${this.udp.session_id}`
      );

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

      // Wait for agent to join before sending hello response
      console.log(
        `⏳ [HELLO] Waiting for agent to join before sending hello response to ${this.deviceId}`
      );
      const agentWaitStartTime = Date.now();
      const agentReady = await this.bridge.waitForAgentJoin(4000); // Reduced timeout from 7000ms to 4000ms
      const agentWaitEndTime = Date.now();
      console.log(
        `⏱️ [TIMING-AGENT] Agent wait took ${
          agentWaitEndTime - agentWaitStartTime
        }ms`
      );

      if (agentReady) {
        console.log(
          `✅ [HELLO] Agent ready, sending hello response to ${this.deviceId}`
        );
      } else {
        console.log(
          `⚠️ [HELLO] Agent join timeout, sending hello response anyway to ${this.deviceId}`
        );
      }

      // Reset activity timer after bridge is fully connected and ready
      // This prevents timeout during the initialization phase (cleanup + agent join)
      this.lastActivityTime = Date.now();
      console.log(
        `⏱️ [HELLO] Reset activity timer after bridge connection for device: ${this.deviceId}`
      );

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
      console.log(
        `👋 [GOODBYE-DEVICEID] Received goodbye message from device: ${this.deviceId}, session: ${json.session_id}`
      );
      this.bridge.close();
      this.bridge = null;
      //commet temporarly, dgoodby message is not working well

      return;
    }

    // Handle abort message - forward to LiveKit agent via data channel
    if (json.type === "abort") {
      try {
        console.log(
          `🛑 [ABORT] Received abort signal from device: ${this.deviceId}`
        );
        await this.bridge.sendAbortSignal(json.session_id);
        debug("Successfully forwarded abort signal to LiveKit agent");

        // IMPORTANT: Also notify mobile app that playback was stopped by toy
        this.bridge.forwardPlaybackStatusToMobile("stopped", "");
        console.log(
          `📱 [ABORT] Notified mobile app that playback was stopped by toy`
        );
      } catch (error) {
        debug("Failed to forward abort signal to LiveKit:", error);
      }
      return;
    }

    // Handle function_call from mobile app - forward directly to LiveKit agent
    if (json.type === "function_call" && json.source === "mobile_app") {
      try {
        console.log(
          `🎵 [MOBILE] Function call received from mobile app: ${this.deviceId}`
        );
        console.log(`   🎯 Function: ${json.function_call?.name}`);
        console.log(
          `   📝 Arguments: ${JSON.stringify(json.function_call?.arguments)}`
        );

        // Check if bridge and room are available
        if (
          !this.bridge ||
          !this.bridge.room ||
          !this.bridge.room.localParticipant
        ) {
          console.error(
            `❌ [MOBILE] No bridge/room available to handle function call`
          );
          return;
        }

        // Only send abort signal for playback commands, not for volume control
        const functionName = json.function_call?.name;
        const isPlaybackCommand = functionName === 'play_music' || functionName === 'play_story';
        
        if (isPlaybackCommand) {
          console.log(`🛑 [MOBILE] Sending abort signal before new playback`);
          await this.bridge.sendAbortSignal(this.udp.session_id);

          // Wait a moment for abort to process
          await new Promise((resolve) => setTimeout(resolve, 100));
        } else {
          console.log(`🔊 [MOBILE] Volume control command - skipping abort signal`);
        }

        // Then forward the new function call to LiveKit agent
        const messageString = JSON.stringify({
          type: "function_call",
          function_call: json.function_call,
          source: "mobile_app",
          timestamp: json.timestamp || Date.now(),
          request_id: json.request_id || `mobile_req_${Date.now()}`,
        });
        const messageData = new Uint8Array(Buffer.from(messageString, "utf8"));

        await this.bridge.room.localParticipant.publishData(messageData, {
          reliable: true,
        });

        console.log(`✅ [MOBILE] Function call forwarded to LiveKit agent`);
      } catch (error) {
        console.error(`❌ [MOBILE] Failed to forward function call:`, error);
      }
      return;
    }

    // Handle mobile music request - forward to LiveKit bridge (legacy support)
    if (json.type === "mobile_music_request") {
      try {
        console.log(
          `🎵 [MOBILE] Mobile music request received from virtual device: ${this.deviceId}`
        );
        console.log(`   🎵 Song: ${json.song_name}`);
        console.log(`   🗂️ Type: ${json.content_type}`);
        console.log(`   🌐 Language: ${json.language || "Not specified"}`);

        // Mark this as a mobile-initiated connection
        this.isMobileConnection = true;
        console.log(
          `   📱 Marked as mobile connection for MAC: ${this.macAddress}`
        );

        // Check if bridge and room are available
        if (
          !this.bridge ||
          !this.bridge.room ||
          !this.bridge.room.localParticipant
        ) {
          console.error(
            `❌ [MOBILE] No bridge/room available to handle music request`
          );
          return;
        }

        // Convert to function_call format for LiveKit agent
        const functionName =
          json.content_type === "story" ? "play_story" : "play_music";
        const functionArguments = {};

        if (json.content_type === "music") {
          // For music: song_name and language
          if (json.song_name) {
            functionArguments.song_name = json.song_name;
          }
          if (json.language) {
            functionArguments.language = json.language;
          }
        } else if (json.content_type === "story") {
          // For stories: story_name and category
          if (json.song_name) {
            functionArguments.story_name = json.song_name;
          }
          if (json.language) {
            functionArguments.category = json.language;
          }
        }

        // Create function call message for LiveKit agent
        const functionCallMessage = {
          type: "function_call",
          function_call: {
            name: functionName,
            arguments: functionArguments,
          },
          source: "mobile_app",
          timestamp: Date.now(),
          request_id: `mobile_req_${Date.now()}`,
        };

        // Forward to LiveKit agent via data channel
        const messageString = JSON.stringify(functionCallMessage);
        const messageData = new Uint8Array(Buffer.from(messageString, "utf8"));

        await this.bridge.room.localParticipant.publishData(messageData, {
          reliable: true,
        });

        console.log(`✅ [MOBILE] Music request forwarded to LiveKit agent`);
        console.log(`   🎯 Function: ${functionName}`);
        console.log(`   📝 Arguments: ${JSON.stringify(functionArguments)}`);
      } catch (error) {
        console.error(
          `❌ [MOBILE] Failed to handle mobile music request:`,
          error
        );
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
        console.log(
          `🕒 [END-TIMEOUT] End prompt timeout reached, force closing virtual connection: ${
            this.deviceId
          } (waited ${Math.round(timeSinceEndPrompt / 1000)}s)`
        );

        // Send goodbye MQTT message before force closing
        try {
          this.sendMqttMessage(
            JSON.stringify({
              type: "goodbye",
              session_id: this.udp ? this.udp.session_id : null,
              reason: "end_prompt_timeout",
              timestamp: Date.now(),
            })
          );
          console.log(
            `👋 [GOODBYE-MQTT] Sent goodbye MQTT message to virtual device on timeout: ${this.deviceId}`
          );
        } catch (error) {
          console.error(
            `Failed to send goodbye MQTT message: ${error.message}`
          );
        }

        this.close();
        return;
      }

      // Show countdown for end prompt completion
      if (timeSinceEndPrompt % 5000 < 1000) {
        const remainingSeconds = Math.round(
          (maxEndWaitTime - timeSinceEndPrompt) / 1000
        );
        console.log(
          `⏳ [END-WAIT] Virtual device ${this.deviceId}: ${remainingSeconds}s until force disconnect`
        );
      }
      return; // Don't do normal timeout check while ending
    }

    // Check for inactivity timeout (1 minute of no communication)
    const timeSinceLastActivity = now - this.lastActivityTime;

    // Skip timeout check if audio is actively playing
    if (this.bridge && this.bridge.isAudioPlaying) {
      // Reset the timer while audio is playing to prevent timeout
      this.lastActivityTime = now;
      console.log(
        `🎵 [AUDIO-ACTIVE] Resetting timer - audio is playing for virtual device: ${this.deviceId}`
      );
      return;
    }

    if (timeSinceLastActivity > this.inactivityTimeoutMs) {
      // Send end prompt instead of immediate close
      if (!this.isEnding && this.bridge) {
        this.isEnding = true;
        this.endPromptSentTime = now;
        console.log(
          `👋 [END-PROMPT] Sending goodbye message before timeout: ${
            this.deviceId
          } (inactive for ${Math.round(
            timeSinceLastActivity / 1000
          )}s) - Last activity: ${new Date(
            this.lastActivityTime
          ).toISOString()}, Now: ${new Date(now).toISOString()}`
        );

        try {
          // Send end prompt to agent for voice goodbye (TTS "Time flies fast...")
          // Note: Goodbye MQTT will be sent AFTER TTS finishes (in agent_state_changed handler)
          this.goodbyeSent = false; // Flag to track if goodbye MQTT was sent
          await this.bridge.sendEndPrompt(this.udp.session_id);
          console.log(
            `👋 [END-PROMPT-SENT] Waiting for TTS goodbye to complete before sending goodbye MQTT: ${this.deviceId}`
          );
        } catch (error) {
          console.error(`Failed to send end prompt: ${error.message}`);
          // If end prompt fails, close immediately
          this.close();
        }
        return;
      } else {
        // No bridge available, send goodbye message and close immediately
        console.log(
          `🕒 [TIMEOUT] Closing virtual connection due to 1-minute inactivity: ${
            this.deviceId
          } (inactive for ${Math.round(timeSinceLastActivity / 1000)}s)`
        );

        // Send goodbye MQTT message before closing
        try {
          this.sendMqttMessage(
            JSON.stringify({
              type: "goodbye",
              session_id: this.udp ? this.udp.session_id : null,
              reason: "inactivity_timeout",
              timestamp: Date.now(),
            })
          );
          console.log(
            `👋 [GOODBYE-MQTT] Sent goodbye MQTT message to virtual device: ${this.deviceId}`
          );
        } catch (error) {
          console.error(
            `Failed to send goodbye MQTT message: ${error.message}`
          );
        }

        this.close();
        return;
      }
    }

    // Log remaining time until timeout (only show every 30 seconds to avoid spam)
    if (timeSinceLastActivity % 30000 < 1000) {
      const remainingSeconds = Math.round(
        (this.inactivityTimeoutMs - timeSinceLastActivity) / 1000
      );
      console.log(
        `⏰ [TIMER-CHECK] Virtual device ${this.deviceId}: ${remainingSeconds}s until timeout`
      );
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

    // Initialize LiveKit RoomServiceClient for room management
    try {
      const livekitConfig = configManager.get("livekit");
      if (
        livekitConfig &&
        livekitConfig.url &&
        livekitConfig.api_key &&
        livekitConfig.api_secret
      ) {
        this.roomService = new RoomServiceClient(
          livekitConfig.url,
          livekitConfig.api_key,
          livekitConfig.api_secret
        );
        console.log(
          "✅ [INIT] RoomServiceClient initialized for session cleanup"
        );
      } else {
        console.warn(
          "⚠️ [INIT] LiveKit config incomplete, room cleanup will be skipped"
        );
        this.roomService = null;
      }
    } catch (error) {
      console.error(
        "❌ [INIT] Failed to initialize RoomServiceClient:",
        error.message
      );
      this.roomService = null;
    }
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

    const clientId = `mqtt-gateway-${Date.now()}-${Math.random()
      .toString(36)
      .substr(2, 9)}`;
    const brokerUrl = `${brokerConfig.protocol}://${brokerConfig.host}:${brokerConfig.port}`;

    console.log(`Connecting to EMQX broker: ${brokerUrl}`);

    this.mqttClient = mqtt.connect(brokerUrl, {
      clientId: clientId,
      keepalive: brokerConfig.keepalive || 60,
      clean: brokerConfig.clean !== false,
      reconnectPeriod: brokerConfig.reconnectPeriod || 1000,
      connectTimeout: brokerConfig.connectTimeout || 30000,
    });

    this.mqttClient.on("connect", () => {
      console.log(`✅ Connected to EMQX broker: ${brokerUrl}`);
      // Subscribe to gateway control topics
      this.mqttClient.subscribe("devices/+/hello", (err) => {
        if (err) {
          console.error("Failed to subscribe to device hello topic:", err);
        } else {
          console.log("📡 Subscribed to devices/+/hello");
        }
      });
      this.mqttClient.subscribe("devices/+/data", (err) => {
        if (err) {
          console.error("Failed to subscribe to device data topic:", err);
        } else {
          console.log("📡 Subscribed to devices/+/data");
        }
      });
      // Subscribe to the internal topic where EMQX republishes with client info
      this.mqttClient.subscribe("internal/server-ingest", (err) => {
        if (err) {
          console.error(
            "Failed to subscribe to internal/server-ingest topic:",
            err
          );
        } else {
          console.log("📡 Subscribed to internal/server-ingest");
        }
      });
      // NOTE: We don't subscribe to device-server directly anymore
      // EMQX rule will republish from device-server to internal/server-ingest with client ID
      // this.mqttClient.subscribe("device-server", (err) => {
      //   if (err) {
      //     console.error("Failed to subscribe to device-server topic:", err);
      //   } else {
      //     console.log("📡 Subscribed to device-server");
      //   }
      // });
    });

    this.mqttClient.on("error", (err) => {
      console.error("MQTT connection error:", err);
    });

    this.mqttClient.on("offline", () => {
      console.warn("MQTT client went offline");
    });

    this.mqttClient.on("reconnect", () => {
      console.log("MQTT client reconnecting...");
    });

    this.mqttClient.on("message", (topic, message) => {
      this.handleMqttMessage(topic, message);
    });
  }

  async handleMqttMessage(topic, message) {
    // Add detailed logging for all incoming MQTT messages
    console.log(`📨 [MQTT IN] Received message on topic: ${topic}`);
    console.log(`📨 [MQTT IN] Message length: ${message.length} bytes`);

    try {
      const payload = JSON.parse(message.toString());
      const topicParts = topic.split("/");

      console.log(
        `📨 [MQTT IN] Parsed payload:`,
        JSON.stringify(payload, null, 2)
      );
      console.log(`📨 [MQTT IN] Topic parts:`, topicParts);

      if (topic === "internal/server-ingest") {
        // Handle messages republished by EMQX with client ID info
        console.log(`📨 [MQTT IN] Message from internal/server-ingest topic`);

        // Extract client ID and original payload from EMQX republish rule
        const clientId = payload.sender_client_id;
        const originalPayload = payload.orginal_payload;

        if (!clientId || !originalPayload) {
          console.error(
            `❌ [MQTT IN] Invalid republished message format - missing clientId or originalPayload`
          );
          return;
        }

        console.log(`📨 [MQTT IN] Client ID: ${clientId}`);
        console.log(
          `📨 [MQTT IN] Original payload:`,
          JSON.stringify(originalPayload, null, 2)
        );

        // Extract device MAC from client ID
        let deviceId = "unknown-device";
        const parts = clientId.split("@@@");
        if (parts.length >= 2) {
          deviceId = parts[1].replace(/_/g, ":"); // Convert MAC format
        }

        console.log(
          `📨 [MQTT IN] Device message from internal/server-ingest - Device: ${deviceId}, Message type: ${originalPayload.type}`
        );

        // Create enhanced payload with client connection info for VirtualMQTTConnection
        const enhancedPayload = {
          ...originalPayload,
          clientId: clientId,
          username: "extracted_from_emqx",
          password: "extracted_from_emqx",
        };

        // Handle MCP responses - forward to LiveKit agent
        if (
          originalPayload.type === "mcp" &&
          originalPayload.payload &&
          originalPayload.payload.result
        ) {
          console.log(
            `🔋 [MCP-RESPONSE] Processing MCP response from device ${deviceId}`
          );

          // Find the device connection
          const deviceInfo = this.deviceConnections.get(deviceId);
          if (deviceInfo && deviceInfo.connection) {
            const requestId = `req_${originalPayload.payload.id}`;

            // Use the connection's method to forward the response
            await deviceInfo.connection.forwardMcpResponse(
              originalPayload.payload,
              originalPayload.session_id,
              requestId
            );
          } else {
            console.warn(
              `⚠️ [MCP-RESPONSE] No connection found for device ${deviceId}, cannot forward response`
            );
          }
        }

        if (originalPayload.type === "hello") {
          console.log(
            `👋 [HELLO] Processing hello message from internal/server-ingest: ${deviceId}`
          );
          this.handleDeviceHello(deviceId, enhancedPayload);
        } else if (originalPayload.type === "mode-change") {
          console.log(
            `🔘 [MODE-CHANGE] Processing mode change from internal/server-ingest: ${deviceId}`
          );
          this.handleDeviceModeChange(deviceId, enhancedPayload);
        } else if (originalPayload.type === "abort") {
          // Special handling for abort messages - send to BOTH real and virtual devices
          console.log(
            `🛑 [ABORT] Processing abort message from internal/server-ingest: ${deviceId}`
          );

          let abortSent = false;

          // Send abort to real ESP32 connection if exists
          const realConnection = this.findRealDeviceConnection(deviceId);
          if (realConnection) {
            console.log(
              `🛑 [ABORT] Routing abort to real ESP32 device: ${deviceId}`
            );
            realConnection.handlePublish({
              payload: JSON.stringify(originalPayload),
            });
            abortSent = true;
          }

          // ALSO send abort to virtual device connection if exists
          const deviceInfo = this.deviceConnections.get(deviceId);
          if (deviceInfo && deviceInfo.connection) {
            console.log(
              `🛑 [ABORT] Routing abort to virtual device (LiveKit): ${deviceId}`
            );
            // Forward abort to the virtual device's handlePublish
            deviceInfo.connection.handlePublish({
              payload: JSON.stringify(originalPayload),
            });
            abortSent = true;
          }

          if (!abortSent) {
            console.log(
              `⚠️ [ABORT] No connections found for device: ${deviceId}, abort cannot be processed`
            );
          }
        } else {
          // ALWAYS check for real ESP32 connection FIRST (prioritize over virtual)
          const realConnection = this.findRealDeviceConnection(deviceId);

          if (realConnection) {
            console.log(
              `🎯 [ROUTE] Routing message from mobile to existing ESP32: ${deviceId}`
            );
            // Route the message to the existing ESP32 connection
            realConnection.handlePublish({
              payload: JSON.stringify(originalPayload),
            });
          } else {
            // No real ESP32 connection - check if there's a virtual connection
            const deviceInfo = this.deviceConnections.get(deviceId);

            if (deviceInfo && deviceInfo.connection) {
              console.log(
                `📊 [DATA] Routing to virtual device connection: ${deviceId}`
              );

              // Send success message to mobile app
              const successMessage = {
                type: "device_status",
                status: "connected",
                message: "song is playing",
                deviceId: deviceId,
                timestamp: Date.now(),
              };

              // Publish to app/p2p/{macAddress}
              const appTopic = `app/p2p/${deviceId}`;
              console.log(
                `✅ [MOBILE-RESPONSE] Sending device connected status to ${appTopic}`
              );

              if (this.mqttClient && this.mqttClient.connected) {
                this.mqttClient.publish(
                  appTopic,
                  JSON.stringify(successMessage),
                  (err) => {
                    if (err) {
                      console.error(
                        `❌ [MOBILE-RESPONSE] Failed to send success to mobile app:`,
                        err
                      );
                    } else {
                      console.log(
                        `✅ [MOBILE-RESPONSE] Device connected status sent to mobile app`
                      );
                    }
                  }
                );
              }

              this.handleDeviceData(deviceId, enhancedPayload);
            } else {
              console.log(
                `⚠️ [DATA] No connection found for device: ${deviceId}, message type: ${originalPayload.type}`
              );

              // Send device not connected message to mobile app
              const errorMessage = {
                type: "device_status",
                status: "not_connected",
                message: "Device is not connected",
                deviceId: deviceId,
                timestamp: Date.now(),
              };

              // Publish to app/p2p/{macAddress}
              const appTopic = `app/p2p/${deviceId}`;
              console.log(
                `❌ [MOBILE-RESPONSE] Sending device not connected status to ${appTopic}`
              );

              if (this.mqttClient && this.mqttClient.connected) {
                this.mqttClient.publish(
                  appTopic,
                  JSON.stringify(errorMessage),
                  (err) => {
                    if (err) {
                      console.error(
                        `❌ [MOBILE-RESPONSE] Failed to send error to mobile app:`,
                        err
                      );
                    } else {
                      console.log(
                        `✅ [MOBILE-RESPONSE] Device not connected status sent to mobile app`
                      );
                    }
                  }
                );
              }
            }
          }
        }
      } else if (topic === "device-server") {
        // Handle messages from device-server topic (for real devices)
        console.log(`📨 [MQTT IN] Message from device-server topic`);

        // Extract device MAC from client_id (with underscore) or clientId (camelCase)
        let deviceId = "unknown-device";
        const clientIdField = payload.clientId || payload.client_id;

        if (clientIdField) {
          // If it's already in MAC format (with colons or underscores)
          if (clientIdField.includes(":") || clientIdField.includes("_")) {
            deviceId = clientIdField.replace(/_/g, ":");
          } else {
            // If it's in the format GID_test@@@mac@@@uuid
            const parts = clientIdField.split("@@@");
            if (parts.length >= 2) {
              deviceId = parts[1].replace(/_/g, ":");
            }
          }
        }

        console.log(
          `📨 [MQTT IN] Device message from device-server - Device: ${deviceId}, Message type: ${payload.type}`
        );

        // Add clientId to payload if not present (for VirtualMQTTConnection)
        // Create a proper clientId in the format GID_test@@@MAC@@@UUID
        if (!payload.clientId && clientIdField) {
          // If clientIdField is just the MAC, create a full clientId
          if (clientIdField.includes("@@@")) {
            // Already in full format
            payload.clientId = clientIdField;
          } else {
            // Just MAC address, create full format
            payload.clientId = `GID_test@@@${clientIdField}@@@${crypto.randomUUID()}`;
          }
        }

        if (payload.type === "hello") {
          console.log(
            `👋 [HELLO] Processing hello message from device-server: ${deviceId}`
          );
          this.handleDeviceHello(deviceId, payload);
        } else if (payload.type === "mode-change") {
          console.log(
            `🔘 [MODE-CHANGE] Processing mode change from device-server: ${deviceId}`
          );
          this.handleDeviceModeChange(deviceId, payload);
        } else {
          console.log(
            `📊 [DATA] Processing data message from device-server: ${deviceId}`
          );
          this.handleDeviceData(deviceId, payload);
        }
      } else if (topicParts.length >= 3 && topicParts[0] === "devices") {
        const deviceId = topicParts[1];
        const messageType = topicParts[2];

        console.log(
          `📨 [MQTT IN] Device message - Device: ${deviceId}, Type: ${messageType}`
        );
        debug(
          `📨 Received MQTT message from device ${deviceId}: ${messageType}`
        );

        if (messageType === "hello") {
          console.log(
            `👋 [HELLO] Processing hello message from device: ${deviceId}`
          );
          this.handleDeviceHello(deviceId, payload);
        } else if (messageType === "data") {
          console.log(
            `📊 [DATA] Processing data message from device: ${deviceId}`
          );
          this.handleDeviceData(deviceId, payload);
        } else {
          console.log(
            `❓ [UNKNOWN] Unknown message type '${messageType}' from device: ${deviceId}`
          );
        }
      } else {
        console.log(
          `❓ [MQTT IN] Message on unexpected topic format: ${topic}`
        );
      }
    } catch (error) {
      console.error("❌ [MQTT IN] Error processing MQTT message:", error);
      console.log(`📨 [MQTT IN] Raw message:`, message.toString());
    }
  }

  handleDeviceHello(deviceId, payload) {
    console.log(`📱 [HELLO] handleDeviceHello called for device: ${deviceId}`);

    // Create a virtual connection for this device
    const connectionId = this.generateNewConnectionId();
    console.log(`📱 [HELLO] Generated connection ID: ${connectionId}`);

    const virtualConnection = new VirtualMQTTConnection(
      deviceId,
      connectionId,
      this,
      payload
    );
    console.log(
      `📱 [HELLO] Created VirtualMQTTConnection for device: ${deviceId}`
    );

    this.connections.set(connectionId, virtualConnection);
    this.deviceConnections.set(deviceId, {
      connectionId,
      connection: virtualConnection,
    });

    console.log(`📱 [HELLO] Device ${deviceId} connected via EMQX`);
    console.log(
      `📱 [HELLO] Now calling handlePublish to process hello message...`
    );

    // Manually trigger the hello message processing
    try {
      virtualConnection.handlePublish({ payload: JSON.stringify(payload) });
      console.log(
        `📱 [HELLO] Successfully called handlePublish for device: ${deviceId}`
      );
    } catch (error) {
      console.error(
        `❌ [HELLO] Error in handlePublish for device ${deviceId}:`,
        error
      );
    }
  }

  findRealDeviceConnection(deviceId) {
    // Search through all gateway connections for the real device with UDP
    for (const [connectionId, connection] of this.connections) {
      // Check if this is a real MQTTConnection (not VirtualMQTTConnection)
      // and matches the device ID and has UDP endpoint
      if (
        connection &&
        (connection.macAddress === deviceId ||
          connection.deviceId === deviceId) &&
        connection.udp &&
        connection.udp.remoteAddress &&
        connection.constructor.name === "MQTTConnection"
      ) {
        console.log(
          `✅ [FIND-DEVICE] Found real device connection for ${deviceId}`
        );
        return connection;
      }
    }

    // Also check deviceConnections map
    const deviceInfo = this.deviceConnections.get(deviceId);
    if (deviceInfo && deviceInfo.connection) {
      const conn = deviceInfo.connection;
      if (
        conn.udp &&
        conn.udp.remoteAddress &&
        conn.constructor.name === "MQTTConnection"
      ) {
        console.log(
          `✅ [FIND-DEVICE] Found real device in deviceConnections for ${deviceId}`
        );
        return conn;
      }
    }

    console.log(
      `❌ [FIND-DEVICE] No real device connection found for ${deviceId}`
    );
    return null;
  }

  handleDeviceData(deviceId, payload) {
    const deviceInfo = this.deviceConnections.get(deviceId);
    if (deviceInfo && deviceInfo.connection) {
      deviceInfo.connection.handlePublish({ payload: JSON.stringify(payload) });
    } else {
      console.warn(`📱 Received data from unknown device: ${deviceId}`);
    }
  }

  async handleDeviceModeChange(deviceId, payload) {
    try {
      console.log(`🔘 [MODE-CHANGE] Device ${deviceId} requesting mode change`);

      // Extract MAC address (remove colons for API call)
      const macAddress = deviceId.replace(/:/g, "").toLowerCase();

      // Call Manager API
      const axios = require("axios");
      const apiUrl = `${process.env.MANAGER_API_URL}/agent/device/${macAddress}/cycle-mode`;

      console.log(`📡 [MODE-CHANGE] Calling API: ${apiUrl}`);
      const response = await axios.post(apiUrl, {}, { timeout: 5000 });

      if (response.data.code === 0 && response.data.data.success) {
        const { newModeName, oldModeName, agentId } = response.data.data;
        console.log(
          `✅ [MODE-CHANGE] Mode updated: ${oldModeName} → ${newModeName}`
        );

        // Load audio map
        const fs = require("fs");
        const path = require("path");
        const audioMapPath = path.join(
          __dirname,
          "audio",
          "mode_change",
          "audio_map.json"
        );
        const audioMap = JSON.parse(fs.readFileSync(audioMapPath, "utf8"));

        // Get audio file for mode (use PCM extension instead of Opus)
        const audioFileName = audioMap.modes[newModeName] || audioMap.default;
        const pcmFileName = audioFileName.replace(".opus", ".pcm");
        const audioFilePath = path.join(
          __dirname,
          "audio",
          "mode_change",
          pcmFileName
        );

        if (!fs.existsSync(audioFilePath)) {
          console.error(
            `❌ [MODE-CHANGE] Audio file not found: ${audioFilePath}`
          );
          return;
        }

        console.log(`🎵 [MODE-CHANGE] Streaming audio: ${pcmFileName}`);

        // Stream audio via UDP
        await this.streamAudioViaUdp(deviceId, audioFilePath, newModeName);
      } else {
        console.error(`❌ [MODE-CHANGE] API error:`, response.data);
      }
    } catch (error) {
      console.error(`❌ [MODE-CHANGE] Error:`, error.message);
    }
  }

  async streamAudioViaUdp(deviceId, audioFilePath, modeName) {
    try {
      const fs = require("fs");
      const path = require("path");
      const connection = this.deviceConnections.get(deviceId)?.connection;

      if (!connection) {
        console.error(
          `❌ [MODE-CHANGE] No active connection for device: ${deviceId}`
        );
        return;
      }

      // Get client ID for publishing MQTT messages
      const clientId = connection.clientId;
      if (!clientId) {
        console.error(
          `❌ [MODE-CHANGE] No client ID found for device: ${deviceId}`
        );
        return;
      }

      // Check if we need to convert Opus file to PCM first
      const pcmFilePath = audioFilePath.replace(".opus", ".pcm");

      if (!fs.existsSync(pcmFilePath)) {
        console.log(
          `⚠️ [MODE-CHANGE] PCM file not found. Please convert Opus to PCM:`
        );
        console.log(
          `   ffmpeg -i ${audioFilePath} -f s16le -ar 24000 -ac 1 ${pcmFilePath}`
        );
        console.error(`❌ [MODE-CHANGE] Cannot stream without PCM file`);
        return;
      }

      // Read PCM file (24kHz, mono, 16-bit signed)
      const pcmData = fs.readFileSync(pcmFilePath);
      console.log(
        `📦 [MODE-CHANGE] Loaded ${pcmData.length} bytes PCM from ${pcmFilePath}`
      );

      const controlTopic = `devices/p2p/${clientId}`;

      // Send TTS start via MQTT
      const ttsStartMsg = {
        type: "tts",
        state: "start",
        text: `Switched to ${modeName} mode`,
        timestamp: Date.now(),
      };
      this.mqttClient.publish(
        controlTopic,
        JSON.stringify(ttsStartMsg),
        (err) => {
          if (err) {
            console.error(`❌ [MODE-CHANGE] Failed to publish TTS start:`, err);
          } else {
            console.log(
              `📤 [MODE-CHANGE] TTS start sent to ${deviceId} via ${controlTopic}`
            );
          }
        }
      );

      // Wait a bit for TTS start to be processed
      await new Promise((resolve) => setTimeout(resolve, 200));

      // Stream PCM in 60ms frames, encode to Opus, send via UDP
      // Same as LiveKit audio: 24kHz, 60ms = 1440 samples = 2880 bytes PCM
      const FRAME_SIZE_SAMPLES = 1440; // 24000 Hz * 0.06s
      const FRAME_SIZE_BYTES = FRAME_SIZE_SAMPLES * 2; // 2 bytes per sample
      let offset = 0;
      let frameCount = 0;

      // Calculate relative timestamp
      const startTime = connection.udp?.startTime || Date.now();
      let baseTimestamp = (Date.now() - startTime) & 0xffffffff;

      while (offset < pcmData.length) {
        const frameData = pcmData.slice(
          offset,
          Math.min(offset + FRAME_SIZE_BYTES, pcmData.length)
        );

        // Pad last frame if incomplete
        let frameTosend = frameData;
        if (frameData.length < FRAME_SIZE_BYTES) {
          frameTosend = Buffer.alloc(FRAME_SIZE_BYTES);
          frameData.copy(frameTosend);
          // Rest is zeros (silence padding)
        }

        // Calculate timestamp for this frame
        const timestamp = (baseTimestamp + frameCount * 60) & 0xffffffff;

        // Encode to Opus (same as LiveKit audio streaming)
        if (opusEncoder) {
          try {
            const opusBuffer = opusEncoder.encode(
              frameTosend,
              FRAME_SIZE_SAMPLES
            );

            if (frameCount % 20 === 0) {
              console.log(
                `🎵 [MODE-CHANGE] Frame ${frameCount}: PCM ${frameTosend.length}B → Opus ${opusBuffer.length}B`
              );
            }

            // Send via UDP (will be encrypted automatically)
            connection.sendUdpMessage(opusBuffer, timestamp);
          } catch (err) {
            console.error(`❌ [MODE-CHANGE] Opus encode error:`, err.message);
            // Fallback to PCM
            connection.sendUdpMessage(frameTosend, timestamp);
          }
        } else {
          // No Opus encoder available, send PCM directly
          console.warn(`⚠️ [MODE-CHANGE] No Opus encoder, sending PCM`);
          connection.sendUdpMessage(frameTosend, timestamp);
        }

        offset += FRAME_SIZE_BYTES;
        frameCount++;

        // Wait 60ms for next frame (match frame duration)
        await new Promise((resolve) => setTimeout(resolve, 60));
      }

      console.log(
        `📦 [MODE-CHANGE] Streamed ${frameCount} frames (${pcmData.length} bytes PCM)`
      );

      // Wait a bit before sending TTS stop
      await new Promise((resolve) => setTimeout(resolve, 100));

      // Send TTS stop
      const ttsStopMsg = {
        type: "tts",
        state: "stop",
        timestamp: Date.now(),
      };
      this.mqttClient.publish(
        controlTopic,
        JSON.stringify(ttsStopMsg),
        (err) => {
          if (err) {
            console.error(`❌ [MODE-CHANGE] Failed to publish TTS stop:`, err);
          } else {
            console.log(
              `📤 [MODE-CHANGE] TTS stop sent to ${deviceId} via ${controlTopic}`
            );
          }
        }
      );

      // Wait a bit to ensure TTS stop is processed
      await new Promise((resolve) => setTimeout(resolve, 200));

      // Send goodbye message to close the LiveKit session after mode change
      const goodbyeMsg = {
        type: "goodbye",
        session_id: connection.udp?.session_id || null,
        reason: "mode_change",
        timestamp: Date.now(),
      };

      this.mqttClient.publish(
        controlTopic,
        JSON.stringify(goodbyeMsg),
        (err) => {
          if (err) {
            console.error(`❌ [MODE-CHANGE] Failed to publish goodbye:`, err);
          } else {
            console.log(
              `👋 [MODE-CHANGE] Goodbye sent to ${deviceId} - LiveKit session will close`
            );
          }
        }
      );
    } catch (error) {
      console.error(`❌ [MODE-CHANGE] Audio streaming error:`, error.message);
      console.error(error.stack);
    }
  }

  publishToDevice(clientIdOrDeviceId, message) {
    console.log(
      `📤 [MQTT OUT] publishToDevice called - Client/Device: ${clientIdOrDeviceId}`
    );
    console.log(`📤 [MQTT OUT] Message:`, JSON.stringify(message, null, 2));

    if (this.mqttClient && this.mqttClient.connected) {
      // Use the full client ID directly in the topic
      const topic = `devices/p2p/${clientIdOrDeviceId}`;
      console.log(`📤 [MQTT OUT] Publishing to topic: ${topic}`);

      this.mqttClient.publish(topic, JSON.stringify(message), (err) => {
        if (err) {
          console.error(
            `❌ [MQTT OUT] Failed to publish to client ${clientIdOrDeviceId}:`,
            err
          );
        } else {
          console.log(
            `✅ [MQTT OUT] Successfully published to client ${clientIdOrDeviceId} on topic ${topic}`
          );
          debug(
            `📤 Published to client ${clientIdOrDeviceId}: ${JSON.stringify(
              message
            )}`
          );
        }
      });
    } else {
      console.error(
        "❌ [MQTT OUT] MQTT client not connected, cannot publish message"
      );
      console.log(
        `📊 [MQTT OUT] Client connected: ${
          this.mqttClient ? this.mqttClient.connected : "null"
        }`
      );
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

// Handle unhandled errors from LiveKit SDK
process.on("uncaughtException", (error) => {
  if (
    error.message &&
    error.message.includes("InvalidState - failed to capture frame")
  ) {
    console.warn(
      `⚠️ [GLOBAL] Caught InvalidState error, continuing operation...`
    );
    console.warn(
      `⚠️ [HINT] This usually happens when the peer connection disconnects during audio capture`
    );
    // Don't exit - the error is non-fatal
  } else {
    console.error(`❌ [FATAL] Uncaught exception:`, error);
    process.exit(1);
  }
});

process.on("unhandledRejection", (reason, promise) => {
  console.error(
    `❌ [FATAL] Unhandled rejection at:`,
    promise,
    `reason:`,
    reason
  );
});

process.on("SIGINT", () => {
  console.warn("Received SIGINT signal, starting shutdown");
  gateway.stop();
});
