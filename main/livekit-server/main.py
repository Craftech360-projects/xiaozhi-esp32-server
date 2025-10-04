from src.utils.model_preloader import model_preloader
from src.utils.model_cache import model_cache
from src.utils.database_helper import DatabaseHelper
from src.services.chat_history_service import ChatHistoryService
from src.services.prompt_service import PromptService
from src.services.unified_audio_player import UnifiedAudioPlayer
from src.services.foreground_audio_player import ForegroundAudioPlayer
from src.services.story_service import StoryService
from src.services.music_service import MusicService
from src.mcp.device_control_service import DeviceControlService
from src.mcp.mcp_executor import LiveKitMCPExecutor
from src.utils.helpers import UsageManager
from src.handlers.chat_logger import ChatEventHandler
from src.agent.main_agent import Assistant
from src.providers.provider_factory import ProviderFactory
from src.config.config_loader import ConfigLoader
import logging
import asyncio
import os
import aiohttp
import json
from datetime import datetime
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


logger = logging.getLogger("agent")


async def delete_livekit_room(room_name: str):
    """Delete a LiveKit room using the API"""
    try:
        # Get LiveKit credentials from environment
        livekit_url = os.getenv("LIVEKIT_URL", "").replace(
            "ws://", "http://").replace("wss://", "https://")
        api_key = os.getenv("LIVEKIT_API_KEY")
        api_secret = os.getenv("LIVEKIT_API_SECRET")

        if not all([livekit_url, api_key, api_secret]):
            logger.warning(
                "LiveKit credentials not configured for room deletion")
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
        logger.warning(
            "LiveKit API client not available, using HTTP API directly")
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
                            logger.info(
                                f"🗑️ Successfully deleted room via API: {room_name}")
                        else:
                            logger.error(
                                f"Failed to delete room: {resp.status}")
                finally:
                    await session.close()
        except Exception as e:
            logger.error(f"Failed to delete room via HTTP API: {e}")
    except Exception as e:
        logger.error(f"Failed to delete room: {e}")


def prewarm(proc: JobProcess):
    """Fast prewarm function using cached models"""
    logger.info("[PREWARM] Fast prewarm: Using cached models")

    # Start background model loading if not already started
    if not model_preloader.is_ready():
        model_preloader.start_background_loading()

    # Load VAD model directly on main thread (required by Silero)
    if "vad_model" not in model_cache._models:
        logger.info("[PREWARM] Loading VAD model on main thread...")
        vad = ProviderFactory.create_vad()
        model_cache._models["vad_model"] = vad
        logger.info("[PREWARM] VAD model loaded and cached")
    else:
        vad = model_cache._models["vad_model"]
        logger.info("[PREWARM] Using cached VAD model")

    proc.userdata["vad"] = vad
    proc.userdata["embedding_model"] = model_cache.get_embedding_model()
    proc.userdata["qdrant_client"] = model_cache.get_qdrant_client()

    # Store service initialization info for later use
    proc.userdata["service_cache_ready"] = True

    # Log cache status
    stats = model_cache.get_cache_stats()
    logger.info(
        f"[PREWARM] Fast prewarm complete: {stats['cache_size']} models cached")

    # Optional: Wait briefly for background loading (non-blocking)
    if not model_preloader.is_ready():
        logger.info("[PREWARM] Background model loading in progress...")
        # Don't wait - let the session start immediately


async def entrypoint(ctx: JobContext):
    """Main entrypoint for the organized agent"""
    ctx.log_context_fields = {"room": ctx.room.name}
    print(f"Starting agent in room: {ctx.room.name}")

    # Load configuration (environment variables already loaded at module level)
    groq_config = ConfigLoader.get_groq_config()
    tts_config = ConfigLoader.get_tts_config()
    agent_config = ConfigLoader.get_agent_config()

    # Extract MAC address from room name and fetch device-specific prompt
    prompt_service = PromptService()
    room_name = ctx.room.name

    # Parse room name to extract MAC address (format: UUID_MAC)
    device_mac = None
    if '_' in room_name:
        parts = room_name.split('_')
        if len(parts) >= 2:
            # Last part is MAC without colons
            mac_part = parts[-1]
            # Reconstruct MAC with colons: 00163eacb538 → 00:16:3e:ac:b5:38
            if len(mac_part) == 12 and mac_part.isalnum():  # Valid MAC length and hex
                device_mac = ':'.join(mac_part[i:i+2] for i in range(0, 12, 2))
                logger.info(f"📱 Extracted MAC from room name: {device_mac}")

    # Initialize chat history service if MAC is available
    chat_history_service = None
    if device_mac:
        try:
            # Get Manager API configuration
            manager_api_url = os.getenv(
                "MANAGER_API_URL")
            manager_api_secret = os.getenv(
                "MANAGER_API_SECRET")

            # Create database helper and get agent_id
            db_helper = DatabaseHelper(manager_api_url, manager_api_secret)
            agent_id = await db_helper.get_agent_id(device_mac)

            # Create chat history service
            chat_history_service = ChatHistoryService(
                manager_api_url=manager_api_url,
                secret=manager_api_secret,
                device_mac=device_mac,
                session_id=room_name,
                agent_id=agent_id
            )

            # Start periodic sending
            chat_history_service.start_periodic_sending()
            logger.info(
                f"📝✅ Chat history service initialized for MAC: {device_mac}, Agent ID: {agent_id}")
            logger.info(
                f"📝📊 Service config: batch_size={chat_history_service.batch_size}, interval={chat_history_service.send_interval}s")

        except Exception as e:
            logger.error(f"📝❌ Failed to initialize chat history service: {e}")
            chat_history_service = None

    # Fetch device-specific prompt BEFORE creating assistant
    if device_mac:
        try:
            agent_prompt = await prompt_service.get_prompt(room_name, device_mac)
            logger.info(
                f"🎯 Using device-specific prompt for MAC: {device_mac} (length: {len(agent_prompt)} chars)")
            # Log first few lines of the fetched prompt for verification
            prompt_lines = agent_prompt.split('\n')[:5]  # First 5 lines
            logger.info(
                f"📝 Fetched prompt preview: {' | '.join(line.strip()[:50] for line in prompt_lines if line.strip())}")
        except Exception as e:
            logger.warning(
                f"Failed to fetch device prompt for MAC {device_mac}, using default: {e}")
            agent_prompt = ConfigLoader.get_default_prompt()
            logger.info(
                f"📄 Fallback to default prompt (length: {len(agent_prompt)} chars)")
    else:
        agent_prompt = ConfigLoader.get_default_prompt()
        logger.info(
            f"📄 Using default prompt - no MAC in room name '{room_name}' (length: {len(agent_prompt)} chars)")

    # NEW: Add emotion instructions to the prompt
    try:
        agent_prompt = prompt_service.add_emotion_instructions(agent_prompt)
        logger.info(f"✨ [EMOTION] Enhanced prompt with emotion instructions (new length: {len(agent_prompt)} chars)")
    except Exception as e:
        logger.warning(f"⚠️ [EMOTION] Failed to add emotion instructions: {e}")
        # Continue with original prompt if enhancement fails

    # Get VAD first as it's needed for STT
    vad = ctx.proc.userdata["vad"]

    # Create providers using factory
    llm = ProviderFactory.create_llm(groq_config)

    # Log LLM info for debugging (but don't hook into it - use conversation events instead)
    if chat_history_service:
        logger.debug(
            f"🧠 Using LLM type: {type(llm)} (will capture responses via conversation_item_added event)")

    stt = ProviderFactory.create_stt(
        groq_config, vad)  # Pass VAD to STT factory
    tts = ProviderFactory.create_tts(groq_config, tts_config)
    # Disable turn detection to avoid timeout issues
    turn_detection = ProviderFactory.create_turn_detection()

    # Set up voice AI pipeline
    session = AgentSession(
        llm=llm,
        stt=stt,
        tts=tts,
        turn_detection=turn_detection,  # Disabled to avoid timeout
        vad=vad,
        preemptive_generation=agent_config['preemptive_generation'],
        min_endpointing_delay=1.2,      # Increase from 500ms to 1.2s
        min_interruption_duration=1.0,   # Require longer pause
    )

    # Get preloaded models from prewarm
    preloaded_embedding_model = ctx.proc.userdata.get("embedding_model")
    preloaded_qdrant_client = ctx.proc.userdata.get("qdrant_client")

    # Try to use cached services first, otherwise create new ones
    music_service = model_cache.get_cached_service("music_service")
    story_service = model_cache.get_cached_service("story_service")

    services_from_cache = False

    if music_service and story_service:
        logger.info("[FAST] Using cached music and story services")
        services_from_cache = True
    else:
        logger.info("[INIT] Creating new music and story services...")
        # Create new services with preloaded models

        music_service = MusicService(preloaded_embedding_model, preloaded_qdrant_client)
        story_service = StoryService(preloaded_embedding_model, preloaded_qdrant_client)


    audio_player = ForegroundAudioPlayer()
    unified_audio_player = UnifiedAudioPlayer()

    # Create device control service and MCP executor
    device_control_service = DeviceControlService()
    mcp_executor = LiveKitMCPExecutor()
    logger.info("🎛️ Device control service and MCP executor created")

    # Create agent with dynamic prompt and inject services
    assistant = Assistant(instructions=agent_prompt)
    assistant.set_services(music_service, story_service,
                           audio_player, unified_audio_player, device_control_service, mcp_executor)

    # Log session info (responses will be captured via conversation_item_added event)
    if chat_history_service:
        logger.debug(
            "🎯 Chat history service ready - will capture via conversation_item_added and session.history")

    # Setup event handlers and pass assistant reference for abort handling
    ChatEventHandler.set_assistant(assistant)
    if chat_history_service:
        ChatEventHandler.set_chat_history_service(chat_history_service)
        logger.info(f"📝🔗 Chat history service connected to event handlers")
    else:
        logger.warning(
            f"📝⚠️ No chat history service available - events will not be captured")
    ChatEventHandler.setup_session_handlers(session, ctx)

    # Setup usage tracking
    usage_manager = UsageManager()

    async def log_usage():
        """Log usage summary on shutdown"""
        await usage_manager.log_usage()
        logger.info("Sent usage_summary via data channel")

    ctx.add_shutdown_callback(log_usage)

    # Initialize services only if not from cache
    if not services_from_cache:
        logger.info("[INIT] Initializing music and story services...")
        try:
            music_initialized = await music_service.initialize()
            story_initialized = await story_service.initialize()

            if music_initialized:
                # Cache the initialized service
                model_cache.cache_service("music_service", music_service)
                languages = await music_service.get_all_languages()
                logger.info(
                    f"[INIT] Music service initialized with {len(languages)} languages")
            else:
                logger.warning("[INIT] Music service initialization failed")

            if story_initialized:
                # Cache the initialized service
                model_cache.cache_service("story_service", story_service)
                categories = await story_service.get_all_categories()
                logger.info(
                    f"[INIT] Story service initialized with {len(categories)} categories")
            else:
                logger.warning("[INIT] Story service initialization failed")

        except Exception as e:
            logger.error(
                f"[INIT] Failed to initialize music/story services: {e}")
    else:
        # Services are from cache, just log their status
        try:
            if music_service and music_service.is_initialized:
                languages = await music_service.get_all_languages()
                logger.info(
                    f"[FAST] Music service ready with {len(languages)} languages")

            if story_service and story_service.is_initialized:
                categories = await story_service.get_all_categories()
                logger.info(
                    f"[FAST] Story service ready with {len(categories)} categories")
        except Exception as e:
            logger.warning(f"[FAST] Error checking cached services: {e}")

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

            # 1. Save session history to JSON file (using documented method)
            try:
                if session and hasattr(session, 'history') and session.history:
                    current_date = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"transcript_{ctx.room.name}_{current_date}.json"

                    logger.info(f"💾 Saving session history to: {filename}")

                    # Create transcripts directory if it doesn't exist
                    os.makedirs("transcripts", exist_ok=True)
                    filepath = os.path.join("transcripts", filename)

                    # Use the documented method to save conversation history
                    with open(filepath, 'w', encoding='utf-8') as f:
                        history_dict = session.history.to_dict()
                        json.dump(history_dict, f, indent=2,
                                  ensure_ascii=False)

                    message_count = len(history_dict.get('messages', []))
                    logger.info(
                        f"💾✅ Session history saved: {filepath} ({message_count} messages)")

                    # Log a sample of the conversation for verification
                    if message_count > 0:
                        messages = history_dict.get('messages', [])
                        # Last 3 messages
                        for i, msg in enumerate(messages[-3:]):
                            role = msg.get('role', 'unknown')
                            content = msg.get('content', '')
                            if isinstance(content, list):
                                # Handle content as list (some formats)
                                content = ' '.join(str(item)
                                                   for item in content)
                            logger.debug(
                                f"💾 Message {i}: {role} - '{str(content)[:50]}...'")

                else:
                    logger.warning(
                        f"💾⚠️ Session history not available or empty for backup")
            except Exception as e:
                logger.error(f"💾❌ Failed to save session history: {e}")
                import traceback
                logger.debug(f"💾❌ Traceback: {traceback.format_exc()}")

            # 2. Cleanup chat history service
            try:
                if chat_history_service:
                    logger.info("📝 Cleaning up chat history service")
                    await chat_history_service.cleanup()
            except Exception as e:
                logger.warning(f"📝❌ Chat history cleanup error: {e}")

            # 3. End the agent session (use aclose() method)
            try:
                if session and hasattr(session, 'aclose'):
                    logger.info("Ending agent session")
                    await session.aclose()
            except Exception as e:
                logger.warning(
                    f"Session close error (expected during shutdown): {e}")

            # 4. Stop audio services
            try:
                if audio_player:
                    await audio_player.stop()
                if unified_audio_player:
                    await unified_audio_player.stop()
            except Exception as e:
                logger.warning(f"Audio service stop error: {e}")

            # 5. Clean up music and story services (if cleanup methods exist)
            try:
                if music_service and hasattr(music_service, 'cleanup'):
                    await music_service.cleanup()
                if story_service and hasattr(story_service, 'cleanup'):
                    await story_service.cleanup()
            except Exception as e:
                logger.warning(f"Service cleanup error: {e}")

            # 6. Disconnect from room (gracefully handle already disconnected)
            try:
                if ctx.room and hasattr(ctx.room, 'disconnect'):
                    logger.info("Disconnecting from LiveKit room")
                    await ctx.room.disconnect()
            except Exception as e:
                logger.warning(
                    f"Room disconnect error (may already be disconnected): {e}")

            # 7. Request room deletion via API (requires admin token)
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
        logger.info(
            f"👤 Participant disconnected: {participant.identity}, remaining: {participant_count}")

        # If no participants left, cleanup room and session
        if participant_count == 0:
            logger.info("🔴 No participants remaining, initiating cleanup")
            asyncio.create_task(cleanup_room_and_session())

    @ctx.room.on("participant_connected")
    def on_participant_connected(participant: rtc.RemoteParticipant):
        nonlocal participant_count
        participant_count += 1
        logger.info(
            f"👤 Participant connected: {participant.identity}, total: {participant_count}")

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
