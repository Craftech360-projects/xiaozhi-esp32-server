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
# from src.services.music_service import MusicService
# from src.services.story_service import StoryService
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
    # Load configuration (environment variables already loaded at module level)
    groq_config = ConfigLoader.get_groq_config()
    tts_config = ConfigLoader.get_tts_config()
    agent_config = ConfigLoader.get_agent_config()
    
    logger.info("🔥 Starting prewarm process...")
    
    # Preload VAD model
    proc.userdata["vad"] = ProviderFactory.create_vad()
    logger.info("✅ VAD model prewarmed")

    # Preload LLM model
    try:
        proc.userdata["llm"] = ProviderFactory.create_llm(groq_config)
        logger.info("✅ LLM model prewarmed")
    except Exception as e:
        logger.error(f"❌ Error prewarming LLM: {e}")
        proc.userdata["llm"] = None

    # Preload STT model
    try:
        proc.userdata["stt"] = ProviderFactory.create_stt(groq_config)
        logger.info("✅ STT model prewarmed")
    except Exception as e:
        logger.error(f"❌ Error prewarming STT: {e}")
        proc.userdata["stt"] = None

    # Preload TTS model
    try:
        proc.userdata["tts"] = ProviderFactory.create_tts(groq_config, tts_config)
        logger.info("✅ TTS model prewarmed")
    except Exception as e:
        logger.error(f"❌ Error prewarming TTS: {e}")
        proc.userdata["tts"] = None

    # Turn detection model cannot be prewarmed (requires job context)
    # So we set it to None and let it be created during entrypoint
    proc.userdata["turn_detection"] = None
    logger.info("⚠️ Turn detection model cannot be prewarmed (requires job context)")

    # Initialize education service if enabled
    if ENABLE_EDUCATION:
        try:
            import asyncio
            from src.services.shared_component_manager import initialize_shared_components

            logger.info("🔥 Prewarming educational shared components...")

            # Initialize shared educational components that can be reused across clients
            # Run the async initialization in a new event loop since prewarm is sync
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                success = loop.run_until_complete(initialize_shared_components())
                if success:
                    logger.info("✅ Educational shared components prewarmed successfully")
                    
                    # No need to create an educational service instance during prewarm
                    # Each client will create their own instance using shared components
                    proc.userdata["education_service"] = None
                    logger.info("ℹ️ Educational service instances will be created per client using shared components")
                else:
                    logger.error("❌ Failed to prewarm educational shared components")
                    proc.userdata["education_service"] = None
            finally:
                loop.close()

        except Exception as e:
            logger.error(f"❌ Error prewarming education service: {e}")
            proc.userdata["education_service"] = None

    logger.info("🎉 Prewarm process completed")

async def entrypoint(ctx: JobContext):
    """Main entrypoint for the organized agent"""
    ctx.log_context_fields = {"room": ctx.room.name}
    print(f"Starting agent in room: {ctx.room.name}")

    # Load configuration (environment variables already loaded at module level)
    groq_config = ConfigLoader.get_groq_config()
    tts_config = ConfigLoader.get_tts_config()
    agent_config = ConfigLoader.get_agent_config()

    # Use prewarmed providers from process userdata
    llm = ctx.proc.userdata.get("llm")
    stt = ctx.proc.userdata.get("stt")
    tts = ctx.proc.userdata.get("tts")
    turn_detection = ctx.proc.userdata.get("turn_detection")
    vad = ctx.proc.userdata["vad"]

    # Fallback to factory creation if prewarm failed
    if not llm:
        logger.warning("LLM not prewarmed, creating now...")
        llm = ProviderFactory.create_llm(groq_config)

    if not stt:
        logger.warning("STT not prewarmed, creating now...")
        stt = ProviderFactory.create_stt(groq_config)

    if not tts:
        logger.warning("TTS not prewarmed, creating now...")
        tts = ProviderFactory.create_tts(groq_config, tts_config)

    if not turn_detection:
        logger.info("Creating turn detection model (cannot be prewarmed)...")
        turn_detection = ProviderFactory.create_turn_detection()

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

    # Initialize music and story services FIRST - DISABLED
    # music_service = MusicService()
    # story_service = StoryService()
    music_service = None
    story_service = None
    audio_player = ForegroundAudioPlayer()
    unified_audio_player = UnifiedAudioPlayer()

    # Create agent based on mode
    if ENABLE_EDUCATION:
        assistant = EducationalAssistant()
        # Create a new instance with shared components for each client
        logger.info("🔧 Creating educational service for client with shared components...")
        from src.services.education_service import EducationService

        education_service = EducationService()
        # Initialize using shared components (much faster than individual initialization)
        success = await education_service.initialize(use_shared_components=True)
        if success:
            assistant.education_service = education_service
            assistant.is_service_initialized = True
            # Set Grade 6 Science context for this client
            await education_service.set_student_context(6, "science")
            logger.info("✅ Educational service ready for client with Grade 6 Science context (using shared components)")
        else:
            logger.warning("⚠️ Failed to initialize educational service for client, falling back to individual initialization...")
            # Try with individual components if shared components failed
            education_service = EducationService()
            success = await education_service.initialize(use_shared_components=False)
            if success:
                assistant.education_service = education_service
                assistant.is_service_initialized = True
                # Set Grade 6 Science context
                await education_service.set_student_context(6, "science")
                logger.info("✅ Educational service ready for client with Grade 6 Science context (using individual components)")
            else:
                logger.warning("⚠️ Failed to initialize educational service for client (even with individual components)")
    else:
        assistant = Assistant()

    # Set services for all agents - music and story services disabled
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

    logger.info("Music and story services disabled")
    # Music and story services initialization disabled
    # try:
    #     music_initialized = await music_service.initialize()
    #     story_initialized = await story_service.initialize()
    #
    #     if music_initialized:
    #         languages = await music_service.get_all_languages()
    #         logger.info(f"Music service initialized with {len(languages)} languages")
    #     else:
    #         logger.warning("Music service initialization failed")
    #
    #     if story_initialized:
    #         categories = await story_service.get_all_categories()
    #         logger.info(f"Story service initialized with {len(categories)} categories")
    #     else:
    #         logger.warning("Story service initialization failed")
    #
    # except Exception as e:
    #     logger.error(f"Failed to initialize music/story services: {e}")

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