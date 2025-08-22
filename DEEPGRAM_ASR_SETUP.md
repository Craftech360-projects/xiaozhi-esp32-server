# Deepgram ASR Integration Guide

This guide explains how to set up and use Deepgram's Nova-2 ASR (Automatic Speech Recognition) with the Xiaozhi voice assistant system.

## 🎯 Why Deepgram?

Deepgram's Nova-2 is one of the most accurate and fastest ASR models available:

- **🏆 Industry-leading accuracy** - Outperforms most competitors
- **⚡ Ultra-fast processing** - Real-time transcription with low latency  
- **🌍 100+ languages supported** - Including English, Chinese, Spanish, French, German, Japanese, Korean, and more
- **🎛️ Advanced features** - Smart formatting, punctuation, speaker diarization
- **💰 Competitive pricing** - Pay-per-use with generous free tier

## 📋 Prerequisites

1. **Deepgram Account**: Sign up at [console.deepgram.com](https://console.deepgram.com/)
2. **API Key**: Get your API key from the Deepgram console
3. **Python Dependencies**: The required packages are already added to `requirements.txt`

## 🚀 Quick Setup

### Step 1: Get Your API Key

1. Go to [Deepgram Console](https://console.deepgram.com/)
2. Sign up for a free account (includes $200 in free credits)
3. Navigate to **API Keys** section
4. Create a new API key and copy it

### Step 2: Configure Xiaozhi

1. Open `main/xiaozhi-server/config.yaml`
2. Find the `ASR` section and locate `DeepgramASR`
3. Replace `your-deepgram-api-key` with your actual API key:

```yaml
ASR:
  DeepgramASR:
    type: deepgram
    api_key: your-actual-deepgram-api-key-here
    model: nova-2
    language: en  # Change to your preferred language
    smart_format: true
    punctuate: true
    diarize: false
    multichannel: false
    timeout: 60
    output_dir: tmp/
```

### Step 3: Select Deepgram as Your ASR Provider

In the same `config.yaml` file, find the `selected_module` section and change the ASR setting:

```yaml
selected_module:
  ASR: DeepgramASR  # Change this to use Deepgram
```

### Step 4: Install Dependencies

```bash
cd main/xiaozhi-server
pip install -r requirements.txt
```

### Step 5: Test the Integration

Run the test script to verify everything works:

```bash
cd main/xiaozhi-server
python test_deepgram_asr.py
```

## ⚙️ Configuration Options

### Language Support

Deepgram supports 100+ languages. Common language codes:

```yaml
language: en    # English
language: zh    # Chinese (Mandarin)
language: es    # Spanish
language: fr    # French
language: de    # German
language: ja    # Japanese
language: ko    # Korean
language: pt    # Portuguese
language: ru    # Russian
language: it    # Italian
```

### Model Options

```yaml
model: nova-2      # Latest and most accurate (recommended)
model: nova        # Previous generation, still excellent
model: enhanced    # Good balance of speed and accuracy
model: base        # Fastest, good for real-time applications
```

### Advanced Features

```yaml
# Smart formatting (recommended)
smart_format: true    # Adds punctuation, capitalization, number formatting

# Punctuation
punctuate: true       # Adds punctuation marks

# Speaker diarization (identify different speakers)
diarize: true         # Useful for multi-speaker conversations

# Multichannel processing
multichannel: true    # For stereo or multi-channel audio
```

## 🔧 Troubleshooting

### Common Issues

1. **"Invalid API key" error**
   - Double-check your API key in the config file
   - Ensure there are no extra spaces or quotes around the key

2. **"Module not found" error**
   - Run `pip install deepgram-sdk` to install the SDK
   - Make sure you're in the correct directory

3. **Timeout errors**
   - Increase the `timeout` value in config
   - Check your internet connection

4. **Poor transcription quality**
   - Try using `model: nova-2` for best accuracy
   - Enable `smart_format: true` and `punctuate: true`
   - Ensure audio quality is good (16kHz, mono recommended)

### Testing Your Setup

Use the provided test script:

```bash
python test_deepgram_asr.py
```

This will:
- ✅ Check if all dependencies are installed
- ✅ Verify your API key works
- ✅ Test transcription with sample audio
- ✅ Show detailed error messages if something fails

## 💡 Tips for Best Results

1. **Audio Quality**: Use 16kHz sample rate, mono channel for best results
2. **Language Setting**: Set the correct language code for your use case
3. **Smart Format**: Enable smart formatting for better readability
4. **Model Selection**: Use `nova-2` for highest accuracy, `base` for fastest processing

## 📊 Pricing

Deepgram offers competitive pricing:
- **Free Tier**: $200 in credits (approximately 45 hours of audio)
- **Pay-as-you-go**: Starting at $0.0043 per minute
- **Volume discounts**: Available for high usage

Check current pricing at [deepgram.com/pricing](https://deepgram.com/pricing)

## 🆚 Comparison with Other ASR Providers

| Feature | Deepgram Nova-2 | OpenAI Whisper | Google Speech |
|---------|----------------|----------------|---------------|
| Accuracy | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Speed | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| Languages | 100+ | 99 | 125+ |
| Real-time | ✅ | ❌ | ✅ |
| Pricing | $$ | $ | $$$ |

## 🔗 Useful Links

- [Deepgram Console](https://console.deepgram.com/)
- [Deepgram Documentation](https://developers.deepgram.com/)
- [Language Support](https://developers.deepgram.com/docs/language)
- [Model Comparison](https://developers.deepgram.com/docs/model)

## 🎉 You're All Set!

Once configured, your Xiaozhi assistant will use Deepgram's industry-leading ASR for highly accurate speech recognition. The system will automatically:

1. 🎤 Capture audio from your ESP32 device
2. 🔄 Send it to Deepgram for transcription
3. 📝 Return accurate, formatted text
4. 🤖 Process the text with your selected LLM
5. 🔊 Respond with synthesized speech

Enjoy your enhanced voice assistant experience! 🚀