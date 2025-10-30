# Word Ladder Game - Integration Plan for LiveKit Server

## Overview

This document outlines the plan to integrate the Word Ladder game functionality (with background audio sound effects) into the existing LiveKit server architecture.

## Current Architecture Understanding

### Existing Structure
```
livekit-server/
├── main.py                          # Main entry point (Agent initialization)
├── src/
│   ├── agent/
│   │   ├── main_agent.py           # Assistant class with 15+ function tools
│   │   └── filtered_agent.py       # Base agent with TTS filtering
│   ├── services/                    # Business logic services
│   │   ├── music_service.py
│   │   ├── story_service.py
│   │   ├── foreground_audio_player.py
│   │   └── unified_audio_player.py
│   ├── mcp/                        # Device control via MCP
│   ├── config/                     # Configuration management
│   └── utils/                      # Utilities (cache, helpers)
├── audio/                          # Audio files directory
└── config.yaml                     # Configuration file
```

### Key Points
1. **Function tools** are defined in `src/agent/main_agent.py` using `@function_tool` decorator
2. **Services** are initialized in `main.py` and injected into the Assistant
3. **Prompts** are fetched from database (Manager API) with child profile injection
4. **Audio files** are stored in `audio/` or `main/audios/` directory
5. **BackgroundAudioPlayer** is already available in LiveKit agents framework
6. **Configuration** comes from: API → .env → config.yaml → hardcoded defaults

---

## Integration Plan

### Phase 1: Add Game State Management

**Location:** `src/agent/main_agent.py` (Assistant class)

**What to Add:**
1. **Class-level constants:**
   ```python
   # Word list for word ladder game (100 words)
   WORD_LIST = [
       "cat", "dog", "sun", "moon", "tree", "book", ...
   ]
   ```

2. **Instance variables in `__init__`:**
   ```python
   # Word ladder game state
   self.start_word = "cold"
   self.target_word = "warm"
   self.current_word = "cold"
   self.failure_count = 0
   self.max_failures = 2

   # Background audio player (for game sounds only)
   self.game_audio_player = None
   ```

3. **Helper method:**
   ```python
   def _pick_valid_word_pair(self):
       """Generate two random words ensuring last letter ≠ first letter"""
       # Logic to pick valid word pairs
   ```

**Integration Point:** Add to existing `Assistant` class without modifying existing functionality.

---

### Phase 2: Add Three New Function Tools

**Location:** `src/agent/main_agent.py`

**Tools to Add:**

#### 1. `play_success_sound()` ✅
```python
@function_tool()
async def play_success_sound(self, ctx: RunContext) -> str:
    """
    Play happy sound when child answers correctly in word ladder game.

    This function:
    - Resets failure counter to 0
    - Plays success audio (Happy.mp3)
    - Logs success

    Use this BEFORE giving positive feedback to child.
    """
    # Reset failure counter
    self.failure_count = 0

    # Play success audio via BackgroundAudioPlayer
    if self.game_audio_player:
        await self.game_audio_player.play("audio/Happy.mp3")
        logger.info(f"✅ Success sound (failures reset: {self.failure_count})")

    return "Success sound played - child answered correctly!"
```

#### 2. `play_failure_sound()` ❌
```python
@function_tool()
async def play_failure_sound(self, ctx: RunContext) -> str:
    """
    Play sad sound when child answers incorrectly in word ladder game.

    This function:
    - Increments failure counter
    - Plays failure audio (Sad.mp3)
    - Auto-restarts game after 2 consecutive failures
    - Generates new word pair on restart

    Use this BEFORE giving encouragement feedback.
    """
    # Increment failure counter
    self.failure_count += 1
    logger.info(f"Failure count: {self.failure_count}/{self.max_failures}")

    # Play failure audio
    if self.game_audio_player:
        await self.game_audio_player.play("audio/Sad.mp3")

    # Check for restart (2 failures)
    if self.failure_count >= self.max_failures:
        # Generate new words
        self.start_word, self.target_word = self._pick_valid_word_pair()
        self.current_word = self.start_word
        self.failure_count = 0

        logger.info(f"🔄 Game restart: {self.start_word} → {self.target_word}")
        return f"GAME RESTART! New words: {self.start_word} → {self.target_word}"

    return f"Failure sound played - {self.failure_count}/2 failures"
```

#### 3. `play_victory_sound()` 🎉
```python
@function_tool()
async def play_victory_sound(self, ctx: RunContext) -> str:
    """
    Play celebration sound when child completes word ladder.

    This function:
    - Plays victory audio (victory.mp3)
    - Logs completion

    Use this BEFORE celebrating with the child.
    """
    if self.game_audio_player:
        await self.game_audio_player.play("audio/victory.mp3")
        logger.info("🎉 Victory sound played")

    return "Victory sound played - game completed!"
```

**Integration Point:** Add these methods to the `Assistant` class alongside existing tools (play_music, play_story, etc.)

---

### Phase 3: Initialize BackgroundAudioPlayer

**Location:** `main.py` (entrypoint function)

**What to Add:**

After creating the Assistant and before starting the session:

```python
# Around line 550 (after assistant initialization)

# Initialize BackgroundAudioPlayer for game sounds
game_audio_player = BackgroundAudioPlayer()

# Inject into assistant
assistant.game_audio_player = game_audio_player

# Start game audio player after session starts
await session.start(ctx.room, agent=assistant)
await game_audio_player.start(room=ctx.room, agent_session=session)

logger.info("Game audio player initialized")
```

**Note:** BackgroundAudioPlayer is separate from existing audio players (ForegroundAudioPlayer, UnifiedAudioPlayer). It plays on a separate track.

---

### Phase 4: Audio Files Setup

**Location:** `main/livekit-server/audio/` or `main/audios/`

**Files Needed:**
1. **Happy.mp3** - Success/correct answer sound (1-3 seconds)
2. **Sad.mp3** - Failure/wrong answer sound (1-2 seconds)
3. **victory.mp3** - Victory/celebration sound (3-5 seconds)

**Recommended Format:**
- **Format:** WAV (fastest) or MP3
- **Sample Rate:** 16kHz
- **Channels:** Mono
- **Duration:** 1-5 seconds
- **Size:** < 1MB per file

**Path Configuration:**
```python
# In function tools, use relative paths
AUDIO_BASE_PATH = "audio/"

# Or use environment variable
GAME_AUDIO_PATH = os.getenv("GAME_AUDIO_PATH", "audio/")

# Full paths
SUCCESS_SOUND = os.path.join(GAME_AUDIO_PATH, "Happy.mp3")
FAILURE_SOUND = os.path.join(GAME_AUDIO_PATH, "Sad.mp3")
VICTORY_SOUND = os.path.join(GAME_AUDIO_PATH, "victory.mp3")
```

---

### Phase 5: Prompt Integration

**Location:** Database (Manager API) - Prompt will be fetched from backend

**What Needs to be in the Prompt:**

The prompt should include instructions for the word ladder game and when to call the function tools:

```
<GameMode name="word_ladder">
You are playing the Word Ladder game with a child.

Game Rules:
- Start word: {start_word}
- Target word: {target_word}
- Each word must start with the last letter of the previous word
- All words must be valid English words

Response Style:
- Keep responses SHORT (5-10 words max)
- Do NOT repeat the word chain
- Just say "Nice! Next word?" or "Try again!"

Function Tools:
- When child answers CORRECTLY:
  1. Call play_success_sound()
  2. Say short positive response: "Great! Next word?"

- When child answers WRONG:
  1. Call play_failure_sound()
  2. Say short encouragement: "Try again, buddy!"

- When child reaches TARGET word:
  1. Call play_victory_sound()
  2. Celebrate: "You did it!"

Game Restart:
- After 2 consecutive failures, game restarts automatically
- You will be told: "GAME RESTART! New words: [word1] → [word2]"
- Announce new words to child: "Let's try new words! Start with [word1], reach [word2]!"

Current Game State:
- Start word: {start_word}
- Target word: {target_word}
- Failures: {failure_count}/2
</GameMode>
```

**Dynamic Variables:**
The prompt will need placeholders that are populated at runtime:
- `{start_word}` - Current start word
- `{target_word}` - Current target word
- `{failure_count}` - Current failure count

**Implementation Options:**

**Option A: Static Prompt (Simple)**
- Prompt is stored in database with game instructions
- Agent uses hardcoded start/target words (cold → warm)
- Works for testing and MVP

**Option B: Dynamic Prompt Updates (Recommended)**
- Add method to update prompt dynamically when game restarts:
```python
def _update_game_prompt(self):
    """Update agent instructions with current game state"""
    # This is similar to existing update_agent_mode() function
    # Update self instructions with current start_word, target_word
```

**Option C: Template-Based (Best for Production)**
- Use existing template system in `prompt_service.py`
- Create Jinja2 template with game state variables
- Render template with current game state
- Already supported in the codebase!

---

### Phase 6: Configuration (Optional)

**Location:** `config.yaml` or `.env`

**Optional Settings:**
```yaml
# config.yaml
word_ladder:
  enabled: true
  max_failures: 2
  audio_path: "audio/"
  word_list_size: 100
```

Or in `.env`:
```bash
# Enable word ladder game
WORD_LADDER_ENABLED=true
WORD_LADDER_MAX_FAILURES=2
WORD_LADDER_AUDIO_PATH=audio/
```

**Access in Code:**
```python
max_failures = int(os.getenv("WORD_LADDER_MAX_FAILURES", "2"))
audio_path = os.getenv("WORD_LADDER_AUDIO_PATH", "audio/")
```

---

## Integration Steps (Implementation Order)

### Step 1: Prepare Audio Files
1. Get or create 3 audio files (Happy.mp3, Sad.mp3, victory.mp3)
2. Place in `main/livekit-server/audio/` directory
3. Test audio file paths are correct

### Step 2: Add Game State to Assistant
1. Open `src/agent/main_agent.py`
2. Add `WORD_LIST` constant at class level
3. Add game state variables to `__init__` method
4. Add `_pick_valid_word_pair()` helper method

### Step 3: Add Three Function Tools
1. Add `play_success_sound()` method with `@function_tool` decorator
2. Add `play_failure_sound()` method with game restart logic
3. Add `play_victory_sound()` method
4. Test that methods are syntactically correct

### Step 4: Initialize BackgroundAudioPlayer
1. Open `main.py`
2. Find where Assistant is created (around line 520-530)
3. Add BackgroundAudioPlayer initialization
4. Inject into assistant
5. Start player after session starts

### Step 5: Update Database Prompt
1. Add word ladder game instructions to agent prompt in database
2. Include function tool usage guidelines
3. Include game state variables (start_word, target_word)
4. Test prompt rendering with template system

### Step 6: Test End-to-End
1. Run agent: `python main.py dev`
2. Connect via playground or device
3. Start word ladder game with voice
4. Test correct answer → Happy.mp3 plays
5. Test wrong answer → Sad.mp3 plays
6. Test 2 consecutive wrong answers → Game restarts
7. Test victory → victory.mp3 plays

---

## Code Changes Summary

### Files to Modify:

1. **`src/agent/main_agent.py`** (200-250 lines added)
   - Add WORD_LIST constant
   - Add game state variables to __init__
   - Add _pick_valid_word_pair() helper
   - Add 3 function tools (play_success_sound, play_failure_sound, play_victory_sound)

2. **`main.py`** (10-15 lines added)
   - Initialize BackgroundAudioPlayer
   - Inject into assistant
   - Start player after session

3. **Database Prompt** (Update via Manager API or config.yaml)
   - Add game instructions
   - Add function tool guidelines
   - Add game state variables

### Files to Create:

1. **Audio files:**
   - `audio/Happy.mp3`
   - `audio/Sad.mp3`
   - `audio/victory.mp3`

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         User (Child)                         │
└────────────────────────┬────────────────────────────────────┘
                         │ Voice Input
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    LiveKit Room                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Agent Session (STT-LLM-TTS Pipeline)         │  │
│  │                                                        │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐          │  │
│  │  │   STT    │→ │   LLM    │→ │   TTS    │          │  │
│  │  │(Deepgram)│  │  (Groq)  │  │  (Groq)  │          │  │
│  │  └──────────┘  └─────┬────┘  └──────────┘          │  │
│  │                       │                               │  │
│  │                       │ Function Call                 │  │
│  │                       ▼                               │  │
│  │         ┌─────────────────────────────────┐          │  │
│  │         │   Assistant (main_agent.py)     │          │  │
│  │         │                                  │          │  │
│  │         │  - Existing Tools (15+):        │          │  │
│  │         │    • play_music()               │          │  │
│  │         │    • play_story()               │          │  │
│  │         │    • set_device_volume()        │          │  │
│  │         │    • search_wikipedia()         │          │  │
│  │         │    • ...                        │          │  │
│  │         │                                  │          │  │
│  │         │  - NEW Tools (3):               │          │  │
│  │         │    • play_success_sound() ✅    │          │  │
│  │         │    • play_failure_sound() ❌    │          │  │
│  │         │    • play_victory_sound() 🎉    │          │  │
│  │         │                                  │          │  │
│  │         │  - Game State:                  │          │  │
│  │         │    • WORD_LIST (100 words)      │          │  │
│  │         │    • start_word, target_word    │          │  │
│  │         │    • failure_count (0-2)        │          │  │
│  │         │    • _pick_valid_word_pair()    │          │  │
│  │         └──────────────┬──────────────────┘          │  │
│  │                        │                               │  │
│  └────────────────────────┼───────────────────────────────┘  │
│                           │                                  │
│                           ▼                                  │
│         ┌─────────────────────────────────────┐             │
│         │   BackgroundAudioPlayer             │             │
│         │   (Separate audio track)            │             │
│         │                                      │             │
│         │   Plays:                             │             │
│         │   • audio/Happy.mp3   (success)     │             │
│         │   • audio/Sad.mp3     (failure)     │             │
│         │   • audio/victory.mp3 (win)         │             │
│         └─────────────────────────────────────┘             │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │           Existing Services (Unchanged)                 │ │
│  │  • MusicService                                         │ │
│  │  • StoryService                                         │ │
│  │  • ForegroundAudioPlayer (music/stories)               │ │
│  │  • UnifiedAudioPlayer                                   │ │
│  │  • MCPExecutor (device control)                        │ │
│  │  • GoogleSearchService                                  │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
                    Audio Output
              (Foreground + Background)
```

---

## Key Integration Points

### 1. No Conflict with Existing Audio
- **Existing:** ForegroundAudioPlayer (music/stories)
- **New:** BackgroundAudioPlayer (game sounds)
- **Separation:** Different audio tracks, no interference
- **Control:** Can play simultaneously

### 2. Function Tool Consistency
- **Pattern:** Same as existing tools (play_music, play_story)
- **Decorator:** `@function_tool()` like all other tools
- **Async:** All tools are async
- **Return:** String message for LLM context

### 3. Service Injection Pattern
- **Existing pattern:** Services injected via `set_services()` in main.py
- **For game audio:** Direct attribute assignment (`assistant.game_audio_player = ...`)
- **Alternative:** Add to `set_services()` method

### 4. Prompt Integration
- **Existing system:** Prompts fetched from Manager API
- **Game instructions:** Add to database prompt
- **Template support:** Already available via PromptService
- **Dynamic updates:** Can use `update_agent_mode()` pattern

---

## Testing Strategy

### Unit Tests
```python
# tests/test_word_ladder.py

def test_pick_valid_word_pair():
    """Test word pair generation"""
    assistant = Assistant()
    word1, word2 = assistant._pick_valid_word_pair()

    # Assertions
    assert word1 != word2
    assert word1[-1].lower() != word2[0].lower()
    assert word1 in assistant.WORD_LIST
    assert word2 in assistant.WORD_LIST

def test_failure_counter_reset_on_success():
    """Test failure counter resets on correct answer"""
    assistant = Assistant()
    assistant.failure_count = 1

    # Simulate success
    await assistant.play_success_sound(mock_context)

    assert assistant.failure_count == 0

def test_game_restart_after_two_failures():
    """Test game restarts after 2 failures"""
    assistant = Assistant()
    initial_words = (assistant.start_word, assistant.target_word)

    # First failure
    await assistant.play_failure_sound(mock_context)
    assert assistant.failure_count == 1

    # Second failure (triggers restart)
    result = await assistant.play_failure_sound(mock_context)

    assert "GAME RESTART" in result
    assert assistant.failure_count == 0
    assert (assistant.start_word, assistant.target_word) != initial_words
```

### Integration Tests
1. Test BackgroundAudioPlayer initialization
2. Test audio file paths are correct
3. Test function tool execution in live session
4. Test audio plays on separate track
5. Test game restart logic end-to-end

### Manual Testing
1. Connect device to agent
2. Start word ladder game via voice
3. Test all 3 scenarios (success, failure, victory)
4. Verify audio files play correctly
5. Test game restart after 2 failures
6. Test that music/stories still work (no conflict)

---

## Rollout Plan

### Phase 1: Development (Week 1)
- Add function tools to main_agent.py
- Add BackgroundAudioPlayer initialization
- Test locally with dev mode
- Verify audio files play correctly

### Phase 2: Prompt Update (Week 1-2)
- Add game instructions to database prompt
- Test prompt rendering with template system
- Verify LLM calls function tools correctly

### Phase 3: Testing (Week 2)
- Unit tests for game logic
- Integration tests for audio playback
- Manual testing on devices
- Load testing (multiple concurrent games)

### Phase 4: Deployment (Week 2-3)
- Deploy to staging environment
- Test with real devices
- Monitor logs for errors
- Collect user feedback

### Phase 5: Production (Week 3)
- Deploy to production
- Monitor performance metrics
- A/B test with control group
- Iterate based on feedback

---

## Success Metrics

### Technical Metrics
- ✅ Audio files play within 500ms of function call
- ✅ No audio playback conflicts with music/stories
- ✅ Game restart works correctly after 2 failures
- ✅ Word pair generation follows validation rules
- ✅ Memory usage increase < 50MB per session

### User Metrics
- ✅ Children engage with word ladder game
- ✅ Average game duration > 3 minutes
- ✅ Completion rate > 30%
- ✅ Positive sentiment in feedback
- ✅ Repeat usage rate > 50%

---

## Risk Assessment

### Low Risk ✅
- **Adding function tools:** Standard pattern, well-tested
- **BackgroundAudioPlayer:** Built-in LiveKit feature
- **Audio file playback:** Simple, isolated functionality

### Medium Risk ⚠️
- **Audio file size:** Large files may cause timeout
  - **Mitigation:** Use small WAV files (< 500KB)
- **Prompt complexity:** Too detailed may confuse LLM
  - **Mitigation:** Test with multiple prompt variations
- **Game state persistence:** Not saved between sessions
  - **Mitigation:** Document as feature, not bug

### High Risk 🚫
- **Conflict with existing audio:** None identified
- **Breaking existing functionality:** Unlikely, changes are additive
- **Performance degradation:** Audio player is lightweight

---

## Future Enhancements

### Phase 2 Features
1. **Difficulty levels:** Easy (3-letter words) / Hard (5-letter words)
2. **Hints:** Give first letter of valid next word
3. **Score tracking:** Track wins/losses in database
4. **Leaderboard:** Compare with other children
5. **Custom word lists:** Allow parents to add words
6. **Multi-language:** Support other languages

### Phase 3 Features
1. **Adaptive difficulty:** Adjust based on child's performance
2. **Time challenge:** Complete ladder within time limit
3. **Multiplayer:** Two children compete
4. **Theme-based:** Animals, food, colors categories
5. **Progress persistence:** Save game state between sessions

---

## Conclusion

The word ladder game integration is **low-risk, high-value** and follows existing patterns in the codebase. The implementation is straightforward:

1. ✅ Add 3 function tools to existing Assistant class
2. ✅ Initialize BackgroundAudioPlayer (10 lines in main.py)
3. ✅ Add game instructions to database prompt
4. ✅ Place 3 audio files in audio/ directory

**Total Code Changes:** ~250 lines
**Files Modified:** 2 (main_agent.py, main.py)
**Dependencies:** None (uses existing LiveKit framework)
**Deployment Risk:** Low

The game enhances child engagement while maintaining full compatibility with existing features (music, stories, device control).

---

## Next Steps

1. ✅ Review this integration plan
2. ✅ Get approval from team
3. ⏳ Implement Step 1-6 (see Implementation Order section)
4. ⏳ Test locally with dev mode
5. ⏳ Deploy to staging
6. ⏳ Production rollout

**Estimated Development Time:** 2-3 days
**Estimated Testing Time:** 1-2 days
**Estimated Deployment Time:** 1 day

**Total Timeline:** 4-6 days from approval to production

---

**Document Version:** 1.0
**Last Updated:** 2025-10-30
**Author:** Integration Planning Team
