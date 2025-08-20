# Vue.js Dashboard - Complete Guide & Importance

## 🎯 Purpose of the Vue.js Dashboard

The Vue.js dashboard (`manager-web`) is the **central control panel** for managing your entire Cheeko AI toy ecosystem. It's not just a nice-to-have interface - it's the critical management layer that controls how your devices behave, what AI models they use, and how users interact with the system.

## 🔄 How Dashboard Changes Affect Your Application

### 1. **Agent Configuration → Device Personality**
When you modify an agent in the dashboard:
```
Dashboard Action → Database Update → Python Server Reads → Device Behavior Changes
```

**Example Flow:**
- You change agent prompt from "Be friendly" to "Be educational"
- Dashboard saves to `ai_agent` table
- Python server reads new prompt on next connection
- Device now responds educationally instead of just friendly

### 2. **Model Provider Settings → AI Service Selection**
```yaml
Dashboard Model Config → Changes Which AI Services Are Used:
- Switch from Groq to OpenAI → Different response quality/speed
- Change TTS from ElevenLabs to EdgeTTS → Different voice quality
- Update ASR from Sherpa to Whisper → Different speech recognition accuracy
```

### 3. **Device Management → User Access Control**
```
Dashboard Device Binding → Controls Which Devices Can Connect:
- Bind device to agent → Device gets personality
- Unbind device → Device loses access
- Update firmware → Device gets new capabilities
```

## 📊 Dashboard Features & Their Database Dependencies

| Dashboard Feature | Required Tables | Impact on Application |
|------------------|-----------------|----------------------|
| **User Login** | `sys_user`, `sys_user_token` | Controls who can manage system |
| **Agent Management** | `ai_agent`, `ai_agent_template` | Defines AI personalities |
| **Device Control** | `device`, `device_ota_mag` | Manages ESP32 connections |
| **Model Configuration** | `model_provider`, `model_config` | Selects AI services |
| **Chat History Viewer** | `ai_agent_chat_history`, `ai_agent_chat_audio` | Reviews conversations |
| **Voice Customization** | `timbre` | Changes TTS voices |
| **System Settings** | `sys_params`, `sys_dict_*` | Global configurations |
| **Usage Analytics** | `usage_stats` | Monitors system usage |

## 🗄️ Critical Tables for Dashboard Functionality

### **MUST HAVE Tables** (Dashboard won't work without these):
1. **`sys_user`** - User authentication
2. **`sys_user_token`** - Session management
3. **`ai_agent`** - Agent configurations
4. **`device`** - Device registry
5. **`sys_params`** - System settings

### **IMPORTANT Tables** (Major features disabled without these):
6. **`ai_agent_chat_history`** - Chat history feature
7. **`model_provider`** - Model management
8. **`model_config`** - Model settings
9. **`device_ota`** - Firmware updates
10. **`timbre`** - Voice customization

### **OPTIONAL Tables** (Enhanced features):
11. **`sys_dict_type`, `sys_dict_data`** - Dropdown options
12. **`ai_agent_template`** - Template library
13. **`usage_stats`** - Analytics dashboard
14. **`ai_agent_plugin_mapping`** - Plugin management

## 🔧 How Each Dashboard Page Uses the Database

### 1. **Home Page (Agent List)**
```javascript
// Fetches from database:
SELECT * FROM ai_agent WHERE user_id = ?
SELECT * FROM device WHERE user_id = ?
```
**Purpose:** Shows all your AI agents and their bound devices

### 2. **Device Management Page**
```javascript
// Operations:
- Add Device: INSERT INTO device
- Bind Agent: UPDATE device SET agent_id = ?
- View Status: SELECT * FROM device WHERE user_id = ?
```
**Purpose:** Connect ESP32 devices to AI agents

### 3. **Model Configuration Page**
```javascript
// Configuration flow:
- List Providers: SELECT * FROM model_provider
- Update Settings: UPDATE model_config SET parameters = ?
- Test Connection: Validates API keys
```
**Purpose:** Configure which AI services to use (Groq, ElevenLabs, etc.)

### 4. **Chat History Page**
```javascript
// Query history:
SELECT * FROM ai_agent_chat_history 
WHERE agent_id = ? 
ORDER BY create_time DESC
```
**Purpose:** Review past conversations for quality/safety

### 5. **System Settings Page**
```javascript
// Manage parameters:
SELECT * FROM sys_params
UPDATE sys_params SET param_value = ? WHERE param_code = ?
```
**Purpose:** Configure global system behavior

## 🎮 Real-World Usage Examples

### Example 1: Creating a New AI Assistant
```sql
-- Dashboard creates new agent
INSERT INTO ai_agent (
    id, 
    agent_name, 
    system_prompt, 
    model_provider,
    user_id
) VALUES (
    'agent_001',
    'Educational Cheeko',
    'You are an educational assistant for kids learning math',
    'groq',
    1
);

-- Dashboard binds device to agent
UPDATE device 
SET agent_id = 'agent_001' 
WHERE device_code = '123456';
```
**Result:** Device now acts as educational math tutor

### Example 2: Switching AI Providers
```sql
-- Dashboard updates model configuration
UPDATE model_config 
SET provider_id = (SELECT id FROM model_provider WHERE provider_name = 'openai')
WHERE model_type = 'LLM' AND is_default = 1;
```
**Result:** All devices now use OpenAI instead of Groq

### Example 3: Reviewing Usage
```sql
-- Dashboard queries analytics
SELECT 
    DATE(create_time) as date,
    COUNT(*) as messages,
    agent_id
FROM ai_agent_chat_history
WHERE user_id = 1
GROUP BY DATE(create_time), agent_id;
```
**Result:** See daily usage patterns and popular agents

## 🚀 Quick Setup Guide for Railway MySQL

### Step 1: Connect to Railway MySQL
```bash
mysql -h caboose.proxy.rlwy.net -P 41629 -u root -pIVIwxOEAWLTsPRfbhNKOmeCqVXdphTVV railway
```

### Step 2: Run the Schema
```bash
mysql -h caboose.proxy.rlwy.net -P 41629 -u root -pIVIwxOEAWLTsPRfbhNKOmeCqVXdphTVV railway < DASHBOARD_SCHEMA_RAILWAY.sql
```

### Step 3: Verify Tables Created
```sql
SHOW TABLES;
-- Should show all tables from the schema
```

### Step 4: Update Spring Boot Configuration
In `application.yml`:
```yaml
spring:
  datasource:
    url: jdbc:mysql://caboose.proxy.rlwy.net:41629/railway?useUnicode=true&characterEncoding=UTF-8&serverTimezone=UTC
    username: root
    password: IVIwxOEAWLTsPRfbhNKOmeCqVXdphTVV
```

### Step 5: Start the Dashboard
```bash
cd main/manager-web
npm install
npm run serve
```

## 📈 Impact Analysis: With vs Without Dashboard

### **WITH Dashboard:**
- ✅ Visual agent management
- ✅ Real-time device monitoring
- ✅ Easy model switching
- ✅ Chat history review
- ✅ Multi-user support
- ✅ Analytics and insights
- ✅ OTA firmware updates
- ✅ Voice customization

### **WITHOUT Dashboard:**
- ❌ Manual database edits
- ❌ No device visibility
- ❌ Config file editing only
- ❌ No conversation history
- ❌ Single configuration
- ❌ No usage tracking
- ❌ Manual firmware updates
- ❌ Fixed voice settings

## 🔐 Security Considerations

The dashboard provides critical security features:
1. **User Authentication** - Only authorized users can modify settings
2. **Token-based Sessions** - Secure API access
3. **Role-based Access** - Admin vs normal user permissions
4. **Audit Trail** - Track who changed what and when

## 💡 Best Practices

1. **Always use the dashboard for configuration changes** - Direct database edits can break consistency
2. **Regular backups** - Export your agent configurations periodically
3. **Monitor chat history** - Review conversations for quality and safety
4. **Update firmware via dashboard** - Ensures proper version tracking
5. **Use templates** - Create reusable agent personalities

## 🎯 Summary

The Vue.js dashboard is the **command center** of your Cheeko system:
- **Controls** how devices behave (through agents)
- **Manages** which AI services are used (through model config)
- **Monitors** system usage and conversations
- **Updates** device firmware
- **Secures** access through authentication

Without the dashboard tables in Railway MySQL, you would need to:
- Manually edit configuration files
- Use SQL commands to manage devices
- Have no visibility into conversations
- Cannot easily switch between AI providers
- Lose multi-user support

The dashboard transforms a complex technical system into a user-friendly management platform that non-technical users can operate.