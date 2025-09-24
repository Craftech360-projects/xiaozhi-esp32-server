from src.handlers.report_handle import start_report_thread, stop_report_thread
from src.config.manage_api_client import init_service as init_manage_api, manage_api_http_safe_close
from src.services.unified_audio_player import UnifiedAudioPlayer
from src.services.foreground_audio_player import ForegroundAudioPlayer
from src.services.story_service import StoryService
from src.services.music_service import MusicService
from src.utils.helpers import UsageManager
from src.handlers.chat_logger import ChatEventHandler
from src.agent.main_agent import Assistant
from src.providers.provider_factory import ProviderFactory
from src.config.config_loader import ConfigLoader
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
# from livekit.plugins import noise_cancellation  # Commented out due to import issues

# Load environment variables first, before importing modules
load_dotenv(".env")

# Log some key environment variables to show what's loaded
print("="*60)
print("XIAOZHI LIVEKIT AGENT - Configuration Status")
print("="*60)
print("Environment Variables (.env):")
print(f"   LIVEKIT_URL: {os.getenv('LIVEKIT_URL', 'Not set')}")
print(f"   GROQ_API_KEY: {'Set' if os.getenv('GROQ_API_KEY') else 'Not set'}")
print(f"   TTS_PROVIDER: {os.getenv('TTS_PROVIDER', 'Not set')}")
print(f"   REDIS_URL: {os.getenv('REDIS_URL', 'Not set')[:20]}..." if os.getenv(
    'REDIS_URL') else "   REDIS_URL: Not set")

# Import our organized modules

logger = logging.getLogger("agent")

# Log configuration source at startup
startup_config = ConfigLoader._load_yaml_config()
if startup_config.get('read_config_from_api', False):
    init_manage_api(startup_config)
print("\nConfiguration Source (config.yaml):")
if startup_config.get('read_config_from_api', False):
    manager_api_config = startup_config.get('manager_api', {})
    manager_api_url = manager_api_config.get('url', 'Not configured')
    print(f"   Mode: MANAGER API (Dynamic)")
    print(f"   API URL: {manager_api_url}")
    print(f"   Status: ENABLED - Will fetch models from backend")
else:
    print(f"   Mode: LOCAL CONFIG (Static)")
    print(f"   Status: DISABLED - Using local fallback models")
print("="*60)


def prewarm(proc: JobProcess):
    """Prewarm function to load VAD model and embedding models"""
    import os
    from src.services.semantic_search import QdrantSemanticSearch, QDRANT_AVAILABLE

    # Load VAD model
    proc.userdata["vad"] = ProviderFactory.create_vad()

    # Pre-load embedding models for semantic search
    if QDRANT_AVAILABLE:
        try:
            logger.info("PREWARM: Loading embedding model...")
            from sentence_transformers import SentenceTransformer

            # Load the embedding model (this is the heavy operation)
            embedding_model_name = os.getenv(
                "EMBEDDING_MODEL", "all-MiniLM-L6-v2")
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
                logger.info("PREWARM: Qdrant client prepared")

            logger.info(
                f"PREWARM: Complete - Embedding model '{embedding_model_name}' loaded")

        except Exception as e:
            logger.warning(f"PREWARM: Failed for embedding models: {e}")
            # Continue without prewarmed models - services will load them later
            proc.userdata["embedding_model"] = None
            proc.userdata["qdrant_client"] = None
    else:
        logger.warning("PREWARM: Qdrant dependencies not available")
        proc.userdata["embedding_model"] = None
        proc.userdata["qdrant_client"] = None


async def entrypoint(ctx: JobContext):
    """Main entrypoint for the organized agent"""
    ctx.log_context_fields = {"room": ctx.room.name}
    logger.info(f"AGENT: Starting in room - {ctx.room.name}")

    # Load configuration from Java backend API (not env files)
    logger.info("AGENT: Loading configuration from configured source...")
    groq_config = await ConfigLoader.get_groq_config()
    tts_config = await ConfigLoader.get_tts_config()
    # This one stays sync as it's for agent settings
    agent_config = ConfigLoader.get_agent_config()

    logger.info(
        f"AGENT: Configuration loaded - LLM={groq_config.get('llm_model')}, STT={groq_config.get('stt_model')}, TTS={tts_config.get('model')}")

    # Create providers using factory
    llm = ProviderFactory.create_llm(groq_config)
    stt = ProviderFactory.create_stt(groq_config)
    tts = ProviderFactory.create_tts(groq_config, tts_config)
    # Disable turn detection to avoid timeout issues
    turn_detection = ProviderFactory.create_turn_detection()
    vad = ctx.proc.userdata["vad"]

    # Set up voice AI pipeline with turn detection enabled
    logger.info("AGENT: Enabling turn detection for better conversation flow")
    logger.info(f"AGENT: Turn detection object: {turn_detection}")
    logger.info(f"AGENT: VAD object: {vad}")

    session = AgentSession(
        llm=llm,
        stt=stt,
        tts=tts,
        turn_detection=turn_detection,  # Enable turn detection
        vad=vad,
        preemptive_generation=agent_config['preemptive_generation'],
    )

    logger.info(f"AGENT: AgentSession created with turn detection enabled: {turn_detection is not None}")

    session.session_id = ctx.room.name
    mac_address = "unknown-device"
    for participant in ctx.room.remote_participants.values():
        if ":" in participant.identity:
            mac_address = participant.identity
            break
    session.mac_address = mac_address

    start_report_thread(session)

    async def stop_reporting():
        await asyncio.to_thread(stop_report_thread, session)

    ctx.add_shutdown_callback(stop_reporting)

    async def close_api_client():
        await asyncio.to_thread(manage_api_http_safe_close)

    ctx.add_shutdown_callback(close_api_client)

    # Get preloaded models from prewarm
    preloaded_embedding_model = ctx.proc.userdata.get("embedding_model")
    preloaded_qdrant_client = ctx.proc.userdata.get("qdrant_client")

    # Initialize music service with preloaded models, story service without semantic search
    music_service = MusicService(
        preloaded_embedding_model, preloaded_qdrant_client)
    story_service = StoryService()  # No semantic search - simple initialization
    audio_player = ForegroundAudioPlayer()
    unified_audio_player = UnifiedAudioPlayer()

    # Create agent and inject services
    assistant = Assistant()
    assistant.set_services(music_service, story_service,
                           audio_player, unified_audio_player)

    # Setup event handlers and pass assistant reference for abort handling
    ChatEventHandler.set_assistant(assistant)

    # OPTIMIZED: Single-point response capture to avoid race conditions
    # Priority order: session.say() > LLM stream > fallbacks
    original_say = session.say

    async def patched_say(text, **kwargs):
        # PRIMARY: Capture response text at session.say() level (most reliable)
        if text and text.strip() and text != "[Audio response generated]":
            ChatEventHandler.set_last_response(text.strip())
            logger.info(f"🎯 Session.say captured (PRIMARY): {text[:50]}...")

        # Call original say method
        return await original_say(text, **kwargs)

    session.say = patched_say
    logger.info("✅ Session.say hook installed successfully")

    # SECONDARY: LLM stream capture as backup (lower priority to avoid conflicts)
    if hasattr(llm, '_client'):
        original_client = llm._client
        if hasattr(original_client, 'chat') and hasattr(original_client.chat, 'completions'):
            original_create = original_client.chat.completions.create

            async def patched_create(*args, **kwargs):
                # Call the original method to get the stream
                stream = await original_create(*args, **kwargs)
                # Create a wrapper to capture the response
                return LLMStreamCapture(stream)

            # Create wrapper class to capture streaming response (backup only)
            class LLMStreamCapture:
                def __init__(self, original_stream):
                    self._stream = original_stream
                    self._captured_text = ""
                    self._response_captured_by_say = False

                def __aiter__(self):
                    return self

                async def __anext__(self):
                    chunk = await self._stream.__anext__()

                    # Extract content from streaming chunk
                    if hasattr(chunk, 'choices') and chunk.choices:
                        choice = chunk.choices[0]
                        if hasattr(choice, 'delta') and choice.delta:
                            content = getattr(choice.delta, 'content', None)
                            if content:
                                self._captured_text += content

                        # Check if stream is complete
                        if hasattr(choice, 'finish_reason') and choice.finish_reason == 'stop':
                            if self._captured_text.strip():
                                # Check if session.say already captured this response
                                latest_response = ChatEventHandler._chat_sync.get_latest_response()
                                if not latest_response or latest_response != self._captured_text.strip():
                                    # Only capture if session.say didn't already get it
                                    ChatEventHandler.set_last_response(self._captured_text.strip())
                                    logger.info(f"🔄 LLM stream captured (BACKUP): {self._captured_text[:50]}...")
                                else:
                                    logger.info(f"⏭️ LLM stream skipped (already captured by session.say)")

                    return chunk

                async def __aenter__(self):
                    if hasattr(self._stream, '__aenter__'):
                        await self._stream.__aenter__()
                    return self

                async def __aexit__(self, exc_type, exc_val, exc_tb):
                    if hasattr(self._stream, '__aexit__'):
                        return await self._stream.__aexit__(exc_type, exc_val, exc_tb)

            original_client.chat.completions.create = patched_create
            logger.info("✅ LLM stream capture installed as backup")
    else:
        logger.warning("Could not find LLM client to hook into")

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
            logger.info(
                f"Music service initialized with {len(languages)} languages")
        else:
            logger.warning("Music service initialization failed")

        if story_initialized:
            categories = await story_service.get_all_categories()
            logger.info(
                f"Story service initialized with {len(categories)} categories")
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
            logger.info(
                "Continuing without noise cancellation (local server mode)")
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
        logger.warning(
            f"Failed to integrate audio players with session/context: {e}")

    await ctx.connect()

if __name__ == "__main__":
    cli.run_app(WorkerOptions(
        entrypoint_fnc=entrypoint,
        prewarm_fnc=prewarm,
        num_idle_processes=0,  # Disable process pooling to avoid initialization issues
        initialize_process_timeout=30.0,  # Increase timeout to 30 seconds
    ))
