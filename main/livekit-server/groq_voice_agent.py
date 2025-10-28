"""
Simple Groq Voice Agent with LiveKit
Speak via microphone and get responses through STT -> LLM -> TTS pipeline
"""

import logging
from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentSession,
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    cli,
)
from livekit.plugins import groq, silero
from livekit.plugins import deepgram, cartesia

# Import TEN VAD wrapper
from ten_vad_wrapper import TENVAD

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set TEN VAD wrapper to DEBUG for detailed logs
logging.getLogger('ten_vad_wrapper').setLevel(logging.INFO)


async def entrypoint(ctx: JobContext):
    """
    Main entrypoint for the voice agent
    Connects to room and starts voice conversation
    """

    logger.info("Starting Groq voice agent...")

    # Connect to the room
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    logger.info(f"Connected to room: {ctx.room.name}")

    # Create the agent with instructions
    agent = Agent(
        instructions="You are a helpful and friendly AI assistant. Respond naturally and concisely.reply in 50 words only"
    )

    # Create agent session with Groq STT, LLM, TTS and custom VAD
    session = AgentSession(
        # Deepgram STT - Speech to Text
        stt=deepgram.STT(
            model="nova-3",
            language="en",
        ),

        # Groq LLM - Language Model
        llm=groq.LLM(
            model="llama-3.3-70b-versatile",
        ),

        # Groq TTS - Text to Speech
        tts=groq.TTS(
            model="playai-tts",
            voice="Arista-PlayAI",
        ),

        # TEN VAD settings optimized for children + STT compatibility
        # Using TEN VAD instead of Silero for better performance
        vad=TENVAD.load(
            min_speech_duration=0.15,       # INCREASED: STT needs min 100ms audio
            min_silence_duration=0.6,      # INCREASED: Give more time before cutoff
            activation_threshold=0.15,      # ADJUSTED: Balance between sensitivity and noise
            prefix_padding_duration=0.4,   # Add context before speech starts
            sample_rate=16000,             # 16kHz sample rate
            max_buffered_speech=60.0,      # Buffer up to 60 seconds
            hop_size=160,                  # TEN VAD: 160 samples = 10ms latency
        ),

        # OLD: Silero VAD (comment out for now)
        # vad=silero.VAD.load(
        #     min_speech_duration=0.02,
        #     min_silence_duration=0.2,
        #     activation_threshold=0.1,
        #     max_buffered_speech=60.0,
        # ),
    )

    # Add event handlers for debugging
    @session.on("user_started_speaking")
    def on_user_started_speaking():
        logger.info("🎤 USER STARTED SPEAKING - VAD detected speech")

    @session.on("user_stopped_speaking")
    def on_user_stopped_speaking():
        logger.info("🔇 USER STOPPED SPEAKING - VAD ended speech")

    @session.on("user_speech_committed")
    def on_user_speech_committed(message):
        logger.info(f"📝 USER SPEECH COMMITTED: '{message.content if message.content else '[EMPTY]'}'")
        if not message.content:
            logger.warning("⚠️ EMPTY TRANSCRIPT - STT returned no text!")

    @session.on("agent_started_speaking")
    def on_agent_started_speaking():
        logger.info("🤖 AGENT STARTED SPEAKING")

    @session.on("agent_stopped_speaking")
    def on_agent_stopped_speaking():
        logger.info("🤐 AGENT STOPPED SPEAKING")

    # Start the session with the agent
    await session.start(agent=agent, room=ctx.room)
    logger.info("Agent session started - ready for voice input!")
    logger.info("Speak into your microphone...")
    logger.info("📊 Monitoring: VAD triggers, STT transcripts, and agent responses")


if __name__ == "__main__":
    # Run the agent
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
        )
    )
