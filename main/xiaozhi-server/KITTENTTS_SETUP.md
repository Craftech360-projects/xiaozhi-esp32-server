# KittenTTS Setup Guide for xiaozhi-server

## Quick Setup

### For Docker Users
If you're using Docker, eSpeak-NG is automatically installed in the container. Just:

1. **Update configuration**:
   Edit `data/.config.yaml` and change:
   ```yaml
   selected_module:
     TTS: kittentts  # Change from 'elevenlabs' to 'kittentts'
   ```

2. **Start with Docker**:
   ```bash
   docker-compose -f docker-compose-local.yml up
   ```

### For Local Installation

1. **Install eSpeak-NG** (Required for phonemization):
   - **Windows**: Run `install_espeak_windows.bat` or see `WINDOWS_ESPEAK_INSTALL.md`
   - **Linux**: `sudo apt-get install espeak-ng` or `sudo yum install espeak-ng`
   - **macOS**: `brew install espeak-ng`

2. **Install dependencies**:
   ```bash
   cd main/xiaozhi-server
   python install_kittentts.py
   ```

3. **Update configuration**:
   Edit `data/.config.yaml` and change:
   ```yaml
   selected_module:
     TTS: kittentts  # Change from 'elevenlabs' to 'kittentts'
   ```

4. **Test the setup**:
   ```bash
   python test_kittentts.py
   ```

5. **Start xiaozhi-server**:
   ```bash
   python app.py
   ```

## Configuration Options

The KittenTTS configuration is already added to your `data/.config.yaml`:

```yaml
TTS:
  kittentts:
    model_name: KittenML/kitten-tts-nano-0.1
    voice: expr-voice-5-m  # Available: expr-voice-2-m/f, expr-voice-3-m/f, etc.
    speed: 1.0  # 0.5-2.0
    sample_rate: 24000
    format: wav
    output_dir: tmp/
```

## Available Voices

- `expr-voice-2-m` / `expr-voice-2-f` (Male/Female)
- `expr-voice-3-m` / `expr-voice-3-f` (Male/Female)  
- `expr-voice-4-m` / `expr-voice-4-f` (Male/Female)
- `expr-voice-5-m` / `expr-voice-5-f` (Male/Female)

## Benefits

✅ **No API costs** - Completely free  
✅ **Privacy** - Runs locally, no data sent to servers  
✅ **Offline** - Works without internet (after initial model download)  
✅ **Lightweight** - Only 25MB model size  
✅ **Fast** - Optimized for real-time synthesis  
✅ **CPU-only** - No GPU required  

## Troubleshooting

If you encounter issues:

1. **Missing dependencies**: Run `python install_kittentts.py`
2. **Import errors**: Check that KittenTTS folder exists in project root
3. **Model download fails**: Ensure internet connection for first run
4. **Test the setup**: Run `python test_kittentts.py`

For detailed documentation, see: `docs/kittentts-integration.md`