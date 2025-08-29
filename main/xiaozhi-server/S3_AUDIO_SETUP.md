# S3 Audio Streaming Setup Guide

This guide explains how to set up S3 audio streaming for xiaozhi-server.

## 🔐 Security Setup (IMPORTANT!)

### 1. Create New AWS Credentials
**NEVER use the credentials you shared in chat - they are compromised!**

1. Go to AWS IAM Console
2. **Revoke the old access keys immediately**
3. Create a new IAM user with S3 read permissions
4. Generate new access keys

### 2. Set Up Environment Variables
Create a `.env` file in the xiaozhi-server directory:

```bash
# Copy .env.example to .env
cp .env.example .env
```

Edit `.env` with your NEW credentials:
```
AWS_ACCESS_KEY_ID=your_new_access_key_here
AWS_SECRET_ACCESS_KEY=your_new_secret_key_here
AWS_DEFAULT_REGION=us-east-1
S3_BUCKET_NAME=cheeko-audio-files
```

## 📦 Installation

Install required packages:
```bash
pip install -r requirements.txt
```

## 🗂️ Directory Structure

Your xiaozhi-server should have:
```
xiaozhi-server/
├── music/
│   ├── Hindi/metadata.json
│   ├── Kannada/metadata.json
│   └── English/metadata.json
├── stories/
│   ├── Fantasy/metadata.json
│   └── Adventure/metadata.json
├── s3_audio_player.py
├── test_s3_audio.py
└── .env
```

S3 bucket structure:
```
cheeko-audio-files/
├── music/
│   ├── Hindi/
│   │   ├── song1.mp3
│   │   └── song2.mp3
│   └── Kannada/
│       └── song3.mp3
└── stories/
    └── Fantasy/
        ├── story1.mp3
        └── story2.mp3
```

## 🧪 Testing

Test the setup:
```bash
python test_s3_audio.py
```

## 🎵 Usage Examples

```python
from s3_audio_player import S3AudioPlayer

# Initialize player
player = S3AudioPlayer()

# Play music
result = player.play_music("Hindi", "bandar mama")
print(result)  # "Playing: Bandar Mama Aur Kele"

# Play story
result = player.play_story("Fantasy", "cat portrait")
print(result)  # "Playing story: A Portrait of a Cat"

# List available content
print("Music languages:", player.list_available_music())
print("Story categories:", player.list_available_stories())
```

## 🔧 Integration with Main App

In your main application (app.py), you can integrate like this:

```python
from s3_audio_player import S3AudioPlayer

# Initialize once
audio_player = S3AudioPlayer()

# In your voice command handler
def handle_voice_command(command):
    if "play music" in command.lower():
        # Extract language and song from command
        # Example: "play hindi music bandar mama"
        parts = command.lower().split()
        if len(parts) >= 4:
            language = parts[2]
            song = " ".join(parts[3:])
            result = audio_player.play_music(language, song)
            return result
    
    elif "play story" in command.lower():
        # Example: "play fantasy story cat"
        parts = command.lower().split()
        if len(parts) >= 4:
            category = parts[2]
            story = " ".join(parts[3:])
            result = audio_player.play_story(category, story)
            return result
```

## 🛡️ Security Features

- ✅ Credentials stored in environment variables (not in code)
- ✅ Presigned URLs with 1-hour expiration
- ✅ Fallback to public URLs if needed
- ✅ Error handling for network issues
- ✅ Logging for debugging

## 🚀 Benefits

- **Storage Efficient**: No large audio files on server
- **Scalable**: Easy to add new content to S3
- **Fast Search**: Metadata stays local for instant search
- **Secure**: Temporary URLs with expiration
- **Reliable**: Fallback mechanisms for network issues