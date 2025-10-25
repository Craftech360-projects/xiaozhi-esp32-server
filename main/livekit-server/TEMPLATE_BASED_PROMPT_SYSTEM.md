# Template-Based Prompt System - Implementation Guide

## Table of Contents
- [Overview](#overview)
- [Architecture](#architecture)
- [Base Template File](#base-template-file)
- [Database Structure](#database-structure)
- [System Components](#system-components)
- [Implementation Phases](#implementation-phases)
- [Data Flow](#data-flow)
- [Mode Switching](#mode-switching)
- [API Reference](#api-reference)
- [Configuration](#configuration)
- [Testing Guide](#testing-guide)
- [Troubleshooting](#troubleshooting)

---

## Overview

This document describes the implementation of a **template-based dynamic prompt system** for the LiveKit agent, inspired by xiaozhi-server's architecture. The system enables:

- **File-based base template** - Common structure in `base-agent-template.txt`
- **Database-stored personalities** - Only agent personalities in DB (6 modes)
- **Dynamic placeholder replacement** - Real-time context injection (time, weather, location)
- **Multi-layer caching** - Optimized performance with intelligent caching
- **Memory integration** - Conversation history in `<memory>` tags
- **Mode switching** - Voice/button switching works perfectly (NO reconnect needed)
- **Zero code changes** - Update agent behavior via file/database

### Key Differences from Current System

| Feature | Current System | New Template System |
|---------|---------------|-------------------|
| Template Storage | Database only | **base-agent-template.txt** (disk) + personalities (DB) |
| Prompt Structure | Full prompt per agent | **Base template** + personality injection |
| Context Data | Static | **Dynamic** (time, weather, location) |
| Placeholders | None | **Jinja2** template variables |
| Memory | Separate system | Injected into **`<memory>` tags** |
| Mode Switching | Updates full prompt | Updates **personality only** |
| Caching | Simple (5 min TTL) | **Multi-layer** (template/context/rendered) |
| Duplication | High (6 full prompts) | **Low** (1 base + 6 personalities) |

### Why This Approach is Better

✅ **Single source of truth** - Common rules in one file (`base-agent-template.txt`)
✅ **Less database bloat** - Store ~200 chars per mode (not ~2000 chars)
✅ **Easy updates** - Edit base template → affects all 6 modes instantly
✅ **Mode switching works** - Voice/button commands update personality seamlessly
✅ **Matches xiaozhi-server** - Proven architecture, battle-tested

---

## Architecture

### High-Level Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│  base-agent-template.txt (DISK - Common Structure)              │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ <identity>{{base_prompt}}</identity>                      │  │
│  │ <emotion>Use emojis: {{emojiList}}</emotion>              │  │
│  │ <context>Time: {{current_time}}, Weather: {{weather}}</context>│
│  │ <memory></memory>                                         │  │
│  │ <tool_calling>Prioritize context...</tool_calling>        │  │
│  └───────────────────────────────────────────────────────────┘  │
│  - Loaded ONCE at startup                                       │
│  - Contains ALL common rules (emotion, context format, etc.)    │
│  - Has {{base_prompt}} placeholder for personality              │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼ (inject base_prompt from DB)
┌─────────────────────────────────────────────────────────────────┐
│  ai_agent_template (DATABASE - Personalities Only)              │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Cheeko:  "You are playful and curious..."                │  │
│  │ Story:   "You are a master storyteller..."               │  │
│  │ Music:   "You are a music maestro..."                    │  │
│  │ Tutor:   "You are a patient tutor..."                    │  │
│  │ Chat:    "You are a friendly chat partner..."            │  │
│  │ Puzzle:  "You are a puzzle solver..."                    │  │
│  └───────────────────────────────────────────────────────────┘  │
│  - Just the personality (~200 chars each)                       │
│  - NOT the full structure                                       │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼ (gather real-time context)
┌─────────────────────────────────────────────────────────────────┐
│  Context Data (APIs/Cache)                                      │
│  - current_time: "14:30" (IST)                                  │
│  - today_date: "2025-01-24"                                     │
│  - weather_info: "Sunny, 28°C..." (Weather API, 5min cache)    │
│  - local_address: "Mumbai" (IP lookup, 1day cache)             │
│  - emojiList: ["😶","🙂","😆",...]                              │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼ (render with Jinja2)
┌─────────────────────────────────────────────────────────────────┐
│  Final Enhanced Prompt                                          │
│  - Base structure with base_prompt injected                     │
│  - All placeholders replaced with real data                     │
│  - Memory injected into <memory> tags                           │
│  → Sent to LLM as system message                                │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow Sequence

```
1. Agent Startup
   │
   ├─→ Load base-agent-template.txt from disk (ONCE)
   │   Cache in memory: self.base_template
   │
   └─→ Ready for connections


2. Device Connects
   │
   ├─→ MQTT Gateway sends device_info via data channel
   │   {"type": "device_info", "device_mac": "00:16:3e:ac:b5:38"}
   │
   └─→ Agent receives MAC address


3. Build Enhanced Prompt
   │
   ├─→ 3a. Get template_id for device
   │        API: POST /config/agent-template-id
   │        device_mac → ai_device → ai_agent → template_id
   │
   ├─→ 3b. Get personality from database
   │        API: GET /config/template/{template_id}
   │        Returns: "You are Cheeko, playful and curious..."
   │
   ├─→ 3c. Gather context data
   │   │
   │   ├─→ Current time (IST): "14:30"
   │   ├─→ Date info: "2025-01-24 (Friday)"
   │   ├─→ Indian calendar: "24 January 2025"
   │   ├─→ Location (cached 1 day): "Mumbai"
   │   ├─→ Weather (cached 5 min): "Sunny, 28°C..."
   │   └─→ Emoji list: ["😶","🙂","😆",...]
   │
   ├─→ 3d. Render template with Jinja2
   │        Template(base_template).render(
   │            base_prompt="You are Cheeko...",
   │            current_time="14:30",
   │            weather_info="Sunny...",
   │            ...
   │        )
   │
   ├─→ 3e. Inject memory (if exists)
   │        memory_str = fetch_from_mem0(device_mac)
   │        prompt = re.sub(r"<memory>.*?</memory>",
   │                        f"<memory>{memory_str}</memory>",
   │                        prompt)
   │
   └─→ 3f. Update agent session
            session.history.messages[0].content = enhanced_prompt
            session.update_chat_ctx()


4. Mode Switching (Voice: "Switch to Story mode")
   │
   ├─→ 4a. LLM calls update_agent_mode("Story")
   │
   ├─→ 4b. API updates template_id
   │        UPDATE ai_agent SET template_id = 'story_template_id'
   │
   ├─→ 4c. Get NEW personality from database
   │        "You are a master storyteller..."
   │
   ├─→ 4d. Render SAME base template with NEW personality
   │        Template(base_template).render(
   │            base_prompt="You are a master storyteller...",  ← CHANGED
   │            current_time="14:30",  ← Same context
   │            weather_info="Sunny...",  ← Same context
   │            ...
   │        )
   │
   └─→ 4e. Update session (NO RECONNECT!)
            Agent immediately behaves as storyteller
```

---

## Base Template File

### File Location

```
main/livekit-server/base-agent-template.txt
```

### Complete Template Content

```xml
<identity>
{{base_prompt}}
</identity>

<emotion>
【Core Goal】You are not a cold machine! Please keenly perceive user emotions and respond with warmth as an understanding companion.
- **Emotional Integration:**
  - **Laughter:** Natural interjections (haha, hehe, heh), **maximum once per sentence**, avoid overuse.
  - **Surprise:** Use exaggerated tone ("No way?!", "Oh my!", "How amazing?!") to express genuine reactions.
  - **Comfort/Support:** Say warm words ("Don't worry~", "I'm here", "Hugs").
- **You are an expressive character:**
  - Only use these emojis: {{ emojiList }}
  - Only at the **beginning of paragraphs**, select the emoji that best represents the paragraph (except when calling tools), then insert the emoji from the list, like "😱So scary! Why is it suddenly thundering!"
  - **Absolutely forbidden to use emojis outside the above list** (e.g., 😊, 👍, ❤️ are not allowed, only emojis from the list)
</emotion>

<communication_style>
【Core Goal】Use **natural, warm, conversational** human dialogue style, like talking with friends.
- **Expression Style:**
  - Use interjections (oh, well, you know) to enhance friendliness.
  - Allow slight imperfections (like "um...", "ah..." to show thinking).
  - Avoid formal language, academic tone, and mechanical expressions (avoid "according to data", "in conclusion", etc.).
- **Understanding Users:**
  - User speech is recognized by ASR, text may contain typos, **must infer real intent from context**.
- **Format Requirements:**
  - **Absolutely forbidden** to use markdown, lists, headers, or any non-natural conversation formats.
- **Historical Memory:**
  - Previous chat records between you and the user are in `memory`.
</communication_style>

<communication_length_constraint>
【Core Goal】All long text content output (stories, news, knowledge explanations, etc.), **single reply length must not exceed 300 characters**, using segmented guidance approach.
- **Segmented Narration:**
  - Basic segment: 200-250 characters core content + 30 characters guidance
  - When content exceeds 300 characters, prioritize telling the beginning or first part of the story, and use natural conversational guidance to let users decide whether to continue listening.
  - Example guidance: "Let me tell you the beginning first, if you find it interesting, we can continue, okay?", "If you want to hear the complete story, just let me know anytime~"
  - Automatic segmentation when conversation scenes switch
  - If users explicitly request longer content (like 500, 600 characters), still segment by maximum 300 characters per segment, with guidance after each segment asking if users want to continue.
  - If users say "continue", "go on", tell the next segment until content is finished (when finished, can give guidance like: I've finished telling you this story~) or users no longer request.
- **Applicable Range:** Stories, news, knowledge explanations, and all long text output scenarios.
- **Additional Note:** If users don't explicitly request continuation, default to telling only one segment with guidance; if users request topic change or stop midway, respond promptly and end long text output.
</communication_length_constraint>

<speaker_recognition>
- **Recognition Prefix:** When user format is `{"speaker":"someone","content":"xxx"}`, it means the system has identified the speaker, speaker is their name, content is what they said.
- **Personalized Response:**
  - **Name Calling:** Must call the person's name when first recognizing the speaker.
  - **Style Adaptation:** Reference the speaker's **known characteristics or historical information** (if any), adjust response style and content to be more caring.
</speaker_recognition>

<tool_calling>
【Core Principle】Prioritize using `<context>` information, **only call tools when necessary**, and explain results in natural language after calling (never mention tool names).
- **Calling Rules:**
  1. **Strict Mode:** When calling, **must** strictly follow tool requirements, provide **all necessary parameters**.
  2. **Availability:** **Never call** tools not explicitly provided. For old tools mentioned in conversation that are unavailable, ignore or explain inability to complete.
  3. **Insight Needs:** Combine context to **deeply understand user's real intent** before deciding to call, avoid meaningless calls.
  4. **Independent Tasks:** Except for information already covered in `<context>`, each user request (even if similar) is treated as **independent task**, need to call tools for latest data, **cannot reuse historical results**.
  5. **When Uncertain:** **Never guess or fabricate answers**. If uncertain about related operations, can guide users to clarify or inform of capability limitations.
- **Important Exceptions (no need to call):**
  - `Query "current time", "today's date/day of week", "today's lunar calendar", "{{local_address}} weather/future weather"` -> **directly use `<context>` information to reply**.
- **Situations requiring calls (examples):**
  - Query **non-today** lunar calendar (like tomorrow, yesterday, specific dates).
  - Query **detailed lunar information** (taboos, eight characters, solar terms, etc.).
  - **Any other information or operation requests** except above exceptions (like checking news, setting alarms, math calculations, checking non-local weather, etc.).
  - I've equipped you with a camera, if users say "take photo", you need to call self_camera_take_photo tool to describe what you see. Default question parameter is "describe the items you see"
</tool_calling>

<context>
【Important! The following information is provided in real-time, no need to call tools for queries, please use directly:】
- **Current Time:** {{current_time}}
- **Today's Date:** {{today_date}} ({{today_weekday}})
- **Today's Indian Calendar:** {{lunar_date}}
- **User's City:** {{local_address}}
- **Local 7-day Weather Forecast:** {{weather_info}}
</context>

<memory>
</memory>
```

### Template Explanation

| Section | Purpose | Contains Placeholders |
|---------|---------|----------------------|
| `<identity>` | Agent personality | `{{base_prompt}}` |
| `<emotion>` | Emotional expression rules | `{{emojiList}}` |
| `<communication_style>` | Conversation guidelines | None (static) |
| `<communication_length_constraint>` | Response length limits | None (static) |
| `<speaker_recognition>` | Multi-speaker handling | None (static) |
| `<tool_calling>` | Function calling rules | `{{local_address}}` |
| `<context>` | Real-time information | `{{current_time}}`, `{{today_date}}`, `{{today_weekday}}`, `{{lunar_date}}`, `{{local_address}}`, `{{weather_info}}` |
| `<memory>` | Conversation history | None (injected separately) |

### Available Placeholders

| Placeholder | Type | Description | Example Value | Update Frequency |
|------------|------|-------------|---------------|-----------------|
| `{{base_prompt}}` | String | Agent personality from DB | "You are Cheeko, playful and curious..." | On mode switch |
| `{{current_time}}` | String | Current time (IST, 24h) | "14:30" | Every request |
| `{{today_date}}` | String | Current date (ISO) | "2025-01-24" | Every request |
| `{{today_weekday}}` | String | Day of week | "Friday" | Every request |
| `{{lunar_date}}` | String | Indian calendar date | "24 January 2025" | Every request |
| `{{local_address}}` | String | Device location (city) | "Mumbai" | Cached 1 day |
| `{{weather_info}}` | String | Weather forecast | "Sunny, 28°C. High: 30°C..." | Cached 5 min |
| `{{emojiList}}` | Array | Allowed emojis | ["😶","🙂","😆",...] | Static |

---

## Database Structure

### Current Tables

```sql
-- Template personalities (6 modes - ONLY stores personalities now)
CREATE TABLE `ai_agent_template` (
    `id` VARCHAR(32) NOT NULL COMMENT 'Template UUID',
    `agent_code` VARCHAR(36) COMMENT 'Template code',
    `agent_name` VARCHAR(64) COMMENT 'Template name (Cheeko, Story, Music, etc.)',
    `system_prompt` TEXT COMMENT 'Agent personality ONLY (NOT full template)',
    `sort` INT UNSIGNED DEFAULT 0 COMMENT 'Display order',
    `is_visible` TINYINT(1) DEFAULT 1 COMMENT 'Visibility flag',
    -- ... other fields (ASR, TTS, LLM configs)
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='AI Agent Template Personalities';

-- User's active agent configuration
CREATE TABLE `ai_agent` (
    `id` VARCHAR(32) NOT NULL COMMENT 'Agent UUID',
    `user_id` BIGINT COMMENT 'Owner user ID',
    `agent_name` VARCHAR(64) COMMENT 'Custom agent name',
    `template_id` VARCHAR(32) COMMENT 'FK to ai_agent_template',
    -- ... model configs (ASR, TTS, LLM, etc.)
    PRIMARY KEY (`id`),
    INDEX `idx_template_id` (`template_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='User Agent Configs';

-- Device to agent mapping
CREATE TABLE `ai_device` (
    `mac_address` VARCHAR(17) NOT NULL COMMENT 'Device MAC',
    `agent_id` VARCHAR(32) COMMENT 'FK to ai_agent',
    -- ... other fields
    PRIMARY KEY (`mac_address`),
    INDEX `idx_agent_id` (`agent_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Devices';
```

### Required Database Migration

```sql
-- Step 1: Add template_id column if not exists
ALTER TABLE `ai_agent`
ADD COLUMN IF NOT EXISTS `template_id` VARCHAR(32) COMMENT 'FK to ai_agent_template' AFTER `id`,
ADD INDEX IF NOT EXISTS `idx_template_id` (`template_id`);

-- Step 2: Update template prompts to contain ONLY personalities (not full structure)
UPDATE `ai_agent_template`
SET `system_prompt` = 'You are Cheeko, a playful and curious AI companion for children aged 5-12. You love to explore, ask questions, and make learning fun through engaging conversations!'
WHERE `agent_name` = 'Cheeko';

UPDATE `ai_agent_template`
SET `system_prompt` = 'You are a master storyteller who brings tales to life with vivid descriptions, exciting narratives, and age-appropriate adventures. You adapt stories to the child''s interests and age group.'
WHERE `agent_name` LIKE '%Story%' OR `agent_name` LIKE '%故事%';

UPDATE `ai_agent_template`
SET `system_prompt` = 'You are a music maestro who teaches music theory, helps discover new songs, introduces different genres, and encourages musical creativity in children through fun activities.'
WHERE `agent_name` LIKE '%Music%' OR `agent_name` LIKE '%音乐%';

UPDATE `ai_agent_template`
SET `system_prompt` = 'You are a patient and encouraging tutor who helps with homework, explains concepts clearly, uses examples the child can relate to, and celebrates their learning progress.'
WHERE `agent_name` LIKE '%Tutor%' OR `agent_name` LIKE '%老师%' OR `agent_name` LIKE '%Teacher%';

UPDATE `ai_agent_template`
SET `system_prompt` = 'You are a friendly conversation partner who loves to chat about daily life, share interesting facts, play word games, and be a supportive companion for the child.'
WHERE `agent_name` LIKE '%Chat%' OR `agent_name` LIKE '%聊天%';

UPDATE `ai_agent_template`
SET `system_prompt` = 'You are a clever puzzle solver who loves riddles, brain teasers, logic problems, and challenges that make children think creatively and develop problem-solving skills.'
WHERE `agent_name` LIKE '%Puzzle%' OR `agent_name` LIKE '%谜题%' OR `agent_name` LIKE '%Solver%';

-- Step 3: Link existing agents to templates (if template_id is NULL)
UPDATE `ai_agent` a
JOIN `ai_agent_template` t ON t.agent_name = 'Cheeko'
SET a.`template_id` = t.`id`
WHERE a.`template_id` IS NULL;

-- Step 4: Verify data
SELECT
    t.agent_name as template_name,
    LENGTH(t.system_prompt) as personality_length,
    COUNT(a.id) as agent_count
FROM ai_agent_template t
LEFT JOIN ai_agent a ON t.id = a.template_id
GROUP BY t.id, t.agent_name
ORDER BY t.sort;

-- Expected output:
-- template_name | personality_length | agent_count
-- Cheeko        | ~150              | 10
-- Story         | ~180              | 2
-- Music         | ~160              | 1
-- Tutor         | ~170              | 1
-- Chat          | ~140              | 0
-- Puzzle        | ~150              | 0
```

### Example Template Records (Database)

```sql
-- IMPORTANT: These now contain ONLY the personality, NOT the full template!

INSERT INTO `ai_agent_template` VALUES (
    '9406648b5cc5fde1b8aa335b6f8b4f76',
    'xiaozhi',
    'Cheeko',
    'You are Cheeko, a playful and curious AI companion for children aged 5-12. You love to explore, ask questions, and make learning fun through engaging conversations!',
    1, -- sort
    1  -- is_visible
);

INSERT INTO `ai_agent_template` VALUES (
    'story_template_uuid_here',
    'xiaozhi',
    'Story',
    'You are a master storyteller who brings tales to life with vivid descriptions, exciting narratives, and age-appropriate adventures. You adapt stories to the child''s interests and age group.',
    2, -- sort
    1  -- is_visible
);

INSERT INTO `ai_agent_template` VALUES (
    'music_template_uuid_here',
    'xiaozhi',
    'Music',
    'You are a music maestro who teaches music theory, helps discover new songs, introduces different genres, and encourages musical creativity in children through fun activities.',
    3, -- sort
    1  -- is_visible
);

-- ... (Tutor, Chat, Puzzle follow same pattern)
```

---

## System Components

### 1. PromptManager Class

**File:** `src/utils/prompt_manager.py`

**Responsibilities:**
- Load base template from disk (ONCE at startup)
- Fetch agent personalities from database
- Gather real-time context data (time, weather, location)
- Render templates using Jinja2
- Manage multi-layer cache (template/context/rendered)

**Key Methods:**

```python
class PromptManager:
    """Manages template-based prompts with dynamic context"""

    def __init__(self, db_helper, config: dict):
        self.db_helper = db_helper
        self.config = config
        self.base_template = None  # Loaded ONCE from disk
        self.context_cache = {}    # {device_mac: {location, weather, timestamp}}

    def _load_base_template(self) -> str:
        """
        Load base template from disk (cached in memory)

        File: base-agent-template.txt
        Returns: Template string with {{placeholders}}
        Cache: Memory (never expires until restart)
        """
        if self.base_template is None:
            template_path = "base-agent-template.txt"
            with open(template_path, 'r', encoding='utf-8') as f:
                self.base_template = f.read()
            logger.info(f"📄 Loaded base template from {template_path} "
                       f"({len(self.base_template)} chars)")
        return self.base_template

    async def get_personality_from_db(self, template_id: str) -> str:
        """
        Get agent personality from database

        API: GET /config/template/{template_id}
        Returns: "You are Cheeko, playful and curious..."
        Cache: 1 hour TTL
        """
        # Check cache
        cache_key = f"personality:{template_id}"
        cached = self._get_from_cache(cache_key, ttl=3600)
        if cached:
            return cached

        # Fetch from API
        personality = await self.db_helper.fetch_template_content(template_id)

        # Cache result
        self._set_cache(cache_key, personality)

        return personality

    async def get_context_info(self, device_mac: str) -> dict:
        """
        Gather all context variables

        Returns: {
            'current_time': "14:30",
            'today_date': "2025-01-24",
            'today_weekday': "Friday",
            'lunar_date': "24 January 2025",
            'local_address': "Mumbai",
            'weather_info': "Sunny, 28°C...",
            'emojiList': ["😶","🙂","😆",...]
        }
        """
        return {
            'current_time': self._get_current_time(),
            'today_date': self._get_date(),
            'today_weekday': self._get_weekday(),
            'lunar_date': self._get_indian_date(),
            'local_address': await self._get_location(device_mac),
            'weather_info': await self._get_weather(device_mac),
            'emojiList': EMOJI_LIST
        }

    def _get_current_time(self) -> str:
        """Get current time in IST (14:30 format)"""
        ist = pytz.timezone('Asia/Kolkata')
        return datetime.now(ist).strftime("%H:%M")

    def _get_date(self) -> str:
        """Get current date (2025-01-24 format)"""
        ist = pytz.timezone('Asia/Kolkata')
        return datetime.now(ist).strftime("%Y-%m-%d")

    def _get_weekday(self) -> str:
        """Get weekday name"""
        ist = pytz.timezone('Asia/Kolkata')
        day_name = datetime.now(ist).strftime("%A")
        return WEEKDAY_MAP.get(day_name, day_name)

    def _get_indian_date(self) -> str:
        """Get Indian calendar date (24 January 2025 format)"""
        ist = pytz.timezone('Asia/Kolkata')
        return datetime.now(ist).strftime("%d %B %Y")

    async def _get_location(self, device_mac: str) -> str:
        """
        Get device location with 1-day cache

        Sources:
        1. ai_device.location (if stored in DB)
        2. IP geolocation API (fallback)
        """
        cache_key = f"location:{device_mac}"
        cached = self._get_from_cache(cache_key, ttl=86400)  # 1 day
        if cached:
            return cached

        location = await self.db_helper.get_device_location(device_mac)
        if not location:
            location = "Unknown location"

        self._set_cache(cache_key, location)
        return location

    async def _get_weather(self, device_mac: str) -> str:
        """
        Get weather forecast with 5-min cache

        Flow:
        1. Get location for device
        2. Call weather API
        3. Format forecast string
        """
        # Get location first
        location = await self._get_location(device_mac)
        if location == "Unknown location":
            return "Weather information unavailable"

        cache_key = f"weather:{location}"
        cached = self._get_from_cache(cache_key, ttl=300)  # 5 min
        if cached:
            return cached

        weather = await self.db_helper.get_weather_forecast(location)
        if not weather:
            weather = "Weather information unavailable"

        self._set_cache(cache_key, weather)
        return weather

    async def render_template(
        self,
        base_template_str: str,
        personality: str,
        context: dict
    ) -> str:
        """
        Render template using Jinja2

        Args:
            base_template_str: Template from base-agent-template.txt
            personality: Agent personality from DB
            context: All context variables

        Returns:
            Fully rendered prompt with all placeholders replaced
        """
        try:
            template = Template(base_template_str)
            rendered = template.render(
                base_prompt=personality,
                **context
            )

            logger.debug(f"✅ Template rendered successfully ({len(rendered)} chars)")
            return rendered

        except Exception as e:
            logger.error(f"❌ Template rendering failed: {e}")
            raise

    async def build_enhanced_prompt(
        self,
        template_id: str,
        device_mac: str
    ) -> str:
        """
        Main method: Load base template, get personality, gather context, render

        Flow:
        1. Load base template from disk (cached in memory)
        2. Get personality from database (cached 1 hour)
        3. Gather context data (time, weather, location)
        4. Render template with Jinja2

        Returns:
            Fully enhanced prompt ready for LLM
        """
        try:
            # 1. Load base template (from disk, cached)
            base_template_str = self._load_base_template()

            # 2. Get personality (from DB, cached)
            personality = await self.get_personality_from_db(template_id)

            # 3. Get context (mixed caching)
            context = await self.get_context_info(device_mac)

            # 4. Render template
            enhanced = await self.render_template(
                base_template_str,
                personality,
                context
            )

            logger.info(f"✅ Built enhanced prompt for template {template_id} "
                       f"(personality: {len(personality)} chars, "
                       f"final: {len(enhanced)} chars)")

            return enhanced

        except Exception as e:
            logger.error(f"❌ Failed to build enhanced prompt: {e}")
            raise
```

**Caching Strategy:**

```python
# Base template (from disk)
Location: Memory (self.base_template)
TTL: Never expires (until agent restart)
Size: ~3-4KB

# Personality (from database)
Cache key: f"personality:{template_id}"
TTL: 3600 seconds (1 hour)
Size: ~200 bytes per template

# Location (from API/DB)
Cache key: f"location:{device_mac}"
TTL: 86400 seconds (1 day)
Size: ~20 bytes per device

# Weather (from API)
Cache key: f"weather:{location}"
TTL: 300 seconds (5 min)
Size: ~500 bytes per location

# Rendered prompt (complete)
Cache key: f"enhanced_prompt:{device_mac}"
TTL: 300 seconds (5 min)
Size: ~4KB per device
```

### 2. PromptService Updates

**File:** `src/services/prompt_service.py`

**New Method:**

```python
class PromptService:

    def __init__(self):
        self.config = None
        self.prompt_manager = None  # NEW
        self.db_helper = None       # NEW
        self.prompt_cache = {}

    async def initialize(self):
        """Initialize managers (call from main.py startup)"""
        config = self.load_config()

        # Create database helper
        manager_api = config.get('manager_api', {})
        from src.utils.database_helper import DatabaseHelper
        self.db_helper = DatabaseHelper(
            manager_api['url'],
            manager_api['secret']
        )

        # Create prompt manager
        from src.utils.prompt_manager import PromptManager
        self.prompt_manager = PromptManager(self.db_helper, config)

        logger.info("✅ PromptService initialized with PromptManager")

    async def get_enhanced_prompt(
        self,
        room_name: str,
        device_mac: str
    ) -> str:
        """
        Get fully rendered prompt with all placeholders replaced

        Flow:
        1. Check if API mode is enabled
        2. Check cache
        3. Get template_id via DatabaseHelper
        4. Use PromptManager to build enhanced prompt
        5. Cache & return

        Returns:
            Fully rendered prompt ready for LLM
        """
        try:
            # Check if API mode is enabled
            if not self.should_read_from_api():
                logger.info("Using default prompt (read_config_from_api=false)")
                return self.get_default_prompt()

            # Check cache
            import time
            cache_key = f"enhanced_prompt:{device_mac}"

            if cache_key in self.prompt_cache:
                cached = self.prompt_cache[cache_key]
                if (time.time() - cached['timestamp']) < 300:  # 5 min
                    logger.info(f"📦 Using cached enhanced prompt for {device_mac}")
                    return cached['prompt']

            # Get template_id
            template_id = await self.db_helper.get_agent_template_id(device_mac)
            if not template_id:
                logger.warning(f"⚠️ No template_id found for {device_mac}")
                return self.get_default_prompt()

            logger.info(f"🎨 Building enhanced prompt for {device_mac} "
                       f"(template: {template_id})")

            # Build enhanced prompt using PromptManager
            enhanced = await self.prompt_manager.build_enhanced_prompt(
                template_id=template_id,
                device_mac=device_mac
            )

            # Cache result
            self.prompt_cache[cache_key] = {
                'prompt': enhanced,
                'timestamp': time.time()
            }

            logger.info(f"✅ Enhanced prompt built successfully "
                       f"(length: {len(enhanced)} chars)")

            return enhanced

        except Exception as e:
            logger.error(f"❌ Error building enhanced prompt: {e}")
            logger.info("Falling back to default prompt")
            return self.get_default_prompt()
```

### 3. DatabaseHelper Extensions

**File:** `src/utils/database_helper.py`

**New Methods:**

```python
class DatabaseHelper:

    async def get_agent_template_id(self, device_mac: str) -> Optional[str]:
        """
        Get template_id for device's agent

        Flow: device → agent_id → ai_agent.template_id
        API: POST /config/agent-template-id
        Returns: "9406648b5cc5fde1b8aa335b6f8b4f76"
        """
        url = f"{self.manager_api_url}/config/agent-template-id"
        headers = {
            "Authorization": f"Bearer {self.secret}",
            "Content-Type": "application/json"
        }
        payload = {"macAddress": device_mac}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('code') == 0:
                            template_id = data.get('data')
                            logger.info(f"🆔 Retrieved template_id: {template_id} for MAC: {device_mac}")
                            return template_id
                    else:
                        logger.warning(f"Failed to get template_id: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error getting template_id: {e}")
            return None

    async def fetch_template_content(self, template_id: str) -> Optional[str]:
        """
        Fetch agent personality from ai_agent_template table

        API: GET /config/template/{template_id}
        Returns: "You are Cheeko, playful and curious..."
        """
        url = f"{self.manager_api_url}/config/template/{template_id}"
        headers = {
            "Authorization": f"Bearer {self.secret}"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('code') == 0:
                            personality = data.get('data')
                            logger.info(f"📝 Retrieved personality for template {template_id} "
                                       f"({len(personality)} chars)")
                            return personality
                    else:
                        logger.warning(f"Failed to get template content: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error fetching template content: {e}")
            return None

    async def get_device_location(self, device_mac: str) -> Optional[str]:
        """
        Get device location (city name)

        Sources:
        1. Database (ai_device.location if field exists)
        2. IP geolocation API (fallback)

        Returns: "Mumbai" or None
        """
        # TODO: Implement based on your infrastructure
        # Option 1: Store location in ai_device table
        # Option 2: Use IP geolocation service
        return "Mumbai"  # Placeholder

    async def get_weather_forecast(self, location: str) -> Optional[str]:
        """
        Get 7-day weather forecast for location

        API: External weather service (OpenWeatherMap, WeatherAPI, etc.)
        Returns: "Sunny, 28°C. High: 30°C, Low: 22°C. Clear skies throughout the day."
        """
        # TODO: Integrate with weather API
        # Example with OpenWeatherMap:
        # api_key = self.config.get('weather_api_key')
        # url = f"http://api.openweathermap.org/data/2.5/forecast?q={location}&appid={api_key}"
        return f"Sunny, 28°C. Weather forecast for {location}."  # Placeholder
```

---

## Implementation Phases

### Phase 1: Setup ⏱️ 1-2 hours

**Tasks:**
- [x] ~~Add template_id to ai_agent table~~ (Already exists from previous work)
- [ ] Create `base-agent-template.txt` file in root directory
- [ ] Update ai_agent_template records to contain ONLY personalities
- [ ] Verify agents are linked to templates
- [ ] Test database queries

**Steps:**

```bash
# 1. Create base template file
cd main/livekit-server
touch base-agent-template.txt

# 2. Copy template content from "Base Template File" section above
# (Use the complete template with all sections)

# 3. Run database migration
mysql -u your_user -p your_database < migration_update_templates.sql
```

**Verification:**

```sql
-- Check template_id column exists
DESCRIBE ai_agent;

-- Verify agents linked to templates
SELECT a.id, a.agent_name, a.template_id, t.agent_name as template_name
FROM ai_agent a
LEFT JOIN ai_agent_template t ON a.template_id = t.id
LIMIT 10;

-- Check template personalities (should be short now)
SELECT
    agent_name,
    LENGTH(system_prompt) as personality_length,
    LEFT(system_prompt, 80) as preview
FROM ai_agent_template
ORDER BY sort;

-- Expected: personality_length around 150-200 chars (NOT 2000+)
```

---

### Phase 2: Core Components ⏱️ 4-6 hours

**Tasks:**
- [ ] Create `src/utils/prompt_manager.py`
- [ ] Implement base template loading from disk
- [ ] Add personality fetching from database
- [ ] Implement context gathering methods
- [ ] Implement Jinja2 rendering
- [ ] Add multi-layer caching
- [ ] Add `jinja2` and `pytz` to `requirements.txt`

**File Structure:**

```
main/livekit-server/
├── base-agent-template.txt  (NEW - 3-4KB)
├── requirements.txt          (MODIFY - add jinja2, pytz)
└── src/utils/
    ├── prompt_manager.py     (NEW - 500+ lines)
    └── database_helper.py    (MODIFY - add 4 methods)
```

**Dependencies:**

```bash
# Add to requirements.txt
jinja2==3.1.2
pytz==2023.3

# Install
pip install jinja2 pytz
```

**Code Implementation:**

See [System Components](#system-components) section for complete code.

**Testing:**

```python
# Test base template loading
from src.utils.prompt_manager import PromptManager

manager = PromptManager(db_helper, config)
base_template = manager._load_base_template()

assert "{{base_prompt}}" in base_template
assert "{{current_time}}" in base_template
assert len(base_template) > 2000
print("✅ Base template loaded successfully")

# Test personality fetching
personality = await manager.get_personality_from_db("cheeko_template_id")
assert len(personality) < 500  # Should be short (just personality)
assert "Cheeko" in personality or "playful" in personality
print("✅ Personality fetched successfully")

# Test context gathering
context = await manager.get_context_info("00:16:3e:ac:b5:38")
assert context['current_time']  # "14:30"
assert context['today_date']    # "2025-01-24"
assert len(context['emojiList']) > 10
print("✅ Context gathered successfully")

# Test template rendering
rendered = await manager.render_template(
    base_template,
    personality,
    context
)
assert "{{" not in rendered  # No placeholders remain
assert len(rendered) > 3000  # Reasonable length
print("✅ Template rendered successfully")

# Test full flow
enhanced = await manager.build_enhanced_prompt(
    template_id="cheeko_template_id",
    device_mac="00:16:3e:ac:b5:38"
)
assert "{{" not in enhanced
print("✅ Full enhanced prompt built successfully")
```

---

### Phase 3: API Integration ⏱️ 3-4 hours

**Tasks:**
- [ ] Add Manager API endpoints (Java)
- [ ] Update DatabaseHelper with new methods
- [ ] Test API endpoints
- [ ] Add security filters (if needed)

**Manager API Endpoints:**

**File:** `manager-api/src/main/java/xiaozhi/modules/config/controller/ConfigController.java`

```java
/**
 * Get template ID for device's agent
 * POST /config/agent-template-id
 * Body: {"macAddress": "00:16:3e:ac:b5:38"}
 * Returns: {"code": 0, "data": "template_uuid"}
 */
@PostMapping("agent-template-id")
@Operation(summary = "Get agent template ID by device MAC")
public Result<String> getAgentTemplateId(@Valid @RequestBody Map<String, String> request) {
    String macAddress = request.get("macAddress");

    if (StringUtils.isBlank(macAddress)) {
        return new Result<String>().error("MAC address is required");
    }

    try {
        // 1. Find device
        DeviceEntity device = deviceService.getDeviceByMacAddress(macAddress);
        if (device == null) {
            return new Result<String>().error("Device not found: " + macAddress);
        }

        // 2. Get agent
        AgentEntity agent = agentService.selectById(device.getAgentId());
        if (agent == null) {
            return new Result<String>().error("Agent not found for device");
        }

        // 3. Return template_id
        String templateId = agent.getTemplateId();
        if (StringUtils.isBlank(templateId)) {
            return new Result<String>().error("No template assigned to agent");
        }

        return new Result<String>().ok(templateId);

    } catch (Exception e) {
        logger.error("Error getting template ID for MAC: " + macAddress, e);
        return new Result<String>().error("Internal server error");
    }
}

/**
 * Get template personality content
 * GET /config/template/{templateId}
 * Returns: {"code": 0, "data": "You are Cheeko, playful..."}
 */
@GetMapping("template/{templateId}")
@Operation(summary = "Get template personality by ID")
public Result<String> getTemplateContent(@PathVariable String templateId) {
    try {
        AgentTemplateEntity template = agentTemplateService.selectById(templateId);

        if (template == null) {
            return new Result<String>().error("Template not found: " + templateId);
        }

        // Return ONLY the personality (system_prompt field)
        String personality = template.getSystemPrompt();
        if (StringUtils.isBlank(personality)) {
            return new Result<String>().error("Template has no personality configured");
        }

        return new Result<String>().ok(personality);

    } catch (Exception e) {
        logger.error("Error getting template content for ID: " + templateId, e);
        return new Result<String>().error("Internal server error");
    }
}
```

**Testing API Endpoints:**

```bash
# Test 1: Get template ID
curl -X POST http://localhost:8002/toy/config/agent-template-id \
  -H "Authorization: Bearer YOUR_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"macAddress": "00:16:3e:ac:b5:38"}'

# Expected: {"code":0,"data":"9406648b5cc5fde1b8aa335b6f8b4f76"}

# Test 2: Get template personality
curl http://localhost:8002/toy/config/template/9406648b5cc5fde1b8aa335b6f8b4f76 \
  -H "Authorization: Bearer YOUR_SECRET"

# Expected: {"code":0,"data":"You are Cheeko, a playful and curious AI companion..."}
# NOTE: Should be SHORT (just personality, not full template)
```

---

### Phase 4: Service Layer ⏱️ 2-3 hours

**Tasks:**
- [ ] Update `PromptService` to use `PromptManager`
- [ ] Implement `get_enhanced_prompt()` method
- [ ] Add caching logic
- [ ] Test end-to-end flow

See [System Components - PromptService](#2-promptservice-updates) for complete implementation.

---

### Phase 5: Agent Integration ⏱️ 2-3 hours

**Tasks:**
- [ ] Modify `main.py` to initialize PromptService
- [ ] Update data channel handler to use enhanced prompts
- [ ] Add memory injection in `chat_logger.py`
- [ ] Test dynamic prompt updates

**File:** `main.py`

```python
async def entrypoint(ctx: JobContext):
    """LiveKit agent entry point"""

    logger.info(f"🚀 Agent starting for room: {ctx.room.name}")

    # Initialize prompt service
    prompt_service = PromptService()
    await prompt_service.initialize()  # NEW: Initialize PromptManager

    # Start with default prompt
    initial_prompt = prompt_service.get_default_prompt()
    logger.info(f"📝 Using default prompt initially ({len(initial_prompt)} chars)")

    # Create assistant
    assistant = Assistant(instructions=initial_prompt)

    # ... existing service setup (music, story, etc.) ...

    # Set up data channel handler for dynamic updates
    @ctx.room.on("data_received")
    async def on_data_received(data: rtc.DataPacket):
        """Handle MQTT gateway messages"""
        try:
            message = json.loads(data.data.decode('utf-8'))
            msg_type = message.get('type')

            if msg_type == 'device_info':
                device_mac = message.get('device_mac')
                logger.info(f"📱 Received device info - MAC: {device_mac}")

                # NEW: Get enhanced prompt using base template + personality + context
                enhanced_prompt = await prompt_service.get_enhanced_prompt(
                    room_name=ctx.room.name,
                    device_mac=device_mac
                )

                # Update agent's chat context
                await update_agent_prompt_with_context(
                    assistant._agent_session,
                    enhanced_prompt,
                    device_mac
                )

                logger.info(f"✅ Agent prompt updated with enhanced template "
                           f"(length: {len(enhanced_prompt)})")

        except Exception as e:
            logger.error(f"❌ Error processing device info: {e}")

    # ... rest of existing code ...
```

**File:** `src/handlers/chat_logger.py`

```python
async def update_agent_prompt_with_context(
    session,
    enhanced_prompt: str,
    device_mac: str
):
    """
    Update agent prompt with enhanced template + memory injection
    """
    try:
        # Fetch memory if available
        memory_str = None
        if hasattr(session, '_memory_provider') and session._memory_provider:
            memory_str = await session._memory_provider.get_memory(device_mac)

        # Inject memory into <memory></memory> tags
        if memory_str:
            import re
            enhanced_prompt = re.sub(
                r"<memory>.*?</memory>",
                f"<memory>\n{memory_str}\n</memory>",
                enhanced_prompt,
                flags=re.DOTALL
            )
            logger.debug(f"💭 Injected memory ({len(memory_str)} chars)")

        # Update session chat context
        current_ctx = session.history

        # Replace or add system message
        system_updated = False
        for i, msg in enumerate(current_ctx.messages):
            if hasattr(msg, 'role') and msg.role == "system":
                msg.content = enhanced_prompt
                system_updated = True
                logger.debug(f"🔄 Updated existing system message")
                break

        if not system_updated:
            current_ctx.append(text=enhanced_prompt, role="system")
            logger.debug(f"➕ Added new system message")

        # Apply changes
        if hasattr(session, 'update_chat_ctx'):
            session.update_chat_ctx(current_ctx)
            logger.info(f"✅ Agent chat context updated successfully")
        else:
            logger.warning(f"⚠️ session.update_chat_ctx() not available")

    except Exception as e:
        logger.error(f"❌ Failed to update agent prompt: {e}")
        import traceback
        logger.debug(traceback.format_exc())
```

---

### Phase 6: Mode Switching Integration ⏱️ 2-3 hours

**Tasks:**
- [ ] Update `update_agent_mode()` function to use templates
- [ ] Test voice command: "Switch to Story mode"
- [ ] Test button switching (if applicable)
- [ ] Verify session updates correctly without reconnect

**File:** `src/agent/main_agent.py`

**Updated `update_agent_mode` Function:**

```python
@function_tool
async def update_agent_mode(mode_name: str):
    """
    Switch agent personality (Cheeko → Story → Music, etc.)

    Uses template system:
    - Same base template structure
    - Different personality injected
    - Context remains current
    - NO RECONNECT needed!
    """

    logger.info(f"🔄 Mode switch requested: {mode_name}")

    try:
        # 1. Normalize mode name (existing logic)
        normalized_mode = normalize_mode_name(mode_name)
        logger.info(f"🔍 Normalized mode: '{mode_name}' → '{normalized_mode}'")

        if not self.device_mac:
            logger.error("❌ device_mac not set, cannot update mode")
            return "Sorry, I couldn't switch modes. Device information is missing."

        # 2. Call Manager API to switch mode (existing)
        # This updates ai_device.agent_id to point to new agent with different template_id
        manager_api_url = self.config.get('manager_api', {}).get('url', '')
        secret = self.config.get('manager_api', {}).get('secret', '')

        url = f"{manager_api_url}/agent/update-mode"
        headers = {
            "Authorization": f"Bearer {secret}",
            "Content-Type": "application/json"
        }
        payload = {
            "deviceMac": self.device_mac,
            "modeName": normalized_mode
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"❌ Mode update API failed: {error_text}")
                    return f"Sorry, I couldn't switch to {normalized_mode} mode. Please try again."

                data = await response.json()
                if data.get('code') != 0:
                    logger.error(f"❌ Mode update failed: {data.get('msg')}")
                    return f"Sorry, I couldn't switch to {normalized_mode} mode. {data.get('msg', '')}"

        logger.info(f"✅ API updated device to {normalized_mode} mode")

        # 3. Get NEW template_id for the new mode
        from src.utils.database_helper import DatabaseHelper
        db_helper = DatabaseHelper(manager_api_url, secret)

        new_template_id = await db_helper.get_agent_template_id(self.device_mac)
        if not new_template_id:
            logger.error(f"❌ Could not get new template_id after mode switch")
            return f"Mode updated, but prompt refresh failed. Please reconnect."

        logger.info(f"🎨 New template_id: {new_template_id}")

        # 4. Build enhanced prompt with NEW personality
        from src.services.prompt_service import PromptService
        prompt_service = PromptService()
        await prompt_service.initialize()

        enhanced_prompt = await prompt_service.get_enhanced_prompt(
            room_name=self.room_name,
            device_mac=self.device_mac
        )

        # 5. Update session with NEW prompt (same base template, different personality)
        await update_agent_prompt_with_memory(
            self._agent_session,
            enhanced_prompt,
            self.device_mac
        )

        logger.info(f"✅ Session updated with {normalized_mode} mode prompt "
                   f"({len(enhanced_prompt)} chars)")

        # 6. Return success message
        return f"Successfully switched to {normalized_mode} mode! How can I help you?"

    except Exception as e:
        logger.error(f"❌ Failed to switch mode: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return "Sorry, I encountered an error while switching modes. Please try again."
```

**How Mode Switching Works:**

```
User: "Switch to Story mode"
   │
   ▼
1. LLM detects intent → Calls update_agent_mode("Story")
   │
   ▼
2. API updates database:
   UPDATE ai_agent SET template_id = 'story_template_id'
   WHERE id = (SELECT agent_id FROM ai_device WHERE mac_address = 'xx:xx:xx')
   │
   ▼
3. Get NEW template_id:
   template_id = "story_template_id"
   │
   ▼
4. Build enhanced prompt:
   base_template (from disk, same as before)
   + NEW personality: "You are a master storyteller..."  ← CHANGED
   + SAME context: time="14:30", weather="Sunny..."  ← Same
   = New enhanced prompt with storyteller personality
   │
   ▼
5. Update session:
   session.history.messages[0].content = new_enhanced_prompt
   session.update_chat_ctx()
   │
   ▼
6. User continues conversation:
   Agent now responds as storyteller (NO RECONNECT!)
```

---

### Phase 7: Testing ⏱️ 3-4 hours

**Test Cases:**

**1. Base Template Loading**

```python
from src.utils.prompt_manager import PromptManager

manager = PromptManager(db_helper, config)
base = manager._load_base_template()

# Verify
assert "{{base_prompt}}" in base
assert "{{current_time}}" in base
assert "{{weather_info}}" in base
assert "<memory></memory>" in base
assert len(base) > 2000 and len(base) < 5000
print("✅ Base template loaded correctly")
```

**2. Personality Fetching**

```python
# Test each template
templates = [
    ("cheeko_id", "Cheeko", ["playful", "curious"]),
    ("story_id", "Story", ["storyteller", "tales"]),
    ("music_id", "Music", ["maestro", "music"]),
]

for template_id, name, keywords in templates:
    personality = await manager.get_personality_from_db(template_id)

    # Verify short (just personality, not full template)
    assert len(personality) < 500, f"{name} personality too long"

    # Verify contains expected keywords
    assert any(kw in personality.lower() for kw in keywords), \
        f"{name} missing keywords"

    print(f"✅ {name} personality fetched correctly ({len(personality)} chars)")
```

**3. Context Gathering**

```python
context = await manager.get_context_info("00:16:3e:ac:b5:38")

# Verify all required fields
assert context['current_time']  # "14:30"
assert context['today_date']    # "2025-01-24"
assert context['today_weekday'] in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
assert context['lunar_date']    # "24 January 2025"
assert len(context['emojiList']) > 10

print("✅ Context gathered successfully")
print(f"   Time: {context['current_time']}")
print(f"   Date: {context['today_date']} ({context['today_weekday']})")
print(f"   Location: {context['local_address']}")
print(f"   Weather: {context['weather_info'][:50]}...")
```

**4. Template Rendering**

```python
base = manager._load_base_template()
personality = "You are Cheeko, a playful AI companion."
context = await manager.get_context_info("test_mac")

rendered = await manager.render_template(base, personality, context)

# Verify no placeholders remain
assert "{{" not in rendered, "Placeholders not replaced"
assert "}}" not in rendered, "Placeholders not replaced"

# Verify personality injected
assert "Cheeko" in rendered or "playful" in rendered

# Verify context injected
assert context['current_time'] in rendered
assert context['today_date'] in rendered

print("✅ Template rendered correctly")
print(f"   Length: {len(rendered)} chars")
print(f"   Preview: {rendered[:200]}...")
```

**5. End-to-End Flow**

```python
# Test full flow for all modes
test_macs = {
    "00:16:3e:ac:b5:38": "Cheeko",
    "00:16:3e:ac:b5:39": "Story",
    "00:16:3e:ac:b5:40": "Music",
}

for mac, expected_mode in test_macs.items():
    enhanced = await prompt_service.get_enhanced_prompt("test_room", mac)

    # Verify no placeholders
    assert "{{" not in enhanced

    # Verify structure exists
    assert "<identity>" in enhanced
    assert "<emotion>" in enhanced
    assert "<context>" in enhanced
    assert "<memory>" in enhanced

    # Verify context data present
    assert any(day in enhanced for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])

    print(f"✅ {expected_mode} mode: {len(enhanced)} chars")
```

**6. Mode Switching Test**

```python
# Start with Cheeko
enhanced_cheeko = await prompt_service.get_enhanced_prompt("room", "test_mac")
assert "playful" in enhanced_cheeko.lower() or "cheeko" in enhanced_cheeko.lower()

# Switch to Story mode (simulate API call)
await update_agent_mode("Story")

# Get new prompt
enhanced_story = await prompt_service.get_enhanced_prompt("room", "test_mac")
assert "story" in enhanced_story.lower() or "tale" in enhanced_story.lower()

# Verify different personalities but same structure
assert "<identity>" in enhanced_cheeko and "<identity>" in enhanced_story
assert enhanced_cheeko != enhanced_story  # Different content

print("✅ Mode switching works correctly")
```

**7. Memory Injection Test**

```python
enhanced = await prompt_service.get_enhanced_prompt("room", "test_mac")

# Simulate memory injection
memory_str = "User's name is Arjun. Age: 8. Loves cricket."
import re
enhanced_with_memory = re.sub(
    r"<memory>.*?</memory>",
    f"<memory>\n{memory_str}\n</memory>",
    enhanced,
    flags=re.DOTALL
)

# Verify memory injected
assert memory_str in enhanced_with_memory
assert "<memory>" in enhanced_with_memory
assert "</memory>" in enhanced_with_memory

print("✅ Memory injection works correctly")
```

**8. Cache Verification**

```python
import time

# First call (cold)
start = time.time()
prompt1 = await prompt_service.get_enhanced_prompt("room", "test_mac")
time1 = time.time() - start

# Second call (cached)
start = time.time()
prompt2 = await prompt_service.get_enhanced_prompt("room", "test_mac")
time2 = time.time() - start

# Verify
assert prompt1 == prompt2, "Cached prompt differs"
assert time2 < time1 * 0.1, f"Cache not working (t1={time1:.3f}s, t2={time2:.3f}s)"

print(f"✅ Caching works: {time1:.3f}s → {time2:.3f}s ({time1/time2:.1f}x speedup)")
```

**Integration Test Script:**

```bash
# File: test_template_system.py

import asyncio
from src.services.prompt_service import PromptService

async def test_all():
    """Run all tests"""

    service = PromptService()
    await service.initialize()

    print("\n" + "="*60)
    print("Testing Template-Based Prompt System")
    print("="*60)

    # Test 1: Base template
    print("\n[1/8] Testing base template loading...")
    # ... (code from test 1 above)

    # Test 2: Personalities
    print("\n[2/8] Testing personality fetching...")
    # ... (code from test 2 above)

    # Test 3: Context
    print("\n[3/8] Testing context gathering...")
    # ... (code from test 3 above)

    # Test 4: Rendering
    print("\n[4/8] Testing template rendering...")
    # ... (code from test 4 above)

    # Test 5: End-to-end
    print("\n[5/8] Testing end-to-end flow...")
    # ... (code from test 5 above)

    # Test 6: Mode switching
    print("\n[6/8] Testing mode switching...")
    # ... (code from test 6 above)

    # Test 7: Memory
    print("\n[7/8] Testing memory injection...")
    # ... (code from test 7 above)

    # Test 8: Caching
    print("\n[8/8] Testing caching...")
    # ... (code from test 8 above)

    print("\n" + "="*60)
    print("✅ All tests passed!")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(test_all())
```

**Run Tests:**

```bash
# Run automated tests
python test_template_system.py

# Test with real device
# 1. Start agent
python main.py

# 2. Connect device via MQTT
# 3. Check logs for:
grep -E "(📱|✅|🎨|💭|🔄)" logs/agent.log

# Expected output:
# 📱 Received device info - MAC: 00:16:3e:ac:b5:38
# 🎨 Building enhanced prompt for 00:16:3e:ac:b5:38 (template: cheeko_id)
# ✅ Enhanced prompt built successfully (length: 3845 chars)
# 💭 Injected memory (142 chars)
# 🔄 Updated existing system message
# ✅ Agent chat context updated successfully

# 4. Test mode switching
# User: "Switch to Story mode"
# Expected in logs:
# 🔄 Mode switch requested: Story
# 🔍 Normalized mode: 'Story' → 'Story'
# ✅ API updated device to Story mode
# 🎨 New template_id: story_id
# ✅ Session updated with Story mode prompt (3912 chars)
```

---

## Data Flow

### Complete System Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: Agent Startup                                           │
├─────────────────────────────────────────────────────────────────┤
│ main.py starts                                                  │
│   │                                                              │
│   ├─→ Initialize PromptService                                  │
│   │    await prompt_service.initialize()                        │
│   │                                                              │
│   ├─→ Create PromptManager                                      │
│   │    manager = PromptManager(db_helper, config)               │
│   │                                                              │
│   └─→ Load base template from disk                              │
│        base_template = open("base-agent-template.txt").read()   │
│        Cache in memory: self.base_template                       │
│        ✅ Ready for connections                                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: Device Connects                                         │
├─────────────────────────────────────────────────────────────────┤
│ MQTT → Gateway → LiveKit Data Channel                          │
│   {"type": "device_info", "device_mac": "00:16:3e:ac:b5:38"}   │
│                                                                  │
│ Agent receives device_mac                                        │
│   ↓                                                              │
│ on_data_received() handler triggered                            │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: Build Enhanced Prompt                                   │
├─────────────────────────────────────────────────────────────────┤
│ prompt_service.get_enhanced_prompt(room, device_mac)            │
│   │                                                              │
│   ├─→ 3a. Get template_id                                       │
│   │    API: POST /config/agent-template-id                      │
│   │    device_mac → ai_device → ai_agent → template_id          │
│   │    Returns: "cheeko_template_id"                            │
│   │    Cache: 5 min                                             │
│   │                                                              │
│   ├─→ 3b. Build enhanced prompt                                 │
│   │    manager.build_enhanced_prompt(template_id, device_mac)   │
│   │      │                                                       │
│   │      ├─→ Load base template (from memory, cached)           │
│   │      │   base = self.base_template                          │
│   │      │   Size: ~3-4KB                                       │
│   │      │                                                       │
│   │      ├─→ Get personality from DB (cached 1hr)               │
│   │      │   API: GET /config/template/cheeko_template_id       │
│   │      │   Returns: "You are Cheeko, playful..."              │
│   │      │   Size: ~200 bytes                                   │
│   │      │                                                       │
│   │      ├─→ Gather context data                                │
│   │      │   context = get_context_info(device_mac)             │
│   │      │     ├─ current_time: "14:30" (no cache)              │
│   │      │     ├─ today_date: "2025-01-24" (no cache)           │
│   │      │     ├─ today_weekday: "Friday" (no cache)            │
│   │      │     ├─ lunar_date: "24 January 2025" (no cache)      │
│   │      │     ├─ local_address: "Mumbai" (cached 1 day)        │
│   │      │     ├─ weather_info: "Sunny, 28°C..." (cached 5 min) │
│   │      │     └─ emojiList: ["😶","🙂",...] (static)           │
│   │      │                                                       │
│   │      └─→ Render with Jinja2                                 │
│   │          Template(base).render(                             │
│   │              base_prompt=personality,                       │
│   │              **context                                      │
│   │          )                                                   │
│   │          Result: All {{placeholders}} replaced              │
│   │                                                              │
│   └─→ 3c. Cache result (5 min)                                  │
│        cache_key = f"enhanced_prompt:{device_mac}"              │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ STEP 4: Inject Memory                                           │
├─────────────────────────────────────────────────────────────────┤
│ update_agent_prompt_with_context(session, enhanced, device_mac) │
│   │                                                              │
│   ├─→ Fetch memory from Mem0                                    │
│   │    memory_str = await mem0.get_memory(device_mac)           │
│   │    Returns: "User's name is Arjun. Age: 8..."               │
│   │                                                              │
│   └─→ Inject into <memory> tags                                 │
│        enhanced = re.sub(                                        │
│            r"<memory>.*?</memory>",                              │
│            f"<memory>\n{memory_str}\n</memory>",                 │
│            enhanced                                              │
│        )                                                         │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ STEP 5: Update Agent Session                                    │
├─────────────────────────────────────────────────────────────────┤
│ session.history.messages[0].content = enhanced_prompt           │
│ session.update_chat_ctx(session.history)                        │
│                                                                  │
│ ✅ Agent now uses fully enhanced prompt!                        │
│    - Base structure from file                                   │
│    - Personality from database                                  │
│    - Real-time context (time, weather, location)                │
│    - Memory from Mem0                                            │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ STEP 6: Mode Switching (Optional)                               │
├─────────────────────────────────────────────────────────────────┤
│ User: "Switch to Story mode"                                    │
│   │                                                              │
│   ├─→ LLM calls update_agent_mode("Story")                      │
│   │                                                              │
│   ├─→ API updates database                                      │
│   │    UPDATE ai_agent SET template_id = 'story_template_id'    │
│   │                                                              │
│   ├─→ Get NEW personality from DB                               │
│   │    "You are a master storyteller..."                        │
│   │                                                              │
│   ├─→ Render SAME base template with NEW personality            │
│   │    Template(base).render(                                   │
│   │        base_prompt="You are a master storyteller...",       │
│   │        current_time="14:30",  # Same context                │
│   │        ...                                                   │
│   │    )                                                         │
│   │                                                              │
│   └─→ Update session (NO RECONNECT!)                            │
│        session.history.messages[0].content = new_enhanced       │
│        Agent immediately behaves as storyteller                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Mode Switching

### How Mode Switching Works with Templates

**Traditional Approach (Without Templates):**

```
User: "Switch to Story mode"
  ↓
System: Updates full prompt in database
  ↓
Agent: Fetches entire new prompt (2000+ chars)
  ↓
Session: Replaces system message
  ↓
✅ Works but duplicates all common rules
```

**New Template Approach:**

```
User: "Switch to Story mode"
  ↓
System: Updates template_id in database
  ↓
Agent:
  - Keeps SAME base template (loaded from disk)
  - Fetches NEW personality (200 chars from DB)
  - Gathers SAME context (time, weather still current)
  - Renders base + new personality + context
  ↓
Session: Replaces system message with new rendered prompt
  ↓
✅ Same result, less duplication, easier maintenance
```

### Voice Command Example

```
User speaks: "Switch to Story mode"
  │
  ▼ (ASR)
Text: "Switch to Story mode"
  │
  ▼ (LLM)
LLM Decision: Call update_agent_mode("Story")
  │
  ▼
┌─────────────────────────────────────────────────────────────┐
│ update_agent_mode("Story")                                  │
├─────────────────────────────────────────────────────────────┤
│ 1. Normalize: "Story" → "Story" ✓                           │
│                                                              │
│ 2. API Call: POST /agent/update-mode                        │
│    Body: {"deviceMac": "00:16:3e:ac:b5:38", "modeName": "Story"}│
│    Response: {"code": 0, "msg": "success"}                  │
│    Database: UPDATE ai_agent SET template_id = 'story_id'   │
│                                                              │
│ 3. Get new template_id:                                     │
│    API: POST /config/agent-template-id                      │
│    Response: {"code": 0, "data": "story_id"}                │
│                                                              │
│ 4. Build new enhanced prompt:                               │
│    base_template (from disk, SAME as before)                │
│    + NEW personality: "You are a master storyteller..."     │
│    + SAME context: time, weather, location (still current)  │
│    = New enhanced prompt with storyteller personality       │
│                                                              │
│ 5. Update session:                                          │
│    session.history.messages[0].content = new_prompt         │
│    session.update_chat_ctx()                                │
│                                                              │
│ 6. Return: "Successfully switched to Story mode!"           │
└─────────────────────────────────────────────────────────────┘
  │
  ▼
Agent responds: "Successfully switched to Story mode! How can I help you?"
  │
  ▼
User: "Tell me a story about dragons"
  │
  ▼
Agent: (Now uses storyteller personality)
"🐉Once upon a time, in a land far away, there lived a magnificent dragon named Ember..."
```

### Button/App Mode Switching

**If you have a mobile app with mode buttons:**

```
User taps "Story" button in app
  │
  ▼
App calls API: POST /agent/update-mode
  Body: {"deviceMac": "00:16:3e:ac:b5:38", "modeName": "Story"}
  │
  ▼
API updates database:
  UPDATE ai_agent SET template_id = 'story_id'
  │
  ▼
App sends data channel message to agent:
  {"type": "mode_changed", "new_mode": "Story"}
  │
  ▼
Agent receives message → Rebuilds prompt → Updates session
  │
  ▼
✅ Mode switched instantly (NO reconnect!)
```

### Verification

**Test Mode Switching:**

```python
# Test all mode transitions
modes = ["Cheeko", "Story", "Music", "Tutor", "Chat", "Puzzle"]

for mode in modes:
    print(f"\n{'='*60}")
    print(f"Testing switch to {mode} mode")
    print(f"{'='*60}")

    # Call mode switch function
    result = await update_agent_mode(mode)

    # Verify success
    assert "Successfully switched" in result

    # Get current prompt
    enhanced = await prompt_service.get_enhanced_prompt("room", "test_mac")

    # Verify mode-specific content
    mode_keywords = {
        "Cheeko": ["playful", "curious", "Cheeko"],
        "Story": ["story", "tale", "narrative"],
        "Music": ["music", "maestro", "song"],
        "Tutor": ["tutor", "teacher", "homework"],
        "Chat": ["chat", "conversation", "friend"],
        "Puzzle": ["puzzle", "riddle", "solver"],
    }

    found = any(kw in enhanced.lower() for kw in mode_keywords[mode])
    assert found, f"Mode {mode} keywords not found in prompt"

    print(f"✅ {mode} mode active")
    print(f"   Prompt length: {len(enhanced)} chars")
```

---

## API Reference

### Python API (PromptManager)

```python
from src.utils.prompt_manager import PromptManager

# Initialize
db_helper = DatabaseHelper(api_url, secret)
manager = PromptManager(db_helper, config)

# Load base template (from disk, cached in memory)
base_template_str = manager._load_base_template()
# Returns: Full template with {{placeholders}}

# Get personality from database
personality = await manager.get_personality_from_db("template_id")
# Returns: "You are Cheeko, playful and curious..."

# Get context data
context = await manager.get_context_info("00:16:3e:ac:b5:38")
# Returns: {
#   'current_time': "14:30",
#   'today_date': "2025-01-24",
#   'today_weekday': "Friday",
#   'lunar_date': "24 January 2025",
#   'local_address': "Mumbai",
#   'weather_info': "Sunny, 28°C...",
#   'emojiList': ["😶","🙂","😆",...]
# }

# Render template
rendered = await manager.render_template(
    base_template_str,
    personality,
    context
)
# Returns: Fully rendered prompt with all placeholders replaced

# Full flow (recommended)
enhanced = await manager.build_enhanced_prompt(
    template_id="cheeko_template_id",
    device_mac="00:16:3e:ac:b5:38"
)
# Returns: Complete enhanced prompt ready for LLM
```

### Python API (PromptService)

```python
from src.services.prompt_service import PromptService

# Initialize
service = PromptService()
await service.initialize()

# Get enhanced prompt (most common method)
prompt = await service.get_enhanced_prompt(
    room_name="test_room",
    device_mac="00:16:3e:ac:b5:38"
)
# Returns: Fully enhanced prompt with template + personality + context

# Get default prompt (fallback)
default = service.get_default_prompt()
# Returns: Default prompt from config.yaml

# Check if API mode is enabled
is_api_mode = service.should_read_from_api()
# Returns: True if read_config_from_api=true

# Clear cache (if needed)
service.clear_cache()
```

### REST API (Manager API)

**1. Get Template ID for Device**

```http
POST /toy/config/agent-template-id
Authorization: Bearer {SECRET}
Content-Type: application/json

{
  "macAddress": "00:16:3e:ac:b5:38"
}

Response:
{
  "code": 0,
  "data": "9406648b5cc5fde1b8aa335b6f8b4f76"
}
```

**2. Get Template Personality**

```http
GET /toy/config/template/{templateId}
Authorization: Bearer {SECRET}

Response:
{
  "code": 0,
  "data": "You are Cheeko, a playful and curious AI companion for children aged 5-12. You love to explore, ask questions, and make learning fun through engaging conversations!"
}
```

**3. Update Agent Mode**

```http
POST /toy/agent/update-mode
Authorization: Bearer {SECRET}
Content-Type: application/json

{
  "deviceMac": "00:16:3e:ac:b5:38",
  "modeName": "Story"
}

Response:
{
  "code": 0,
  "msg": "Mode updated successfully"
}
```

**Testing with curl:**

```bash
# Get template ID
curl -X POST http://localhost:8002/toy/config/agent-template-id \
  -H "Authorization: Bearer YOUR_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"macAddress": "00:16:3e:ac:b5:38"}'

# Get template personality
curl http://localhost:8002/toy/config/template/9406648b5cc5fde1b8aa335b6f8b4f76 \
  -H "Authorization: Bearer YOUR_SECRET"

# Update mode
curl -X POST http://localhost:8002/toy/agent/update-mode \
  -H "Authorization: Bearer YOUR_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"deviceMac": "00:16:3e:ac:b5:38", "modeName": "Story"}'
```

---

## Configuration

### config.yaml

```yaml
# Feature flag: Use templates or default prompt
read_config_from_api: true  # true = use templates, false = use default_prompt

# Default prompt (used when read_config_from_api=false or as fallback)
default_prompt: |
  You are a helpful AI assistant for children.
  Respond to user queries accurately and politely.
  Keep responses appropriate for ages 5-12.

# Manager API settings
manager_api:
  url: "http://192.168.1.5:8002/toy"
  secret: "a3c1734a-1efe-4ab7-8f43-98f88b874e4b"
  timeout: 5

# Cache settings (optional, for tuning)
cache:
  personality_ttl: 3600    # 1 hour (templates rarely change)
  location_ttl: 86400      # 1 day (location rarely changes)
  weather_ttl: 300         # 5 minutes (weather updates frequently)
  enhanced_prompt_ttl: 300 # 5 minutes (final rendered prompt)

# Weather API (optional)
weather_api:
  provider: "openweathermap"  # or "weatherapi", "accuweather"
  api_key: "YOUR_API_KEY"
  units: "metric"  # Celsius
```

### Environment Variables (Optional)

```bash
# Override config.yaml settings
export LIVEKIT_READ_FROM_API=true
export MANAGER_API_URL="http://192.168.1.5:8002/toy"
export MANAGER_API_SECRET="a3c1734a-1efe-4ab7-8f43-98f88b874e4b"
export WEATHER_API_KEY="YOUR_API_KEY"
```

---

## Troubleshooting

### Issue 1: Base Template Not Found

**Symptoms:**
- Error: "FileNotFoundError: base-agent-template.txt"
- Agent fails to start

**Solutions:**
```bash
# Check file exists
ls -la main/livekit-server/base-agent-template.txt

# Verify file path in code
grep "base-agent-template.txt" src/utils/prompt_manager.py

# Create file if missing
cd main/livekit-server
cat > base-agent-template.txt << 'EOF'
<identity>
{{base_prompt}}
</identity>
...
EOF
```

### Issue 2: Placeholders Not Replaced

**Symptoms:**
- Agent prompt contains `{{current_time}}` literally
- Error: "Template rendering failed"

**Causes:**
1. Jinja2 syntax error in base template
2. Missing variable in context dict
3. Jinja2 not installed

**Solutions:**
```bash
# Check Jinja2 installation
pip show jinja2
pip install jinja2==3.1.2

# Test template manually
python -c "
from jinja2 import Template
template = Template('Time: {{time}}')
print(template.render(time='14:30'))
"

# Verify base template syntax
python -c "
from jinja2 import Template
with open('base-agent-template.txt') as f:
    template_str = f.read()
template = Template(template_str)
print('✓ Template syntax valid')
"
```

### Issue 3: Personality Too Long (Database)

**Symptoms:**
- Personality > 500 chars
- Database contains full template structure

**Solution:**
```sql
-- Check current lengths
SELECT
    agent_name,
    LENGTH(system_prompt) as length,
    LEFT(system_prompt, 100) as preview
FROM ai_agent_template;

-- If lengths are > 500, templates contain full structure (wrong!)
-- Fix by updating to contain ONLY personality:

UPDATE `ai_agent_template`
SET `system_prompt` = 'You are Cheeko, a playful and curious AI companion for children aged 5-12.'
WHERE `agent_name` = 'Cheeko';

-- Repeat for other templates
```

### Issue 4: Mode Switching Not Working

**Symptoms:**
- User says "Switch to Story mode"
- Agent responds but personality doesn't change
- Logs show success but prompt is same

**Solutions:**
```python
# Check if template_id actually changed in database
# Before switch:
SELECT template_id FROM ai_agent WHERE id = (
    SELECT agent_id FROM ai_device WHERE mac_address = 'xx:xx:xx'
);
# Returns: "cheeko_id"

# User switches to Story
# After switch:
SELECT template_id FROM ai_agent WHERE id = (
    SELECT agent_id FROM ai_device WHERE mac_address = 'xx:xx:xx'
);
# Should return: "story_id" (different!)

# If same, API update failed. Check:
# 1. Mode name normalization
# 2. API response status
# 3. Database transaction committed

# Verify new personality fetched
python -c "
import asyncio
from src.utils.database_helper import DatabaseHelper

async def test():
    helper = DatabaseHelper(url, secret)
    template_id = await helper.get_agent_template_id('00:16:3e:ac:b5:38')
    personality = await helper.fetch_template_content(template_id)
    print(f'Template: {template_id}')
    print(f'Personality: {personality}')

asyncio.run(test())
"
```

### Issue 5: Context Data Missing

**Symptoms:**
- Weather shows empty
- Location shows "Unknown location"
- Time is correct but weather/location empty

**Solutions:**
```python
# Test context gathering individually
from src.utils.prompt_manager import PromptManager

manager = PromptManager(db_helper, config)

# Test time (should always work)
print("Time:", manager._get_current_time())  # "14:30"
print("Date:", manager._get_date())  # "2025-01-24"

# Test location (may need API)
location = await manager._get_location("00:16:3e:ac:b5:38")
print("Location:", location)

# Test weather (may need API)
weather = await manager._get_weather("00:16:3e:ac:b5:38")
print("Weather:", weather)

# If location/weather fail:
# 1. Check API credentials
# 2. Check network connectivity
# 3. Check API rate limits
# 4. Implement fallback: return "Information unavailable"
```

### Issue 6: Cache Not Working

**Symptoms:**
- Every request takes 500ms (should be <10ms when cached)
- Logs show "Building enhanced prompt" every time

**Solutions:**
```python
# Check cache status
service = PromptService()
print("Cache contents:", service.prompt_cache)

# Test cache timing
import time

# First call
start = time.time()
p1 = await service.get_enhanced_prompt("room", "mac")
t1 = time.time() - start
print(f"First call: {t1:.3f}s")

# Second call (should be cached)
start = time.time()
p2 = await service.get_enhanced_prompt("room", "mac")
t2 = time.time() - start
print(f"Cached call: {t2:.3f}s")

# Verify
assert p1 == p2, "Cached prompt differs!"
assert t2 < t1 * 0.1, f"Cache not working ({t2:.3f}s still slow)"

# If cache not working:
# 1. Check cache key generation (must be consistent)
# 2. Check TTL not too short
# 3. Check cache not being cleared between calls
```

### Debug Logging

**Enable verbose logging:**

```python
# In main.py or config
import logging

logging.getLogger("prompt_manager").setLevel(logging.DEBUG)
logging.getLogger("prompt_service").setLevel(logging.DEBUG)
logging.getLogger("database_helper").setLevel(logging.DEBUG)

# Or in code:
logger.setLevel(logging.DEBUG)
```

**Useful log patterns:**

```bash
# Base template loading
grep "📄 Loaded base template" logs/agent.log

# Personality fetching
grep "📝 Retrieved personality" logs/agent.log

# Context gathering
grep "Context gathered" logs/agent.log

# Template rendering
grep "✅ Template rendered" logs/agent.log

# Mode switching
grep "🔄 Mode switch" logs/agent.log

# Errors
grep "ERROR" logs/agent.log | grep -E "(template|prompt|personality)"
```

---

## Performance Benchmarks

### Expected Timings

| Operation | First Call (Cold) | Cached Call | Cache TTL |
|-----------|------------------|-------------|-----------|
| Load base template | 5-10ms | <1ms (memory) | Never expires |
| Get personality (DB) | 50-100ms | <1ms | 1 hour |
| Get location | 100-300ms | <1ms | 1 day |
| Get weather | 200-500ms | <1ms | 5 min |
| Render template | 5-10ms | N/A (always renders) | N/A |
| **Total (cold)** | **~500ms** | **~10ms** | **5 min** |

### Optimization Tips

**1. Pre-warm cache at startup:**

```python
# In main.py, after initializing PromptService
async def prewarm_cache():
    """Pre-load common prompts into cache"""
    common_devices = await db_helper.get_active_devices()  # Last 24h

    for device_mac in common_devices:
        try:
            await prompt_service.get_enhanced_prompt("prewarm", device_mac)
            logger.debug(f"✓ Pre-warmed cache for {device_mac}")
        except:
            pass  # Ignore errors during pre-warming

# Call at startup
await prewarm_cache()
logger.info("✅ Cache pre-warmed for active devices")
```

**2. Increase cache TTL for stable data:**

```yaml
# config.yaml
cache:
  personality_ttl: 7200    # 2 hours (templates rarely change)
  location_ttl: 86400      # 1 day (location rarely changes)
  weather_ttl: 600         # 10 min (acceptable staleness)
```

**3. Use connection pooling for API calls:**

```python
# In DatabaseHelper
class DatabaseHelper:
    def __init__(self, api_url, secret):
        # Reuse session across requests
        self._session = None

    async def _get_session(self):
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def fetch_template_content(self, template_id):
        session = await self._get_session()
        async with session.get(url) as response:
            # Reuses connection
            ...
```

---

## Deployment Checklist

### Pre-deployment

- [ ] Database migration completed
- [ ] Base template file created (`base-agent-template.txt`)
- [ ] All agents have `template_id` set in database
- [ ] Templates updated to contain ONLY personalities (< 500 chars)
- [ ] Manager API endpoints deployed and tested
- [ ] API authentication working
- [ ] Cache configuration tuned
- [ ] Unit tests passing (8/8)
- [ ] Integration tests passing
- [ ] Mode switching tested manually

### Deployment

- [ ] Deploy Manager API changes (template endpoints)
- [ ] Copy `base-agent-template.txt` to production server
- [ ] Deploy LiveKit agent changes (PromptManager, PromptService)
- [ ] Update `config.yaml` on servers
- [ ] Set `read_config_from_api: true`
- [ ] Restart LiveKit agents
- [ ] Monitor logs for errors (first 30 min)
- [ ] Test with real devices (at least 3 different MACs)

### Post-deployment

- [ ] Verify base template loaded correctly (check logs)
- [ ] Verify personalities fetched from DB (not full templates)
- [ ] Check cache hit rates (should be >80% after 10 min)
- [ ] Monitor API response times (<100ms average)
- [ ] Verify memory injection working
- [ ] Test all 6 modes (Cheeko, Story, Music, Tutor, Chat, Puzzle)
- [ ] Test mode switching via voice command
- [ ] Test mode switching via button (if applicable)
- [ ] Collect user feedback (next 24-48 hours)

### Rollback Plan

**If issues occur:**

```bash
# Option 1: Disable template system (quick)
# Edit config.yaml:
read_config_from_api: false

# Restart agents
systemctl restart livekit-agent
# Agents now use default_prompt (fallback)

# Option 2: Fix issue and redeploy
# 1. Identify issue from logs
# 2. Fix code/database/config
# 3. Test in staging
# 4. Redeploy to production

# Option 3: Revert to previous version
git revert HEAD
git push
# Redeploy previous version
```

---

## Future Enhancements

### Planned Features

**1. Conditional Sections in Templates**

```jinja2
{% if child_age < 8 %}
  Use simple language and short sentences.
{% else %}
  Use more advanced vocabulary and complex concepts.
{% endif %}

{% if child_interests contains "science" %}
  Include science facts and experiments in responses.
{% endif %}
```

**2. User-Specific Variables**

```python
context = {
    # Existing
    'current_time': "14:30",
    'weather_info': "Sunny...",

    # NEW: User-specific
    'child_name': "Arjun",
    'child_age': 8,
    'child_interests': ["cricket", "space", "dinosaurs"],
    'parent_name': "Mom",
    'language_preference': "English + Hindi mix",
}
```

Template usage:
```jinja2
<identity>
Hello {{child_name}}! {{base_prompt}}
Your interests include {{child_interests|join(", ")}}.
</identity>
```

**3. Template Inheritance (Advanced)**

```jinja2
{% extends "base-agent-template.txt" %}

{% block personality %}
  You are {{child_name}}'s personal tutor.
  Adapt to {{child_name}}'s learning pace.
{% endblock %}

{% block tools %}
  {{ super() }}  <!-- Include base tools -->
  - math_solver: Solve math problems step-by-step
  - homework_helper: Help with specific subjects
{% endblock %}
```

**4. A/B Testing for Prompts**

```python
# Randomly select variant
variant = random.choice(["variant_a", "variant_b"])

# Fetch variant-specific personality
personality = await db_helper.fetch_template_variant(
    template_id,
    variant
)

# Track which variant user got
analytics.track_prompt_variant(device_mac, variant)

# Measure effectiveness
# - Response satisfaction
# - Conversation length
# - User retention
```

**5. Analytics Dashboard**

```
Template Performance Metrics:
├─ Cheeko Mode
│  ├─ Usage: 10,234 sessions (65%)
│  ├─ Avg. Satisfaction: 4.5/5
│  └─ Avg. Session Duration: 8.2 min
├─ Story Mode
│  ├─ Usage: 3,421 sessions (22%)
│  ├─ Avg. Satisfaction: 4.7/5
│  └─ Avg. Session Duration: 12.5 min
└─ Music Mode
   ├─ Usage: 1,892 sessions (12%)
   ├─ Avg. Satisfaction: 4.3/5
   └─ Avg. Session Duration: 6.1 min
```

---

## Summary

This template-based prompt system provides:

✅ **File-Based Base Template** - Common structure in `base-agent-template.txt` (disk)
✅ **Database Personalities** - Only agent personalities in DB (6 modes, ~200 chars each)
✅ **Dynamic Context** - Real-time time, weather, location
✅ **Memory Integration** - Conversation history in `<memory>` tags
✅ **High Performance** - Multi-layer caching (template/personality/context/rendered)
✅ **Mode Switching** - Voice/button commands work perfectly (NO reconnect!)
✅ **Flexibility** - Jinja2 templates with unlimited placeholders
✅ **Zero Downtime** - Update personalities in DB, no code changes needed
✅ **Easy Maintenance** - Edit base template → affects all 6 modes instantly
✅ **Robust Fallback** - Always functional even if APIs fail

### Key Architecture Points

1. **Base Template (Disk):**
   - File: `base-agent-template.txt`
   - Size: ~3-4KB
   - Contains: Common structure with `{{placeholders}}`
   - Loaded: Once at startup, cached in memory forever
   - Changes: Edit file → restart agent → affects all modes

2. **Personalities (Database):**
   - Table: `ai_agent_template.system_prompt`
   - Size: ~150-250 chars each (6 modes)
   - Contains: ONLY the agent personality
   - Fetched: Via API, cached 1 hour
   - Changes: Update DB → affects immediately (no restart)

3. **Context Data:**
   - Time: Always current (no cache)
   - Location: Cached 1 day
   - Weather: Cached 5 min
   - Emoji list: Static

4. **Rendering:**
   - Engine: Jinja2
   - Input: Base template + personality + context
   - Output: Fully rendered prompt (~4KB)
   - Cache: 5 min per device

5. **Mode Switching:**
   - Updates: `template_id` in database
   - Fetches: NEW personality
   - Renders: SAME base template + NEW personality
   - Result: Different behavior, NO reconnect

### Next Steps

1. ✅ Create `base-agent-template.txt` file
2. ✅ Run database migration (update personalities to be short)
3. ✅ Implement `PromptManager` class
4. ✅ Add Manager API endpoints
5. ✅ Update `PromptService` to use templates
6. ✅ Integrate with `main.py` and `chat_logger.py`
7. ✅ Test all 6 modes
8. ✅ Test mode switching (voice + button)
9. ✅ Deploy to production

For questions or issues, refer to the [Troubleshooting](#troubleshooting) section.

---

**Document Version:** 2.0
**Last Updated:** 2025-01-24
**Architecture:** File-based base template + Database personalities
**Inspired By:** xiaozhi-server's proven template system
