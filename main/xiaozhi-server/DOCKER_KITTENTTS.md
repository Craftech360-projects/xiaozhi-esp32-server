# KittenTTS with Docker

## Quick Setup for Docker Users

KittenTTS works seamlessly with Docker! All dependencies including eSpeak-NG are automatically installed in the container.

### 1. Update Configuration

Edit `data/.config.yaml`:

```yaml
selected_module:
  TTS: kittentts  # Change from 'elevenlabs' to 'kittentts'

TTS:
  kittentts:
    model_name: KittenML/kitten-tts-nano-0.1
    voice: expr-voice-5-m  # Choose your preferred voice
    speed: 1.0
    sample_rate: 24000
    format: wav
    output_dir: tmp/
```

### 2. Start the Container

```bash
docker-compose -f docker-compose-local.yml up --build
```

### 3. That's it!

The container will:
- ✅ Install eSpeak-NG automatically
- ✅ Download KittenTTS model on first use
- ✅ Start xiaozhi-server with KittenTTS enabled

## Available Voices

- `expr-voice-2-m` / `expr-voice-2-f` (Male/Female)
- `expr-voice-3-m` / `expr-voice-3-f` (Male/Female)
- `expr-voice-4-m` / `expr-voice-4-f` (Male/Female)
- `expr-voice-5-m` / `expr-voice-5-f` (Male/Female)

## Benefits in Docker

- 🐳 **Zero Setup**: No manual dependency installation
- 🔒 **Isolated**: Doesn't affect your host system
- 📦 **Portable**: Works the same everywhere
- 🚀 **Fast**: Pre-built container with all dependencies

## Troubleshooting

If you encounter issues:

1. **Rebuild the container**:
   ```bash
   docker-compose -f docker-compose-local.yml up --build
   ```

2. **Check logs**:
   ```bash
   docker logs xiaozhi-esp32-server
   ```

3. **Verify configuration**: Make sure `selected_module.TTS: kittentts` is set correctly

## Performance

KittenTTS in Docker provides:
- **Fast startup**: Model loads quickly
- **Low memory**: Only ~25MB model size
- **CPU efficient**: No GPU required
- **Real-time**: Suitable for live conversations