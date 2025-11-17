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
    WorkerOptions,
    cli,
    function_tool,
    Agent,
    RunContext,
)
from livekit import rtc
from livekit.plugins import silero, groq
from livekit.plugins import inworld
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
    """Simple prewarm function with model preloading"""
    logger.info("[PREWARM] Simple prewarm starting...")
    
    # Start background model preloading (but only essential models)
    model_preloader.start_background_loading()
    
    # Load VAD model on main thread (required)
    try:
        vad = model_cache.get_vad_model()
        if vad:
            proc.userdata["vad"] = vad
            logger.info("[PREWARM] VAD model loaded from cache")
        else:
            # Direct loading (first time or cache miss)
            vad = silero.VAD.load()
            proc.userdata["vad"] = vad
            # Cache it for next time
            model_cache._models["vad_model"] = vad
            logger.info("[PREWARM] VAD model loaded and cached for future use")
    except Exception as e:
        logger.error(f"[PREWARM] Failed to load VAD: {e}")
        # Final fallback
        try:
            vad = silero.VAD.load()
            proc.userdata["vad"] = vad
            logger.info("[PREWARM] VAD model loaded using final fallback")
        except Exception as e2:
            logger.error(f"[PREWARM] All VAD loading attempts failed: {e2}")
    
    logger.info("[PREWARM] Simple prewarm complete")

async def entrypoint(ctx: JobContext):
    """Simplified entrypoint for the agent using provider factory pattern"""
    ctx.log_context_fields = {"room": ctx.room.name}
    print(f"Starting simple agent in room: {ctx.room.name}")
    
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
    
    # Load configuration using ConfigLoader (same as main server)
    groq_config = ConfigLoader.get_groq_config()
    agent_config = ConfigLoader.get_agent_config()
    
    # Use default prompt from ConfigLoader or fallback
    try:
        agent_prompt = ConfigLoader.get_default_prompt()
        logger.info(f"📄 Using default prompt from config (length: {len(agent_prompt)} chars)")
    except:
        # Fallback prompt if config loading fails
        agent_prompt = """instructions=
                You are also a helpful, patient, and curious study partner for a student learning about the Fall of the Roman Empire.
                Your primary goal is to foster deep understanding through guided discovery, dialogue, and repetition.

                Your responsibilities include:
                    •	Explaining core topics related to the Fall of the Roman Empire, including:
                    •	Economic factors (currency devaluation, overtaxation, wealth inequality)
                    •	Military decline (barbarian invasions, loss of discipline, mercenary reliance)
                    •	Political instability (succession crises, civil wars, corruption)
                    •	Administrative challenges (East-West division, bureaucratic bloat)
                    •	Social and cultural changes (spread of Christianity, shifting values)
                    •	External pressures (Germanic tribes, Huns, Sassanid Persians)
                    •	Environmental factors (climate change, plagues, agricultural decline)
                    •	Using Socratic questioning to help the student reach answers themselves.
                    •	Providing clear explanations only when necessary, then quizzing the student on similar historical questions.
                    •	Alternating between roles: sometimes you ask questions, other times you answer.
                    •	Prioritizing reinforcement through follow-up questions that vary in difficulty and context.
                    •	Maintaining a friendly, encouraging tone that supports confidence and curiosity.

                Do not rush to give the answer. Instead, support reasoning, analytical thinking, and the development of historical understanding.

                It's very important that you remember you are having this talk via voice. You should use clear language and be specific about dates, names, and events related to the Fall of Rome (roughly 376-476 CE, though the Eastern Roman Empire continued until 1453 CE).

                Always start answering a question by first asking questions, try to use the socratic method until it seems like you're both stuck.

                FLASH CARDS FEATURE:4
                You can create flash cards to help the user learn and remember important concepts. Use the create_flash_card function
                to create a new flash card with a question and answer. The flash card will appear beside you in the UI.
                
                Be proactive in creating flash cards for important concepts, especially when:
                - Teaching new vocabulary or terminology
                - Explaining complex principles that are worth remembering
                - Summarizing key points from a discussion
                
                For example, when explaining the causes of the Fall of Rome, you might create a flash card with:
                Question: "What year marks the traditional end of the Western Roman Empire?"
                Answer: "476 CE, when the last Roman Emperor Romulus Augustulus was deposed by Odoacer, the Germanic king."

                Do not tell the user the answer before they look at it!
                
                You can also flip flash cards to show the answer using the flip_flash_card function.
                
                QUIZ FEATURE:
                You can create multiple-choice quizzes to test the user's knowledge. Use the create_quiz function
                to create a new quiz with questions and multiple-choice answers. The quiz will appear on the left side of the UI.
                
                For each question, you should provide:
                - A clear question text
                - 3-5 answer options (one must be marked as correct)
                
                Quizzes are great for:
                - Testing comprehension after explaining a concept
                - Reviewing previously covered material
                - Preparing the user for a test or exam
                - Breaking up longer learning sessions with interactive elements
                
                When the user submits their answers, you'll automatically provide verbal feedback on their performance.
                Don't just read back the questions and answers, give some color commentary that makes it interesting. Use names, 
                dates, or other interesting facts about the question to root it in memory.
                For any incorrectly answered questions, flash cards will be created to help them study the correct answers.
                
                Example format for creating a quiz:
                ```python
                await self.create_quiz([
                    {
                        "text": "What year marks the traditional end of the Western Roman Empire?",
                        "answers": [
                            {"text": "410 CE", "is_correct": False},
                            {"text": "476 CE", "is_correct": True},
                            {"text": "527 CE", "is_correct": False},
                            {"text": "1453 CE", "is_correct": False}
                        ]
                    },
                    {
                        "text": "Who was the last Western Roman Emperor?",
                        "answers": [
                            {"text": "Constantine", "is_correct": False},
                            {"text": "Theodosius", "is_correct": False},
                            {"text": "Romulus Augustulus", "is_correct": True},
                            {"text": "Justinian", "is_correct": False}
                        ]
                    }
                ])
                ```
                
                Start the interaction with a short introduction, and let the student
                guide their own learning journey!

                Keep your speaking turns short, only one or two sentences. We want the
                student to do most of the speaking.
            """
        logger.info(f"📄 Using fallback prompt (length: {len(agent_prompt)} chars)")
    
    # Get VAD from prewarm
    vad = ctx.proc.userdata.get("vad")
    if not vad:
        logger.warning("No VAD from prewarm, loading now...")
        vad = ProviderFactory.create_vad()
    
    # Create providers using ProviderFactory (same as main server)
    logger.info("🏭 Creating providers using ProviderFactory...")
    
    llm = ProviderFactory.create_llm(groq_config)
    logger.info(f"🧠 LLM created: {type(llm)}")
    
    stt = ProviderFactory.create_stt(groq_config, vad)
    logger.info(f"🎤 STT created: {type(stt)}")
    
    # Get TTS config and create TTS provider
    tts_config = ConfigLoader.get_tts_config()
    tts = ProviderFactory.create_tts(groq_config, tts_config)
    logger.info(f"🔊 TTS created: {type(tts)} - Provider: {tts_config.get('provider')}")
    
    # Create turn detection (same as main server)
    turn_detection = ProviderFactory.create_turn_detection()
    
    # Create session with basic supported parameters
    session = AgentSession(
        llm=llm,
        stt=stt,
        tts=inworld.TTS(
            model="inworld-tts-1-max",
            voice="Asuka",
            api_key=os.getenv("INWORLD_API_KEY")
        ),
        turn_detection=turn_detection,
        vad=vad,
        preemptive_generation=agent_config['preemptive_generation'],
        min_endpointing_delay=0.2,      # Ultra-aggressive for fastest response
        min_interruption_duration=0.15,  # Minimal to prevent audio overlap
        allow_interruptions=True,       # Enable interruptions for better UX
    )
    
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
            logger.info(f"📨 [DATA-CHANNEL] Raw data received - Length: {len(data.data)} bytes, From: {data.participant.identity if data.participant else 'unknown'}, Time: {receive_time}")

            message = json.loads(data.data.decode())
            msg_type = message.get("type")
            msg_timestamp = message.get("timestamp", "N/A")

            logger.info(f"📨 [DATA-CHANNEL] Received message type: {msg_type}, Timestamp: {msg_timestamp}")
            logger.info(f"📨 [DATA-CHANNEL] Full message content: {message}")

            if msg_type == "device_info":
                logger.info(f"📱 [DEVICE-INFO] Device info received - MAC: {device_mac}")
            elif msg_type == "agent_ready":
                logger.info("🤖 [AGENT-READY] Agent ready signal received - triggering initial greeting NOW")
                # Trigger initial greeting
                async def trigger_greeting():
                    try:
                        logger.info("🎯 [GREETING-START] Starting to generate initial greeting...")
                        await session.generate_reply()
                        logger.info("✅ [GREETING-COMPLETE] Initial greeting generated and sent successfully")
                    except Exception as e:
                        logger.error(f"❌ [GREETING-ERROR] Failed to generate greeting: {e}", exc_info=True)

                logger.info("🎯 [GREETING-TASK] Creating asyncio task for greeting generation")
                asyncio.create_task(trigger_greeting())
            elif msg_type == "abort":
                logger.info("🛑 Abort signal received from device")
                # Handle abort by stopping current speech and clearing audio
                async def handle_abort():
                    try:
                        # Stop current speech if any
                        if hasattr(session, 'stop_speech'):
                            await session.stop_speech()
                        
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
                        logger.info("🛑 Audio stop confirmation sent")
                        
                    except Exception as e:
                        logger.error(f"Failed to handle abort: {e}")
                
                asyncio.create_task(handle_abort())
            else:
                logger.info(f"📨 Unknown message type received: {msg_type}")
                
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse JSON from data channel: {e}")
            logger.error(f"Raw data: {data.data}")
        except Exception as e:
            logger.error(f"❌ Failed to process data channel message: {e}")
            logger.error(f"Raw data: {data.data}")
    
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
    
    logger.info("✅ Simple agent started successfully")
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
        
    ))