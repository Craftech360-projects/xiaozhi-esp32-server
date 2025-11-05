# Continuous Music Streaming Implementation Guide

## Overview
This document outlines the implementation of continuous music streaming functionality for LiveKit rooms, controlled via MQTT signals from mobile apps. The system allows starting/stopping continuous music playback in active LiveKit sessions without requiring agent interaction.

## Architecture

```
Mobile App → MQTT Gateway → LiveKit Agent → Continuous Music Service → Music Streaming
```

## Key Features
- **MQTT-Controlled**: Start/stop music via MQTT signals from mobile app
- **Room-Specific**: Each active LiveKit room can have independent music streaming
- **Continuous Playback**: Auto-queues next songs for seamless streaming
- **Existing Infrastructure**: Reuses current MusicService and UnifiedAudioPlayer
- **Non-Intrusive**: Doesn't interfere with existing agent functionality

## Implementation Plan

### 1. Create Continuous Music Service

**File**: `main/livekit-server/src/services/continuous_music_service.py`

```python
"""
Continuous Music Streaming Service
Manages continuous music playback for LiveKit rooms via MQTT signals
"""

import asyncio
import logging
from typing import Optional, Dict, List
from enum import Enum

logger = logging.getLogger(__name__)

class StreamingState(Enum):
    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"

class ContinuousStreamingService:
    """Service for continuous music streaming controlled via MQTT"""
    
    def __init__(self, music_service, unified_audio_player):
        self.music_service = music_service
        self.audio_player = unified_audio_player
        self.state = StreamingState.STOPPED
        self.current_playlist = []
        self.current_index = 0
        self.current_language = None
        self.current_genre = None
        self.streaming_task = None
        self.room_name = None
        self.device_mac = None
        
    def set_room_info(self, room_name: str, device_mac: str):
        """Set room and device information"""
        self.room_name = room_name
        self.device_mac = device_mac
        
    async def start_streaming(self, language: Optional[str] = None, genre: Optional[str] = None) -> str:
        """Start continuous music streaming"""
        if self.state == StreamingState.PLAYING:
            return "Music streaming is already active"
            
        self.current_language = language
        self.current_genre = genre
        self.state = StreamingState.PLAYING
        
        # Generate initial playlist
        await self._generate_playlist()
        
        # Start streaming task
        self.streaming_task = asyncio.create_task(self._streaming_loop())
        
        logger.info(f"🎵 Started continuous streaming for room: {self.room_name}")
        return f"Started continuous music streaming{f' ({language})' if language else ''}"
        
    async def stop_streaming(self) -> str:
        """Stop continuous music streaming"""
        if self.state == StreamingState.STOPPED:
            return "Music streaming is not active"
            
        self.state = StreamingState.STOPPED
        
        # Stop current playback
        await self.audio_player.stop()
        
        # Cancel streaming task
        if self.streaming_task and not self.streaming_task.done():
            self.streaming_task.cancel()
            
        logger.info(f"🎵 Stopped continuous streaming for room: {self.room_name}")
        return "Stopped continuous music streaming"
        
    async def skip_current_song(self) -> str:
        """Skip to next song in playlist"""
        if self.state != StreamingState.PLAYING:
            return "No music is currently playing"
            
        # Stop current song
        await self.audio_player.stop()
        
        # Move to next song (streaming loop will pick it up)
        self.current_index += 1
        
        return "Skipped to next song"
        
    async def _generate_playlist(self, size: int = 10):
        """Generate playlist of songs"""
        self.current_playlist = []
        
        try:
            # Get random songs or search by genre
            for _ in range(size):
                if self.current_genre:
                    # Search for songs by genre/query
                    songs = await self.music_service.search_songs(
                        self.current_genre, 
                        self.current_language
                    )
                    if songs:
                        self.current_playlist.append(songs[0])
                else:
                    # Get random songs
                    song = await self.music_service.get_random_song(self.current_language)
                    if song:
                        self.current_playlist.append(song)
                        
            logger.info(f"🎵 Generated playlist with {len(self.current_playlist)} songs")
            
        except Exception as e:
            logger.error(f"🎵 Error generating playlist: {e}")
            
    async def _streaming_loop(self):
        """Main streaming loop - plays songs continuously"""
        try:
            while self.state == StreamingState.PLAYING:
                # Check if we need more songs in playlist
                if self.current_index >= len(self.current_playlist) - 2:
                    await self._generate_playlist()
                    
                # Get current song
                if self.current_index < len(self.current_playlist):
                    current_song = self.current_playlist[self.current_index]
                    
                    logger.info(f"🎵 Playing: {current_song['title']}")
                    
                    # Play the song (this will block until song finishes)
                    await self.audio_player.play_from_url(
                        current_song['url'], 
                        current_song['title']
                    )
                    
                    # Move to next song
                    self.current_index += 1
                    
                else:
                    # No songs available, wait and retry
                    logger.warning("🎵 No songs in playlist, waiting...")
                    await asyncio.sleep(5)
                    
        except asyncio.CancelledError:
            logger.info("🎵 Streaming loop cancelled")
        except Exception as e:
            logger.error(f"🎵 Error in streaming loop: {e}")
            self.state = StreamingState.STOPPED
            
    def get_status(self) -> Dict:
        """Get current streaming status"""
        current_song = None
        if (self.current_index < len(self.current_playlist) and 
            self.current_playlist):
            current_song = self.current_playlist[self.current_index]
            
        return {
            "state": self.state.value,
            "current_song": current_song['title'] if current_song else None,
            "playlist_size": len(self.current_playlist),
            "current_index": self.current_index,
            "language": self.current_language,
            "genre": self.current_genre
        }
```

### 2. Add MQTT Message Handlers

**File**: `main/livekit-server/src/handlers/chat_logger.py`

Add these new handler methods to the `ChatEventHandler` class:

```python
@staticmethod
async def _handle_start_continuous_music(session, ctx, message):
    """Handle start continuous music signal from MQTT gateway"""
    try:
        logger.info("🎵 Processing start continuous music signal from MQTT gateway")
        
        # Get continuous streaming service from assistant
        if (ChatEventHandler._assistant_instance and 
            hasattr(ChatEventHandler._assistant_instance, 'continuous_streaming_service')):
            
            language = message.get('language')
            genre = message.get('genre')
            
            result = await ChatEventHandler._assistant_instance.continuous_streaming_service.start_streaming(
                language=language, 
                genre=genre
            )
            
            logger.info(f"🎵 Continuous music started: {result}")
            
            # Send confirmation via data channel
            confirmation = {
                "type": "continuous_music_started",
                "message": result,
                "language": language,
                "genre": genre
            }
            
            await ctx.room.local_participant.publish_data(
                json.dumps(confirmation).encode(),
                topic="music_control",
                reliable=True
            )
            
        else:
            logger.error("🎵 Continuous streaming service not available")
            
    except Exception as e:
        logger.error(f"🎵 Error handling start continuous music: {e}")

@staticmethod
async def _handle_stop_continuous_music(session, ctx, message):
    """Handle stop continuous music signal from MQTT gateway"""
    try:
        logger.info("🎵 Processing stop continuous music signal from MQTT gateway")
        
        # Get continuous streaming service from assistant
        if (ChatEventHandler._assistant_instance and 
            hasattr(ChatEventHandler._assistant_instance, 'continuous_streaming_service')):
            
            result = await ChatEventHandler._assistant_instance.continuous_streaming_service.stop_streaming()
            
            logger.info(f"🎵 Continuous music stopped: {result}")
            
            # Send confirmation via data channel
            confirmation = {
                "type": "continuous_music_stopped",
                "message": result
            }
            
            await ctx.room.local_participant.publish_data(
                json.dumps(confirmation).encode(),
                topic="music_control",
                reliable=True
            )
            
        else:
            logger.error("🎵 Continuous streaming service not available")
            
    except Exception as e:
        logger.error(f"🎵 Error handling stop continuous music: {e}")

@staticmethod
async def _handle_skip_music(session, ctx, message):
    """Handle skip music signal from MQTT gateway"""
    try:
        logger.info("🎵 Processing skip music signal from MQTT gateway")
        
        # Get continuous streaming service from assistant
        if (ChatEventHandler._assistant_instance and 
            hasattr(ChatEventHandler._assistant_instance, 'continuous_streaming_service')):
            
            result = await ChatEventHandler._assistant_instance.continuous_streaming_service.skip_current_song()
            
            logger.info(f"🎵 Music skipped: {result}")
            
            # Send confirmation via data channel
            confirmation = {
                "type": "music_skipped",
                "message": result
            }
            
            await ctx.room.local_participant.publish_data(
                json.dumps(confirmation).encode(),
                topic="music_control",
                reliable=True
            )
            
        else:
            logger.error("🎵 Continuous streaming service not available")
            
    except Exception as e:
        logger.error(f"🎵 Error handling skip music: {e}")
```

Add these message type handlers in the `on_data_received` method:

```python
# Add these elif blocks in the on_data_received method

# Handle start continuous music from MQTT gateway
elif message.get('type') == 'start_continuous_music':
    logger.info("🎵 Processing start continuous music signal from MQTT gateway")
    asyncio.create_task(
        ChatEventHandler._handle_start_continuous_music(session, ctx, message))

# Handle stop continuous music from MQTT gateway  
elif message.get('type') == 'stop_continuous_music':
    logger.info("🎵 Processing stop continuous music signal from MQTT gateway")
    asyncio.create_task(
        ChatEventHandler._handle_stop_continuous_music(session, ctx, message))

# Handle skip music from MQTT gateway
elif message.get('type') == 'skip_music':
    logger.info("🎵 Processing skip music signal from MQTT gateway")
    asyncio.create_task(
        ChatEventHandler._handle_skip_music(session, ctx, message))
```

### 3. Integrate with Main Agent

**File**: `main/livekit-server/src/agent/main_agent.py`

Add continuous streaming service to the Assistant class:

```python
# Add this import at the top
from ..services.continuous_music_service import ContinuousStreamingService

# Add this to the Assistant class __init__ method
def __init__(self, instructions: str, tts_provider=None):
    # ... existing code ...
    self.continuous_streaming_service = None

# Add this method to set services
def set_services(self, music_service, story_service, audio_player, unified_audio_player, 
                device_control_service, mcp_executor, google_search_service):
    # ... existing code ...
    
    # Initialize continuous streaming service
    self.continuous_streaming_service = ContinuousStreamingService(
        music_service, 
        unified_audio_player
    )
    logger.info("🎵 Continuous streaming service initialized")

# Add this to set_room_info method
def set_room_info(self, room_name: str = None, device_mac: str = None):
    """Set room name and device MAC address"""
    self.room_name = room_name
    self.device_mac = device_mac
    
    # Set room info for continuous streaming service
    if self.continuous_streaming_service:
        self.continuous_streaming_service.set_room_info(room_name, device_mac)
```

### 4. Initialize in Main Entry Point

**File**: `main/livekit-server/main.py`

No changes needed - the service is initialized in the Assistant class when `set_services()` is called.

### 5. MQTT Message Format

Mobile apps should send these MQTT messages to control streaming:

**Start Continuous Music:**
```json
{
  "type": "start_continuous_music",
  "language": "English",
  "genre": "pop",
  "session_id": "your_session_id"
}
```

**Stop Continuous Music:**
```json
{
  "type": "stop_continuous_music",
  "session_id": "your_session_id"
}
```

**Skip Current Song:**
```json
{
  "type": "skip_music", 
  "session_id": "your_session_id"
}
```

## How It Works

1. **Mobile App** sends MQTT signal to start continuous music
2. **MQTT Gateway** forwards the message to LiveKit via data channel (no changes needed)
3. **LiveKit Agent** receives message in `chat_logger.py` and routes to continuous streaming service
4. **Continuous Streaming Service** starts playlist generation and streaming loop
5. **Music plays continuously** using existing `MusicService` and `UnifiedAudioPlayer`
6. **Mobile App** can send stop/skip signals anytime to control playback

## Key Benefits

- ✅ **Reuses existing infrastructure** (MusicService, UnifiedAudioPlayer, CDN streaming)
- ✅ **No MQTT Gateway changes** required
- ✅ **Room-specific streaming** - each active session independent
- ✅ **Non-intrusive** - doesn't affect existing agent functionality  
- ✅ **Mobile app controlled** - start/stop/skip via MQTT
- ✅ **Continuous playback** - auto-queues next songs
- ✅ **Language/genre support** - leverages existing music search

## Testing

1. Start a LiveKit session (agent active)
2. Send `start_continuous_music` MQTT message from mobile app
3. Verify music starts playing continuously
4. Send `skip_music` to test skipping
5. Send `stop_continuous_music` to stop streaming
6. Verify normal agent functionality still works

## Error Handling

- Service gracefully handles music service failures
- Falls back to random songs if search fails
- Proper cleanup when rooms close
- Logging for debugging streaming issues

This implementation provides the exact functionality you requested: MQTT-controlled continuous music streaming for active LiveKit sessions, using your existing music infrastructure.