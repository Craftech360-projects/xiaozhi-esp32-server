# Langfuse Logging Enabled - Debug Guide

## ✅ **Langfuse Logs Successfully Enabled**

The following logs have been enabled to help track and debug Langfuse connection issues:

### 🔍 **Enabled Log Categories**

#### **1. Langfuse Client Initialization**
- **Location**: `config/langfuse_config.py`
- **Shows**: Host, debug mode, connection status
- **Example**: 
  ```
  [INFO] Langfuse client initialized - Host: https://cloud.langfuse.com, Debug: False (connection will be tested on first use)
  ```

#### **2. Langfuse Wrapper Loading**
- **Location**: `core/providers/llm/langfuse_wrapper.py`
- **Shows**: Module loading and tracker initialization
- **Example**:
  ```
  [INFO] Langfuse wrapper loaded: core.providers.llm.langfuse_wrapper
  [INFO] Langfuse tracker initialized - Enabled: True
  ```

#### **3. LLM Provider Call Tracking**
- **Location**: `core/providers/llm/openai/openai.py`
- **Shows**: Every LLM API call with session and model details
- **Examples**:
  ```
  [INFO] OpenAI LLM response call: session=abc123, model=gpt-4
  [INFO] OpenAI function call: session=abc123, model=gpt-4, functions=2
  ```

#### **4. Langfuse Generation Tracking**
- **Location**: `core/providers/llm/langfuse_wrapper.py`
- **Shows**: When Langfuse starts tracking each API call
- **Examples**:
  ```
  [INFO] Langfuse generation started: a4e9f4849cac67df
  [INFO] Langfuse function generation started: f8e623d8345aa5c5
  ```

#### **5. Tracking Status Messages**
- **Location**: `core/providers/llm/langfuse_wrapper.py`
- **Shows**: When tracking is disabled or skipped
- **Examples**:
  ```
  [INFO] Langfuse tracking disabled - skipping openai
  [INFO] Langfuse function tracking disabled - skipping openai
  ```

### 📊 **Log Filtering Configuration**

The logger has been configured to:
- ✅ **Always allow** Langfuse-related debug messages (override normal DEBUG filtering)
- ✅ **Allow** LLM provider debug logs for API tracking
- ✅ **Promote** key Langfuse debug messages to INFO level for visibility
- ❌ **Still filter** repetitive VAD/ASR messages to reduce noise

### 🔧 **What Was Modified**

#### **1. Logger Filter (`config/logger.py`)**
```python
# ALWAYS allow Langfuse-related debug messages to pass through
if "langfuse" in tag.lower() or "langfuse" in message.lower():
    return record["message"]

# ALSO allow LLM provider debug logs for tracking API calls
if "llm" in tag.lower() and any(phrase in message.lower() for phrase in [
    "tracking", "generation", "response", "openai", "decorator", "api"
]):
    return record["message"]
```

#### **2. Langfuse Wrapper (`core/providers/llm/langfuse_wrapper.py`)**
- Promoted key debug messages to INFO level
- Enhanced connection status logging
- Better generation ID tracking

#### **3. Langfuse Config (`config/langfuse_config.py`)**
- Added host and debug mode to initialization logs
- Better connection status reporting

#### **4. OpenAI Provider (`core/providers/llm/openai/openai.py`)**
- Promoted API call logs to INFO level
- Enhanced session and model tracking

### 🐛 **How to Debug Langfuse Issues**

#### **1. Check Initialization**
Look for these logs during startup:
```bash
grep "Langfuse client initialized" server.log
grep "Langfuse tracker initialized" server.log
```

#### **2. Check API Call Tracking**
Look for these logs during LLM calls:
```bash
grep "OpenAI LLM response call" server.log
grep "Langfuse generation started" server.log
```

#### **3. Check for Connection Issues**
Look for error messages:
```bash
grep -i "langfuse.*error" server.log
grep -i "authentication.*failed" server.log
```

#### **4. Check Streaming Response Tracking**
Look for completion messages:
```bash
grep "Streaming response tracked" server.log
grep "Function streaming tracked" server.log
```

### 📋 **Common Troubleshooting**

#### **If you see "Langfuse tracking disabled"**
- Check environment variables: `LANGFUSE_SECRET_KEY`, `LANGFUSE_PUBLIC_KEY`
- Verify the keys are correct in your `.env` file

#### **If you see "Langfuse generation started" but no completion**
- Check network connectivity to Langfuse servers
- Look for error messages in the streaming response tracking

#### **If no Langfuse logs appear at all**
- Check log level is set to INFO or lower
- Verify the logging configuration loaded correctly

### 🎯 **Expected Log Flow for a Working Call**

1. **Initialization** (on startup):
   ```
   Langfuse client initialized - Host: https://cloud.langfuse.com, Debug: False
   Langfuse wrapper loaded: core.providers.llm.langfuse_wrapper
   Langfuse tracker initialized - Enabled: True
   ```

2. **API Call** (during conversation):
   ```
   OpenAI LLM response call: session=abc123, model=gpt-4
   Langfuse generation started: a4e9f4849cac67df
   Streaming response tracked: 15 chunks, 240 chars
   LLM call tracked successfully
   ```

### 🔍 **Real-time Monitoring**

To monitor logs in real-time:
```bash
# Watch all Langfuse-related logs
tail -f server.log | grep -i langfuse

# Watch LLM API calls
tail -f server.log | grep "OpenAI LLM response call"

# Watch for errors
tail -f server.log | grep -i error | grep -i langfuse
```

## ✅ **Status: Langfuse Logging Fully Enabled**

All necessary logs have been enabled to track Langfuse connection and tracking issues. You should now have full visibility into:
- Client initialization and configuration
- API call tracking and generation creation
- Streaming response processing
- Error conditions and connection issues

The logs will help identify exactly where the Langfuse integration might be failing in your production environment.