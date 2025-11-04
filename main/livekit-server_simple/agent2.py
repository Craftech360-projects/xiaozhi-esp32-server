import os
from dotenv import load_dotenv
from livekit.plugins import ultravox
from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import noise_cancellation, silero, google
from google.genai import types


load_dotenv(".env.local")

# --- ADD THIS LINE FOR TESTING ---
print(f"DEBUG: ULTRAVOX_API_KEY is loaded: {(os.getenv('ULTRAVOX_API_KEY'))}")
# ---------------------------------
class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""You are a helpful voice AI assistant.
            You eagerly assist users with their questions by providing information from your extensive knowledge.
            Your responses are concise, to the point, and without any complex formatting or punctuation including emojis, asterisks, or other symbols.
            You are curious, friendly, and have a sense of humor.""",
        )


async def entrypoint(ctx: agents.JobContext):
    
    session = AgentSession(
        # llm=google.realtime.RealtimeModel(
        #     model="gemini-2.5-flash-native-audio-preview-09-2025",
        #     _gemini_tools=[types.GoogleSearch()],
        # ),
         llm=ultravox.realtime.RealtimeModel(),
        # vad=silero.VAD.load(
        #     activation_threshold=0.5,      # Adjusted threshold (default is 0.5)
        #     min_speech_duration=0.1,      # Minimum duration to consider as speech
        #     min_silence_duration=0.5,      # Wait 1.5 seconds of silence before ending
        #     prefix_padding_duration=0.1,   # Padding before speech to avoid cutting off start
        #     max_buffered_speech=60.0,      # Allow up to 60 seconds of continuous speech
        # ),
        # Explicitly disable the turn detection to stop the SDK from loading a default
        turn_detection=None, 
       
    )

    await session.start(
        room=ctx.room,
        agent=Assistant(),
        room_input_options=RoomInputOptions(
            # For telephony applications, use `BVCTelephony` instead for best results
            noise_cancellation=noise_cancellation.BVC(), 
        ),
    )

    await session.generate_reply(
        instructions="Greet the user and offer your assistance.",

        allow_interruptions=False
    )


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))