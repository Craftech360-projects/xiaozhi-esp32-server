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
from src.agent.main_agent import Assistant
from src.handlers.chat_logger import ChatEventHandler
from src.utils.helpers import UsageManager
from src.services.music_service import MusicService
from src.services.story_service import StoryService
from src.services.foreground_audio_player import ForegroundAudioPlayer
from src.services.unified_audio_player import UnifiedAudioPlayer

logger = logging.getLogger("agent")

def prewarm(proc: JobProcess):
    """Prewarm function to load VAD model and embedding models"""
    import os
    from src.services.semantic_search import QdrantSemanticSearch, QDRANT_AVAILABLE

    # Load VAD model
    proc.userdata["vad"] = ProviderFactory.create_vad()

    # Pre-load embedding models for semantic search
    if QDRANT_AVAILABLE:
        try:
            logger.info("🔥 Prewarming: Loading embedding model...")
            from sentence_transformers import SentenceTransformer

            # Load the embedding model (this is the heavy operation)
            embedding_model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
            embedding_model = SentenceTransformer(embedding_model_name)
            proc.userdata["embedding_model"] = embedding_model

            # Pre-initialize Qdrant client (but don't test connection yet)
            qdrant_url = os.getenv("QDRANT_URL", "")
            qdrant_api_key = os.getenv("QDRANT_API_KEY", "")

            if qdrant_url and qdrant_api_key:
                from qdrant_client import QdrantClient
                qdrant_client = QdrantClient(
                    url=qdrant_url,
                    api_key=qdrant_api_key,
                    timeout=10
                )
                proc.userdata["qdrant_client"] = qdrant_client
                logger.info("🔥 Prewarming: Qdrant client prepared")

            logger.info(f"✅ Prewarming complete: Embedding model '{embedding_model_name}' loaded")

        except Exception as e:
            logger.warning(f"⚠️ Prewarming failed for embedding models: {e}")
            # Continue without prewarmed models - services will load them later
            proc.userdata["embedding_model"] = None
            proc.userdata["qdrant_client"] = None
    else:
        logger.warning("⚠️ Qdrant dependencies not available for prewarming")
        proc.userdata["embedding_model"] = None
        proc.userdata["qdrant_client"] = None

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
    )

    # Get preloaded models from prewarm
    preloaded_embedding_model = ctx.proc.userdata.get("embedding_model")
    preloaded_qdrant_client = ctx.proc.userdata.get("qdrant_client")

    # Initialize music service with preloaded models, story service without semantic search
    music_service = MusicService(preloaded_embedding_model, preloaded_qdrant_client)
    story_service = StoryService()  # No semantic search - simple initialization
    audio_player = ForegroundAudioPlayer()
    unified_audio_player = UnifiedAudioPlayer()

    # Create agent and inject services
    assistant = Assistant()
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

if __name__ == "__main__":
    cli.run_app(WorkerOptions(
        entrypoint_fnc=entrypoint,
        prewarm_fnc=prewarm,
        num_idle_processes=0,  # Disable process pooling to avoid initialization issues
        initialize_process_timeout=30.0,  # Increase timeout to 30 seconds
    ))