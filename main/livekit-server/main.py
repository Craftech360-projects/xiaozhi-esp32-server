import logging
import asyncio
import os
import aiohttp
from dotenv import load_dotenv
from livekit.agents import (
    AgentSession,
    JobContext,
    JobProcess,
    WorkerOptions,
    cli,
    RoomInputOptions,
)
from livekit import rtc
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

async def delete_livekit_room(room_name: str):
    """Delete a LiveKit room using the API"""
    try:
        # Get LiveKit credentials from environment
        livekit_url = os.getenv("LIVEKIT_URL", "").replace("ws://", "http://").replace("wss://", "https://")
        api_key = os.getenv("LIVEKIT_API_KEY")
        api_secret = os.getenv("LIVEKIT_API_SECRET")

        if not all([livekit_url, api_key, api_secret]):
            logger.warning("LiveKit credentials not configured for room deletion")
            return

        # For LiveKit Cloud, use the management API
        # For self-hosted, this would be different
        from livekit import api

        # Create API client
        lk_api = api.LiveKitAPI(
            url=livekit_url,
            api_key=api_key,
            api_secret=api_secret,
        )

        # Delete the room using the correct API method
        from livekit.api import DeleteRoomRequest
        request = DeleteRoomRequest(room=room_name)
        await lk_api.room.delete_room(request)
        logger.info(f"🗑️ Successfully deleted room: {room_name}")

    except ImportError:
        logger.warning("LiveKit API client not available, using HTTP API directly")
        # Fallback to direct HTTP API call
        try:
            import jwt
            import time

            # Generate access token for API call
            now = int(time.time())
            token_payload = {
                "exp": now + 600,  # 10 minutes
                "iss": api_key,
                "nbf": now,
                "sub": api_key,
                "roomAdmin": True,
                "room": room_name,
            }
            token = jwt.encode(token_payload, api_secret, algorithm="HS256")

            # Make API call to delete room
            async with aiohttp.ClientSession() as session:
                try:
                    headers = {"Authorization": f"Bearer {token}"}
                    url = f"{livekit_url}/twirp/livekit.RoomService/DeleteRoom"
                    payload = {"room": room_name}

                    async with session.post(url, json=payload, headers=headers) as resp:
                        if resp.status == 200:
                            logger.info(f"🗑️ Successfully deleted room via API: {room_name}")
                        else:
                            logger.error(f"Failed to delete room: {resp.status}")
                finally:
                    await session.close()
        except Exception as e:
            logger.error(f"Failed to delete room via HTTP API: {e}")
    except Exception as e:
        logger.error(f"Failed to delete room: {e}")

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

    # Track participants and manage room lifecycle
    participant_count = len(ctx.room.remote_participants)
    cleanup_completed = False

    async def cleanup_room_and_session():
        """Cleanup room and session when participant leaves"""
        nonlocal cleanup_completed
        if cleanup_completed:
            return
        cleanup_completed = True

        try:
            logger.info("🔴 Initiating room and session cleanup")

            # 1. End the agent session (use aclose() method)
            try:
                if session and hasattr(session, 'aclose'):
                    logger.info("Ending agent session")
                    await session.aclose()
            except Exception as e:
                logger.warning(f"Session close error (expected during shutdown): {e}")

            # 2. Stop audio services
            try:
                if audio_player:
                    await audio_player.stop()
                if unified_audio_player:
                    await unified_audio_player.stop()
            except Exception as e:
                logger.warning(f"Audio service stop error: {e}")

            # 3. Clean up music and story services (if cleanup methods exist)
            try:
                if music_service and hasattr(music_service, 'cleanup'):
                    await music_service.cleanup()
                if story_service and hasattr(story_service, 'cleanup'):
                    await story_service.cleanup()
            except Exception as e:
                logger.warning(f"Service cleanup error: {e}")

            # 4. Disconnect from room (gracefully handle already disconnected)
            try:
                if ctx.room and hasattr(ctx.room, 'disconnect'):
                    logger.info("Disconnecting from LiveKit room")
                    await ctx.room.disconnect()
            except Exception as e:
                logger.warning(f"Room disconnect error (may already be disconnected): {e}")

            # 5. Request room deletion via API (requires admin token)
            try:
                room_name = ctx.room.name if ctx.room else "unknown"
                await delete_livekit_room(room_name)
            except Exception as e:
                logger.warning(f"Room deletion error: {e}")

            logger.info("✅ Room and session cleanup completed")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            # Continue cleanup even if there are errors

    # Monitor participant events
    @ctx.room.on("participant_disconnected")
    def on_participant_disconnected(participant: rtc.RemoteParticipant):
        nonlocal participant_count
        participant_count -= 1
        logger.info(f"👤 Participant disconnected: {participant.identity}, remaining: {participant_count}")

        # If no participants left, cleanup room and session
        if participant_count == 0:
            logger.info("🔴 No participants remaining, initiating cleanup")
            asyncio.create_task(cleanup_room_and_session())

    @ctx.room.on("participant_connected")
    def on_participant_connected(participant: rtc.RemoteParticipant):
        nonlocal participant_count
        participant_count += 1
        logger.info(f"👤 Participant connected: {participant.identity}, total: {participant_count}")

    # Monitor room disconnection
    @ctx.room.on("disconnected")
    def on_room_disconnected():
        logger.info("🔴 Room disconnected, initiating cleanup")
        asyncio.create_task(cleanup_room_and_session())

    # Add cleanup to shutdown callback
    ctx.add_shutdown_callback(cleanup_room_and_session)

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