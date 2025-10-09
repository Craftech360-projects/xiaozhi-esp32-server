# Mem0 Usage in LiveKit Server

## 🎯 What is Mem0?

**Mem0** is a cloud-based memory service that provides persistent, intelligent memory for AI agents. It allows the agent to remember conversations across multiple sessions.

**Official:** https://mem0.ai/

---

## 🔧 How Mem0 is Used in LiveKit

### **Purpose:**
1. **Remember child profile** across sessions
2. **Store conversation history** for context in future conversations
3. **Recall user preferences** and past interactions

---

## 📍 Implementation Details

### **1. Initialization (main.py:276-327)**

```python
# Check if mem0 is enabled
mem0_enabled = os.getenv("MEM0_ENABLED", "false").lower() == "true"

if device_mac and mem0_enabled:
    # Get API key
    mem0_api_key = os.getenv("MEM0_API_KEY")

    # Initialize mem0 provider
    mem0_provider = Mem0MemoryProvider(
        api_key=mem0_api_key,
        role_id=device_mac  # Use device MAC as unique user ID
    )
```

**Key Points:**
- Uses device MAC address as unique user ID (`role_id`)
- Each device has its own memory namespace
- Configuration via environment variables

---

### **2. Save Child Profile to Mem0 (main.py:294-305)**

```python
# Store child profile in mem0 for agent memory
if child_profile:
    child_info = {
        "role": "system",
        "content": f"Child Profile - Name: {child_profile.get('name')}, "
                   f"Age: {child_profile.get('age')}, "
                   f"Age Group: {child_profile.get('ageGroup')}, "
                   f"Gender: {child_profile.get('gender')}, "
                   f"Interests: {child_profile.get('interests')}"
    }

    # Save to mem0 as permanent memory
    await mem0_provider.save_memory({"messages": [child_info]})
    logger.info(f"👶💭 Child profile saved to mem0: {child_profile.get('name')}")
```

**Purpose:**
- Store child profile as a **permanent system message**
- Agent will remember child's name, age, interests across all sessions
- Even if device reconnects, agent knows who the child is

**Example Memory Stored:**
```
Child Profile - Name: Rahul, Age: 9, Age Group: Late Elementary, Gender: male, Interests: ["games", "sports", "science"]
```

---

### **3. Query Existing Memories (main.py:307-317)**

```python
# Fetch existing memories and inject into prompt
logger.info("💭 Querying mem0 for existing memories...")
memories = await mem0_provider.query_memory("conversation history and user preferences")

if memories:
    # Inject memories into agent prompt's <memory> section
    agent_prompt = agent_prompt.replace(
        "<memory>", f"<memory>\n{memories}")
    logger.info(f"💭✅ Loaded memories from mem0 ({len(memories)} chars)")
```

**Purpose:**
- Load **previous conversations** and **stored memories**
- Inject into agent prompt before session starts
- Agent has context of past interactions

**Example Memories Retrieved:**
```
<memory>
- [2025-10-09 10:30] Child Profile - Name: Rahul, Age: 9...
- [2025-10-08 15:45] User asked about dinosaurs
- [2025-10-07 11:20] User likes playing cricket
- [2025-10-06 16:10] User's favorite color is blue
</memory>
```

---

### **4. Capture Conversation During Session (main.py:410-433)**

```python
# Add mem0 conversation capture event handler
if mem0_provider:
    @session.on("conversation_item_added")
    def _on_mem0_conversation_item(ev):
        try:
            item = ev.item
            if hasattr(item, 'role') and hasattr(item, 'content'):
                role = item.role
                content = item.content

                # Extract text from content
                if isinstance(content, list):
                    content = ' '.join(str(c) for c in content)

                if role in ['user', 'assistant'] and content:
                    # Buffer message for later saving
                    conversation_messages.append({
                        'role': role,
                        'content': content
                    })
                    logger.debug(f"💭 Captured {role} message for mem0")
        except Exception as e:
            logger.error(f"💭 Failed to capture message: {e}")

    logger.info("💭 Mem0 conversation capture enabled")
```

**Purpose:**
- **Capture every message** during the conversation
- Store in buffer (`conversation_messages`)
- Will be saved when session ends

**Example Buffer:**
```python
conversation_messages = [
    {'role': 'user', 'content': 'Hi Cheeko!'},
    {'role': 'assistant', 'content': 'Hi Rahul! How are you today?'},
    {'role': 'user', 'content': 'Tell me about space'},
    {'role': 'assistant', 'content': 'Space is super cool! Let me tell you...'},
]
```

---

### **5. Save Conversation on Disconnect (main.py:519-554)**

```python
# Save conversation to mem0 cloud (using captured messages buffer)
if mem0_provider and conversation_messages:
    message_count = len(conversation_messages)

    logger.info(f"💭 Saving {message_count} messages to mem0 cloud")

    # Create history dict from conversation buffer
    history_dict = {'messages': conversation_messages}

    # Save to mem0
    await mem0_provider.save_memory(history_dict)

    logger.info(f"💭✅ Session saved to mem0 cloud ({message_count} messages)")
```

**Purpose:**
- When device disconnects, **save entire conversation** to mem0
- Mem0 will intelligently extract:
  - Important facts
  - User preferences
  - Topics discussed
  - Key information

**What Mem0 Stores:**
```
[2025-10-09 14:30] User Rahul asked about space and dinosaurs
[2025-10-09 14:35] User expressed interest in science experiments
[2025-10-09 14:40] User's favorite subject is science
```

---

## 🔄 Complete Workflow

```
┌────────────────────────────────────────────────────────────┐
│ Session Start (Device Connects)                           │
└────────────┬───────────────────────────────────────────────┘
             │
             ▼
┌────────────────────────────────────────────────────────────┐
│ 1. Initialize Mem0                                         │
│    - Create Mem0MemoryProvider with device MAC            │
│    - Use MAC as unique user ID                             │
└────────────┬───────────────────────────────────────────────┘
             │
             ▼
┌────────────────────────────────────────────────────────────┐
│ 2. Save Child Profile to Mem0                             │
│    - Store: Name, Age, Interests                           │
│    - As system message (permanent memory)                  │
└────────────┬───────────────────────────────────────────────┘
             │
             ▼
┌────────────────────────────────────────────────────────────┐
│ 3. Query Mem0 for Existing Memories                       │
│    - Fetch previous conversations                          │
│    - Get stored preferences                                │
│    - Retrieve child profile from previous session          │
└────────────┬───────────────────────────────────────────────┘
             │
             ▼
┌────────────────────────────────────────────────────────────┐
│ 4. Inject Memories into Agent Prompt                      │
│    - Replace <memory> tag with actual memories             │
│    - Agent now has context of past interactions            │
└────────────┬───────────────────────────────────────────────┘
             │
             ▼
┌────────────────────────────────────────────────────────────┐
│ 5. During Conversation                                     │
│    - Capture each message (user + assistant)               │
│    - Store in buffer (conversation_messages)               │
└────────────┬───────────────────────────────────────────────┘
             │
             ▼
┌────────────────────────────────────────────────────────────┐
│ Session End (Device Disconnects)                          │
└────────────┬───────────────────────────────────────────────┘
             │
             ▼
┌────────────────────────────────────────────────────────────┐
│ 6. Save Conversation to Mem0                              │
│    - Upload buffered messages to mem0 cloud                │
│    - Mem0 extracts important information                   │
│    - Stores as searchable memories                         │
└────────────────────────────────────────────────────────────┘
```

---

## 🎯 Benefits

### **1. Persistent Memory**
- Agent remembers child across sessions
- No need to re-introduce yourself

### **2. Contextual Conversations**
- Agent knows past topics discussed
- Can reference previous conversations
- Builds continuity

### **3. Personalization**
- Remembers child's preferences
- Adapts to child's interests
- Tailors responses based on history

### **4. Intelligence**
- Mem0 intelligently extracts key information
- Not just raw text storage
- Semantic search capabilities

---

## 📊 Example Scenario

### **Session 1 (First Time):**
```
User: Hi!
Agent: Hi friend! How can I help you today?
User: My name is Rahul
Agent: Nice to meet you, Rahul!
User: I like dinosaurs
Agent: Dinosaurs are awesome! Let me tell you about T-Rex...

[Session ends - Mem0 stores:]
- Child's name is Rahul
- Interested in dinosaurs
```

### **Session 2 (Next Day):**
```
[Agent loads memories from Mem0]
[Prompt now contains: "Child's name is Rahul, interested in dinosaurs"]

User: Hi!
Agent: Hi Rahul! Want to hear more about dinosaurs today?
         ↑ Remembers name!
User: Yes! Tell me about velociraptors
Agent: Great choice! Remember we talked about T-Rex yesterday?
                    ↑ Remembers previous conversation!
```

---

## ⚙️ Configuration

### **Environment Variables (.env):**

```bash
# Enable mem0
MEM0_ENABLED=true

# Mem0 API key (get from https://mem0.ai/)
MEM0_API_KEY=your_mem0_api_key_here
```

### **To Get Mem0 API Key:**
1. Go to https://mem0.ai/
2. Sign up for an account
3. Get your API key from dashboard
4. Add to `.env` file

---

## 🔍 Mem0 Provider Class

**Location:** `src/memory/mem0_provider.py`

### **Methods:**

#### **1. `__init__(api_key, role_id)`**
Initialize mem0 client with API key and user ID

#### **2. `save_memory(history_dict)`**
Save conversation history to mem0
- Input: `{'messages': [{'role': 'user', 'content': '...'}, ...]}`
- Converts to text format
- Uploads to mem0 cloud
- Returns save result

#### **3. `query_memory(query)`**
Query memories from mem0
- Input: Search query string
- Returns: Formatted memory string with timestamps
- Example output:
  ```
  - [2025-10-09 10:30] Child's name is Rahul
  - [2025-10-08 15:45] Likes dinosaurs
  ```

---

## 📈 Memory Flow Diagram

```
┌─────────────┐
│   Device    │
│ MAC: aa:bb  │
└──────┬──────┘
       │ Connects
       ▼
┌─────────────────────────┐
│   LiveKit Server        │
│                         │
│  1. Check mem0_enabled  │
│  2. Init Mem0Provider   │
│     - role_id: aa:bb    │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│         Mem0 Cloud                  │
│                                     │
│  User: aa:bb (device MAC)           │
│  ├─ Memory 1: Child name is Rahul   │
│  ├─ Memory 2: Age 9, likes games    │
│  ├─ Memory 3: Asked about space     │
│  └─ Memory 4: Favorite color blue   │
└─────────────────────────────────────┘
       ▲                    │
       │ Save               │ Query
       │                    ▼
┌─────────────────────────────────────┐
│   Agent Conversation                │
│                                     │
│  - Loads memories at start          │
│  - Has full context                 │
│  - Captures new messages            │
│  - Saves on disconnect              │
└─────────────────────────────────────┘
```

---

## ✅ Summary

**Mem0 in LiveKit provides:**

1. ✅ **Persistent memory** across sessions
2. ✅ **Child profile storage** (name, age, interests)
3. ✅ **Conversation history** retrieval
4. ✅ **Intelligent memory** extraction
5. ✅ **Contextual awareness** for agent
6. ✅ **Personalized experiences** for each child

**Without Mem0:**
- Agent forgets everything after disconnect
- No context from previous sessions
- User must re-introduce themselves

**With Mem0:**
- Agent remembers child's name and preferences
- Continues conversations naturally
- Builds long-term relationship

---

**Created:** 2025-10-09
**Status:** ✅ Fully Implemented
**Configuration:** `.env` - `MEM0_ENABLED=true`, `MEM0_API_KEY=xxx`
