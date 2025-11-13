# Plan: Next/Previous Song/Story Control

## Overview
Add ability for firmware to send MQTT messages to skip to next or previous song/story in music and story modes.

---

## Architecture Flow

```
[Firmware Button Press]
        ↓
[Firmware sends MQTT message on control topic]
        ↓
[approom.js receives MQTT message]
        ↓
[approom.js sends HTTP POST to media_api.py]
        ↓
[media_api.py sets skip event on bot]
        ↓
[Bot interrupts current streaming, updates index, plays new song/story]
```

---

## 1. MQTT Message Format (Firmware Side)

### Topics

**For Next:**
```
cheeko/{macAddress}/control/next
```

**For Previous:**
```
cheeko/{macAddress}/control/previous
```

### Payload

**Simple Option (Recommended):**
```json
{
  "type": "control",
  "action": "next"
}
```

```json
{
  "type": "control",
  "action": "previous"
}
```

**Alternative - Empty Payload:**
You can also send empty payload and just use the topic to determine action.

### Example from Firmware
```c
// When user presses "next" button
const char* topic = "cheeko/6825ddbbf3a0/control/next";
const char* payload = "{\"type\":\"control\",\"action\":\"next\"}";
mqtt_publish(topic, payload);

// When user presses "previous" button
const char* topic = "cheeko/6825ddbbf3a0/control/previous";
const char* payload = "{\"type\":\"control\",\"action\":\"previous\"}";
mqtt_publish(topic, payload);
```

---

## 2. Changes to `media_api.py`

### 2.1 Add Skip Control to MusicBot Class

```python
class MusicBot(MediaBot):
    def __init__(self, room_name: str, token: str, language: Optional[str] = None,
                 playlist: Optional[List[dict]] = None, start_index: int = 0):
        super().__init__(room_name, token, "music")
        self.language = language
        self.playlist = playlist
        self.current_index = start_index  # NEW: Track current position
        self.skip_requested = False  # NEW: Flag to interrupt current song
        self.skip_direction = None  # NEW: 'next', 'previous', or None
        self.skip_lock = asyncio.Lock()  # NEW: Thread safety for skip operations

    async def run(self):
        """Main entry point - connect and stream music with skip support"""
        try:
            if not await self.connect_to_room():
                return

            if self.playlist and len(self.playlist) > 0:
                logger.info(f"🎵 Using playlist with {len(self.playlist)} songs")

                # Loop through playlist starting from current_index
                while self.current_index >= 0 and self.current_index < len(self.playlist):
                    if self.should_stop:
                        break

                    playlist_item = self.playlist[self.current_index]
                    filename = playlist_item.get('filename')
                    category = playlist_item.get('category')
                    title = playlist_item.get('title', filename)

                    if not filename or not category:
                        self.current_index += 1
                        continue

                    song_url = music_service.get_song_url(filename, category)
                    logger.info(f"🎵 [{self.current_index + 1}/{len(self.playlist)}] Playing: '{title}'")

                    # Reset skip flag before streaming
                    self.skip_requested = False
                    self.skip_direction = None

                    # Stream this song (can be interrupted by skip)
                    await self._stream_song(song_url, title)

                    # Check if skip was requested during streaming
                    async with self.skip_lock:
                        if self.skip_requested:
                            if self.skip_direction == 'next':
                                logger.info("⏭️ Skipping to next song")
                                self.current_index += 1
                            elif self.skip_direction == 'previous':
                                logger.info("⏮️ Going to previous song")
                                # If already at start, restart current song
                                if self.current_index > 0:
                                    self.current_index -= 1
                                # else: self.current_index stays same (restart current)
                            self.skip_requested = False
                        else:
                            # Normal progression - song finished naturally
                            self.current_index += 1

                    # Small gap between songs
                    if not self.should_stop:
                        await asyncio.sleep(1)

                logger.info("✅ Finished playlist")
            else:
                # Fallback to random song
                logger.info("🎵 No playlist provided")
                song = await music_service.get_random_song(language=self.language)
                if song:
                    await self._stream_song(song['url'], song['title'])

            await asyncio.sleep(2)

        except Exception as e:
            logger.error(f"❌ Music bot error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await self.disconnect()
            if self.room_name in active_bots:
                del active_bots[self.room_name]

    async def _stream_song(self, song_url: str, title: str):
        """Stream a single song - can be interrupted by skip"""
        stream_iterator = StreamingAudioIterator(
            cdn_url=song_url,
            stop_event=self.should_stop,
            title=title
        )

        logger.info(f"🎵 Starting progressive stream...")
        frame_count = 0

        async for frame in stream_iterator:
            # Check for skip or stop
            if self.should_stop or self.skip_requested:
                if self.skip_requested:
                    logger.info(f"⏭️ Skip requested, interrupting stream...")
                await stream_iterator.close()  # Stop download
                break

            await self.audio_source.capture_frame(frame)
            frame_count += 1

            if frame_count % 500 == 0:
                elapsed = (frame_count * 20) / 1000
                logger.info(f"   ⏱️ {elapsed:.1f}s streamed")

        logger.info(f"✅ Stream ended for '{title}'")

    # NEW: Skip control methods
    async def skip_to_next(self):
        """Request skip to next song"""
        async with self.skip_lock:
            logger.info("⏭️ [CONTROL] Next song requested")
            self.skip_requested = True
            self.skip_direction = 'next'

    async def skip_to_previous(self):
        """Request skip to previous song"""
        async with self.skip_lock:
            logger.info("⏮️ [CONTROL] Previous song requested")
            self.skip_requested = True
            self.skip_direction = 'previous'

    def get_current_status(self):
        """Get current playback status"""
        return {
            "current_index": self.current_index,
            "playlist_length": len(self.playlist) if self.playlist else 0,
            "current_song": self.playlist[self.current_index].get('title') if self.playlist and 0 <= self.current_index < len(self.playlist) else None
        }
```

### 2.2 Add Skip Control to StoryBot Class

**Same structure as MusicBot** - just replace "song" with "story" and use `story_service` instead of `music_service`.

```python
class StoryBot(MediaBot):
    # Same implementation as MusicBot but:
    # - self.age_group instead of self.language
    # - story_service.get_story_url() instead of music_service.get_song_url()
    # - "story" in log messages instead of "song"
```

### 2.3 Add REST API Endpoints for Skip Control

```python
@app.post("/music-bot/{room_name}/next")
async def music_bot_skip_next(room_name: str):
    """Skip to next song in music playlist"""
    logger.info(f"🎵 [API] Next song request for room: {room_name}")

    if room_name not in active_bots:
        raise HTTPException(status_code=404, detail=f"Music bot not found in room: {room_name}")

    bot = active_bots[room_name]

    if not isinstance(bot, MusicBot):
        raise HTTPException(status_code=400, detail=f"Bot in room {room_name} is not a music bot")

    await bot.skip_to_next()

    return {
        "status": "success",
        "message": "Skipping to next song",
        "current_status": bot.get_current_status()
    }


@app.post("/music-bot/{room_name}/previous")
async def music_bot_skip_previous(room_name: str):
    """Skip to previous song in music playlist"""
    logger.info(f"🎵 [API] Previous song request for room: {room_name}")

    if room_name not in active_bots:
        raise HTTPException(status_code=404, detail=f"Music bot not found in room: {room_name}")

    bot = active_bots[room_name]

    if not isinstance(bot, MusicBot):
        raise HTTPException(status_code=400, detail=f"Bot in room {room_name} is not a music bot")

    await bot.skip_to_previous()

    return {
        "status": "success",
        "message": "Skipping to previous song",
        "current_status": bot.get_current_status()
    }


@app.post("/story-bot/{room_name}/next")
async def story_bot_skip_next(room_name: str):
    """Skip to next story in story playlist"""
    logger.info(f"📖 [API] Next story request for room: {room_name}")

    if room_name not in active_bots:
        raise HTTPException(status_code=404, detail=f"Story bot not found in room: {room_name}")

    bot = active_bots[room_name]

    if not isinstance(bot, StoryBot):
        raise HTTPException(status_code=400, detail=f"Bot in room {room_name} is not a story bot")

    await bot.skip_to_next()

    return {
        "status": "success",
        "message": "Skipping to next story",
        "current_status": bot.get_current_status()
    }


@app.post("/story-bot/{room_name}/previous")
async def story_bot_skip_previous(room_name: str):
    """Skip to previous story in story playlist"""
    logger.info(f"📖 [API] Previous story request for room: {room_name}")

    if room_name not in active_bots:
        raise HTTPException(status_code=404, detail=f"Story bot not found in room: {room_name}")

    bot = active_bots[room_name]

    if not isinstance(bot, StoryBot):
        raise HTTPException(status_code=400, detail=f"Bot in room {room_name} is not a story bot")

    await bot.skip_to_previous()

    return {
        "status": "success",
        "message": "Skipping to previous story",
        "current_status": bot.get_current_status()
    }


@app.get("/bot/{room_name}/status")
async def get_bot_status(room_name: str):
    """Get current playback status"""
    if room_name not in active_bots:
        raise HTTPException(status_code=404, detail=f"Bot not found in room: {room_name}")

    bot = active_bots[room_name]

    return {
        "room_name": room_name,
        "bot_type": bot.bot_type,
        "status": bot.get_current_status()
    }
```

---

## 3. Changes to `approom.js`

### 3.1 Track Current Room Name for Each Device

Add property to track room names in the device info:

```javascript
// In handleDeviceModeChange or spawnMusicBot/spawnStoryBot
const deviceInfo = this.deviceConnections.get(macAddress);
if (deviceInfo) {
  deviceInfo.currentRoomName = roomName;  // NEW: Store room name
  deviceInfo.currentMode = mode;  // NEW: Store current mode ('music' or 'story')
}
```

### 3.2 Subscribe to Control Topics

```javascript
// In setupMQTTClient or after successful connection
setupControlTopics(macAddress) {
  // Subscribe to control topics for this device
  const nextTopic = `cheeko/${macAddress}/control/next`;
  const previousTopic = `cheeko/${macAddress}/control/previous`;

  this.mqttClient.subscribe(nextTopic, (err) => {
    if (!err) {
      console.log(`✅ [CONTROL] Subscribed to: ${nextTopic}`);
    } else {
      console.error(`❌ [CONTROL] Failed to subscribe to ${nextTopic}:`, err);
    }
  });

  this.mqttClient.subscribe(previousTopic, (err) => {
    if (!err) {
      console.log(`✅ [CONTROL] Subscribed to: ${previousTopic}`);
    } else {
      console.error(`❌ [CONTROL] Failed to subscribe to ${previousTopic}:`, err);
    }
  });
}
```

### 3.3 Handle Control Messages in handleMqttMessage

```javascript
async handleMqttMessage(topic, message) {
  console.log(`📨 [MQTT IN] Received message on topic: ${topic}`);

  try {
    // Check if this is a control message
    if (topic.includes('/control/next')) {
      await this.handleNextControl(topic);
      return;
    } else if (topic.includes('/control/previous')) {
      await this.handlePreviousControl(topic);
      return;
    }

    // ... rest of existing message handling ...
  } catch (error) {
    console.error(`❌ [MQTT] Error handling message:`, error);
  }
}

async handleNextControl(topic) {
  // Extract MAC address from topic: cheeko/{macAddress}/control/next
  const topicParts = topic.split('/');
  const macAddress = topicParts[1];

  console.log(`⏭️ [CONTROL] Next requested for device: ${macAddress}`);

  // Find device info
  const deviceInfo = this.deviceConnections.get(macAddress);
  if (!deviceInfo) {
    console.warn(`⚠️ [CONTROL] Device not found: ${macAddress}`);
    return;
  }

  const roomName = deviceInfo.currentRoomName;
  const mode = deviceInfo.currentMode;

  if (!roomName || !mode) {
    console.warn(`⚠️ [CONTROL] No active room or mode for device: ${macAddress}`);
    return;
  }

  try {
    let apiUrl;
    if (mode === 'music') {
      apiUrl = `http://localhost:8003/music-bot/${roomName}/next`;
    } else if (mode === 'story') {
      apiUrl = `http://localhost:8003/story-bot/${roomName}/next`;
    } else {
      console.warn(`⚠️ [CONTROL] Next/Previous not supported for mode: ${mode}`);
      return;
    }

    console.log(`⏭️ [CONTROL] Sending skip request to: ${apiUrl}`);
    const response = await axios.post(apiUrl, {}, { timeout: 5000 });

    console.log(`✅ [CONTROL] Skip successful:`, response.data);
  } catch (error) {
    console.error(`❌ [CONTROL] Failed to skip:`, error.message);
  }
}

async handlePreviousControl(topic) {
  // Extract MAC address from topic
  const topicParts = topic.split('/');
  const macAddress = topicParts[1];

  console.log(`⏮️ [CONTROL] Previous requested for device: ${macAddress}`);

  const deviceInfo = this.deviceConnections.get(macAddress);
  if (!deviceInfo) {
    console.warn(`⚠️ [CONTROL] Device not found: ${macAddress}`);
    return;
  }

  const roomName = deviceInfo.currentRoomName;
  const mode = deviceInfo.currentMode;

  if (!roomName || !mode) {
    console.warn(`⚠️ [CONTROL] No active room or mode for device: ${macAddress}`);
    return;
  }

  try {
    let apiUrl;
    if (mode === 'music') {
      apiUrl = `http://localhost:8003/music-bot/${roomName}/previous`;
    } else if (mode === 'story') {
      apiUrl = `http://localhost:8003/story-bot/${roomName}/previous`;
    } else {
      console.warn(`⚠️ [CONTROL] Next/Previous not supported for mode: ${mode}`);
      return;
    }

    console.log(`⏮️ [CONTROL] Sending skip request to: ${apiUrl}`);
    const response = await axios.post(apiUrl, {}, { timeout: 5000 });

    console.log(`✅ [CONTROL] Skip successful:`, response.data);
  } catch (error) {
    console.error(`❌ [CONTROL] Failed to skip:`, error.message);
  }
}
```

### 3.4 Update spawnMusicBot/spawnStoryBot to Store Room Info

```javascript
async spawnMusicBot(roomName, playlist = null) {
  if (!playlist) {
    playlist = await this.fetchPlaylist('music');
  }

  const response = await axios.post('http://localhost:8003/start-music-bot', {
    room_name: roomName,
    device_mac: this.macAddress,
    language: this.language,
    playlist: playlist
  });

  // NEW: Store room info for control messages
  const deviceInfo = this.deviceConnections.get(this.macAddress);
  if (deviceInfo) {
    deviceInfo.currentRoomName = roomName;
    deviceInfo.currentMode = 'music';
    console.log(`✅ [CONTROL] Stored room info - Room: ${roomName}, Mode: music`);
  }

  return response.data;
}

async spawnStoryBot(roomName, playlist = null) {
  if (!playlist) {
    playlist = await this.fetchPlaylist('story');
  }

  const response = await axios.post('http://localhost:8003/start-story-bot', {
    room_name: roomName,
    device_mac: this.macAddress,
    age_group: this.ageGroup,
    playlist: playlist
  });

  // NEW: Store room info for control messages
  const deviceInfo = this.deviceConnections.get(this.macAddress);
  if (deviceInfo) {
    deviceInfo.currentRoomName = roomName;
    deviceInfo.currentMode = 'story';
    console.log(`✅ [CONTROL] Stored room info - Room: ${roomName}, Mode: story`);
  }

  return response.data;
}
```

---

## 4. StreamingAudioIterator Enhancement

The `StreamingAudioIterator` already checks `self.stop_event` during download. We need to make sure it can be interrupted:

```python
class StreamingAudioIterator:
    def __init__(self, cdn_url: str, stop_event, title: str):
        self.cdn_url = cdn_url
        self.stop_event = stop_event
        self.title = title
        self.chunk_size = 64 * 1024
        self.frame_queue = asyncio.Queue(maxsize=100)
        self.producer_task = None
        self.session = None
        self.is_closed = False  # NEW: Track if iterator was explicitly closed

    async def close(self):
        """Explicitly close the iterator and stop download"""
        self.is_closed = True
        self.stop_event = True

        # Cancel producer task if running
        if self.producer_task and not self.producer_task.done():
            self.producer_task.cancel()

        # Close HTTP session
        if self.session:
            await self.session.close()

        # Signal end of stream
        try:
            await self.frame_queue.put(None)
        except:
            pass

    async def _produce_frames(self):
        # ... existing code ...
        async for chunk in response.content.iter_chunked(self.chunk_size):
            if self.stop_event or self.is_closed:  # NEW: Check is_closed
                logger.info("⏹️ Stop/skip requested, halting download")
                break
            # ... rest of processing ...
```

---

## 5. Edge Cases & Behavior

### 5.1 Previous at Start of Playlist (Index 0)
**Behavior:** Restart current song

```python
if self.skip_direction == 'previous':
    if self.current_index > 0:
        self.current_index -= 1  # Go to previous
    # else: keep current_index = 0 (restart current song)
```

### 5.2 Next at End of Playlist
**Behavior:** Stop playing (or loop - configurable)

```python
if self.current_index >= len(self.playlist):
    logger.info("📝 Reached end of playlist")
    break  # Stop
    # OR: self.current_index = 0  # Loop back to start
```

### 5.3 Multiple Skip Requests
**Behavior:** Only process one skip at a time (using `skip_lock`)

### 5.4 Skip During Silence Gap
**Behavior:** Skip is only processed during song streaming, ignored during 1-second gap between songs

### 5.5 No Playlist
**Behavior:** Next/Previous do nothing (single random song mode)

---

## 6. Testing Plan

### 6.1 Test Next Command
```bash
# Device MAC: 6825ddbbf3a0
# Publish MQTT message:
mosquitto_pub -h 192.168.1.170 -t "cheeko/6825ddbbf3a0/control/next" -m '{"type":"control","action":"next"}'
```

### 6.2 Test Previous Command
```bash
mosquitto_pub -h 192.168.1.170 -t "cheeko/6825ddbbf3a0/control/previous" -m '{"type":"control","action":"previous"}'
```

### 6.3 Test via Direct API
```bash
# Get room name from logs, then:
curl -X POST "http://localhost:8003/music-bot/{room_name}/next"
curl -X POST "http://localhost:8003/music-bot/{room_name}/previous"
```

### 6.4 Check Status
```bash
curl -X GET "http://localhost:8003/bot/{room_name}/status"
```

---

## 7. Firmware Integration (Summary for Firmware Team)

### Message Format to Send

**Topic for Next:**
```
cheeko/{YOUR_MAC_ADDRESS}/control/next
```

**Topic for Previous:**
```
cheeko/{YOUR_MAC_ADDRESS}/control/previous
```

**Payload (JSON):**
```json
{
  "type": "control",
  "action": "next"
}
```

or

```json
{
  "type": "control",
  "action": "previous"
}
```

**Alternative - Empty Payload:**
You can send empty payload - the action is determined by the topic.

### Example C Code
```c
void handleNextButton() {
    char topic[100];
    sprintf(topic, "cheeko/%s/control/next", device_mac);

    const char* payload = "{\"type\":\"control\",\"action\":\"next\"}";
    mqtt_publish(topic, payload, strlen(payload));
}

void handlePreviousButton() {
    char topic[100];
    sprintf(topic, "cheeko/%s/control/previous", device_mac);

    const char* payload = "{\"type\":\"control\",\"action\":\"previous\"}";
    mqtt_publish(topic, payload, strlen(payload));
}
```

---

## 8. Implementation Checklist

### media_api.py
- [ ] Add `current_index`, `skip_requested`, `skip_direction`, `skip_lock` to MusicBot
- [ ] Modify MusicBot.run() to handle skip logic
- [ ] Add `skip_to_next()` and `skip_to_previous()` methods to MusicBot
- [ ] Add `get_current_status()` method to MusicBot
- [ ] Repeat same changes for StoryBot
- [ ] Add POST `/music-bot/{room_name}/next` endpoint
- [ ] Add POST `/music-bot/{room_name}/previous` endpoint
- [ ] Add POST `/story-bot/{room_name}/next` endpoint
- [ ] Add POST `/story-bot/{room_name}/previous` endpoint
- [ ] Add GET `/bot/{room_name}/status` endpoint
- [ ] Enhance StreamingAudioIterator with `close()` method

### approom.js
- [ ] Add `currentRoomName` and `currentMode` to device info tracking
- [ ] Add `setupControlTopics()` method to subscribe to control messages
- [ ] Call `setupControlTopics()` when device connects
- [ ] Add control topic handling in `handleMqttMessage()`
- [ ] Implement `handleNextControl()` method
- [ ] Implement `handlePreviousControl()` method
- [ ] Update `spawnMusicBot()` to store room info
- [ ] Update `spawnStoryBot()` to store room info

### Testing
- [ ] Test next button during music playback
- [ ] Test previous button during music playback
- [ ] Test next button during story playback
- [ ] Test previous button during story playback
- [ ] Test previous at start of playlist (should restart)
- [ ] Test next at end of playlist (should stop)
- [ ] Test rapid multiple skip requests
- [ ] Test skip with no playlist (should do nothing gracefully)

---

## 9. Notes

1. **Thread Safety**: Using `asyncio.Lock()` for skip_lock ensures skip requests are processed safely
2. **Interruption**: StreamingAudioIterator checks `skip_requested` flag every frame
3. **No Database Changes**: All state is in-memory in the bot instances
4. **Playlist Position**: Persisted only during bot lifetime, resets on mode change
5. **Performance**: Skip is near-instant (interrupts current streaming within 20ms)

---

## Summary

This plan adds complete next/previous control for music and story modes:

- **Firmware sends MQTT** to `cheeko/{mac}/control/next` or `cheeko/{mac}/control/previous`
- **approom.js receives** and forwards to media_api
- **media_api bot** interrupts current streaming, updates playlist index, plays new item
- **Edge cases handled**: previous at start, next at end, multiple skips
- **No database changes** needed - all in-memory state
