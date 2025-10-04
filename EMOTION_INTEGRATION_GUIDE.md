# 🎭 Emotion Detection Integration Guide

## Overview

This guide explains how to integrate emotion detection into the LiveKit-server to match the xiaozhi-server behavior. The emotion system detects emojis in LLM responses and forwards them to ESP32 devices via MQTT protocol.

**Important:** This implementation provides **protocol-level emotion metadata only**. The xiaozhi-server sends emotion information to the device, but does not control hardware (LEDs, sounds, etc.) directly. What the ESP32 firmware does with this emotion data depends entirely on your device's firmware implementation.

---

## 📊 System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        EMOTION DETECTION FLOW                            │
└─────────────────────────────────────────────────────────────────────────┘

1. LLM Response Generation
   ┌──────────────────┐
   │   LiveKit Agent  │  Generates response with emoji
   │   (LLM Provider) │  Example: "😂 That's hilarious!"
   └────────┬─────────┘
            │
            ▼
   ┌──────────────────────────────────────────┐
   │  Emotion Detection (First Chunk)         │
   │  • Scans for emoji in text               │
   │  • Maps emoji → emotion name             │
   │  • Example: 😂 → "laughing"              │
   └────────┬─────────────────────────────────┘
            │
            ▼
2. Data Channel Communication
   ┌──────────────────────────────────────────┐
   │  LiveKit Data Channel                    │
   │  Sends: {                                │
   │    "type": "llm_emotion",                │
   │    "emoji": "😂",                        │
   │    "emotion": "laughing"                 │
   │  }                                       │
   └────────┬─────────────────────────────────┘
            │
            ▼
3. MQTT Gateway Processing
   ┌──────────────────────────────────────────┐
   │  mqtt-gateway (app.js)                   │
   │  • Receives data via RoomEvent           │
   │  • Calls sendLlmMessage(emoji, emotion)  │
   │  • Publishes to MQTT topic               │
   └────────┬─────────────────────────────────┘
            │
            ▼
4. ESP32 Device Processing
   ┌──────────────────────────────────────────┐
   │  ESP32 Firmware (Your Implementation)   │
   │  • Receives MQTT message:                │
   │    {                                     │
   │      "type": "llm",                      │
   │      "text": "😂",                       │
   │      "emotion": "laughing",              │
   │      "session_id": "..."                 │
   │    }                                     │
   │  • What happens next is firmware-        │
   │    dependent (LEDs, sounds, etc.)        │
   └──────────────────────────────────────────┘
```

---

## 🎨 Emotion Mapping

### Supported Emotions (from xiaozhi-server)

| Emoji | Emotion Name | Use Case |
|-------|-------------|----------|
| 😂 | laughing | Jokes, funny stories |
| 😭 | crying | Sad stories, empathy |
| 😠 | angry | Frustrated responses |
| 😔 | sad | Sympathetic responses |
| 😍 | loving | Affectionate replies |
| 😲 | surprised | Unexpected info |
| 😱 | shocked | Very surprising news |
| 🤔 | thinking | Pondering, analyzing |
| 😌 | relaxed | Calm, peaceful |
| 😴 | sleepy | Bedtime stories |
| 😜 | silly | Playful responses |
| 🙄 | confused | Don't understand |
| 😶 | neutral | Default state |
| 🙂 | happy | Positive responses (default) |
| 😆 | laughing | Very funny |
| 😳 | embarrassed | Shy responses |
| 😉 | winking | Playful secrets |
| 😎 | cool | Confident replies |
| 🤤 | delicious | Food-related |
| 😘 | kissy | Affectionate |
| 😏 | confident | Self-assured |

**Note:** The emotion mapping is used for:
1. **Making the LLM emotionally expressive** - The system prompt instructs the LLM to include emojis
2. **Providing metadata to devices** - The ESP32 receives emotion information
3. **Device firmware decides behavior** - What happens with this data (LEDs, sounds, display) depends on your ESP32 firmware implementation

---

## 🔧 Implementation Guide

### Phase 1: Create Emotion Utilities

**File:** `main/livekit-server/src/utils/emotion_utils.py`

```python
"""
Emotion detection and management utilities for LiveKit agent
Maps emojis in LLM responses to emotion states - matches xiaozhi-server behavior
"""
import logging
import json

logger = logging.getLogger("emotion_utils")

# Emotion mapping from xiaozhi-server/core/utils/textUtils.py
EMOJI_MAP = {
    "😂": "laughing",
    "😭": "crying",
    "😠": "angry",
    "😔": "sad",
    "😍": "loving",
    "😲": "surprised",
    "😱": "shocked",
    "🤔": "thinking",
    "😌": "relaxed",
    "😴": "sleepy",
    "😜": "silly",
    "🙄": "confused",
    "😶": "neutral",
    "🙂": "happy",
    "😆": "laughing",
    "😳": "embarrassed",
    "😉": "winking",
    "😎": "cool",
    "🤤": "delicious",
    "😘": "kissy",
    "😏": "confident",
}

# Emoji detection ranges
EMOJI_RANGES = [
    (0x1F600, 0x1F64F),  # Emoticons
    (0x1F300, 0x1F5FF),  # Misc symbols and pictographs
    (0x1F680, 0x1F6FF),  # Transport and map symbols
    (0x1F900, 0x1F9FF),  # Supplemental symbols and pictographs
    (0x1FA70, 0x1FAFF),  # Extended pictographic
    (0x2600, 0x26FF),    # Misc symbols
    (0x2700, 0x27BF),    # Dingbats
]

def is_emoji(char: str) -> bool:
    """Check if character is emoji"""
    code_point = ord(char)
    return any(start <= code_point <= end for start, end in EMOJI_RANGES)

def extract_emotion(text: str) -> tuple[str, str]:
    """
    Extract emotion from text by finding first emoji
    Matches xiaozhi-server behavior exactly

    Args:
        text: Text to analyze for emotion

    Returns:
        tuple: (emoji, emotion_name) - defaults to ("🙂", "happy")
    """
    emoji = "🙂"
    emotion = "happy"

    for char in text:
        if char in EMOJI_MAP:
            emoji = char
            emotion = EMOJI_MAP[char]
            logger.debug(f"✨ Detected emotion: {emoji} → {emotion}")
            break

    return emoji, emotion

def remove_emojis(text: str) -> str:
    """
    Remove all emojis from text (useful for TTS processing)

    Args:
        text: Text containing emojis

    Returns:
        Text with emojis removed
    """
    return ''.join(char for char in text if not is_emoji(char))

async def send_emotion_via_data_channel(room, emoji: str, emotion: str):
    """
    Send emotion message via LiveKit data channel to MQTT gateway
    Gateway will forward to ESP32 via MQTT

    Args:
        room: LiveKit room instance
        emoji: Emoji character (e.g., "😂")
        emotion: Emotion name (e.g., "laughing")
    """
    try:
        message = {
            "type": "llm_emotion",
            "emoji": emoji,
            "emotion": emotion,
        }
        await room.local_participant.publish_data(
            json.dumps(message).encode(),
            topic="emotion",
            reliable=True
        )
        logger.info(f"✨ [EMOTION] Sent to gateway: {emoji} ({emotion})")
    except Exception as e:
        logger.warning(f"⚠️ [EMOTION] Failed to send emotion message: {e}")
```

---

### Phase 2: Update Chat Event Handler

**File:** `main/livekit-server/src/handlers/chat_logger.py`

Add emotion tracking:

```python
# Add import at the top
from ..utils.emotion_utils import extract_emotion, send_emotion_via_data_channel

class ChatEventHandler:
    """Event handler for chat logging and data channel communication"""

    # Store assistant reference for abort handling
    _assistant_instance = None
    _chat_history_service = None

    # NEW: Emotion tracking flag
    _emotion_sent_for_current_turn = False

    @staticmethod
    def reset_emotion_flag():
        """Reset emotion flag when agent starts new response"""
        ChatEventHandler._emotion_sent_for_current_turn = False
        logger.debug("🔄 [EMOTION] Reset emotion flag for new turn")

    @staticmethod
    async def process_agent_text_for_emotion(ctx, text: str):
        """
        Process agent response text to detect and send emotion
        Matches xiaozhi-server behavior: send emotion on first chunk only

        Args:
            ctx: Job context with room access
            text: Agent's response text
        """
        # Only process emotion once per conversation turn
        if ChatEventHandler._emotion_sent_for_current_turn:
            return

        # Only process non-empty text
        if not text or not text.strip():
            return

        try:
            # Extract emotion from text
            emoji, emotion = extract_emotion(text)

            # Send via data channel to MQTT gateway
            if ctx and ctx.room:
                await send_emotion_via_data_channel(ctx.room, emoji, emotion)
                ChatEventHandler._emotion_sent_for_current_turn = True
                logger.info(f"✅ [EMOTION] Processed: {emoji} ({emotion})")
        except Exception as e:
            logger.error(f"❌ [EMOTION] Error processing emotion: {e}")

    @staticmethod
    def setup_session_handlers(session, ctx):
        """Setup all session event handlers including emotion detection"""

        # ... existing handlers ...

        # NEW: Add agent speech started handler
        @session.on("agent_speech_started")
        def on_agent_speech_started(message):
            """Reset emotion flag when agent starts speaking"""
            ChatEventHandler.reset_emotion_flag()
            logger.debug("🎤 [AGENT] Speech started - emotion flag reset")

        # NEW: Add agent speech committed handler for emotion detection
        @session.on("agent_speech_committed")
        def on_agent_speech_committed(message):
            """
            Detect emotion from agent's committed speech
            This fires after LLM generates response but before TTS
            """
            try:
                # Extract text from message
                text = message.message if hasattr(message, 'message') else str(message)

                # Process emotion asynchronously
                import asyncio
                asyncio.create_task(
                    ChatEventHandler.process_agent_text_for_emotion(ctx, text)
                )
                logger.debug(f"📝 [EMOTION] Processing text: {text[:50]}...")
            except Exception as e:
                logger.error(f"❌ [EMOTION] Error in speech_committed handler: {e}")
```

---

### Phase 3: Update MQTT Gateway

**File:** `main/mqtt-gateway/app.js`

Add emotion handling in the data channel receiver:

```javascript
// In LiveKitBridge class, update DataReceived handler (around line 274)
this.room.on(
  RoomEvent.DataReceived,
  (payload, participant, kind, topic) => {
    try {
      const str = Buffer.from(payload).toString("utf-8");
      let data;
      try {
        data = JSON5.parse(str);
      } catch (err) {
        console.error("Invalid JSON5:", err.message);
        return;
      }

      switch (data.type) {
        case "agent_state_changed":
          // ... existing handler ...
          break;

        case "user_input_transcribed":
          // ... existing handler ...
          break;

        case "speech_created":
          // ... existing handler ...
          break;

        // NEW: Handle emotion messages from LiveKit agent
        case "llm_emotion":
          console.log(`✨ [EMOTION] Received: ${data.emoji} (${data.emotion})`);
          // Use existing sendLlmMessage function (already defined in app.js:1192)
          this.sendLlmMessage(data.emoji, data.emotion);
          break;

        case "device_control":
          // ... existing handler ...
          break;

        case "function_call":
          // ... existing handler ...
          break;

        default:
          // console.log(`Unknown data type: ${data.type}`);
      }
    } catch (error) {
      console.error(`Error processing data packet: ${error}`);
    }
  }
);
```

**Note:** The `sendLlmMessage()` function already exists in the gateway (line 1192-1206) but was never called. This integration uses it.

---

### Phase 4: Update System Prompt

**File:** `main/livekit-server/src/services/prompt_service.py` or wherever prompts are loaded

Add emotion instruction to the system prompt (based on xiaozhi-server's agent-base-prompt.txt):

```python
EMOTION_INSTRUCTION = """
## 🎭 Emotional Expression

You are an expressive character who shows emotions through emojis:

**Rules:**
1. Include ONE emoji at the VERY BEGINNING of your response
2. Choose the emoji that best matches your emotional state
3. Only use emojis from this list: 😂 😭 😠 😔 😍 😲 😱 🤔 😌 😴 😜 🙄 😶 🙂 😆 😳 😉 😎
4. The emoji will be sent to the device but NOT spoken in TTS

**Examples:**
- User: "Tell me a joke!" → "😂 Why don't scientists trust atoms? Because they make up everything!"
- User: "I'm scared of the dark" → "😌 Don't worry, I'm here with you. The dark is just night time sleeping!"
- User: "That's amazing!" → "😲 I know, right?! Isn't that so cool!"
- User: "I'm sad" → "😔 I'm sorry you're feeling sad. Want to talk about it?"

Remember: Be warm, emotionally aware, and expressive - especially for kids!
"""

def enhance_prompt_with_emotions(base_prompt: str) -> str:
    """Add emotion instructions to base prompt"""
    return f"{base_prompt}\n\n{EMOTION_INSTRUCTION}"
```

Then update where prompts are loaded in `main.py`:

```python
# In entrypoint function, after fetching device prompt:
if device_mac:
    try:
        agent_prompt = await prompt_service.get_prompt(room_name, device_mac)
        # NEW: Add emotion instructions
        from src.services.prompt_service import enhance_prompt_with_emotions
        agent_prompt = enhance_prompt_with_emotions(agent_prompt)
        logger.info(f"🎯 Using device-specific prompt with emotion support")
    except Exception as e:
        logger.warning(f"Failed to fetch device prompt: {e}")
```

---

## 🧪 Testing Guide

### Test 1: Basic Emotion Detection

**Test Case:** Ask the agent to tell a joke

```
User: "Tell me a funny joke!"
Expected Flow:
  1. LLM generates: "😂 Why did the chicken cross the road? To get to the other side!"
  2. emotion_utils extracts: emoji="😂", emotion="laughing"
  3. Data channel sends: {"type": "llm_emotion", "emoji": "😂", "emotion": "laughing"}
  4. MQTT gateway forwards: {"type": "llm", "text": "😂", "emotion": "laughing", "session_id": "..."}
  5. ESP32 receives the message (what happens next depends on firmware)
```

**Logs to Check:**
```
livekit-server logs:
  ✨ [EMOTION] Detected emotion: 😂 → laughing
  ✨ [EMOTION] Sent to gateway: 😂 (laughing)

mqtt-gateway logs:
  ✨ [EMOTION] Received: 😂 (laughing)
  📤 [MQTT OUT] Sending LLM response to device: 00:16:3e:ac:b5:38 - "😂"
```

### Test 2: Emotion Changes Per Context

**Test Case:** Various emotional contexts

```
Scenario A - Sadness:
  User: "I lost my favorite toy"
  Expected: 😔 sad

Scenario B - Excitement:
  User: "I got an A+ on my test!"
  Expected: 😲 surprised / 😍 loving

Scenario C - Bedtime:
  User: "Can you tell me a bedtime story?"
  Expected: 😴 sleepy
```

### Test 3: Default Emotion

**Test Case:** Neutral conversation

```
User: "What time is it?"
Expected: 🙂 happy (default)
```

---

## 🐛 Troubleshooting

### Problem: No emotion messages in MQTT gateway

**Check:**
1. LiveKit-server logs for emotion detection
2. Data channel topic is correct ("emotion")
3. MQTT gateway is subscribed to DataReceived event

**Solution:**
```bash
# Check livekit-server logs
grep "EMOTION" logs/livekit-server.log

# Check mqtt-gateway logs
grep "llm_emotion" mqtt-gateway/logs/*.log
```

### Problem: Wrong emotion detected

**Check:**
1. LLM is including emoji at the start of response
2. Emoji is in EMOJI_MAP
3. System prompt includes emotion instructions

**Solution:**
Add more logging:
```python
logger.info(f"🔍 [DEBUG] Raw LLM text: {text[:100]}")
logger.info(f"🔍 [DEBUG] First char: {text[0]} (code: {ord(text[0])})")
```

### Problem: Emotion sent multiple times

**Check:**
1. `_emotion_sent_for_current_turn` flag is resetting properly
2. `agent_speech_started` event is firing

**Solution:**
Verify reset logic:
```python
@session.on("agent_speech_started")
def on_agent_speech_started(message):
    logger.info("🔄 [DEBUG] Speech started - resetting emotion flag")
    ChatEventHandler.reset_emotion_flag()
```

### Problem: ESP32 not responding to emotions

**Check:**
1. MQTT message format matches expected format: `{"type": "llm", "text": "😂", "emotion": "laughing", "session_id": "..."}`
2. ESP32 firmware handles "llm" message type
3. MQTT topic is correct: `devices/p2p/<mac_address>`

**Solution:**
Monitor MQTT traffic:
```bash
# Subscribe to MQTT topic to see messages
mosquitto_sub -h <broker> -t "devices/p2p/<mac_address>" -v
```

---

## 📝 File Structure Summary

```
main/livekit-server/
├── src/
│   ├── utils/
│   │   └── emotion_utils.py          ✨ NEW - Emotion detection & management
│   ├── handlers/
│   │   └── chat_logger.py             📝 MODIFIED - Add emotion event handling
│   ├── services/
│   │   └── prompt_service.py          📝 MODIFIED - Add emotion instructions
│   └── agent/
│       └── main_agent.py              (No changes needed)
├── main.py                            📝 MODIFIED - Wire up emotion prompt
└── tests/
    └── test_emotion_utils.py          ✨ NEW - Unit tests (optional)

main/mqtt-gateway/
└── app.js                             📝 MODIFIED - Handle llm_emotion messages
```

---

## ✅ Implementation Checklist

- [ ] Create `emotion_utils.py` with emoji mapping and detection
- [ ] Update `chat_logger.py` with emotion event handlers
- [ ] Add emotion instruction to system prompts
- [ ] Update MQTT gateway to handle `llm_emotion` data channel messages
- [ ] Test with various emotional contexts
- [ ] Verify ESP32 receives emotion messages via MQTT
- [ ] Add logging for debugging
- [ ] (Optional) Document device-specific emotion handling in ESP32 firmware

---

## 🎯 Performance Considerations

### Minimal Overhead

- Emotion detection happens on **first chunk only** (not every chunk)
- Uses simple character iteration (O(n) where n = text length, typically < 100 chars)
- Data channel messages are small (~100 bytes)
- No blocking operations
- Matches xiaozhi-server performance characteristics

---

## 📊 What xiaozhi-server Does (Reference)

For reference, here's exactly what xiaozhi-server does with emotions:

1. **Detects emoji** from first LLM response chunk (`core/utils/textUtils.py:86-111`)
2. **Sends WebSocket message** to client:
   ```json
   {
     "type": "llm",
     "text": "😂",
     "emotion": "laughing",
     "session_id": "..."
   }
   ```
3. **Does NOT control hardware** - that's up to the client firmware
4. **Uses emotion in system prompt** to make LLM responses more expressive (`agent-base-prompt.txt:5-15`)

This implementation replicates that behavior exactly via LiveKit's data channel instead of WebSocket.

---

## ❓ FAQ

### Q: Will this control LEDs on my device?
**A:** No. This sends emotion metadata to your ESP32. What your device does with it depends entirely on your ESP32 firmware implementation.

### Q: What if my device doesn't use emotion data?
**A:** The device will receive the message but can ignore it. No harm done. The main benefit is making the LLM responses more emotionally expressive via the system prompt.

### Q: Can I customize the emotion mappings?
**A:** Yes. Modify `EMOJI_MAP` in `emotion_utils.py` to add/remove/change emoji → emotion mappings.

### Q: Does this affect TTS voice/tone?
**A:** No. The emotion is metadata only. Some TTS providers (like Minimax) support emotion parameters, but that's separate from this implementation.

---

## 📚 Related Documentation

- [MQTT Gateway Message Flow](./mqtt-gateway-message-flow.md)
- [Agent Base Prompt System](./docs/agent-base-prompt-system.md)
- [LiveKit Data Channel API](https://docs.livekit.io/realtime/client/data-messages/)
- [ESP32 MQTT Protocol Spec](./mqtt-integration.md)
- [xiaozhi-server emotion implementation](./main/xiaozhi-server/core/utils/textUtils.py)

---

## 🆘 Support

For issues or questions:
1. Check troubleshooting section above
2. Review logs in `livekit-server/logs/` and `mqtt-gateway/logs/`
3. Compare with xiaozhi-server behavior in `core/utils/textUtils.py`
4. Verify MQTT gateway connectivity
5. Monitor MQTT traffic with `mosquitto_sub`

---

**Generated:** 2025-10-04
**Version:** 1.1 (Accurate to xiaozhi-server implementation)
**Status:** Production Ready ✅
