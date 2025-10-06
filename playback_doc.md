Music Playback Flow - Detailed Documentation

  Based on my analysis of the codebase, here's the complete step-by-step flow for playing music from the mobile app:

  Architecture Overview

  The music playback system consists of:
  1. LiveKit Server (Python) - AI agent that processes commands
  2. MQTT Gateway (Node.js) - Bridge between ESP32 devices and LiveKit
  3. Qdrant Cloud - Vector database for music search
  4. AWS CloudFront/S3 - Music file storage and CDN delivery

  ---
  Complete Music Playback Flow

  Phase 1: User Request (Voice/Mobile App)

  Step 1: User initiates music request
  - User says: "Play Baby Shark" or "Play music" (voice)
  - OR user sends MQTT command from mobile app with music request

  Key Files:
  - Mobile app → MQTT → main/mqtt-gateway/app.js

  ---
  Phase 2: Speech-to-Text & AI Processing

  Step 2: LiveKit STT converts voice to text
  - Audio captured from device → LiveKit Room
  - STT (Groq Whisper) transcribes: "Play Baby Shark"
  - Location: main/livekit-server/main.py:246

  Step 3: LLM processes request and calls function
  - LLM (Groq Llama) analyzes transcribed text
  - Determines this is a music request
  - Calls function tool: play_music(song_name="baby shark")
  - Location: main/livekit-server/src/agent/main_agent.py:53-128

  ---
  Phase 3: Music Search & Selection

  Step 4: Music service searches for song
  - Function: play_music() in main_agent.py:53
  - Calls: await self.music_service.search_songs(song_name, language)
  - Location: main/livekit-server/src/services/music_service.py:52-82

  Step 5: Semantic search in Qdrant Cloud
  - Generates embedding for query: "baby shark"
  - Searches Qdrant vector database
  - Uses fuzzy matching for spell tolerance
  - Returns top 5 matches with scores
  - Location: main/livekit-server/src/services/semantic_search.py:234-351

  Search Algorithm:
  # Priority order:
  1. Exact title match (score: 1.0)
  2. Exact romanized match (score: 0.95)
  3. Alternative names match (score: 0.9)
  4. Keyword match (score: 0.85)
  5. Substring matches (score: 0.6-0.8)
  6. Word-level fuzzy matching (score: 0.4-0.6)

  Step 6: Generate CloudFront URL
  - Best match selected from search results
  - URL generated: https://dbtnllz9fcr1z.cloudfront.net/music/{language}/{filename}.mp3
  - Fallback: S3 direct URL if CloudFront fails
  - Location: music_service.py:42-50

  ---
  Phase 4: Audio Download & Streaming

  Step 7: Send music start signal to device
  - Publishes data channel message to MQTT Gateway:
  {
    "type": "music_playback_started",
    "title": "Baby Shark",
    "language": "English",
    "message": "Now playing: Baby Shark"
  }
  - Location: main_agent.py:92-117

  Step 8: Start audio playback
  - Calls: await player.play_from_url(song['url'], song['title'])
  - Uses UnifiedAudioPlayer which streams through LiveKit TTS channel
  - Location: main/livekit-server/src/services/unified_audio_player.py:77-94

  Step 9: Download and convert audio
  - Streaming Mode (default):
    - Downloads MP3 in 64KB chunks
    - Converts MP3 → PCM (48kHz, mono, 16-bit) on-the-fly
    - No full download required
    - Location: unified_audio_player.py:150-198
  - Fallback Mode (if streaming fails):
    - Downloads full MP3 file
    - Converts to PCM using pydub
    - Location: unified_audio_player.py:200-241

  Step 10: Create audio frames
  - Converts PCM to LiveKit AudioFrames
  - 48kHz sample rate, 20ms frames (960 samples)
  - Async iterator pattern for streaming
  - Location: unified_audio_player.py:327-366 (AudioFrameIterator)

  ---
  Phase 5: LiveKit Transmission

  Step 11: Inject frames into TTS channel
  - Uses session.say() with audio frames:
  speech_handle = self.session.say(
      text="",  # Empty text - no TTS
      audio=audio_frames,  # Pre-recorded audio
      allow_interruptions=True,
      add_to_chat_ctx=False
  )
  - Location: unified_audio_player.py:112-126

  Step 12: LiveKit transmits audio to room
  - Audio frames sent to LiveKit Room
  - All participants receive audio track
  - Real-time streaming at 48kHz

  ---
  Phase 6: MQTT Gateway Processing

  Step 13: MQTT Gateway receives audio track
  - Subscribes to agent's audio track
  - Receives 48kHz PCM audio frames
  - Location: main/mqtt-gateway/app.js:320-373

  Step 14: Audio resampling (48kHz → 24kHz)
  - Downsamples from 48kHz to 24kHz for ESP32 efficiency
  - Uses LiveKit AudioResampler
  - Location: app.js:93-94

  Step 15: Frame buffering (20ms → 60ms)
  - Accumulates resampled audio into 60ms frames
  - Target: 1440 samples (60ms at 24kHz) = 2880 bytes
  - Location: app.js:95-99

  Step 16: Opus encoding
  - Encodes 24kHz PCM → Opus compressed format
  - Uses audify-plus Opus encoder
  - Significantly reduces bandwidth
  - Location: app.js:46-60 (encoder init)

  ---
  Phase 7: Device Delivery

  Step 17: Send Opus packets to device
  - Forwards Opus frames via UDP to ESP32 device
  - Protocol: Custom UDP audio protocol
  - Location: MQTT gateway UDP sender

  Step 18: Device receives and decodes
  - ESP32 receives Opus packets
  - Decodes Opus → PCM
  - Plays through speaker/DAC

  ---
  Phase 8: Playback Control Signals

  Throughout playback, these signals are sent:

  Music Start Signal (main_agent.py:92-117):
  {
    "type": "music_playback_started",
    "title": "Baby Shark",
    "language": "English"
  }

  Agent State Changes (unified_audio_player.py:306-324):
  {
    "type": "agent_state_changed",
    "data": {
      "old_state": "listening",
      "new_state": "speaking"
    }
  }

  Music End Signal (unified_audio_player.py:268-282):
  {
    "type": "music_playback_stopped"
  }

  Completion Message (after music ends):
  - TTS message: "That was Baby Shark. What would you like to hear next?"
  - Location: unified_audio_player.py:284-304

  ---
  Phase 9: Stop Music (User Interruption)

  Step 19: User says "Stop music"
  - LLM calls: stop_audio() function
  - Location: main_agent.py:182-271

  Step 20: Immediate stop sequence
  1. Set stop event (stops frame iteration immediately)
  2. Interrupt session.say() speech handle
  3. Cancel background playback task
  4. Clear audio state manager
  5. Send music_playback_stopped signal
  6. Send agent state → listening
  - Location: unified_audio_player.py:48-75

  ---
  Mobile App Integration Guide

  Option 1: Voice Command (Recommended)

  User speaks → Device captures audio → MQTT Gateway → LiveKit → AI processes → Music plays

  Option 2: Direct MQTT Command

  Send MQTT message to trigger music:

  {
    "type": "play_music_request",
    "song_name": "Baby Shark",  // Optional
    "language": "English"        // Optional
  }

  Implementation needed in MQTT Gateway:
  - Add handler in app.js DataReceived event
  - Forward to LiveKit agent via data channel
  - Agent processes as function call

  Option 3: LiveKit Data Channel (Direct)

  Publish data to LiveKit room:

  await room.localParticipant.publishData(
    JSON.stringify({
      type: "music_command",
      action: "play",
      song_name: "Baby Shark"
    }).encode(),
    topic: "music_control"
  );

  ---
  Key Files Reference

  | Component       | File                                                     | Purpose                          |
  |-----------------|----------------------------------------------------------|----------------------------------|
  | Main Agent      | main/livekit-server/src/agent/main_agent.py              | Function tools for music/stories |
  | Music Service   | main/livekit-server/src/services/music_service.py        | Music search & URL generation    |
  | Semantic Search | main/livekit-server/src/services/semantic_search.py      | Qdrant vector search             |
  | Audio Player    | main/livekit-server/src/services/unified_audio_player.py | Audio streaming & playback       |
  | MQTT Gateway    | main/mqtt-gateway/app.js                                 | Bridge to ESP32 devices          |
  | Entry Point     | main/livekit-server/main.py                              | Service initialization           |

  ---
  API Endpoints for Mobile App

  Trigger Music via Voice

  Mobile App → MQTT → Device → Voice Input → AI Agent → Music

  Trigger Music Programmatically

  Add this handler to mqtt-gateway/app.js (DataReceived section):

  case "mobile_music_request":
    console.log(`🎵 [MOBILE] Music request: ${data.song_name}`);
    // Forward to LiveKit agent
    await this.room.localParticipant.publishData(
      JSON.stringify({
        type: "function_call",
        function_call: {
          name: "play_music",
          arguments: {
            song_name: data.song_name,
            language: data.language
          }
        }
      }).encode(),
      topic: "mcp_function_call"
    );
    break;

  ---
  Environment Variables Required

  # Qdrant (Music Search)
  QDRANT_URL=https://your-qdrant-cloud.qdrant.io
  QDRANT_API_KEY=your_api_key

  # CloudFront CDN
  CLOUDFRONT_DOMAIN=dbtnllz9fcr1z.cloudfront.net
  S3_BASE_URL=https://cheeko-audio-files.s3.us-east-1.amazonaws.com
  USE_CDN=true

  # LiveKit
  LIVEKIT_URL=wss://your-livekit.cloud
  LIVEKIT_API_KEY=your_key
  LIVEKIT_API_SECRET=your_secret

  ---
  Music Collection Structure

  Music stored in Qdrant with this schema:

  {
    "title": "Baby Shark",
    "filename": "baby_shark.mp3",
    "language": "English",
    "romanized": "baby shark",
    "alternatives": ["baby shark song", "baby shark dance"],
    "keywords": ["kids", "dance", "fun"],
    "searchable_text": "Baby Shark baby shark baby shark song..."
  }

  Supported Languages: English, Hindi, Telugu, Tamil, Malayalam, Kannada, Bengali

  ---
  This documentation provides the complete end-to-end flow! You can trigger music playback from the mobile app by:
  1. Voice commands (natural language)
  2. Adding MQTT message handler (requires code change in mqtt-gateway)
  3. Direct LiveKit data channel messages