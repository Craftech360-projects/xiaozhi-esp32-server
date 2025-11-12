# Content Items API Documentation

## Overview

The Content Items API provides complete CRUD (Create, Read, Update, Delete) operations for managing music and story content items in the system.

**Base URL**: `http://localhost:8002/toy`

**Authentication**: Not required (anonymous access enabled)

---

## Table Structure

**Table Name**: `content_items`

| Column | Type | Description |
|--------|------|-------------|
| id | CHAR(36) | Unique identifier (UUID) |
| title | TEXT | Content title |
| romanized | TEXT | Romanized version of title |
| filename | TEXT | Audio filename |
| content_type | VARCHAR(50) | Type: 'music' or 'story' |
| category | VARCHAR(100) | Content category (e.g., English, Fantasy) |
| alternatives | JSON | Alternative titles/search terms |
| file_url | TEXT | File storage URL |
| duration_seconds | INT | Duration in seconds |
| created_at | DATETIME | Creation timestamp |
| updated_at | DATETIME | Last update timestamp |
| thumbnail_url | VARCHAR(500) | Thumbnail image URL |

---

## API Endpoints

### CREATE Operations

#### 1. Create Single Content Item

**Endpoint**: `POST /content/items`

**Description**: Creates a new content item

**Request Body**:
```json
{
  "title": "Test Song",
  "romanized": "Test Song",
  "filename": "test_song.mp3",
  "contentType": "music",
  "category": "English",
  "alternatives": "[\"test\",\"song\",\"demo\"]",
  "fileUrl": null,
  "durationSeconds": 120,
  "thumbnailUrl": "https://example.com/thumbnail.png"
}
```

**cURL Command**:
```bash
curl -X POST "http://localhost:8002/toy/content/items" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Song",
    "romanized": "Test Song",
    "filename": "test_song.mp3",
    "contentType": "music",
    "category": "English",
    "alternatives": "[\"test\",\"song\",\"demo\"]",
    "fileUrl": null,
    "durationSeconds": 120,
    "thumbnailUrl": "https://example.com/thumbnail.png"
  }'
```

**Response**:
```json
{
  "code": 0,
  "msg": "success",
  "data": "a1b2c3d4-5678-90ab-cdef-1234567890ab"
}
```

---

#### 2. Batch Create Content Items

**Endpoint**: `POST /content/items/batch`

**Description**: Creates multiple content items at once

**Request Body**:
```json
[
  {
    "title": "Test Song 1",
    "romanized": "Test Song 1",
    "filename": "test_song_1.mp3",
    "contentType": "music",
    "category": "English",
    "alternatives": "[\"test1\"]",
    "durationSeconds": 120
  },
  {
    "title": "Test Story 1",
    "romanized": "Test Story 1",
    "filename": "test_story_1.mp3",
    "contentType": "story",
    "category": "Fantasy",
    "alternatives": "[\"story1\"]",
    "durationSeconds": 180
  }
]
```

**cURL Command**:
```bash
curl -X POST "http://localhost:8002/toy/content/items/batch" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "title": "Test Song 1",
      "romanized": "Test Song 1",
      "filename": "test_song_1.mp3",
      "contentType": "music",
      "category": "English",
      "alternatives": "[\"test1\"]",
      "durationSeconds": 120
    },
    {
      "title": "Test Story 1",
      "romanized": "Test Story 1",
      "filename": "test_story_1.mp3",
      "contentType": "story",
      "category": "Fantasy",
      "alternatives": "[\"story1\"]",
      "durationSeconds": 180
    }
  ]'
```

**Response**:
```json
{
  "code": 0,
  "msg": "success",
  "data": 2
}
```

---

### READ Operations

#### 3. Get All Content Items (Paginated)

**Endpoint**: `GET /content/items`

**Description**: Retrieves paginated list of all content items with optional filters

**Query Parameters**:
- `page` (optional, default: 1) - Page number
- `limit` (optional, default: 20) - Items per page
- `query` (optional) - Search query
- `contentType` (optional) - Filter by content type (music/story)
- `category` (optional) - Filter by category
- `sortBy` (optional, default: created_at) - Sort field
- `sortDirection` (optional, default: desc) - Sort direction (asc/desc)

**cURL Commands**:

```bash
# Get first page (10 items)
curl -X GET "http://localhost:8002/toy/content/items?page=1&limit=10"

# Get all music items
curl -X GET "http://localhost:8002/toy/content/items?contentType=music&page=1&limit=20"

# Get all story items
curl -X GET "http://localhost:8002/toy/content/items?contentType=story&page=1&limit=20"

# Get English category items
curl -X GET "http://localhost:8002/toy/content/items?category=English&page=1&limit=10"

# Search with query
curl -X GET "http://localhost:8002/toy/content/items?query=twinkle&page=1&limit=10"
```

**Response**:
```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "list": [
      {
        "id": "bbf2b486-b8cd-405b-9515-84ffc95ecaf3",
        "title": "Twinkle Twinkle Little Star",
        "romanized": "Twinkle Twinkle Little Star",
        "filename": "Twinkle Twinkle Little Star.mp3",
        "contentType": "music",
        "category": "English",
        "alternatives": "[\"twinkle twinkle little star\",\"little star\"]",
        "fileUrl": null,
        "durationSeconds": null,
        "createdAt": "2025-09-17 07:00:20",
        "updatedAt": "2025-09-17 07:00:20",
        "thumbnailUrl": "https://example.com/twinkle.png"
      }
    ],
    "total": 31,
    "page": 1,
    "limit": 10
  }
}
```

---

#### 4. Get Content Item by ID

**Endpoint**: `GET /content/items/{id}`

**Description**: Retrieves a specific content item by its ID

**cURL Command**:
```bash
curl -X GET "http://localhost:8002/toy/content/items/bbf2b486-b8cd-405b-9515-84ffc95ecaf3"
```

**Response**:
```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "id": "bbf2b486-b8cd-405b-9515-84ffc95ecaf3",
    "title": "Twinkle Twinkle Little Star",
    "romanized": "Twinkle Twinkle Little Star",
    "filename": "Twinkle Twinkle Little Star.mp3",
    "contentType": "music",
    "category": "English",
    "alternatives": "[\"twinkle twinkle little star\",\"little star\"]",
    "fileUrl": null,
    "durationSeconds": null,
    "createdAt": "2025-09-17 07:00:20",
    "updatedAt": "2025-09-17 07:00:20",
    "thumbnailUrl": "https://example.com/twinkle.png"
  }
}
```

---

#### 5. Get Content Items by Type

**Endpoint**: `GET /content/items/type/{contentType}`

**Description**: Retrieves all content items of a specific type

**cURL Commands**:
```bash
# Get all music items
curl -X GET "http://localhost:8002/toy/content/items/type/music"

# Get all story items
curl -X GET "http://localhost:8002/toy/content/items/type/story"
```

**Response**:
```json
{
  "code": 0,
  "msg": "success",
  "data": [
    {
      "id": "1e72aa9e-3dbf-4006-8000-3db91e6c6ceb",
      "title": "Baby Shark Dance",
      "contentType": "music",
      "category": "English"
    }
  ]
}
```

---

#### 6. Get Content Items by Category

**Endpoint**: `GET /content/items/category/{category}`

**Description**: Retrieves all content items in a specific category

**cURL Commands**:
```bash
# Get all English items
curl -X GET "http://localhost:8002/toy/content/items/category/English"

# Get all Fantasy items
curl -X GET "http://localhost:8002/toy/content/items/category/Fantasy"

# Get all Phonics items
curl -X GET "http://localhost:8002/toy/content/items/category/Phonics"
```

**Response**:
```json
{
  "code": 0,
  "msg": "success",
  "data": [
    {
      "id": "1e72aa78-3dbf-4006-8000-3db91e6c6cc5",
      "title": "Baa Baa Black Sheep",
      "category": "English"
    }
  ]
}
```

---

#### 7. Search Content Items

**Endpoint**: `GET /content/items/search`

**Description**: Full-text search across content titles, romanized titles, and alternatives

**Query Parameters**:
- `query` (required) - Search query
- `contentType` (optional) - Filter by content type
- `page` (optional, default: 1) - Page number
- `limit` (optional, default: 20) - Items per page

**cURL Commands**:
```bash
# Search for "baby shark"
curl -X GET "http://localhost:8002/toy/content/items/search?query=baby+shark"

# Search for "twinkle" in music only
curl -X GET "http://localhost:8002/toy/content/items/search?query=twinkle&contentType=music"

# Search for "fairy" in stories
curl -X GET "http://localhost:8002/toy/content/items/search?query=fairy&contentType=story"
```

**Response**:
```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "list": [
      {
        "id": "1e72aa9e-3dbf-4006-8000-3db91e6c6ceb",
        "title": "Baby Shark Dance",
        "contentType": "music"
      }
    ],
    "total": 1
  }
}
```

---

#### 8. Get Categories by Content Type

**Endpoint**: `GET /content/items/categories`

**Description**: Retrieves distinct categories for a specific content type

**Query Parameters**:
- `contentType` (required) - Content type (music/story)

**cURL Commands**:
```bash
# Get all music categories
curl -X GET "http://localhost:8002/toy/content/items/categories?contentType=music"

# Get all story categories
curl -X GET "http://localhost:8002/toy/content/items/categories?contentType=story"
```

**Response**:
```json
{
  "code": 0,
  "msg": "success",
  "data": [
    "English",
    "Phonics"
  ]
}
```

---

#### 9. Get Content Statistics

**Endpoint**: `GET /content/items/statistics`

**Description**: Retrieves statistics including total counts and available categories

**cURL Command**:
```bash
curl -X GET "http://localhost:8002/toy/content/items/statistics"
```

**Response**:
```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "totalMusic": 22,
    "totalStories": 9,
    "totalContent": 31,
    "musicCategories": ["English", "Phonics"],
    "storyCategories": ["Adventure", "Bedtime", "Educational", "Fairy Tales", "Fantasy"]
  }
}
```

---

### UPDATE Operations

#### 10. Full Update Content Item

**Endpoint**: `PUT /content/items/{id}`

**Description**: Completely replaces an existing content item

**Request Body**:
```json
{
  "title": "Twinkle Twinkle Little Star - Updated",
  "romanized": "Twinkle Twinkle Little Star",
  "filename": "Twinkle Twinkle Little Star.mp3",
  "contentType": "music",
  "category": "English",
  "alternatives": "[\"twinkle twinkle\",\"updated version\"]",
  "durationSeconds": 150,
  "thumbnailUrl": "https://example.com/twinkle.png"
}
```

**cURL Command**:
```bash
curl -X PUT "http://localhost:8002/toy/content/items/bbf2b486-b8cd-405b-9515-84ffc95ecaf3" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Twinkle Twinkle Little Star - Updated",
    "romanized": "Twinkle Twinkle Little Star",
    "filename": "Twinkle Twinkle Little Star.mp3",
    "contentType": "music",
    "category": "English",
    "alternatives": "[\"twinkle twinkle\",\"updated version\"]",
    "durationSeconds": 150,
    "thumbnailUrl": "https://example.com/twinkle.png"
  }'
```

**Response**:
```json
{
  "code": 0,
  "msg": "success",
  "data": true
}
```

---

#### 11. Partial Update Content Item

**Endpoint**: `PATCH /content/items/{id}`

**Description**: Updates specific fields of an existing content item

**Request Body**:
```json
{
  "durationSeconds": 180,
  "thumbnailUrl": "https://example.com/new-thumbnail.png"
}
```

**cURL Commands**:
```bash
# Update only duration
curl -X PATCH "http://localhost:8002/toy/content/items/bbf2b486-b8cd-405b-9515-84ffc95ecaf3" \
  -H "Content-Type: application/json" \
  -d '{
    "durationSeconds": 180
  }'

# Update multiple fields
curl -X PATCH "http://localhost:8002/toy/content/items/bbf2b486-b8cd-405b-9515-84ffc95ecaf3" \
  -H "Content-Type: application/json" \
  -d '{
    "durationSeconds": 180,
    "thumbnailUrl": "https://example.com/new-thumbnail.png",
    "category": "Kids Songs"
  }'
```

**Response**:
```json
{
  "code": 0,
  "msg": "success",
  "data": true
}
```

---

#### 12. Batch Update Content Items

**Endpoint**: `PUT /content/items/batch`

**Description**: Updates multiple content items at once

**Request Body**:
```json
[
  {
    "id": "bbf2b486-b8cd-405b-9515-84ffc95ecaf3",
    "title": "Twinkle Twinkle - Updated",
    "contentType": "music",
    "category": "English",
    "durationSeconds": 150
  },
  {
    "id": "1e72aa9e-3dbf-4006-8000-3db91e6c6ceb",
    "title": "Baby Shark - Updated",
    "contentType": "music",
    "category": "English",
    "durationSeconds": 200
  }
]
```

**cURL Command**:
```bash
curl -X PUT "http://localhost:8002/toy/content/items/batch" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "id": "bbf2b486-b8cd-405b-9515-84ffc95ecaf3",
      "title": "Twinkle Twinkle - Updated",
      "durationSeconds": 150
    },
    {
      "id": "1e72aa9e-3dbf-4006-8000-3db91e6c6ceb",
      "title": "Baby Shark - Updated",
      "durationSeconds": 200
    }
  ]'
```

**Response**:
```json
{
  "code": 0,
  "msg": "success",
  "data": 2
}
```

---

### DELETE Operations

#### 13. Delete Single Content Item

**Endpoint**: `DELETE /content/items/{id}`

**Description**: Deletes a specific content item

**cURL Command**:
```bash
curl -X DELETE "http://localhost:8002/toy/content/items/YOUR_TEST_ID_HERE"
```

**Response**:
```json
{
  "code": 0,
  "msg": "success",
  "data": true
}
```

---

#### 14. Batch Delete Content Items

**Endpoint**: `DELETE /content/items/batch`

**Description**: Deletes multiple content items at once

**Request Body**:
```json
[
  "id1",
  "id2",
  "id3"
]
```

**cURL Command**:
```bash
curl -X DELETE "http://localhost:8002/toy/content/items/batch" \
  -H "Content-Type: application/json" \
  -d '["a1b2c3d4-5678-90ab-cdef-1234567890ab", "b2c3d4e5-6789-01bc-def0-234567890abc"]'
```

**Response**:
```json
{
  "code": 0,
  "msg": "success",
  "data": 2
}
```

---

## Complete Test Sequence

Run these commands in order to test all operations:

```bash
# 1. Get statistics
curl -X GET "http://localhost:8002/toy/content/items/statistics"

# 2. Get all items (first page)
curl -X GET "http://localhost:8002/toy/content/items?page=1&limit=5"

# 3. Get music categories
curl -X GET "http://localhost:8002/toy/content/items/categories?contentType=music"

# 4. Get all music items
curl -X GET "http://localhost:8002/toy/content/items/type/music"

# 5. Get items by category
curl -X GET "http://localhost:8002/toy/content/items/category/English"

# 6. Search for a song
curl -X GET "http://localhost:8002/toy/content/items/search?query=baby+shark"

# 7. Get specific item by ID
curl -X GET "http://localhost:8002/toy/content/items/1e72aa9e-3dbf-4006-8000-3db91e6c6ceb"

# 8. Create a new test item
curl -X POST "http://localhost:8002/toy/content/items" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Song",
    "romanized": "Test Song",
    "filename": "test_song.mp3",
    "contentType": "music",
    "category": "Test",
    "alternatives": "[\"test\"]",
    "durationSeconds": 120
  }'

# 9. Update the test item (use the ID from step 8 response)
curl -X PATCH "http://localhost:8002/toy/content/items/YOUR_NEW_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "durationSeconds": 180
  }'

# 10. Delete the test item
curl -X DELETE "http://localhost:8002/toy/content/items/YOUR_NEW_ID"
```

---

## Error Responses

### 404 Not Found
```json
{
  "code": 404,
  "msg": "Content item not found",
  "data": null
}
```

### 500 Server Error
```json
{
  "code": 500,
  "msg": "Failed to create content item",
  "data": null
}
```

---

## Sample Content Items

Here are some existing content item IDs you can use for testing:

### Music Items:
- `bbf2b486-b8cd-405b-9515-84ffc95ecaf3` - Twinkle Twinkle Little Star
- `1e72aa9e-3dbf-4006-8000-3db91e6c6ceb` - Baby Shark Dance
- `02efecde-9971-477f-b310-94071bfcfd88` - Johny Johny Yes Papa
- `9fe6c3da-ed9c-4098-9923-da998a8ddd4d` - Old MacDonald
- `1e72aa78-3dbf-4006-8000-3db91e6c6cc5` - Baa Baa Black Sheep

### Story Items:
- `b8c2da63-6970-47dd-9eba-d925265b46eb` - Sleeping Beauty
- `5019678d-af60-4874-a618-eee14dd480fe` - Hansel and Gretel
- `54f11754-5e63-44af-899e-dc105449af2e` - Katie Unicorn
- `c77afde2-98dd-452e-bcdf-96041482b8e9` - The Three Dogs

---

## Swagger Documentation

You can also access the interactive API documentation at:

**URL**: http://localhost:8002/toy/doc.html

This provides a UI to test all endpoints without using curl.

---

## Notes

- All timestamps are in the format: `YYYY-MM-DD HH:MM:SS`
- The `alternatives` field stores JSON arrays as strings
- Content types are restricted to: `music` or `story`
- UUIDs are automatically generated for new items if not provided
- The `updated_at` field is automatically updated on any modification
