# Playlist API CURL Commands

Base URL: `http://192.168.1.166:8002/toy`
Device MAC: `6825ddbbf3a0`

## Sample Content IDs

**Music:**
- `1e72aa78-3dbf-4006-8000-3db91e6c6cc5`
- `1e72aa9e-3dbf-4006-8000-3db91e6c6ceb`

**Story:**
- `1e72aa69-3dbf-4006-8000-3db91e6c6ccb`
- `1e72aa91-3dbf-4006-8000-3db91e6c6cdc`

---

# Music Playlist APIs

## 1. GET Music Playlist

Retrieve the current music playlist for a device.

```bash
curl -X GET "http://192.168.1.166:8002/toy/device/6825ddbbf3a0/playlist/music"
```

**Response:**
```json
{
  "code": 0,
  "msg": null,
  "data": [
    {
      "contentId": "1e72aa78-3dbf-4006-8000-3db91e6c6cc5",
      "title": "Song Title",
      "romanized": "song-romanized",
      "filename": "song.mp3",
      "category": "english",
      "position": 0,
      "durationSeconds": 180,
      "thumbnailUrl": "https://example.com/thumb.jpg"
    }
  ]
}
```

---

## 2. POST - Add Songs to Music Playlist

Append songs to the end of the existing music playlist.

```bash
curl -X POST "http://192.168.1.166:8002/toy/device/6825ddbbf3a0/playlist/music" \
  -H "Content-Type: application/json" \
  -d "{\"contentIds\":[\"1e72aa78-3dbf-4006-8000-3db91e6c6cc5\",\"1e72aa9e-3dbf-4006-8000-3db91e6c6ceb\"]}"
```

**Response:**
```json
{
  "code": 0,
  "msg": null,
  "data": {
    "message": "Added 2 songs to playlist",
    "count": 2
  }
}
```

---

## 3. PUT - Replace Music Playlist

Replace the entire music playlist with new songs.

```bash
curl -X PUT "http://192.168.1.166:8002/toy/device/6825ddbbf3a0/playlist/music" \
  -H "Content-Type: application/json" \
  -d "{\"contentIds\":[\"1e72aa78-3dbf-4006-8000-3db91e6c6cc5\",\"1e72aa9e-3dbf-4006-8000-3db91e6c6ceb\"]}"
```

**Response:**
```json
{
  "code": 0,
  "msg": null,
  "data": {
    "message": "Playlist replaced successfully",
    "count": 2
  }
}
```

---

## 4. PATCH - Reorder Music Playlist

Update the positions of playlist items (for drag-and-drop reordering).

```bash
curl -X PATCH "http://192.168.1.166:8002/toy/device/6825ddbbf3a0/playlist/music/reorder" \
  -H "Content-Type: application/json" \
  -d "{\"items\":[{\"contentId\":\"1e72aa9e-3dbf-4006-8000-3db91e6c6ceb\",\"position\":0},{\"contentId\":\"1e72aa78-3dbf-4006-8000-3db91e6c6cc5\",\"position\":1}]}"
```

**Response:**
```json
{
  "code": 0,
  "msg": null,
  "data": {
    "message": "Playlist reordered successfully",
    "count": 2
  }
}
```

---

## 5. DELETE - Remove Song from Music Playlist

Remove a specific song from the music playlist.

```bash
curl -X DELETE "http://192.168.1.166:8002/toy/device/6825ddbbf3a0/playlist/music/1e72aa78-3dbf-4006-8000-3db91e6c6cc5"
```

**Response:**
```json
{
  "code": 0,
  "msg": null,
  "data": {
    "message": "Song removed from playlist",
    "count": 1
  }
}
```

---

## 6. DELETE - Clear Music Playlist

Remove all songs from the music playlist.

```bash
curl -X DELETE "http://192.168.1.166:8002/toy/device/6825ddbbf3a0/playlist/music"
```

**Response:**
```json
{
  "code": 0,
  "msg": null,
  "data": {
    "message": "Playlist cleared successfully",
    "count": 0
  }
}
```

---

# Story Playlist APIs

## 1. GET Story Playlist

Retrieve the current story playlist for a device.

```bash
curl -X GET "http://192.168.1.166:8002/toy/device/6825ddbbf3a0/playlist/story"
```

**Response:**
```json
{
  "code": 0,
  "msg": null,
  "data": [
    {
      "contentId": "1e72aa69-3dbf-4006-8000-3db91e6c6ccb",
      "title": "Story Title",
      "romanized": "story-romanized",
      "filename": "story.mp3",
      "category": "fairy-tales",
      "position": 0,
      "durationSeconds": 300,
      "thumbnailUrl": "https://example.com/thumb.jpg"
    }
  ]
}
```

---

## 2. POST - Add Stories to Story Playlist

Append stories to the end of the existing story playlist.

```bash
curl -X POST "http://192.168.1.166:8002/toy/device/6825ddbbf3a0/playlist/story" \
  -H "Content-Type: application/json" \
  -d "{\"contentIds\":[\"1e72aa69-3dbf-4006-8000-3db91e6c6ccb\",\"1e72aa91-3dbf-4006-8000-3db91e6c6cdc\"]}"
```

**Response:**
```json
{
  "code": 0,
  "msg": null,
  "data": {
    "message": "Added 2 stories to playlist",
    "count": 2
  }
}
```

---

## 3. PUT - Replace Story Playlist

Replace the entire story playlist with new stories.

```bash
curl -X PUT "http://192.168.1.166:8002/toy/device/6825ddbbf3a0/playlist/story" \
  -H "Content-Type: application/json" \
  -d "{\"contentIds\":[\"1e72aa69-3dbf-4006-8000-3db91e6c6ccb\",\"1e72aa91-3dbf-4006-8000-3db91e6c6cdc\"]}"
```

**Response:**
```json
{
  "code": 0,
  "msg": null,
  "data": {
    "message": "Playlist replaced successfully",
    "count": 2
  }
}
```

---

## 4. PATCH - Reorder Story Playlist

Update the positions of playlist items (for drag-and-drop reordering).

```bash
curl -X PATCH "http://192.168.1.166:8002/toy/device/6825ddbbf3a0/playlist/story/reorder" \
  -H "Content-Type: application/json" \
  -d "{\"items\":[{\"contentId\":\"1e72aa91-3dbf-4006-8000-3db91e6c6cdc\",\"position\":0},{\"contentId\":\"1e72aa69-3dbf-4006-8000-3db91e6c6ccb\",\"position\":1}]}"
```

**Response:**
```json
{
  "code": 0,
  "msg": null,
  "data": {
    "message": "Playlist reordered successfully",
    "count": 2
  }
}
```

---

## 5. DELETE - Remove Story from Story Playlist

Remove a specific story from the story playlist.

```bash
curl -X DELETE "http://192.168.1.166:8002/toy/device/6825ddbbf3a0/playlist/story/1e72aa69-3dbf-4006-8000-3db91e6c6ccb"
```

**Response:**
```json
{
  "code": 0,
  "msg": null,
  "data": {
    "message": "Story removed from playlist",
    "count": 1
  }
}
```

---

## 6. DELETE - Clear Story Playlist

Remove all stories from the story playlist.

```bash
curl -X DELETE "http://192.168.1.166:8002/toy/device/6825ddbbf3a0/playlist/story"
```

**Response:**
```json
{
  "code": 0,
  "msg": null,
  "data": {
    "message": "Playlist cleared successfully",
    "count": 0
  }
}
```

---

# Testing Workflow

## Step 1: Start Manager API
```bash
cd C:\Users\Acer\Cheeko-esp32-server\main\manager-api
.\mvnw.cmd spring-boot:run
```

## Step 2: Get Current Content IDs
```bash
# List all music content
curl -X GET "http://192.168.1.166:8002/toy/content/items?contentType=music&page=1&limit=10"

# List all story content
curl -X GET "http://192.168.1.166:8002/toy/content/items?contentType=story&page=1&limit=10"
```

## Step 3: Test Complete Music Flow
```bash
# 1. Add songs
curl -X POST "http://192.168.1.166:8002/toy/device/6825ddbbf3a0/playlist/music" \
  -H "Content-Type: application/json" \
  -d "{\"contentIds\":[\"1e72aa78-3dbf-4006-8000-3db91e6c6cc5\",\"1e72aa9e-3dbf-4006-8000-3db91e6c6ceb\"]}"

# 2. View playlist
curl -X GET "http://192.168.1.166:8002/toy/device/6825ddbbf3a0/playlist/music"

# 3. Reorder
curl -X PATCH "http://192.168.1.166:8002/toy/device/6825ddbbf3a0/playlist/music/reorder" \
  -H "Content-Type: application/json" \
  -d "{\"items\":[{\"contentId\":\"1e72aa9e-3dbf-4006-8000-3db91e6c6ceb\",\"position\":0},{\"contentId\":\"1e72aa78-3dbf-4006-8000-3db91e6c6cc5\",\"position\":1}]}"

# 4. Remove one song
curl -X DELETE "http://192.168.1.166:8002/toy/device/6825ddbbf3a0/playlist/music/1e72aa78-3dbf-4006-8000-3db91e6c6cc5"

# 5. Clear all
curl -X DELETE "http://192.168.1.166:8002/toy/device/6825ddbbf3a0/playlist/music"
```

## Step 4: Test Complete Story Flow
```bash
# 1. Replace entire playlist
curl -X PUT "http://192.168.1.166:8002/toy/device/6825ddbbf3a0/playlist/story" \
  -H "Content-Type: application/json" \
  -d "{\"contentIds\":[\"1e72aa69-3dbf-4006-8000-3db91e6c6ccb\",\"1e72aa91-3dbf-4006-8000-3db91e6c6cdc\"]}"

# 2. View playlist
curl -X GET "http://192.168.1.166:8002/toy/device/6825ddbbf3a0/playlist/story"

# 3. Add more stories
curl -X POST "http://192.168.1.166:8002/toy/device/6825ddbbf3a0/playlist/story" \
  -H "Content-Type: application/json" \
  -d "{\"contentIds\":[\"ANOTHER-STORY-ID-HERE\"]}"
```

---

# Notes

1. **Authentication**: These endpoints are configured for anonymous access via Shiro (`/device/**/playlist/**`)
2. **Base URL**: Always use `/toy` prefix for manager-api endpoints
3. **Content IDs**: Use real UUIDs from the `content_items` table - query them first
4. **Positions**: Automatically managed - you only need to specify positions when reordering
5. **Response Format**: All responses follow the standard format with `code`, `msg`, and `data` fields
6. **Error Handling**:
   - 404: Device or content not found
   - 400: Invalid content type (mixing music/story)
   - 500: Database/server errors

---

# Integration with Bot

When a device switches to music/story mode:

1. **MQTT Gateway** fetches playlist: `GET /device/{mac}/playlist/{mode}`
2. **Spawns bot** with playlist data
3. **Bot iterates** through playlist items
4. **Constructs URLs** from filename + category using `MusicService`/`StoryService`
5. **Streams progressively** using `StreamingAudioIterator`

The bot doesn't need full URLs in the database - just filename and category are enough!
