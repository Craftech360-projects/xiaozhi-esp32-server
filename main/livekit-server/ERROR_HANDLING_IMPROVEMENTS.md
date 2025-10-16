# LiveKit Server Error Handling Improvements

## Overview
This document describes the comprehensive error handling and user feedback improvements implemented to handle empty transcripts, empty LLM responses, and LLM failures in the LiveKit server.

## Supported Providers

The LiveKit server currently supports the following AI providers:

### Speech-to-Text (STT)
- **Groq Whisper** (default) - Fast, cloud-based STT
- **Deepgram** - Optional cloud STT provider

### Text-to-Speech (TTS)
- **Edge TTS** (default) - Microsoft Edge TTS, free and high quality
- **Groq TTS** - Cloud-based TTS
- **ElevenLabs** - Optional premium TTS provider

### Large Language Model (LLM)
- **Groq** - Fast inference with Llama models (Llama 3.1, Llama 3.3, etc.)

All providers support fallback configuration for high availability.

## Problem Statement

Previously, when errors occurred in the voice AI pipeline, users were left in confusion with no feedback:

1. **Empty Transcripts**: When STT failed to transcribe or produced empty results, the system remained silent
2. **Empty LLM Responses**: When the LLM returned no content, the agent showed "speaking" state but played no audio
3. **LLM Failures/Timeouts**: When the LLM failed or timed out, the system crashed or hung indefinitely
4. **No User Communication**: All failures were silent, leaving users confused about what happened

## Solutions Implemented

### 1. Empty Transcript Detection & Feedback
**File**: `src/handlers/chat_logger.py`
**Location**: Lines 342-362

#### What it does:
- Detects when `user_input_transcribed` event has empty or missing transcript text
- Generates a random clarification message asking the user to repeat
- Uses natural, friendly language appropriate for children

#### Messages used:
```python
clarification_messages = [
    "Sorry, I couldn't hear you properly. Could you please repeat that?",
    "I didn't catch that. Could you say it again?",
    "Sorry, I couldn't understand. Can you repeat what you said?",
    "I couldn't hear you clearly. Could you please try again?"
]
```

#### Flow:
```
User speaks → STT produces empty transcript → Event fires
→ Detect empty transcript → Generate clarification request
→ Agent speaks: "Sorry, I couldn't hear you properly..."
→ User repeats their question
```

### 2. Empty LLM Response Detection & Fallback
**File**: `src/agent/filtered_agent.py`
**Location**: Lines 92-93, 189-200

#### What it does:
- Tracks total characters received from LLM stream (`total_chars_received`)
- After LLM stream completes, checks if any meaningful content was received
- If empty, generates a fallback message explaining the issue

#### Messages used:
```python
fallback_messages = [
    "I'm sorry, I'm having trouble thinking right now. Could you try asking again?",
    "Hmm, I seem to be having a moment. Could you repeat that?",
    "Sorry, my mind went blank for a second. What was that again?",
    "I apologize, I didn't quite process that. Could you say it once more?"
]
```

#### Flow:
```
User question → LLM processes → Returns empty response
→ Detect total_chars_received == 0 → Generate fallback
→ Agent speaks: "I'm sorry, I'm having trouble thinking..."
→ User asks again
```

### 3. LLM Timeout Detection & Recovery
**File**: `src/agent/filtered_agent.py`
**Location**: Lines 96-97, 162-168, 178-188

#### What it does:
- Wraps LLM streaming in try/except with timeout tracking
- Catches `asyncio.TimeoutError` and general exceptions
- Provides specific timeout messages when LLM takes too long

#### Timeout Configuration:
```python
llm_timeout = 15.0  # 15 second timeout for LLM response
```

#### Messages used:
```python
timeout_messages = [
    "I'm sorry, I'm taking too long to think. Could you try asking me something else?",
    "Hmm, my response is taking longer than expected. Let's try again?",
    "Sorry, I seem to be running slow. Could you ask me that again?"
]
```

#### Flow:
```
User question → LLM starts processing → Takes > 15 seconds
→ TimeoutError caught → Set llm_timed_out = True
→ Generate timeout message → Agent speaks timeout response
→ User tries different question or retries
```

### 4. Exception Handling for LLM Errors
**File**: `src/agent/filtered_agent.py`
**Location**: Lines 165-168

#### What it does:
- Catches any unexpected exceptions during LLM streaming
- Logs full error traceback for debugging
- Continues gracefully to fallback message generation

#### Error Handling:
```python
except Exception as e:
    logger.error(f"❌ Error processing LLM stream: {e}")
    import traceback
    logger.error(f"❌ Traceback: {traceback.format_exc()}")
```

## Code Changes Summary

### Modified Files

1. **`src/handlers/chat_logger.py`**
   - Added empty transcript detection in `_on_user_input_transcribed` event handler
   - Added clarification message generation via `session.generate_reply()`
   - Added random message selection for variety

2. **`src/agent/filtered_agent.py`**
   - Added `asyncio` import for exception handling
   - Added `total_chars_received` tracking variable
   - Added `llm_timed_out` flag for timeout detection
   - Added try/except block around LLM stream processing
   - Added empty response detection logic
   - Added timeout detection and handling
   - Added fallback message generation for both cases

## Technical Details

### Empty Transcript Detection
```python
@session.on("user_input_transcribed")
def _on_user_input_transcribed(ev: UserInputTranscribedEvent):
    user_text = None
    # Try to extract transcript from various attributes
    if hasattr(ev, 'transcript') and ev.transcript:
        user_text = str(ev.transcript).strip()

    # If empty, ask for clarification
    if not user_text:
        clarification = random.choice(clarification_messages)
        session.generate_reply(instructions=f"Say this exact message: '{clarification}'")
```

### Empty LLM Response Detection
```python
async def buffered_filtered_text_stream():
    total_chars_received = 0

    async for text_chunk in text:
        total_chars_received += len(text_chunk)
        # ... process chunk ...

    # After stream ends
    if total_chars_received == 0:
        fallback = random.choice(fallback_messages)
        yield fallback
```

### LLM Timeout Handling
```python
try:
    async for text_chunk in text:
        # Process chunks...

except asyncio.TimeoutError:
    logger.error(f"⏱️ LLM response timeout after {llm_timeout} seconds")
    llm_timed_out = True
except Exception as e:
    logger.error(f"❌ Error processing LLM stream: {e}")

if llm_timed_out:
    yield random.choice(timeout_messages)
```

## Benefits

### User Experience
✅ **No more silent failures** - Users always get feedback
✅ **Clear communication** - Messages explain what went wrong
✅ **Natural language** - Child-friendly, conversational tone
✅ **Actionable guidance** - Users know to repeat or try again
✅ **Variety** - Multiple messages prevent repetitive responses

### Developer Experience
✅ **Better logging** - All errors logged with context
✅ **Easier debugging** - Full tracebacks captured
✅ **Graceful degradation** - System continues operating
✅ **Timeout protection** - Prevents infinite hangs
✅ **Clear error categorization** - Different messages for different errors

### System Reliability
✅ **Prevents crashes** - Exceptions caught and handled
✅ **Prevents hangs** - Timeout protection active
✅ **Maintains state** - Agent returns to listening after errors
✅ **Recoverable errors** - Users can retry immediately

## Testing Recommendations

### Test Cases

1. **Empty Transcript Test**
   - Speak very quietly or mumble
   - Cover microphone during speech
   - Expected: Agent asks for clarification

2. **Empty LLM Response Test**
   - Simulate LLM returning empty string
   - Expected: Agent says "I'm having trouble thinking..."

3. **LLM Timeout Test**
   - Simulate slow LLM (>15 seconds)
   - Expected: Agent says "I'm taking too long to think..."

4. **LLM Error Test**
   - Disconnect LLM API
   - Expected: Fallback adapter tries backup, or timeout message

5. **Network Failure Test**
   - Disconnect network during LLM call
   - Expected: Timeout or error message, system recovers

## Configuration

### Adjustable Parameters

**Timeout Duration** (`filtered_agent.py`):
```python
llm_timeout = 15.0  # Increase for slower LLMs, decrease for faster response
```

**Message Customization**:
All messages can be customized in the respective arrays in the source files. Consider:
- User's age group (currently optimized for children)
- Language/locale
- Brand voice/personality

## Future Improvements

### Potential Enhancements

1. **Retry Logic**
   - Automatic LLM retry on timeout (with exponential backoff)
   - Automatic transcript retry with different STT provider

2. **Metrics & Monitoring**
   - Track empty transcript rate
   - Track LLM timeout frequency
   - Alert on high error rates

3. **Adaptive Timeouts**
   - Adjust timeout based on LLM provider performance
   - Lower timeout for simple queries, higher for complex ones

4. **Contextual Messages**
   - Different messages based on conversation context
   - Personalized messages using child profile

5. **Error Recovery Strategies**
   - Try alternative phrasing when LLM fails
   - Suggest simpler questions when complex ones timeout

## Logging

### Log Messages to Watch

**Empty Transcript**:
```
📝⚠️ Empty transcript detected - triggering clarification response
🔊 Asking for clarification: 'Sorry, I couldn't hear you properly...'
```

**Empty LLM Response**:
```
❌ Empty LLM response detected - generating fallback message
🔊 Using fallback message: 'I'm sorry, I'm having trouble thinking...'
```

**LLM Timeout**:
```
⏱️ LLM response timeout after 15.0 seconds
⏱️ LLM timeout detected - generating timeout message
🔊 Using timeout message: 'I'm sorry, I'm taking too long to think...'
```

**LLM Error**:
```
❌ Error processing LLM stream: [error details]
❌ Traceback: [full traceback]
```

## Conclusion

These improvements transform the LiveKit server from a system that silently fails into one that gracefully handles errors and communicates clearly with users. The implementation is:

- **User-friendly**: Clear, actionable messages
- **Developer-friendly**: Comprehensive logging and error tracking
- **Production-ready**: Robust error handling and timeout protection
- **Maintainable**: Easily customizable messages and parameters

The system now provides a professional, reliable user experience even when things go wrong.
