# Dynamic Prompt Management System

## Overview

This document describes the implementation of a dynamic prompt management system for the LiveKit agent that allows prompts to be stored in a database and fetched dynamically, enabling easy testing of different prompts without code changes.

## Problem Statement

- **Before**: LiveKit agent prompts were hardcoded in `main_agent.py`
- **Challenge**: Testing different prompts required code changes and redeployment
- **Need**: Dynamic prompt loading from database with easy switching between local and API modes

## Solution Architecture

### High-Level Flow (Updated 2024)

```
Device MQTT → MQTT Gateway → LiveKit Data Channel → Agent → PromptService → [Config Flag] → API or Local Prompt → Dynamic Update
```

### Components

1. **Config-Based Control**: `read_config_from_api` flag in `config.yaml`
2. **Prompt Service**: Python service handling prompt fetching logic
3. **API Endpoint**: Java Spring Boot endpoint for database prompt retrieval
4. **Data Channel Communication**: LiveKit data channel for real-time MAC address transmission
5. **Dynamic Update System**: Real-time prompt updates using LiveKit's official API
6. **Fallback System**: Graceful degradation to local prompt when API fails

## Implementation Plan

### Phase 1: Configuration Setup ✅

**File**: `main/livekit-server/config.yaml`

**Changes**:
- Added `read_config_from_api` boolean flag
- Added `default_prompt` section with full Cheeko prompt
- Existing `manager_api` configuration for API access

```yaml
# Configuration source control
read_config_from_api: true  # true = API mode, false = local mode

# Default agent prompt (used when read_config_from_api is false)
default_prompt: |
  <identity>
  You are Cheeko, a playful and slightly mischievous AI companion...
  </identity>
  # ... full prompt content

# Manager API settings (used when read_config_from_api is true)
manager_api:
  url: "http://192.168.1.5:8002/toy"
  secret: "a3c1734a-1efe-4ab7-8f43-98f88b874e4b"
  timeout: 5
  cache_duration: 30  # seconds
```

### Phase 2: Python Prompt Service ✅

**File**: `main/livekit-server/src/services/prompt_service.py`

**Features**:
- Config flag checking (`should_read_from_api()`)
- MAC address extraction from LiveKit room names
- API communication with proper authentication
- Caching mechanism (5-minute TTL)
- Robust error handling and fallback
- Support for different room name formats

**Key Methods**:
```python
async def get_prompt(room_name: str) -> str
def should_read_from_api() -> bool
def get_default_prompt() -> str
async def fetch_prompt_from_api(mac_address: str) -> Optional[str]
```

### Phase 3: Configuration Loader Updates ✅

**File**: `main/livekit-server/src/config/config_loader.py`

**Additions**:
- `load_yaml_config()` - Load config.yaml
- `should_read_from_api()` - Check API flag
- `get_default_prompt()` - Extract default prompt
- `get_manager_api_config()` - API configuration

### Phase 4: Agent Integration ✅

**File**: `main/livekit-server/src/agent/main_agent.py`

**Changes**:
- Modified `Assistant.__init__()` to accept `instructions` parameter
- Removed hardcoded prompt
- Made prompt injection dynamic

**Before**:
```python
def __init__(self) -> None:
    super().__init__(instructions="<hardcoded prompt>")
```

**After**:
```python
def __init__(self, instructions: str = None) -> None:
    if instructions is None:
        instructions = "You are a helpful AI assistant."
    super().__init__(instructions=instructions)
```

### Phase 5: Main Entry Point Integration ✅

**File**: `main/livekit-server/main.py`

**Changes**:
- Import `PromptService`
- Initialize agent with default prompt at startup
- Set up data channel handlers for dynamic updates
- Graceful fallback on errors

**Integration Code**:
```python
# Initialize prompt service with default prompt first
prompt_service = PromptService()
agent_prompt = ConfigLoader.get_default_prompt()
logger.info(f"📄 Starting with default prompt (length: {len(agent_prompt)} chars)")
logger.info("📡 Device-specific prompt will be loaded via data channel when MQTT gateway connects")

# Create agent with default prompt (will be updated dynamically)
assistant = Assistant(instructions=agent_prompt)
```

### Phase 6: Java API Endpoint ✅

**File**: `main/manager-api/src/main/java/xiaozhi/modules/config/controller/ConfigController.java`

**New Endpoint**: `POST /config/agent-prompt`

**Features**:
- Uses existing server secret authentication pattern
- Follows established `/config/**` endpoint structure
- Accepts MAC address in JSON payload
- Returns prompt from database via device → agent binding

**Implementation**:
```java
@PostMapping("agent-prompt")
@Operation(summary = "获取智能体提示词")
public Result<String> getAgentPrompt(@Valid @RequestBody Map<String, String> request) {
    String macAddress = request.get("macAddress");
    if (macAddress == null || macAddress.trim().isEmpty()) {
        return new Result<String>().error("MAC address is required");
    }

    String prompt = configService.getAgentPrompt(macAddress);
    return new Result<String>().ok(prompt);
}
```

### Phase 7: Service Layer Implementation ✅

**File**: `main/manager-api/src/main/java/xiaozhi/modules/config/service/impl/ConfigServiceImpl.java`

**New Method**: `getAgentPrompt(String macAddress)`

**Logic Flow**:
1. Look up device by MAC address
2. Get associated agent ID from device
3. Retrieve agent entity from database
4. Extract and return `system_prompt` field
5. Proper error handling for missing devices/agents

**Implementation**:
```java
@Override
public String getAgentPrompt(String macAddress) {
    // 根据MAC地址查找设备
    DeviceEntity device = deviceService.getDeviceByMacAddress(macAddress);
    if (device == null) {
        throw new RenException(ErrorCode.OTA_DEVICE_NOT_FOUND, "Device not found for MAC: " + macAddress);
    }

    // 获取智能体信息
    AgentEntity agent = agentService.selectById(device.getAgentId());
    if (agent == null) {
        throw new RenException("Agent not found for device: " + macAddress);
    }

    // 返回系统提示词
    String systemPrompt = agent.getSystemPrompt();
    if (StringUtils.isBlank(systemPrompt)) {
        throw new RenException("No system prompt configured for agent: " + agent.getAgentName());
    }

    return systemPrompt;
}
```

### Phase 8: Security Configuration ✅

**File**: `main/manager-api/src/main/java/xiaozhi/modules/security/config/ShiroConfig.java`

**Addition**: Added `/agent/prompt/**` to server filter chain

```java
filterMap.put("/config/**", "server");        // Existing
filterMap.put("/agent/prompt/**", "server");  // Added for original endpoint
```

**Note**: Final implementation uses `/config/agent-prompt` which was already covered by `/config/**` pattern.

### Phase 9: MQTT Gateway Data Channel Integration ✅

**File**: `main/mqtt-gateway/app.js`

**Changes**:
- Modified `sendInitialGreeting()` to send device info
- Added `device_info` message with MAC address
- Sends MAC via LiveKit data channel before agent greeting

**Implementation**:
```javascript
// First send device information for prompt loading
const deviceInfoMessage = {
  type: "device_info",
  device_mac: this.macAddress,
  device_uuid: this.uuid,
  timestamp: Date.now(),
  source: "mqtt_gateway"
};

// Send device info via LiveKit data channel
const deviceInfoData = new Uint8Array(Buffer.from(JSON.stringify(deviceInfoMessage), 'utf8'));
await this.room.localParticipant.publishData(deviceInfoData, { reliable: true });
```

### Phase 10: Dynamic Chat Context Update ✅

**File**: `main/livekit-server/src/handlers/chat_logger.py`

**Changes**:
- Added `_handle_device_info()` method
- Uses LiveKit's official `session.history` and `update_chat_ctx()`
- Implements complete prompt replacement strategy
- Comprehensive error handling and debugging

**Implementation**:
```python
@staticmethod
async def _handle_device_info(session, ctx, device_mac):
    # Fetch device-specific prompt
    device_prompt = await prompt_service.get_prompt(ctx.room.name, device_mac)

    # Update chat context using LiveKit's official API
    current_ctx = session.history

    # Replace existing system message or add new one
    for i, msg in enumerate(current_ctx.messages):
        if hasattr(msg, 'role') and msg.role == "system":
            msg.content = device_prompt  # Complete replacement
            break
    else:
        current_ctx.append(text=device_prompt, role="system")

    # Apply changes
    if hasattr(session, 'update_chat_ctx'):
        session.update_chat_ctx(current_ctx)
```

## System Flow (Updated 2024)

### 1. Device Connection & Communication
```
Device MQTT → EMQX Broker → MQTT Gateway → LiveKit WebSocket → LiveKit Server
```

### 2. Agent Dispatch & Initial Setup
```
LiveKit Server → Agent Job → AgentSession → Default Prompt → Agent Ready
```

### 3. Dynamic Prompt Update Flow
```
MQTT Gateway → LiveKit Data Channel → device_info Message →
Agent Chat Logger → PromptService → API Call → Database Lookup →
Chat Context Update → Agent Personality Changed
```

### 4. MAC Address Transmission
```
MQTT Gateway: {type: "device_info", device_mac: "00:16:3e:ac:b5:38"}
→ LiveKit Data Channel → Agent Receives MAC → API Call
```

### 5. Prompt Replacement Strategy
```
Agent Start: Default Prompt (4188 chars) → Device Info Received →
Device Prompt Fetched (900 chars) → Complete Replacement →
Agent Uses Device-Specific Behavior
```

### 6. Config Flag Check
```
read_config_from_api: true  → API Mode (fetch from database)
read_config_from_api: false → Local Mode (use config.yaml)
```

### 7. Fallback Mechanism
```
API Call → [Success] → Complete prompt replacement
         → [Failure] → Continue with default prompt
```

## Database Schema

### Required Tables

**ai_device**:
- `mac_address` (VARCHAR) - Device MAC address
- `agent_id` (VARCHAR) - FK to ai_agent table

**ai_agent**:
- `id` (VARCHAR) - Primary key
- `system_prompt` (TEXT) - The prompt content
- `agent_name` (VARCHAR) - Agent display name

### Server Configuration

**sys_params**:
- `param_code`: "server.secret"
- `param_value`: Server secret for API authentication

## Testing & Usage (Updated 2024)

### Testing Different Modes

1. **Local Mode Testing**:
   ```yaml
   read_config_from_api: false
   ```
   - Agent uses prompt from `default_prompt` in config.yaml
   - No network calls made
   - Instant startup, no dynamic updates

2. **API Mode Testing**:
   ```yaml
   read_config_from_api: true
   ```
   - Agent starts with default prompt
   - MQTT gateway sends device MAC via data channel
   - Agent dynamically fetches and applies device-specific prompt
   - Falls back to default if API fails
   - Caches successful responses

### Real-Time Testing Process

1. **Start Agent**: Agent begins with default prompt (4188 chars)
2. **Device Connects**: MQTT gateway sends device_info message
3. **Prompt Update**: Agent fetches device-specific prompt (900 chars)
4. **Behavior Change**: Agent immediately uses new personality
5. **Logging**: Full prompt content logged for verification

### Updating Prompts

1. **Local Prompts**: Edit `default_prompt` in config.yaml (requires restart)
2. **Database Prompts**: Update `system_prompt` field in `ai_agent` table via manager UI (immediate effect)
3. **No Code Changes**: Switch modes by toggling config flag
4. **Real-time Updates**: Changes apply immediately when device connects

### Device Setup

1. Ensure device is registered in `ai_device` table with MAC format `00:16:3e:ac:b5:38`
2. Bind device to an agent (`agent_id` field)
3. Configure agent's `system_prompt` field
4. Test with any room name format (MAC transmitted via data channel)

### Verification Steps

1. **Check Logs**: Look for "📝 Device-specific prompt content:" in logs
2. **Prompt Length**: Default (4188 chars) → Device-specific (varies)
3. **Agent Behavior**: Test if agent follows device-specific rules
4. **Fallback**: Test with unregistered device (should use default)

## API Reference

### Endpoint: POST /config/agent-prompt

**Authentication**: Server Secret (Bearer token)

**Request**:
```json
{
  "macAddress": "00163eacb538"
}
```

**Response**:
```json
{
  "code": 0,
  "data": "<prompt content>",
  "msg": null
}
```

**Headers**:
```
Authorization: Bearer a3c1734a-1efe-4ab7-8f43-98f88b874e4b
Content-Type: application/json
```

## Error Handling

### Common Scenarios

1. **Device Not Found**: Returns error, falls back to default prompt
2. **Agent Not Found**: Returns error, falls back to default prompt
3. **Empty Prompt**: Returns error, falls back to default prompt
4. **Network Timeout**: Logs warning, falls back to default prompt
5. **Authentication Failure**: Logs error, falls back to default prompt

### Logging (Updated 2024)

#### Successful Dynamic Update:
```
📱 Processing device info from MQTT gateway - MAC: 00:16:3e:ac:b5:38
🔄 Device-specific prompt fetched (length: 900 chars)
📝 Device-specific prompt content:
[Role Setting]
You are Cheeko, a friendly, curious, and playful AI friend...
✅ Added new system message using append()
✅ Successfully updated agent prompt using update_chat_ctx()
```

#### Fallback Scenarios:
- **API Fallback**: "Failed to fetch prompt from API for MAC: {mac}"
- **Local Mode**: "Using default prompt from config (read_config_from_api=false)"
- **Device Not Found**: "Device not found" → Falls back to default
- **Chat Update Failed**: "Failed to update chat context" → Agent continues with default

## Performance Considerations

### Caching Strategy
- **API Responses**: Cached for 5 minutes per MAC address
- **Config Loading**: Loaded once at startup
- **Default Prompt**: Loaded once, reused for all fallbacks

### Network Optimization
- **Timeout**: 5 seconds for API calls
- **Async**: Non-blocking API calls using aiohttp
- **Connection Reuse**: Session-based HTTP client

## Security

### Authentication
- Server secret authentication via `Authorization: Bearer` header
- Secret stored in database `sys_params` table
- Matches existing authentication pattern for `/config/**` endpoints

### Data Protection
- No sensitive data in API requests (only MAC address)
- Prompts are not sensitive but access is controlled
- Fallback ensures service availability even if auth fails

## Monitoring & Troubleshooting

### Key Metrics
- Prompt fetch success rate
- API response times
- Fallback usage frequency
- Cache hit rates

### Debug Information
- Room name → MAC extraction results
- API endpoint URLs and responses
- Cache status per MAC address
- Config flag status

### Common Issues

1. **Always Using Default Prompt**:
   - Check `read_config_from_api` flag
   - Verify manager API URL and secret
   - Check device-agent binding in database

2. **Authentication Errors**:
   - Verify server secret in database matches config
   - Check if manager API server is running
   - Ensure endpoint is accessible

3. **Device Not Found**:
   - Verify device MAC address in database
   - Check room name format
   - Ensure MAC address extraction logic

## Future Enhancements

### Potential Improvements

1. **Prompt Versioning**: Track prompt changes over time
2. **A/B Testing**: Support for multiple prompt variants
3. **Prompt Templates**: Parameterized prompts with variables
4. **Real-time Updates**: WebSocket-based prompt updates
5. **Analytics**: Track prompt effectiveness metrics
6. **Multi-language**: Prompt localization support

### Configuration Extensions

1. **Environment-specific Prompts**: Different prompts per environment
2. **User-specific Prompts**: Personalized prompts per user
3. **Time-based Prompts**: Different prompts based on time of day
4. **Context-aware Prompts**: Prompts based on conversation history

## Conclusion (Updated 2024)

The dynamic prompt management system successfully achieves the goal of enabling easy prompt testing without code changes. The implementation provides:

- ✅ **Flexible Configuration**: Easy switching between local and API modes
- ✅ **Real-time Updates**: Dynamic prompt changes without agent restarts
- ✅ **Robust Fallback**: Always functional even when API fails
- ✅ **Production Ready**: Proper error handling and comprehensive logging
- ✅ **Performance Optimized**: Caching and async operations
- ✅ **Secure**: Proper authentication and access control
- ✅ **Developer Friendly**: Clear separation of concerns
- ✅ **LiveKit Native**: Uses official LiveKit v1.x API methods
- ✅ **Complete Replacement**: Device-specific prompts completely override defaults
- ✅ **Data Channel Communication**: Real-time MAC transmission via LiveKit

### Key Innovations (2024):

1. **Data Channel Integration**: Uses LiveKit's native data channel for MAC transmission
2. **Dynamic Chat Context Updates**: Real-time prompt updates using `session.history` and `update_chat_ctx()`
3. **Complete Prompt Replacement**: Device-specific prompts entirely replace default behavior
4. **Timing Independence**: No more race conditions or waiting for participants
5. **Comprehensive Debugging**: Full prompt content logging and detailed error information

This system enables rapid iteration on agent prompts while maintaining system reliability, performance, and real-time responsiveness.