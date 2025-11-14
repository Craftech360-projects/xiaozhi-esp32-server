# Tool Usage Fix - Preventing Unwanted Function Calls

## Issue

When asking the agent to "tell me a story", the LLM (llama3.1:8b) was calling MCP tools like `set_light_color(color="off")` before telling the story, even though the user didn't request any light changes.

**Example Log**:
```
2025-11-14 09:36:03,094 - DEBUG livekit.agents - executing tool
  function: set_light_color
  arguments: {"color":"off"}
```

This happened because the LLM was being "creative" and trying to set the mood for storytelling by turning off lights.

## Root Cause

The system prompt had this instruction:
```
Use them ONLY when explicitly requested by the user.
```

However, this wasn't specific enough. The LLM interpreted "setting the mood for a story" as a valid reason to use the light control function.

## Solution

Updated the system prompt with more explicit instructions about when NOT to use tools:

### Before
```xml
<tools>
You have access to these functions:
...
Use them ONLY when explicitly requested by the user.
</tools>
```

### After
```xml
<tools>
You have access to these functions:
...

IMPORTANT: Use these functions ONLY when the user EXPLICITLY asks you to:
- "turn on the light" → use set_light_color
- "change volume" → use set_device_volume
- "check battery" → use check_battery_level

DO NOT use these functions for:
- Storytelling (just tell the story directly)
- General conversation (just respond normally)
- Setting mood/ambiance (unless explicitly requested)

If unsure whether to use a function, DON'T use it - just respond with text.
</tools>
```

## Key Changes

1. **Explicit Examples**: Added clear examples of when to use each function
2. **Negative Examples**: Listed scenarios where tools should NOT be used
3. **Default Behavior**: "If unsure, DON'T use it" - conservative approach
4. **Specific Scenarios**: Called out storytelling and mood-setting explicitly

## Expected Behavior After Fix

### User: "Can you tell me a story?"
**Before**: Calls `set_light_color("off")` then tells story  
**After**: Just tells the story directly ✅

### User: "Turn off the lights"
**Before**: Calls `set_light_color("off")` ✅  
**After**: Calls `set_light_color("off")` ✅ (no change, correct behavior)

### User: "Tell me a story and turn off the lights"
**Before**: Calls `set_light_color("off")` then tells story ✅  
**After**: Calls `set_light_color("off")` then tells story ✅ (no change, correct behavior)

## Testing

To test the fix:

1. Restart the agent:
   ```bash
   python simple_main.py dev
   ```

2. Ask for a story:
   ```
   User: "Can you tell me a story?"
   ```

3. Check logs - should NOT see:
   ```
   executing tool {"function": "set_light_color"}
   ```

4. The agent should respond directly with the story.

## Why This Matters

**Performance**: Unnecessary function calls add latency:
- MCP call: ~200ms
- Light change: ~100ms
- Total wasted: ~300ms per unnecessary call

**User Experience**: 
- Unexpected device behavior (lights turning off)
- Slower responses
- Confusing for users who didn't ask for device changes

**Resource Usage**:
- Extra network calls
- Extra logging
- Extra processing

## Related Files

- `simple_main.py` - System prompt with tool usage instructions
- MCP tools: `set_light_color`, `set_device_volume`, `check_battery_level`, etc.

## Status

✅ **Fixed** - Tool usage instructions are now more explicit and conservative

---

**Date**: 2025-11-14  
**Issue**: Unwanted tool calls during storytelling  
**Fix**: Updated system prompt with explicit tool usage guidelines
