"""
Cheeko Word Ladder Game - Voice Agent with Game Audio

This script demonstrates:
- Foreground audio: Agent's voice (TTS)
- Background audio: Game sound effects (success, failure, victory) triggered by function tools
- No ambient or thinking sounds - clean audio for kid's game
"""

import asyncio
import logging
import os
import random
from dotenv import load_dotenv
from livekit import agents, rtc
from livekit.agents import (
    Agent,
    AgentSession,
    BackgroundAudioPlayer,
    JobContext,
    function_tool,
    RunContext,
)
from livekit.plugins import openai, silero, groq, deepgram

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VoiceAssistant(Agent):
    """Voice assistant with custom behavior and game logic"""

    # Word list for random word pair generation (100 simple, kid-friendly words)
    WORD_LIST = [
        "cat", "dog", "sun", "moon", "tree", "book", "fish", "bird",
        "cold", "warm", "fast", "slow", "jump", "run", "play", "toy",
        "red", "blue", "big", "small", "hot", "ice", "rain", "snow",
        "cup", "pen", "box", "car", "bus", "road", "door", "room",
        "hand", "foot", "head", "leg", "arm", "nose", "eye", "ear",
        "day", "night", "star", "sky", "hill", "lake", "sand", "rock",
        "frog", "duck", "lion", "bear", "wolf", "fox", "owl", "bee",
        "ball", "kite", "game", "fun", "sing", "dance", "clap", "wave",
        "coin", "ring", "lamp", "desk", "chair", "bed", "wall", "roof",
        "wind", "leaf", "stem", "seed", "root", "bark", "twig", "vine",
        "gold", "silk", "wool", "wood", "iron", "rope", "tile", "mesh",
        "path", "gate", "step", "yard", "pond", "well", "nest", "cave",
        "tent", "flag", "drum", "horn"
    ]

    def __init__(self):
        # Failure tracking for game restart
        self.failure_count = 0
        self.max_failures = 2

        # Game state variables - initialize with random word pair
        self.start_word, self.target_word = self._pick_valid_pair()
        self.current_word = self.start_word

        # Background audio player reference
        self.background_player = None

        super().__init__(
            instructions=f"""
<System>

You are Cheeko — a friendly voice companion who plays the Word Ladder game with a child.
You speak naturally, with warmth, excitement, and patience. 
Keep sentences short and playful.
Focus on only the game no other conversations
Speak like a playing buddy

Reasoning: low
Use cheerful encouragement. Never sound disappointed.

Your goals:
1. Start by telling the start and target words.
2. Wait silently for the kid’s next word (the system will capture it through speech input).
3. Check if the child’s word is a valid English word and starting letter starts from the last letter of the word you said before
4. If correct - announce the next step word.
5. If wrong - gently say it’s not correct and encourage trying again.
6. When the final word is reached, celebrate joyfully!

Rules (for you, Cheeko, not to be spoken):
- Speak to the child as “buddy”.
- Never reveal the full ladder in advance.
- When wrong, say one of:
  “Hmm, not quite! Try again, buddy!”  
  “Almost there! Say it one more time!”  
  “Close! You can do it! Try again!”
- When right, say one of:
  “Yay! That’s right!”  
  “Nice one, buddy!”  
  “Perfect! Let’s move to the next word!”
- When finishing:
  “Woohoo! We made it from START to END! You did amazing!” 🎉
</System>

<Developer>
Game flow template:
1️⃣ Cheeko: “Okay! Let’s start with the word cold, and our goal is warm!”
2️⃣ Wait for the child’s word.
3️⃣ Validate (using your reasoning or optional tool call below).
4️⃣ If correct → respond with positive reinforcement + next challenge.
5️⃣ If wrong → respond kindly and ask to try again.
6️⃣ When target reached → celebrate and end round.
Tool call (optional for validation):
{{"tool":"CheckWord","arguments":{{"word":"..."}}}}
Use only when needed to confirm validity.

If child says "dog" (correct):
→ {{"tool":"play_success_sound","arguments":{{"type":"success","clip":"success.mp3"}}}}
→ Cheeko: "Yay! That's right, cold to dog! You're awesome!"

If child says "cat" (wrong):
→ {{"tool":"play_failure_sound","arguments":{{"type":"failure","clip":"failure.mp3"}}}}
→ Cheeko: "Hmm, not quite buddy! Try again, what word after cold?"


</Developer>

<GameState>
Current start word: {self.start_word}
Current target word: {self.target_word}
Failure count: {self.failure_count}/{self.max_failures}

Important tracking rules:
- When child answers CORRECTLY:
  1. Call play_success_sound()
  2. Reset failure counter internally
  3. Say SHORT response: "Great! Next word?" (NO word chain repetition)

- When child answers WRONG:
  1. Call play_failure_sound()
  2. Increment failure counter internally
  3. If failure count reaches 2, game will auto-restart with new words

- When game RESTARTS (after 2 failures):
  You will receive new start_word and target_word
  Announce: "Let's try new words! Start with [start_word], reach [target_word]!"
</GameState>

<ResponseStyle>
Keep ALL responses SHORT and simple:
✅ "Nice! Next word?"
✅ "Good! What's next?"
✅ "Perfect! Your turn!"
✅ "Try again, buddy!"

❌ "Yay! That's right, cold to dog to great!" (NO - too long, repetitive)
❌ "You said cold, then dog, now..." (NO - don't list chain)

NEVER repeat the word chain. Just acknowledge and move forward!
</ResponseStyle>

<User>
Start word: {self.start_word}
Target word: {self.target_word}
</User>

<Assistant>
Okay buddy! Let's start with the word {self.start_word}!  
We need to reach {self.target_word}!  
What word comes next? (pause)  

(Wait for input...)

If child says correct word:
[Call play_success_sound()]
Nice! Next word?  

(Wait for input...)

If child says wrong word:
[Call play_failure_sound()]
Try again, buddy!  

(Continue loop until reaching target word.)  

When final word reached:
[Call play_victory_sound()]
Woohoo! You did it!

If game restarts after 2 failures:
Let's try new words! Start with [new word], reach [new target]!

</Assistant>

IMPORTANT FUNCTION TOOLS:
You have access to three function tools to play sound effects:
1. play_success_sound() - Call when child's answer is CORRECT
2. play_failure_sound() - Call when child's answer is WRONG
3. play_victory_sound() - Call when child reaches the FINAL target word

Always call the appropriate sound function BEFORE giving your verbal response!""")

    def set_background_player(self, player: BackgroundAudioPlayer):
        """Set the background audio player reference"""
        self.background_player = player

    def _pick_valid_pair(self):
        """
        Pick two random words from WORD_LIST ensuring:
        - Words are different
        - Last letter of word1 ≠ first letter of word2 (to create a puzzle)

        Returns:
            tuple: (start_word, target_word)
        """
        while True:
            word1 = random.choice(self.WORD_LIST)
            word2 = random.choice(self.WORD_LIST)

            # Ensure words are different
            if word1 == word2:
                continue

            # CRITICAL: Ensure last letter ≠ first letter (creates puzzle)
            if word1[-1].lower() != word2[0].lower():
                logger.info(f"Generated word pair: {word1} → {word2}")
                return word1, word2

    @function_tool()
    async def play_success_sound(
        self,
        ctx: RunContext,
    ) -> str:
        """
        Play happy/success sound when child says correct word in the word ladder game.

        Use this function when:
        - The child's word is a valid English word
        - The word follows the word ladder rules (starts with last letter of previous word)
        - The answer is correct

        IMPORTANT: Call this BEFORE giving positive feedback to the child.
        """
        # Reset failure counter on correct answer
        self.failure_count = 0

        if self.background_player:
            try:
                await self.background_player.play("C:/Users/Acer/Cheeko-esp32-server/main/audio/Happy.mp3")
                logger.info(f"✅ Success sound played (failures reset: {self.failure_count})")
                return "Success sound played - child answered correctly!"
            except Exception as e:
                logger.error(f"Failed to play success sound: {e}")
                return f"Could not play success sound: {e}"
        return "Background audio player not available"

    @function_tool()
    async def play_failure_sound(
        self,
        ctx: RunContext,
    ) -> str:
        """
        Play sad/failure sound when child says wrong word in the word ladder game.

        Use this function when:
        - The child's word is not a valid English word
        - The word doesn't follow the word ladder rules
        - The answer is incorrect

        IMPORTANT: Call this BEFORE giving encouragement to try again.
        """
        # Increment failure counter
        self.failure_count += 1
        logger.info(f"Failure count: {self.failure_count}/{self.max_failures}")

        # Play failure sound
        if self.background_player:
            try:
                await self.background_player.play("C:/Users/Acer/Cheeko-esp32-server/main/audio/Sad.mp3")
                logger.info(f"❌ Failure sound played (failure {self.failure_count}/{self.max_failures})")
            except Exception as e:
                logger.error(f"Failed to play failure sound: {e}")

        # Check if game should restart (2 consecutive failures)
        if self.failure_count >= self.max_failures:
            # Generate new word pair
            self.start_word, self.target_word = self._pick_valid_pair()
            self.current_word = self.start_word
            self.failure_count = 0

            logger.info(f"🔄 Game restarting with new words: {self.start_word} → {self.target_word}")
            return f"GAME RESTART! New words: {self.start_word} → {self.target_word}. Tell the child about the new game!"

        return f"Failure sound played - {self.failure_count}/{self.max_failures} failures"

    @function_tool()
    async def play_victory_sound(
        self,
        ctx: RunContext,
    ) -> str:
        """
        Play celebration/victory sound when child reaches the final target word.

        Use this function when:
        - The child has successfully completed the word ladder
        - The final target word has been reached
        - It's time to celebrate!

        IMPORTANT: Call this BEFORE celebrating with the child.
        """
        if self.background_player:
            try:
                await self.background_player.play("C:/Users/Acer/Cheeko-esp32-server/main/audio/victory.mp3")
                logger.info("🎉 Victory sound played")
                return "Victory sound played - game completed successfully!"
            except Exception as e:
                logger.error(f"Failed to play victory sound: {e}")
                return f"Could not play victory sound: {e}"
        return "Background audio player not available"


async def entrypoint(ctx: JobContext):
    """
    Main entrypoint for the voice agent with background audio
    """
    logger.info("Starting agent with background audio support")

    # Connect to the room
    await ctx.connect()
    logger.info(f"Connected to room: {ctx.room.name}")

    # Create background audio player (for on-demand game sounds only)
    # No ambient or thinking sounds - only custom game audio via function tools
    background_audio = BackgroundAudioPlayer()

    # Create the voice agent
    assistant = VoiceAssistant()

    # Connect background audio player to assistant (for function tools)
    assistant.set_background_player(background_audio)

    # Create agent session with STT, LLM, and TTS (foreground audio)
    session = AgentSession(
        # Speech-to-Text: Listens to user
        stt=deepgram.STT(model="nova-2"),
        # Large Language Model: Generates responses
        llm=groq.LLM(model="openai/gpt-oss-120b"),
        # Text-to-Speech: Agent's voice (foreground audio)
        tts=groq.TTS(voice="Aaliyah-PlayAI"),
        # VAD: Voice Activity Detection
        vad=silero.VAD.load(),
    )

    # Start the agent session (connects STT-LLM-TTS pipeline)
    await session.start(room=ctx.room, agent=assistant)

    # Start background audio player (only if not in console mode)
    # Background audio is not supported in console mode
    # This must be called AFTER session.start()
    try:
        await background_audio.start(room=ctx.room, agent_session=session)
        logger.info("Background audio player started")
    except Exception as e:
        logger.warning(f"Background audio not started: {e}")

    # Wait a moment for connection to stabilize
    await asyncio.sleep(1)

    # Agent greets the user (foreground audio - TTS)
    await session.say(
        "Hello! I'm your voice assistant. How can I help you today?",
        allow_interruptions=False,
    )

    # The agent will now handle user interactions automatically
    # Game sounds (success, failure, victory) will play automatically via function tools
    # when the LLM validates the child's answers

    logger.info("Agent is ready and listening for the word ladder game...")


if __name__ == "__main__":
    """
    Run the agent worker

    Before running:
    1. Create a .env file with the following variables:
       LIVEKIT_URL=wss://your-livekit-server.com
       LIVEKIT_API_KEY=your-api-key
       LIVEKIT_API_SECRET=your-api-secret
       GROQ_API_KEY=your-groq-key
       DEEPGRAM_API_KEY=your-deepgram-key

    2. Run with:
       python background_audio.py start
    """
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
