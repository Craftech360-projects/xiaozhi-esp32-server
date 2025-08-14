# 🎭 Kid Companion Voice Guide

## 🌟 **RECOMMENDED: `expr-voice-3-f`**

**Why this voice is perfect for kids:**
- ✅ **Warm & Nurturing**: Has a caring, motherly quality
- ✅ **Clear Pronunciation**: Easy for children to understand
- ✅ **Age-Appropriate**: Not too mature, not too childish
- ✅ **Engaging**: Keeps children interested in conversations
- ✅ **Comfortable**: Pleasant for extended interactions

## 🎧 **Listen & Compare**

Audio samples are saved in `tmp/voice_tests/`:
- `expr-voice-2-f_phrase_*.wav` - More energetic, slightly higher pitch
- `expr-voice-3-f_phrase_*.wav` - **RECOMMENDED** - Warm and nurturing
- `expr-voice-4-f_phrase_*.wav` - Softer, gentler tone
- `expr-voice-5-f_phrase_*.wav` - Clear and friendly

## ⚙️ **Current Configuration**

Your config is now set to:
```yaml
TTS: kittentts
voice: expr-voice-3-f  # Kid-friendly female voice
speed: 0.9  # Slightly slower for comprehension
```

## 🎯 **Voice Characteristics for Kids**

| Voice | Best For | Characteristics |
|-------|----------|----------------|
| `expr-voice-2-f` | **Energetic kids** | Higher energy, more animated |
| `expr-voice-3-f` | **Most kids** ⭐ | Warm, nurturing, clear |
| `expr-voice-4-f` | **Sensitive kids** | Gentle, soft, calming |
| `expr-voice-5-f` | **Older kids** | Clear, friendly, mature |

## 🔧 **Fine-Tuning Tips**

### Speed Settings:
- `0.8` - For very young children (3-5 years)
- `0.9` - **RECOMMENDED** for most kids (4-8 years)
- `1.0` - For older children (8+ years)

### To Change Voice:
1. Edit `data/.config.yaml`
2. Change `voice: expr-voice-X-f`
3. Restart xiaozhi-server

## 🎪 **Testing Different Voices**

Run this to test all voices:
```bash
python test_kid_voices.py
```

## 👂 **What to Listen For**

When choosing a voice, consider:
- **Warmth**: Does it sound caring and friendly?
- **Clarity**: Can children easily understand each word?
- **Energy**: Is it engaging but not overwhelming?
- **Comfort**: Would you be comfortable hearing this for hours?
- **Age-appropriate**: Does it match your target age group?

## 🎨 **Cheeko's Personality Match**

Based on your prompt, Cheeko is:
- Friendly and curious
- Playful but caring
- Encouraging and positive

**`expr-voice-3-f`** matches this personality perfectly with its warm, nurturing, and engaging tone.

## 🚀 **Ready to Go!**

Your xiaozhi-server is now configured with the perfect voice for a kid companion. Start the server and let Cheeko chat with the children! 🎉