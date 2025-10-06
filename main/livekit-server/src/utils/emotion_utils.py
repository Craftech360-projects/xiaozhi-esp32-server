"""
Emotion detection and management utilities for LiveKit agent
Maps emojis in LLM responses to emotion states - matches xiaozhi-server behavior

This module is ISOLATED and does not affect existing functionality.
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
    try:
        code_point = ord(char)
        return any(start <= code_point <= end for start, end in EMOJI_RANGES)
    except (TypeError, ValueError):
        return False

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

    if not text:
        return emoji, emotion

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
    if not text:
        return text
    return ''.join(char for char in text if not is_emoji(char))

async def send_emotion_via_data_channel(room, emoji: str, emotion: str):
    """
    Send emotion message via LiveKit data channel to MQTT gateway
    Gateway will forward to ESP32 via MQTT

    Args:
        room: LiveKit room instance
        emoji: Emoji character (e.g., "😂") - used for detection but not sent
        emotion: Emotion name (e.g., "laughing")
    """
    try:
        if not room:
            logger.warning("⚠️ [EMOTION] No room available, skipping emotion send")
            return

        message = {
            "type": "llm",
            "emotion": emotion,
        }
        await room.local_participant.publish_data(
            json.dumps(message).encode(),
            reliable=True
        )
        logger.info(f"✨ [EMOTION] Sent to gateway: {emotion}")
    except Exception as e:
        # Non-fatal error - log and continue
        logger.warning(f"⚠️ [EMOTION] Failed to send emotion message: {e}")
