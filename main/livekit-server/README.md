# LiveKit Server - Voice AI Agent System

A sophisticated voice AI agent system built with LiveKit Agents that provides interactive conversational experiences for children. Features multi-modal AI capabilities including voice conversation, music playback, storytelling, device control, and long-term memory.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Directory Structure](#directory-structure)
- [Installation](#installation)
- [Configuration](#configuration)
- [Core Components](#core-components)
- [Agent Tools & Functions](#agent-tools--functions)
- [Services](#services)
- [API Integration](#api-integration)
- [Audio Pipeline](#audio-pipeline)
- [Memory Management](#memory-management)
- [Error Handling](#error-handling)
- [Deployment](#deployment)
- [Development Guide](#development-guide)

---

## Overview

The LiveKit Server is a real-time voice AI agent designed for child-friendly interactions. It leverages LiveKit's infrastructure for low-latency communication and integrates multiple AI services:

- **Speech-to-Text (STT)**: Groq Whisper or Deepgram
- **Language Model (LLM)**: Groq OpenAI models
- **Text-to-Speech (TTS)**: Microsoft Edge TTS, ElevenLabs, or Groq
- **Voice Activity Detection (VAD)**: Silero VAD
- **Memory**: Mem0 for long-term conversation memory
- **Semantic Search**: Qdrant vector database for music/stories

### Key Features

- Real-time voice conversation with children
- Dynamic prompt switching (Cheeko, Story, Music, Tutor, Chat modes)
- Music and story playback with semantic search
- Device control (volume, LED lights, battery status)
- Long-term memory with Mem0
- Multi-language support
- Error recovery and fallback mechanisms
- Process pooling for performance optimization

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        User Device                          │
│                     (ESP32 / LiveKit)                       │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ WebSocket
                         │
┌────────────────────────▼────────────────────────────────────┐
│                   LiveKit Server                            │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                  Agent Session                       │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐    │   │
│  │  │    STT     │→ │    LLM     │→ │    TTS     │    │   │
│  │  │  (Groq/    │  │  (Groq)    │  │  (Edge/    │    │   │
│  │  │ Deepgram)  │  │            │  │ ElevenLabs)│    │   │
│  │  └────────────┘  └─────┬──────┘  └────────────┘    │   │
│  │                         │                            │   │
│  │                         │ Function Tools (22+)      │   │
│  │                         ▼                            │   │
│  │  ┌──────────────────────────────────────────────┐  │   │
│  │  │          Assistant (main_agent.py)           │  │   │
│  │  │  • Mode Switching   • Music Control          │  │   │
│  │  │  • Story Control    • Device Control         │  │   │
│  │  │  • Search           • Volume/Light Control   │  │   │
│  │  └──────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                    Services                          │   │
│  │  • MusicService      • StoryService                 │   │
│  │  • ChatHistoryService • PromptService               │   │
│  │  • AudioPlayer       • DeviceControl                │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────┬────────────────┬─────────────────────┘
                      │                │
        ┌─────────────┴────────┐  ┌───▼───────────┐
        │   Manager API        │  │  Mem0 Cloud   │
        │   (Backend)          │  │  (Memory)     │
        │  • Prompts/Config    │  │               │
        │  • Chat History      │  │               │
        │  • Child Profiles    │  │               │
        └──────────────────────┘  └───────────────┘
                      │
        ┌─────────────▼────────────┐
        │   Qdrant Cloud           │
        │   (Semantic Search)      │
        │  • Music Database        │
        │  • Story Database        │
        └──────────────────────────┘
```

---

## Directory Structure

```
livekit-server/
├── main.py                          # Primary entry point
├── groq_voice_agent.py              # Groq-specific agent
├── client.py                        # Client interface
├── startup_preloader.py             # Model preloader
├── ten_vad_wrapper.py               # VAD wrapper
├── requirements.txt                 # Dependencies
│
├── config/
│   └── livekit.yaml                 # LiveKit configuration
│
├── src/
│   ├── agent/                       # Agent logic
│   │   ├── main_agent.py           # Assistant with 22+ tools
│   │   ├── filtered_agent.py       # Text filtering for TTS
│   │   ├── error_handler.py        # Error recovery
│   │   ├── error_callback.py       # Error callbacks
│   │   └── create_error_audio.py   # Error audio generation
│   │
│   ├── config/                      # Configuration management
│   │   └── config_loader.py        # Centralized config loading
│   │
│   ├── providers/                   # AI/ML providers
│   │   ├── provider_factory.py     # Provider factory
│   │   ├── edge_tts_provider.py    # Microsoft Edge TTS
│   │   ├── ten_vad_wrapper.py      # TEN VAD provider
│   │   └── ollama_llm_provider.py  # Ollama LLM
│   │
│   ├── services/                    # Business logic
│   │   ├── music_service.py         # Music search/playback
│   │   ├── story_service.py         # Story search/playback
│   │   ├── unified_audio_player.py  # Audio player
│   │   ├── chat_history_service.py  # Chat logging
│   │   ├── prompt_service.py        # Prompt management
│   │   ├── semantic_search.py       # Semantic search
│   │   └── google_search_service.py # Wikipedia search
│   │
│   ├── mcp/                         # Model Context Protocol
│   │   ├── mcp_executor.py         # MCP tool execution
│   │   ├── mcp_handler.py          # MCP handlers
│   │   └── device_control_service.py # Device control
│   │
│   ├── memory/                      # Memory management
│   │   ├── mem0_provider.py        # Mem0 integration
│   │   └── local_memory_provider.py # Local memory
│   │
│   ├── handlers/                    # Event handlers
│   │   └── chat_logger.py          # Chat event logging
│   │
│   └── utils/                       # Utilities
│       ├── model_cache.py          # Model caching
│       ├── model_preloader.py      # Background preloading
│       ├── audio_state_manager.py  # Audio state tracking
│       ├── database_helper.py      # API client
│       ├── text_filter.py          # Text filtering
│       └── helpers.py              # General utilities
│
└── model_cache/                     # Cached models directory
```

---

## Installation

### Prerequisites

- Python 3.9+
- LiveKit Server running
- Manager API backend running
- (Optional) Qdrant Cloud account for semantic search
- (Optional) Mem0 Cloud account for memory

### Step 1: Clone Repository

```bash
cd C:\Users\Acer\Cheeko-esp32-server\main\livekit-server
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Configure Environment

Create a `.env` file in the root directory:

```env
# LiveKit Configuration
LIVEKIT_URL=ws://localhost:7880
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret

# Manager API
MANAGER_API_URL=http://localhost:8080
MANAGER_API_SECRET=your_api_secret

# LLM Configuration
LLM_MODEL=openai/gpt-oss-20b
FALLBACK_ENABLED=false
FALLBACK_LLM_MODEL=llama-3.1-8b-instant

# STT Configuration
STT_PROVIDER=groq
STT_MODEL=whisper-large-v3-turbo
STT_LANGUAGE=en

# TTS Configuration
TTS_PROVIDER=edge
EDGE_TTS_VOICE=en-US-AnaNeural
EDGE_TTS_RATE=+0%
EDGE_TTS_VOLUME=+0%
EDGE_TTS_PITCH=+0Hz
EDGE_TTS_SAMPLE_RATE=24000

# Memory
MEM0_ENABLED=true
MEM0_API_KEY=your_mem0_api_key

# Semantic Search (Optional)
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=your_qdrant_api_key
EMBEDDING_MODEL=all-MiniLM-L6-v2

# Google Search (Optional)
GOOGLE_SEARCH_ENABLED=false
GOOGLE_API_KEY=your_google_api_key
GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id

# CDN Configuration
CLOUDFRONT_DOMAIN=your.cloudfront.net
S3_BASE_URL=https://s3.amazonaws.com/your-bucket
USE_CDN=true

# Agent Features
PREEMPTIVE_GENERATION=false
NOISE_CANCELLATION=true
PROMPT_SYSTEM=template
```

### Step 4: Run the Agent

```bash
# Development mode
python main.py

# Production mode with worker pooling
python main.py --workers 3
```

---

## Configuration

### Configuration System

The system uses a layered configuration approach:

1. **Environment Variables** (`.env`) - Highest priority
2. **API Responses** (Manager API) - Device-specific config
3. **Hardcoded Defaults** - Fallback values

### Key Configuration Options

#### LLM Configuration

```python
# File: src/config/config_loader.py
get_groq_config() returns:
{
    'llm_model': 'openai/gpt-oss-20b',
    'stt_model': 'whisper-large-v3-turbo',
    'tts_model': 'playai-tts',
    'stt_provider': 'groq' | 'deepgram',
    'fallback_enabled': bool,
    'fallback_llm_model': 'llama-3.1-8b-instant'
}
```

#### TTS Configuration

```python
get_tts_config(api_config=None) returns:
{
    'provider': 'edge' | 'elevenlabs' | 'groq',
    'edge_voice': 'en-US-AnaNeural',
    'edge_rate': '+0%',
    'edge_volume': '+0%',
    'edge_pitch': '+0Hz',
    'elevenlabs_voice_id': str,
    'elevenlabs_model': 'eleven_turbo_v2_5'
}
```

---

## Core Components

### 1. Main Entry Point (`main.py`)

**File Reference**: `main.py:156-902`

The entry point orchestrates the entire agent lifecycle:

#### Initialization Flow

```python
async def entrypoint(ctx: JobContext):
    # Phase 1: Load configuration
    groq_config = ConfigLoader.get_groq_config()
    agent_config = ConfigLoader.get_agent_config()

    # Phase 2: Extract device MAC from room name
    device_mac = extract_mac_from_room_name(room_name)

    # Phase 3: Parallel API calls
    results = await asyncio.gather(
        db_helper.get_agent_id(device_mac),
        prompt_service.get_prompt_and_config(room_name, device_mac),
        db_helper.get_child_profile_by_mac(device_mac),
        query_mem0_memories(device_mac)
    )

    # Phase 4: Render prompt with child profile
    prompt = template.render(
        child_name=child_profile['name'],
        child_age=child_profile['age'],
        emojiList=EMOJI_LIST
    )

    # Phase 5: Create AI providers
    llm = ProviderFactory.create_llm(groq_config)
    stt = ProviderFactory.create_stt(groq_config, vad)
    tts = ProviderFactory.create_tts(groq_config, tts_config)

    # Phase 6: Initialize agent
    assistant = Assistant(instructions=prompt, tts_provider=tts)

    # Phase 7: Start session
    session = AgentSession(llm=llm, stt=stt, tts=tts)
    await session.start()
```

### 2. Assistant Agent (`src/agent/main_agent.py`)

**File Reference**: `src/agent/main_agent.py:75-902`

The primary agent class with 22+ function tools.

#### Class Structure

```python
class Assistant(FilteredAgent):
    def __init__(self, instructions: str = None, tts_provider=None):
        super().__init__(instructions=instructions, tts_provider=tts_provider)

        # Service references (injected after initialization)
        self.music_service = None
        self.story_service = None
        self.audio_player = None
        self.device_control_service = None

        # Room info
        self.room_name = None
        self.device_mac = None
```

### 3. Filtered Agent (`src/agent/filtered_agent.py`)

**File Reference**: `src/agent/filtered_agent.py:45-200`

Custom agent with text filtering for TTS output.

#### Features

- **Emoji Removal**: Removes problematic emojis that TTS can't pronounce
- **Emotion Detection**: Extracts emotions from emojis before removal
- **Sentence Buffering**: Buffers incomplete sentences for natural speech
- **Fallback Messages**: Generates fallback if LLM produces no output
- **30-Second Timeout**: Automatic fallback on LLM timeout

---

## Agent Tools & Functions

The Assistant provides 22+ function tools for the LLM to use.

### Mode Management

#### `update_agent_mode(mode_name: str)`

**File Reference**: `src/agent/main_agent.py:155-248`

Dynamically switches agent personality/template.

**Supported Modes:**
- **Cheeko** (default): Playful AI companion
- **Story**: Storytelling mode
- **Music**: Music DJ mode
- **Tutor**: Educational tutor
- **Chat**: Conversational friend

### Music Control

- `play_music(query: str)` - Search and play music
- `stop_music()` - Stop music playback
- `pause_music()` - Pause music
- `resume_music()` - Resume music
- `next_music()` - Skip to next song

**File Reference**: `src/agent/main_agent.py:303-450`

### Story Control

- `tell_story(query: str)` - Search and play stories
- `stop_story()`, `pause_story()`, `resume_story()`, `next_story()`

**File Reference**: `src/agent/main_agent.py:451-598`

### Device Control

#### Volume Control

- `set_volume(volume: int)` - Set volume 0-100
- `adjust_volume(action: str, step: int)` - Increase/decrease volume
- `get_volume()` - Get current volume level
- `mute_device()` - Mute device

#### LED Light Control

- `set_light_color(color: str, brightness: int)` - Set LED color
- `set_light_mode(mode: str)` - Set LED mode (solid, blink, rainbow)
- `set_rainbow_speed(speed: int)` - Control rainbow effect speed

#### Battery

- `check_battery_level()` - Get battery status

**File Reference**: `src/agent/main_agent.py:599-800`

### Search & Information

#### `search_wikipedia(query: str)`

**File Reference**: `src/agent/main_agent.py:801-850`

Wikipedia search with intelligent triggering.

**Mandatory Triggers:**
- Keywords: "latest", "recent", "current", "now", "today"
- Year: 2025 (current year)
- Explicit request: "search Wikipedia"

---

## Services

### Music Service

**File Reference**: `src/services/music_service.py:17-200`

```python
class MusicService:
    async def search_songs(query: str, language: str = None) -> List[Dict]:
        """
        Search songs using semantic search

        Returns: List of songs with title, filename, url, score
        """

    def get_song_url(filename: str, language: str) -> str:
        """Generate CloudFront or S3 URL"""

    async def get_all_languages() -> List[str]:
        """Get all available music languages"""
```

### Story Service

**File Reference**: `src/services/story_service.py:17-200`

Similar to MusicService but for stories.

### Chat History Service

**File Reference**: `src/services/chat_history_service.py:12-200`

```python
class ChatHistoryService:
    def __init__(self, manager_api_url, secret, device_mac, session_id, agent_id):
        self.batch_size = 5          # Messages per batch
        self.send_interval = 30      # Seconds between sends

    def add_message(chat_type: int, content: str):
        """chat_type: 1 = user, 2 = agent"""

    async def flush_messages():
        """Send buffered messages to API"""
```

### Prompt Service

**File Reference**: `src/services/prompt_service.py:11-300`

Manages prompt templates and rendering.

---

## API Integration

### Database Helper

**File Reference**: `src/utils/database_helper.py:8-150`

```python
class DatabaseHelper:
    async def get_agent_id(device_mac: str) -> str:
        """GET /agent/device/{mac}/agent-id"""

    async def get_child_profile_by_mac(device_mac: str) -> dict:
        """POST /config/child-profile-by-mac"""
```

### API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/agent/device/{mac}/agent-id` | GET | Get agent ID |
| `/config/child-profile-by-mac` | POST | Get child profile |
| `/config/agent-template` | POST | Get prompt template |
| `/agent/update-mode` | PUT | Update agent mode |
| `/chat-history/add` | POST | Save chat messages |

---

## Audio Pipeline

### Complete Audio Flow

```
USER SPEECH
    ↓
STT (Speech-to-Text)
  Provider: Groq or Deepgram
  VAD: Silero
    ↓
LLM (Language Model)
  Provider: Groq
  Model: openai/gpt-oss-20b
    ↓
FilteredAgent Processing
  - Remove emojis
  - Detect emotions
  - Buffer sentences
    ↓
TTS (Text-to-Speech)
  Provider: Edge TTS / ElevenLabs / Groq
    ↓
AGENT SPEECH OUTPUT
```

### VAD (Voice Activity Detection)

**File Reference**: `src/providers/provider_factory.py:96-110`

- **Model**: Silero VAD
- **Loading**: Main thread only
- **Purpose**: Detect speech presence

### STT Providers

- **Groq STT**: whisper-large-v3-turbo
- **Deepgram STT**: nova-3
- **Fallback**: Automatic retry

### TTS Providers

- **Edge TTS** (Microsoft - Default)
- **ElevenLabs TTS** (Premium)
- **Groq TTS**

---

## Memory Management

### Mem0 Integration

**File Reference**: `src/memory/mem0_provider.py:6-116`

```python
class Mem0MemoryProvider:
    async def save_memory(history_dict: dict, child_name: str = None):
        """Save conversation to Mem0 cloud"""

    async def query_memory(query: str) -> str:
        """Query memories - returns formatted memory string"""
```

### Memory Flow

1. **Session Start**: Query memories in parallel with API calls
2. **Prompt Injection**: Replace `<memory>` placeholder
3. **Session End**: Save conversation to Mem0

---

## Error Handling

### Error Recovery Manager

**File Reference**: `src/agent/error_handler.py:19-100`

```python
class ErrorRecoveryManager:
    def __init__(self, max_retries: int = 3):
        self.error_counts = {}
        self.max_retries = max_retries
        self.fallback_messages = {...}

    def should_recover(error_type: str) -> bool:
        """Returns True if error_count < max_retries"""

    def get_fallback_message(error_type: str) -> str:
        """Returns random fallback message"""
```

### Fallback Providers

- **LLM Fallback**: Primary + faster fallback model
- **STT Fallback**: Primary + Groq fallback
- **TTS Fallback**: Primary + Edge TTS fallback

---

## Deployment

### Development

```bash
python main.py
```

### Production (with worker pooling)

```bash
python main.py --workers 3
```

### Worker Pooling Configuration

**File Reference**: `main.py:910-918`

```python
cli.run_app(WorkerOptions(
    entrypoint_fnc=entrypoint,
    prewarm_fnc=prewarm,
    num_idle_processes=3,
    initialize_process_timeout=120.0,
    job_memory_warn_mb=2000,
))
```

---

## Development Guide

### Adding New Agent Tools

```python
# File: src/agent/main_agent.py

@self._ctx.ai_callable(
    description="Your tool description"
)
async def my_new_tool(
    param1: Annotated[str, llm.TypeInfo(description="Param description")]
):
    """Tool implementation"""
    try:
        result = do_something(param1)
        return f"Success: {result}"
    except Exception as e:
        return f"Error: {str(e)}"
```

### Testing

```bash
# Manual testing with LiveKit room
python main.py
# Join room with LiveKit client
```

### Debugging

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## Troubleshooting

### Common Issues

**Agent not responding**
- Check LiveKit connection
- Verify Groq API key
- Check error logs

**Music/stories not playing**
- Verify Qdrant connection
- Check S3/CloudFront URLs
- Ensure USE_CDN is set correctly

**Memory not persisting**
- Verify MEM0_ENABLED=true
- Check Mem0 API key

**High latency**
- Enable worker pooling: `--workers 3`
- Use CloudFront CDN

---

## Additional Resources

- **LiveKit Documentation**: https://docs.livekit.io/
- **Groq API Docs**: https://console.groq.com/docs
- **Mem0 Docs**: https://docs.mem0.ai/
- **Qdrant Docs**: https://qdrant.tech/documentation/

---

**Last Updated**: 2025-10-28
