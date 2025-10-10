# Mode Change Audio Files

This directory contains pre-recorded PCM audio files for mode change confirmations.

## Audio Format

- **Format**: Raw PCM (s16le)
- **Sample Rate**: 24 kHz
- **Channels**: Mono (1 channel)
- **Bit Depth**: 16-bit signed
- **Encoding**: Little-endian
- **Frame Duration**: 60ms

## Required Files

You need to generate the following PCM files:

- `mode_cheeko.pcm` - "Switched to Cheeko mode"
- `mode_story.pcm` - "Switched to Story mode"
- `mode_music.pcm` - "Switched to Music mode"
- `mode_tutor.pcm` - "Switched to Tutor mode"
- `mode_chat.pcm` - "Switched to Chat mode"
- `mode_changed.pcm` - Generic "Mode changed" (default fallback)

## How to Generate Audio Files

### Method 1: Using edge-tts + ffmpeg (Recommended)

```bash
# Install edge-tts (Python)
pip install edge-tts

# Generate audio for each mode
cd C:\Users\Acer\Cheeko-esp32-server\main\mqtt-gateway\audio\mode_change

# Cheeko mode
edge-tts --voice "en-US-AndrewNeural" --text "Switched to Cheeko mode" --write-media temp.mp3
ffmpeg -i temp.mp3 -f s16le -ar 24000 -ac 1 mode_cheeko.pcm

# Story mode
edge-tts --voice "en-US-AndrewNeural" --text "Switched to Story mode" --write-media temp.mp3
ffmpeg -i temp.mp3 -f s16le -ar 24000 -ac 1 mode_story.pcm

# Music mode
edge-tts --voice "en-US-AndrewNeural" --text "Switched to Music mode" --write-media temp.mp3
ffmpeg -i temp.mp3 -f s16le -ar 24000 -ac 1 mode_music.pcm

# Tutor mode
edge-tts --voice "en-US-AndrewNeural" --text "Switched to Tutor mode" --write-media temp.mp3
ffmpeg -i temp.mp3 -f s16le -ar 24000 -ac 1 mode_tutor.pcm

# Chat mode
edge-tts --voice "en-US-AndrewNeural" --text "Switched to Chat mode" --write-media temp.mp3
ffmpeg -i temp.mp3 -f s16le -ar 24000 -ac 1 mode_chat.pcm

# Default fallback
edge-tts --voice "en-US-AndrewNeural" --text "Mode changed" --write-media temp.mp3
ffmpeg -i temp.mp3 -f s16le -ar 24000 -ac 1 mode_changed.pcm

# Clean up temp file
del temp.mp3
```

### Method 2: Convert Existing Opus Files

If you already have `.opus` files:

```bash
cd C:\Users\Acer\Cheeko-esp32-server\main\mqtt-gateway\audio\mode_change

ffmpeg -i mode_cheeko.opus -f s16le -ar 24000 -ac 1 mode_cheeko.pcm
ffmpeg -i mode_story.opus -f s16le -ar 24000 -ac 1 mode_story.pcm
ffmpeg -i mode_music.opus -f s16le -ar 24000 -ac 1 mode_music.pcm
ffmpeg -i mode_tutor.opus -f s16le -ar 24000 -ac 1 mode_tutor.pcm
ffmpeg -i mode_chat.opus -f s16le -ar 24000 -ac 1 mode_chat.pcm
ffmpeg -i mode_changed.opus -f s16le -ar 24000 -ac 1 mode_changed.pcm
```

## How It Works

1. **Device triggers mode change** (button press or voice command)
2. **Manager API cycles the mode** in database
3. **MQTT Gateway loads PCM file** based on mode name
4. **Streams PCM in 60ms frames**:
   - Each frame = 2880 bytes (1440 samples × 2 bytes)
   - Encodes to Opus using audify-plus encoder
   - Sends via UDP with AES-128-CTR encryption
5. **Device plays audio** confirmation

## File Size Reference

Typical file sizes for ~2 second audio:
- PCM: ~96 KB (24000 Hz × 2 sec × 2 bytes)
- After Opus compression: sent as ~200 bytes per 60ms frame

## Troubleshooting

**Audio plays too fast:**
- Verify sample rate is 24000 Hz: `ffprobe mode_story.pcm`
- Re-generate with `-ar 24000` flag

**Audio file not found:**
- Check file exists in `audio/mode_change/` directory
- Verify filename matches `audio_map.json`

**No audio plays:**
- Check UDP connection is established
- Verify Opus encoder is initialized
- Check logs for encryption errors

## Audio Map

The `audio_map.json` file maps mode names to PCM files:

```json
{
  "modes": {
    "Story": "mode_story.pcm",
    "Music": "mode_music.pcm",
    "Tutor": "mode_tutor.pcm",
    "Chat": "mode_chat.pcm"
  }
}
```

If a mode is not found in the map, it uses the default: `mode_changed.pcm`
