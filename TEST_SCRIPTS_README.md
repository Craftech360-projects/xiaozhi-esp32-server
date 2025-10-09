# Kid Profile API Test Scripts

## Overview

All test scripts use **API calls only** - no SQL required!

---

## Available Test Scripts

### 1. `test_kid_profile_api.py` ⭐ **RECOMMENDED**

**Quick and simple test - use this one!**

```bash
python test_kid_profile_api.py
```

**What it does:**
- Login with username/password
- Create a kid profile
- Assign kid to device
- Verify the assignment

**Output:** Clean, simple, color-coded status messages

**Use when:** You want to quickly test the complete flow

---

### 2. `test_kid_profile_api_complete.py`

**Detailed test with interactive options**

```bash
python test_kid_profile_api_complete.py
```

**What it does:**
- Login with username/password
- Check for existing kid profiles
- Ask if you want to use existing or create new
- Assign kid to device
- Verify via LiveKit endpoint
- Show detailed progress at each step

**Use when:** You want to see all the details or test with existing kids

---

### 3. `verify_kid_device_link.py`

**Quick verification only**

```bash
python verify_kid_device_link.py
```

**What it does:**
- Only tests the `/config/child-profile-by-mac` endpoint
- Shows if kid is linked to device
- No login required (uses server secret)

**Use when:** You just want to verify if a kid is already linked

---

### 4. `check_manager_api.py`

**Health check for Manager API**

```bash
python check_manager_api.py
```

**What it does:**
- Tests if Manager API is running
- Tests multiple endpoints
- Shows detailed responses

**Use when:** You want to verify the Manager API is working

---

## Comparison Table

| Script | Login Required | Creates Kid | Assigns Device | Interactive | Output Detail |
|--------|---------------|-------------|----------------|-------------|---------------|
| `test_kid_profile_api.py` | ✅ | ✅ | ✅ | Minimal | Simple |
| `test_kid_profile_api_complete.py` | ✅ | ✅ | ✅ | Full | Detailed |
| `verify_kid_device_link.py` | ❌ | ❌ | ❌ | None | Minimal |
| `check_manager_api.py` | ❌ | ❌ | ❌ | None | Detailed |

---

## Quick Start

1. **Start Manager API:**
   ```bash
   cd D:\cheekofinal\xiaozhi-esp32-server\main\manager-api
   mvn spring-boot:run "-Dspring-boot.run.arguments=--spring.profiles.active=dev"
   ```

2. **Run the test:**
   ```bash
   python test_kid_profile_api.py
   ```

3. **Enter your credentials when prompted**

4. **Done!** ✅

---

## What You Need

### For All Tests:
- Manager API running on `http://localhost:8002`
- Python 3.x with `requests` library

### For Login-Based Tests:
- Valid user account (username/password)
- User must own the device you're testing with

### Configuration:
Edit these variables in the test scripts if needed:
```python
BASE_URL = "http://localhost:8002/toy"
MAC_ADDRESS = "68:25:dd:bb:f3:a0"  # Change to your device MAC
```

---

## Expected Flow

```
User Login
    ↓
Create Kid Profile (via API)
    ↓
Assign Kid to Device (via API)
    ↓
Verify Assignment (LiveKit endpoint)
    ↓
✅ SUCCESS!
```

---

## Common Issues

### ❌ Connection Error

**Problem:** Manager API not running

**Solution:**
```bash
cd D:\cheekofinal\xiaozhi-esp32-server\main\manager-api
mvn spring-boot:run "-Dspring-boot.run.arguments=--spring.profiles.active=dev"
```

### ❌ Login Failed

**Problem:** Wrong username/password

**Solution:** Check your credentials and try again

### ❌ Device Not Found

**Problem:** Device MAC address doesn't exist in database

**Solution:** Make sure the device has been registered first

### ❌ You Don't Own This Device

**Problem:** Device belongs to different user

**Solution:** Login with the correct user account

---

## API Endpoints Used

All scripts use these REST API endpoints:

1. **POST** `/user/login` - Login with captcha bypass
2. **POST** `/api/mobile/kids/create` - Create kid profile
3. **PUT** `/device/assign-kid-by-mac` - Assign kid to device
4. **POST** `/config/child-profile-by-mac` - Get child profile (LiveKit)

See `TESTING_GUIDE.md` for detailed API documentation.

---

## No SQL Required! 🎉

All these scripts use **REST APIs only**. No need to:
- ❌ Run SQL INSERT statements
- ❌ Manually update database tables
- ❌ Connect to MySQL directly

Everything is done through proper API calls, just like the Flutter mobile app!
