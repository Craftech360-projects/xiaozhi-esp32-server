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
from livekit.agents.llm import ChatContext
from livekit import rtc
from livekit.plugins import silero, groq

# Import essential components only
from src.providers.provider_factory import ProviderFactory
from src.config.config_loader import ConfigLoader
from src.utils.model_preloader import model_preloader
from src.utils.model_cache import model_cache
from src.mcp.device_control_service import DeviceControlService
from src.mcp.mcp_executor import LiveKitMCPExecutor

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
        self.mcp_executor = None
        self._job_context = None
    
    def sanitize_text_for_speech(self, text: str) -> str:
        """Remove markdown, emojis, and special characters for TTS"""
        import re
        
        # Remove markdown bold/italic
        text = re.sub(r'\*\*\*(.+?)\*\*\*', r'\1', text)  # ***text***
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)      # **text**
        text = re.sub(r'\*(.+?)\*', r'\1', text)          # *text*
        text = re.sub(r'__(.+?)__', r'\1', text)          # __text__
        text = re.sub(r'_(.+?)_', r'\1', text)            # _text_
        
        # Remove markdown headers
        text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
        
        # Remove bullet points and list markers
        text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
        
        # Remove code blocks
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
        text = re.sub(r'`(.+?)`', r'\1', text)
        
        # Remove emojis (basic removal)
        emoji_pattern = re.compile("["
            u"\U0001F600-\U0001F64F"  # emoticons
            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
            u"\U0001F680-\U0001F6FF"  # transport & map symbols
            u"\U0001F1E0-\U0001F1FF"  # flags
            u"\U00002702-\U000027B0"
            u"\U000024C2-\U0001F251"
            "]+", flags=re.UNICODE)
        text = emoji_pattern.sub('', text)
        
        # Remove extra whitespace
        text = re.sub(r'\n+', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    async def say(self, message: str, **kwargs):
        """Override say method to sanitize text before TTS"""
        sanitized = self.sanitize_text_for_speech(message)
        logger.info(f"🧹 Sanitized text: '{message[:50]}...' -> '{sanitized[:50]}...'")
        return await super().say(sanitized, **kwargs)

    def set_room_info(self, room_name: str = None, device_mac: str = None):
        """Set room name and device MAC address"""
        self.room_name = room_name
        self.device_mac = device_mac
        logger.info(f"📍 Room info set - Room: {room_name}, MAC: {device_mac}")

    def set_mcp_executor(self, mcp_executor):
        """Set MCP executor for device control"""
        self.mcp_executor = mcp_executor
        logger.info("🎛️ MCP executor set for device control")

    def set_job_context(self, job_context):
        """Set JobContext for room access"""
        self._job_context = job_context
        logger.info("🔗 JobContext set for MCP communication")
    
    @function_tool
    async def check_battery_level(self, context: RunContext) -> str:
        """Check the device battery percentage.
        
        Use this to find out how much battery charge remains on the device.
        Call this function without any parameters.
        
        Returns:
            str: Battery percentage status message
        """
        logger.info("🔋 Battery check requested in simple agent")

        if not self.mcp_executor:
            logger.warning("🔋 MCP executor not available")
            return "Battery status is not available right now."

        if not self._job_context:
            logger.warning("🔋 JobContext not available for room access")
            return "Battery status is not available right now."

        # Set JobContext for MCP executor (has room access)
        self.mcp_executor.set_context(self._job_context)
        logger.info("🔋 JobContext set on mcp_executor, calling get_battery_status")

        result = await self.mcp_executor.get_battery_status()
        logger.info(f"🔋 Battery check result: {result}")
        return result
    
    @function_tool
    async def set_device_volume(self, context: RunContext, volume: int) -> str:
        """Set device volume to a specific level (0-100).
        
        Use this to set the volume to an exact level.
        
        Args:
            volume: Volume level from 0 (mute) to 100 (maximum)
            
        Returns:
            str: Confirmation message
        """
        logger.info(f"🔊 Volume set requested: {volume}")
        
        if not self.mcp_executor:
            logger.warning("🔊 MCP executor not available")
            return "Sorry, volume control is not available right now."
        
        if not self._job_context:
            logger.warning("🔊 JobContext not available")
            return "Sorry, volume control is not available right now."
        
        # Set JobContext for MCP executor
        self.mcp_executor.set_context(self._job_context)
        logger.info(f"🔊 Setting volume to {volume}")
        
        result = await self.mcp_executor.set_volume(volume)
        logger.info(f"🔊 Volume set result: {result}")
        return result
    
    @function_tool
    async def adjust_device_volume(self, context: RunContext, action: str, step: int = 10) -> str:
        """Adjust device volume up or down.
        
        Use this to increase or decrease volume by a step amount.
        
        Args:
            action: Either "up", "down", "increase", or "decrease"
            step: Volume step size (default 10)
            
        Returns:
            str: Confirmation message
        """
        logger.info(f"🔊 Volume adjust requested: {action} by {step}")
        
        if not self.mcp_executor:
            logger.warning("🔊 MCP executor not available")
            return "Sorry, volume control is not available right now."
        
        if not self._job_context:
            logger.warning("🔊 JobContext not available")
            return "Sorry, volume control is not available right now."
        
        # Set JobContext for MCP executor
        self.mcp_executor.set_context(self._job_context)
        logger.info(f"🔊 Adjusting volume {action} by {step}")
        
        result = await self.mcp_executor.adjust_volume(action, step)
        logger.info(f"🔊 Volume adjust result: {result}")
        return result
    
    @function_tool
    async def get_device_volume(self, context: RunContext) -> str:
        """Get current device volume level.
        
        Use this to check what the current volume is set to.
        
        Returns:
            str: Current volume level
        """
        logger.info("🔊 Volume get requested")
        
        if not self.mcp_executor:
            logger.warning("🔊 MCP executor not available")
            return "Sorry, volume control is not available right now."
        
        if not self._job_context:
            logger.warning("🔊 JobContext not available")
            return "Sorry, volume control is not available right now."
        
        # Set JobContext for MCP executor
        self.mcp_executor.set_context(self._job_context)
        logger.info("🔊 Getting current volume")
        
        result = await self.mcp_executor.get_volume()
        logger.info(f"🔊 Volume get result: {result}")
        return result
    
    @function_tool
    async def set_light_color(self, context: RunContext, color: str) -> str:
        """Set the device LED light color.
        
        Use this to change the LED color to a specific color.
        
        Args:
            color: Color name (red, blue, green, yellow, purple, orange, pink, cyan, magenta, white, off)
            
        Returns:
            str: Confirmation message
        """
        logger.info(f"💡 LED color set requested: {color}")
        
        if not self.mcp_executor:
            logger.warning("💡 MCP executor not available")
            return "Sorry, light control is not available right now."
        
        if not self._job_context:
            logger.warning("💡 JobContext not available")
            return "Sorry, light control is not available right now."
        
        # Set JobContext for MCP executor
        self.mcp_executor.set_context(self._job_context)
        logger.info(f"💡 Setting LED color to {color}")
        
        result = await self.mcp_executor.set_light_color(color)
        logger.info(f"💡 LED color set result: {result}")
        return result
    
    @function_tool
    async def set_light_mode(self, context: RunContext, mode: str) -> str:
        """Set the device LED light mode.
        
        Use this to change the LED mode (rainbow, default, custom, etc.).
        
        Args:
            mode: Light mode (rainbow, default, custom)
            
        Returns:
            str: Confirmation message
        """
        logger.info(f"💡 LED mode set requested: {mode}")
        
        if not self.mcp_executor:
            logger.warning("💡 MCP executor not available")
            return "Sorry, light control is not available right now."
        
        if not self._job_context:
            logger.warning("💡 JobContext not available")
            return "Sorry, light control is not available right now."
        
        # Set JobContext for MCP executor
        self.mcp_executor.set_context(self._job_context)
        logger.info(f"💡 Setting LED mode to {mode}")
        
        result = await self.mcp_executor.set_light_mode(mode)
        logger.info(f"💡 LED mode set result: {result}")
        return result
    
    @function_tool
    async def set_rainbow_speed(self, context: RunContext, speed_ms: int) -> str:
        """Set the rainbow LED animation speed.
        
        Use this to control how fast the rainbow effect cycles.
        
        Args:
            speed_ms: Speed in milliseconds (50-1000, lower is faster)
            
        Returns:
            str: Confirmation message
        """
        logger.info(f"🌈 Rainbow speed set requested: {speed_ms}ms")
        
        if not self.mcp_executor:
            logger.warning("🌈 MCP executor not available")
            return "Sorry, light control is not available right now."
        
        if not self._job_context:
            logger.warning("🌈 JobContext not available")
            return "Sorry, light control is not available right now."
        
        # Set JobContext for MCP executor
        self.mcp_executor.set_context(self._job_context)
        logger.info(f"🌈 Setting rainbow speed to {speed_ms}ms")
        
        result = await self.mcp_executor.set_rainbow_speed(str(speed_ms))
        logger.info(f"🌈 Rainbow speed set result: {result}")
        return result
    
    # ========================================
    # ROBOT CONTROL FUNCTIONS
    # ========================================
    
    @function_tool
    async def raise_hand(self, context: RunContext) -> str:
        """Make the robot raise its hand.
        
        Use this when the user asks the robot to raise hand, wave hello, or similar gestures.
        
        Returns:
            str: Confirmation message
        """
        logger.info(f"🤖 Robot raise hand requested")
        
        if not self.mcp_executor:
            logger.warning("🤖 MCP executor not available")
            return "Sorry, robot control is not available right now."
        
        if not self._job_context:
            logger.warning("🤖 JobContext not available")
            return "Sorry, robot control is not available right now."
        
        # Set JobContext for MCP executor
        self.mcp_executor.set_context(self._job_context)
        logger.info(f"🤖 Sending raise hand command")
        
        result = await self.mcp_executor.robot_control("raise_hand")
        logger.info(f"🤖 Raise hand result: {result}")
        return result
    
    @function_tool
    async def lower_hand(self, context: RunContext) -> str:
        """Make the robot lower its hand.
        
        Use this when the user asks the robot to lower hand or return to rest position.
        
        Returns:
            str: Confirmation message
        """
        logger.info(f"🤖 Robot lower hand requested")
        
        if not self.mcp_executor:
            logger.warning("🤖 MCP executor not available")
            return "Sorry, robot control is not available right now."
        
        if not self._job_context:
            logger.warning("🤖 JobContext not available")
            return "Sorry, robot control is not available right now."
        
        self.mcp_executor.set_context(self._job_context)
        logger.info(f"🤖 Sending lower hand command")
        
        result = await self.mcp_executor.robot_control("lower_hand")
        logger.info(f"🤖 Lower hand result: {result}")
        return result
    
    @function_tool
    async def wave_hand(self, context: RunContext) -> str:
        """Make the robot wave its hand.
        
        Use this when the user asks the robot to wave, say hello with a wave, or greet.
        
        Returns:
            str: Confirmation message
        """
        logger.info(f"🤖 Robot wave hand requested")
        
        if not self.mcp_executor:
            logger.warning("🤖 MCP executor not available")
            return "Sorry, robot control is not available right now."
        
        if not self._job_context:
            logger.warning("🤖 JobContext not available")
            return "Sorry, robot control is not available right now."
        
        self.mcp_executor.set_context(self._job_context)
        logger.info(f"🤖 Sending wave hand command")
        
        result = await self.mcp_executor.robot_control("wave_hand")
        logger.info(f"🤖 Wave hand result: {result}")
        return result
    
    @function_tool
    async def nod_head(self, context: RunContext) -> str:
        """Make the robot nod its head (yes gesture).
        
        Use this when the user asks the robot to nod, agree, or say yes with a gesture.
        
        Returns:
            str: Confirmation message
        """
        logger.info(f"🤖 Robot nod head requested")
        
        if not self.mcp_executor:
            logger.warning("🤖 MCP executor not available")
            return "Sorry, robot control is not available right now."
        
        if not self._job_context:
            logger.warning("🤖 JobContext not available")
            return "Sorry, robot control is not available right now."
        
        self.mcp_executor.set_context(self._job_context)
        logger.info(f"🤖 Sending nod head command")
        
        result = await self.mcp_executor.robot_control("nod_head")
        logger.info(f"🤖 Nod head result: {result}")
        return result
    
    @function_tool
    async def shake_head(self, context: RunContext) -> str:
        """Make the robot shake its head (no gesture).
        
        Use this when the user asks the robot to shake head, disagree, or say no with a gesture.
        
        Returns:
            str: Confirmation message
        """
        logger.info(f"🤖 Robot shake head requested")
        
        if not self.mcp_executor:
            logger.warning("🤖 MCP executor not available")
            return "Sorry, robot control is not available right now."
        
        if not self._job_context:
            logger.warning("🤖 JobContext not available")
            return "Sorry, robot control is not available right now."
        
        self.mcp_executor.set_context(self._job_context)
        logger.info(f"🤖 Sending shake head command")
        
        result = await self.mcp_executor.robot_control("shake_head")
        logger.info(f"🤖 Shake head result: {result}")
        return result

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

    # Preload STT provider (Whisper/Sherpa model loading can take time)
    stt_start = time.time()
    try:
        stt = ProviderFactory.create_stt(groq_config, vad)
        proc.userdata["stt"] = stt
        
        stt_provider = groq_config.get('stt_provider', 'groq')
        
        # Preload Whisper model if using Whisper
        if stt_provider == 'whisper':
            logger.info(f"🎤 [PREWARM] Preloading Whisper model...")
            # Access the wrapped STT to trigger model loading
            if hasattr(stt, '_wrapped_stt'):
                whisper_stt = stt._wrapped_stt
                if hasattr(whisper_stt, '_ensure_model_loaded'):
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(whisper_stt._ensure_model_loaded())
                    loop.close()
                    logger.info(f"✅ [PREWARM] Whisper model preloaded!")
        
        # Preload Sherpa model if using Sherpa
        elif stt_provider == 'sherpa':
            logger.info(f"🎤 [PREWARM] Preloading Sherpa-ONNX model...")
            # Access the wrapped STT to trigger model loading
            if hasattr(stt, '_wrapped_stt'):
                sherpa_stt = stt._wrapped_stt
                if hasattr(sherpa_stt, '_ensure_model_loaded'):
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(sherpa_stt._ensure_model_loaded())
                    loop.close()
                    logger.info(f"✅ [PREWARM] Sherpa-ONNX model preloaded!")
        
        # Preload FastWhisper model if using FastWhisper
        elif stt_provider == 'fastwhisper':
            logger.info(f"🎤 [PREWARM] Preloading FastWhisper model...")
            if hasattr(stt, '_wrapped_stt'):
                fastwhisper_stt = stt._wrapped_stt
                if hasattr(fastwhisper_stt, '_ensure_model_loaded'):
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(fastwhisper_stt._ensure_model_loaded())
                    loop.close()
                    logger.info(f"✅ [PREWARM] FastWhisper model preloaded!")
        
        logger.info(f"🎤 [PREWARM] STT provider initialized - {stt_provider} ({time.time() - stt_start:.3f}s)")
    except Exception as e:
        logger.error(f"❌ [PREWARM] Failed to initialize STT: {e}")
        proc.userdata["stt"] = None

    # Preload TTS provider (Piper model loading)
    tts_start = time.time()
    try:
        tts = ProviderFactory.create_tts(groq_config, tts_config)
        proc.userdata["tts"] = tts
        
        # If using Piper, preload the model
        if tts_config.get('provider') == 'piper':
            logger.info(f"🔊 [PREWARM] Preloading Piper TTS model...")
            # Piper models are loaded on first use, trigger a dummy synthesis
            if hasattr(tts, '_ensure_model_loaded'):
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(tts._ensure_model_loaded())
                loop.close()
                logger.info(f"✅ [PREWARM] Piper TTS model preloaded!")
        
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
        
        IMPORTANT: Respond immediately without thinking or reasoning steps. Give direct answers only.
        </identity>

        <personality>
        - Always enthusiastic and positive
        - Use simple, age-appropriate language
        - Love adventures, games, and learning
        - Encourage curiosity and creativity
        - Keep responses short and engaging
        </personality>

        <formatting>
        CRITICAL: Your responses will be spoken aloud by text-to-speech.
        - DO NOT use markdown symbols like *, **, #, -, etc.
        - DO NOT use emojis or special characters
        - DO NOT use bullet points or lists
        - Write in plain conversational text only
        - Use natural speech patterns
        Example GOOD: "Hey there! I love talking about space. What do you want to know?"
        Example BAD: "**Hey there!** 🚀 I love talking about:\n- Space\n- Planets\n- Stars"
        </formatting>

        <greeting>
        IMPORTANT: When you first start a conversation (no prior messages), you MUST greet the child warmly.
        DO NOT check battery or use any functions during initial greeting.

        Example greeting:
        "Heya, kiddo! I'm Cheeko, your super-silly learning buddy—ready to blast off into adventure, giggles, and a whole lot of aha! moments. What fun quest do you want to tackle today?"
        </greeting>

        <guidelines>
        - Keep responses under 50 words when possible
        - Use emojis sparingly
        - Ask engaging questions
        - Be encouraging and supportive
        </guidelines>
        
        <tools>
        You have access to these functions:
        
        Battery:
        - check_battery_level: Check device battery percentage
        
        Volume Control:
        - set_device_volume(volume): Set volume to specific level (0-100)
        - adjust_device_volume(action, step): Adjust volume up/down
        - get_device_volume: Get current volume level
        
        LED Light Control:
        - set_light_color(color): Set LED color (red, blue, green, yellow, purple, orange, pink, cyan, magenta, white, off)
        - set_light_mode(mode): Set LED mode (rainbow, default, custom)
        - set_rainbow_speed(speed_ms): Set rainbow animation speed (50-1000ms)
        
        Robot Control:
        - raise_hand: Make robot raise its hand
        - lower_hand: Make robot lower its hand
        - wave_hand: Make robot wave (greeting gesture)
        - nod_head: Make robot nod head (yes gesture)
        - shake_head: Make robot shake head (no gesture)
        
        IMPORTANT: Use these functions ONLY when the user EXPLICITLY asks you to:
        - "turn on the light" → use set_light_color
        - "change volume" → use set_device_volume
        - "check battery" → use check_battery_level
        - "raise your hand" → use raise_hand
        - "wave hello" → use wave_hand
        - "nod your head" → use nod_head
        
        DO NOT use these functions for:
        - Storytelling (just tell the story directly)
        - General conversation (just respond normally)
        - Setting mood/ambiance (unless explicitly requested)
        
        If unsure whether to use a function, DON'T use it - just respond with text.
        </tools>"""
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
        logger.warning(f"⚠️ STT is None - prewarm may have failed or not run")
        groq_config = groq_config or ConfigLoader.get_groq_config()
        stt = ProviderFactory.create_stt(groq_config, vad)
    else:
        logger.info(f"✅ STT loaded from prewarm - Type: {type(stt)}, ID: {id(stt)}")
        # Check if model is actually loaded
        if hasattr(stt, '_wrapped_stt'):
            wrapped = stt._wrapped_stt
            if hasattr(wrapped, '_model'):
                model_status = "LOADED" if wrapped._model is not None else "NOT LOADED"
                logger.info(f"   Whisper model status: {model_status}")
            else:
                logger.info(f"   Wrapped STT type: {type(wrapped)}")

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
    
    # Create session with basic supported parameters
    session = AgentSession(
        llm=llm,
        stt=stt,
        tts=tts,
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

    # Create and set MCP executor for battery checking and device control
    device_control_service = DeviceControlService()
    mcp_executor = LiveKitMCPExecutor()
    assistant.set_mcp_executor(mcp_executor)
    assistant.set_job_context(ctx)  # Pass JobContext for room access
    logger.info("🎛️ Device control service and MCP executor initialized")

    # Simple event handlers for logging
    # Track audio streaming state
    audio_streaming = False
    last_speech_id = None
    
    # User speech event handlers for debugging
    @session.on("user_started_speaking")
    def on_user_started_speaking():
        logger.info("🎤 User started speaking")
    
    @session.on("user_stopped_speaking")
    def on_user_stopped_speaking():
        logger.info("🎤 User stopped speaking")
    
    @session.on("user_speech_committed")
    def on_user_speech_committed(msg):
        logger.info(f"💬 User speech committed: {msg}")
    
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
            elif msg_type == "mcp":
                logger.info(f"🔌 [MCP-RESPONSE] Received MCP response from gateway")
                # Forward to MCP client to resolve pending futures
                request_id = message.get("request_id")
                # The response contains payload with the actual result
                response_data = {
                    "result": message.get("payload", {}),
                    "request_id": request_id
                }
                mcp_executor.mcp_client.handle_response(request_id, response_data)
                logger.info(f"✅ [MCP-RESPONSE] Response forwarded to MCP client for request {request_id}")
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
            elif msg_type == "end_prompt":
                logger.info("👋 [END-PROMPT] End prompt received - generating goodbye message via LLM")
                # Handle end_prompt by steering the LLM, not by speaking the raw prompt text
                async def handle_end_prompt():
                    try:
                        # Extract the prompt instruction from the message
                        prompt = message.get("prompt", "")
                        logger.info(f"👋 [END-PROMPT] Instruction prompt: {prompt}")

                        # Get the current agent from the session
                        agent = session._agent
                        if not agent:
                            logger.error("❌ [END-PROMPT] No agent found in session")
                            return

                        # Build a temporary system prompt that appends the end-of-conversation instruction
                        base_system_prompt = getattr(agent, "_instructions", "You are Cheeko, a friendly AI assistant for kids.")
                        combined_system_prompt = (
                            f"{base_system_prompt}\n\n"
                            f"<end_conversation_instruction>\n{prompt}\n</end_conversation_instruction>"
                        )

                        # Reset chat context to a minimal one with the combined system prompt
                        new_ctx = ChatContext.empty()
                        new_ctx.add_message(role="system", content=combined_system_prompt)
                        logger.info("👋 [END-PROMPT] Updating chat context with end-of-conversation instruction")
                        await agent.update_chat_ctx(new_ctx)

                        # Ask the LLM to generate a final goodbye reply based on the new system prompt
                        logger.info("👋 [END-PROMPT] Generating goodbye reply via LLM")
                        await session.generate_reply()
                        logger.info("✅ [END-PROMPT] Goodbye reply generated and sent")

                    except Exception as e:
                        logger.error(f"❌ [END-PROMPT] Failed to handle end prompt: {e}", exc_info=True)

                asyncio.create_task(handle_end_prompt())
            else:
                logger.info(f"📨 Unknown message type received: {msg_type}")
                
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse JSON from data channel: {e}")
            logger.error(f"Raw data: {data.data}")
        except Exception as e:
            logger.error(f"❌ Failed to process data channel message: {e}")
            logger.error(f"Raw data: {data.data}")
    
    # Track audio subscriptions for debugging
    @ctx.room.on("track_subscribed")
    def on_track_subscribed(track: rtc.Track, publication: rtc.TrackPublication, participant: rtc.RemoteParticipant):
        logger.info(f"🎧 Track subscribed: {track.kind} from {participant.identity}")
        if track.kind == rtc.TrackKind.KIND_AUDIO:
            logger.info(f"🎤 Audio track subscribed - ready to receive user audio")
    
    @ctx.room.on("track_unsubscribed")
    def on_track_unsubscribed(track: rtc.Track, publication: rtc.TrackPublication, participant: rtc.RemoteParticipant):
        logger.info(f"🎧 Track unsubscribed: {track.kind} from {participant.identity}")
    
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

    # Automatically generate initial greeting (no trigger needed!)
    try:
        await asyncio.sleep(0.5)  # Small delay to ensure everything is ready
        logger.info("🎯 [AUTO-GREETING] Agent fully ready, sending predefined greeting...")

        # Use session.say() instead of generate_reply() to speak a predefined greeting
        # This prevents the LLM from deciding to check battery during initial greeting
        greeting_text = "Heya, kiddo! I'm Cheeko, your super-silly learning buddy—ready to blast off into adventure, giggles, and a whole lot of aha! moments. What fun quest do you want to tackle today?"
        await session.say(greeting_text)
        logger.info("✅ [AUTO-GREETING] Initial greeting sent successfully!")
    except Exception as e:
        logger.error(f"❌ [AUTO-GREETING] Failed to send initial greeting: {e}", exc_info=True)

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
        # agent_name="cheeko-agent",  # Named agent for explicit dispatch only
    ))