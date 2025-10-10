# Kid Profile API Testing Guide

## Quick Start

### 1. Start the Manager API

```bash
cd D:\cheekofinal\xiaozhi-esp32-server\main\manager-api
mvn spring-boot:run "-Dspring-boot.run.arguments=--spring.profiles.active=dev"
```

Wait for the server to start on port 8002.

---

## 2. Run API Tests (No SQL Required!)

We have multiple test scripts available:

### Option A: Quick Test (Recommended)

```bash
python test_kid_profile_api.py
```

This compact script will:
1. Ask for your username and password
2. Create a kid profile via API
3. Assign kid to device via API
4. Verify the assignment works

**All using REST APIs - no SQL needed!**

### Option B: Detailed Test

```bash
python test_kid_profile_api_complete.py
```

This comprehensive script will:
1. Login with username/password
2. Check for existing kid profiles
3. Optionally create new kid profile
4. Assign kid to device
5. Verify via LiveKit endpoint
6. Show detailed step-by-step progress

### Option C: Verify Existing Setup

```bash
python verify_kid_device_link.py
```

Use this to quickly verify if a kid is already linked to a device.

---

## 3. Expected Output

When you run the quick test (`test_kid_profile_api.py`), you should see:

```
============================================================
Kid Profile API Test (API Only)
============================================================

Username (email): your@email.com
Password: ********

🔐 Logging in...
✅ Login successful
👶 Creating kid profile...
✅ Kid created (ID: 1)
🔗 Assigning kid to device...
✅ Kid assigned to device
🎯 Verifying profile retrieval...
✅ Profile retrieved:
   Name: Rahul, Age: 10, Group: Late Elementary

============================================================
🎉 ALL TESTS PASSED!
============================================================
```

---

## 4. API Endpoints Used

All endpoints use `http://localhost:8002/toy` as the base URL.

### 1. User Login (No Captcha Required)

```
POST /user/login
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "yourpassword",
  "captcha": "MOBILE_APP_BYPASS",
  "captchaId": "any-uuid-here"
}
```

Response:
```json
{
  "code": 0,
  "data": {
    "token": "your-user-token-here"
  }
}
```

### 2. Create Kid Profile

```
POST /api/mobile/kids/create
Authorization: Bearer YOUR_USER_TOKEN
Content-Type: application/json

{
  "name": "Rahul",
  "dateOfBirth": "2014-10-09",
  "gender": "male",
  "interests": "[\"games\", \"sports\", \"science\"]",
  "avatarUrl": "https://example.com/avatar.jpg"
}
```

Response:
```json
{
  "code": 0,
  "data": {
    "kid": {
      "id": 1,
      "name": "Rahul",
      "age": 10,
      "ageGroup": "Late Elementary"
    }
  }
}
```

### 3. Assign Kid to Device

```
PUT /device/assign-kid-by-mac
Authorization: Bearer YOUR_USER_TOKEN
Content-Type: application/json

{
  "macAddress": "68:25:dd:bb:f3:a0",
  "kidId": 1
}
```

Response:
```json
{
  "code": 0,
  "msg": "success"
}
```

### 4. Get Child Profile by MAC (LiveKit Endpoint)

**Get Child Profile by MAC:**
```
POST /toy/config/child-profile-by-mac
Authorization: Bearer da11d988-f105-4e71-b095-da62ada82189

{
  "macAddress": "68:25:dd:bb:f3:a0"
}
```

Response:
```json
{
  "code": 0,
  "data": {
    "name": "Rahul",
    "age": 10,
    "ageGroup": "Late Elementary",
    "gender": "male",
    "interests": "[\"games\", \"sports\", \"science\"]"
  }
}
```

### For Mobile App (Login Required)

**Login to Get Token:**
```
POST /toy/user/login

{
  "username": "user@example.com",
  "password": "yourpassword",
  "captcha": "MOBILE_APP_BYPASS",
  "captchaId": "any-uuid-here"
}
```

Response:
```json
{
  "code": 0,
  "data": {
    "token": "your-token-here"
  }
}
```

**Assign Kid to Device:**
```
PUT /toy/device/assign-kid-by-mac
Authorization: Bearer YOUR_USER_TOKEN

{
  "macAddress": "68:25:dd:bb:f3:a0",
  "kidId": 1
}
```

Response:
```json
{
  "code": 0,
  "msg": "success"
}
```

---

## 5. Troubleshooting

### Error: "No child assigned to this device"

**Cause:** Device exists but kid is not linked

**Solution:** Run the assign API again:
```bash
python test_kid_profile_api.py
```

Or use the detailed test to assign existing kid to device.

### Error: "Device not found for MAC: ..."

**Cause:** Device doesn't exist in database

**Solution:** The device needs to be registered first. This normally happens when the physical device connects to the system. For testing, you may need to create a device record (contact admin).

### Error: "token is invalid, please log in again"

**Cause:** User token expired (tokens expire after 12 hours)

**Solution:** Run the test again - it will get a fresh token automatically when you login.

### Error: "验证码错误" (Captcha error)

**Cause:** Backend doesn't accept `MOBILE_APP_BYPASS`

**Solution:** The backend should be configured to accept this bypass token for mobile apps. Check the captcha validation settings in the backend.

### Error: "You don't own this device"

**Cause:** The device is registered to a different user

**Solution:** Make sure you're logging in with the correct user account that owns the device.

---

## 6. Login Without Captcha

The test script uses the same login method as the Flutter mobile app:

```python
import uuid

def login_user(username, password):
    response = requests.post(
        "http://localhost:8002/toy/user/login",
        headers={'Content-Type': 'application/json'},
        json={
            'username': username,
            'mobile': username,
            'password': password,
            'captcha': 'MOBILE_APP_BYPASS',  # Same as Flutter app
            'captchaId': str(uuid.uuid4())
        }
    )
    return response.json()['data']['token']
```

This is the exact same approach used by the Flutter app in `java_auth_service.dart`.

---

## 7. Next Steps

Once all tests pass:

1. **Flutter App Integration:**
   - Create `JavaKidProfileService` to replace Supabase
   - Use the kid profile APIs to manage kids from mobile app

2. **LiveKit Server Integration:**
   - LiveKit server calls `/config/child-profile-by-mac` with device MAC
   - Agent prompts are personalized with kid's name, age, interests

3. **Agent Prompt Customization:**
   - Update agent prompts to use Jinja2 template variables
   - Example: `Hello {{child_name}}! I see you're {{child_age}} years old and love {{child_interests}}`

---

## Files Reference

- `test_kid_profile_api_simple.py` - Main test script with login
- `verify_kid_device_link.py` - Quick verification script
- `check_manager_api.py` - Health check script
- `KID_PROFILE_API_REFERENCE.md` - Complete API documentation
- `kid_profile_implementation_plan.md` - Implementation plan
