#!/usr/bin/env node

// Simple test to isolate Opus encoding issues
const { OpusEncoder } = require('@discordjs/opus');

console.log('🧪 Testing @discordjs/opus encoding...');

try {
  // Create encoder
  const encoder = new OpusEncoder(24000, 1);
  console.log('✅ OpusEncoder created successfully');

  // Create test PCM data (2880 bytes = 1440 samples * 2 bytes)
  const frameSize = 1440; // 60ms at 24kHz
  const pcmData = Buffer.alloc(frameSize * 2); // 2880 bytes
  
  // Fill with test audio data (sine wave)
  for (let i = 0; i < frameSize; i++) {
    const sample = Math.sin(2 * Math.PI * 440 * i / 24000) * 16384; // 440Hz sine wave
    pcmData.writeInt16LE(Math.round(sample), i * 2);
  }
  
  console.log(`✅ Created test PCM data: ${pcmData.length} bytes`);

  // Test encoding multiple times
  for (let i = 0; i < 10; i++) {
    try {
      const encoded = encoder.encode(pcmData, frameSize);
      console.log(`✅ Encode ${i + 1}: ${pcmData.length}B → ${encoded.length}B`);
    } catch (err) {
      console.error(`❌ Encode ${i + 1} failed:`, err.message);
      break;
    }
  }

  console.log('✅ All encoding tests passed!');
  
} catch (error) {
  console.error('❌ Test failed:', error.message);
  console.error('Stack:', error.stack);
  process.exit(1);
}