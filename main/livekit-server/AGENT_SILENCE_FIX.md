# Agent Silence Fix - Prevent TTS Before Music

## Problem Analysis 🔍

From the logs, the issue is clear:
```
16:14:45,147 - tools execution completed (function returns empty string)
16:14:45,861 - Agent state changed: 'thinking' -> 'speaking' (PROBLEM!)
16:14:47,589 - Injecting music into TTS queue (too late!)
```

**Root Cause**: LiveKit's agent framework automatically generates responses after function calls, even when functions return empty strings. The agent is instructed to "respond naturally after function plays" which causes it to speak before the music starts.

## Solution Implemented ✅

### 1. Modified Agent Instructions
**File**: `src/agent/main_agent.py`

**Added Critical Rules**:
```
[Interaction Guidelines]
- CRITICAL: When you call play_music or play_story functions, DO NOT speak immediately after. Stay silent and let the music/story play first.

<tool_calling>
- IMPORTANT: After calling play_music or play_story functions, DO NOT respond immediately. Let the music/story play first.
- CRITICAL RULE: If a function returns "[MUSIC_PLAYING - STAY_SILENT]" or "[STORY_PLAYING - STAY_SILENT]", DO NOT generate any response. Stay completely silent.
- NEVER say things like "Now playing..." or "Here's your song..." immediately after calling functions.
- Only speak again after the music/story naturally completes.
```

### 2. Modified Function Returns
**File**: `src/agent/main_agent.py`

**Before**:
```python
return ""  # Empty string - but agent still responds
```

**After**:
```python
return "[MUSIC_PLAYING - STAY_SILENT]"  # Explicit instruction to stay silent
```

### 3. Reordered Operations
**File**: `src/agent/main_agent.py`

**Before**:
```python
await player.play_from_url(song['url'], song['title'])  # Start music
# Send data channel notification
return ""
```

**After**:
```python
# Send data channel notification FIRST
music_start_data = {"type": "music_playback_started", ...}
await room.local_participant.publish_data(...)

# THEN start music
await player.play_from_url(song['url'], song['title'])
return "[MUSIC_PLAYING - STAY_SILENT]"
```

## Expected Flow Now 🎯

### Desired Sequence:
```
1. User: "Play baby shark"
2. Agent calls play_music() function
3. Function sends data channel notification
4. Function starts music playback
5. Function returns "[MUSIC_PLAYING - STAY_SILENT]"
6. Agent sees this return and STAYS SILENT
7. Music plays without TTS interruption
8. After music ends: completion message via audio player
```

### Key Changes:
- ✅ **Explicit silence instructions** in agent prompt
- ✅ **Special return values** that instruct agent to stay silent
- ✅ **Data channel notifications first** before music starts
- ✅ **Completion messages** handled by audio player after music ends

## Fallback Plan 🔧

If the agent still generates responses despite these instructions, the issue is that **LiveKit's agent framework ignores function returns and always generates responses**. In that case, we would need:

### Alternative Approach 1: Session Interruption
```python
# In play_music function
await player.play_from_url(song['url'], song['title'])
# Immediately interrupt any pending agent response
if hasattr(context, 'session'):
    context.session.interrupt()
return ""
```

### Alternative Approach 2: Custom Agent Pipeline
- Override the agent's response generation
- Intercept responses after function calls
- Suppress TTS when music functions are called

### Alternative Approach 3: Different Architecture
- Don't use function tools for music
- Use direct session.say() with audio frames
- Handle music requests in the main conversation flow

## Testing Instructions 📊

1. **Start the agent**:
   ```bash
   cd main/livekit-server
   python main.py dev
   ```

2. **Test music request**:
   - Say: "Play baby shark"
   - Expected: Music starts immediately without TTS
   - Check logs for agent state changes

3. **Verify sequence**:
   - Function should return "[MUSIC_PLAYING - STAY_SILENT]"
   - Agent should NOT change to "speaking" state
   - Music should start without voice overlay

4. **Test completion**:
   - Let music play completely
   - Should get completion message after music ends

## Success Criteria ✅

- ✅ No TTS before music starts
- ✅ Music plays cleanly without interruption
- ✅ Data channel notifications work
- ✅ Completion messages after music ends
- ✅ Immediate abort still works (< 200ms)

## Status: 🧪 TESTING REQUIRED

The changes are implemented. Now we need to test if:
1. The agent respects the silence instructions
2. The special return values suppress responses
3. Music plays without TTS interruption

If the agent still speaks before music, we'll need to implement one of the fallback approaches.