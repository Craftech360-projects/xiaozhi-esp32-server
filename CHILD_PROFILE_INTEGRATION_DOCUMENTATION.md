# Child Profile Integration - Complete Documentation

## 📋 Overview

This document explains the complete implementation of the Child Profile feature, which enables personalized AI agent interactions based on a child's age, interests, and profile information.

---

## 🎯 Feature Purpose

Allow parents to:
1. Create profiles for their children (name, date of birth, gender, interests)
2. Assign specific devices (toys) to specific children
3. Have the AI agent automatically personalize responses based on the child's profile

---

## 🗄️ Database Schema

### Table: `kid_profile`

Stores child profile information.

```sql
CREATE TABLE kid_profile (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT NOT NULL,                -- Parent/guardian user ID
  name VARCHAR(100) NOT NULL,             -- Child's name
  date_of_birth DATE NOT NULL,            -- Birth date (for age calculation)
  gender VARCHAR(20),                     -- Gender: male/female/other
  interests TEXT,                         -- JSON array: ["games", "sports", "science"]
  avatar_url VARCHAR(500),                -- Profile picture URL
  creator BIGINT,                         -- Who created this record
  create_date DATETIME,                   -- Creation timestamp
  updater BIGINT,                         -- Last updater
  update_date DATETIME,                   -- Last update timestamp

  FOREIGN KEY (user_id) REFERENCES sys_user(id)
);
```

### Table: `ai_device` (Modified)

Added `kid_id` column to link devices to children.

```sql
ALTER TABLE ai_device
ADD COLUMN kid_id BIGINT,
ADD FOREIGN KEY (kid_id) REFERENCES kid_profile(id);
```

---

## 🔄 Data Flow Architecture

```
┌─────────────────┐
│  ESP32 Device   │
│ MAC: aa:bb:cc   │
└────────┬────────┘
         │ Connects to LiveKit
         ▼
┌─────────────────────────────────────────────────────────────┐
│                    LiveKit Server                            │
│  1. Extracts MAC from room name                             │
│  2. Calls Manager API: /config/agent-prompt                 │
│  3. Calls Manager API: /config/child-profile-by-mac         │
│  4. Renders Jinja2 template with child data                 │
│  5. Saves child profile to mem0                             │
└────────┬────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Manager API                               │
│                                                              │
│  /config/agent-prompt:                                      │
│    1. Find device by MAC                                    │
│    2. Get agent.system_prompt from database                 │
│    3. Check if device.kid_id exists                         │
│    4. If yes: Inject child profile Jinja2 template          │
│    5. Return prompt (with or without child template)        │
│                                                              │
│  /config/child-profile-by-mac:                              │
│    1. Find device by MAC                                    │
│    2. Get device.kid_id                                     │
│    3. Fetch kid profile from database                       │
│    4. Return child data (name, age, interests, etc.)        │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Database                                  │
│  - kid_profile table (child information)                    │
│  - ai_device table (device.kid_id links to profile)         │
│  - ai_agent table (agent.system_prompt - original prompt)   │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 Backend Implementation (Manager API)

### 1. Child Profile CRUD APIs

**Location:** `xiaozhi/modules/sys/controller/MobileKidProfileController.java`

#### Create Child Profile
```http
POST /api/mobile/kids/create
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Rahul",
  "dateOfBirth": "2015-10-12",
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
    "id": 1976198867056529410,
    "name": "Rahul",
    "age": 9,
    "ageGroup": "Late Elementary"
  }
}
```

#### List Child Profiles
```http
GET /api/mobile/kids/list
Authorization: Bearer <token>
```

#### Update Child Profile
```http
PUT /api/mobile/kids/{id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Rahul Kumar",
  "interests": "[\"games\", \"robotics\"]"
}
```

#### Delete Child Profile
```http
DELETE /api/mobile/kids/{id}
Authorization: Bearer <token>
```

---

### 2. Device Assignment APIs

**Location:** `xiaozhi/modules/device/controller/DeviceController.java`

#### Assign Kid to Device by Device ID
```http
POST /api/mobile/devices/{deviceId}/assign-kid
Authorization: Bearer <token>
Content-Type: application/json

{
  "kidId": 1976198867056529410
}
```

#### Assign Kid to Device by MAC Address
```http
POST /api/mobile/devices/assign-kid-by-mac
Authorization: Bearer <token>
Content-Type: application/json

{
  "macAddress": "68:25:dd:bb:f3:a0",
  "kidId": 1976198867056529410
}
```

---

### 3. LiveKit Integration APIs

#### Get Agent Prompt (with Child Profile Template)

**Location:** `xiaozhi/modules/config/controller/ConfigController.java`

```http
POST /config/agent-prompt
Authorization: Bearer <secret>
Content-Type: application/json

{
  "macAddress": "68:25:dd:bb:f3:a0"
}
```

**Response:**
```json
{
  "code": 0,
  "data": "<identity>\n\n{% if child_name %}...(child profile template)...{% endif %}\n\nYou are Cheeko..."
}
```

**Implementation Logic** (`ConfigServiceImpl.java:460-510`):

```java
public String getAgentPrompt(String macAddress) {
    // 1. Find device by MAC
    DeviceEntity device = deviceService.getDeviceByMacAddress(macAddress);

    // 2. Get agent and original prompt from database
    AgentEntity agent = agentService.selectById(device.getAgentId());
    String systemPrompt = agent.getSystemPrompt();

    // 3. Check if device has a child assigned
    Long kidId = device.getKidId();

    if (kidId != null) {
        // 4. Fetch child profile
        KidProfileDTO kid = kidProfileService.get(kidId);

        if (kid != null) {
            // 5. Build Jinja2 template section
            String childProfileSection =
                "\n\n{% if child_name %}\n" +
                "🎯 **Child Profile:**\n" +
                "- **Name:** {{ child_name }}\n" +
                "{% if child_age %}- **Age:** {{ child_age }} years old{% endif %}\n" +
                "{% if age_group %}- **Age Group:** {{ age_group }}{% endif %}\n" +
                "{% if child_gender %}- **Gender:** {{ child_gender }}{% endif %}\n" +
                "{% if child_interests %}- **Interests:** {{ child_interests }}{% endif %}\n\n" +
                "**Important:** Always address this child by their name ({{ child_name }}) " +
                "and personalize your responses based on their age ({{ child_age }}) " +
                "and interests ({{ child_interests }}). For age group {{ age_group }}, " +
                "use age-appropriate vocabulary and concepts.\n" +
                "{% endif %}\n";

            // 6. Inject after <identity> tag (or at beginning)
            if (systemPrompt.contains("<identity>")) {
                systemPrompt = systemPrompt.replace(
                    "<identity>",
                    "<identity>" + childProfileSection
                );
            } else {
                systemPrompt = childProfileSection + systemPrompt;
            }
        }
    }

    // 7. Return modified prompt (or original if no child)
    return systemPrompt;
}
```

**Key Points:**
- ✅ Original prompt in database remains unchanged
- ✅ Child profile template is injected dynamically on-the-fly
- ✅ If device has no child assigned, original prompt is returned
- ✅ Template uses Jinja2 syntax for conditional rendering

---

#### Get Child Profile by MAC

**Location:** `xiaozhi/modules/config/controller/ConfigController.java`

```http
POST /config/child-profile-by-mac
Authorization: Bearer <secret>
Content-Type: application/json

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
    "age": 9,
    "ageGroup": "Late Elementary",
    "gender": "male",
    "interests": "[\"games\", \"sports\", \"science\"]"
  }
}
```

---

## 🎨 LiveKit Server Implementation

### 1. Database Helper

**Location:** `main/livekit-server/src/utils/database_helper.py:86-143`

```python
async def get_child_profile_by_mac(self, device_mac: str) -> Optional[dict]:
    """Get child profile assigned to device by MAC address"""
    url = f"{self.manager_api_url}/config/child-profile-by-mac"
    headers = {
        "Authorization": f"Bearer {self.secret}",
        "Content-Type": "application/json"
    }
    payload = {"macAddress": device_mac}

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                if data.get('code') == 0:
                    return data.get('data')
    return None
```

---

### 2. Main Entry Point

**Location:** `main/livekit-server/main.py`

#### Step 1: Fetch Agent Prompt (lines 216-234)
```python
# Fetch device-specific prompt BEFORE creating assistant
if device_mac:
    agent_prompt = await prompt_service.get_prompt(room_name, device_mac)
    # Returns prompt WITH child profile Jinja2 template
```

#### Step 2: Fetch Child Profile (lines 236-248)
```python
# Fetch child profile if device MAC is available
child_profile = None
if device_mac:
    try:
        child_profile = await db_helper.get_child_profile_by_mac(device_mac)
        if child_profile:
            logger.info(
                f"👶 Child profile loaded: {child_profile.get('name')}, "
                f"age {child_profile.get('age')} ({child_profile.get('ageGroup')})"
            )
    except Exception as e:
        logger.warning(f"Failed to fetch child profile: {e}")
        child_profile = None
```

#### Step 3: Prepare Template Variables (lines 256-264)
```python
# Prepare template variables
template_vars = {
    'emojiList': EMOJI_List,
    'child_name': child_profile.get('name', 'friend') if child_profile else 'friend',
    'child_age': child_profile.get('age', '') if child_profile else '',
    'age_group': child_profile.get('ageGroup', '') if child_profile else '',
    'child_gender': child_profile.get('gender', '') if child_profile else '',
    'child_interests': child_profile.get('interests', '') if child_profile else ''
}
```

#### Step 4: Render Jinja2 Template (lines 267-273)
```python
# Render agent prompt with Jinja2 template
if any(placeholder in agent_prompt for placeholder in ['{{', '{%']):
    template = Template(agent_prompt)
    agent_prompt = template.render(**template_vars)
    logger.info("🎨 Rendered agent prompt with template variables")
    if child_profile:
        logger.info(
            f"👶 Personalized for: {template_vars['child_name']}, "
            f"{template_vars['child_age']} years old"
        )
```

**Result:** All `{{ child_name }}` → `Rahul`, `{{ child_age }}` → `9`, etc.

#### Step 5: Save to mem0 (lines 294-305)
```python
if mem0_provider and child_profile:
    # Store child profile in mem0 for agent memory
    child_info = {
        "role": "system",
        "content": f"Child Profile - Name: {child_profile.get('name')}, "
                   f"Age: {child_profile.get('age')}, "
                   f"Age Group: {child_profile.get('ageGroup')}, "
                   f"Gender: {child_profile.get('gender')}, "
                   f"Interests: {child_profile.get('interests')}"
    }
    await mem0_provider.save_memory({"messages": [child_info]})
    logger.info(f"👶💭 Child profile saved to mem0: {child_profile.get('name')}")
```

---

## 📝 Jinja2 Template Variables

Available in agent prompts:

| Variable | Type | Example Value | Description |
|----------|------|---------------|-------------|
| `{{ child_name }}` | string | "Rahul" | Child's name |
| `{{ child_age }}` | integer | 9 | Current age (calculated from DOB) |
| `{{ age_group }}` | string | "Late Elementary" | Age group classification |
| `{{ child_gender }}` | string | "male" | Gender |
| `{{ child_interests }}` | string | "[\"games\", \"sports\"]" | JSON array of interests |

### Age Group Classification

Calculated automatically in `KidProfileDTO.getAgeGroup()`:

| Age | Age Group |
|-----|-----------|
| < 3 | Toddler |
| 3-5 | Preschool |
| 6-8 | Early Elementary |
| 9-11 | Late Elementary |
| 12-14 | Early Teen |
| 15+ | Teen |

---

## 🎯 Complete Example Flow

### Setup Phase

1. **Parent creates child profile:**
   ```http
   POST /api/mobile/kids/create
   {"name": "Rahul", "dateOfBirth": "2015-10-12", "gender": "male"}
   ```
   Response: `{"id": 1976198867056529410}`

2. **Parent assigns device to child:**
   ```http
   POST /api/mobile/devices/assign-kid-by-mac
   {"macAddress": "68:25:dd:bb:f3:a0", "kidId": 1976198867056529410}
   ```

### Runtime Phase

1. **Device connects to LiveKit:**
   - Room name: `session_123_6825ddbbf3a0`
   - MAC extracted: `68:25:dd:bb:f3:a0`

2. **LiveKit fetches prompt:**
   ```http
   POST /config/agent-prompt
   {"macAddress": "68:25:dd:bb:f3:a0"}
   ```

   **Manager API logic:**
   - Finds device → agent
   - Gets `agent.system_prompt` from DB
   - Checks `device.kid_id` → Found (Rahul)
   - Injects child profile template
   - Returns modified prompt

3. **LiveKit fetches child data:**
   ```http
   POST /config/child-profile-by-mac
   {"macAddress": "68:25:dd:bb:f3:a0"}
   ```
   Returns: `{name: "Rahul", age: 9, ...}`

4. **LiveKit renders template:**
   - Replaces `{{ child_name }}` with "Rahul"
   - Replaces `{{ child_age }}` with 9
   - Saves to mem0

5. **Agent starts with personalized prompt:**
   ```
   🎯 **Child Profile:**
   - **Name:** Rahul
   - **Age:** 9 years old
   - **Age Group:** Late Elementary
   - **Gender:** male
   - **Interests:** ["games", "sports", "science"]

   **Important:** Always address this child by their name (Rahul)...
   ```

6. **Agent behavior:**
   - Greets: "Hi Rahul!"
   - Uses age-appropriate vocabulary for 9-year-olds
   - References interests: "Want to hear about a cool science experiment?"
   - Remembers everything via mem0

---

## 🔍 Testing

### Test Scripts

1. **`test_kid_profile_api_complete.py`** - Full end-to-end test
   - Creates kid profile
   - Assigns to device
   - Verifies assignment
   - Tests LiveKit endpoint

2. **`test_prompt_with_kid_profile.py`** - Prompt verification
   - Checks config.yaml setting
   - Fetches prompt from Manager API
   - Verifies template injection

3. **`test_prompt_rendering.py`** - Complete flow demonstration
   - Shows raw prompt with templates
   - Shows child profile data
   - Shows final rendered prompt
   - Saves comparison to file

### Run Tests

```bash
# Full integration test
python test_kid_profile_api_complete.py

# Verify prompt injection
python test_prompt_with_kid_profile.py

# See before/after rendering
python test_prompt_rendering.py
```

---

## 🎨 Benefits of This Architecture

### 1. **Clean Database**
- Original agent prompts remain unchanged in database
- No need to update database prompts for each child

### 2. **Dynamic Injection**
- Child profile template added on-the-fly during API call
- If no child assigned, returns clean prompt

### 3. **Separation of Concerns**
- Manager API: Handles data and injection
- LiveKit: Handles rendering with actual values
- Database: Stores clean, reusable prompts

### 4. **Flexibility**
- Easy to modify template format
- Can add new variables without database changes
- Same agent prompt works for all devices

### 5. **Conditional Rendering**
- Uses `{% if child_name %}` wrapper
- Template section only appears when child exists
- Graceful fallback to "friend" if needed

---

## 📁 Key Files Modified/Created

### Manager API (Java/Spring Boot)

**Created:**
- `xiaozhi/modules/sys/entity/KidProfileEntity.java`
- `xiaozhi/modules/sys/dao/KidProfileDao.java`
- `xiaozhi/modules/sys/dao/KidProfileDao.xml`
- `xiaozhi/modules/sys/dto/KidProfileDTO.java`
- `xiaozhi/modules/sys/dto/KidProfileCreateDTO.java`
- `xiaozhi/modules/sys/dto/KidProfileUpdateDTO.java`
- `xiaozhi/modules/sys/service/KidProfileService.java`
- `xiaozhi/modules/sys/service/impl/KidProfileServiceImpl.java`
- `xiaozhi/modules/sys/controller/MobileKidProfileController.java`
- `xiaozhi/modules/config/dto/ChildProfileDTO.java`
- `xiaozhi/modules/device/dto/AssignKidToDeviceDTO.java`
- `xiaozhi/modules/device/dto/AssignKidByMacDTO.java`

**Modified:**
- `xiaozhi/modules/device/entity/DeviceEntity.java` - Added `kid_id` field
- `xiaozhi/modules/device/controller/DeviceController.java` - Added assignment endpoints
- `xiaozhi/modules/config/controller/ConfigController.java` - Added `/config/child-profile-by-mac`
- `xiaozhi/modules/config/service/impl/ConfigServiceImpl.java` - **Added dynamic prompt injection logic (lines 479-501)**

### Database

**Migrations:**
- `main/manager-api/src/main/resources/db/changelog/202510091430_create_kid_profile_table.sql`
- `main/manager-api/src/main/resources/db/changelog/202510091431_add_kid_id_to_device.sql`

### LiveKit Server (Python)

**Modified:**
- `main/livekit-server/src/utils/database_helper.py` - Added `get_child_profile_by_mac()` (lines 86-143)
- `main/livekit-server/main.py` - Added child profile fetching, rendering, and mem0 storage (lines 236-305)

**Created:**
- `test_kid_profile_api_complete.py` - Full integration test
- `test_prompt_with_kid_profile.py` - Prompt verification test
- `test_prompt_rendering.py` - Rendering demonstration

---

## 🚀 Future Enhancements

### Phase 4: Flutter App Integration

**Screens to Create:**
1. Kid Profile Management Screen
   - List all child profiles
   - Create/edit profiles
   - Delete profiles

2. Device Assignment Screen
   - List all devices
   - Dropdown to select kid for each device
   - Show which kid is assigned to which device

3. Profile View Screen
   - View child details
   - See which devices assigned
   - Edit interests and preferences

**Service Classes:**
- `JavaKidProfileService` - CRUD operations
- `JavaDeviceService.assignKidToDevice()` - Assignment

---

## 📊 Summary

This implementation provides a robust, scalable solution for personalizing AI agent interactions based on child profiles:

✅ Clean database design with proper foreign keys
✅ Dynamic prompt injection without database modifications
✅ Flexible Jinja2 templating system
✅ Proper separation of concerns (API, rendering, storage)
✅ Integration with mem0 for persistent memory
✅ Complete REST API for mobile app integration
✅ Comprehensive testing suite

The agent now has full awareness of the child's profile and can provide age-appropriate, personalized interactions while maintaining a clean, maintainable codebase.

---

**Created:** 2025-10-09
**Version:** 1.0
**Status:** ✅ Fully Implemented and Tested
