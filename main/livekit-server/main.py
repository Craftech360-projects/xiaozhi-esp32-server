import logging
import asyncio
import os
from dotenv import load_dotenv
from livekit.agents import (
    AgentSession,
    JobContext,
    JobProcess,
    WorkerOptions,
    cli,
    RoomInputOptions,
)
from livekit.plugins import noise_cancellation

# Load environment variables first, before importing modules
load_dotenv(".env")

# Import our organized modules
from src.config.config_loader import ConfigLoader
from src.providers.provider_factory import ProviderFactory
from src.handlers.chat_logger import ChatEventHandler
from src.utils.helpers import UsageManager
from src.services.music_service import MusicService
from src.services.story_service import StoryService
from src.services.foreground_audio_player import ForegroundAudioPlayer
from src.services.unified_audio_player import UnifiedAudioPlayer

# Initialize logger
logger = logging.getLogger("agent")

# Check if educational mode is enabled
ENABLE_EDUCATION = os.getenv("ENABLE_EDUCATION", "false").lower() == "true"

if ENABLE_EDUCATION:
    from src.agent.educational_agent import EducationalAssistant
    logger.info("Educational mode enabled - using EducationalAssistant")
else:
    from src.agent.main_agent import Assistant
    logger.info("Standard mode - using standard Assistant")

def prewarm(proc: JobProcess):
    """Prewarm function to load VAD model and initialize education service"""
    proc.userdata["vad"] = ProviderFactory.create_vad()

    # Initialize education service if enabled and not already done
    if ENABLE_EDUCATION:
        # Check if already prewarmed using a simple file flag
        prewarm_flag_file = "education_prewarmed.flag"

        if os.path.exists(prewarm_flag_file):
            logger.info("📚 Educational system already prewarmed, skipping...")
            proc.userdata["education_service"] = None  # Will be initialized fresh per client
            return

        try:
            import asyncio
            from src.services.education_service import EducationService

            logger.info("🔥 Prewarming educational RAG system...")

            # Create and initialize education service
            education_service = EducationService()

            # Run async initialization in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                success = loop.run_until_complete(education_service.initialize())
                if success:
                    proc.userdata["education_service"] = education_service
                    logger.info("✅ Educational RAG system prewarmed successfully")

                    # Create flag file to prevent future prewarms
                    with open(prewarm_flag_file, "w") as f:
                        f.write("prewarmed")
                else:
                    logger.error("❌ Failed to prewarm educational system")
                    proc.userdata["education_service"] = None
            finally:
                loop.close()

        except Exception as e:
            logger.error(f"❌ Error prewarming education service: {e}")
            proc.userdata["education_service"] = None

async def entrypoint(ctx: JobContext):
    """Main entrypoint for the organized agent"""
    ctx.log_context_fields = {"room": ctx.room.name}
    print(f"Starting agent in room: {ctx.room.name}")

    # Load configuration (environment variables already loaded at module level)
    groq_config = ConfigLoader.get_groq_config()
    tts_config = ConfigLoader.get_tts_config()
    agent_config = ConfigLoader.get_agent_config()

    # Create providers using factory
    llm = ProviderFactory.create_llm(groq_config)
    stt = ProviderFactory.create_stt(groq_config)
    tts = ProviderFactory.create_tts(groq_config, tts_config)
    # Disable turn detection to avoid timeout issues
    turn_detection = ProviderFactory.create_turn_detection()
    vad = ctx.proc.userdata["vad"]

    # Set up voice AI pipeline
    session = AgentSession(
        llm=llm,
        stt=stt,
        tts=tts,
        turn_detection=turn_detection,  # Disabled to avoid timeout
        vad=vad,
        preemptive_generation=agent_config['preemptive_generation'],
        max_tool_steps=25,  # Increased for educational searches
    )

    # Initialize music and story services FIRST
    music_service = MusicService()
    story_service = StoryService()
    audio_player = ForegroundAudioPlayer()
    unified_audio_player = UnifiedAudioPlayer()

    # Create agent based on mode
    if ENABLE_EDUCATION:
        assistant = EducationalAssistant()
        # Use the prewarmed education service from userdata, or create fresh if needed
        education_service = ctx.proc.userdata.get("education_service")
        if education_service:
            assistant.education_service = education_service
            assistant.is_service_initialized = True
            logger.info("✅ Using prewarmed educational RAG system")
        else:
            # Create a lightweight education service for this client
            logger.info("🔧 Creating educational service for client...")
            from src.services.education_service import EducationService

            education_service = EducationService()
            # Quick initialization - should be fast due to global class flags
            success = await education_service.initialize()
            if success:
                assistant.education_service = education_service
                assistant.is_service_initialized = True
                logger.info("✅ Educational service ready for client")
            else:
                logger.warning("⚠️ Failed to initialize educational service for client")
    else:
        assistant = Assistant()

    # Set services for all agents
    assistant.set_services(music_service, story_service, audio_player, unified_audio_player)

    # Setup event handlers and pass assistant reference for abort handling
    ChatEventHandler.set_assistant(assistant)
    ChatEventHandler.setup_session_handlers(session, ctx)

    # Setup usage tracking
    usage_manager = UsageManager()

    async def log_usage():
        """Log usage summary on shutdown"""
        await usage_manager.log_usage()
        logger.info("Sent usage_summary via data channel")

    ctx.add_shutdown_callback(log_usage)

    logger.info("Initializing music and story services...")
    try:
        music_initialized = await music_service.initialize()
        story_initialized = await story_service.initialize()

        if music_initialized:
            languages = await music_service.get_all_languages()
            logger.info(f"Music service initialized with {len(languages)} languages")
        else:
            logger.warning("Music service initialization failed")

        if story_initialized:
            categories = await story_service.get_all_categories()
            logger.info(f"Story service initialized with {len(categories)} categories")
        else:
            logger.warning("Story service initialization failed")

    except Exception as e:
        logger.error(f"Failed to initialize music/story services: {e}")

    # Create room input options with optional noise cancellation
    room_options = None
    if agent_config['noise_cancellation']:
        try:
            room_options = RoomInputOptions(
                noise_cancellation=noise_cancellation.BVC()
            )
            logger.info("Noise cancellation enabled (requires LiveKit Cloud)")
        except Exception as e:
            logger.warning(f"Could not enable noise cancellation: {e}")
            logger.info("Continuing without noise cancellation (local server mode)")
            room_options = None
    else:
        logger.info("Noise cancellation disabled by configuration")

    # Start agent session
    await session.start(
        agent=assistant,
        room=ctx.room,
        room_input_options=room_options,
    )

    # Set up music/story integration with session and context
    try:
        # Pass session and context to both audio players
        audio_player.set_session(session)
        audio_player.set_context(ctx)
        unified_audio_player.set_session(session)
        unified_audio_player.set_context(ctx)
        logger.info("Audio players integrated with session and context")
    except Exception as e:
        logger.warning(f"Failed to integrate audio players with session/context: {e}")

    await ctx.connect()

    # Note: Agent will greet users when they first speak

if __name__ == "__main__":
    # Set timeout based on mode (educational mode needs more time for RAG initialization)
    timeout = 60.0 if ENABLE_EDUCATION else 30.0

    cli.run_app(WorkerOptions(
        entrypoint_fnc=entrypoint,
        prewarm_fnc=prewarm,
        num_idle_processes=1,  # Keep 1 process warmed up for immediate client connections
        initialize_process_timeout=timeout,
    ))