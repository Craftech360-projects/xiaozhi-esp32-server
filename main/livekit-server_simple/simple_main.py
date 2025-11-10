#!/usr/bin/env python3
"""
Simplified LiveKit Agent for Cheeko
Keeps all messages and initial greetings while removing unnecessary complexity
Uses preloading and prewarming but removes unnecessary services
"""

import logging
import asyncio
import os
import json
import time
import threading
from datetime import datetime
from dotenv import load_dotenv

# Resource monitoring imports
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logging.warning("psutil not available - install with: pip install psutil")

from livekit.agents import (
    AgentSession,
    JobContext,
    JobProcess,
    JobRequest,
    WorkerOptions,
    cli,
    function_tool,
    Agent,
    RunContext,
    RoomIO,
)
from livekit.agents.llm import ChatContext, ChatMessage, StopResponse
from livekit import rtc
from livekit.plugins import silero, groq

# Import essential components only
from src.providers.provider_factory import ProviderFactory
from src.config.config_loader import ConfigLoader
from src.utils.model_preloader import model_preloader
from src.utils.model_cache import model_cache

# Load environment variables
load_dotenv(".env")

logger = logging.getLogger("simple_agent")

class ResourceMonitor:
    """Monitor system resources and log performance metrics"""
    
    def __init__(self, log_interval=10):
        self.log_interval = log_interval
        self.monitoring = False
        self.monitor_thread = None
        self.start_time = time.time()
        self.client_count = 0
        
    def start_monitoring(self):
        """Start resource monitoring in background thread"""
        if not PSUTIL_AVAILABLE:
            logger.warning("📊 Resource monitoring disabled - psutil not available")
            return
            
        if self.monitoring:
            return
            
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info(f"📊 Resource monitoring started (interval: {self.log_interval}s)")
    
    def stop_monitoring(self):
        """Stop resource monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)
        logger.info("📊 Resource monitoring stopped")
    
    def increment_clients(self):
        """Increment active client count"""
        self.client_count += 1
        logger.info(f"📊 Active clients: {self.client_count}")
    
    def decrement_clients(self):
        """Decrement active client count"""
        self.client_count = max(0, self.client_count - 1)
        logger.info(f"📊 Active clients: {self.client_count}")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                self._log_resources()
                time.sleep(self.log_interval)
            except Exception as e:
                logger.error(f"📊 Resource monitoring error: {e}")
                time.sleep(self.log_interval)
    
    def _log_resources(self):
        """Log current resource usage"""
        if not PSUTIL_AVAILABLE:
            return
            
        try:
            # System-wide metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Process-specific metrics
            process = psutil.Process()
            process_cpu = process.cpu_percent()
            process_memory = process.memory_info()
            process_threads = process.num_threads()
            
            # Network I/O
            net_io = psutil.net_io_counters()
            
            # Uptime
            uptime = time.time() - self.start_time
            
            logger.info(
                f"📊 RESOURCES | "
                f"Clients: {self.client_count} | "
                f"Uptime: {uptime:.1f}s | "
                f"CPU: {cpu_percent:.1f}% (proc: {process_cpu:.1f}%) | "
                f"RAM: {memory.percent:.1f}% (proc: {process_memory.rss/1024/1024:.1f}MB) | "
                f"Threads: {process_threads} | "
                f"Net: ↓{net_io.bytes_recv/1024/1024:.1f}MB ↑{net_io.bytes_sent/1024/1024:.1f}MB"
            )
            
            # Enhanced alerting with performance recommendations
            if cpu_percent > 80:
                logger.warning(f"⚠️ HIGH CPU USAGE: {cpu_percent:.1f}% - Consider reducing client load")
            if memory.percent > 85:
                logger.warning(f"⚠️ HIGH MEMORY USAGE: {memory.percent:.1f}% - Memory cleanup recommended")
            if self.client_count > 4 and cpu_percent > 60:
                logger.warning(f"⚠️ PERFORMANCE RISK: {self.client_count} clients, CPU {cpu_percent:.1f}% - Audio jitter possible")
            if self.client_count > 6:
                logger.error(f"🚨 OVERLOAD: {self.client_count} clients exceeds recommended limit of 6")
            
            # Performance optimization suggestions
            if cpu_percent > 70 and self.client_count > 2:
                logger.info(f"💡 OPTIMIZATION TIP: High CPU with {self.client_count} clients - consider process scaling")
            if process_memory.rss/1024/1024 > 500:  # 500MB
                logger.info(f"💡 MEMORY TIP: Process using {process_memory.rss/1024/1024:.1f}MB - consider restart if growing")
                
        except Exception as e:
            logger.error(f"📊 Failed to log resources: {e}")

# Global resource monitor
resource_monitor = ResourceMonitor(log_interval=10)  # Log every 10 seconds (reduced thread activity)

class SimpleAssistant(Agent):
    """Simplified AI Assistant with basic functionality"""

    def __init__(self, instructions: str = None) -> None:
        super().__init__(instructions=instructions or "You are Cheeko, a friendly AI assistant for kids.")
        self.room_name = None
        self.device_mac = None

    def set_room_info(self, room_name: str = None, device_mac: str = None):
        """Set room name and device MAC address"""
        self.room_name = room_name
        self.device_mac = device_mac
        logger.info(f"📍 Room info set - Room: {room_name}, MAC: {device_mac}")

    async def on_user_turn_completed(self, turn_ctx: ChatContext, new_message: ChatMessage) -> None:
        """Callback before generating a reply after user turn committed"""
        if not new_message.text_content:
            # Prevent empty turns from generating responses (e.g., user pressed/released PTT without speaking)
            logger.info("[PTT] Ignoring empty user turn - no speech detected")
            raise StopResponse()
    
    @function_tool
    async def check_battery_level(self, context: RunContext, unused: str = '') -> str:
        """Check the device battery percentage.
        
        Use this to find out how much battery charge remains on the device.
        Call this function without any parameters.
        
        Args:
            unused: Internal parameter, leave empty or omit
            
        Returns:
            str: Battery percentage status message
        """
        try:
            # Send battery check request via data channel
            if hasattr(context, 'room') and context.room:
                battery_request = {
                    "type": "battery_check",
                    "timestamp": datetime.now().isoformat()
                }
                
                # Send via data channel to MQTT gateway
                await context.room.local_participant.publish_data(
                    json.dumps(battery_request).encode(),
                    topic="battery_request"
                )
                
                logger.info("🔋 Battery check request sent via data channel")
                return "Battery check requested. The device will report its current battery level."
            else:
                return "Unable to check battery - no room connection available."
                
        except Exception as e:
            logger.error(f"🔋❌ Battery check failed: {e}")
            return "Sorry, I couldn't check the battery level right now."

def prewarm(proc: JobProcess):
    """Optimized prewarm function - preloads ALL providers to eliminate job startup delay"""
    import time
    prewarm_start = time.time()
    logger.info("🚀 [PREWARM] Starting optimized prewarm - loading all providers...")

    # Start background model preloading (but only essential models)
    model_preloader.start_background_loading()

    # Load VAD model on main thread (required)
    vad_start = time.time()
    try:
        vad = model_cache.get_vad_model()
        if vad:
            proc.userdata["vad"] = vad
            logger.info(f"✅ [PREWARM] VAD model loaded from cache ({time.time() - vad_start:.3f}s)")
        else:
            # Direct loading (first time or cache miss)
            vad = silero.VAD.load()
            proc.userdata["vad"] = vad
            # Cache it for next time
            model_cache._models["vad_model"] = vad
            logger.info(f"✅ [PREWARM] VAD model loaded and cached ({time.time() - vad_start:.3f}s)")
    except Exception as e:
        logger.error(f"❌ [PREWARM] Failed to load VAD: {e}")
        # Final fallback
        try:
            vad = silero.VAD.load()
            proc.userdata["vad"] = vad
            logger.info(f"✅ [PREWARM] VAD model loaded using fallback ({time.time() - vad_start:.3f}s)")
        except Exception as e2:
            logger.error(f"❌ [PREWARM] All VAD loading attempts failed: {e2}")
            vad = None

    # Load configurations
    groq_config = ConfigLoader.get_groq_config()
    tts_config = ConfigLoader.get_tts_config()
    logger.info(f"📋 [PREWARM] Configurations loaded")

    # Preload LLM provider (biggest bottleneck - 1.1s)
    llm_start = time.time()
    try:
        llm = ProviderFactory.create_llm(groq_config)
        proc.userdata["llm"] = llm
        logger.info(f"🧠 [PREWARM] LLM provider initialized ({time.time() - llm_start:.3f}s)")
    except Exception as e:
        logger.error(f"❌ [PREWARM] Failed to initialize LLM: {e}")
        proc.userdata["llm"] = None

    # Preload STT provider (second bottleneck - 0.35s)
    stt_start = time.time()
    try:
        stt = ProviderFactory.create_stt(groq_config, vad)
        proc.userdata["stt"] = stt
        logger.info(f"🎤 [PREWARM] STT provider initialized ({time.time() - stt_start:.3f}s)")
    except Exception as e:
        logger.error(f"❌ [PREWARM] Failed to initialize STT: {e}")
        proc.userdata["stt"] = None

    # Preload TTS provider (0.1s)
    tts_start = time.time()
    try:
        tts = ProviderFactory.create_tts(groq_config, tts_config)
        proc.userdata["tts"] = tts
        logger.info(f"🔊 [PREWARM] TTS provider initialized - {tts_config.get('provider')} ({time.time() - tts_start:.3f}s)")
    except Exception as e:
        logger.error(f"❌ [PREWARM] Failed to initialize TTS: {e}")
        proc.userdata["tts"] = None

    # Preload turn detection
    try:
        turn_detection = ProviderFactory.create_turn_detection()
        proc.userdata["turn_detection"] = turn_detection
        logger.info(f"🔄 [PREWARM] Turn detection initialized")
    except Exception as e:
        logger.error(f"❌ [PREWARM] Failed to initialize turn detection: {e}")
        proc.userdata["turn_detection"] = None

    # Store configs for entrypoint
    proc.userdata["groq_config"] = groq_config
    proc.userdata["tts_config"] = tts_config

    total_time = time.time() - prewarm_start
    logger.info(f"✅ [PREWARM] Complete! Total time: {total_time:.3f}s - Job startup will now be near-instant!")

async def entrypoint(ctx: JobContext):
    """Optimized entrypoint - uses preloaded providers for near-instant startup"""
    import time
    entrypoint_start = time.time()

    ctx.log_context_fields = {"room": ctx.room.name}
    logger.info(f"🚀 [ENTRYPOINT] Starting agent in room: {ctx.room.name}")

    # Start resource monitoring for this session
    resource_monitor.start_monitoring()
    resource_monitor.increment_clients()

    room_name = ctx.room.name
    device_mac = None

    # Extract MAC address from room name (format: UUID_MAC)
    if '_' in room_name:
        parts = room_name.split('_')
        if len(parts) >= 2:
            mac_part = parts[-1]
            if len(mac_part) == 12 and mac_part.isalnum():
                device_mac = ':'.join(mac_part[i:i+2] for i in range(0, 12, 2))
                logger.info(f"📱 Extracted MAC from room name: {device_mac}")

    # Load agent configuration
    agent_config = ConfigLoader.get_agent_config()

    # Use default prompt from ConfigLoader or fallback
    try:
        agent_prompt = ConfigLoader.get_default_prompt()
        logger.info(f"📄 Using default prompt from config (length: {len(agent_prompt)} chars)")
    except:
        # Fallback prompt if config loading fails
        agent_prompt = """<identity>
        You are Cheeko, a playful AI companion for kids 3–12 years old. You're super silly, energetic, and love to learn and explore with children!
        </identity>

        <personality>
        - Always enthusiastic and positive
        - Use simple, age-appropriate language
        - Love adventures, games, and learning
        - Encourage curiosity and creativity
        - Keep responses short and engaging
        </personality>

        <greeting>
        When you first meet a child, greet them warmly with something like:
        "Heya, kiddo! I'm Cheeko, your super-silly learning buddy—ready to blast off into adventure, giggles, and a whole lot of aha! moments. What fun quest do you want to tackle today?"
        </greeting>

        <guidelines>
        - Keep responses under 50 words when possible
        - Use emojis sparingly
        - Ask engaging questions
        - Be encouraging and supportive
        - If asked about battery, use the check_battery_level function
        </guidelines>"""
        logger.info(f"📄 Using fallback prompt (length: {len(agent_prompt)} chars)")

    # ⚡ PERFORMANCE OPTIMIZATION: Use preloaded providers from prewarm
    logger.info("⚡ [OPTIMIZATION] Loading providers from prewarm cache...")

    # Get preloaded providers from prewarm (near-instant)
    vad = ctx.proc.userdata.get("vad")
    llm = ctx.proc.userdata.get("llm")
    stt = ctx.proc.userdata.get("stt")
    tts = ctx.proc.userdata.get("tts")
    turn_detection = ctx.proc.userdata.get("turn_detection")
    groq_config = ctx.proc.userdata.get("groq_config")
    tts_config = ctx.proc.userdata.get("tts_config")

    # Fallback to creating providers if prewarm failed (should be rare)
    if not vad:
        logger.warning("⚠️ VAD not preloaded, creating now (this will add latency)...")
        vad = ProviderFactory.create_vad()
    else:
        logger.info("✅ VAD loaded from prewarm")

    if not llm:
        logger.warning("⚠️ LLM not preloaded, creating now (this will add ~1.1s latency)...")
        groq_config = groq_config or ConfigLoader.get_groq_config()
        llm = ProviderFactory.create_llm(groq_config)
    else:
        logger.info("✅ LLM loaded from prewarm")

    if not stt:
        logger.warning("⚠️ STT not preloaded, creating now (this will add ~0.35s latency)...")
        groq_config = groq_config or ConfigLoader.get_groq_config()
        stt = ProviderFactory.create_stt(groq_config, vad)
    else:
        logger.info("✅ STT loaded from prewarm")

    if not tts:
        logger.warning("⚠️ TTS not preloaded, creating now (this will add ~0.1s latency)...")
        groq_config = groq_config or ConfigLoader.get_groq_config()
        tts_config = tts_config or ConfigLoader.get_tts_config()
        tts = ProviderFactory.create_tts(groq_config, tts_config)
    else:
        logger.info(f"✅ TTS loaded from prewarm - Provider: {tts_config.get('provider') if tts_config else 'unknown'}")

    if not turn_detection:
        logger.info("ℹ️ Turn detection not preloaded (may be disabled)")
        turn_detection = ProviderFactory.create_turn_detection()
    else:
        logger.info("✅ Turn detection loaded from prewarm")

    provider_load_time = time.time() - entrypoint_start
    logger.info(f"⚡ [PERFORMANCE] Providers loaded in {provider_load_time:.3f}s (vs ~1.6s without prewarm)")

    # Create session with push-to-talk support (manual turn detection)
    session = AgentSession(
        llm=llm,
        stt=stt,
        tts=tts,
        turn_detection="manual",  # Manual turn detection for push-to-talk
        vad=vad,
        preemptive_generation=agent_config['preemptive_generation'],
        min_endpointing_delay=0.2,      # Ultra-aggressive for fastest response
        min_interruption_duration=0.15,  # Minimal to prevent audio overlap
        allow_interruptions=True,       # Enable interruptions for better UX
    )

    # Disable audio input by default for push-to-talk mode
    session.input.set_audio_enabled(False)
    logger.info("[PTT] Initial setup: Audio input DISABLED (push-to-talk mode)")
    
    # Create assistant
    assistant = SimpleAssistant(instructions=agent_prompt)
    assistant.set_room_info(room_name=room_name, device_mac=device_mac)
    
    # Simple event handlers for logging
    # Track audio streaming state
    audio_streaming = False
    last_speech_id = None
    
    @session.on("agent_state_changed")
    def on_agent_state_changed(ev):
        nonlocal audio_streaming
        logger.info(f"Agent state: {ev.old_state} -> {ev.new_state}")
        
        # Send state to MQTT gateway via data channel with proper audio tracking
        async def send_state_change():
            nonlocal audio_streaming  # Need this for nested async function
            try:
                # Handle speaking state
                if ev.new_state == "speaking":
                    audio_streaming = True
                    logger.info("🎵 Audio streaming started")
                
                # Handle speaking->listening transition with audio stream awareness
                if ev.old_state == "speaking" and ev.new_state == "listening":
                    if audio_streaming:
                        logger.info("🎵 Waiting for audio stream to complete before sending state change...")
                        # Ultra-fast delay for Groq TTS (much faster than EdgeTTS)
                        await asyncio.sleep(0.8)  # Reduced from 1.5s for Groq performance
                        audio_streaming = False
                        logger.info("🎵 Audio stream should be complete now")
                
                state_data = {
                    "type": "agent_state_changed",
                    "data": {
                        "type": "agent_state_changed",
                        "old_state": ev.old_state,
                        "new_state": ev.new_state,
                        "audio_streaming": audio_streaming,
                        "created_at": datetime.now().timestamp()
                    }
                }
                
                await ctx.room.local_participant.publish_data(
                    json.dumps(state_data).encode(),
                    topic=""
                )
                logger.info(f"📤 State change sent: {ev.old_state} -> {ev.new_state} (audio_streaming: {audio_streaming})")
                
            except Exception as e:
                logger.error(f"Failed to send state change: {e}")
        
        asyncio.create_task(send_state_change())
    
    @session.on("speech_created")
    def on_speech_created(ev):
        nonlocal audio_streaming, last_speech_id
        speech_id = getattr(ev, 'speech_id', 'unknown')
        last_speech_id = speech_id
        audio_streaming = True
        logger.info(f"🤖 Speech created: {speech_id}")
        
        # Send speech event to MQTT gateway
        try:
            speech_data = {
                "type": "speech_created",
                "data": {
                    "type": "speech_created",
                    "speech_id": speech_id,
                    "user_initiated": getattr(ev, 'user_initiated', True),
                    "source": getattr(ev, 'source', 'generate_reply'),
                    "created_at": datetime.now().timestamp()
                }
            }
            
            asyncio.create_task(
                ctx.room.local_participant.publish_data(
                    json.dumps(speech_data).encode(),
                    topic=""
                )
            )
        except Exception as e:
            logger.error(f"Failed to send speech event: {e}")
    
    @session.on("speech_finished")
    def on_speech_finished(ev):
        nonlocal audio_streaming
        speech_id = getattr(ev, 'speech_id', 'unknown')
        audio_streaming = False
        logger.info(f"🤖 Speech finished - audio stream complete: {speech_id}")
        
        # Send precise speech completion event
        try:
            speech_finished_data = {
                "type": "speech_finished",
                "data": {
                    "type": "speech_finished",
                    "speech_id": speech_id,
                    "created_at": datetime.now().timestamp()
                }
            }
            
            asyncio.create_task(
                ctx.room.local_participant.publish_data(
                    json.dumps(speech_finished_data).encode(),
                    topic=""
                )
            )
        except Exception as e:
            logger.error(f"Failed to send speech finished event: {e}")
    
    # Handle data channel messages from MQTT gateway
    @ctx.room.on("data_received")
    def on_data_received(data: rtc.DataPacket):
        try:
            import time
            receive_time = time.time()
            logger.info(f"📨 [DATA-CHANNEL] *** DATA RECEIVED *** - Length: {len(data.data)} bytes, From: {data.participant.identity if data.participant else 'unknown'}, Time: {receive_time}")

            message = json.loads(data.data.decode())
            msg_type = message.get("type")
            msg_timestamp = message.get("timestamp", "N/A")

            logger.info(f"📨 [DATA-CHANNEL] Received message type: {msg_type}, Timestamp: {msg_timestamp}")
            logger.info(f"📨 [DATA-CHANNEL] Full message content: {message}")

            if msg_type == "device_info":
                logger.info(f"📱 [DEVICE-INFO] Device info received - MAC: {device_mac}")
            elif msg_type == "abort":
                logger.info("🛑 [ABORT] Abort signal received from device - interrupting agent speech")
                # Handle abort by interrupting current speech
                async def handle_abort():
                    try:
                        # Interrupt current speech using the session.interrupt() method
                        logger.info("🛑 [ABORT] Calling session.interrupt() to stop agent speech...")
                        session.interrupt()
                        logger.info("✅ [ABORT] Agent speech interrupted successfully")

                        # Send immediate audio stop confirmation
                        abort_response = {
                            "type": "audio_stopped",
                            "data": {
                                "type": "audio_stopped",
                                "reason": "abort_received",
                                "created_at": datetime.now().timestamp()
                            }
                        }

                        await ctx.room.local_participant.publish_data(
                            json.dumps(abort_response).encode(),
                            topic=""
                        )
                        logger.info("✅ [ABORT] Audio stop confirmation sent to gateway")

                    except Exception as e:
                        logger.error(f"❌ [ABORT] Failed to handle abort: {e}", exc_info=True)

                asyncio.create_task(handle_abort())
            elif msg_type == "disconnect_agent":
                logger.info("👋 [DISCONNECT] Disconnect signal received - agent leaving room (room stays alive)")
                # Handle agent disconnect - leave room but don't shut down process
                async def handle_disconnect():
                    try:
                        logger.info("👋 [DISCONNECT] Agent disconnecting from room...")

                        # Stop any ongoing speech first
                        try:
                            session.interrupt()
                            logger.info("✅ [DISCONNECT] Interrupted ongoing speech")
                        except Exception as e:
                            logger.warning(f"⚠️ [DISCONNECT] No speech to interrupt: {e}")

                        # Disconnect from the room
                        await ctx.room.disconnect()
                        logger.info("✅ [DISCONNECT] Agent disconnected successfully - room remains alive for redeployment")

                    except Exception as e:
                        logger.error(f"❌ [DISCONNECT] Failed to disconnect agent: {e}", exc_info=True)

                asyncio.create_task(handle_disconnect())
            elif msg_type == "clear_history":
                logger.info("🧹 [CLEAR-HISTORY] Clear history signal received - resetting conversation to brand new")
                # Handle clearing chat history without disconnecting
                async def handle_clear_history():
                    try:
                        logger.info("🧹 [CLEAR-HISTORY] Clearing conversation history...")

                        # Get the current agent from the session
                        agent = session._agent
                        if not agent:
                            logger.error("❌ [CLEAR-HISTORY] No agent found in session")
                            return

                        # Get the system prompt from the agent's instructions
                        system_prompt = agent._instructions if hasattr(agent, '_instructions') else "You are Cheeko, a friendly AI assistant for kids."
                        logger.info(f"🧹 [CLEAR-HISTORY] Retrieved system prompt (length: {len(system_prompt)} chars)")

                        # Create a new empty ChatContext with just the system message
                        new_ctx = ChatContext.empty()
                        new_ctx.add_message(role="system", content=system_prompt)
                        logger.info("🧹 [CLEAR-HISTORY] Created new empty context with system prompt")

                        # Update the agent's chat context to the new empty one
                        await agent.update_chat_ctx(new_ctx)
                        logger.info("✅ [CLEAR-HISTORY] Chat context updated successfully")

                        # Interrupt any ongoing speech for clean state
                        session.interrupt()
                        logger.info("✅ [CLEAR-HISTORY] Interrupted ongoing speech")

                        # Send confirmation back to gateway
                        history_cleared_response = {
                            "type": "history_cleared",
                            "data": {
                                "type": "history_cleared",
                                "cleared_at": datetime.now().timestamp(),
                                "status": "success"
                            }
                        }

                        await ctx.room.local_participant.publish_data(
                            json.dumps(history_cleared_response).encode(),
                            topic=""
                        )
                        logger.info("✅ [CLEAR-HISTORY] History cleared successfully - conversation reset to brand new!")

                    except Exception as e:
                        logger.error(f"❌ [CLEAR-HISTORY] Failed to clear history: {e}", exc_info=True)

                asyncio.create_task(handle_clear_history())
            else:
                logger.info(f"📨 Unknown message type received: {msg_type}")
                
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse JSON from data channel: {e}")
            logger.error(f"Raw data: {data.data}")
        except Exception as e:
            logger.error(f"❌ Failed to process data channel message: {e}")
            logger.error(f"Raw data: {data.data}")

    logger.info("✅ [DATA-CHANNEL] Data channel handler registered successfully")

    # Enhanced cleanup on disconnect with resource monitoring
    @ctx.room.on("participant_disconnected")
    def on_participant_disconnected(participant: rtc.RemoteParticipant):
        logger.info(f"👤 Participant disconnected: {participant.identity}")
        resource_monitor.decrement_clients()
        
        # Trigger garbage collection for memory cleanup
        import gc
        gc.collect()
        logger.info("🧹 Memory cleanup triggered after client disconnect")
    
    @ctx.room.on("disconnected")
    def on_room_disconnected():
        logger.info("🔴 Room disconnected")
        resource_monitor.decrement_clients()
        resource_monitor.stop_monitoring()
        
        # Final cleanup
        import gc
        gc.collect()
        logger.info("🧹 Final cleanup completed")
    
    # Start the session
    await session.start(agent=assistant, room=ctx.room)

    # Register push-to-talk RPC methods
    @ctx.room.local_participant.register_rpc_method("start_turn")
    async def start_turn(data: rtc.RpcInvocationData):
        logger.info(f"[PTT] start_turn called by {data.caller_identity}")
        session.interrupt()
        session.clear_user_turn()
        session.input.set_audio_enabled(True)
        logger.info("[PTT] Audio input ENABLED")
        return "Audio input enabled"

    @ctx.room.local_participant.register_rpc_method("end_turn")
    async def end_turn(data: rtc.RpcInvocationData):
        logger.info(f"[PTT] end_turn called by {data.caller_identity}")
        session.input.set_audio_enabled(False)
        logger.info("[PTT] Audio input DISABLED, committing user turn")
        session.commit_user_turn(
            transcript_timeout=10.0,
            stt_flush_duration=2.0,
        )
        return "Audio input disabled and turn committed"

    @ctx.room.local_participant.register_rpc_method("cancel_turn")
    async def cancel_turn(data: rtc.RpcInvocationData):
        logger.info(f"[PTT] cancel_turn called by {data.caller_identity}")
        session.input.set_audio_enabled(False)
        session.clear_user_turn()
        logger.info("[PTT] Audio input CANCELLED")
        return "Turn cancelled"

    logger.info("✅ Push-to-talk RPC methods registered successfully")
    logger.info("✅ Simple agent started successfully")
    logger.info("🔗 [CONNECTION] Agent connecting to room and waiting for messages...")
    await ctx.connect()

if __name__ == "__main__":
    # Set high priority for audio processing
    import os
    if os.name == 'nt':  # Windows
        try:
            import psutil
            p = psutil.Process()
            p.nice(psutil.HIGH_PRIORITY_CLASS)
            logger.info("🚀 Set high priority for audio processing")
        except:
            pass
    
    cli.run_app(WorkerOptions(
        entrypoint_fnc=entrypoint,
        prewarm_fnc=prewarm,
        num_idle_processes=2,  # Reduced for lower thread usage (was 6)
        initialize_process_timeout=60.0,
        agent_name="cheeko-agent",  # Named agent for explicit dispatch only
    ))