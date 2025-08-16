# Mobile API Specification for Flutter Parental App

## Overview
This document defines the REST API endpoints that your Flutter mobile app will consume. These endpoints bridge Supabase authentication with Railway MySQL toy data.

## Base Configuration
```yaml
Base URL: https://your-domain.com/api/mobile
Authentication: Bearer JWT (from Supabase)
Content-Type: application/json
API Version: v1
```

## Authentication Flow

### 1. Verify Supabase Token
```http
POST /api/mobile/auth/verify
Content-Type: application/json
Authorization: Bearer <supabase_jwt_token>

Request Body:
{
  "supabase_user_id": "uuid-from-supabase",
  "email": "parent@example.com",
  "full_name": "Parent Name"
}

Response 200:
{
  "success": true,
  "user_verified": true,
  "has_active_devices": false,
  "message": "User verified successfully"
}

Response 401:
{
  "success": false,
  "error": "Invalid or expired token",
  "code": "AUTH_INVALID_TOKEN"
}
```

## Device Activation APIs

### 1. Validate Activation Code
```http
POST /api/mobile/activation/validate
Authorization: Bearer <supabase_jwt_token>

Request Body:
{
  "activation_code": "123456",
  "child_name": "Emma",
  "child_age": 5,
  "child_interests": ["animals", "stories", "counting"]
}

Response 200:
{
  "success": true,
  "activation_id": "uuid",
  "toy_serial_number": "CHEEKO-20250816-000001",
  "toy_model": "CHEEKO-V1",
  "device_mac": "68:25:dd:bc:03:7c",
  "message": "Device activated successfully"
}

Response 400:
{
  "success": false,
  "error": "Invalid activation code",
  "code": "ACTIVATION_INVALID_CODE"
}

Response 409:
{
  "success": false,
  "error": "Device already activated",
  "code": "DEVICE_ALREADY_ACTIVE"
}
```

### 2. Get Activation Status
```http
GET /api/mobile/activation/{activation_id}/status
Authorization: Bearer <supabase_jwt_token>

Response 200:
{
  "activation_id": "uuid",
  "status": "active", // pending, active, inactive, error
  "device_online": true,
  "device_last_seen": "2025-08-16T12:30:00Z",
  "sync_status": "connected", // connected, disconnected, syncing
  "last_sync": "2025-08-16T12:25:00Z"
}
```

### 3. List User's Devices
```http
GET /api/mobile/devices
Authorization: Bearer <supabase_jwt_token>

Response 200:
{
  "devices": [
    {
      "activation_id": "uuid",
      "child_name": "Emma",
      "child_age": 5,
      "toy_model": "CHEEKO-V1",
      "device_mac": "68:25:dd:bc:03:7c",
      "activation_status": "active",
      "device_online": true,
      "activated_at": "2025-08-16T10:00:00Z"
    }
  ],
  "total_devices": 1
}
```

## Dashboard APIs

### 1. Get Dashboard Summary
```http
GET /api/mobile/dashboard/{activation_id}
Authorization: Bearer <supabase_jwt_token>

Response 200:
{
  "child_info": {
    "name": "Emma",
    "age": 5,
    "device_online": true,
    "last_activity": "2025-08-16T11:45:00Z"
  },
  "today_summary": {
    "conversations": 12,
    "duration_minutes": 45,
    "mood": "happy", // happy, neutral, sad, excited
    "mood_score": 0.8, // -1 to 1
    "engagement_level": "high" // low, medium, high
  },
  "week_summary": {
    "total_conversations": 78,
    "average_daily_minutes": 35,
    "consistency_score": 0.85,
    "trend": "increasing" // increasing, decreasing, stable
  },
  "recent_achievement": {
    "milestone_name": "First 50 Words",
    "achieved_at": "2025-08-15T16:30:00Z",
    "description": "Emma has learned 50 new words!"
  },
  "highlights": [
    "Showed great interest in ocean animals",
    "Asked 8 creative questions about dolphins",
    "Demonstrated counting skills up to 20"
  ],
  "concerns": [],
  "recommendations": [
    "Try exploring more math concepts",
    "Continue with animal-themed conversations"
  ]
}
```

### 2. Get Daily Analytics
```http
GET /api/mobile/analytics/{activation_id}/daily
Authorization: Bearer <supabase_jwt_token>
Query Parameters:
  - date: 2025-08-16 (optional, defaults to today)
  - timezone: America/New_York (optional)

Response 200:
{
  "date": "2025-08-16",
  "summary": {
    "total_conversations": 12,
    "duration_minutes": 45,
    "average_session_duration": 3.75,
    "longest_session": 8,
    "topics_discussed": ["animals", "counting", "colors"],
    "new_words_learned": 3,
    "questions_asked": 8,
    "overall_sentiment": 0.8,
    "engagement_level": "high"
  },
  "hourly_activity": [
    {
      "hour": 9,
      "conversations": 3,
      "duration_minutes": 12,
      "mood_score": 0.9
    }
    // ... more hours
  ],
  "top_topics": [
    {
      "topic": "ocean animals",
      "frequency": 5,
      "engagement": 0.9
    }
  ],
  "ai_insights": "Emma showed exceptional curiosity about ocean animals today, asking thoughtful questions about dolphin behavior and whale migration."
}
```

### 3. Get Weekly Analytics
```http
GET /api/mobile/analytics/{activation_id}/weekly
Authorization: Bearer <supabase_jwt_token>
Query Parameters:
  - week_start: 2025-08-10 (optional, defaults to current week)

Response 200:
{
  "week_start": "2025-08-10",
  "week_end": "2025-08-16",
  "summary": {
    "total_conversations": 78,
    "total_duration_minutes": 285,
    "average_daily_engagement": 40.7,
    "consistency_score": 0.85,
    "vocabulary_growth_rate": 2.3,
    "engagement_trend": "increasing"
  },
  "daily_breakdown": [
    {
      "date": "2025-08-10",
      "conversations": 10,
      "duration_minutes": 38,
      "mood_score": 0.7
    }
    // ... rest of week
  ],
  "learning_progress": {
    "milestones_achieved": [
      {
        "name": "First 50 Words",
        "achieved_at": "2025-08-15T16:30:00Z"
      }
    ],
    "skills_improved": ["vocabulary", "counting", "social_interaction"],
    "areas_for_growth": ["problem_solving", "creativity"]
  },
  "weekly_insights": "Emma has shown remarkable growth this week, particularly in vocabulary and social interaction skills."
}
```

## Conversation History APIs

### 1. Get Conversation History
```http
GET /api/mobile/conversations/{activation_id}
Authorization: Bearer <supabase_jwt_token>
Query Parameters:
  - date: 2025-08-16 (optional)
  - limit: 50 (optional, default 20, max 100)
  - offset: 0 (optional)
  - category: education (optional filter)

Response 200:
{
  "conversations": [
    {
      "id": 12345,
      "session_id": "session_abc123",
      "timestamp": "2025-08-16T11:45:00Z",
      "messages": [
        {
          "type": "child",
          "content": "Tell me about dolphins!",
          "timestamp": "2025-08-16T11:45:00Z"
        },
        {
          "type": "ai",
          "content": "Dolphins are amazing sea creatures! They're very smart and love to play. Did you know they can jump really high out of the water?",
          "timestamp": "2025-08-16T11:45:05Z"
        }
      ],
      "category": "education",
      "sub_category": "animals",
      "duration_minutes": 3.5,
      "sentiment_score": 0.9,
      "educational_value": 0.8,
      "keywords": ["dolphins", "ocean", "animals", "jumping"]
    }
  ],
  "pagination": {
    "total": 156,
    "limit": 20,
    "offset": 0,
    "has_more": true
  }
}
```

### 2. Get Conversation Details
```http
GET /api/mobile/conversations/{activation_id}/{conversation_id}
Authorization: Bearer <supabase_jwt_token>

Response 200:
{
  "id": 12345,
  "session_id": "session_abc123",
  "started_at": "2025-08-16T11:45:00Z",
  "ended_at": "2025-08-16T11:48:30Z",
  "duration_minutes": 3.5,
  "message_count": 12,
  "messages": [
    {
      "id": 67890,
      "type": "child", // child, ai
      "content": "Tell me about dolphins!",
      "timestamp": "2025-08-16T11:45:00Z",
      "audio_available": true
    }
    // ... all messages
  ],
  "analytics": {
    "category": "education",
    "sub_category": "animals",
    "sentiment_score": 0.9,
    "educational_value": 0.8,
    "complexity_level": "medium",
    "child_initiated": true,
    "vocabulary_used": ["intelligent", "mammals", "echolocation"],
    "concepts_discussed": ["marine biology", "animal behavior"]
  }
}
```

## Milestones & Achievements APIs

### 1. Get Milestones
```http
GET /api/mobile/milestones/{activation_id}
Authorization: Bearer <supabase_jwt_token>
Query Parameters:
  - status: achieved (optional: all, in_progress, achieved)
  - type: vocabulary (optional: vocabulary, social, cognitive, creative)

Response 200:
{
  "milestones": [
    {
      "id": 101,
      "type": "vocabulary",
      "name": "First 100 Words",
      "description": "Learn and use 100 different words in conversations",
      "target_value": 100,
      "current_value": 67,
      "progress_percentage": 67,
      "status": "in_progress",
      "age_group": "4-5",
      "difficulty": "medium",
      "estimated_completion": "2025-09-15"
    },
    {
      "id": 102,
      "type": "social",
      "name": "Polite Conversations",
      "description": "Consistently use please, thank you, and excuse me",
      "status": "achieved",
      "achieved_at": "2025-08-15T16:30:00Z"
    }
  ],
  "summary": {
    "total_milestones": 12,
    "achieved": 3,
    "in_progress": 7,
    "not_started": 2
  }
}
```

### 2. Get Recent Achievements
```http
GET /api/mobile/achievements/{activation_id}
Authorization: Bearer <supabase_jwt_token>
Query Parameters:
  - limit: 10 (optional, default 5)
  - days: 30 (optional, default 7)

Response 200:
{
  "achievements": [
    {
      "milestone_name": "First 50 Words",
      "achieved_at": "2025-08-15T16:30:00Z",
      "description": "Emma has learned 50 new words!",
      "difficulty": "medium",
      "related_conversations": 23
    }
  ],
  "total_achievements_this_period": 1
}
```

## Settings APIs

### 1. Get Settings
```http
GET /api/mobile/settings/{activation_id}
Authorization: Bearer <supabase_jwt_token>

Response 200:
{
  "child_profile": {
    "name": "Emma",
    "age": 5,
    "learning_level": "beginner",
    "preferred_topics": ["animals", "stories", "counting"],
    "language_preference": "en"
  },
  "content_settings": {
    "daily_time_limit_minutes": 60,
    "bedtime_cutoff": "20:00",
    "content_filters": {
      "inappropriate_content": true,
      "violence": true,
      "adult_themes": true
    },
    "educational_focus": ["creativity", "learning", "social_skills"]
  },
  "privacy_settings": {
    "analytics_enabled": true,
    "audio_storage_enabled": true,
    "data_retention_days": 90
  },
  "notification_settings": {
    "daily_summary_enabled": true,
    "daily_summary_time": "19:00",
    "achievement_notifications": true,
    "concern_alerts": true
  }
}
```

### 2. Update Settings
```http
PUT /api/mobile/settings/{activation_id}
Authorization: Bearer <supabase_jwt_token>

Request Body:
{
  "child_profile": {
    "preferred_topics": ["animals", "stories", "math"],
    "learning_level": "intermediate"
  },
  "content_settings": {
    "daily_time_limit_minutes": 45
  },
  "notification_settings": {
    "daily_summary_time": "18:30"
  }
}

Response 200:
{
  "success": true,
  "message": "Settings updated successfully",
  "synced_to_supabase": true
}
```

## Real-time APIs

### 1. WebSocket Connection
```javascript
// WebSocket URL for real-time updates
ws://your-domain.com/api/mobile/realtime/{activation_id}

// Authentication via query parameter or header
ws://your-domain.com/api/mobile/realtime/{activation_id}?token=<jwt_token>

// Message types received:
{
  "type": "device_status",
  "data": {
    "online": true,
    "last_seen": "2025-08-16T12:30:00Z"
  }
}

{
  "type": "new_conversation",
  "data": {
    "conversation_id": 12345,
    "started_at": "2025-08-16T12:30:00Z",
    "preview": "Child started talking about space..."
  }
}

{
  "type": "daily_summary_ready",
  "data": {
    "date": "2025-08-16",
    "total_conversations": 12,
    "highlights": ["Great curiosity about science today!"]
  }
}

{
  "type": "achievement_unlocked",
  "data": {
    "milestone_name": "Science Explorer",
    "achieved_at": "2025-08-16T14:30:00Z"
  }
}
```

### 2. Server-Sent Events (Alternative)
```http
GET /api/mobile/events/{activation_id}
Authorization: Bearer <supabase_jwt_token>
Accept: text/event-stream

Response:
data: {"type": "device_status", "data": {"online": true}}

data: {"type": "new_conversation", "data": {"conversation_id": 12345}}

data: {"type": "heartbeat", "timestamp": "2025-08-16T12:30:00Z"}
```

## Error Handling

### Standard Error Response Format
```json
{
  "success": false,
  "error": "Human readable error message",
  "code": "ERROR_CODE",
  "details": {
    "field": "specific field that caused error",
    "validation_errors": []
  },
  "timestamp": "2025-08-16T12:30:00Z",
  "request_id": "req_abc123"
}
```

### Error Codes
```yaml
Authentication Errors:
  - AUTH_INVALID_TOKEN: JWT token is invalid or expired
  - AUTH_MISSING_TOKEN: Authorization header missing
  - AUTH_USER_NOT_FOUND: Supabase user not found

Activation Errors:
  - ACTIVATION_INVALID_CODE: 6-digit code is invalid
  - ACTIVATION_CODE_EXPIRED: Code has expired
  - ACTIVATION_CODE_USED: Code already used
  - DEVICE_ALREADY_ACTIVE: Device is already activated
  - DEVICE_NOT_FOUND: Device MAC not found in system

Data Errors:
  - ACTIVATION_NOT_FOUND: Activation ID not found
  - INSUFFICIENT_PERMISSIONS: User doesn't own this device
  - INVALID_DATE_RANGE: Date parameters are invalid
  - DATA_NOT_AVAILABLE: Analytics data not yet available

System Errors:
  - INTERNAL_ERROR: Server error
  - SERVICE_UNAVAILABLE: Railway database connection issue
  - RATE_LIMIT_EXCEEDED: Too many requests
```

## Rate Limiting
```yaml
Authentication: 10 requests/minute
Activation: 5 requests/minute  
Dashboard: 60 requests/minute
Analytics: 30 requests/minute
Conversations: 100 requests/minute
Real-time: 1 connection per device
```

## Flutter Integration Examples

### 1. Authentication Service
```dart
class AuthService {
  static const String baseUrl = 'https://your-domain.com/api/mobile';
  
  Future<bool> verifySupabaseToken(User user) async {
    final response = await http.post(
      Uri.parse('$baseUrl/auth/verify'),
      headers: {
        'Authorization': 'Bearer ${user.accessToken}',
        'Content-Type': 'application/json',
      },
      body: jsonEncode({
        'supabase_user_id': user.id,
        'email': user.email,
        'full_name': user.userMetadata?['full_name'],
      }),
    );
    
    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      return data['user_verified'] == true;
    }
    
    throw Exception('Token verification failed');
  }
}
```

### 2. Device Activation Service
```dart
class ActivationService {
  Future<ActivationResult> activateDevice({
    required String activationCode,
    required String childName,
    required int childAge,
    required List<String> interests,
  }) async {
    final user = Supabase.instance.client.auth.currentUser!;
    
    final response = await http.post(
      Uri.parse('$baseUrl/activation/validate'),
      headers: {
        'Authorization': 'Bearer ${user.accessToken}',
        'Content-Type': 'application/json',
      },
      body: jsonEncode({
        'activation_code': activationCode,
        'child_name': childName,
        'child_age': childAge,
        'child_interests': interests,
      }),
    );
    
    final data = jsonDecode(response.body);
    
    if (response.statusCode == 200 && data['success']) {
      return ActivationResult.success(
        activationId: data['activation_id'],
        toySerialNumber: data['toy_serial_number'],
        deviceMac: data['device_mac'],
      );
    }
    
    return ActivationResult.error(
      message: data['error'],
      code: data['code'],
    );
  }
}
```

### 3. Dashboard Service
```dart
class DashboardService {
  Future<DashboardData> getDashboardSummary(String activationId) async {
    final user = Supabase.instance.client.auth.currentUser!;
    
    final response = await http.get(
      Uri.parse('$baseUrl/dashboard/$activationId'),
      headers: {
        'Authorization': 'Bearer ${user.accessToken}',
      },
    );
    
    if (response.statusCode == 200) {
      return DashboardData.fromJson(jsonDecode(response.body));
    }
    
    throw Exception('Failed to load dashboard data');
  }
}
```

### 4. Real-time Connection
```dart
class RealtimeService {
  late WebSocketChannel _channel;
  
  void connect(String activationId) {
    final user = Supabase.instance.client.auth.currentUser!;
    final uri = Uri.parse('ws://your-domain.com/api/mobile/realtime/$activationId?token=${user.accessToken}');
    
    _channel = WebSocketChannel.connect(uri);
    
    _channel.stream.listen((message) {
      final data = jsonDecode(message);
      _handleRealtimeMessage(data);
    });
  }
  
  void _handleRealtimeMessage(Map<String, dynamic> message) {
    switch (message['type']) {
      case 'device_status':
        // Update device online status
        break;
      case 'new_conversation':
        // Show notification or update UI
        break;
      case 'achievement_unlocked':
        // Show achievement popup
        break;
    }
  }
}
```

This API specification provides everything your Flutter app needs to authenticate parents, activate devices, and display rich analytics from the toy interactions.