import json
import asyncio
import logging
from livekit.agents import (
    AgentFalseInterruptionEvent,
    AgentStateChangedEvent,
    UserInputTranscribedEvent,
    SpeechCreatedEvent,
    NOT_GIVEN,
)
from ..utils.audio_state_manager import audio_state_manager

logger = logging.getLogger("chat_logger")

class ChatEventHandler:
    """Event handler for chat logging and data channel communication"""

    # Store assistant reference for abort handling
    _assistant_instance = None

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

        @session.on("speech_created")
        def _on_speech_created(ev: SpeechCreatedEvent):
            # logger.info(f"Speech created with id: {ev.speech_id}, duration: {ev.duration_ms}ms")
            payload = json.dumps({
                "type": "speech_created",
                "data": ev.dict()
            })
            asyncio.create_task(ctx.room.local_participant.publish_data(payload.encode("utf-8"), reliable=True))
            logger.info("Sent speech_created via data channel")

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

                # Handle cleanup request from MQTT gateway
                elif message.get('type') == 'cleanup_request':
                    logger.info("🧹 Processing cleanup request from MQTT gateway")
                    # This will trigger our participant disconnect logic
                    # The room cleanup will be handled by the event handlers in main.py

            except Exception as e:
                logger.error(f"Error processing data channel message: {e}")