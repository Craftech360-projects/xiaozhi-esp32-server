# Quick Test Guide - Force Update Feature

## Pre-Test Checklist

```bash
# 1. Check if backend is running
curl http://localhost:8002/ota/
# Expected: "OTA interface running normally..."

# 2. Check database connection
# Verify server logs show successful database connection
```

---

## Test Scenarios Summary

### 🔴 CRITICAL Tests (Must Pass)

#### Test 1: Normal Mode - Device with Older Version
```bash
curl -X POST http://localhost:8002/ota/ \
  -H "Device-Id: AA:BB:CC:DD:EE:FF" \
  -H "Content-Type: application/json" \
  -d '{"application":{"version":"1.5.0"},"board":{"type":"ESP32"}}'
```
**Expected:** `firmware.version = "2.0.0"` (latest), `firmware.url` = download URL
**Result:** ⬜ PENDING

---

#### Test 2: Force Update - Device with Newer Version (DOWNGRADE)
**Pre-requisite:** Enable force update for ESP32 v2.1.0 in UI

```bash
curl -X POST http://localhost:8002/ota/ \
  -H "Device-Id: AA:BB:CC:DD:EE:FF" \
  -H "Content-Type: application/json" \
  -d '{"application":{"version":"2.5.0"},"board":{"type":"ESP32"}}'
```
**Expected:** `firmware.version = "2.1.0"` (forced), `firmware.url` = download URL
**Result:** ⬜ PENDING

---

#### Test 3: Force Update - Device Already on Forced Version
```bash
curl -X POST http://localhost:8002/ota/ \
  -H "Device-Id: AA:BB:CC:DD:EE:FF" \
  -H "Content-Type: application/json" \
  -d '{"application":{"version":"2.1.0"},"board":{"type":"ESP32"}}'
```
**Expected:** `firmware.version = "2.1.0"`, `firmware.url = "null"` (no update needed)
**Result:** ⬜ PENDING

---

### 🟡 Important Tests

#### Test 4: Only One Force Update Per Type
**Steps:**
1. Enable force update on Firmware A (ESP32, v2.0.0)
2. Enable force update on Firmware B (ESP32, v2.1.0)
3. Check database: `SELECT id, version, force_update FROM ai_ota WHERE type='ESP32';`

**Expected:** Only Firmware B has force_update=1, Firmware A has force_update=0
**Result:** ⬜ PENDING

---

#### Test 5: Disable Force Update Returns to Normal
**Steps:**
1. With force update enabled, disable it via UI
2. Run Test 1 again

**Expected:** Normal behavior (latest version, no downgrade)
**Result:** ⬜ PENDING

---

### 🟢 Optional Tests

#### Test 6: Frontend UI
- ⬜ Force Update column visible
- ⬜ Toggle switches work
- ⬜ Confirmation dialogs appear
- ⬜ Only one toggle active per type

---

## Backend Log Verification

After running tests, check logs for:

```
✅ Force update ACTIVE:
🔒 Force update ACTIVE for type: ESP32, forced version: 2.1.0, device current: 2.5.0

✅ Downgrade scenario:
📥 Force update download URL generated - Device will DOWNGRADE to version 2.1.0

✅ Device compliant:
✅ Device already on forced version 2.1.0, no download needed

✅ Force update response:
📦 FORCE OTA Response - Type: ESP32, Current: 2.5.0, Target: 2.1.0, URL: http://...

✅ Normal mode:
📦 Normal OTA Response - Type: ESP32, Current: 1.5.0, Latest: 2.0.0, URL: http://...
```

---

## Quick Database Checks

```sql
-- Check if migration applied
SHOW COLUMNS FROM ai_ota LIKE 'force_update';

-- Check current force update status
SELECT id, firmware_name, version, type, force_update
FROM ai_ota
ORDER BY type, version;

-- Check which firmware has force update enabled
SELECT * FROM ai_ota WHERE force_update = 1;
```

---

## Test Results

| Test # | Scenario | Status | Notes |
|--------|----------|--------|-------|
| 1 | Normal Mode - Older Version | ⬜ | |
| 2 | Force Update - Downgrade | ⬜ | **CRITICAL** |
| 3 | Force Update - Already Compliant | ⬜ | |
| 4 | Only One Force Per Type | ⬜ | |
| 5 | Disable Returns to Normal | ⬜ | |
| 6 | Frontend UI | ⬜ | |

**Legend:** ⬜ Pending | ✅ Passed | ❌ Failed

---

## Troubleshooting

**Issue:** Server not responding
- Check if running: `curl http://localhost:8002/ota/`
- Check logs for errors
- Verify port 8002 is free

**Issue:** Database error
- Check application-local.yml configuration
- Verify MySQL is running on 192.168.1.6:3307
- Test connection: `mysql -h 192.168.1.6 -P 3307 -u manager -p`

**Issue:** Force update not working
- Verify force_update column exists
- Check if force_update = 1 for target firmware
- Review backend logs for "Force update ACTIVE" message

**Issue:** Downgrade not happening
- Ensure force update is enabled (force_update=1)
- Verify buildFirmwareInfo() checks forceUpdate FIRST
- Check logs for version comparison logic

---

## Expected Test Timeline

- Database migration: 5 min
- Backend API tests: 15 min
- Frontend UI tests: 10 min
- Log verification: 5 min

**Total:** ~35 minutes

---

## Success Criteria

✅ All CRITICAL tests pass
✅ Backend logs show correct messages
✅ UI toggle works correctly
✅ Only one force update per type enforced
✅ Downgrade scenario works
