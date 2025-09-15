# 🎯 Conversation & Langfuse Logs Enabled

## ✅ **All Conversation Flow Logs Successfully Enabled**

I've enabled comprehensive logging to track the entire conversation flow and identify exactly where Langfuse tracking might be failing.

### 📋 **Log Flow Overview**

Here's the complete log sequence you should see for a working conversation:

```
1. 🔌 NEW WEBSOCKET CONNECTION: ('192.168.1.77', 54321)
2. 📡 STARTING CONNECTION HANDLER: session=abc123-def456
3. 🎯 CONVERSATION STARTED: session=abc123-def456, text='Hello, how are you...'
4. 📝 SENDING TO LLM: session=abc123-def456, text='Hello, how are you...'
5. 🤖 LLM CHAT STARTED: session=abc123-def456, query='Hello...', tool_call=False, depth=0
6. [CRITICAL] REAL LLM CALL IMMINENT: session=abc123-def456, llm_type=<class...>, intent_type=function_call
7. [INFO] OpenAI LLM response call: session=abc123-def456, model=gpt-4
8. [INFO] Langfuse generation started: a4e9f4849cac67df
9. [INFO] Streaming response tracked: 15 chunks, 240 chars
10. 🔚 CONNECTION CLOSED: session=abc123-def456
```

### 🔍 **Enabled Log Categories**

#### **1. WebSocket Connection Logs**
- **File**: `core/websocket_server.py`
- **Shows**: New connections, connection handlers, disconnections
- **Examples**:
  ```
  🔌 NEW WEBSOCKET CONNECTION: ('192.168.1.77', 54321)
  📡 STARTING CONNECTION HANDLER: session=abc123-def456
  🔚 CONNECTION CLOSED: session=abc123-def456
  ```

#### **2. Conversation Start Logs**
- **File**: `core/handle/receiveAudioHandle.py`
- **Shows**: When a conversation is initiated from voice or text
- **Example**:
  ```
  🎯 CONVERSATION STARTED: session=abc123-def456, text='Hello, how are you today?...'
  ```

#### **3. LLM Routing Logs**
- **File**: `core/handle/receiveAudioHandle.py`
- **Shows**: When text is being sent to the LLM for processing
- **Example**:
  ```
  📝 SENDING TO LLM: session=abc123-def456, text='Hello, how are you today?...'
  ```

#### **4. LLM Chat Handler Logs**
- **File**: `core/connection.py`
- **Shows**: LLM chat processing start with detailed context
- **Example**:
  ```
  🤖 LLM CHAT STARTED: session=abc123-def456, query='Hello...', tool_call=False, depth=0
  ```

#### **5. Critical LLM Call Logs**
- **File**: `core/connection.py`
- **Shows**: Exactly when the real LLM provider is about to be called
- **Examples**:
  ```
  [CRITICAL] REAL LLM CALL IMMINENT: session=abc123-def456, llm_type=<class...>, intent_type=function_call
  [DEBUG] CALLING response_with_functions for session abc123-def456
  [DEBUG] CALLING response for session abc123-def456
  ```

#### **6. Langfuse Tracking Logs**
- **File**: `core/providers/llm/langfuse_wrapper.py`
- **Shows**: Langfuse decoration and tracking status
- **Examples**:
  ```
  [INFO] OpenAI LLM response call: session=abc123-def456, model=gpt-4
  [INFO] Langfuse generation started: a4e9f4849cac67df
  [INFO] Streaming response tracked: 15 chunks, 240 chars
  [INFO] LLM call tracked successfully
  ```

### 🐛 **Debugging Different Scenarios**

#### **No Logs at All**
If you see no conversation logs:
- Check if WebSocket connection is being established
- Look for: `🔌 NEW WEBSOCKET CONNECTION`
- If missing: Client connection issue

#### **Connection but No Conversation**
If you see connection but no conversation start:
- Look for: `🎯 CONVERSATION STARTED`
- If missing: Voice/text input not reaching conversation handler
- Check VAD, ASR logs for voice processing issues

#### **Conversation Starts but No LLM Call**
If you see conversation start but no LLM:
- Look for: `📝 SENDING TO LLM` and `🤖 LLM CHAT STARTED`
- If missing: Intent handling or routing issue

#### **LLM Call but No Langfuse**
If you see LLM call but no Langfuse tracking:
- Look for: `[INFO] OpenAI LLM response call` and `[INFO] Langfuse generation started`
- If missing: Langfuse wrapper not properly decorating the call

#### **Langfuse Starts but No Completion**
If you see generation start but no completion:
- Look for: `[INFO] Streaming response tracked` or `[INFO] LLM call tracked successfully`
- If missing: Streaming response processing issue

### 🧪 **Testing Your Setup**

#### **Option 1: Use the WebSocket Test**
```bash
python test_websocket_conversation.py
```

#### **Option 2: Connect with a Real Device**
Use your ESP32 device or web client to send voice/text

#### **Option 3: Monitor Logs in Real-time**
```bash
# Watch all conversation logs
tail -f server.log | grep -E "🔌|📡|🎯|📝|🤖|LANGFUSE|OpenAI"

# Watch only Langfuse logs
tail -f server.log | grep -i langfuse

# Watch only critical LLM calls
tail -f server.log | grep "REAL LLM CALL IMMINENT"
```

### 📊 **Log Analysis Commands**

```bash
# Check WebSocket connections today
grep "NEW WEBSOCKET CONNECTION" server.log | grep $(date +%y%m%d)

# Count successful conversations today  
grep "CONVERSATION STARTED" server.log | grep $(date +%y%m%d) | wc -l

# Check LLM call success rate
grep "LLM CHAT STARTED" server.log | wc -l
grep "Langfuse generation started" server.log | wc -l

# Find failed Langfuse calls
grep "LLM CHAT STARTED" server.log > /tmp/llm_calls.log
grep "Langfuse generation started" server.log > /tmp/langfuse_calls.log
diff /tmp/llm_calls.log /tmp/langfuse_calls.log
```

### 🎯 **What This Enables**

With these logs enabled, you can now:

1. **Track Complete Conversation Flow** - From WebSocket connection to LLM response
2. **Identify Langfuse Connection Points** - See exactly when Langfuse should activate
3. **Debug Missing Conversations** - Find where the flow breaks in the pipeline
4. **Monitor Real-time Activity** - See live conversation processing
5. **Analyze Success Rates** - Compare conversation starts vs Langfuse tracking

### ✅ **Next Steps**

1. **Start a conversation** through your device or test script
2. **Watch the logs** for the complete flow sequence above
3. **Identify where the chain breaks** if Langfuse tracking is missing
4. **Check specific error messages** around the failure point

The logs will now clearly show you exactly where the Langfuse integration is failing in your conversation pipeline!