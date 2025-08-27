# Multilingual STT Solution for Regional Language Song Names

## Problem Analysis

When you say "play Aane banthondu Aane" (Kannada song), the current STT system:
1. Uses `language: en-IN` configuration in Deepgram
2. Tries to transcribe Kannada words as English phonetics
3. Results in poor transcription like "play aan bantondo aan"
4. LLM and music matcher can't find the correct song

## Solution: Deepgram Multilingual Code-Switching

Based on Deepgram's documentation, we can implement multilingual support using:

### 1. Multi-Language Detection
Configure Deepgram to detect and transcribe multiple languages simultaneously:

```yaml
DeepgramASR:
  type: deepgram
  api_key: your_api_key
  model: nova-3
  # Remove single language, use detect_language instead
  detect_language: true
  # Or specify multiple languages
  language: ["en-IN", "hi", "kn", "te", "ta"]  # English-India, Hindi, Kannada, Telugu, Tamil
  smart_format: true
  punctuate: true
  code_switching: true  # Enable code-switching support
```

### 2. Language-Aware Processing
The system should:
- Detect the primary language of the utterance
- Handle code-switching within the same sentence
- Preserve original script/romanization for better matching

### 3. Enhanced Music Matching
Improve the multilingual matcher to handle:
- Mixed language requests: "play Aane banthondu Aane"
- Phonetic variations from STT
- Cross-script matching (Devanagari, Kannada script, etc.)

## Implementation Steps

### Step 1: Update Deepgram Configuration
### Step 2: Modify ASR Provider
### Step 3: Enhance Multilingual Matcher
### Step 4: Add Phonetic Matching
### Step 5: Test with Regional Languages

## Expected Results

After implementation:
- "play Aane banthondu Aane" → Correctly transcribed in Kannada/romanized
- Better matching with metadata entries
- Support for mixed language requests
- Improved accuracy for all regional languages