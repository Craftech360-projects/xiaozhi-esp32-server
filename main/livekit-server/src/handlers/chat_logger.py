import json
import asyncio
import logging
import aiohttp
import time
import threading
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from livekit.agents import (
    AgentFalseInterruptionEvent,
    AgentStateChangedEvent,
    UserInputTranscribedEvent,
    SpeechCreatedEvent,
    ChatMessageEvent,
    FunctionCallOutputEvent,
    NOT_GIVEN,
)
from ..utils.audio_state_manager import audio_state_manager
from ..config.config_loader import ConfigLoader
from .report_handle import enqueue_user_report, enqueue_agent_report

logger = logging.getLogger("chat_logger")

@dataclass
class ChatMessage:
    """Thread-safe chat message with proper correlation"""
    user_input: str
    agent_response: str
    timestamp: int
    user_input_hash: int
    correlation_id: str = field(default_factory=lambda: str(int(time.time() * 1000000)))

class ChatSynchronizer:
    """Thread-safe chat message synchronization manager"""

    def __init__(self):
        self._lock = threading.RLock()  # Reentrant lock for nested operations
        self._pending_inputs: Dict[str, str] = {}  # correlation_id -> user_input
        self._pending_responses: Dict[str, str] = {}  # correlation_id -> agent_response
        self._completed_messages: List[ChatMessage] = []
        self._current_correlation_id: Optional[str] = None
        self._message_sequence = 0

    def register_user_input(self, user_input: str) -> str:
        """Register user input and return correlation_id for response matching"""
        with self._lock:
            correlation_id = f"{int(time.time() * 1000000)}_{self._message_sequence}"
            self._message_sequence += 1
            self._pending_inputs[correlation_id] = user_input.strip()
            self._current_correlation_id = correlation_id
            logger.info(f"🎯 SYNC: Registered user input with ID {correlation_id}: '{user_input[:50]}...'")
            return correlation_id

    def register_agent_response(self, response: str, correlation_id: Optional[str] = None) -> bool:
        """Register agent response and attempt correlation with user input"""
        with self._lock:
            # Use current correlation ID if none provided
            if not correlation_id:
                correlation_id = self._current_correlation_id

            if not correlation_id:
                logger.warning(f"⚠️ SYNC: No correlation ID for response: '{response[:50]}...'")
                return False

            # Store response
            self._pending_responses[correlation_id] = response.strip()

            # Try to create complete message if both input and response exist
            if correlation_id in self._pending_inputs:
                user_input = self._pending_inputs[correlation_id]
                chat_message = ChatMessage(
                    user_input=user_input,
                    agent_response=response.strip(),
                    timestamp=int(time.time() * 1000),
                    user_input_hash=hash(user_input),
                    correlation_id=correlation_id
                )

                # Add to completed messages and clean up pending
                self._completed_messages.append(chat_message)
                del self._pending_inputs[correlation_id]
                del self._pending_responses[correlation_id]

                logger.info(f"✅ SYNC: Created complete message pair {correlation_id}")
                logger.info(f"   Q: '{user_input[:50]}...'")
                logger.info(f"   A: '{response[:50]}...'")
                return True
            else:
                logger.info(f"🔄 SYNC: Stored response for {correlation_id}, waiting for input")
                return False

    def get_latest_response(self) -> Optional[str]:
        """Get the latest agent response for speech synthesis"""
        with self._lock:
            if self._completed_messages:
                return self._completed_messages[-1].agent_response
            # Fallback to pending responses if no completed messages
            elif self._pending_responses:
                latest_id = max(self._pending_responses.keys())
                return self._pending_responses[latest_id]
            return None

    def get_response_for_speech(self) -> Optional[ChatMessage]:
        """Get and consume the next available response for speech synthesis"""
        with self._lock:
            # Prioritize completed messages first
            if self._completed_messages:
                message = self._completed_messages.pop(0)  # FIFO
                logger.info(f"🎙️ SYNC: Serving completed message: '{message.agent_response[:50]}...'")
                return message

            return None

    def cleanup_old_entries(self, max_age_seconds: int = 300):  # 5 minutes
        """Clean up old pending entries to prevent memory leaks"""
        with self._lock:
            current_time = int(time.time() * 1000000)
            cutoff_time = current_time - (max_age_seconds * 1000000)

            # Clean pending inputs
            old_input_ids = [cid for cid in self._pending_inputs.keys() if int(cid.split('_')[0]) < cutoff_time]
            for old_id in old_input_ids:
                del self._pending_inputs[old_id]

            # Clean pending responses
            old_response_ids = [cid for cid in self._pending_responses.keys() if int(cid.split('_')[0]) < cutoff_time]
            for old_id in old_response_ids:
                del self._pending_responses[old_id]

            # Limit completed messages history
            if len(self._completed_messages) > 100:
                self._completed_messages = self._completed_messages[-50:]  # Keep last 50

            if old_input_ids or old_response_ids:
                logger.info(f"🧹 SYNC: Cleaned {len(old_input_ids)} old inputs, {len(old_response_ids)} old responses")


class ChatEventHandler:
    """Event handler for chat logging and data channel communication"""

    # Store assistant reference for abort handling
    _assistant_instance = None

    # NEW: Thread-safe chat synchronization
    _chat_sync = ChatSynchronizer()

    # Keep existing variables for backward compatibility
    _last_agent_response = None  # Deprecated but maintained for compatibility
    _pending_responses = {}  # Deprecated but maintained for compatibility
    _current_user_input = None  # Deprecated but maintained for compatibility
    _response_queue = []  # Deprecated but maintained for compatibility
    _turn_detector_context = {}  # Still used for turn detection context

    # Manager API configuration
    _manager_api_url = "http://localhost:8002"
    _agent_id = None  # Will be set dynamically from session context

    @staticmethod
    def set_assistant(assistant):
        """Set the assistant instance for abort handling"""
        ChatEventHandler._assistant_instance = assistant

    @staticmethod
    def set_last_response(response_text: str):
        """Store the last agent response for logging - UPDATED with sync management"""
        # NEW: Use thread-safe synchronization system
        ChatEventHandler._chat_sync.register_agent_response(response_text)

        # Maintain backward compatibility with existing code
        ChatEventHandler._last_agent_response = response_text
        logger.debug(f"Stored agent response for logging: {response_text[:100]}...")

        # Clear old queue and add latest response (backward compatibility)
        ChatEventHandler._response_queue.clear()
        ChatEventHandler._response_queue.append(response_text)
        logger.info(f"✅ RESPONSE SET (CLEARED QUEUE): {response_text[:50]}...")

        # Maintain old hash correlation for compatibility
        if ChatEventHandler._current_user_input:
            user_hash = hash(ChatEventHandler._current_user_input)
            ChatEventHandler._pending_responses[user_hash] = response_text
            logger.info(f"🔗 CORRELATED: Q(hash {user_hash}): '{ChatEventHandler._current_user_input[:30]}...' -> A: '{response_text[:30]}...'")

        # Cleanup old hash-based responses
        if len(ChatEventHandler._pending_responses) > 3:
            oldest_hash = min(ChatEventHandler._pending_responses.keys())
            del ChatEventHandler._pending_responses[oldest_hash]

        # Perform periodic cleanup of sync system
        ChatEventHandler._chat_sync.cleanup_old_entries()

    @staticmethod
    def _extract_turn_context(log_data):
        """Extract conversation context from turn detector logs and sync Q&A properly"""
        try:
            input_text = log_data.get('input', '')
            eou_probability = log_data.get('eou_probability', 0)

            if input_text and '<|im_start|>' in input_text:
                # Parse the conversation format: <|im_start|><|assistant|>...text...<|im_end|><|im_start|><|user|>...text...
                logger.debug(f"🔍 TURN CONTEXT: Parsing input: {input_text[:100]}...")

                # Split by tokens to extract conversation turns
                parts = input_text.split('<|im_start|>')
                conversation = []

                for part in parts[1:]:  # Skip first empty part
                    if '<|assistant|>' in part:
                        content = part.replace('<|assistant|>', '').replace('<|im_end|>', '').strip()
                        if content:
                            conversation.append({"role": "assistant", "content": content})
                    elif '<|user|>' in part:
                        content = part.replace('<|user|>', '').replace('<|im_end|>', '').strip()
                        if content:
                            conversation.append({"role": "user", "content": content})

                # Store the conversation context
                ChatEventHandler._turn_detector_context = {
                    "conversation": conversation,
                    "eou_probability": eou_probability,
                    "timestamp": int(time.time() * 1000)
                }

                logger.info(f"📝 TURN CONTEXT: Updated with {len(conversation)} turns, EOU: {eou_probability}")

                # Use turn detector context for perfect Q&A synchronization
                ChatEventHandler._sync_from_turn_detector(conversation)

        except Exception as e:
            logger.warning(f"Error parsing turn detector context: {e}")

    @staticmethod
    def _sync_from_turn_detector(conversation):
        """Use turn detector conversation history for perfect Q&A sync - UPDATED"""
        try:
            if len(conversation) >= 2:
                # Get the latest user question from conversation
                latest_user_turn = None
                latest_assistant_turn = None

                # Find the latest user and assistant turns
                for turn in reversed(conversation):
                    if turn['role'] == 'user' and not latest_user_turn:
                        latest_user_turn = turn['content']
                    elif turn['role'] == 'assistant' and not latest_assistant_turn:
                        latest_assistant_turn = turn['content']

                if latest_user_turn and latest_assistant_turn:
                    # NEW: Use proper synchronization system
                    # Register both input and response with turn detector context
                    correlation_id = ChatEventHandler._chat_sync.register_user_input(latest_user_turn)
                    ChatEventHandler._chat_sync.register_agent_response(latest_assistant_turn, correlation_id)

                    # Maintain backward compatibility: clear old queue and add response
                    ChatEventHandler._response_queue.clear()
                    ChatEventHandler._response_queue.append(latest_assistant_turn)
                    logger.info(f"🎯 PERFECT SYNC: Q: '{latest_user_turn[:50]}...' -> A: '{latest_assistant_turn[:50]}...'")

        except Exception as e:
            logger.warning(f"Error in turn detector sync: {e}")

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
            logger.info(f"🔄 Agent state changed: {ev.old_state} → {ev.new_state}")

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
            logger.info("📡 Sent agent_state_changed via data channel")

        @session.on("user_input_transcribed")
        def _on_user_input_transcribed(ev: UserInputTranscribedEvent):
            logger.info(f"🎤 User said: {ev}")
            logger.info(f"🔍 Turn detection - User input is_final: {ev.is_final}")

            # NEW: Register user input with synchronization system
            question_text = ev.transcript.strip()
            correlation_id = ChatEventHandler._chat_sync.register_user_input(question_text)

            # Maintain backward compatibility
            ChatEventHandler._current_user_input = question_text
            logger.info(f"📝 USER INPUT: '{question_text}' (ID: {correlation_id})")

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

        @session.on("function_call_output")
        def _on_function_call_output(ev: FunctionCallOutputEvent):
            logger.debug(f"Function call output: {ev}")
            # This might contain LLM responses if functions return text
            if hasattr(ev, 'output') and ev.output:
                ChatEventHandler.set_last_response(ev.output)
                logger.info(f"Captured function output: {ev.output[:100]}...")

        # Try to capture chat messages that might contain LLM responses
        @session.on("chat_message")
        def _on_chat_message(ev: ChatMessageEvent):
            logger.debug(f"Chat message: {ev}")
            if hasattr(ev, 'message') and ev.message:
                # Check if this is an agent message
                if hasattr(ev, 'role') and ev.role == 'assistant':
                    ChatEventHandler.set_last_response(ev.message)
                    logger.info(f"Captured assistant message: {ev.message[:100]}...")

        @session.on("speech_created")
        def _on_speech_created(ev: SpeechCreatedEvent):
            # Send event via data channel
            payload = json.dumps({
                "type": "speech_created",
                "data": ev.dict()
            })
            asyncio.create_task(ctx.room.local_participant.publish_data(payload.encode("utf-8"), reliable=True))
            logger.info("Sent speech_created via data channel")

            # NEW: Use thread-safe synchronized response retrieval
            speech_text = None
            chat_message = None

            try:
                # Primary: Use new synchronization system
                chat_message = ChatEventHandler._chat_sync.get_response_for_speech()
                if chat_message:
                    speech_text = chat_message.agent_response
                    logger.info(f"✅ SYNC SERVED: {speech_text[:50]}...")
                    # Enqueue both user and agent reports
                    enqueue_user_report(session, chat_message.user_input)
                    enqueue_agent_report(session, speech_text)
                else:
                    # Fallback 1: Use legacy response queue (backward compatibility)
                    if ChatEventHandler._response_queue:
                        speech_text = ChatEventHandler._response_queue.pop(0)
                        logger.info(f"✅ QUEUE SERVED: {speech_text[:50]}...")
                        enqueue_agent_report(session, speech_text)

                    # Fallback 2: Try legacy hash correlation (preserves original functionality)
                    elif ChatEventHandler._pending_responses:
                        latest_hash = max(ChatEventHandler._pending_responses.keys())
                        speech_text = ChatEventHandler._pending_responses.get(latest_hash)
                        if speech_text:
                            logger.info(f"⚠️ HASH SERVED: Using correlated response for hash {latest_hash}: {speech_text[:50]}...")
                            del ChatEventHandler._pending_responses[latest_hash]
                            enqueue_agent_report(session, speech_text)
            except Exception as e:
                logger.warning(f"🔄 Error in response retrieval logic: {e}")

            # Final fallback to global last response (preserves original functionality)
            if not speech_text:
                speech_text = ChatEventHandler._last_agent_response
                if speech_text:
                    logger.info(f"⚠️ GLOBAL FALLBACK: Using last response: {speech_text[:50]}...")
                    enqueue_agent_report(session, speech_text)

            if not speech_text:
                speech_text = "[Audio response generated]"
                logger.warning("⚠️ No LLM response captured, using placeholder")

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

        # Hook into turn detector logs to extract conversation context
        original_logger = logging.getLogger("livekit.plugins.turn_detector")
        original_debug = original_logger.debug

        def patched_debug(msg, *args, **kwargs):
            # Call original debug first
            original_debug(msg, *args, **kwargs)

            # Extract turn detector context for chat sync - be more aggressive about capturing
            try:
                if "eou prediction" in str(msg) or "prediction" in str(msg) or "input" in str(kwargs):
                    logger.info(f"🔍 TURN DEBUG: msg='{msg}', kwargs={kwargs}")
                    ChatEventHandler._extract_turn_context(kwargs)
            except Exception as e:
                logger.warning(f"Failed to extract turn context: {e}")

        original_logger.debug = patched_debug
        logger.info("✅ Turn detector context extraction enabled")

        # Try to add turn detection event handlers with generic approach
        try:
            @session.on("turn_started")
            def _on_turn_started(ev):
                logger.info(f"🎯 TURN DETECTION: Turn started - {ev}")
        except:
            logger.debug("turn_started event not available")

        try:
            @session.on("turn_ended")
            def _on_turn_ended(ev):
                logger.info(f"🎯 TURN DETECTION: Turn ended - {ev}")
        except:
            logger.debug("turn_ended event not available")

        try:
            @session.on("user_speech_started")
            def _on_user_speech_started(ev):
                logger.info(f"🎯 TURN DETECTION: User speech started - {ev}")
        except:
            logger.debug("user_speech_started event not available")

        try:
            @session.on("user_speech_ended")
            def _on_user_speech_ended(ev):
                logger.info(f"🎯 TURN DETECTION: User speech ended - {ev}")
        except:
            logger.debug("user_speech_ended event not available")

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