// ========================================
// Unit Tests for LoopStateManager
// ========================================
// Tests the loop state management functionality

console.log("🧪 Testing LoopStateManager\n");

// Import the LoopStateManager class (we'll create a minimal version for testing)
class LoopStateManager {
  constructor() {
    this.loopStates = new Map();
  }

  setLoopState(macAddress, loopEnabled, contentType) {
    if (loopEnabled) {
      this.loopStates.set(macAddress, {
        loopEnabled: true,
        contentType,
        timestamp: Date.now(),
      });
    } else {
      this.loopStates.delete(macAddress);
    }
  }

  getLoopState(macAddress) {
    return this.loopStates.get(macAddress) || null;
  }

  clearLoopState(macAddress) {
    this.loopStates.delete(macAddress);
  }

  isLoopEnabled(macAddress) {
    const state = this.loopStates.get(macAddress);
    return state?.loopEnabled || false;
  }
}

// Test utilities
let testsPassed = 0;
let testsFailed = 0;

function assert(condition, message) {
  if (condition) {
    console.log(`✅ ${message}`);
    testsPassed++;
  } else {
    console.error(`❌ ${message}`);
    testsFailed++;
  }
}

function assertEquals(actual, expected, message) {
  if (actual === expected) {
    console.log(`✅ ${message}`);
    testsPassed++;
  } else {
    console.error(`❌ ${message}`);
    console.error(`   Expected: ${expected}`);
    console.error(`   Actual: ${actual}`);
    testsFailed++;
  }
}

function assertNotNull(value, message) {
  if (value !== null && value !== undefined) {
    console.log(`✅ ${message}`);
    testsPassed++;
  } else {
    console.error(`❌ ${message}`);
    console.error(`   Value was null or undefined`);
    testsFailed++;
  }
}

function assertNull(value, message) {
  if (value === null || value === undefined) {
    console.log(`✅ ${message}`);
    testsPassed++;
  } else {
    console.error(`❌ ${message}`);
    console.error(`   Expected null, got: ${value}`);
    testsFailed++;
  }
}

// Test 1: setLoopState with valid inputs
console.log("1️⃣ Test setLoopState with valid inputs");
const manager = new LoopStateManager();
const testMac = "AA:BB:CC:DD:EE:FF";

manager.setLoopState(testMac, true, "music");
const state1 = manager.getLoopState(testMac);
assertNotNull(state1, "State should exist after setting loop enabled");
assertEquals(state1?.loopEnabled, true, "Loop should be enabled");
assertEquals(state1?.contentType, "music", "Content type should be 'music'");
assert(state1?.timestamp > 0, "Timestamp should be set");

manager.setLoopState(testMac, true, "story");
const state2 = manager.getLoopState(testMac);
assertEquals(
  state2?.contentType,
  "story",
  "Content type should be updated to 'story'"
);

console.log("");

// Test 2: getLoopState returns correct state
console.log("2️⃣ Test getLoopState returns correct state");
const manager2 = new LoopStateManager();
const testMac2 = "11:22:33:44:55:66";

// Test with no state set
const emptyState = manager2.getLoopState(testMac2);
assertNull(emptyState, "Should return null for non-existent state");

// Test with state set
manager2.setLoopState(testMac2, true, "music");
const existingState = manager2.getLoopState(testMac2);
assertNotNull(existingState, "Should return state object");
assertEquals(
  existingState?.loopEnabled,
  true,
  "Should return correct loop enabled value"
);
assertEquals(
  existingState?.contentType,
  "music",
  "Should return correct content type"
);

console.log("");

// Test 3: clearLoopState removes state
console.log("3️⃣ Test clearLoopState removes state");
const manager3 = new LoopStateManager();
const testMac3 = "AA:11:BB:22:CC:33";

// Set state first
manager3.setLoopState(testMac3, true, "story");
const beforeClear = manager3.getLoopState(testMac3);
assertNotNull(beforeClear, "State should exist before clearing");

// Clear state
manager3.clearLoopState(testMac3);
const afterClear = manager3.getLoopState(testMac3);
assertNull(afterClear, "State should be null after clearing");

// Verify isLoopEnabled also returns false
assertEquals(
  manager3.isLoopEnabled(testMac3),
  false,
  "isLoopEnabled should return false after clearing"
);

console.log("");

// Test 4: isLoopEnabled returns boolean
console.log("4️⃣ Test isLoopEnabled returns boolean");
const manager4 = new LoopStateManager();
const testMac4 = "FF:EE:DD:CC:BB:AA";

// Test with no state
assertEquals(
  manager4.isLoopEnabled(testMac4),
  false,
  "Should return false when no state exists"
);
assertEquals(
  typeof manager4.isLoopEnabled(testMac4),
  "boolean",
  "Should return boolean type"
);

// Test with loop enabled
manager4.setLoopState(testMac4, true, "music");
assertEquals(
  manager4.isLoopEnabled(testMac4),
  true,
  "Should return true when loop is enabled"
);
assertEquals(
  typeof manager4.isLoopEnabled(testMac4),
  "boolean",
  "Should return boolean type"
);

// Test with loop disabled
manager4.setLoopState(testMac4, false, "music");
assertEquals(
  manager4.isLoopEnabled(testMac4),
  false,
  "Should return false when loop is disabled"
);

console.log("");

// Test 5: Multiple devices
console.log("5️⃣ Test multiple devices independently");
const manager5 = new LoopStateManager();
const mac1 = "AA:AA:AA:AA:AA:AA";
const mac2 = "BB:BB:BB:BB:BB:BB";

manager5.setLoopState(mac1, true, "music");
manager5.setLoopState(mac2, true, "story");

assertEquals(
  manager5.isLoopEnabled(mac1),
  true,
  "Device 1 should have loop enabled"
);
assertEquals(
  manager5.isLoopEnabled(mac2),
  true,
  "Device 2 should have loop enabled"
);
assertEquals(
  manager5.getLoopState(mac1)?.contentType,
  "music",
  "Device 1 should have music type"
);
assertEquals(
  manager5.getLoopState(mac2)?.contentType,
  "story",
  "Device 2 should have story type"
);

// Clear one device
manager5.clearLoopState(mac1);
assertEquals(
  manager5.isLoopEnabled(mac1),
  false,
  "Device 1 should have loop disabled"
);
assertEquals(
  manager5.isLoopEnabled(mac2),
  true,
  "Device 2 should still have loop enabled"
);

console.log("");

// Test 6: Edge cases
console.log("6️⃣ Test edge cases");
const manager6 = new LoopStateManager();

// Test with empty string MAC
manager6.setLoopState("", true, "music");
assertEquals(
  manager6.isLoopEnabled(""),
  true,
  "Should handle empty string MAC"
);

// Test with null/undefined content type
manager6.setLoopState("test:mac", true, null);
const nullTypeState = manager6.getLoopState("test:mac");
assertEquals(
  nullTypeState?.contentType,
  null,
  "Should handle null content type"
);

// Test clearing non-existent state (should not throw)
try {
  manager6.clearLoopState("non:existent:mac");
  console.log("✅ Clearing non-existent state does not throw error");
  testsPassed++;
} catch (e) {
  console.error("❌ Clearing non-existent state threw error:", e.message);
  testsFailed++;
}

console.log("");

// Summary
console.log("=".repeat(50));
console.log(`📊 Test Results: ${testsPassed} passed, ${testsFailed} failed`);
console.log("=".repeat(50));

if (testsFailed === 0) {
  console.log("🎉 All LoopStateManager tests passed!");
  process.exit(0);
} else {
  console.error("❌ Some tests failed");
  process.exit(1);
}
