# LiveKit Background Audio Examples

This directory contains example scripts demonstrating how to use **background audio** and **foreground audio** in LiveKit voice agents.

## Audio Types Explained

### Foreground Audio (Agent's Voice)
- The main TTS (Text-to-Speech) output from the agent
- What the agent "says" to the user
- Configured via the `tts` parameter in `AgentSession`
- Examples: OpenAI TTS, ElevenLabs, Cartesia, etc.

### Background Audio (Separate Track)
- Played on a separate audio track using `BackgroundAudioPlayer`
- Does NOT interfere with the agent's speech
- Can include:
  - **Ambient sounds**: Continuous background noise (office ambience, music, etc.)
  - **Thinking sounds**: Plays when agent is processing (keyboard typing, etc.)
  - **On-demand sounds**: Sound effects triggered programmatically

## Available Scripts

### 1. `background_audio_example.py` (Basic)
Simple example showing:
- Ambient office noise playing continuously
- Thinking sounds when agent processes
- Agent greeting with TTS (foreground audio)

**Run:**
```bash
python background_audio_example.py start
```

### 2. `background_audio_advanced.py` (Advanced)
Advanced example with:
- Function tools to control background audio
- Play notification sounds on demand
- Play thinking indicators with duration control
- Agent can trigger sound effects via LLM tool calls

**Run:**
```bash
# Run the agent
python background_audio_advanced.py start

# Test audio configuration
python background_audio_advanced.py test
```

## Setup Requirements

### 1. Install Dependencies
```bash
pip install livekit-agents livekit-plugins-openai livekit-plugins-silero
```

### 2. Environment Variables
```bash
export LIVEKIT_URL=wss://your-livekit-server.com
export LIVEKIT_API_KEY=your-api-key
export LIVEKIT_API_SECRET=your-api-secret
export OPENAI_API_KEY=your-openai-key
```

Or create a `.env` file:
```env
LIVEKIT_URL=wss://your-livekit-server.com
LIVEKIT_API_KEY=your-api-key
LIVEKIT_API_SECRET=your-api-secret
OPENAI_API_KEY=your-openai-key
```

## Audio Sources

The `BackgroundAudioPlayer` supports multiple audio sources:

### Built-in Audio Clips
```python
from livekit.agents import BuiltinAudioClip

BuiltinAudioClip.OFFICE_AMBIENCE    # Office background noise
BuiltinAudioClip.KEYBOARD_TYPING    # Keyboard typing sound
BuiltinAudioClip.KEYBOARD_TYPING2   # Shorter typing sound
```

### Local Audio Files
```python
# Supports: MP3, WAV, AAC, FLAC, OGG, Opus, WebM, MP4
background_audio.play("/path/to/your-audio.mp3")
background_audio.play("./sounds/notification.wav")
```

### Custom Audio Frames
```python
# For advanced use cases
async def audio_generator():
    # Generate or stream audio frames
    yield rtc.AudioFrame(...)

background_audio.play(audio_generator())
```

## Usage Patterns

### Basic Background Player
```python
from livekit.agents import BackgroundAudioPlayer, AudioConfig, BuiltinAudioClip

background_audio = BackgroundAudioPlayer(
    ambient_sound=AudioConfig(
        BuiltinAudioClip.OFFICE_AMBIENCE,
        volume=0.3
    ),
    thinking_sound=AudioConfig(
        BuiltinAudioClip.KEYBOARD_TYPING,
        volume=0.6
    )
)

# Start after session.start()
await background_audio.start(room=ctx.room, agent_session=session)
```

### Play Sound On-Demand
```python
# Play once
background_audio.play("/path/to/notification.mp3")

# Play and wait for completion
await background_audio.play("/path/to/sound.wav")

# Play on loop
handle = background_audio.play("/path/to/music.mp3", loop=True)

# Stop early
await asyncio.sleep(5)
handle.stop()
```

### Multiple Audio Clips (Randomized)
```python
# Play random sounds with probabilities
background_audio = BackgroundAudioPlayer(
    thinking_sound=[
        AudioConfig(BuiltinAudioClip.KEYBOARD_TYPING, volume=0.8, probability=0.5),
        AudioConfig(BuiltinAudioClip.KEYBOARD_TYPING2, volume=0.7, probability=0.3),
        # 20% chance of silence (1.0 - 0.5 - 0.3)
    ]
)
```

## Common Use Cases

### 1. Hold Music (Call Transfer)
```python
# Put caller on hold with music
hold_audio = BackgroundAudioPlayer()
await hold_audio.start(room=ctx.room, agent_session=session)
await hold_audio.play("/path/to/hold-music.mp3", loop=True)
```

### 2. Game Sound Effects
```python
# Play victory sound
background_audio.play("/sounds/victory.wav")

# Play defeat sound
background_audio.play("/sounds/defeat.mp3")
```

### 3. Notification/Alert Sounds
```python
# Play alert when important event occurs
background_audio.play(
    AudioConfig(BuiltinAudioClip.KEYBOARD_TYPING2, volume=0.9)
)
```

### 4. Restaurant Ambience
```python
# Create realistic restaurant agent
background_audio = BackgroundAudioPlayer(
    ambient_sound="/sounds/restaurant-noise.mp3"
)
```

## Key Points

1. **Separate Tracks**: Background audio is published on a different audio track than the agent's TTS output
2. **No Interference**: Background and foreground audio play simultaneously without mixing issues
3. **Automatic Lifecycle**: Thinking sounds automatically play when agent is processing
4. **Volume Control**: Adjust volume per audio clip to balance levels
5. **Probability**: Randomize sounds to avoid repetition

## Troubleshooting

### Background audio not playing
- Ensure `background_audio.start()` is called AFTER `session.start()`
- Check that room connection is established (`await ctx.connect()`)
- Verify audio file paths are correct

### Audio too loud/quiet
- Adjust `volume` parameter in `AudioConfig` (0.0 to 1.0)
- Typical values: ambient=0.2-0.4, thinking=0.5-0.7, effects=0.7-0.9

### Thinking sounds not triggering
- Ensure `thinking_sound` is configured in `BackgroundAudioPlayer`
- Thinking sounds only play when agent is in "thinking" state (processing LLM response)

## Additional Resources

- [LiveKit Agents Documentation](https://docs.livekit.io/agents/build/audio/)
- [Background Audio Example](https://github.com/livekit/agents/blob/main/examples/voice_agents/background_audio.py)
- [Audio Sources Documentation](https://docs.livekit.io/agents/build/audio/#audio-sources)

## Next Steps

1. Try the basic example first to understand the concept
2. Experiment with different audio files and volumes
3. Use the advanced example to see dynamic control
4. Integrate into your existing agent implementation
