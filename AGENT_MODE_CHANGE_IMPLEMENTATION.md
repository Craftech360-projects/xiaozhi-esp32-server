# Agent Mode Change Feature - Implementation Documentation

## Overview

This document explains the implementation of the **Agent Mode Change** feature, which allows users to dynamically switch an AI agent's personality/mode (e.g., from "Cheeko" to "Storyteller") during an active conversation without requiring a reconnection.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Database Schema](#database-schema)
3. [Backend Implementation (Manager API)](#backend-implementation-manager-api)
4. [Frontend Implementation (LiveKit Server)](#frontend-implementation-livekit-server)
5. [Dynamic Session Update](#dynamic-session-update)
6. [Data Flow](#data-flow)
7. [API Endpoints](#api-endpoints)
8. [Testing](#testing)
9. [Troubleshooting](#troubleshooting)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         User Request                         │
│          "Switch to Storyteller mode"                        │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│               LiveKit AI Agent (main_agent.py)               │
│          Detects intent → Triggers function tool             │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│           update_agent_mode("Storyteller")                   │
│   1. Fetch agent_id from device MAC                          │
│   2. Call Manager API: PUT /agent/update-mode                │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│               Manager API (Spring Boot)                      │
│   1. Validate agent exists                                   │
│   2. Fetch template by name (ai_agent_template)              │
│   3. Copy template fields to agent (ai_agent)                │
│   4. Update database                                         │
│   5. Return new prompt in response                           │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│           LiveKit Agent Receives Response                    │
│   1. Extract new prompt from API response                    │
│   2. Update agent's internal instructions                    │
│   3. Update active session's instructions                    │
│   4. Return success message to user                          │
└─────────────────────────────────────────────────────────────┘
                 │
                 ▼
         [New prompt active immediately!]
```

---

## Database Schema

### **1. ai_agent_template Table**

Stores template configurations for different agent modes.

```sql
CREATE TABLE `ai_agent_template` (
    `id` VARCHAR(32) NOT NULL,
    `agent_code` VARCHAR(36),
    `agent_name` VARCHAR(64),           -- Template name (e.g., "Cheeko", "Storyteller")
    `asr_model_id` VARCHAR(32),
    `vad_model_id` VARCHAR(64),
    `llm_model_id` VARCHAR(32),
    `vllm_model_id` VARCHAR(32),
    `tts_model_id` VARCHAR(32),
    `tts_voice_id` VARCHAR(32),
    `mem_model_id` VARCHAR(32),
    `intent_model_id` VARCHAR(32),
    `system_prompt` TEXT,               -- Template system prompt
    `lang_code` VARCHAR(10),
    `language` VARCHAR(10),
    `chat_history_conf` INT,
    `sort` INT UNSIGNED DEFAULT 0,
    `is_visible` INT DEFAULT 1,
    `creator` BIGINT,
    `created_at` DATETIME,
    `updater` BIGINT,
    `updated_at` DATETIME,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

**Key Fields:**
- `agent_name`: Template identifier (used for searching)
- `system_prompt`: The personality/instructions for this mode
- `sort`: Priority (lower = default template)

---

### **2. ai_agent Table**

Stores individual agent instances (per user).

```sql
CREATE TABLE `ai_agent` (
    `id` VARCHAR(32) NOT NULL,
    `user_id` BIGINT,
    `agent_code` VARCHAR(36),
    `agent_name` VARCHAR(64),
    `asr_model_id` VARCHAR(32),
    `vad_model_id` VARCHAR(64),
    `llm_model_id` VARCHAR(32),
    `vllm_model_id` VARCHAR(32),
    `tts_model_id` VARCHAR(32),
    `tts_voice_id` VARCHAR(32),
    `mem_model_id` VARCHAR(32),
    `intent_model_id` VARCHAR(32),
    `system_prompt` TEXT,               -- Current active prompt (updated on mode change)
    `lang_code` VARCHAR(10),
    `language` VARCHAR(10),
    `chat_history_conf` INT,
    `sort` INT,
    `creator` BIGINT,
    `created_at` DATETIME,
    `updater` BIGINT,
    `updated_at` DATETIME,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

**Note:** When mode changes, template fields are copied to this table.

---

### **3. ai_device Table**

Links devices to agents via MAC address.

```sql
CREATE TABLE `ai_device` (
    `id` VARCHAR(255) NOT NULL,
    `mac_address` VARCHAR(17),          -- Format: 68:25:dd:ba:39:78
    `agent_id` VARCHAR(32),             -- Links to ai_agent.id
    `user_id` BIGINT,
    `board` VARCHAR(50),
    `alias` VARCHAR(100),
    `creator` BIGINT,
    `create_date` DATETIME,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

**Key:** MAC address → Agent ID mapping

---

## Backend Implementation (Manager API)

### **File Structure**

```
manager-api/
├── src/main/java/xiaozhi/modules/agent/
│   ├── controller/
│   │   └── AgentController.java        # API endpoints
│   ├── service/
│   │   ├── AgentService.java           # Interface
│   │   ├── AgentTemplateService.java   # Template interface
│   │   └── impl/
│   │       ├── AgentServiceImpl.java   # Mode update logic
│   │       └── AgentTemplateServiceImpl.java
│   ├── dto/
│   │   └── AgentUpdateModeDTO.java     # Request DTO
│   └── entity/
│       ├── AgentEntity.java
│       └── AgentTemplateEntity.java
└── modules/security/config/
    └── ShiroConfig.java                # Authentication config
```

---

### **1. DTO - AgentUpdateModeDTO.java**

**Location:** `src/main/java/xiaozhi/modules/agent/dto/AgentUpdateModeDTO.java`

```java
@Data
@Schema(description = "智能体模式更新对象")
public class AgentUpdateModeDTO implements Serializable {

    @Schema(description = "智能体ID", required = true)
    @NotBlank(message = "智能体ID不能为空")
    private String agentId;

    @Schema(description = "模板模式名称", required = true)
    @NotBlank(message = "模式名称不能为空")
    private String modeName;
}
```

---

### **2. Service Interface - AgentTemplateService.java**

**Location:** `src/main/java/xiaozhi/modules/agent/service/AgentTemplateService.java`

```java
public interface AgentTemplateService extends IService<AgentTemplateEntity> {

    /**
     * 根据模板名称获取模板
     */
    AgentTemplateEntity getTemplateByName(String modeName);
}
```

---

### **3. Service Implementation - AgentTemplateServiceImpl.java**

**Location:** `src/main/java/xiaozhi/modules/agent/service/impl/AgentTemplateServiceImpl.java`

```java
@Override
public AgentTemplateEntity getTemplateByName(String modeName) {
    LambdaQueryWrapper<AgentTemplateEntity> wrapper = new LambdaQueryWrapper<>();
    wrapper.eq(AgentTemplateEntity::getAgentName, modeName)
           .last("LIMIT 1");
    return this.getOne(wrapper);
}
```

**SQL Generated:**
```sql
SELECT * FROM ai_agent_template
WHERE agent_name = 'Storyteller'
LIMIT 1;
```

---

### **4. Core Logic - AgentServiceImpl.java**

**Location:** `src/main/java/xiaozhi/modules/agent/service/impl/AgentServiceImpl.java`

```java
@Override
@Transactional(rollbackFor = Exception.class)
public String updateAgentMode(String agentId, String modeName) {
    // 1. Validate agent exists
    AgentEntity agent = this.selectById(agentId);
    if (agent == null) {
        throw new RenException("智能体不存在");
    }

    // 2. Fetch template by name
    AgentTemplateEntity template = agentTemplateService.getTemplateByName(modeName);
    if (template == null) {
        throw new RenException("模板 '" + modeName + "' 不存在");
    }

    // 3. Copy template configuration to agent
    String oldPrompt = agent.getSystemPrompt();

    agent.setAsrModelId(template.getAsrModelId());
    agent.setVadModelId(template.getVadModelId());
    agent.setLlmModelId(template.getLlmModelId());
    agent.setVllmModelId(template.getVllmModelId());
    agent.setTtsModelId(template.getTtsModelId());
    agent.setTtsVoiceId(template.getTtsVoiceId());
    agent.setMemModelId(template.getMemModelId());
    agent.setIntentModelId(template.getIntentModelId());
    agent.setSystemPrompt(template.getSystemPrompt());  // ← NEW PROMPT
    agent.setChatHistoryConf(template.getChatHistoryConf());
    agent.setLangCode(template.getLangCode());
    agent.setLanguage(template.getLanguage());

    // 4. Update audit info
    try {
        UserDetail user = SecurityUser.getUser();
        if (user != null) {
            agent.setUpdater(user.getId());
        }
    } catch (Exception e) {
        // Server secret filter - no user context
    }
    agent.setUpdatedAt(new Date());

    // 5. Commit to database
    this.updateById(agent);

    // 6. Log the change
    System.out.println("🔄 ===== AGENT MODE UPDATE =====");
    System.out.println("Agent ID: " + agentId);
    System.out.println("Template: " + modeName);
    System.out.println("Old Prompt: " + oldPrompt.substring(0, 100) + "...");
    System.out.println("New Prompt: " + template.getSystemPrompt().substring(0, 100) + "...");
    System.out.println("================================");

    // 7. Return new prompt to caller
    return template.getSystemPrompt();
}
```

**SQL Generated:**
```sql
UPDATE ai_agent SET
    system_prompt = '<new prompt from template>',
    llm_model_id = '<template llm>',
    tts_model_id = '<template tts>',
    -- ... other fields
    updated_at = NOW()
WHERE id = 'agent_id_here';
```

---

### **5. Controller - AgentController.java**

**Location:** `src/main/java/xiaozhi/modules/agent/controller/AgentController.java`

```java
@PutMapping("/update-mode")
@Operation(summary = "Update agent mode from template")
public Result<String> updateMode(@RequestBody @Valid AgentUpdateModeDTO dto) {
    String updatedPrompt = agentService.updateAgentMode(dto.getAgentId(), dto.getModeName());
    return new Result<String>().ok(updatedPrompt);
}
```

**Response Format:**
```json
{
  "code": 0,
  "data": "<identity>You are a Storyteller...</identity>...",
  "msg": "success"
}
```

---

### **6. Authentication - ShiroConfig.java**

**Location:** `src/main/java/xiaozhi/modules/security/config/ShiroConfig.java`

```java
// Add to filter chain
filterMap.put("/agent/update-mode", "server");  // Uses ServerSecretFilter
```

**Authentication:**
- Uses `ServerSecretFilter` (validates `MANAGER_API_SECRET`)
- No user login required
- Allows LiveKit server to call the API

---

### **7. Helper Endpoint - Get Agent ID by MAC**

**Location:** `AgentController.java`

```java
@GetMapping("/device/{macAddress}/agent-id")
@Operation(summary = "Get agent ID by device MAC address")
public Result<String> getAgentIdByMac(@PathVariable("macAddress") String macAddress) {
    String cleanMac = macAddress.replace(":", "").replace("-", "").toLowerCase();

    DeviceEntity device = deviceService.getDeviceByMacAddress(cleanMac);
    if (device == null) {
        return new Result<String>().error("Device not found");
    }

    if (StringUtils.isBlank(device.getAgentId())) {
        return new Result<String>().error("No agent associated with device");
    }

    return new Result<String>().ok(device.getAgentId());
}
```

**Authentication:**
```java
filterMap.put("/agent/device/*/agent-id", "server");
```

---

### **8. MAC Address Format Handling**

**Location:** `DeviceServiceImpl.java`

```java
@Override
public DeviceEntity getDeviceByMacAddress(String macAddress) {
    // Try exact match first
    QueryWrapper<DeviceEntity> wrapper = new QueryWrapper<>();
    wrapper.eq("mac_address", macAddress);
    DeviceEntity device = baseDao.selectOne(wrapper);

    // If not found and no colons, try with colons (68:25:dd:ba:39:78)
    if (device == null && !macAddress.contains(":")) {
        String macWithColons = macAddress.replaceAll("(.{2})", "$1:").replaceAll(":$", "");
        wrapper = new QueryWrapper<>();
        wrapper.eq("mac_address", macWithColons);
        device = baseDao.selectOne(wrapper);
    }

    // If not found and has colons, try without
    if (device == null && macAddress.contains(":")) {
        String macWithoutColons = macAddress.replace(":", "");
        wrapper = new QueryWrapper<>();
        wrapper.eq("mac_address", macWithoutColons);
        device = baseDao.selectOne(wrapper);
    }

    return device;
}
```

**Handles both formats:**
- `6825ddba3978`
- `68:25:dd:ba:39:78`

---

## Frontend Implementation (LiveKit Server)

### **File Structure**

```
livekit-server/
├── main.py                          # Session initialization
├── src/
│   ├── agent/
│   │   └── main_agent.py           # Agent class with function tools
│   └── utils/
│       └── database_helper.py      # Database API calls
```

---

### **1. Agent Initialization - main.py**

**Location:** `main.py`

```python
# Create agent with initial prompt
assistant = Assistant(instructions=agent_prompt)

# Inject services
assistant.set_services(music_service, story_service, audio_player, ...)

# Pass room info (includes device MAC)
assistant.set_room_info(room_name=room_name, device_mac=device_mac)

# Start session
await session.start(agent=assistant, room=ctx.room)

# Pass session reference for dynamic updates
assistant.set_agent_session(session)
logger.info("🔗 Session reference passed to assistant")
```

**Key:** `set_agent_session()` allows runtime instruction updates.

---

### **2. Agent Class - main_agent.py**

**Location:** `src/agent/main_agent.py`

```python
class Assistant(Agent):
    """Main AI Assistant agent class"""

    def __init__(self, instructions: str = None):
        super().__init__(instructions=instructions)

        # Service references
        self.music_service = None
        self.story_service = None

        # Room and device info
        self.room_name = None
        self.device_mac = None

        # Session reference for dynamic updates
        self._agent_session = None

    def set_room_info(self, room_name: str = None, device_mac: str = None):
        """Set room name and device MAC address"""
        self.room_name = room_name
        self.device_mac = device_mac

    def set_agent_session(self, session):
        """Set session reference for dynamic updates"""
        self._agent_session = session
```

**Note:** `self._agent_session` stores reference to LiveKit AgentSession.

---

### **3. Function Tool - update_agent_mode()**

**Location:** `src/agent/main_agent.py`

```python
@function_tool
async def update_agent_mode(self, context: RunContext, mode_name: str) -> str:
    """Update agent configuration mode by applying a template

    Args:
        mode_name: Template mode name (e.g., "Cheeko", "Storyteller")

    Returns:
        Success or error message
    """
    try:
        import os
        import aiohttp

        # 1. Validate device MAC
        if not self.device_mac:
            return "Device MAC address is not available"

        # 2. Get Manager API configuration
        manager_api_url = os.getenv("MANAGER_API_URL")
        manager_api_secret = os.getenv("MANAGER_API_SECRET")

        if not manager_api_url or not manager_api_secret:
            return "Manager API is not configured"

        # 3. Fetch agent_id using DatabaseHelper
        db_helper = DatabaseHelper(manager_api_url, manager_api_secret)
        agent_id = await db_helper.get_agent_id(self.device_mac)

        if not agent_id:
            return f"No agent found for device MAC: {self.device_mac}"

        logger.info(f"🔄 Updating agent {agent_id} to mode: {mode_name}")

        # 4. Call update-mode API
        url = f"{manager_api_url}/agent/update-mode"
        headers = {
            "Authorization": f"Bearer {manager_api_secret}",
            "Content-Type": "application/json"
        }
        payload = {
            "agentId": agent_id,
            "modeName": mode_name
        }

        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.put(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"✅ Agent mode updated in database to '{mode_name}'")

                    # 5. Get the new prompt from API response
                    if result.get('code') == 0 and result.get('data'):
                        new_prompt = result.get('data')

                        # 6. Update agent's instructions dynamically
                        self._instructions = new_prompt
                        logger.info(f"📝 Instructions updated (length: {len(new_prompt)})")

                        # 7. Update active session
                        if self._agent_session:
                            try:
                                self._agent_session._agent._instructions = new_prompt
                                logger.info(f"🔄 Session instructions updated in real-time!")
                            except Exception as e:
                                logger.warning(f"⚠️ Could not update session: {e}")

                        return f"Successfully updated agent mode to '{mode_name}'! The changes are now active."
                    else:
                        return f"Mode updated in database. Please reconnect."
                else:
                    return f"Failed to update mode: {response.status}"

    except Exception as e:
        logger.error(f"Error updating agent mode: {e}")
        return f"Error: {str(e)}"
```

---

### **4. Database Helper - database_helper.py**

**Location:** `src/utils/database_helper.py`

```python
class DatabaseHelper:
    """Helper class for database-related operations via Manager API"""

    def __init__(self, manager_api_url: str, secret: str):
        self.manager_api_url = manager_api_url.rstrip('/')
        self.secret = secret

    async def get_agent_id(self, device_mac: str) -> Optional[str]:
        """Get agent_id from database using device MAC address"""
        url = f"{self.manager_api_url}/agent/device/{device_mac}/agent-id"
        headers = {
            "Authorization": f"Bearer {self.secret}",
            "Content-Type": "application/json"
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    # Handle Result<String> format: {code: 0, data: "agent_id"}
                    if data.get('code') == 0 and data.get('data'):
                        agent_id = data.get('data')
                        logger.info(f"🆔✅ Retrieved agent_id: {agent_id}")
                        return str(agent_id)

        return None
```

---

## Dynamic Session Update

### **How LiveKit Session Instructions Are Updated**

The LiveKit `Agent` class has a read-only `instructions` property. To update it dynamically:

```python
# Agent class structure (simplified)
class Agent:
    def __init__(self, instructions: str):
        self._instructions = instructions  # Internal storage

    @property
    def instructions(self):
        return self._instructions  # Read-only!

    # No setter method
```

**Solution:**
1. Access internal `_instructions` attribute directly
2. Update both agent and session references

```python
# Update agent's instructions
self._instructions = new_prompt

# Update session's agent instructions
if self._agent_session:
    self._agent_session._agent._instructions = new_prompt
```

**Result:** Next AI response uses the new prompt immediately!

---

## Data Flow

### **Complete Request Flow**

```
┌────────────────────────────────────────────────────────────┐
│ 1. User says: "Switch to Storyteller mode"                 │
└───────────────────┬────────────────────────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────────────────────────┐
│ 2. LiveKit AI Agent (LLM)                                  │
│    Detects intent → Calls update_agent_mode("Storyteller") │
└───────────────────┬────────────────────────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────────────────────────┐
│ 3. Get Agent ID                                            │
│    GET /agent/device/68:25:dd:ba:39:78/agent-id            │
│    Response: { code: 0, data: "11507ab8..." }              │
└───────────────────┬────────────────────────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────────────────────────┐
│ 4. Update Mode                                             │
│    PUT /agent/update-mode                                  │
│    Body: { agentId: "11507ab8...", modeName: "Storyteller" }│
└───────────────────┬────────────────────────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────────────────────────┐
│ 5. Manager API - AgentServiceImpl.updateAgentMode()       │
│    a. SELECT * FROM ai_agent WHERE id = '11507ab8...'      │
│    b. SELECT * FROM ai_agent_template                      │
│       WHERE agent_name = 'Storyteller' LIMIT 1             │
│    c. agent.setSystemPrompt(template.getSystemPrompt())    │
│    d. UPDATE ai_agent SET system_prompt = '...'            │
│       WHERE id = '11507ab8...'                             │
│    e. COMMIT transaction                                   │
│    f. RETURN new prompt                                    │
└───────────────────┬────────────────────────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────────────────────────┐
│ 6. Response to LiveKit                                     │
│    { code: 0,                                              │
│      data: "<identity>You are a Storyteller...</identity>",│
│      msg: "success" }                                      │
└───────────────────┬────────────────────────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────────────────────────┐
│ 7. LiveKit Updates Instructions                           │
│    a. self._instructions = new_prompt                      │
│    b. self._agent_session._agent._instructions = new_prompt│
└───────────────────┬────────────────────────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────────────────────────┐
│ 8. AI Response to User                                     │
│    "Successfully updated agent mode to 'Storyteller'!      │
│     The changes are now active in this conversation."      │
└────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────────────────────────┐
│ 9. Next User Message                                       │
│    AI responds using NEW Storyteller prompt! ✅            │
└────────────────────────────────────────────────────────────┘
```

---

## API Endpoints

### **1. Update Agent Mode**

**Endpoint:** `PUT /agent/update-mode`

**Authentication:** Server Secret (`Authorization: Bearer {MANAGER_API_SECRET}`)

**Request:**
```json
{
  "agentId": "11507ab86d464c769803b12e228791c9",
  "modeName": "Storyteller"
}
```

**Response (Success):**
```json
{
  "code": 0,
  "data": "<identity>You are a magical storyteller...</identity>...",
  "msg": "success"
}
```

**Response (Error):**
```json
{
  "code": 1,
  "data": null,
  "msg": "模板 'InvalidMode' 不存在"
}
```

---

### **2. Get Agent ID by MAC**

**Endpoint:** `GET /agent/device/{macAddress}/agent-id`

**Authentication:** Server Secret

**Request:**
```
GET /agent/device/68:25:dd:ba:39:78/agent-id
```

**Response (Success):**
```json
{
  "code": 0,
  "data": "11507ab86d464c769803b12e228791c9",
  "msg": "success"
}
```

**Response (Error):**
```json
{
  "code": 1,
  "data": null,
  "msg": "Device not found for MAC address: 68:25:dd:ba:39:78"
}
```

---

### **3. Get Agent Prompt by MAC**

**Endpoint:** `GET /agent/prompt/{macAddress}`

**Authentication:** Server Secret

**Request:**
```
GET /agent/prompt/68:25:dd:ba:39:78
```

**Response:**
```json
{
  "code": 0,
  "data": "<identity>You are Cheeko...</identity>...",
  "msg": "success"
}
```

---

## Testing

### **Manual Testing Steps**

#### **1. Prepare Test Data**

Ensure templates exist:
```sql
SELECT id, agent_name FROM ai_agent_template;
```

Expected output:
```
+----------------------------------+-------------+
| id                               | agent_name  |
+----------------------------------+-------------+
| 9406648b5cc5fde1b8aa335b6f8b4f76 | Cheeko      |
| template_id_2                    | Storyteller |
+----------------------------------+-------------+
```

#### **2. Test Backend API**

```bash
# Get agent ID
curl -X GET "http://localhost:8080/agent/device/68:25:dd:ba:39:78/agent-id" \
  -H "Authorization: Bearer your_manager_api_secret"

# Update mode
curl -X PUT "http://localhost:8080/agent/update-mode" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_manager_api_secret" \
  -d '{
    "agentId": "11507ab86d464c769803b12e228791c9",
    "modeName": "Storyteller"
  }'
```

#### **3. Test LiveKit Integration**

1. Start LiveKit conversation
2. User says: "Switch to Storyteller mode"
3. Check logs for:
   ```
   🔄 Updating agent 11507... to mode: Storyteller
   ✅ Agent mode updated in database
   📝 Instructions updated dynamically (length: 2500 chars)
   🔄 Session instructions updated in real-time!
   ```
4. Next user message should get Storyteller-style response

#### **4. Verify Database Update**

```sql
SELECT
    id,
    agent_name,
    SUBSTRING(system_prompt, 1, 100) as prompt_preview,
    updated_at
FROM ai_agent
WHERE id = '11507ab86d464c769803b12e228791c9';
```

---

### **Expected Logs**

#### **Manager API Logs:**

```
🔄 ===== AGENT MODE UPDATE =====
Agent ID: 11507ab86d464c769803b12e228791c9
Agent Name: Cheeko
Template: Storyteller (template_id)
Old Prompt Preview: <identity>You are Cheeko, a playful AI...
New Prompt Preview: <identity>You are a magical storyteller...
New LLM Model: LLM_groq_llama3.3_70b
New TTS Model: TTS_EdgeTTS
Database Updated: YES ✅
================================
```

#### **LiveKit Server Logs:**

```
2025-10-03 17:55:23 - INFO - 🔄 Updating agent 11507... to mode: Storyteller
2025-10-03 17:55:23 - INFO - ✅ Agent mode updated in database to 'Storyteller'
2025-10-03 17:55:23 - INFO - 📦 API Response: code=0, has_data=True, data_length=2500
2025-10-03 17:55:23 - INFO - 📝 Instructions updated dynamically (length: 2500 chars)
2025-10-03 17:55:23 - INFO - 📝 New prompt preview: <identity>You are a magical storyteller...
2025-10-03 17:55:23 - INFO - 🔄 Session instructions updated in real-time!
```

---

## Troubleshooting

### **Issue 1: "Device not found for MAC address"**

**Cause:** Device not registered in `ai_device` table.

**Solution:**
```sql
INSERT INTO ai_device (id, mac_address, agent_id, user_id, board, create_date)
VALUES (
    'device_6825ddba3978',
    '68:25:dd:ba:39:78',  -- Or '6825ddba3978' (both work)
    'agent_id_here',
    1,
    'ESP32',
    NOW()
);
```

---

### **Issue 2: "Template 'Storyteller' not found"**

**Cause:** Template doesn't exist in `ai_agent_template`.

**Solution:**
```sql
INSERT INTO ai_agent_template (
    id, agent_name, system_prompt, llm_model_id, tts_model_id, created_at
) VALUES (
    UUID(),
    'Storyteller',
    '<identity>You are a magical storyteller...</identity>',
    'LLM_groq_llama3.3_70b',
    'TTS_EdgeTTS',
    NOW()
);
```

---

### **Issue 3: "401 Unauthorized"**

**Cause:** Missing or incorrect `MANAGER_API_SECRET`.

**Solution:**
1. Check `.env` file in LiveKit server:
   ```bash
   MANAGER_API_URL=http://localhost:8080
   MANAGER_API_SECRET=your_secret_here
   ```

2. Verify Shiro config includes endpoint:
   ```java
   filterMap.put("/agent/update-mode", "server");
   ```

---

### **Issue 4: "No prompt data in response"**

**Cause:** API not returning prompt in response.

**Debug:**
```python
# Check API response
logger.info(f"Response: {result}")
```

**Verify:**
- Controller returns `Result<String>` (not `Result<Void>`)
- Service returns prompt string
- Transaction commits before returning

---

### **Issue 5: "Session instructions not updating"**

**Cause:** Session reference not set.

**Solution:**
Ensure `set_agent_session()` is called in `main.py`:
```python
await session.start(agent=assistant, room=ctx.room)
assistant.set_agent_session(session)  # ← MUST be after session.start()
```

---

### **Issue 6: "MAC address format mismatch"**

**Cause:** Database stores `68:25:dd:ba:39:78` but API searches `6825ddba3978`.

**Solution:**
Already handled in `DeviceServiceImpl.getDeviceByMacAddress()` - tries both formats.

---

## Configuration

### **Environment Variables (LiveKit Server)**

```bash
# Manager API
MANAGER_API_URL=http://localhost:8080
MANAGER_API_SECRET=your_secret_key_here

# LiveKit
LIVEKIT_URL=ws://localhost:7880
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret
```

---

### **Shiro Filter Configuration**

**File:** `ShiroConfig.java`

```java
// Server secret authentication (no user login)
filterMap.put("/agent/update-mode", "server");
filterMap.put("/agent/device/*/agent-id", "server");
filterMap.put("/agent/prompt/**", "server");
```

---

## Summary

### **Key Features**

✅ **Dynamic prompt switching** - No reconnection required
✅ **Database persistence** - Changes saved for future sessions
✅ **Real-time update** - Next AI response uses new personality
✅ **Template-based** - Easy to add new modes
✅ **Secure** - Server secret authentication
✅ **Flexible MAC format** - Handles both `68:25:dd:ba:39:78` and `6825ddba3978`

---

### **Files Modified**

**Backend (Manager API):**
- ✅ `AgentController.java` - Added endpoints
- ✅ `AgentService.java` - Added interface method
- ✅ `AgentServiceImpl.java` - Core logic implementation
- ✅ `AgentTemplateService.java` - Added template query
- ✅ `AgentTemplateServiceImpl.java` - Template query implementation
- ✅ `AgentUpdateModeDTO.java` - New DTO created
- ✅ `ShiroConfig.java` - Added authentication filters
- ✅ `DeviceServiceImpl.java` - MAC format handling

**Frontend (LiveKit Server):**
- ✅ `main.py` - Session reference passing
- ✅ `main_agent.py` - Function tool + dynamic update
- ✅ `database_helper.py` - API helper methods

---

### **Implementation Time**

Total implementation: **~4 hours**

Breakdown:
- Backend API: 2 hours
- Frontend function tool: 1 hour
- Dynamic session update: 1 hour
- Testing & debugging: 1 hour (included)

---

## Future Enhancements

### **Potential Improvements**

1. **Fuzzy Mode Name Matching**
   - Handle typos: "storyteler" → "Storyteller"
   - Support aliases: "story mode" → "Storyteller"

2. **Mode History**
   - Track mode changes per session
   - Allow "switch back to previous mode"

3. **Custom User Modes**
   - Let users create personal templates
   - Save custom prompts per user

4. **Voice Personality Switch**
   - Change TTS voice along with prompt
   - Different voices for different modes

5. **Gradual Transition**
   - "Switching to storyteller mode..." message
   - Smooth personality transition

---

## License

This implementation is part of the Cheeko ESP32 Server project.

---

## Support

For issues or questions:
- Check logs in Manager API and LiveKit Server
- Verify database schema matches documentation
- Ensure all environment variables are set
- Test API endpoints independently before integration

---

**Documentation Version:** 1.0
**Last Updated:** 2025-10-03
**Author:** Implementation by Claude (Anthropic)
