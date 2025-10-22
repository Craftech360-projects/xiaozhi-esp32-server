// Convert WAV file to PCM format for jitter testing
// This will convert your test_pcm.wav to the correct PCM format

const fs = require('fs');
const path = require('path');

// Audio parameters matching your gateway's output format
const TARGET_SAMPLE_RATE = 24000; // 24kHz output
const TARGET_CHANNELS = 1;         // Mono
const TARGET_BITS_PER_SAMPLE = 16; // 16-bit

class WAVConverter {
    constructor() {
        this.wavHeader = null;
        this.audioData = null;
    }

    parseWAVHeader(buffer) {
        // Parse WAV header
        const header = {
            chunkID: buffer.toString('ascii', 0, 4),
            chunkSize: buffer.readUInt32LE(4),
            format: buffer.toString('ascii', 8, 12),
            subchunk1ID: buffer.toString('ascii', 12, 16),
            subchunk1Size: buffer.readUInt32LE(16),
            audioFormat: buffer.readUInt16LE(20),
            numChannels: buffer.readUInt16LE(22),
            sampleRate: buffer.readUInt32LE(24),
            byteRate: buffer.readUInt32LE(28),
            blockAlign: buffer.readUInt16LE(32),
            bitsPerSample: buffer.readUInt16LE(34),
            subchunk2ID: buffer.toString('ascii', 36, 40),
            subchunk2Size: buffer.readUInt32LE(40)
        };

        console.log(`📊 [WAV-INFO] Original WAV file properties:`);
        console.log(`   🎵 Sample Rate: ${header.sampleRate}Hz`);
        console.log(`   🔊 Channels: ${header.numChannels}`);
        console.log(`   📏 Bits per Sample: ${header.bitsPerSample}`);
        console.log(`   📦 Audio Format: ${header.audioFormat} (1=PCM)`);
        console.log(`   📁 Data Size: ${header.subchunk2Size} bytes`);
        console.log(`   ⏱️ Duration: ${(header.subchunk2Size / header.byteRate).toFixed(2)}s`);

        return header;
    }

    convertSampleRate(inputBuffer, inputSampleRate, outputSampleRate, channels) {
        if (inputSampleRate === outputSampleRate) {
            return inputBuffer;
        }

        console.log(`🔄 [RESAMPLE] Converting ${inputSampleRate}Hz → ${outputSampleRate}Hz`);

        const inputSamples = inputBuffer.length / 2 / channels; // 16-bit samples
        const outputSamples = Math.floor(inputSamples * outputSampleRate / inputSampleRate);
        const outputBuffer = Buffer.alloc(outputSamples * 2 * channels);

        const ratio = inputSampleRate / outputSampleRate;

        for (let i = 0; i < outputSamples; i++) {
            const inputIndex = i * ratio;
            const inputIndexFloor = Math.floor(inputIndex);
            const inputIndexCeil = Math.min(inputIndexFloor + 1, inputSamples - 1);
            const fraction = inputIndex - inputIndexFloor;

            for (let ch = 0; ch < channels; ch++) {
                // Linear interpolation
                const sample1 = inputBuffer.readInt16LE((inputIndexFloor * channels + ch) * 2);
                const sample2 = inputBuffer.readInt16LE((inputIndexCeil * channels + ch) * 2);
                const interpolatedSample = Math.round(sample1 + (sample2 - sample1) * fraction);

                outputBuffer.writeInt16LE(interpolatedSample, (i * channels + ch) * 2);
            }
        }

        return outputBuffer;
    }

    convertToMono(inputBuffer, channels) {
        if (channels === 1) {
            return inputBuffer;
        }

        console.log(`🔄 [MONO] Converting ${channels} channels → 1 channel`);

        const samples = inputBuffer.length / 2 / channels;
        const outputBuffer = Buffer.alloc(samples * 2);

        for (let i = 0; i < samples; i++) {
            let sum = 0;
            for (let ch = 0; ch < channels; ch++) {
                sum += inputBuffer.readInt16LE((i * channels + ch) * 2);
            }
            const monoSample = Math.round(sum / channels);
            outputBuffer.writeInt16LE(monoSample, i * 2);
        }

        return outputBuffer;
    }

    async convertWAVToPCM(inputPath, outputPath) {
        try {
            console.log(`🎵 [CONVERT] Converting WAV to PCM: ${inputPath} → ${outputPath}`);

            // Read WAV file
            const wavBuffer = fs.readFileSync(inputPath);
            console.log(`📖 [CONVERT] Read ${wavBuffer.length} bytes from WAV file`);

            // Parse WAV header
            const header = this.parseWAVHeader(wavBuffer);

            // Validate WAV format
            if (header.chunkID !== 'RIFF' || header.format !== 'WAVE') {
                throw new Error('Invalid WAV file format');
            }

            if (header.audioFormat !== 1) {
                throw new Error(`Unsupported audio format: ${header.audioFormat} (only PCM supported)`);
            }

            // Extract audio data (skip 44-byte header)
            let audioData = wavBuffer.slice(44);
            console.log(`🎵 [CONVERT] Extracted ${audioData.length} bytes of audio data`);

            // Convert to mono if needed
            if (header.numChannels !== TARGET_CHANNELS) {
                audioData = this.convertToMono(audioData, header.numChannels);
                console.log(`✅ [MONO] Converted to mono: ${audioData.length} bytes`);
            }

            // Resample if needed
            if (header.sampleRate !== TARGET_SAMPLE_RATE) {
                audioData = this.convertSampleRate(
                    audioData, 
                    header.sampleRate, 
                    TARGET_SAMPLE_RATE, 
                    TARGET_CHANNELS
                );
                console.log(`✅ [RESAMPLE] Resampled to ${TARGET_SAMPLE_RATE}Hz: ${audioData.length} bytes`);
            }

            // Write PCM file
            fs.writeFileSync(outputPath, audioData);

            // Calculate final properties
            const finalSamples = audioData.length / 2;
            const finalDuration = finalSamples / TARGET_SAMPLE_RATE;

            console.log(`✅ [CONVERT] Conversion completed!`);
            console.log(`📊 [FINAL] Output PCM properties:`);
            console.log(`   🎵 Sample Rate: ${TARGET_SAMPLE_RATE}Hz`);
            console.log(`   🔊 Channels: ${TARGET_CHANNELS}`);
            console.log(`   📏 Bits per Sample: ${TARGET_BITS_PER_SAMPLE}`);
            console.log(`   📁 File Size: ${audioData.length} bytes`);
            console.log(`   ⏱️ Duration: ${finalDuration.toFixed(2)}s`);
            console.log(`   📦 Total Samples: ${finalSamples}`);

            return {
                success: true,
                outputPath: outputPath,
                sampleRate: TARGET_SAMPLE_RATE,
                channels: TARGET_CHANNELS,
                duration: finalDuration,
                fileSize: audioData.length
            };

        } catch (error) {
            console.error(`❌ [CONVERT] Error converting WAV to PCM: ${error.message}`);
            return {
                success: false,
                error: error.message
            };
        }
    }

    // Analyze PCM file properties
    analyzePCM(pcmPath) {
        try {
            const stats = fs.statSync(pcmPath);
            const samples = stats.size / 2; // 16-bit samples
            const duration = samples / TARGET_SAMPLE_RATE;

            console.log(`📊 [ANALYZE] PCM file analysis: ${pcmPath}`);
            console.log(`   📁 File Size: ${stats.size} bytes`);
            console.log(`   📦 Total Samples: ${samples}`);
            console.log(`   ⏱️ Duration: ${duration.toFixed(2)}s`);
            console.log(`   🎵 Sample Rate: ${TARGET_SAMPLE_RATE}Hz (assumed)`);
            console.log(`   🔊 Channels: ${TARGET_CHANNELS} (assumed)`);

            // Read first few samples for analysis
            const buffer = fs.readFileSync(pcmPath);
            const firstSamples = [];
            for (let i = 0; i < Math.min(10, samples); i++) {
                firstSamples.push(buffer.readInt16LE(i * 2));
            }

            console.log(`   🔍 First 10 samples: [${firstSamples.join(', ')}]`);

            // Check if it's silent
            const maxAmplitude = Math.max(...firstSamples.map(s => Math.abs(s)));
            if (maxAmplitude < 10) {
                console.log(`   🔇 WARNING: Audio appears to be silent (max amplitude: ${maxAmplitude})`);
            } else {
                console.log(`   🔊 Audio detected (max amplitude: ${maxAmplitude})`);
            }

            return {
                fileSize: stats.size,
                samples: samples,
                duration: duration,
                maxAmplitude: maxAmplitude,
                isSilent: maxAmplitude < 10
            };

        } catch (error) {
            console.error(`❌ [ANALYZE] Error analyzing PCM: ${error.message}`);
            return null;
        }
    }
}

// Main execution
async function main() {
    const converter = new WAVConverter();

    const inputWAV = path.join(__dirname, 'test_pcm.wav');
    const outputPCM = path.join(__dirname, 'test.pcm');

    console.log(`🎵 [MAIN] Starting WAV to PCM conversion...`);
    console.log(`📂 [MAIN] Input: ${inputWAV}`);
    console.log(`📂 [MAIN] Output: ${outputPCM}`);

    // Check if input file exists
    if (!fs.existsSync(inputWAV)) {
        console.error(`❌ [MAIN] Input WAV file not found: ${inputWAV}`);
        console.log(`💡 [TIP] Make sure your WAV file is named 'test_pcm.wav' in the mqtt-gateway directory`);
        return;
    }

    // Convert WAV to PCM
    const result = await converter.convertWAVToPCM(inputWAV, outputPCM);

    if (result.success) {
        console.log(`🎉 [SUCCESS] WAV file converted successfully!`);
        console.log(`📁 [SUCCESS] PCM file created: ${result.outputPath}`);
        
        // Analyze the created PCM file
        console.log(`\n🔍 [VERIFY] Verifying created PCM file...`);
        converter.analyzePCM(outputPCM);
        
        console.log(`\n🧪 [READY] PCM file is ready for jitter testing!`);
        console.log(`💡 [NEXT] Your MQTT gateway will now automatically stream this PCM file when a client connects`);
        
    } else {
        console.error(`❌ [FAILED] Conversion failed: ${result.error}`);
    }
}

// Export for use as module or run directly
if (require.main === module) {
    main();
}

module.exports = { WAVConverter };