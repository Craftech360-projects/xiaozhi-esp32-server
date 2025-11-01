import logging
import asyncio
import os
import json
import wave
import tempfile
import numpy as np
import datetime
from dotenv import load_dotenv
from livekit.agents import (
    NOT_GIVEN,
    Agent,
    AgentFalseInterruptionEvent,
    AgentSession,
    JobContext,
    JobProcess,
    AgentStateChangedEvent,
    UserInputTranscribedEvent,
    SpeechCreatedEvent,
    UserStateChangedEvent,
    AgentHandoffEvent,
    MetricsCollectedEvent,
    RoomInputOptions,
    RunContext,
    WorkerOptions,
    function_tool,
    cli,
    metrics,
)
from livekit import rtc
from livekit.plugins import silero
import livekit.plugins.groq as groq
import livekit.plugins.aws as aws
# from livekit.plugins.turn_detector.multilingual import MultilingualModel
from livekit.plugins import noise_cancellation
from custom_silero_vad import create_kids_vad
from livekit.agents.llm import utils as llm_utils

logger = logging.getLogger("agent")

# ========================================
# MONKEY PATCH: Fix LiveKit's args_dict None bug
# ========================================
_original_prepare_function_arguments = llm_utils.prepare_function_arguments

def patched_prepare_function_arguments(*args, **kwargs):
    """
    Patched version that handles None args_dict gracefully.
    This fixes the TypeError: argument of type 'NoneType' is not iterable bug.
    """
    # Log what we're receiving for debugging
    logger.info(f"🔍 prepare_function_arguments: args count={len(args)}, kwargs={list(kwargs.keys())}")

    # Convert args to list for modification
    args_list = list(args)

    # Check and fix args_dict in kwargs
    if 'args_dict' in kwargs:
        if kwargs['args_dict'] is None:
            logger.warning(f"⚠️ Fixed None args_dict in kwargs")
            kwargs['args_dict'] = {}

    # Check and fix args_dict in positional arguments
    # It could be at different positions depending on how it's called
    for i, arg in enumerate(args_list):
        if arg is None:
            logger.warning(f"⚠️ Fixed None at args[{i}], replacing with empty dict")
            args_list[i] = {}

    # Call original function with fixed arguments
    return _original_prepare_function_arguments(*tuple(args_list), **kwargs)

# Apply the patch
llm_utils.prepare_function_arguments = patched_prepare_function_arguments
logger.info("✅ Applied patch for args_dict None bug")

# STT Providers for Buffered Audio Transcription
try:
    import assemblyai as aai
    ASSEMBLYAI_AVAILABLE = True
except ImportError:
    ASSEMBLYAI_AVAILABLE = False
    logger.warning("AssemblyAI not available. Install with: pip install assemblyai")

try:
    from deepgram import DeepgramClient, PrerecordedOptions, FileSource
    DEEPGRAM_AVAILABLE = True
except ImportError:
    DEEPGRAM_AVAILABLE = False
    logger.warning("Deepgram not available. Install with: pip install deepgram-sdk")

load_dotenv(".env")

# ========================================
# Audio Buffer Manager for Kids' Voice
# ========================================
class AudioBufferManager:
    """
    Manages audio buffering for batch STT transcription.
    Buffers audio frames while VAD detects speech, then sends complete audio to STT.
    """

    def __init__(self, sample_rate=16000):
        self.buffer = []
        self.is_recording = False
        self.sample_rate = sample_rate
        self.start_time = None
        self.last_transcript = ""
        logger.info("🎤 AudioBufferManager initialized")

    def start_recording(self):
        """Start buffering audio frames"""
        self.buffer.clear()
        self.is_recording = True
        self.start_time = datetime.datetime.now()
        logger.info("🔴 Started buffering audio for kids' voice...")

    def add_frame(self, audio_data):
        """Add audio frame to buffer"""
        if self.is_recording and audio_data:
            self.buffer.append(audio_data)

    def stop_recording_and_save(self, transcript=""):
        """Stop buffering, save to WAV file, and return complete audio"""
        self.is_recording = False
        self.last_transcript = transcript

        if self.start_time:
            duration = (datetime.datetime.now() - self.start_time).total_seconds()
            logger.info(f"🛑 Stopped buffering. Duration: {duration:.2f}s, Frames: {len(self.buffer)}")

        if not self.buffer:
            logger.warning("⚠️  No audio frames buffered!")
            return None

        # Combine all buffered frames
        try:
            complete_audio = b''.join(self.buffer)
            logger.info(f"✅ Complete audio buffer: {len(complete_audio)} bytes")

            # Save to WAV file for debugging
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # Include milliseconds
            filename = f"D:\\cheekofinal\\xiaozhi-esp32-server\\main\\livekit-server_simple\\captured_audio_{timestamp}.wav"

            if save_audio_as_wav(complete_audio, filename, self.sample_rate):
                # Also save transcript in a companion text file
                txt_filename = filename.replace(".wav", ".txt")
                try:
                    with open(txt_filename, 'w', encoding='utf-8') as f:
                        f.write(f"Timestamp: {timestamp}\n")
                        f.write(f"Duration: {duration:.2f}s\n")
                        f.write(f"Audio bytes: {len(complete_audio)}\n")
                        f.write(f"Sample rate: {self.sample_rate}Hz\n")
                        f.write(f"Transcript: {transcript}\n")
                    logger.info(f"💾 Saved transcript info to {txt_filename}")
                except Exception as e:
                    logger.error(f"❌ Failed to save transcript info: {e}")

            return complete_audio
        except Exception as e:
            logger.error(f"❌ Error combining audio frames: {e}")
            return None

    def is_active(self):
        """Check if currently recording"""
        return self.is_recording


# ========================================
# Audio Format Conversion Utilities
# ========================================
def save_audio_as_wav(audio_bytes, filename, sample_rate=16000, channels=1):
    """
    Convert PCM bytes to WAV file for STT processing.

    Args:
        audio_bytes: Raw PCM audio data as bytes
        filename: Output WAV file path
        sample_rate: Sample rate in Hz (default: 16000)
        channels: Number of audio channels (default: 1 for mono)
    """
    try:
        # Convert bytes to int16 array
        audio_array = np.frombuffer(audio_bytes, dtype=np.int16)

        # Save as WAV
        with wave.open(filename, 'wb') as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_array.tobytes())

        logger.info(f"💾 Saved audio to {filename} ({len(audio_bytes)} bytes, {sample_rate}Hz)")
        return True
    except Exception as e:
        logger.error(f"❌ Error saving WAV file: {e}")
        return False


# ========================================
# STT Transcription Functions
# ========================================
async def transcribe_with_assemblyai(audio_bytes, sample_rate=16000):
    """
    Transcribe audio using AssemblyAI (best for kids' voices).

    Args:
        audio_bytes: Raw PCM audio data
        sample_rate: Sample rate in Hz

    Returns:
        Transcribed text or None if error
    """
    if not ASSEMBLYAI_AVAILABLE:
        logger.error("❌ AssemblyAI not available")
        return None

    try:
        # Configure API key
        api_key = os.getenv("ASSEMBLYAI_API_KEY")
        if not api_key:
            logger.error("❌ ASSEMBLYAI_API_KEY not set in .env")
            return None

        aai.settings.api_key = api_key

        # Save to temporary WAV file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            temp_path = tmp_file.name
            save_audio_as_wav(audio_bytes, temp_path, sample_rate)

        logger.info("🔄 Sending audio to AssemblyAI...")

        # Configure transcription with kids' voice optimizations
        config = aai.TranscriptionConfig(
            language_detection=True,  # Auto-detect language
            speech_model=aai.SpeechModel.best,  # Use best model
            punctuate=True,
            format_text=True,
            filter_profanity=False,  # Don't filter kids' speech
            # Boost common kids' words for better accuracy
            word_boost=[
                "play", "song", "music", "game", "story", "toy",
                "mama", "papa", "please", "thank you", "yes", "no",
                "johnny", "twinkle", "star", "wheels", "bus"
            ],
            boost_param="default"  # Moderate boosting
        )

        # Transcribe
        transcriber = aai.Transcriber()
        transcript = transcriber.transcribe(temp_path, config)

        # Cleanup temp file
        try:
            os.unlink(temp_path)
        except:
            pass

        if transcript.status == aai.TranscriptStatus.error:
            logger.error(f"❌ AssemblyAI error: {transcript.error}")
            return None

        result_text = transcript.text
        logger.info(f"✅ AssemblyAI transcript: '{result_text}'")
        return result_text

    except Exception as e:
        logger.error(f"❌ AssemblyAI transcription error: {e}")
        return None


async def transcribe_with_deepgram(audio_bytes, sample_rate=16000):
    """
    Transcribe audio using Deepgram Nova-3 (alternative for kids' voices).

    Args:
        audio_bytes: Raw PCM audio data
        sample_rate: Sample rate in Hz

    Returns:
        Transcribed text or None if error
    """
    if not DEEPGRAM_AVAILABLE:
        logger.error("❌ Deepgram not available")
        return None

    try:
        # Configure API key
        api_key = os.getenv("DEEPGRAM_API_KEY")
        if not api_key:
            logger.error("❌ DEEPGRAM_API_KEY not set in .env")
            return None

        # Save to temporary WAV file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            temp_path = tmp_file.name
            save_audio_as_wav(audio_bytes, temp_path, sample_rate)

        logger.info("🔄 Sending audio to Deepgram...")

        # Initialize Deepgram client
        deepgram = DeepgramClient(api_key)

        # Read audio file
        with open(temp_path, "rb") as audio_file:
            buffer_data = audio_file.read()

        payload: FileSource = {
            "buffer": buffer_data,
        }

        # Configure options for kids' voices
        options = PrerecordedOptions(
            model="nova-3",  # Latest model
            smart_format=True,
            punctuate=True,
            language="en",
        )

        # Transcribe
        response = deepgram.listen.rest.v("1").transcribe_file(payload, options)

        # Cleanup temp file
        try:
            os.unlink(temp_path)
        except:
            pass

        # Extract transcript
        if response.results and response.results.channels:
            result_text = response.results.channels[0].alternatives[0].transcript
            logger.info(f"✅ Deepgram transcript: '{result_text}'")
            return result_text
        else:
            logger.error("❌ Deepgram: No transcript returned")
            return None

    except Exception as e:
        logger.error(f"❌ Deepgram transcription error: {e}")
        return None


async def transcribe_with_groq_whisper(audio_bytes, sample_rate=16000):
    """
    Transcribe audio using Groq Whisper (already in your stack).

    Args:
        audio_bytes: Raw PCM audio data
        sample_rate: Sample rate in Hz

    Returns:
        Transcribed text or None if error
    """
    try:
        from groq import Groq

        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            logger.error("❌ GROQ_API_KEY not set in .env")
            return None

        client = Groq(api_key=api_key)

        # Save to temporary WAV file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            temp_path = tmp_file.name
            save_audio_as_wav(audio_bytes, temp_path, sample_rate)

        logger.info("🔄 Sending audio to Groq Whisper...")

        # Transcribe with Whisper
        with open(temp_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                file=(temp_path, audio_file.read()),
                model="whisper-large-v3-turbo",
                response_format="text",
                language="en"
            )

        # Cleanup temp file
        try:
            os.unlink(temp_path)
        except:
            pass

        result_text = transcription if isinstance(transcription, str) else transcription.text
        logger.info(f"✅ Groq Whisper transcript: '{result_text}'")
        return result_text

    except Exception as e:
        logger.error(f"❌ Groq Whisper transcription error: {e}")
        return None


async def transcribe_audio(audio_bytes, sample_rate=16000, provider="assemblyai"):
    """
    Main transcription function that routes to the selected STT provider.

    Args:
        audio_bytes: Raw PCM audio data
        sample_rate: Sample rate in Hz
        provider: STT provider to use ("assemblyai", "deepgram", "groq", "aws")

    Returns:
        Transcribed text or None if error
    """
    if not audio_bytes:
        logger.error("❌ No audio data to transcribe")
        return None

    logger.info(f"🎯 Using STT provider: {provider}")

    if provider == "assemblyai":
        return await transcribe_with_assemblyai(audio_bytes, sample_rate)
    elif provider == "deepgram":
        return await transcribe_with_deepgram(audio_bytes, sample_rate)
    elif provider == "groq":
        return await transcribe_with_groq_whisper(audio_bytes, sample_rate)
    else:
        logger.error(f"❌ Unknown STT provider: {provider}")
        return None


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""You are a helpful voice AI assistant for kids.
            You provide short, friendly responses to user questions.
            Your responses are concise, natural, and conversational without complex formatting or symbols.

            IMPORTANT:
            - Only use function tools when the user explicitly asks for something (weather, time, search, music, etc.)
            - For simple greetings or questions, respond directly without calling functions
            - If a user asks "are you working" or "can you hear me", just respond naturally
            - Keep responses short and friendly
            - Never call multiple functions unless necessary""",
        )

    @function_tool
    async def lookup_weather(self, context: RunContext, location: str = "unknown"):
        """
        Get the weather for a specific location.

        Args:
            location: The city or location name (e.g., "New York", "London")
        """
        logger.info(f"Looking up weather for {location}")
        if not location or location == "unknown":
            return "Please tell me which location you'd like to know the weather for."
        return f"The weather in {location} is sunny with a temperature of 70 degrees."

    @function_tool
    async def brave_search(self, context: RunContext, query: str = ""):
        """
        Search for information on the internet.

        Args:
            query: What to search for
        """
        logger.info(f"Searching for: {query}")
        if not query:
            return "Please tell me what you'd like me to search for."
        return f"I found some information about {query}. Here's what I can tell you..."

    @function_tool
    async def play_music(self, context: RunContext, song: str = "", artist: str = ""):
        """
        Play a song by name and optionally artist.

        Args:
            song: The name of the song to play
            artist: The artist name (optional)
        """
        logger.info(f"Playing music: song='{song}', artist='{artist}'")
        if not song:
            return "Please tell me which song you'd like me to play."

        if artist:
            return f"I'd love to play {song} by {artist} for you, but I don't have music playback capability right now."
        return f"I'd love to play {song} for you, but I don't have music playback capability right now."

    @function_tool
    async def play_song(self, context: RunContext, title: str = ""):
        """
        Play a song by title.

        Args:
            title: The title of the song to play
        """
        logger.info(f"Playing song: {title}")
        if not title:
            return "Please tell me which song you'd like me to play."
        return f"I'd love to play {title} for you, but I don't have music playback capability right now."

    @function_tool
    async def brute_force_search(self, context: RunContext, query: str = ""):
        """
        Search comprehensively for information.

        Args:
            query: What to search for
        """
        logger.info(f"Brute force searching for: {query}")
        if not query:
            return "Please tell me what you'd like me to search for."
        return f"I searched for {query} and found some interesting information. What would you like to know more about?"

    @function_tool
    async def web_search(self, context: RunContext, query: str = ""):
        """
        Search the web for information.

        Args:
            query: What to search for on the web
        """
        logger.info(f"Web searching for: {query}")
        if not query:
            return "Please tell me what you'd like me to search for."
        return f"I found some information about {query} on the web. Here's what I can tell you..."

    @function_tool
    async def get_current_time(self, context: RunContext):
        """
        Get the current time.

        No arguments needed.
        """
        logger.info("Getting current time")
        now = datetime.datetime.now()
        return f"The current time is {now.strftime('%I:%M %p')}"

    @function_tool
    async def tell_joke(self, context: RunContext, topic: str = "general"):
        """
        Tell a joke about a specific topic.

        Args:
            topic: The topic for the joke (default: general)
        """
        logger.info(f"Telling a joke about: {topic}")
        return "Why don't scientists trust atoms? Because they make up everything!"

    @function_tool
    async def calculate(self, context: RunContext, expression: str = ""):
        """
        Calculate a mathematical expression.

        Args:
            expression: The math expression to calculate (e.g., "2 + 2", "10 * 5")
        """
        logger.info(f"Calculating: {expression}")
        if not expression:
            return "Please tell me what you'd like me to calculate."

        try:
            # Simple safe calculation (you might want to use a proper math parser)
            result = eval(expression.replace("^", "**"))  # Basic math only
            return f"The answer is {result}"
        except Exception as e:
            logger.error(f"Calculation error: {e}")
            return "I couldn't calculate that. Please try a simpler math expression."

def prewarm(proc: JobProcess):
    # Use kids-optimized VAD instead of default Silero VAD
    try:
        logger.info("🎤 Initializing WHISPER-LEVEL kids VAD...")
        proc.userdata["vad"] = create_kids_vad()
        logger.info("✅ Kids-optimized Silero VAD loaded successfully!")
        logger.info("🔍 VAD will now detect even the softest children's voices")
    except Exception as e:
        logger.warning(f"❌ Failed to load custom VAD, falling back to default: {e}")
        proc.userdata["vad"] = silero.VAD.load()

async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}
    print(f"Starting agent in room: {ctx.room.name}")

    # ========================================
    # BUFFERED AUDIO APPROACH FOR KIDS' VOICES
    # ========================================
    # Initialize audio buffer manager
    audio_buffer = AudioBufferManager(sample_rate=16000)

    # Get STT provider from env (default: assemblyai)
    stt_provider = os.getenv("STT_PROVIDER", "assemblyai")
    logger.info(f"🎯 Selected STT Provider: {stt_provider}")

    try:
        # Set up voice AI pipeline WITH temporary STT for audio capture
        # We'll replace the transcriptions with our buffered approach
        logger.info("Initializing AgentSession with buffered audio...")
        session = AgentSession(
            llm=groq.LLM(model="llama-3.1-8b-instant"),
            stt=groq.STT(),  # ← Keep enabled so LiveKit captures audio, we'll replace transcriptions
            tts=groq.TTS(),  # Use default TTS model
            # turn_detection=MultilingualModel(),  # Temporarily disabled to fix timeout
            vad=ctx.proc.userdata["vad"],
            preemptive_generation=False,
        )
        logger.info("✅ AgentSession initialized successfully (BUFFERED AUDIO MODE)")
        logger.info(f"🤖 LLM Model: {session.llm}")
        logger.info(f"🎤 STT Provider: {stt_provider} (batch mode - will override Groq streaming)")
        logger.info(f"🔊 TTS Provider: Groq")
        logger.info(f"📦 Audio Buffering: ENABLED")
    except Exception as e:
        logger.error(f"Failed to initialize AgentSession: {e}")
        raise

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

    usage_collector = metrics.UsageCollector()
    
    # Track LLM interactions
    @session.on("llm_response")
    def _on_llm_response(response):
        logger.info(f"🤖 LLM Response received: {response}")
    
    # Track when agent generates replies
    async def track_agent_reply(user_msg: str):
        logger.info(f"🔄 Processing user message: '{user_msg}'")
        try:
            # This will be called when the agent processes user input
            pass
        except Exception as e:
            logger.error(f"❌ Error processing user message: {e}")

    # @session.on("metrics_collected")
    # def _on_metrics_collected(ev: MetricsCollectedEvent):
    #     metrics.log_metrics(ev.metrics)
    #     usage_collector.collect(ev.metrics)
    #     payload = json.dumps({
    #         "type": "metrics_collected",
    #         "data": ev.metrics.dict()
    #     })
    #     asyncio.create_task(ctx.room.local_participant.publish_data(payload.encode("utf-8"), reliable=True))
    #     logger.info("Sent metrics_collected via data channel")

    @session.on("agent_state_changed")
    def _on_agent_state_changed(ev: AgentStateChangedEvent):
        logger.info(f"Agent state changed: {ev}")

        # Log detailed state transitions
        if ev.new_state == "thinking":
            logger.info("🧠 AGENT THINKING: Processing user input with LLM...")
        elif ev.new_state == "speaking":
            logger.info("🗣️ AGENT SPEAKING: Converting LLM response to speech...")
        elif ev.new_state == "listening":
            logger.info("👂 AGENT LISTENING: Ready for user input...")

        payload = json.dumps({
            "type": "agent_state_changed",
            "data": ev.dict()
        })
        asyncio.create_task(ctx.room.local_participant.publish_data(payload.encode("utf-8"), reliable=True))
        logger.info("Sent agent_state_changed via data channel")

    @session.on("user_state_changed")
    def _on_user_state_changed(ev: UserStateChangedEvent):
        logger.info(f"👤 User state changed: {ev.new_state}")

        # Control audio buffering based on user speaking state
        if ev.new_state == "speaking":
            logger.info("🎤 User started speaking - starting audio buffer...")
            if not audio_buffer.is_active():
                audio_buffer.start_recording()
        elif ev.new_state == "listening":
            logger.info("🔇 User stopped speaking")
            # Audio will be saved when final transcript arrives

    # ========================================
    # BUFFERED AUDIO EVENT HANDLERS
    # ========================================
    # Note: We need to hook into the actual agent state changes since
    # user_started_speaking/stopped_speaking events don't exist

    # Intercept streaming STT and log transcriptions
    @session.on("user_input_transcribed")
    def _on_user_input_transcribed(ev: UserInputTranscribedEvent):
        """
        This captures Groq's streaming STT output.
        We also trigger audio buffer saving when final transcript is received.
        """
        # Log all transcripts (partial and final)
        if ev.is_final:
            logger.info(f"✅ USER SAID (Groq STT): '{ev.transcript}'")
            logger.info(f"   Language: {ev.language}, Confidence: final")

            # Save the buffered audio with transcript
            logger.info("💾 Saving captured audio to WAV file...")
            audio_buffer.stop_recording_and_save(transcript=ev.transcript)

            # Publish to MQTT
            payload = json.dumps({
                "type": "user_input_transcribed",
                "data": ev.dict()
            })
            asyncio.create_task(ctx.room.local_participant.publish_data(payload.encode("utf-8"), reliable=True))
        else:
            # Log partial transcripts for debugging
            logger.debug(f"📝 Partial: '{ev.transcript}'")

    @session.on("speech_created")
    def _on_speech_created(ev: SpeechCreatedEvent):
        # Log the LLM response that's being converted to speech
        logger.info(f"🗣️ LLM RESPONSE → TTS: Speech created")
        
        # Try to log speech details safely
        if hasattr(ev, 'id'):
            logger.info(f"📝 Speech ID: {ev.id}")
        if hasattr(ev, 'text') and ev.text:
            logger.info(f"💬 LLM Generated Text: '{ev.text}'")
        elif hasattr(ev, 'content') and ev.content:
            logger.info(f"💬 LLM Generated Content: '{ev.content}'")
        
        # Log all available attributes for debugging
        logger.debug(f"Speech event attributes: {dir(ev)}")
        
        payload = json.dumps({
            "type": "speech_created",
            "data": ev.dict()
        })
        asyncio.create_task(ctx.room.local_participant.publish_data(payload.encode("utf-8"), reliable=True))
        logger.info("Sent speech_created via data channel")

        
    async def log_usage():
        summary = usage_collector.get_summary()
        logger.info(f"Usage: {summary}")
        payload = json.dumps({
            "type": "usage_summary",
            "summary": summary.llm_prompt_tokens
        })
        # session.local_participant.publishData(payload.encode("utf-8"), reliable=True)
        logger.info("Sent usage_summary via data channel")

    ctx.add_shutdown_callback(log_usage)

    # ========================================
    # RAW AUDIO CAPTURE FROM LIVEKIT TRACK
    # ========================================
    # Subscribe to track events to capture raw PCM audio
    @ctx.room.on("track_subscribed")
    def on_track_subscribed(
        track: rtc.Track,
        publication: rtc.RemoteTrackPublication,
        participant: rtc.RemoteParticipant,
    ):
        logger.info(f"🎵 Track subscribed: {track.kind} from {participant.identity}")

        if track.kind == rtc.TrackKind.KIND_AUDIO:
            logger.info("🎤 Audio track detected - setting up frame capture...")

            # Create audio stream from track
            audio_stream = rtc.AudioStream(track)

            # Create async task to capture frames
            # Recording will be controlled by user_state_changed events
            async def capture_audio_frames():
                logger.info("🔴 Started audio frame capture loop (waiting for user to speak)...")
                frame_count = 0
                total_frames = 0
                detected_sample_rate = None

                try:
                    async for event in audio_stream:
                        frame = event.frame
                        total_frames += 1

                        # Detect sample rate from first frame
                        if detected_sample_rate is None:
                            detected_sample_rate = frame.sample_rate
                            audio_buffer.sample_rate = detected_sample_rate
                            logger.info(f"🎵 Detected audio sample rate: {detected_sample_rate}Hz")
                            logger.info(f"🎵 Frame details: channels={frame.num_channels}, samples_per_channel={frame.samples_per_channel}")

                        # Only buffer if we're actively recording (user is speaking)
                        if audio_buffer.is_active():
                            try:
                                # Get raw PCM data from frame
                                # frame.data is memoryview of int16 samples
                                pcm_data = bytes(frame.data)

                                # Add to buffer
                                audio_buffer.add_frame(pcm_data)
                                frame_count += 1

                                if frame_count == 1:
                                    logger.info(f"📊 First buffered frame: {len(pcm_data)} bytes, rate={detected_sample_rate}Hz")
                                elif frame_count % 100 == 0:  # Log every 100 frames
                                    logger.debug(f"📊 Buffered {frame_count} frames, {len(pcm_data)} bytes/frame")

                            except Exception as e:
                                logger.error(f"❌ Error processing audio frame: {e}")

                except Exception as e:
                    logger.error(f"❌ Error in audio capture loop: {e}")
                finally:
                    logger.info(f"🛑 Audio capture ended. Buffered: {frame_count}, Total received: {total_frames}")

            # Start the capture task
            asyncio.create_task(capture_audio_frames())

    logger.info("🎧 Starting VAD monitoring for kids' voices...")
    await session.start(
        agent=Assistant(),
        room=ctx.room,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )
    logger.info("🔊 VAD is now actively listening for voice activity!")
    await ctx.connect()

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))