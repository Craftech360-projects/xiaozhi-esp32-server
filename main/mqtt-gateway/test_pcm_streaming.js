// Test PCM file streaming to isolate jitter issues
// This bypasses LiveKit and streams test.pcm directly through the UDP pipeline

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

// Import Opus encoder (same as in app.js)
let OpusEncoder, OpusApplication;
let opusLib = null;

try {
    const audifyPlus = require("@voicehype/audify-plus");
    OpusEncoder = audifyPlus.OpusEncoder;
    OpusApplication = audifyPlus.OpusApplication;
    opusLib = "audify-plus";
    console.log("✅ [OPUS] audify-plus package loaded successfully");
} catch (err) {
    try {
        const discordOpus = require("@discordjs/opus");
        OpusEncoder = discordOpus.OpusEncoder;
        OpusApplication = { OPUS_APPLICATION_AUDIO: "audio" };
        opusLib = "@discordjs/opus";
        console.log("✅ [OPUS] @discordjs/opus package loaded successfully");
    } catch (err2) {
        console.log("⚠️ [OPUS] No Opus library available, will use PCM mode");
        OpusEncoder = null;
    }
}

// Audio parameters (matching LiveKit's format)
const LIVEKIT_SAMPLE_RATE = 48000; // LiveKit uses 48kHz
const OUTPUT_SAMPLE_RATE = 24000;   // Your gateway outputs 24kHz
const CHANNELS = 1;                 // Mono
const FRAME_DURATION_MS = 60;       // 60ms frames for output
const LIVEKIT_FRAME_DURATION_MS = 20; // LiveKit uses 20ms frames internally
const OUTPUT_FRAME_SIZE_SAMPLES = (OUTPUT_SAMPLE_RATE * FRAME_DURATION_MS) / 1000; // 1440 samples
const OUTPUT_FRAME_SIZE_BYTES = OUTPUT_FRAME_SIZE_SAMPLES * 2; // 2880 bytes for 16-bit PCM

class PCMStreamer {
    constructor(pcmFilePath, targetConnection) {
        this.pcmFilePath = pcmFilePath;
        this.targetConnection = targetConnection;
        this.frameBuffer = Buffer.alloc(0);
        this.frameCount = 0;
        this.startTime = Date.now();

        // Initialize Opus encoder (same as app.js)
        this.opusEncoder = null;
        if (OpusEncoder) {
            try {
                if (opusLib === "audify-plus") {
                    this.opusEncoder = new OpusEncoder(OUTPUT_SAMPLE_RATE, CHANNELS, OpusApplication.OPUS_APPLICATION_AUDIO);
                } else if (opusLib === "@discordjs/opus") {
                    this.opusEncoder = new OpusEncoder(OUTPUT_SAMPLE_RATE, CHANNELS);
                }
                console.log(`✅ [OPUS] Encoder initialized for PCM streaming at ${OUTPUT_SAMPLE_RATE}Hz`);
            } catch (err) {
                console.error(`❌ [OPUS] Failed to initialize encoder: ${err.message}`);
                this.opusEncoder = null;
            }
        }
    }

    async streamPCM() {
        console.log(`🎵 [PCM-STREAM] Starting PCM file streaming: ${this.pcmFilePath}`);

        if (!fs.existsSync(this.pcmFilePath)) {
            console.error(`❌ [PCM-STREAM] File not found: ${this.pcmFilePath}`);
            return;
        }

        const fileStats = fs.statSync(this.pcmFilePath);
        console.log(`📁 [PCM-STREAM] File size: ${fileStats.size} bytes`);
        console.log(`⏱️ [PCM-STREAM] Expected duration: ${(fileStats.size / 2 / OUTPUT_SAMPLE_RATE).toFixed(2)}s`);

        const pcmData = fs.readFileSync(this.pcmFilePath);
        console.log(`📖 [PCM-STREAM] Loaded ${pcmData.length} bytes of PCM data`);

        // Add PCM data to frame buffer
        this.frameBuffer = Buffer.concat([this.frameBuffer, pcmData]);

        // Process frames with timing similar to LiveKit streaming
        await this.processFramesWithTiming();
    }

    async processFramesWithTiming() {
        console.log(`🎬 [PCM-STREAM] Starting frame processing with real-time timing`);

        const frameIntervalMs = FRAME_DURATION_MS; // 60ms between frames
        let frameIndex = 0;

        while (this.frameBuffer.length >= OUTPUT_FRAME_SIZE_BYTES) {
            const frameStartTime = Date.now();

            // Extract one frame
            const frameData = this.frameBuffer.slice(0, OUTPUT_FRAME_SIZE_BYTES);
            this.frameBuffer = this.frameBuffer.slice(OUTPUT_FRAME_SIZE_BYTES);

            // Process frame (same logic as app.js)
            await this.processFrame(frameData, frameIndex);

            frameIndex++;

            // Calculate timing for next frame
            const frameProcessTime = Date.now() - frameStartTime;
            const nextFrameDelay = Math.max(0, frameIntervalMs - frameProcessTime);

            if (frameIndex <= 5 || frameIndex % 50 === 0) {
                console.log(`⏱️ [TIMING] Frame ${frameIndex}: processed in ${frameProcessTime}ms, next delay: ${nextFrameDelay}ms`);
            }

            // Wait for next frame timing
            if (nextFrameDelay > 0) {
                await new Promise(resolve => setTimeout(resolve, nextFrameDelay));
            }
        }

        console.log(`✅ [PCM-STREAM] Completed streaming ${frameIndex} frames`);
        console.log(`⏱️ [PCM-STREAM] Total duration: ${(Date.now() - this.startTime) / 1000}s`);
    }

    async processFrame(frameData, frameIndex) {
        if (!this.targetConnection) {
            console.error(`❌ [PROCESS] No target connection available`);
            return;
        }

        // Analyze frame content
        const samples = new Int16Array(frameData.buffer, frameData.byteOffset, frameData.length / 2);
        const maxAmplitude = Math.max(...samples.map(s => Math.abs(s)));
        const isSilent = maxAmplitude < 10;

        if (frameIndex <= 5 || frameIndex % 100 === 0) {
            console.log(`🔍 [FRAME] ${frameIndex}: samples=${samples.length}, max=${maxAmplitude}, first10=[${Array.from(samples.slice(0, 10)).join(',')}]`);
        }

        if (isSilent) {
            if (frameIndex <= 5) {
                console.log(`🔇 [PCM] Silent frame ${frameIndex} detected (max=${maxAmplitude}), skipping`);
            }
            return;
        }

        // Generate timestamp (same as app.js)
        const timestamp = (Date.now() - this.startTime) & 0xffffffff;

        // Encode and send (same logic as app.js processBufferedFrames)
        if (this.opusEncoder) {
            try {
                const alignedBuffer = Buffer.allocUnsafe(frameData.length);
                frameData.copy(alignedBuffer);
                const opusBuffer = this.opusEncoder.encode(alignedBuffer, OUTPUT_FRAME_SIZE_SAMPLES);

                if (frameIndex <= 3 || frameIndex % 100 === 0) {
                    console.log(`🎵 [OPUS] Frame ${frameIndex}: 24kHz 60ms PCM ${frameData.length}B → Opus ${opusBuffer.length}B`);
                }

                this.targetConnection.sendUdpMessage(opusBuffer, timestamp);
            } catch (err) {
                console.error(`❌ [OPUS] Encode error: ${err.message}`);
                console.error(`❌ [OPUS] Frame data length: ${frameData.length}, expected: ${OUTPUT_FRAME_SIZE_BYTES}`);
                console.error(`❌ [OPUS] Sample count: ${OUTPUT_FRAME_SIZE_SAMPLES}, sample rate: ${OUTPUT_SAMPLE_RATE}`);
                // Fallback to PCM
                this.targetConnection.sendUdpMessage(frameData, timestamp);
            }
        } else {
            // Send PCM directly if no Opus encoder
            if (frameIndex <= 3 || frameIndex % 100 === 0) {
                console.log(`⚠️ [PCM] Frame ${frameIndex}: Sending raw PCM ${frameData.length}B (no Opus encoder)`);
            }
            this.targetConnection.sendUdpMessage(frameData, timestamp);
        }
    }
}

module.exports = { PCMStreamer };

// Test function to be called from main app
async function testPCMStreaming(connection) {
    const pcmFilePath = path.join(__dirname, 'test.pcm');
    const streamer = new PCMStreamer(pcmFilePath, connection);

    console.log(`🧪 [TEST] Starting PCM streaming test for connection: ${connection.clientId}`);
    console.log(`🧪 [TEST] This will bypass LiveKit and stream test.pcm directly`);

    await streamer.streamPCM();

    console.log(`🧪 [TEST] PCM streaming test completed`);
}

// Export for use in app.js
module.exports.testPCMStreaming = testPCMStreaming;