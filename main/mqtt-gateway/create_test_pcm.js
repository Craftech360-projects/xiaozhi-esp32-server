// Create a proper test PCM file that matches LiveKit's audio format
// This will help ensure your PCM streaming test works correctly

const fs = require('fs');
const path = require('path');

// Audio parameters matching LiveKit's format
const SAMPLE_RATE = 24000; // 24kHz output (what your gateway sends)
const CHANNELS = 1;         // Mono
const DURATION_SECONDS = 10; // 10 second test file
const AMPLITUDE = 8000;     // Amplitude for test tones

function generateTestPCM() {
    console.log(`🎵 [CREATE-PCM] Generating test PCM file...`);
    console.log(`📊 [CREATE-PCM] Sample rate: ${SAMPLE_RATE}Hz, Channels: ${CHANNELS}, Duration: ${DURATION_SECONDS}s`);
    
    const totalSamples = SAMPLE_RATE * DURATION_SECONDS * CHANNELS;
    const buffer = Buffer.alloc(totalSamples * 2); // 2 bytes per sample (16-bit)
    
    let bufferIndex = 0;
    
    for (let i = 0; i < totalSamples; i++) {
        let sample = 0;
        
        // Create a test pattern with multiple tones
        const t = i / SAMPLE_RATE; // Time in seconds
        
        if (t < 2) {
            // First 2 seconds: 440Hz tone (A4)
            sample = Math.sin(2 * Math.PI * 440 * t) * AMPLITUDE;
        } else if (t < 4) {
            // Next 2 seconds: 880Hz tone (A5)
            sample = Math.sin(2 * Math.PI * 880 * t) * AMPLITUDE;
        } else if (t < 6) {
            // Next 2 seconds: Sweep from 200Hz to 2000Hz
            const freq = 200 + (2000 - 200) * ((t - 4) / 2);
            sample = Math.sin(2 * Math.PI * freq * t) * AMPLITUDE;
        } else if (t < 8) {
            // Next 2 seconds: White noise
            sample = (Math.random() - 0.5) * 2 * AMPLITUDE;
        } else {
            // Last 2 seconds: 1kHz tone with fade out
            const fadeOut = 1 - ((t - 8) / 2);
            sample = Math.sin(2 * Math.PI * 1000 * t) * AMPLITUDE * fadeOut;
        }
        
        // Clamp to 16-bit range
        sample = Math.max(-32768, Math.min(32767, Math.round(sample)));
        
        // Write as little-endian 16-bit signed integer
        buffer.writeInt16LE(sample, bufferIndex);
        bufferIndex += 2;
    }
    
    return buffer;
}

function generateSilentPCM() {
    console.log(`🔇 [CREATE-PCM] Generating silent PCM file for testing...`);
    
    const totalSamples = SAMPLE_RATE * 2 * CHANNELS; // 2 seconds of silence
    const buffer = Buffer.alloc(totalSamples * 2); // All zeros = silence
    
    return buffer;
}

function generateMusicLikePCM() {
    console.log(`🎼 [CREATE-PCM] Generating music-like PCM file...`);
    
    const totalSamples = SAMPLE_RATE * DURATION_SECONDS * CHANNELS;
    const buffer = Buffer.alloc(totalSamples * 2);
    
    let bufferIndex = 0;
    
    // Create a simple chord progression
    const chords = [
        [261.63, 329.63, 392.00], // C major
        [293.66, 369.99, 440.00], // D minor
        [329.63, 415.30, 493.88], // E minor
        [349.23, 440.00, 523.25], // F major
    ];
    
    for (let i = 0; i < totalSamples; i++) {
        const t = i / SAMPLE_RATE;
        const chordIndex = Math.floor(t / 2.5) % chords.length; // Change chord every 2.5 seconds
        const chord = chords[chordIndex];
        
        let sample = 0;
        
        // Add each note in the chord
        for (const freq of chord) {
            sample += Math.sin(2 * Math.PI * freq * t) * (AMPLITUDE / chord.length);
        }
        
        // Add some envelope (attack, decay, sustain, release)
        const chordTime = t % 2.5;
        let envelope = 1;
        
        if (chordTime < 0.1) {
            // Attack
            envelope = chordTime / 0.1;
        } else if (chordTime < 0.3) {
            // Decay
            envelope = 1 - (chordTime - 0.1) / 0.2 * 0.3;
        } else if (chordTime < 2.0) {
            // Sustain
            envelope = 0.7;
        } else {
            // Release
            envelope = 0.7 * (1 - (chordTime - 2.0) / 0.5);
        }
        
        sample *= envelope;
        
        // Clamp to 16-bit range
        sample = Math.max(-32768, Math.min(32767, Math.round(sample)));
        
        // Write as little-endian 16-bit signed integer
        buffer.writeInt16LE(sample, bufferIndex);
        bufferIndex += 2;
    }
    
    return buffer;
}

// Main execution
async function main() {
    try {
        console.log(`🎵 [CREATE-PCM] Creating test PCM files for jitter testing...`);
        
        // Generate different types of test files
        const testPCM = generateTestPCM();
        const silentPCM = generateSilentPCM();
        const musicPCM = generateMusicLikePCM();
        
        // Write files
        const testPath = path.join(__dirname, 'test.pcm');
        const silentPath = path.join(__dirname, 'test_silent.pcm');
        const musicPath = path.join(__dirname, 'test_music.pcm');
        
        fs.writeFileSync(testPath, testPCM);
        fs.writeFileSync(silentPath, silentPCM);
        fs.writeFileSync(musicPath, musicPCM);
        
        console.log(`✅ [CREATE-PCM] Created test files:`);
        console.log(`   📁 ${testPath} (${testPCM.length} bytes) - Multi-tone test`);
        console.log(`   📁 ${silentPath} (${silentPCM.length} bytes) - Silent test`);
        console.log(`   📁 ${musicPath} (${musicPCM.length} bytes) - Music-like test`);
        
        // Analyze existing test.pcm if it exists
        if (fs.existsSync(testPath)) {
            const existingStats = fs.statSync(testPath);
            const expectedDuration = existingStats.size / 2 / SAMPLE_RATE;
            console.log(`📊 [ANALYZE] Existing test.pcm: ${existingStats.size} bytes, ~${expectedDuration.toFixed(2)}s duration`);
        }
        
        console.log(`🧪 [READY] Test PCM files ready for jitter testing!`);
        console.log(`💡 [TIP] Use 'test_music.pcm' for the most realistic audio test`);
        
    } catch (error) {
        console.error(`❌ [CREATE-PCM] Error creating test files: ${error.message}`);
    }
}

// Export for use as module or run directly
if (require.main === module) {
    main();
}

module.exports = { generateTestPCM, generateSilentPCM, generateMusicLikePCM };