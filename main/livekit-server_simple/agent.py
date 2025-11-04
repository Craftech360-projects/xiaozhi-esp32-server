from dotenv import load_dotenv
from livekit.plugins import groq
from livekit import agents, rtc
from livekit.agents import AgentSession, Agent, WorkerOptions, cli
from livekit.plugins import silero
from livekit.plugins import aws
from livekit.plugins import deepgram
from livekit.plugins import google
from google.genai.types import Modality
from livekit.agents.utils.codecs import AudioStreamDecoder
import asyncio
load_dotenv(".env")


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""You are 'Cheeko' voice AI assistant.
            You eagerly assist users with their questions by providing information from your extensive knowledge.
            Your responses are concise, to the point, and without any complex formatting or punctuation including emojis, asterisks, or other symbols.
            You are curious, friendly, and have a sense of humor.""",
        )


async def entrypoint(ctx: agents.JobContext):
    # Connect to the room first
    await ctx.connect()
    
    # NEW: Setup audio source and decoder for Opus data channel
    audio_source = rtc.AudioSource(16000, 1)  # 16kHz mono
    opus_decoder = None
    opus_buffer = bytearray()

    # Publish audio track from our audio source
    track = rtc.LocalAudioTrack.create_audio_track("microphone", audio_source)
    await ctx.room.local_participant.publish_track(track, rtc.TrackPublishOptions(source=rtc.TrackSource.SOURCE_MICROPHONE))
    print("✅ [OPUS] Published audio track from custom source")

    # NEW: Listen for Opus data on 'audio/opus' topic
    @ctx.room.on("data_received")
    def on_data_received(data: rtc.DataPacket):
        # Create async task for the actual processing
        asyncio.create_task(process_opus_data(data))

    async def process_opus_data(data: rtc.DataPacket):
        nonlocal opus_decoder, opus_buffer

        # Only process audio/opus topic
        if data.topic != "audio/opus":
            return

        try:
            # Initialize decoder if not already created
            if opus_decoder is None:
                opus_decoder = AudioStreamDecoder(sample_rate=16000, num_channels=1)
                print("✅ [OPUS] AudioStreamDecoder initialized for 16kHz mono")

            # Push Opus data to decoder
            opus_decoder.push(bytes(data.data))

            # Decode and push frames to audio source
            async for audio_frame in opus_decoder:
                # Capture decoded PCM frame to audio source
                await audio_source.capture_frame(audio_frame)
                print(f"🎵 [OPUS] Decoded and captured frame: {len(audio_frame.data)} samples")

        except Exception as e:
            print(f"❌ [OPUS] Error decoding: {e}")

    session = AgentSession(
        # stt=aws.STT(
        #     region="us-east-1",
        #     language="en-US",
        #     enable_partial_results_stabilization=True,
        #     partial_results_stability="high",
        # ),

        stt=deepgram.STT(
            model="nova-3",
            language="en-US",
            endpointing_ms=3000,  # 3 seconds of silence before finalizing
            interim_results=True,
            punctuate=True,
            smart_format=True,
            filler_words=True,
        ),
        llm=groq.LLM(model="llama-3.1-8b-instant"),
        tts=groq.TTS(),
        vad=silero.VAD.load(),
        
        # vad=silero.VAD.load(
        #     activation_threshold=0.5,      # Adjusted threshold (default is 0.5)
        #     min_speech_duration=0.1,      # Minimum duration to consider as speech
        #     min_silence_duration=0.5,      # Wait 1.5 seconds of silence before ending
        #     prefix_padding_duration=0.1,   # Padding before speech to avoid cutting off start
        #     max_buffered_speech=60.0,      # Allow up to 60 seconds of continuous speech
        # ),
    )



    # session = AgentSession(
    #     llm=google.realtime.RealtimeModel(modalities=[Modality.TEXT]),
    #      tts=groq.TTS(),
    # )
    await session.start(
        room=ctx.room,
        agent=Assistant(),
    )

    await session.generate_reply(
        instructions="Greet the user and offer your assistance."
    )


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint,num_idle_processes=2,  # Disable process pooling to avoid initialization issues
        initialize_process_timeout=120.0,  # Increase timeout to 120 seconds for heavy model loading
        job_memory_warn_mb=2000,))