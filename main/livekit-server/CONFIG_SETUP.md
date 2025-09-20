# LiveKit Server Configuration Setup

## Quick Setup

1. Copy the template configuration:
   ```bash
   cp config.yaml.template config.yaml
   ```

2. Edit `config.yaml` and replace the placeholder API keys:
   - `YOUR_GROQ_API_KEY_HERE` - Get from https://console.groq.com/keys
   - `YOUR_GOOGLE_API_KEY_HERE` - Get from Google Cloud Console
   - `YOUR_DEEPGRAM_API_KEY_HERE` - Get from https://console.deepgram.com/
   - `YOUR_ELEVENLABS_API_KEY_HERE` - Get from https://elevenlabs.io/
   - `YOUR_QDRANT_URL_HERE` - Your Qdrant instance URL
   - `YOUR_QDRANT_API_KEY_HERE` - Your Qdrant API key

3. The configuration is set to fetch models from the manager-api backend (`read_config_from_api: true`)

## Backend Integration

This LiveKit agent is configured to fetch model configurations from the Java backend at `http://localhost:8080`.

- Models are fetched from the dashboard/database through the manager-api
- No fallback to environment variables or static YAML configuration
- Automatic synchronization with dashboard model changes

## Security

- `config.yaml` is in `.gitignore` to prevent committing API keys
- Always use the template file for version control