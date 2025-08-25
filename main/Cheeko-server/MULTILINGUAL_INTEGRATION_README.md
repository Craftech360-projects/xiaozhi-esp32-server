# Multilingual AI Music & Story Player Integration

This document explains the enhanced multilingual functionality integrated into your Xiaozhi ESP32 server for both music and story playback.

## 🎯 Overview

The integration adds AI-powered multilingual support to your `play_music` and `play_story` functions, enabling:

- **Natural language understanding** in multiple languages
- **Intelligent content matching** using fuzzy search and metadata
- **Cross-script support** (e.g., user says "Hanuman Chalisa" in English, finds Hindi file)
- **Contextual responses** based on matching method and user request
- **Fallback mechanisms** to ensure content always plays

## 🏗️ Architecture

### Core Components

1. **MultilingualMatcher** (`plugins_func/utils/multilingual_matcher.py`)

   - Handles metadata.json parsing from language folders
   - Performs fuzzy matching across languages and scripts
   - Supports romanization and alternative name matching

2. **Enhanced play_music** (`plugins_func/functions/play_music.py`)

   - AI-powered music selection with multilingual support
   - Contextual introductions based on matching method
   - Backward compatibility with existing functionality

3. **Enhanced play_story** (`plugins_func/functions/play_story.py`)
   - Intelligent story matching and selection
   - Category-based and specific story requests
   - Multilingual story support (when metadata available)

## 📁 File Structure

```
main/Cheeko-server/
├── music/
│   ├── English/
│   │   ├── metadata.json          # English music metadata
│   │   └── *.mp3                  # English music files
│   ├── Hindi/
│   │   ├── metadata.json          # Hindi music metadata
│   │   └── *.mp3                  # Hindi music files
│   └── [Other Languages]/
├── stories/
│   ├── Bedtime/
│   │   ├── metadata.json          # (Optional) Bedtime story metadata
│   │   └── *.mp3                  # Bedtime story files
│   └── [Other Categories]/
└── plugins_func/
    ├── functions/
    │   ├── play_music.py           # Enhanced music player
    │   └── play_story.py           # Enhanced story player
    └── utils/
        └── multilingual_matcher.py # Core matching engine
```

## 🔧 Configuration

### metadata.json Format

Each language folder should contain a `metadata.json` file:

```json
{
  "Song Title": {
    "romanized": "Song Title",
    "filename": "Song_Title.mp3",
    "alternatives": ["Alternative Name 1", "Alternative Name 2"]
  }
}
```

### Example for Hindi Music

```json
{
  "हनुमान चालीसा": {
    "romanized": "Hanuman Chalisa",
    "filename": "Hanuman Chalisa .mp3",
    "alternatives": ["Hanuman Chalisa", "Hanuman Chalisha"]
  }
}
```

## 🎵 Music Player Features

### Enhanced Function Parameters

```python
play_music(
    user_request: str,           # Full user request
    song_type: str,              # "specific", "random", "language_specific", "educational"
    language_preference: str     # Optional language hint
)
```

### Supported Requests

- **Specific songs**: "play Baa Baa Black Sheep", "sing Hanuman Chalisa"
- **Language requests**: "play Hindi song", "any Telugu music"
- **Educational content**: "play phonics", "alphabet songs"
- **Mood-based**: "something energetic", "calm music"

### Matching Methods

1. **AI Multilingual**: Uses metadata.json for exact and fuzzy matching
2. **Language Random**: Random selection from specified language
3. **Legacy Language**: Folder-based language detection
4. **Legacy Fuzzy**: Filename-based fuzzy matching
5. **Random Fallback**: Random selection when no match found

## 📚 Story Player Features

### Enhanced Function Parameters

```python
play_story(
    user_request: str,           # Full user request
    story_type: str,             # "specific", "category", "random"
    category_preference: str,    # Optional category hint
    requested_language: str      # Optional language hint
)
```

### Supported Requests

- **Specific stories**: "tell me The Boy Who Cried Wolf"
- **Category requests**: "bedtime story", "fantasy story", "educational story"
- **Language requests**: "story in Hindi", "English story"
- **General requests**: "tell me a story", "any story"

### Story Categories

- Bedtime
- Fantasy
- Fairy Tales
- Educational
- Adventure

## 🧪 Testing

Run the test script to verify integration:

```bash
cd main/Cheeko-server
python test_multilingual_integration.py
```

The test will:

- Verify metadata.json loading
- Test language detection
- Test content matching
- Show available content by language

## 🔄 Migration from Legacy System

### Automatic Fallback

The new system maintains **100% backward compatibility**:

1. If metadata.json is not found, falls back to filesystem scanning
2. Legacy function calls still work with new parameter defaults
3. Existing voice commands continue to function

### Gradual Migration

1. **Phase 1**: Use new system with existing files (no metadata needed)
2. **Phase 2**: Add metadata.json to music language folders
3. **Phase 3**: Add metadata.json to story category folders (optional)

## 🎯 User Experience Improvements

### Before Integration

- User: "play Hanuman Chalisa"
- System: Random music or no match

### After Integration

- User: "play Hanuman Chalisa"
- System: "Perfect! I found 'Hanuman Chalisa' in Hindi for you!" → Plays correct song

### Contextual Responses

The system now provides contextual introductions:

- **AI Match**: "Perfect! I found 'Baby Shark Dance' which matches your request!"
- **Language Selection**: "Here's a lovely Hindi song for you: 'Lakdi Ki Kathi'!"
- **Category Match**: "Here's a wonderful bedtime story: 'The Sleepy Bear'!"

## 🔧 Dependencies

New dependencies added to `requirements.txt`:

```
fuzzywuzzy==0.18.0
python-Levenshtein==0.21.1
```

## 🐛 Troubleshooting

### Common Issues

1. **No matches found**

   - Check metadata.json format
   - Verify file paths in metadata match actual files
   - Check file extensions in configuration

2. **Encoding issues**

   - Ensure metadata.json is saved as UTF-8
   - Check for BOM (Byte Order Mark) issues

3. **Performance issues**
   - Large metadata files may slow matching
   - Consider reducing alternatives list size

### Debug Mode

Enable debug logging in your configuration:

```yaml
log:
  log_level: DEBUG
  module_levels:
    play_music: DEBUG
    play_story: DEBUG
```

## 🚀 Future Enhancements

### Planned Features

1. **Learning System**: Track user preferences and improve matching
2. **Voice Feedback**: "I like this song" to improve recommendations
3. **Playlist Generation**: Create smart playlists based on mood/activity
4. **Multi-language Stories**: Support for stories in multiple languages
5. **Content Tagging**: Enhanced metadata with mood, energy, age-group tags

### Adding New Languages

1. Create new language folder in `music/` or `stories/`
2. Add audio files to the folder
3. Create `metadata.json` with proper mappings
4. Update language detection patterns in `MultilingualMatcher`

## 📞 Support

If you encounter issues:

1. Run the test script to verify setup
2. Check logs for detailed error messages
3. Verify metadata.json format and encoding
4. Ensure file paths match between metadata and filesystem

The integration is designed to be robust and provide fallbacks, so your system should continue working even if some components fail.
