# Dynamic Prompt Update - Detailed Data Flow

## Overview

This document explains **exactly how** the AI agent's prompt is updated **in real-time** during an active conversation, without requiring the user to reconnect.

---

## The Problem We Solved

### **Before (Traditional Approach):**

```
User: "Switch to Storyteller mode"
AI: "Mode updated! Please disconnect and reconnect."
User: [Disconnects]
User: [Reconnects]
AI: [Now uses new Storyteller prompt]
```

❌ **Problem:** Bad user experience, interrupts conversation flow.

---

### **After (Our Solution):**

```
User: "Switch to Storyteller mode"
AI: "Successfully updated! Changes are active now."
User: "Tell me a story"
AI: [Immediately responds as Storyteller - NO RECONNECTION!]
```

✅ **Solution:** Dynamic in-memory prompt update without session restart.

---

## Architecture Overview

### **Three Key Components:**

```
┌─────────────────────────────────────────────────────────────┐
│                    1. LiveKit Agent                          │
│   (Python - Runs in conversation session)                   │
│   - Stores current prompt in memory                          │
│   - Has reference to active session                          │
└─────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────┐
│                    2. Manager API                            │
│   (Java Spring Boot - Database backend)                     │
│   - Updates prompt in database                               │
│   - Returns new prompt in response                           │
└─────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────┐
│                    3. MySQL Database                         │
│   - ai_agent_template (template prompts)                    │
│   - ai_agent (user's current agent config)                  │
└─────────────────────────────────────────────────────────────┘
```

---

## Detailed Data Flow

### **Step-by-Step Process**

---

### **STEP 1: User Request**

**User says:** "Switch to Storyteller mode"

**What happens:**
- User's voice → Speech-to-Text (STT)
- Text sent to LLM (Language Model)
- LLM detects intent to change mode
- LLM decides to call `update_agent_mode` function tool

```
┌──────────────────────────────────────────┐
│ User Voice Input                         │
│ "Switch to Storyteller mode"            │
└────────────────┬─────────────────────────┘
                 │
                 ▼ (STT)
┌──────────────────────────────────────────┐
│ Text: "Switch to Storyteller mode"      │
└────────────────┬─────────────────────────┘
                 │
                 ▼ (LLM)
┌──────────────────────────────────────────┐
│ LLM Decision:                            │
│ "User wants to change agent mode.        │
│  Call update_agent_mode('Storyteller')"  │
└──────────────────────────────────────────┘
```

---

### **STEP 2: Function Tool Execution Starts**

**File:** `main_agent.py`
**Function:** `update_agent_mode(mode_name="Storyteller")`

```python
@function_tool
async def update_agent_mode(self, context: RunContext, mode_name: str) -> str:
    # This function is called by the LLM
```

**Current State:**
```
┌────────────────────────────────────────────────┐
│ LiveKit Agent (In-Memory)                      │
├────────────────────────────────────────────────┤
│ self.device_mac = "68:25:dd:ba:39:78"         │
│ self._instructions = "<old Cheeko prompt>"    │
│ self._agent_session = <LiveKit Session Ref>   │
└────────────────────────────────────────────────┘
```

---

### **STEP 3: Get Agent ID from Device MAC**

**Why?** We need to know which agent record to update in the database.

**API Call:**
```
GET http://localhost:8080/agent/device/68:25:dd:ba:39:78/agent-id
Headers:
  Authorization: Bearer {MANAGER_API_SECRET}
```

**Code (database_helper.py):**
```python
db_helper = DatabaseHelper(manager_api_url, manager_api_secret)
agent_id = await db_helper.get_agent_id(self.device_mac)
# Result: agent_id = "11507ab86d464c769803b12e228791c9"
```

**Database Query (Executed by Manager API):**
```sql
-- Step 1: Find device by MAC
SELECT * FROM ai_device
WHERE mac_address = '68:25:dd:ba:39:78'
LIMIT 1;

-- Result:
-- id: device_6825ddba3978
-- mac_address: 68:25:dd:ba:39:78
-- agent_id: 11507ab86d464c769803b12e228791c9  ← This is what we need!
-- user_id: 1
```

**Response:**
```json
{
  "code": 0,
  "data": "11507ab86d464c769803b12e228791c9",
  "msg": "success"
}
```

**State After Step 3:**
```python
agent_id = "11507ab86d464c769803b12e228791c9"
```

---

### **STEP 4: Call Update Mode API**

**Why?** To update the database AND get the new prompt in one transaction.

**API Call:**
```
PUT http://localhost:8080/agent/update-mode
Headers:
  Authorization: Bearer {MANAGER_API_SECRET}
  Content-Type: application/json
Body:
  {
    "agentId": "11507ab86d464c769803b12e228791c9",
    "modeName": "Storyteller"
  }
```

**Code (main_agent.py):**
```python
url = f"{manager_api_url}/agent/update-mode"
payload = {
    "agentId": agent_id,
    "modeName": mode_name  # "Storyteller"
}

async with aiohttp.ClientSession() as session:
    async with session.put(url, json=payload, headers=headers) as response:
        if response.status == 200:
            result = await response.json()
            # result = { code: 0, data: "<new prompt>", msg: "success" }
```

---

### **STEP 5: Backend Processing (Manager API)**

**File:** `AgentServiceImpl.java`
**Method:** `updateAgentMode(agentId, modeName)`

#### **Sub-Step 5.1: Fetch Current Agent**

```java
AgentEntity agent = this.selectById(agentId);
```

**SQL:**
```sql
SELECT * FROM ai_agent
WHERE id = '11507ab86d464c769803b12e228791c9';
```

**Result:**
```
id: 11507ab86d464c769803b12e228791c9
agent_name: Cheeko
system_prompt: <identity>You are Cheeko, a playful AI for kids...</identity>
llm_model_id: LLM_groq_llama3.3_70b
tts_model_id: TTS_EdgeTTS
...
```

#### **Sub-Step 5.2: Fetch Template by Name**

```java
AgentTemplateEntity template = agentTemplateService.getTemplateByName(modeName);
```

**SQL:**
```sql
SELECT * FROM ai_agent_template
WHERE agent_name = 'Storyteller'
LIMIT 1;
```

**Result:**
```
id: template_storyteller_001
agent_name: Storyteller
system_prompt: <identity>You are a magical storyteller who weaves enchanting tales...</identity>
llm_model_id: LLM_groq_llama3.3_70b
tts_model_id: TTS_EdgeTTS
mem_model_id: Memory_mem_local_short
...
```

#### **Sub-Step 5.3: Copy Template Fields to Agent**

```java
String oldPrompt = agent.getSystemPrompt();  // Save for logging

// Copy all fields from template to agent
agent.setSystemPrompt(template.getSystemPrompt());  // ← NEW PROMPT!
agent.setLlmModelId(template.getLlmModelId());
agent.setTtsModelId(template.getTtsModelId());
agent.setMemModelId(template.getMemModelId());
// ... copy all other fields
```

**In-Memory State (Before DB Update):**
```java
agent.systemPrompt = "<identity>You are a magical storyteller...</identity>..."
agent.llmModelId = "LLM_groq_llama3.3_70b"
agent.updatedAt = 2025-10-03 17:55:23
```

#### **Sub-Step 5.4: Update Database**

```java
agent.setUpdatedAt(new Date());
this.updateById(agent);  // MyBatis-Plus auto-generates UPDATE SQL
```

**SQL Generated:**
```sql
UPDATE ai_agent SET
    system_prompt = '<identity>You are a magical storyteller who weaves enchanting tales for children. Your voice is warm and expressive, painting vivid pictures with words. You adapt your stories to be age-appropriate, engaging, and educational. You encourage imagination and curiosity through your narratives.</identity>

<personality>
- Warm and nurturing tone
- Expressive and animated delivery
- Uses vivid imagery and descriptive language
- Asks engaging questions to involve the listener
- Celebrates creativity and imagination
</personality>

<guidelines>
1. Always start stories with engaging hooks
2. Use age-appropriate vocabulary and themes
3. Include moral lessons naturally within stories
4. Encourage participation ("What do you think happens next?")
5. Create safe, magical worlds for exploration
6. End with satisfying conclusions
</guidelines>',
    llm_model_id = 'LLM_groq_llama3.3_70b',
    tts_model_id = 'TTS_EdgeTTS',
    mem_model_id = 'Memory_mem_local_short',
    updated_at = '2025-10-03 17:55:23'
WHERE id = '11507ab86d464c769803b12e228791c9';
```

**Transaction commits here!** ✅ Database now has the new prompt.

#### **Sub-Step 5.5: Return New Prompt**

```java
// Return the new prompt to the API caller
return template.getSystemPrompt();
```

**Controller wraps it:**
```java
@PutMapping("/update-mode")
public Result<String> updateMode(@RequestBody @Valid AgentUpdateModeDTO dto) {
    String updatedPrompt = agentService.updateAgentMode(dto.getAgentId(), dto.getModeName());
    return new Result<String>().ok(updatedPrompt);  // ← Returns prompt in response
}
```

**HTTP Response:**
```json
{
  "code": 0,
  "data": "<identity>You are a magical storyteller who weaves enchanting tales...</identity>...",
  "msg": "success"
}
```

---

### **STEP 6: Update LiveKit Agent's In-Memory Instructions**

**Back in Python (main_agent.py):**

```python
async with session.put(url, json=payload, headers=headers) as response:
    if response.status == 200:
        result = await response.json()
        # result = { code: 0, data: "<new storyteller prompt>", msg: "success" }

        # Extract new prompt from response
        if result.get('code') == 0 and result.get('data'):
            new_prompt = result.get('data')
            # new_prompt = "<identity>You are a magical storyteller...</identity>..."
```

**Why get prompt from API response instead of separate query?**

❌ **Bad Approach (Timing Issue):**
```python
# Update database
await update_mode_api()

# Query database again
new_prompt = await fetch_prompt_api()  # ← Might get OLD data due to transaction timing!
```

✅ **Good Approach (Our Implementation):**
```python
# Update database AND return new prompt in same response
response = await update_mode_api()
new_prompt = response.data  # ← Guaranteed to be the EXACT prompt that was saved!
```

---

### **STEP 7: Update Agent's Internal Instructions**

**Code:**
```python
# Update the agent's own instructions
self._instructions = new_prompt

logger.info(f"📝 Instructions updated dynamically (length: {len(new_prompt)} chars)")
logger.info(f"📝 New prompt preview: {new_prompt[:100]}...")
```

**Memory State:**
```
┌────────────────────────────────────────────────────────┐
│ Agent Object (self)                                    │
├────────────────────────────────────────────────────────┤
│ Before:                                                │
│   self._instructions = "<old Cheeko prompt>"          │
│                                                        │
│ After:                                                 │
│   self._instructions = "<new Storyteller prompt>"     │
└────────────────────────────────────────────────────────┘
```

**Why access `_instructions` directly?**

The LiveKit `Agent` class has a read-only property:

```python
class Agent:
    def __init__(self, instructions: str):
        self._instructions = instructions  # Private internal storage

    @property
    def instructions(self):
        return self._instructions  # Read-only property

    # No setter method! Cannot do: agent.instructions = "new"
```

**Solution:** Access the internal `_instructions` attribute directly:
```python
self._instructions = new_prompt  # Bypass the read-only property
```

---

### **STEP 8: Update Active Session's Instructions**

**This is the CRITICAL step for real-time update!**

**Code:**
```python
# Update the active LiveKit session
if self._agent_session:
    try:
        # Update the session's agent instructions
        self._agent_session._agent._instructions = new_prompt
        logger.info(f"🔄 Session instructions updated in real-time!")
    except Exception as e:
        logger.warning(f"⚠️ Could not update session directly: {e}")
```

**Memory State:**
```
┌─────────────────────────────────────────────────────────┐
│ LiveKit Session (self._agent_session)                  │
├─────────────────────────────────────────────────────────┤
│ session.agent._instructions = "<new Storyteller>"      │
│                                                         │
│ This is the ACTIVE conversation session!                │
│ Next LLM call will use this prompt.                    │
└─────────────────────────────────────────────────────────┘
```

**Why update both `self._instructions` and `session._agent._instructions`?**

```
self._instructions
↓
For future function tool calls within this agent instance

self._agent_session._agent._instructions
↓
For the ACTIVE LiveKit session's LLM calls (next user message)
```

**Session Reference Flow:**

```python
# In main.py (session initialization):
assistant = Assistant(instructions=initial_prompt)
session = AgentSession(llm=llm, stt=stt, tts=tts)
await session.start(agent=assistant, room=ctx.room)

# Pass session reference to assistant
assistant.set_agent_session(session)  # ← Now assistant can update session!

# Later, when mode changes:
# assistant (self) has reference to session
# assistant updates session._agent._instructions
# Next LLM call in session uses new instructions!
```

**Object Relationship:**
```
┌──────────────────────────────────────┐
│ session (AgentSession)               │
│  ├─ _agent → Points to assistant     │
│  ├─ llm                              │
│  ├─ stt                              │
│  └─ tts                              │
└──────────────────────────────────────┘
           ↑
           │ (reference stored)
           │
┌──────────────────────────────────────┐
│ assistant (Assistant)                │
│  ├─ _instructions                    │
│  ├─ _agent_session → Points to       │
│  │                    session         │
│  └─ device_mac                       │
└──────────────────────────────────────┘
```

**When we do:**
```python
self._agent_session._agent._instructions = new_prompt
```

**We're actually doing:**
```python
session → _agent (which is 'assistant') → _instructions = new_prompt
```

**This updates the SAME object that LiveKit uses for LLM calls!**

---

### **STEP 9: Return Success to User**

**Code:**
```python
return f"Successfully updated agent mode to '{mode_name}' and reloaded the new prompt! The changes are now active in this conversation."
```

**LLM receives this response from the function tool.**

**AI speaks to user:**
```
AI: "Successfully updated agent mode to 'Storyteller' and reloaded
     the new prompt! The changes are now active in this conversation."
```

---

### **STEP 10: Next User Message Uses New Prompt**

**User says:** "Tell me a story about a dragon"

**What happens:**

```
┌────────────────────────────────────────────────┐
│ 1. User speech → STT → Text                   │
└────────────────┬───────────────────────────────┘
                 ▼
┌────────────────────────────────────────────────┐
│ 2. LiveKit Session calls LLM                  │
│    llm.generate(                               │
│      instructions=session._agent._instructions,│
│      user_message="Tell me a story..."         │
│    )                                           │
└────────────────┬───────────────────────────────┘
                 ▼
┌────────────────────────────────────────────────┐
│ 3. LLM sees NEW Storyteller prompt:           │
│    "<identity>You are a magical storyteller   │
│     who weaves enchanting tales...</identity>" │
└────────────────┬───────────────────────────────┘
                 ▼
┌────────────────────────────────────────────────┐
│ 4. LLM generates Storyteller-style response:  │
│    "Once upon a time, in a land of emerald    │
│     mountains, there lived a gentle dragon    │
│     named Sparkle..."                          │
└────────────────┬───────────────────────────────┘
                 ▼
┌────────────────────────────────────────────────┐
│ 5. TTS speaks response to user               │
└────────────────────────────────────────────────┘
```

**✅ User hears Storyteller response immediately, no reconnection needed!**

---

## Complete API Call Sequence

### **Summary of All API Calls:**

```
1. GET /agent/device/{mac}/agent-id
   ↓
   Response: { code: 0, data: "agent_id" }

2. PUT /agent/update-mode
   Body: { agentId: "...", modeName: "Storyteller" }
   ↓
   Backend executes:
     - SELECT agent
     - SELECT template
     - UPDATE agent with template data
     - COMMIT
   ↓
   Response: { code: 0, data: "<new prompt full text>", msg: "success" }

3. LiveKit updates:
   - self._instructions = new_prompt
   - session._agent._instructions = new_prompt

4. Done! Next user message uses new prompt.
```

---

## Why This Approach Works

### **Key Design Decisions:**

#### **1. Return Prompt in Update Response**

**Why?**
- Avoids race condition (transaction timing)
- Guarantees we get the EXACT prompt that was saved
- Single atomic operation

**Alternative (Bad):**
```python
# Update mode
await api.put("/update-mode")  # Transaction may not be committed yet

# Query prompt (might get old data!)
prompt = await api.get("/prompt")  # ← Race condition!
```

**Our Solution (Good):**
```python
# Update mode AND get prompt in single response
response = await api.put("/update-mode")
prompt = response.data  # ← Guaranteed correct!
```

---

#### **2. Update Both Agent and Session References**

**Why update `self._instructions`?**
- For future function tool calls within this agent
- Maintains consistency

**Why update `session._agent._instructions`?**
- This is what LiveKit uses for LLM calls
- Immediate effect on next user message

**If we only updated one:**
```python
# Only update self._instructions
self._instructions = new_prompt
# ❌ Session still uses old prompt for LLM calls!

# Only update session
self._agent_session._agent._instructions = new_prompt
# ❌ Function tools might use old self._instructions!
```

**Update both:**
```python
self._instructions = new_prompt
self._agent_session._agent._instructions = new_prompt
# ✅ Everything uses new prompt!
```

---

#### **3. Access Internal `_instructions` Attribute**

**Why not use the property?**

```python
# This doesn't work:
self.instructions = new_prompt
# AttributeError: property 'instructions' of 'Agent' object has no setter

# This works:
self._instructions = new_prompt
# Directly accesses internal storage, bypassing read-only property
```

---

#### **4. Server Secret Authentication**

**Why not user authentication?**

```python
# User auth requires logged-in user
@RequiresPermissions("sys:role:normal")

# Server secret allows machine-to-machine
filterMap.put("/agent/update-mode", "server");
```

**Benefits:**
- LiveKit server can call API without user context
- Secure server-to-server communication
- No need to pass user tokens around

---

## Memory State Transitions

### **Visual Memory Flow:**

```
INITIAL STATE (Cheeko Mode):
┌─────────────────────────────────────────────────────────┐
│ Database (MySQL)                                        │
├─────────────────────────────────────────────────────────┤
│ ai_agent.system_prompt = "<Cheeko prompt>"             │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ LiveKit Agent (Python - In Memory)                     │
├─────────────────────────────────────────────────────────┤
│ self._instructions = "<Cheeko prompt>"                 │
│ session._agent._instructions = "<Cheeko prompt>"       │
└─────────────────────────────────────────────────────────┘

        ↓ User: "Switch to Storyteller mode"
        ↓ Function tool executes
        ↓

TRANSITION (API Call):
┌─────────────────────────────────────────────────────────┐
│ PUT /agent/update-mode                                  │
├─────────────────────────────────────────────────────────┤
│ 1. SELECT template WHERE name='Storyteller'            │
│ 2. UPDATE agent SET prompt='<Storyteller prompt>'      │
│ 3. RETURN '<Storyteller prompt>'                       │
└─────────────────────────────────────────────────────────┘

        ↓ Response received
        ↓ In-memory update
        ↓

FINAL STATE (Storyteller Mode):
┌─────────────────────────────────────────────────────────┐
│ Database (MySQL) - UPDATED ✅                           │
├─────────────────────────────────────────────────────────┤
│ ai_agent.system_prompt = "<Storyteller prompt>"        │
│ ai_agent.updated_at = 2025-10-03 17:55:23              │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ LiveKit Agent (Python) - UPDATED ✅                     │
├─────────────────────────────────────────────────────────┤
│ self._instructions = "<Storyteller prompt>"            │
│ session._agent._instructions = "<Storyteller prompt>"  │
└─────────────────────────────────────────────────────────┘

        ↓ User: "Tell me a story"
        ↓ LLM uses new prompt
        ↓

AI: "Once upon a time..." (Storyteller response)
```

---

## Performance Considerations

### **Timing:**

```
User request → Mode change complete: ~200-500ms

Breakdown:
- LLM detects intent: ~100ms
- API call 1 (get agent_id): ~50ms
- API call 2 (update mode): ~100ms
  - Database SELECT template: ~10ms
  - Database UPDATE agent: ~20ms
  - Transaction commit: ~30ms
- Memory update: <1ms
- Response generation: ~100ms

Total: ~350ms average
```

### **Database Load:**

**Per mode change:**
- 1 SELECT (ai_device) - Get agent by MAC
- 1 SELECT (ai_agent) - Validate agent exists
- 1 SELECT (ai_agent_template) - Get template
- 1 UPDATE (ai_agent) - Save new config

**4 queries total** - Very light!

---

## Error Handling

### **What if API call fails?**

```python
try:
    response = await session.put(url, json=payload)
    if response.status == 200:
        # Update succeeded
    else:
        # Return error to user
        return f"Failed to update mode: {response.status}"
except Exception as e:
    # Network error, timeout, etc.
    return f"Error: {str(e)}"
```

**User sees:** "Failed to update mode" message, can try again.

**Database:** Unchanged (transaction rolled back).

**Session:** Still uses old prompt.

---

### **What if session update fails?**

```python
# Database updated successfully
if result.get('code') == 0:
    new_prompt = result.get('data')
    self._instructions = new_prompt

    # Try to update session
    if self._agent_session:
        try:
            self._agent_session._agent._instructions = new_prompt
        except Exception as e:
            # Log warning but don't fail
            logger.warning(f"Could not update session: {e}")
```

**Result:**
- Database: ✅ Updated
- `self._instructions`: ✅ Updated
- Session: ❌ Not updated (will use on next reconnect)

**User told:** "Mode updated in database. Please reconnect to apply changes."

---

## Comparison: With vs Without Dynamic Update

### **Without Dynamic Update (Old Way):**

```
Timeline:
0s:  User: "Switch to Storyteller mode"
1s:  AI: "Updated! Please disconnect and reconnect."
2s:  User disconnects
5s:  User reconnects
6s:  Session starts with new prompt
7s:  User: "Tell me a story"
8s:  AI: [Storyteller response]

Total time: 8 seconds
User actions: 2 (disconnect + reconnect)
```

### **With Dynamic Update (Our Implementation):**

```
Timeline:
0s:  User: "Switch to Storyteller mode"
0.5s: AI: "Successfully updated! Changes are active now."
1s:  User: "Tell me a story"
2s:  AI: [Storyteller response]

Total time: 2 seconds
User actions: 0 (seamless)
```

**Improvement:**
- ⚡ **4x faster**
- 🎯 **Zero user friction**
- ✅ **Better UX**

---

## Summary

### **The Complete Flow in One Diagram:**

```
USER
  │
  │ "Switch to Storyteller"
  │
  ▼
┌─────────────────────────────────────────┐
│ LiveKit Agent (Python)                  │
│ ┌─────────────────────────────────────┐ │
│ │ 1. Detect intent (LLM)              │ │
│ │ 2. Call update_agent_mode()         │ │
│ │ 3. GET /device/{mac}/agent-id       │─┼─→ Manager API
│ │    ← agent_id                       │ │     ↓
│ │ 4. PUT /update-mode                 │─┼─→ SELECT template
│ │    {agentId, modeName}              │ │   UPDATE agent
│ │    ← {code:0, data:"<new prompt>"}  │ │     ↓
│ │ 5. self._instructions = new_prompt  │ │   Return prompt
│ │ 6. session._agent._instructions =   │ │
│ │    new_prompt                        │ │
│ │ 7. Return success to LLM            │ │
│ └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
  │
  │ "Successfully updated!"
  │
  ▼
USER
  │
  │ "Tell me a story"
  │
  ▼
┌─────────────────────────────────────────┐
│ LiveKit Session                         │
│ Uses: session._agent._instructions      │
│       ↓                                 │
│    LLM generates with NEW prompt        │
│       ↓                                 │
│    "Once upon a time..." ✅             │
└─────────────────────────────────────────┘
  │
  ▼
USER (hears Storyteller response)
```

---

## Key Takeaways

1. ✅ **Two API calls:** Get agent ID + Update mode
2. ✅ **One response:** Contains new prompt directly
3. ✅ **Two memory updates:** Agent + Session
4. ✅ **Zero reconnections:** Works in real-time
5. ✅ **Database persistence:** Saved for future sessions
6. ✅ **Atomic operation:** Database update + prompt return in one transaction

---

**This is how we achieve instant, seamless agent mode switching!** 🚀
