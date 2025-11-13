# Whisper Model Reloading Issue - Debugging Guide

## 🔴 Problem
Whisper model is being loaded **every time** a user speaks, causing:
- ⏱️ **19 second delay** before transcription
- 🔥 **100% CPU usage** during loading
- 💾 **Memory spikes** (5769MB → 2391MB → 967MB)
- 😞 **Poor user experience**

## 🔍 Expected Behavior
The Whisper model should be:
1. ✅ Loaded **once** during prewarm (startup)
2. ✅ Stored in `proc.userdata["stt"]`
3. ✅ **Reused** for all subsequent requests
4. ✅ Never reloaded unless process restarts

## 🐛 Debugging Steps

### Step 1: Check Prewarm Logs
Look for these logs at startup:
```
🎤 [PREWARM] Preloading Whisper model...
⏳ [WHISPER-LOAD] Loading Whisper model: medium.en (Instance ID: ...)
✅ [WHISPER-LOAD] Whisper model loaded successfully: medium.en (Instance ID: ...)
✅ [PREWARM] Whisper model preloaded!
```

**If you DON'T see these logs:**
- ❌ Prewarm is not running
- ❌ Check if `prewarm_entrypoint()` is being called
- ❌ Check if `stt_provider` config is set to `'whisper'`

### Step 2: Check Session Creation Logs
When a new room/session starts, look for:
```
✅ STT loaded from prewarm - Type: <class '...'>, ID: ...
   Whisper model status: LOADED
```

**If you see this instead:**
```
⚠️ STT not preloaded, creating now (this will add ~0.35s latency)...
🆕 [WHISPER-INIT] Creating NEW WhisperSTT instance (ID: ...)
⏳ [WHISPER-LOAD] Loading Whisper model: medium.en (Instance ID: ...)
```

**Then the problem is:**
- ❌ `proc.userdata["stt"]` is `None`
- ❌ Prewarm failed or didn't run
- ❌ STT instance is not being stored/retrieved correctly

### Step 3: Check Instance IDs
Compare the Instance IDs in the logs:
```
Prewarm:  Instance ID: 140234567890123
Session:  Instance ID: 140234567890123  ✅ SAME = GOOD (reusing)
Session:  Instance ID: 140234567890456  ❌ DIFFERENT = BAD (new instance)
```

If IDs are **different**, a new WhisperSTT instance is being created each time.

## 🔧 Possible Root Causes

### Cause 1: Prewarm Not Running
**Check:** Is `prewarm_entrypoint()` being called?
```python
# In simple_main.py
if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm_entrypoint))
```

**Fix:** Ensure `prewarm_fnc=prewarm_entrypoint` is set.

### Cause 2: Config Mismatch
**Check:** Is `stt_provider` set correctly?
```python
# In config
stt_provider: 'whisper'  # Must match exactly
```

**Fix:** Verify config file has correct provider name.

### Cause 3: Multiple Worker Processes
**Check:** Are you running multiple worker processes?
```bash
# Each process has its own memory space
Worker 1: Loads model (Instance ID: 123)
Worker 2: Loads model (Instance ID: 456)  # Different process!
```

**Fix:** Each worker process needs to prewarm independently. This is normal but means each process will load the model once.

### Cause 4: StreamAdapter/FallbackAdapter Creating New Instances
**Check:** Is `create_stt()` being called multiple times?

**Current code:**
```python
# provider_factory.py
def create_stt(config, vad=None):
    return stt.StreamAdapter(
        stt=WhisperSTT(  # ❌ Creates NEW instance every time!
            model=config.get('stt_model', 'base'),
            language=config.get('stt_language', 'en')
        ),
        vad=vad
    )
```

**Fix:** Cache the WhisperSTT instance:
```python
# Global cache for STT instances
_stt_cache = {}

def create_stt(config, vad=None):
    cache_key = f"{config.get('stt_provider')}_{config.get('stt_model')}"
    
    if cache_key not in _stt_cache:
        _stt_cache[cache_key] = WhisperSTT(
            model=config.get('stt_model', 'base'),
            language=config.get('stt_language', 'en')
        )
    
    return stt.StreamAdapter(
        stt=_stt_cache[cache_key],  # ✅ Reuse cached instance
        vad=vad
    )
```

## 🎯 Recommended Fix

The most likely issue is **Cause 4** - `create_stt()` creates a new `WhisperSTT()` instance every time it's called.

**Solution:** Implement instance caching in `provider_factory.py`:

```python
# At module level
_whisper_stt_instance = None
_fastwhisper_stt_instance = None

@staticmethod
def create_stt(config, vad=None):
    global _whisper_stt_instance, _fastwhisper_stt_instance
    
    provider = config.get('stt_provider', 'groq').lower()
    
    if provider == 'whisper':
        # Reuse existing instance if available
        if _whisper_stt_instance is None:
            logger.info("🆕 Creating new WhisperSTT instance (first time)")
            _whisper_stt_instance = WhisperSTT(
                model=config.get('stt_model', 'base'),
                language=config.get('stt_language', 'en')
            )
        else:
            logger.info("♻️ Reusing existing WhisperSTT instance")
        
        return stt.StreamAdapter(
            stt=_whisper_stt_instance,
            vad=vad
        )
    # ... similar for other providers
```

## 📊 Performance Impact

| Scenario | Model Load Time | Memory Usage | User Experience |
|----------|----------------|--------------|-----------------|
| **Current (Reload Every Time)** | 19s per request | 5GB+ spikes | ❌ Terrible |
| **Fixed (Load Once)** | 19s at startup | Stable ~1GB | ✅ Excellent |

## ✅ Verification

After applying the fix, you should see:
1. **At startup:**
   ```
   🆕 Creating new WhisperSTT instance (first time)
   ⏳ [WHISPER-LOAD] Loading Whisper model: medium.en
   ✅ [WHISPER-LOAD] Whisper model loaded successfully
   ```

2. **For subsequent requests:**
   ```
   ♻️ Reusing existing WhisperSTT instance
   ✅ [WHISPER-REUSE] Model already loaded
   ```

3. **No more 19-second delays** during user speech!

## 🚀 Next Steps

1. Run the agent with enhanced logging
2. Check the logs for Instance IDs
3. Identify which cause applies
4. Apply the appropriate fix
5. Verify model is only loaded once
6. Enjoy fast transcription! 🎉
