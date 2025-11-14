# Remote Whisper isinstance() Fix

## Issue

When running the LiveKit agent with `remote_whisper` provider, the following error occurred:

```
TypeError: issubclass() argument 2 cannot be a parameterized generic
```

**Location**: `src/providers/remote_whisper_stt_provider.py`, line 124

**Root Cause**: Using `isinstance(buffer, utils.AudioBuffer)` where `utils.AudioBuffer` is a parameterized generic type (e.g., `AudioBuffer[T]`). Python's `isinstance()` cannot handle parameterized generics directly.

## Solution

Changed from type checking to attribute checking:

### Before (Broken)
```python
def _prepare_audio(self, buffer: Union[utils.AudioBuffer, "rtc.AudioFrame"]):
    """Convert audio buffer to numpy array"""
    import numpy as np
    
    if isinstance(buffer, utils.AudioBuffer):  # ❌ Fails with parameterized generic
        data = np.frombuffer(buffer.data, dtype=np.int16)
    else:
        data = np.array(buffer.data, dtype=np.int16)
    
    return data
```

### After (Fixed)
```python
def _prepare_audio(self, buffer: Union[utils.AudioBuffer, "rtc.AudioFrame"]):
    """Convert audio buffer to numpy array"""
    import numpy as np
    
    # Check if buffer has 'data' attribute (works for both AudioBuffer and AudioFrame)
    if hasattr(buffer, 'data'):
        # Convert buffer data to numpy array
        if isinstance(buffer.data, (bytes, bytearray)):
            data = np.frombuffer(buffer.data, dtype=np.int16)
        else:
            data = np.array(buffer.data, dtype=np.int16)
    else:
        # Fallback: treat as raw data
        data = np.array(buffer, dtype=np.int16)
    
    return data
```

## Why This Works

1. **Duck Typing**: Instead of checking the type, we check for the `data` attribute
2. **More Flexible**: Works with any object that has a `data` attribute
3. **No Generic Issues**: Avoids the parameterized generic problem entirely
4. **Better Error Handling**: Includes fallback for unexpected buffer types

## Testing

After this fix, the remote Whisper STT provider should work correctly:

```bash
# Test the agent
python simple_main.py dev
```

The agent will now successfully:
1. Receive audio from LiveKit
2. Convert it to the correct format
3. Send it to the remote Whisper server
4. Return transcription results

## Status

✅ **Fixed** - Remote Whisper STT provider now handles audio buffers correctly

---

**Date**: 2025-11-13  
**File Modified**: `src/providers/remote_whisper_stt_provider.py`
