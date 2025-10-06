# Mode Change Audio Files

This directory contains pre-recorded Opus audio files for mode change confirmations.

## Audio Format Requirements

- **Codec:** Opus
- **Sample Rate:** 24000 Hz (24 kHz)
- **Channels:** 1 (Mono)
- **Frame Duration:** 60ms
- **Bitrate:** 24 kbps (recommended for voice)

## Required Audio Files

Place your Opus audio files in this directory with these names:

### Mode-Specific Files:
- `mode_cheeko.opus` - "Switched to Cheeko mode"
- `mode_rhymetime.opus` - "Switched to RhymeTime mode"
- `mode_storyteller.opus` - "Switched to Storyteller mode"
- `mode_teacher.opus` - "Switched to Teacher mode"
- `mode_friend.opus` - "Switched to Friend mode"

### Fallback Files:
- `mode_changed.opus` - Generic "Mode changed" (default)
- `mode_error.opus` - "Error changing mode"
- `only_one_mode.opus` - "Only one mode available"

## How to Create Opus Files

### Option 1: Using FFmpeg
```bash
# Convert from WAV/MP3 to Opus (24kHz mono)
ffmpeg -i input.wav -c:a libopus -b:a 24k -ar 24000 -ac 1 -frame_duration 60 mode_cheeko.opus
```

### Option 2: Using Edge TTS (Generate from Text)
```bash
# Install edge-tts
pip install edge-tts

# Generate audio
edge-tts --voice "en-US-AndrewNeural" --text "Switched to Cheeko mode" --write-media mode_cheeko.mp3

# Convert to Opus
ffmpeg -i mode_cheeko.mp3 -c:a libopus -b:a 24k -ar 24000 -ac 1 mode_cheeko.opus
```

### Option 3: Using Online TTS
1. Generate WAV/MP3 from any TTS service
2. Convert to Opus using FFmpeg command above

## File Naming Convention

File names must match the mode names (case-insensitive) with `mode_` prefix:
- Mode name: "RhymeTime" → File: `mode_rhymetime.opus`
- Mode name: "Cheeko" → File: `mode_cheeko.opus`

## Testing Your Files

```bash
# Play Opus file (requires VLC or ffplay)
ffplay mode_cheeko.opus

# Get file info
ffprobe mode_cheeko.opus
```

## Notes

- **Max file size:** Keep under 500KB for fast streaming
- **Duration:** 1-3 seconds recommended
- **Voice:** Use consistent voice across all files
- **Volume:** Normalize all files to same volume level
