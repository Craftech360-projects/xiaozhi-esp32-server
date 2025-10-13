# Force Update Feature - Test Results

**Test Date:** 2025-10-11
**Feature:** Firmware Force Update with Downgrade Support
**Status:** Implementation Complete - Ready for Testing

---

## Test Environment Setup

### Prerequisites
1. Database: MySQL running on 192.168.1.6:3307
2. Backend: Spring Boot application on port 8002
3. Redis: Running on 192.168.1.6:6380
4. Frontend: Vue.js application

---

## Test Scenarios & Expected Results

### Scenario 1: Database Migration
**Test:** Verify force_update column exists in ai_ota table

**Steps:**
```sql
SHOW COLUMNS FROM ai_ota LIKE 'force_update';
SELECT id, firmware_name, version, type, force_update FROM ai_ota LIMIT 5;
```

**Expected Result:**
- Column `force_update` exists with type TINYINT(1)
- Default value is 0
- Index `idx_force_update_type` exists on (type, force_update)

**Actual Result:** ⏳ Pending Manual Verification

**Status:** ⚠️ PENDING

---

### Scenario 2: API Endpoint - List Firmwares
**Test:** GET /api/otaMag?pageNum=1&pageSize=10

**Expected Response:**
```json
{
  "code": 0,
  "data": {
    "list": [
      {
        "id": "uuid",
        "firmwareName": "ESP32 Firmware",
        "type": "ESP32",
        "version": "2.1.0",
        "forceUpdate": 0,
        "size": 1048576,
        "remark": "Stable release",
        "firmwarePath": "uploadfile/abc123.bin",
        "createDate": "2025-10-11T10:00:00"
      }
    ],
    "total": 1
  }
}
```

**Validation Points:**
- ✓ Response includes `forceUpdate` field
- ✓ Field is Integer type (0 or 1)
- ✓ Default value is 0 for existing firmwares

**Status:** ⚠️ REQUIRES AUTHENTICATION - MANUAL TEST

---

### Scenario 3: API Endpoint - Enable Force Update
**Test:** PUT /api/otaMag/forceUpdate/{id}

**Request:**
```json
{
  "forceUpdate": 1,
  "type": "ESP32"
}
```

**Expected Behavior:**
1. Target firmware gets force_update = 1
2. All other ESP32 firmwares get force_update = 0 (auto-disabled)
3. Database transaction commits atomically
4. Success response returned

**Expected Response:**
```json
{
  "code": 0,
  "msg": "success"
}
```

**Status:** ⚠️ REQUIRES AUTHENTICATION - MANUAL TEST

---

### Scenario 4: API Endpoint - Disable Force Update
**Test:** PUT /api/otaMag/forceUpdate/{id}

**Request:**
```json
{
  "forceUpdate": 0,
  "type": "ESP32"
}
```

**Expected Behavior:**
1. Target firmware gets force_update = 0
2. System returns to normal OTA mode (latest version logic)

**Status:** ⚠️ REQUIRES AUTHENTICATION - MANUAL TEST

---

### Scenario 5: Device OTA Check - Normal Mode (No Force Update)

#### 5a: Device with OLDER version
**Device State:**
- Current Version: 1.5.0
- Latest Available: 2.0.0
- Force Update: OFF

**Request:**
```bash
curl -X POST http://localhost:8002/ota/ \
  -H "Device-Id: AA:BB:CC:DD:EE:FF" \
  -H "Content-Type: application/json" \
  -d '{
    "application": {"version": "1.5.0"},
    "board": {"type": "ESP32"}
  }'
```

**Expected Response:**
```json
{
  "server_time": {...},
  "firmware": {
    "version": "2.0.0",
    "url": "http://localhost:8002/otaMag/download/uuid-here"
  },
  "websocket": {...},
  "mqtt": {...}
}
```

**Expected Logs:**
```
📦 Normal OTA Response - Type: ESP32, Current: 1.5.0, Latest: 2.0.0, URL: http://...
```

**Validation:**
- ✓ Returns latest version 2.0.0
- ✓ Provides download URL (upgrade)
- ✓ No force update logs

**Status:** ⚠️ SERVER NOT RUNNING - MANUAL TEST REQUIRED

---

#### 5b: Device with SAME version as latest
**Device State:**
- Current Version: 2.0.0
- Latest Available: 2.0.0
- Force Update: OFF

**Expected Response:**
```json
{
  "firmware": {
    "version": "2.0.0",
    "url": "null"
  }
}
```

**Validation:**
- ✓ Returns same version
- ✓ No download URL (device up to date)

**Status:** ⚠️ MANUAL TEST REQUIRED

---

#### 5c: Device with NEWER version
**Device State:**
- Current Version: 2.5.0
- Latest Available: 2.0.0
- Force Update: OFF

**Expected Response:**
```json
{
  "firmware": {
    "version": "2.5.0",
    "url": "null"
  }
}
```

**Validation:**
- ✓ Returns current version (no downgrade in normal mode)
- ✓ No download URL

**Status:** ⚠️ MANUAL TEST REQUIRED

---

### Scenario 6: Device OTA Check - Force Update Mode (CRITICAL TEST)

#### 6a: Device with OLDER version (Upgrade)
**Device State:**
- Current Version: 1.8.0
- Forced Version: 2.1.0
- Force Update: ON

**Request:**
```bash
curl -X POST http://localhost:8002/ota/ \
  -H "Device-Id: AA:BB:CC:DD:EE:FF" \
  -H "Content-Type: application/json" \
  -d '{
    "application": {"version": "1.8.0"},
    "board": {"type": "ESP32"}
  }'
```

**Expected Response:**
```json
{
  "firmware": {
    "version": "2.1.0",
    "url": "http://localhost:8002/otaMag/download/uuid-here"
  }
}
```

**Expected Logs:**
```
🔒 Force update ACTIVE for type: ESP32, forced version: 2.1.0, device current: 1.8.0
📥 Force update download URL generated - Device will UPGRADE to version 2.1.0
📦 FORCE OTA Response - Type: ESP32, Current: 1.8.0, Target: 2.1.0, URL: http://...
```

**Validation:**
- ✓ Returns forced version 2.1.0 (NOT latest)
- ✓ Provides download URL
- ✓ Force update logs present
- ✓ Upgrade scenario works

**Status:** ⚠️ MANUAL TEST REQUIRED

---

#### 6b: Device with SAME version as forced
**Device State:**
- Current Version: 2.1.0
- Forced Version: 2.1.0
- Force Update: ON

**Expected Response:**
```json
{
  "firmware": {
    "version": "2.1.0",
    "url": "null"
  }
}
```

**Expected Logs:**
```
🔒 Force update ACTIVE for type: ESP32, forced version: 2.1.0, device current: 2.1.0
✅ Device already on forced version 2.1.0, no download needed
📦 FORCE OTA Response - Type: ESP32, Current: 2.1.0, Target: 2.1.0, URL: null
```

**Validation:**
- ✓ Returns forced version
- ✓ No download URL (device compliant)
- ✓ Force update active but no update needed

**Status:** ⚠️ MANUAL TEST REQUIRED

---

#### 6c: Device with NEWER version (DOWNGRADE) - CRITICAL!
**Device State:**
- Current Version: 2.5.0
- Forced Version: 2.1.0
- Force Update: ON

**Expected Response:**
```json
{
  "firmware": {
    "version": "2.1.0",
    "url": "http://localhost:8002/otaMag/download/uuid-here"
  }
}
```

**Expected Logs:**
```
🔒 Force update ACTIVE for type: ESP32, forced version: 2.1.0, device current: 2.5.0
📥 Force update download URL generated - Device will DOWNGRADE to version 2.1.0
📦 FORCE OTA Response - Type: ESP32, Current: 2.5.0, Target: 2.1.0, URL: http://...
```

**Validation:**
- ✓ Returns forced version 2.1.0 (LOWER than device version)
- ✓ Provides download URL
- ✓ DOWNGRADE scenario works (KEY FEATURE!)
- ✓ Ignores that device has newer version

**Status:** ⚠️ MANUAL TEST REQUIRED - THIS IS THE CRITICAL TEST!

---

### Scenario 7: Edge Cases

#### 7a: Missing Device-Id header
**Request:**
```bash
curl -X POST http://localhost:8002/ota/ \
  -H "Content-Type: application/json" \
  -d '{"application": {"version": "1.0.0"}}'
```

**Expected:** HTTP 400 or error response
**Status:** ⚠️ MANUAL TEST

---

#### 7b: Invalid forceUpdate value
**Request:**
```json
{
  "forceUpdate": 2,
  "type": "ESP32"
}
```

**Expected Response:**
```json
{
  "code": 500,
  "msg": "force_update值必须为0或1"
}
```

**Status:** ⚠️ MANUAL TEST

---

#### 7c: Type mismatch
**Request:**
```json
{
  "forceUpdate": 1,
  "type": "ESP8266"
}
```

**But firmware ID is for ESP32**

**Expected Response:**
```json
{
  "code": 500,
  "msg": "固件类型不匹配"
}
```

**Status:** ⚠️ MANUAL TEST

---

#### 7d: Enable force on two firmwares (same type)
**Steps:**
1. Enable force update on Firmware A (ESP32, v2.0.0)
2. Enable force update on Firmware B (ESP32, v2.1.0)

**Expected Behavior:**
- Firmware A: force_update = 0 (auto-disabled)
- Firmware B: force_update = 1 (active)
- Only ONE force update per type allowed

**Status:** ⚠️ MANUAL TEST

---

### Scenario 8: Frontend UI Tests

#### 8a: Force Update Toggle Display
**Test:** Open OTA Management page

**Expected:**
- New column "Force Update" visible
- Toggle switch for each firmware row
- "✓ Active" label when force_update = 1
- Green color for active toggle

**Status:** ⚠️ MANUAL UI TEST

---

#### 8b: Enable Force Update via UI
**Test:** Click toggle to enable force update

**Expected:**
- Confirmation dialog appears
- Message: "Are you sure you want to FORCE all devices of type X to version Y?"
- On confirm: Toggle turns green
- Success message appears
- Other firmwares of same type have disabled toggles

**Status:** ⚠️ MANUAL UI TEST

---

#### 8c: Disable Force Update via UI
**Test:** Click toggle to disable force update

**Expected:**
- Confirmation dialog appears
- On confirm: Toggle turns gray
- Success message appears
- Other toggles for same type become enabled

**Status:** ⚠️ MANUAL UI TEST

---

#### 8d: Tooltip Messages
**Test:** Hover over toggle switches

**Expected Tooltips:**
- Active force update: "Force update is ACTIVE. All devices will update to this version."
- Disabled (another active): "Another version already has force update enabled for this type."
- Disabled (none active): "Enable to force all devices to this version (including downgrades)"

**Status:** ⚠️ MANUAL UI TEST

---

## Code Quality Checks

### Backend Code Review
- ✅ OtaEntity.java: forceUpdate field added
- ✅ OtaService.java: Interface methods added
- ✅ OtaServiceImpl.java: Implementation with transaction
- ✅ OTAMagController.java: Endpoint added with validation
- ✅ DeviceServiceImpl.java: buildFirmwareInfo updated with force update logic
- ✅ Transactional annotation present for atomicity
- ✅ Error handling implemented
- ✅ Logging added for debugging

### Frontend Code Review
- ✅ ota.js: API method added
- ✅ OtaManagement.vue: UI column added
- ✅ Toggle switch implemented
- ✅ Confirmation dialogs present
- ✅ Error handling implemented
- ✅ Tooltips for user guidance

### Database Migration
- ✅ Migration file created: 202510111600.sql
- ✅ Column with default value
- ✅ Index created for performance
- ✅ Backward compatible

---

## Test Execution Instructions

### Step 1: Database Migration
```bash
cd main/manager-api
# Start MySQL if not running
# Run migration (Liquibase will auto-apply)
mvn spring-boot:run
```

Or manually:
```sql
mysql -h 192.168.1.6 -P 3307 -u manager -p manager_api < src/main/resources/db/changelog/202510111600.sql
```

### Step 2: Start Backend
```bash
cd main/manager-api
mvn clean install
mvn spring-boot:run -Dspring-boot.run.profiles=local
```

### Step 3: Start Frontend
```bash
cd main/manager-web
npm install
npm run serve
```

### Step 4: Create Test Data
1. Login to admin panel
2. Go to OTA Management
3. Upload at least 3 firmware files:
   - ESP32 v1.8.0
   - ESP32 v2.1.0
   - ESP32 v2.5.0

### Step 5: Run Manual Tests
Follow scenarios 1-8 above

### Step 6: Verify Logs
Check backend console for log messages:
- 🔒 Force update ACTIVE
- 📥 Force update download URL generated
- ✅ Device already on forced version
- 📦 FORCE OTA Response / Normal OTA Response

---

## Summary

### Implementation Status: ✅ COMPLETE

**Files Modified:** 8
**Database Changes:** 1 migration
**API Endpoints Added:** 1
**Frontend Components Updated:** 2

### Test Status: ⚠️ PENDING MANUAL VERIFICATION

**Automated Tests:** Not applicable (requires running server + auth)
**Manual Tests Required:** 18 scenarios
**Critical Tests:** 6 (force update scenarios)

### Next Steps

1. ☐ Apply database migration
2. ☐ Start backend server
3. ☐ Upload test firmwares
4. ☐ Test force update toggle in UI
5. ☐ Test device OTA check with force update OFF
6. ☐ Enable force update on specific firmware
7. ☐ **Test downgrade scenario (CRITICAL)**
8. ☐ Verify logs
9. ☐ Test edge cases
10. ☐ Production readiness review

---

## Risk Assessment

### Low Risk
- ✅ Default value preserves existing behavior
- ✅ Backward compatible
- ✅ Feature is opt-in
- ✅ Admin-only access

### Medium Risk
- ⚠️ Downgrade capability (new functionality)
- ⚠️ Transaction handling for toggle

### Mitigation
- ✓ Confirmation dialogs
- ✓ Comprehensive logging
- ✓ Database transaction for atomicity
- ✓ Only one force update per type

---

## Contact

For questions or issues:
- Check backend logs for error messages
- Verify database migration applied correctly
- Test with curl before UI testing
- Review DeviceServiceImpl.buildFirmwareInfo() logic

**Status Legend:**
- ✅ Complete/Passed
- ⚠️ Pending Manual Test
- ❌ Failed
- ⏳ In Progress
