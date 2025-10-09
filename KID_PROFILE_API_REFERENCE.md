# Kid Profile API Reference

## Overview
APIs for managing kid profiles and linking them to devices.

---

## Kid Profile Management

### 1. Create Kid Profile
**Endpoint:** `POST /api/mobile/kids/create`
**Auth:** User token required
**Request Body:**
```json
{
  "name": "Rahul",
  "dateOfBirth": "2014-10-09",
  "gender": "male",
  "interests": "[\"games\", \"sports\", \"science\"]",
  "avatarUrl": "https://example.com/avatar.jpg"
}
```
**Response:**
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

---

### 2. Get All Kids
**Endpoint:** `GET /api/mobile/kids/list`
**Auth:** User token required
**Response:**
```json
{
  "code": 0,
  "data": {
    "kids": [
      {
        "id": 1,
        "name": "Rahul",
        "age": 10,
        "gender": "male"
      }
    ]
  }
}
```

---

### 3. Get Kid by ID
**Endpoint:** `GET /api/mobile/kids/{id}`
**Auth:** User token required

---

### 4. Update Kid Profile
**Endpoint:** `PUT /api/mobile/kids/{id}`
**Auth:** User token required
**Request Body:**
```json
{
  "interests": "[\"games\", \"sports\", \"science\", \"coding\"]"
}
```

---

### 5. Delete Kid Profile
**Endpoint:** `DELETE /api/mobile/kids/{id}`
**Auth:** User token required

---

## Device-Kid Linking

### 6. Assign Kid to Device (by Device ID)
**Endpoint:** `PUT /device/assign-kid/{deviceId}`
**Auth:** User token required
**Request Body:**
```json
{
  "kidId": 1
}
```

---

### 7. Assign Kid to Device (by MAC Address)
**Endpoint:** `PUT /device/assign-kid-by-mac`
**Auth:** User token required
**Request Body:**
```json
{
  "macAddress": "68:25:dd:bb:f3:a0",
  "kidId": 1
}
```
**Response:**
```json
{
  "code": 0,
  "msg": "success"
}
```

---

## LiveKit Integration

### 8. Get Child Profile by MAC (for LiveKit)
**Endpoint:** `POST /config/child-profile-by-mac`
**Auth:** Server secret (Bearer token)
**Request Body:**
```json
{
  "macAddress": "68:25:dd:bb:f3:a0"
}
```
**Response:**
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

---

## SQL Direct Setup (for Testing)

If you don't have user authentication set up, use SQL directly:

```sql
-- 1. Create kid profile
INSERT INTO kid_profile (
    user_id, name, date_of_birth, gender, interests, avatar_url,
    creator, create_date, updater, update_date
) VALUES (
    1, 'Rahul', '2014-10-09', 'male',
    '["games", "sports", "science"]', 'https://example.com/avatar.jpg',
    1, NOW(), 1, NOW()
);

-- Get the kid_id
SELECT id FROM kid_profile ORDER BY id DESC LIMIT 1;

-- 2. Assign kid to device
UPDATE ai_device
SET kid_id = 1  -- use the id from above
WHERE mac_address = '68:25:dd:bb:f3:a0';

-- 3. Verify
SELECT d.mac_address, d.kid_id, k.name, k.date_of_birth
FROM ai_device d
LEFT JOIN kid_profile k ON d.kid_id = k.id
WHERE d.mac_address = '68:25:dd:bb:f3:a0';
```

---

## Testing

Run the test script:
```bash
python test_kid_profile_api_simple.py
```

This will:
1. Guide you through SQL setup
2. Test the `/config/child-profile-by-mac` endpoint
3. Optionally test the `/device/assign-kid-by-mac` endpoint (requires user token)
4. Verify LiveKit integration works

---

## Configuration

**Server Secret:** `da11d988-f105-4e71-b095-da62ada82189`
**Base URL:** `http://localhost:8002/toy`

---

## Database Schema

```sql
CREATE TABLE kid_profile (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT NOT NULL,  -- FK to sys_user
  name VARCHAR(100) NOT NULL,
  date_of_birth DATE NOT NULL,
  gender VARCHAR(20),
  interests TEXT,  -- JSON array
  avatar_url VARCHAR(500),
  creator BIGINT,
  create_date DATETIME,
  updater BIGINT,
  update_date DATETIME,
  FOREIGN KEY (user_id) REFERENCES sys_user(id)
);

ALTER TABLE ai_device ADD COLUMN kid_id BIGINT;
ALTER TABLE ai_device ADD FOREIGN KEY (kid_id) REFERENCES kid_profile(id) ON DELETE SET NULL;
```

---

## Flow

```
1. User creates kid profile → kid_profile.id = 1
2. User assigns kid to device → ai_device.kid_id = 1
3. Device connects to LiveKit with MAC
4. LiveKit calls /config/child-profile-by-mac
5. Returns kid profile (name, age, interests)
6. Agent prompt personalized!
```
