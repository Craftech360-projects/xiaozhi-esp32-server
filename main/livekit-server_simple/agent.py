import logging
import asyncio
import os
import json
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
from livekit.plugins import silero
import livekit.plugins.groq as groq
import livekit.plugins.aws as aws
# from livekit.plugins.turn_detector.multilingual import MultilingualModel
from livekit.plugins import noise_cancellation
from custom_silero_vad import create_kids_vad

logger = logging.getLogger("agent")

load_dotenv(".env")

class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""You are a helpful voice AI assistant.
            You eagerly assist users with their questions by providing information from your extensive knowledge.
            Your responses are concise, to the point, and without any complex formatting or punctuation including emojis, asterisks, or other symbols.
            You are curious, friendly, and have a sense of humor.""",
        )

    @function_tool
    async def lookup_weather(self, context: RunContext, location: str):
        logger.info(f"Looking up weather for {location}")
        return "sunny with a temperature of 70 degrees."
    
    @function_tool
    async def brave_search(self, context: RunContext, query: str):
        logger.info(f"Searching for: {query}")
        return f"I found some information about {query}. Here's what I can tell you..."
    
    @function_tool
    async def play_music(self, context: RunContext, song: str = "", artist: str = ""):
        logger.info(f"Playing music: {song} by {artist}")
        return f"I'd love to play {song} by {artist} for you, but I don't have music playback capability right now. You can try asking a music app or device to play it!"
    
    @function_tool
    async def play_song(self, context: RunContext, title: str):
        logger.info(f"Playing song: {title}")
        return f"I'd love to play {title} for you, but I don't have music playback capability right now. You can try asking a music app or device to play it!"
    
    @function_tool
    async def brute_force_search(self, context: RunContext, query: str):
        logger.info(f"Brute force searching for: {query}")
        return f"I searched for {query} and found some interesting information. What would you like to know more about?"
    
    @function_tool
    async def web_search(self, context: RunContext, query: str):
        logger.info(f"Web searching for: {query}")
        return f"I found some information about {query} on the web. Here's what I can tell you..."
    
    @function_tool
    async def get_current_time(self, context: RunContext):
        logger.info("Getting current time")
        import datetime
        now = datetime.datetime.now()
        return f"The current time is {now.strftime('%I:%M %p')}"
    
    @function_tool
    async def tell_joke(self, context: RunContext, topic: str = "general"):
        logger.info(f"Telling a joke about: {topic}")
        return "Why don't scientists trust atoms? Because they make up everything!"
    
    @function_tool
    async def calculate(self, context: RunContext, expression: str):
        logger.info(f"Calculating: {expression}")
        try:
            # Simple safe calculation (you might want to use a proper math parser)
            result = eval(expression.replace("^", "**"))  # Basic math only
            return f"The answer is {result}"
        except:
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

    try:
        # Set up voice AI pipeline
        logger.info("Initializing AgentSession...")
        session = AgentSession(
            llm=groq.LLM(model="llama-3.1-8b-instant"),
            stt=aws.STT(
                language="en-IN",  # US English for better kids' voice recognition
                region="us-east-1",  # AWS region from your .env
                sample_rate=16000,   # Match your VAD sample rate
            ),
            tts=groq.TTS(),  # Use default TTS model
            # turn_detection=MultilingualModel(),  # Temporarily disabled to fix timeout
            vad=ctx.proc.userdata["vad"],
            preemptive_generation=False,
        )
        logger.info("AgentSession initialized successfully")
        logger.info(f"🤖 LLM Model: {session.llm}")
        logger.info(f"🎤 STT Provider: AWS Transcribe (en-US)")
        logger.info(f"🔊 TTS Provider: Groq")
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

    @session.on("user_input_transcribed")
    def _on_user_input_transcribed(ev: UserInputTranscribedEvent):
        logger.info(f"User said: {ev}")
        
        # Log when we receive final transcripts that will be sent to LLM
        if ev.is_final:
            logger.info(f"🧠 FINAL TRANSCRIPT → LLM: '{ev.transcript}' (language: {ev.language})")
        else:
            logger.debug(f"📝 Partial transcript: '{ev.transcript}'")
            
        payload = json.dumps({
            "type": "user_input_transcribed",
            "data": ev.dict()
        })
        asyncio.create_task(ctx.room.local_participant.publish_data(payload.encode("utf-8"), reliable=True))
        logger.info("Sent user_input_transcribed via data channel")

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