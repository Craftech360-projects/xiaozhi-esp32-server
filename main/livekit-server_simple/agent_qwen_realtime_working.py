#!/usr/bin/env python3
"""
LiveKit Agent with Working Qwen Realtime Integration
Based on the successful Gradio realtime implementation
"""
import os
import asyncio
import json
import base64
import secrets
import numpy as np
from dotenv import load_dotenv
from livekit import agents, rtc
from livekit.agents import RoomInputOptions
from livekit.plugins import silero
from websockets.asyncio.client import connect

load_dotenv(".env.local")

# Qwen Realtime Configuration (same as working Gradio version)
API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
# Use international endpoint that's proven to work
API_URL = "wss://dashscope-intl.aliyuncs.com/api-ws/v1/realtime?model=qwen3-omni-flash-realtime"

VOICES = {
    "芊悦": "Cherry",
    "晨煦": "Ethan", 
    "程川": "Eric",
    "甜茶": "Ryan",
    "晓东": "Dylan",
    "李彼得": "Peter",
    "阿珍": "Jada",
    "晴儿": "Sunny",
    "詹妮弗": "Jennifer",
    "卡捷琳娜": "Katerina",
    "老李": "Li",
    "墨讲师": "Elias",
    "秦川": "Marcus",
    "阿清": "Kiki",
    "阿强": "Rocky",
    "阿杰": "Roy",
}

headers = {"Authorization": f"Bearer {API_KEY}"}

class QwenRealtimeHandler:
    """Handles Qwen realtime WebSocket connection"""

    def __init__(self, voice="Cherry"):
        self.voice = voice
        self.connection = None
        self.audio_queue = asyncio.Queue()
        self.transcript_queue = asyncio.Queue()
        self.running = False
        self.input_buffer = b""
        self.send_task = None

    @staticmethod
    def msg_id() -> str:
        return f"event_{secrets.token_hex(10)}"

    async def connect(self):
        """Connect to Qwen realtime API"""
        try:
            print(f"🔗 Connecting to Qwen realtime API...")
            self.connection = await connect(API_URL, additional_headers=headers)

            # Send session configuration (same as working Gradio version)
            session_config = {
                "event_id": self.msg_id(),
                "type": "session.update",
                "session": {
                    "modalities": ["text", "audio"],
                    "voice": self.voice,
                    "input_audio_format": "pcm16",
                    "output_audio_format": "pcm16",
                },
            }

            await self.connection.send(json.dumps(session_config))
            print(f"✅ Connected to Qwen with voice: {self.voice}")

            # Start listening for events
            self.running = True
            asyncio.create_task(self._listen_events())

            return True

        except Exception as e:
            print(f"❌ Failed to connect to Qwen: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def _listen_events(self):
        """Listen for Qwen realtime events"""
        try:
            async for data in self.connection:
                if not self.running:
                    break

                event = json.loads(data)
                if "type" not in event:
                    continue

                event_type = event["type"]
                print(f"📨 Qwen event: {event_type}")

                if event_type == "input_audio_buffer.speech_started":
                    print("🎤 Speech started - clearing output queue")
                    # Clear any pending audio when user starts speaking
                    while not self.audio_queue.empty():
                        try:
                            self.audio_queue.get_nowait()
                        except:
                            break

                elif event_type == "conversation.item.input_audio_transcription.completed":
                    transcript = event.get("transcript", "")
                    if transcript:
                        await self.transcript_queue.put(("user", transcript))
                        print(f"👤 User said: {transcript}")

                elif event_type == "response.audio_transcript.done":
                    transcript = event.get("transcript", "")
                    if transcript:
                        await self.transcript_queue.put(("assistant", transcript))
                        print(f"🤖 Qwen said: {transcript}")

                elif event_type == "response.audio.delta":
                    audio_b64 = event.get("delta", "")
                    if audio_b64:
                        audio_data = base64.b64decode(audio_b64)
                        # Qwen sends PCM16 at 24kHz
                        await self.audio_queue.put(audio_data)

        except Exception as e:
            print(f"❌ Error listening to Qwen events: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.running = False

    async def send_audio(self, audio_frame: rtc.AudioFrame):
        """Send audio frame to Qwen"""
        if not self.connection or not self.running:
            return

        try:
            # Convert audio frame to PCM16 format
            # Qwen expects 16kHz PCM16 input
            audio_data = audio_frame.data

            # Send to Qwen
            audio_b64 = base64.b64encode(audio_data).decode("utf-8")

            message = {
                "event_id": self.msg_id(),
                "type": "input_audio_buffer.append",
                "audio": audio_b64,
            }

            await self.connection.send(json.dumps(message))
            print(f"🎤 Sent {len(audio_data)} bytes of audio to Qwen")

        except Exception as e:
            print(f"❌ Error sending audio to Qwen: {e}")

    async def get_audio_response(self):
        """Get audio response from Qwen (non-blocking)"""
        try:
            return await asyncio.wait_for(self.audio_queue.get(), timeout=0.001)
        except asyncio.TimeoutError:
            return None

    async def get_transcript(self):
        """Get transcript from Qwen (non-blocking)"""
        try:
            return await asyncio.wait_for(self.transcript_queue.get(), timeout=0.001)
        except asyncio.TimeoutError:
            return None

    async def disconnect(self):
        """Disconnect from Qwen"""
        self.running = False
        if self.connection:
            await self.connection.close()
            self.connection = None
        print("🔌 Disconnected from Qwen")

async def entrypoint(ctx: agents.JobContext):
    """Agent entrypoint - handles LiveKit room connection"""
    print("=" * 60)
    print("🎤 QWEN REALTIME LIVEKIT AGENT")
    print("=" * 60)

    if not API_KEY:
        print("❌ DASHSCOPE_API_KEY not found in environment")
        return

    print(f"🔑 API Key loaded: {API_KEY[:20]}...")
    print(f"🌐 API URL: {API_URL}")
    print(f"🎵 Available voices: {list(VOICES.keys())}")

    # Connect to the LiveKit room first
    print("🔗 Connecting to LiveKit room...")
    await ctx.connect()
    print("✅ Connected to LiveKit room")

    # Initialize Qwen handler
    qwen = QwenRealtimeHandler(voice="Cherry")
    if not await qwen.connect():
        print("❌ Failed to connect to Qwen")
        return

    # Create audio source for Qwen output (24kHz mono PCM16)
    audio_source = rtc.AudioSource(24000, 1)
    audio_track = rtc.LocalAudioTrack.create_audio_track("qwen-voice", audio_source)

    # Publish the audio track
    audio_options = rtc.TrackPublishOptions()
    audio_options.source = rtc.TrackSource.SOURCE_MICROPHONE
    await ctx.room.local_participant.publish_track(audio_track, audio_options)
    print("✅ Published Qwen audio track")

    # Track for storing the remote audio stream
    remote_audio_stream = None
    audio_resampler = rtc.AudioResampler(input_rate=48000, output_rate=16000, num_channels=1)

    # Counter for audio frames
    audio_frame_count = 0

    @ctx.room.on("participant_connected")
    def on_participant_connected(participant: rtc.RemoteParticipant):
        """Handle participant connection"""
        print(f"👋 Participant connected: {participant.identity}")
        print(f"   - Participant SID: {participant.sid}")

    @ctx.room.on("track_published")
    def on_track_published(
        publication: rtc.RemoteTrackPublication,
        participant: rtc.RemoteParticipant,
    ):
        """Handle track publication"""
        print(f"📢 Track published: {publication.kind} from {participant.identity}")
        print(f"   - Track SID: {publication.sid}")
        print(f"   - Track subscribed: {publication.subscribed}")

    @ctx.room.on("track_subscribed")
    def on_track_subscribed(
        track: rtc.Track,
        publication: rtc.RemoteTrackPublication,
        participant: rtc.RemoteParticipant,
    ):
        """Handle new track subscription"""
        nonlocal remote_audio_stream

        print(f"📥 Track subscribed: {track.kind} from {participant.identity}")
        print(f"   - Track SID: {track.sid}")

        if track.kind == rtc.TrackKind.KIND_AUDIO:
            print("🎤 Audio track subscribed - starting stream")
            remote_audio_stream = rtc.AudioStream(track)

            # Start task to process incoming audio
            asyncio.create_task(process_participant_audio(remote_audio_stream, qwen, audio_resampler))

    async def process_participant_audio(stream: rtc.AudioStream, handler: QwenRealtimeHandler, resampler: rtc.AudioResampler):
        """Process incoming audio from participant and send to Qwen"""
        nonlocal audio_frame_count
        print("🎧 Processing participant audio stream...")
        try:
            async for event in stream:
                audio_frame_count += 1
                if audio_frame_count % 100 == 0:  # Log every 100 frames
                    print(f"🔊 Received audio frame #{audio_frame_count} from client")
                    print(f"   - Sample rate: {event.frame.sample_rate}")
                    print(f"   - Channels: {event.frame.num_channels}")
                    print(f"   - Samples: {event.frame.samples_per_channel}")

                # Resample from 48kHz (LiveKit default) to 16kHz (Qwen input)
                resampled_frames = resampler.push(event.frame)

                for frame in resampled_frames:
                    # Send to Qwen
                    await handler.send_audio(frame)

        except Exception as e:
            print(f"❌ Error processing participant audio: {e}")
            import traceback
            traceback.print_exc()

    # Check for existing participants and subscribe to their tracks
    print(f"🔍 Checking for existing participants...")
    for participant in ctx.room.remote_participants.values():
        print(f"   - Found participant: {participant.identity}")
        for publication in participant.track_publications.values():
            print(f"     - Track: {publication.kind}, subscribed: {publication.subscribed}")
            if publication.kind == rtc.TrackKind.KIND_AUDIO and publication.track:
                print("     - Subscribing to existing audio track")
                remote_audio_stream = rtc.AudioStream(publication.track)
                asyncio.create_task(process_participant_audio(remote_audio_stream, qwen, audio_resampler))

    # Main loop - play Qwen responses
    print("🔄 Starting main audio playback loop...")
    qwen_audio_count = 0
    try:
        while True:
            # Get audio from Qwen
            audio_data = await qwen.get_audio_response()
            if audio_data is not None:
                qwen_audio_count += 1
                print(f"🔊 Received audio response #{qwen_audio_count} from Qwen ({len(audio_data)} bytes)")

                # Qwen sends PCM16 bytes at 24kHz
                # Convert bytes to int16 array
                audio_array = np.frombuffer(audio_data, dtype=np.int16)

                # Create audio frame for LiveKit
                # Qwen outputs 24kHz mono PCM16
                frame = rtc.AudioFrame(
                    data=audio_array.tobytes(),
                    sample_rate=24000,
                    num_channels=1,
                    samples_per_channel=len(audio_array),
                )

                await audio_source.capture_frame(frame)
                print(f"   ✅ Played back to LiveKit ({len(audio_array)} samples)")

            # Get transcripts for logging
            transcript = await qwen.get_transcript()
            if transcript:
                role, text = transcript
                print(f"📝 [{role.upper()}]: {text}")

            # Small sleep to prevent busy loop
            await asyncio.sleep(0.001)

    except Exception as e:
        print(f"❌ Error in main loop: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await qwen.disconnect()
        print("🛑 Agent stopped")

if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))