from src.providers.provider_factory import ProviderFactory
import logging
import asyncio
import os
import json
import yaml
from datetime import datetime
from dotenv import load_dotenv
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    cli,
    Agent,
    AgentSession,
)
from livekit import rtc

# Load environment variables first, before importing modules
# Load environment variables first, before importing modules
# load_dotenv(".env")

# HARDCODED CREDENTIALS (Temporary for debugging)
os.environ["LIVEKIT_URL"] = "wss://gemini-voice-agent-esksjwtq.livekit.cloud"
os.environ["LIVEKIT_API_KEY"] = "APIMa4zHysSjfXR"
os.environ["LIVEKIT_API_SECRET"] = "JfbdsoOvqaV4fWp54o5dmVCRiHs3mmzEuHsinN3Kne7A"

load_dotenv(".env", override=True) # Load other env vars, but keep hardcoded ones if we set them after?
# Actually, load_dotenv won't override existing env vars by default.
# But to be safe, let's set them AFTER load_dotenv to ensure they overwrite anything in .env
load_dotenv(".env")
os.environ["LIVEKIT_URL"] = "wss://gemini-voice-agent-esksjwtq.livekit.cloud"
os.environ["LIVEKIT_API_KEY"] = "APIMa4zHysSjfXR"
os.environ["LIVEKIT_API_SECRET"] = "JfbdsoOvqaV4fWp54o5dmVCRiHs3mmzEuHsinN3Kne7A"

# Import our organized modules


logger = logging.getLogger("agent")

# Load configuration from config.yaml
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.yaml")
with open(CONFIG_PATH, 'r') as f:
    config = yaml.safe_load(f)

# Extract Gemini Realtime configuration
GEMINI_CONFIG = config.get('gemini_realtime', {})
GEMINI_MODEL = GEMINI_CONFIG.get('model', 'gemini-2.0-flash-exp')
GEMINI_VOICE = GEMINI_CONFIG.get('voice', 'Zephyr')
GEMINI_TEMPERATURE = GEMINI_CONFIG.get('temperature', 0.6)
GEMINI_PROMPT = GEMINI_CONFIG.get('prompt', 'You are a helpful voice assistant.')


async def entrypoint(ctx: JobContext):
    """Minimal Gemini Realtime entrypoint for MQTT toy integration"""

    logger.info(f"Starting agent in room: {ctx.room.name}")

    # Extract MAC address from room name (format: UUID_MAC)
    device_mac = None
    room_name = ctx.room.name
    if '_' in room_name:
        parts = room_name.split('_')
        if len(parts) >= 2:
            mac_part = parts[-1]
            if len(mac_part) == 12 and mac_part.isalnum():
                device_mac = ':'.join(mac_part[i:i+2] for i in range(0, 12, 2))
                logger.info(f"📱 Device MAC: {device_mac}")

    # Use prompt from config.yaml
    agent_prompt = GEMINI_PROMPT
    logger.info(f"🎭 Using voice: {GEMINI_VOICE}")

    # Define Agent (instructions go here, NOT in model!)
    class VoiceAssistant(Agent):
        def __init__(self):
            super().__init__(instructions=agent_prompt)

    # Create Gemini Realtime model using config.yaml settings
    logger.info(f"🎙️ Initializing Gemini Realtime (model: {GEMINI_MODEL}, voice: {GEMINI_VOICE})...")
    from livekit.plugins import google

    session = AgentSession(
        llm=google.realtime.RealtimeModel(
            model=GEMINI_MODEL,
            voice=GEMINI_VOICE,
            temperature=GEMINI_TEMPERATURE,
        ),
    )

    # ============================================================================
    # STATE MANAGEMENT
    # ============================================================================

    current_state = "idle"

    async def emit_agent_state(new_state: str):
        """Emit agent state via data channel for MQTT gateway"""
        nonlocal current_state
        try:
            if new_state == current_state:
                return

            old_state = current_state
            current_state = new_state

            payload = json.dumps({
                "type": "agent_state_changed",
                "data": {
                    "old_state": old_state,
                    "new_state": new_state
                }
            })

            await ctx.room.local_participant.publish_data(
                payload.encode('utf-8'),
                reliable=True
            )
            logger.info(f"📊 State: {old_state} → {new_state}")
        except Exception as e:
            logger.error(f"Failed to emit state: {e}")

    # Map Agent events to states
    @session.on("agent_speech_started")
    def on_agent_speech_started(ev):
        logger.info(f"🔊 EVENT: agent_speech_started - {ev}")
        asyncio.create_task(emit_agent_state("speaking"))

    @session.on("agent_speech_stopped")
    def on_agent_speech_stopped(ev):
        logger.info(f"🔇 EVENT: agent_speech_stopped - {ev}")
        asyncio.create_task(emit_agent_state("listening"))

    @session.on("user_speech_started")
    def on_user_speech_started(ev):
        logger.info(f"🎤 EVENT: user_speech_started - {ev}")
        asyncio.create_task(emit_agent_state("listening"))

    @session.on("user_speech_stopped")
    def on_user_speech_stopped(ev):
        logger.info(f"🤔 EVENT: user_speech_stopped - transitioning to speaking immediately")
        asyncio.create_task(emit_agent_state("speaking"))

    # ============================================================================
    # PARTICIPANT TRACKING & CLEANUP
    # ============================================================================

    participant_count = len(ctx.room.remote_participants)
    cleanup_completed = False

    async def cleanup_session():
        """Minimal cleanup on disconnect"""
        nonlocal cleanup_completed
        if cleanup_completed:
            return
        cleanup_completed = True

        logger.info("🔴 Cleaning up session...")

        try:
            if ctx.room and hasattr(ctx.room, 'disconnect'):
                await ctx.room.disconnect()
        except Exception as e:
            logger.warning(f"Disconnect error: {e}")

        logger.info("✅ Cleanup complete")

    @ctx.room.on("participant_disconnected")
    def on_participant_disconnected(participant: rtc.RemoteParticipant):
        nonlocal participant_count
        participant_count -= 1
        logger.info(f"👤 Participant left: {participant.identity}, remaining: {participant_count}")
        if participant_count == 0:
            asyncio.create_task(cleanup_session())

    @ctx.room.on("participant_connected")
    def on_participant_connected(participant: rtc.RemoteParticipant):
        nonlocal participant_count
        participant_count += 1
        logger.info(f"👤 Participant joined: {participant.identity}, total: {participant_count}")

    @ctx.room.on("disconnected")
    def on_room_disconnected():
        logger.info("🔴 Room disconnected")
        asyncio.create_task(cleanup_session())

    # ============================================================================
    # DATA CHANNEL HANDLERS
    # ============================================================================

    @ctx.room.on("data_received")
    def on_data_received(packet: rtc.DataPacket):
        try:
            payload = packet.data.decode('utf-8')
            data = json.loads(payload)
            logger.debug(f"📨 Received: {data.get('type')}")

            if data.get("type") in ["start_greeting", "agent_ready"]:
                logger.info(f"👋 Greeting request received")
                asyncio.create_task(trigger_greeting())
            elif data.get("type") == "end_prompt":
                logger.info(f"👋 End prompt received, will disconnect naturally")
                # Let the gateway handle the goodbye, we just acknowledge

        except Exception as e:
            logger.warning(f"Failed to handle data: {e}")

    async def trigger_greeting():
        """Generate initial greeting"""
        await asyncio.sleep(2.0)  # Brief delay for session stability
        try:
            logger.info("👋 Generating greeting...")
            logger.info(f"🔍 Session state before greeting: {session}")

            # Try to generate greeting
            result = await session.generate_reply(
                instructions="Say hello and introduce yourself as a funny goofy friend."
            )

            logger.info(f"🔍 Generate reply result: {result}")
            logger.info("✅ Greeting sent")
        except Exception as e:
            logger.error(f"❌ Greeting error: {e}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")

    # ============================================================================
    # START SESSION
    # ============================================================================

    # Connect to room first
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # Wait for a participant to join (critical for Gemini Realtime!)
    participant = await ctx.wait_for_participant()
    logger.info(f"👤 Participant joined: {participant.identity}")

    # Start Gemini session with the room and participant
    await session.start(
        room=ctx.room,
        agent=VoiceAssistant(),
    )

    logger.info("✅ Gemini Realtime agent is LIVE!")


if __name__ == "__main__":
    cli.run_app(WorkerOptions(
        entrypoint_fnc=entrypoint,
        # Use default prewarm, no custom function needed
    ))
