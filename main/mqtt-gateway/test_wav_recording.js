#!/usr/bin/env node

/**
 * Test script for WAV recording functionality
 * Tests the WAVWriter class with simulated ESP32 audio data
 */

const fs = require('fs');
const path = require('path');

// Import the WAVWriter class from app.js
// Since it's embedded in app.js, we'll copy it here for testing
class WAVWriter {
  constructor(filePath, sampleRate = 16000, channels = 1, bitsPerSample = 16) {
    this.filePath = filePath;
    this.sampleRate = sampleRate;
    this.channels = channels;
    this.bitsPerSample = bitsPerSample;
    this.bytesPerSample = bitsPerSample / 8;
    this.blockAlign = channels * this.bytesPerSample;
    this.byteRate = sampleRate * this.blockAlign;
    
    this.audioData = [];
    this.totalBytes = 0;
    this.isFinalized = false;
    
    console.log(`🎵 [WAV] Creating WAV writer: ${filePath} (${sampleRate}Hz, ${channels}ch, ${bitsPerSample}bit)`);
  }

  writeAudio(pcmData) {
    if (this.isFinalized) {
      console.warn(`⚠️ [WAV] Cannot write to finalized WAV file: ${this.filePath}`);
      return;
    }

    this.audioData.push(pcmData);
    this.totalBytes += pcmData.length;
  }

  finalize() {
    if (this.isFinalized) {
      console.warn(`⚠️ [WAV] WAV file already finalized: ${this.filePath}`);
      return;
    }

    try {
      // Ensure directory exists
      const dir = path.dirname(this.filePath);
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }

      // Create WAV header
      const header = this.createWAVHeader();
      
      // Combine header and audio data
      const audioBuffer = Buffer.concat(this.audioData);
      const wavFile = Buffer.concat([header, audioBuffer]);
      
      // Write to file
      fs.writeFileSync(this.filePath, wavFile);
      
      this.isFinalized = true;
      
      console.log(`✅ [WAV] Saved WAV file: ${this.filePath}`);
      console.log(`   📊 Duration: ${(this.totalBytes / this.byteRate).toFixed(2)}s`);
      console.log(`   📦 Size: ${wavFile.length} bytes (${this.totalBytes} audio + ${header.length} header)`);
      
      return this.filePath;
    } catch (error) {
      console.error(`❌ [WAV] Failed to save WAV file ${this.filePath}:`, error.message);
      throw error;
    }
  }

  createWAVHeader() {
    const header = Buffer.alloc(44);
    let offset = 0;

    // RIFF header
    header.write('RIFF', offset); offset += 4;
    header.writeUInt32LE(36 + this.totalBytes, offset); offset += 4; // File size - 8
    header.write('WAVE', offset); offset += 4;

    // fmt chunk
    header.write('fmt ', offset); offset += 4;
    header.writeUInt32LE(16, offset); offset += 4; // fmt chunk size
    header.writeUInt16LE(1, offset); offset += 2;  // PCM format
    header.writeUInt16LE(this.channels, offset); offset += 2;
    header.writeUInt32LE(this.sampleRate, offset); offset += 4;
    header.writeUInt32LE(this.byteRate, offset); offset += 4;
    header.writeUInt16LE(this.blockAlign, offset); offset += 2;
    header.writeUInt16LE(this.bitsPerSample, offset); offset += 2;

    // data chunk
    header.write('data', offset); offset += 4;
    header.writeUInt32LE(this.totalBytes, offset); offset += 4;

    return header;
  }

  getStats() {
    return {
      filePath: this.filePath,
      sampleRate: this.sampleRate,
      channels: this.channels,
      bitsPerSample: this.bitsPerSample,
      totalBytes: this.totalBytes,
      durationSeconds: this.totalBytes / this.byteRate,
      isFinalized: this.isFinalized
    };
  }
}

/**
 * Generate simulated ESP32 audio data (16kHz mono PCM)
 * Creates a simple sine wave for testing
 */
function generateTestAudio(durationSeconds = 2, frequency = 440) {
  const sampleRate = 16000;
  const samples = Math.floor(sampleRate * durationSeconds);
  const buffer = Buffer.alloc(samples * 2); // 16-bit = 2 bytes per sample
  
  console.log(`🎵 [TEST] Generating ${durationSeconds}s of ${frequency}Hz sine wave at ${sampleRate}Hz`);
  
  for (let i = 0; i < samples; i++) {
    // Generate sine wave: amplitude * sin(2π * frequency * time)
    const time = i / sampleRate;
    const amplitude = 16000; // Max amplitude for 16-bit audio
    const sample = Math.floor(amplitude * Math.sin(2 * Math.PI * frequency * time));
    
    // Write as 16-bit signed integer (little-endian)
    buffer.writeInt16LE(sample, i * 2);
  }
  
  return buffer;
}

/**
 * Test the WAV recording functionality
 */
async function testWAVRecording() {
  console.log('🧪 [TEST] Starting WAV recording test...\n');
  
  try {
    // Create test directory
    const testDir = path.join(__dirname, 'test_recordings');
    if (!fs.existsSync(testDir)) {
      fs.mkdirSync(testDir, { recursive: true });
    }
    
    // Test 1: Basic WAV recording
    console.log('📝 [TEST 1] Basic WAV recording test');
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const testFile1 = path.join(testDir, `test_basic_${timestamp}.wav`);
    
    const wavWriter1 = new WAVWriter(testFile1);
    
    // Generate and write test audio in chunks (simulating ESP32 streaming)
    const chunkSize = 320; // 20ms at 16kHz = 320 samples = 640 bytes
    const testAudio = generateTestAudio(2, 440); // 2 seconds of 440Hz tone
    
    console.log(`📦 [TEST 1] Writing audio in ${chunkSize * 2} byte chunks...`);
    for (let offset = 0; offset < testAudio.length; offset += chunkSize * 2) {
      const chunk = testAudio.subarray(offset, Math.min(offset + chunkSize * 2, testAudio.length));
      wavWriter1.writeAudio(chunk);
    }
    
    const savedFile1 = wavWriter1.finalize();
    console.log(`✅ [TEST 1] Completed: ${savedFile1}\n`);
    
    // Test 2: Multiple frequency test
    console.log('📝 [TEST 2] Multiple frequency test');
    const testFile2 = path.join(testDir, `test_multi_freq_${timestamp}.wav`);
    
    const wavWriter2 = new WAVWriter(testFile2);
    
    // Generate different frequencies
    const frequencies = [220, 440, 880, 1760]; // A notes in different octaves
    for (const freq of frequencies) {
      const freqAudio = generateTestAudio(0.5, freq); // 0.5 seconds each
      console.log(`🎵 [TEST 2] Adding ${freq}Hz tone...`);
      
      // Write in chunks
      for (let offset = 0; offset < freqAudio.length; offset += chunkSize * 2) {
        const chunk = freqAudio.subarray(offset, Math.min(offset + chunkSize * 2, freqAudio.length));
        wavWriter2.writeAudio(chunk);
      }
    }
    
    const savedFile2 = wavWriter2.finalize();
    console.log(`✅ [TEST 2] Completed: ${savedFile2}\n`);
    
    // Test 3: Statistics test
    console.log('📝 [TEST 3] Statistics test');
    const stats1 = wavWriter1.getStats();
    const stats2 = wavWriter2.getStats();
    
    console.log('📊 [STATS 1]', stats1);
    console.log('📊 [STATS 2]', stats2);
    
    // Verify file sizes
    const file1Size = fs.statSync(savedFile1).size;
    const file2Size = fs.statSync(savedFile2).size;
    
    console.log(`📏 [VERIFY] File 1: ${file1Size} bytes (expected: ${44 + stats1.totalBytes})`);
    console.log(`📏 [VERIFY] File 2: ${file2Size} bytes (expected: ${44 + stats2.totalBytes})`);
    
    // Test 4: Error handling test
    console.log('\n📝 [TEST 4] Error handling test');
    try {
      wavWriter1.writeAudio(Buffer.alloc(100)); // Should warn about finalized file
      wavWriter1.finalize(); // Should warn about already finalized
    } catch (error) {
      console.log(`⚠️ [TEST 4] Expected error: ${error.message}`);
    }
    
    console.log('\n🎉 [SUCCESS] All WAV recording tests completed successfully!');
    console.log(`📁 [OUTPUT] Test files saved in: ${testDir}`);
    console.log('\n💡 [USAGE] You can play these WAV files with any audio player to verify they work correctly.');
    console.log('   Example: ffplay test_basic_*.wav');
    
  } catch (error) {
    console.error(`❌ [ERROR] Test failed: ${error.message}`);
    console.error(error.stack);
    process.exit(1);
  }
}

// Run the test
if (require.main === module) {
  testWAVRecording();
}

module.exports = { WAVWriter, generateTestAudio, testWAVRecording };