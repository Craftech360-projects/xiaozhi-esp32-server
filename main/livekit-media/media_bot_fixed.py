# media_bot.py - Fixed for livekit-agents 1.2.9
import asyncio
from livekit import rtc
from pathlib import Path
from pydub import AudioSegment
import io

class AudioBot:
    """Audio bot that plays a playlist to a LiveKit room"""

    def __init__(self, playlist, livekit_url, token):
        self.playlist = playlist
        self.livekit_url = livekit_url
        self.token = token
        self.room = None
        self.audio_source = None
        self.audio_track = None
        self.should_stop = False

    async def connect(self):
        """Connect to LiveKit room"""
        try:
            self.room = rtc.Room()
            await self.room.connect(self.livekit_url, self.token)
            print(f"✅ Connected to room: {self.room.name}")

            # Create audio source and track
            self.audio_source = rtc.AudioSource(48000, 1)  # 48kHz, mono
            self.audio_track = rtc.LocalAudioTrack.create_audio_track("playlist", self.audio_source)

            # Publish audio track
            options = rtc.TrackPublishOptions(source=rtc.TrackSource.SOURCE_MICROPHONE)
            await self.room.local_participant.publish_track(self.audio_track, options)
            print("✅ Audio track published")

            return True
        except Exception as e:
            print(f"❌ Failed to connect: {e}")
            return False

    async def play_audio_file(self, file_path):
        """Play an audio file to the room"""
        try:
            print(f"▶️  Playing: {file_path}")

            # Load and convert audio
            audio = AudioSegment.from_file(file_path)
            audio = audio.set_frame_rate(48000).set_channels(1).set_sample_width(2)
            raw_audio = audio.raw_data

            # Stream audio in 20ms frames
            sample_rate = 48000
            frame_duration_ms = 20
            samples_per_frame = sample_rate * frame_duration_ms // 1000  # 960 samples

            total_samples = len(raw_audio) // 2
            total_frames = total_samples // samples_per_frame

            for frame_num in range(total_frames):
                if self.should_stop:
                    break

                start_byte = frame_num * samples_per_frame * 2
                end_byte = start_byte + (samples_per_frame * 2)
                frame_data = raw_audio[start_byte:end_byte]

                # Pad if necessary
                if len(frame_data) < samples_per_frame * 2:
                    frame_data += b'\x00' * (samples_per_frame * 2 - len(frame_data))

                frame = rtc.AudioFrame(
                    data=frame_data,
                    sample_rate=sample_rate,
                    num_channels=1,
                    samples_per_channel=samples_per_frame
                )

                await self.audio_source.capture_frame(frame)
                await asyncio.sleep(frame_duration_ms / 1000.0)

            print(f"✅ Finished: {file_path}")

        except Exception as e:
            print(f"❌ Error playing {file_path}: {e}")

    async def run(self):
        """Main run loop - connect and play playlist"""
        try:
            # Connect to room
            connected = await self.connect()
            if not connected:
                return

            # Play playlist
            print("🎶 Media Bot connected, starting playlist...")
            for song in self.playlist:
                if self.should_stop:
                    break
                await self.play_audio_file(song)
                await asyncio.sleep(1)  # Small gap between songs

            print("✅ Playlist finished")

        except Exception as e:
            print(f"❌ Error in bot: {e}")
        finally:
            await self.disconnect()

    async def disconnect(self):
        """Disconnect from room"""
        if self.room:
            await self.room.disconnect()
            print("👋 Disconnected from room")
