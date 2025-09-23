import json
import asyncio
import logging
import aiohttp
import time
from livekit.agents import (
    AgentFalseInterruptionEvent,
    AgentStateChangedEvent,
    UserInputTranscribedEvent,
    SpeechCreatedEvent,
    NOT_GIVEN,
)
from ..utils.audio_state_manager import audio_state_manager
from ..config.config_loader import ConfigLoader
from .report_handle import enqueue_user_report, enqueue_agent_report

logger = logging.getLogger("chat_logger")

class ChatEventHandler:
    """Event handler for chat logging and data channel communication"""

    # Store assistant reference for abort handling
    _assistant_instance = None

    # Manager API configuration
    _manager_api_url = "http://localhost:8002"
    _agent_id = None  # Will be set dynamically from session context

    @staticmethod
    def set_assistant(assistant):
        """Set the assistant instance for abort handling"""
        ChatEventHandler._assistant_instance = assistant

    @staticmethod
    async def _handle_abort_playback(session, ctx):
        """Handle abort playback signal from MQTT gateway"""
        try:
            if ChatEventHandler._assistant_instance and hasattr(ChatEventHandler._assistant_instance, 'stop_audio'):
                # Call the existing stop_audio function
                result = await ChatEventHandler._assistant_instance.stop_audio(ctx)
                logger.info(f"🛑 Abort signal processed: {result}")
            else:
                logger.warning("🛑 Could not access assistant's stop_audio method for abort signal")
        except Exception as e:
            logger.error(f"🛑 Error handling abort playback: {e}")

    @staticmethod
    def setup_session_handlers(session, ctx):
        """Setup all event handlers for the agent session"""

        @session.on("agent_false_interruption")
        def _on_agent_false_interruption(ev: AgentFalseInterruptionEvent):
            logger.info("False positive interruption, resuming")
            session.generate_reply(instructions=ev.extra_instructions or NOT_GIVEN)
            payload = json.dumps({
                "type": "agent_false_interruption",
                "data": ev.dict()
            })
            asyncio.create_task(ctx.room.local_participant.publish_data(payload.encode("utf-8"), reliable=True))
            logger.info("Sent agent_false_interruption via data channel")

        @session.on("agent_state_changed")
        def _on_agent_state_changed(ev: AgentStateChangedEvent):
            logger.info(f"Agent state changed: {ev}")

            # Check if this state change should be suppressed due to music playback
            should_suppress = audio_state_manager.should_suppress_agent_state_change(
                ev.old_state, ev.new_state
            )

            if should_suppress:
                logger.info(f"🎵 Suppressing agent state change from {ev.old_state} to {ev.new_state} - music is playing")
                return

            payload = json.dumps({
                "type": "agent_state_changed",
                "data": ev.dict()
            })
            asyncio.create_task(ctx.room.local_participant.publish_data(payload.encode("utf-8"), reliable=True))
            logger.info("Sent agent_state_changed via data channel")

        @session.on("user_input_transcribed")
        def _on_user_input_transcribed(ev: UserInputTranscribedEvent):
            logger.info(f"User said: {ev}")
            payload = json.dumps({
                "type": "user_input_transcribed",
                "data": ev.dict()
            })
            asyncio.create_task(ctx.room.local_participant.publish_data(payload.encode("utf-8"), reliable=True))
            logger.info("Sent user_input_transcribed via data channel")

            # Send real-time chat data to manager-api
            chat_data = ChatEventHandler._create_chat_data(
                "user_input_transcribed",
                ev.transcript,
                ctx.room.name,
                ctx,
                None,
                session  # Pass session to update mac_address
            )
            asyncio.create_task(ChatEventHandler._send_chat_to_manager_api(chat_data))

            enqueue_user_report(session, ev.transcript)

        @session.on("speech_created")
        def _on_speech_created(ev: SpeechCreatedEvent):
            # logger.info(f"Speech created with id: {ev.speech_id}, duration: {ev.duration_ms}ms")
            payload = json.dumps({
                "type": "speech_created",
                "data": ev.dict()
            })
            asyncio.create_task(ctx.room.local_participant.publish_data(payload.encode("utf-8"), reliable=True))
            logger.info("Sent speech_created via data channel")

            # Extract actual speech content if available
            speech_text = None  # Start with None to detect if we found real text

            try:
                # Debug the event structure
                logger.debug(f"🔍 Speech event attributes: {dir(ev)}")

                # Try multiple ways to get the actual speech text
                if hasattr(ev, 'speech_handle') and ev.speech_handle:
                    speech_handle = ev.speech_handle
                    logger.debug(f"🔍 Speech handle attributes: {dir(speech_handle)}")

                    # Try different text attributes
                    for attr in ['text', '_text', 'content', 'message']:
                        if hasattr(speech_handle, attr):
                            text_value = getattr(speech_handle, attr)
                            if text_value and isinstance(text_value, str) and text_value.strip():
                                speech_text = text_value.strip()
                                logger.info(f"✅ Found speech text via {attr}: {speech_text[:50]}...")
                                break

                # Try to get text directly from the event
                if not speech_text:
                    for attr in ['text', 'content', 'message', 'transcript']:
                        if hasattr(ev, attr):
                            text_value = getattr(ev, attr)
                            if text_value and isinstance(text_value, str) and text_value.strip():
                                speech_text = text_value.strip()
                                logger.info(f"✅ Found speech text via event.{attr}: {speech_text[:50]}...")
                                break

                # Skip logging if this is music playback (empty text from session.say)
                if hasattr(ev, 'source') and ev.source != 'generate_reply':
                    logger.debug(f"Skipping non-LLM speech event: {ev.source}")
                    return

            except Exception as e:
                logger.debug(f"Could not extract speech text: {e}")

            # Use default if no text was found
            if not speech_text:
                speech_text = "Agent response"
                logger.warning(f"⚠️ No speech text found, using default: {speech_text}")

            # Send real-time chat data to manager-api only for actual LLM responses
            speech_id = getattr(ev, 'id', None) or getattr(ev, 'speech_id', None)
            duration_ms = getattr(ev, 'duration_ms', None)

            additional_data = {}
            if speech_id:
                additional_data["speechId"] = speech_id
            if duration_ms:
                additional_data["durationMs"] = duration_ms

            chat_data = ChatEventHandler._create_chat_data(
                "speech_created",
                speech_text,  # Use extracted text or default
                ctx.room.name,
                ctx,
                additional_data,
                session  # Pass session to update mac_address
            )
            asyncio.create_task(ChatEventHandler._send_chat_to_manager_api(chat_data))

            if speech_text:
                enqueue_agent_report(session, speech_text)

        # Add data channel message handler for abort signals
        @ctx.room.on("data_received")
        def _on_data_received(data_packet):
            try:
                # Decode the data
                message_str = data_packet.data.decode('utf-8')
                message = json.loads(message_str)

                logger.info(f"📨 Received data channel message: {message.get('type', 'unknown')}")

                # Handle abort playback message from MQTT gateway
                if message.get('type') == 'abort_playback':
                    logger.info("🛑 Processing abort playback signal from MQTT gateway")
                    # Create task for immediate execution (stop() method is now aggressive)
                    asyncio.create_task(ChatEventHandler._handle_abort_playback(session, ctx))

                # Handle agent ready message from MQTT gateway
                elif message.get('type') == 'agent_ready':
                    logger.info("🤖 Processing agent ready signal from MQTT gateway")
                    # Trigger initial greeting from the agent
                    greeting_instructions = "Say a brief, friendly hello to greet the user and let them know you're ready to chat. Keep it short and welcoming."
                    session.generate_reply(instructions=greeting_instructions)

            except Exception as e:
                logger.error(f"Error processing data channel message: {e}")

    @staticmethod
    async def _send_chat_to_manager_api(chat_data):
        """Send real-time chat data to manager-api for MySQL storage"""
        try:
            # Get manager-api configuration
            config = ConfigLoader._load_yaml_config()
            manager_api_config = config.get('manager_api', {})
            manager_api_url = manager_api_config.get('url', 'http://localhost:8002')

            # Securely fetch server secret from database
            manager_api_secret = ConfigLoader.get_manager_api_secret()

            # Get agent_id from chat_data or use default
            agent_id = chat_data.get('agent_id', ChatEventHandler._agent_id or 'default-agent')
            url = f"{manager_api_url}/toy/config/livekit/chat/store/{agent_id}"

            # Prepare headers with authentication
            headers = {
                'Content-Type': 'application/json'
            }

            if manager_api_secret:
                headers['Authorization'] = f'Bearer {manager_api_secret}'
                logger.debug(f"🔑 Using authentication for manager-api request")
            else:
                logger.warning(f"⚠️ No manager-api secret found in database")

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=[chat_data], headers=headers, timeout=5) as response:
                    response_text = await response.text()
                    logger.info(f"📡 Manager-api response status: {response.status}")
                    logger.debug(f"📡 Manager-api response body: {response_text}")

                    if response.status == 200:
                        logger.info(f"✅ Real-time chat data sent to manager-api successfully")
                    else:
                        logger.error(f"❌ Manager-api returned status {response.status}: {response_text}")
                        logger.error(f"🔍 Request URL: {url}")
                        logger.error(f"🔍 Request headers: {headers}")
                        logger.error(f"🔍 Request data: {[chat_data]}")

        except Exception as e:
            logger.error(f"❌ Failed to send chat data to manager-api: {e}")

    @staticmethod
    def _create_chat_data(event_type, content, session_id, ctx=None, additional_data=None, session=None):
        """Create chat data structure for manager-api"""
        # Ensure session_id is not None or empty
        if not session_id:
            import uuid
            session_id = f"livekit-session-{uuid.uuid4().hex[:8]}"

        # Extract MAC address from participant identity (if available)
        mac_address = "unknown-device"
        agent_id = ChatEventHandler._agent_id or "default-agent"

        logger.debug(f"🔍 Creating chat data for event: {event_type}, session_id: {session_id}")

        if ctx and hasattr(ctx, 'room') and ctx.room:
            logger.debug(f"🔍 Room found: {ctx.room.name}, participants: {len(ctx.room.remote_participants)}")

            # Try to get MAC address from participant identity
            for participant in ctx.room.remote_participants.values():
                logger.debug(f"🔍 Checking participant: {participant.identity}")
                if participant.identity and ":" in participant.identity:
                    mac_address = participant.identity
                    logger.info(f"✅ Found MAC address from participant: {mac_address}")
                    # Update the session's mac_address for report_handle to use
                    if session and hasattr(session, 'mac_address'):
                        session.mac_address = mac_address
                        logger.debug(f"📝 Updated session.mac_address to: {mac_address}")
                    break

            # Also check all participants (including local)
            if mac_address == "unknown-device":
                all_participants = list(ctx.room.remote_participants.values())
                if hasattr(ctx.room, 'local_participant') and ctx.room.local_participant:
                    all_participants.append(ctx.room.local_participant)

                for participant in all_participants:
                    if participant.identity and ":" in participant.identity:
                        mac_address = participant.identity
                        logger.info(f"✅ Found MAC address from participant (all): {mac_address}")
                        # Update the session's mac_address for report_handle to use
                        if session and hasattr(session, 'mac_address'):
                            session.mac_address = mac_address
                            logger.debug(f"📝 Updated session.mac_address to: {mac_address}")
                        break

            # Use the session_id as passed in (which should be ctx.room.name)
            # The room.name in LiveKit should represent the agent_id (each session has unique agent_id)
            if session_id and len(session_id) >= 32:  # UUID-like format
                agent_id = session_id
                logger.debug(f"🔍 Using session_id as agent_id: {agent_id}")
        else:
            logger.warning("🔍 No room context available for data extraction")

        result_data = {
            "session_id": session_id,
            "type": event_type,
            "content": content,
            "speaker": "user" if event_type == "user_input_transcribed" else "agent",
            "timestamp": int(time.time() * 1000),
            "agent_id": agent_id,
            "mac_address": mac_address,
            **(additional_data or {})
        }

        logger.info(f"📝 Created chat data: session_id={session_id}, agent_id={agent_id}, mac_address={mac_address}")
        return result_data