// Audio Quality Diagnostic Tool
// Run this to compare audio processing between branches

const fs = require('fs');
const path = require('path');

console.log('🔍 Audio Quality Diagnostic Tool\n');
console.log('='.repeat(60));

// Check if we're in the right directory
const appJsPath = path.join(__dirname, 'app.js');
if (!fs.existsSync(appJsPath)) {
  console.error('❌ Error: app.js not found in current directory');
  process.exit(1);
}

const appJsContent = fs.readFileSync(appJsPath, 'utf8');

// Extract key audio processing parameters
const checks = [
  {
    name: 'AudioResampler Quality',
    regex: /AudioResampler\([^)]+,\s*AudioResamplerQuality\.(\w+)\)/,
    expected: 'QUICK'
  },
  {
    name: 'Worker Pool Size',
    regex: /new WorkerPoolManager\((\d+)\)/,
    expected: '4'
  },
  {
    name: 'Encode Timeout',
    regex: /type:\s*'encode'[^}]+},\s*(\d+)\)/,
    expected: '150'
  },
  {
    name: 'Decode Timeout',
    regex: /type:\s*'decode'[^}]+},\s*(\d+)\)/,
    expected: '150'
  },
  {
    name: 'Outgoing Sample Rate',
    regex: /const OUTGOING_SAMPLE_RATE\s*=\s*(\d+)/,
    expected: '24000'
  },
  {
    name: 'Incoming Sample Rate',
    regex: /const INCOMING_SAMPLE_RATE\s*=\s*(\d+)/,
    expected: '16000'
  },
  {
    name: 'Frame Duration',
    regex: /const OUTGOING_FRAME_DURATION_MS\s*=\s*(\d+)/,
    expected: '60'
  },
  {
    name: 'Metrics Logging',
    regex: /this\.workerPool\.startMetricsLogging\((\d+)\)/,
    isCommented: /\/\/\s*this\.workerPool\.startMetricsLogging/
  }
];

console.log('\n📊 Configuration Analysis:\n');

checks.forEach(check => {
  const match = appJsContent.match(check.regex);
  
  if (check.isCommented) {
    const isCommented = check.isCommented.test(appJsContent);
    console.log(`${check.name}:`);
    console.log(`  Status: ${isCommented ? '✅ COMMENTED OUT (Good)' : '⚠️  ACTIVE (May cause overhead)'}`);
  } else if (match) {
    const value = match[1];
    const status = value === check.expected ? '✅' : '⚠️';
    console.log(`${check.name}:`);
    console.log(`  Found: ${value}`);
    console.log(`  Expected: ${check.expected}`);
    console.log(`  Status: ${status}`);
  } else {
    console.log(`${check.name}:`);
    console.log(`  Status: ❌ NOT FOUND`);
  }
  console.log('');
});

// Check for potential performance issues
console.log('\n🔍 Potential Issues:\n');

const issues = [];

// Check for synchronous encoding fallback
if (appJsContent.includes('opusEncoder.encode') && appJsContent.includes('workerPool.encodeOpus')) {
  issues.push({
    severity: 'INFO',
    message: 'Both sync and async encoding paths exist (this is normal for fallback)'
  });
}

// Check for excessive logging
const logCount = (appJsContent.match(/console\.log/g) || []).length;
if (logCount > 100) {
  issues.push({
    severity: 'WARNING',
    message: `High number of console.log statements (${logCount}) - may impact performance`
  });
}

// Check for Buffer.concat in hot path
if (appJsContent.includes('Buffer.concat([this.frameBuffer')) {
  issues.push({
    severity: 'WARNING',
    message: 'Buffer.concat in audio processing loop - this creates new buffers frequently'
  });
}

// Check for await in tight loops
const awaitInLoopPattern = /while\s*\([^)]+\)\s*{[^}]*await[^}]*}/gs;
if (awaitInLoopPattern.test(appJsContent)) {
  issues.push({
    severity: 'INFO',
    message: 'Async/await in while loop detected - normal for audio streaming'
  });
}

if (issues.length === 0) {
  console.log('✅ No obvious issues detected\n');
} else {
  issues.forEach(issue => {
    const icon = issue.severity === 'WARNING' ? '⚠️' : 'ℹ️';
    console.log(`${icon} [${issue.severity}] ${issue.message}\n`);
  });
}

console.log('='.repeat(60));
console.log('\n💡 Recommendations:\n');
console.log('1. Ensure both branches use identical audio parameters');
console.log('2. Disable metrics logging in production (commented out)');
console.log('3. Test with same device and network conditions');
console.log('4. Check if ESP32 firmware is identical between tests');
console.log('5. Monitor CPU usage during audio streaming');
console.log('6. Check network latency and packet loss');
console.log('\n');
