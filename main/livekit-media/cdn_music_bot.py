"""
CDN Music Bot - Streams random music from CloudFront CDN to LiveKit room
With Next/Previous control via LiveKit Data Channel
"""
import asyncio
import logging
import json
from livekit import rtc
from pydub import AudioSegment
import io
import aiohttp
from typing import Optional, Dict, List
from collections import deque
from qdrant_simple import SimpleQdrantMusic

logger = logging.getLogger(__name__)

class CDNMusicBot:
    """Music bot that streams random songs from CDN to LiveKit room with playback control"""

    def __init__(self, livekit_url: str, token: str, qdrant_url: str, qdrant_api_key: str,
                 cloudfront_domain: str, language: Optional[str] = None):
        self.livekit_url = livekit_url
        self.token = token
        self.language = language

        # LiveKit components
        self.room = None
        self.audio_source = None
        self.audio_track = None
        self.should_stop = False

        # Playback control
        self.skip_requested = False
        self.skip_direction = None  # 'next' or 'previous'

        # Song history and current state
        self.song_history: deque = deque(maxlen=10)  # Remember last 10 songs
        self.current_song: Optional[Dict] = None
        self.history_index = -1  # -1 means playing new songs, 0+ means replaying from history

        # Qdrant music service
        self.music_service = SimpleQdrantMusic(qdrant_url, qdrant_api_key, cloudfront_domain)

        # Stats
        self.songs_played = 0

    async def initialize(self) -> bool:
        """Initialize Qdrant and connect to LiveKit"""
        logger.info("🎵 Initializing CDN Music Bot...")

        # Initialize Qdrant
        if not await self.music_service.initialize():
            logger.error("Failed to initialize Qdrant")
            return False

        # Connect to LiveKit room
        if not await self.connect_to_room():
            logger.error("Failed to connect to LiveKit room")
            return False

        logger.info("✅ CDN Music Bot initialized successfully")
        return True

    async def connect_to_room(self) -> bool:
        """Connect to LiveKit room and publish audio track"""
        try:
            self.room = rtc.Room()

            # Setup event listeners BEFORE connecting
            self.setup_event_listeners()

            await self.room.connect(self.livekit_url, self.token)
            logger.info(f"✅ Connected to room: {self.room.name}")

            # Create audio source and track
            self.audio_source = rtc.AudioSource(48000, 1)  # 48kHz, mono
            self.audio_track = rtc.LocalAudioTrack.create_audio_track("cdn-music", self.audio_source)

            # Publish audio track
            options = rtc.TrackPublishOptions(source=rtc.TrackSource.SOURCE_MICROPHONE)
            await self.room.local_participant.publish_track(self.audio_track, options)
            logger.info("✅ Audio track published")

            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to room: {e}")
            return False

    def setup_event_listeners(self):
        """Setup LiveKit room event listeners"""
        @self.room.on("data_received")
        def on_data_received(data: rtc.DataPacket):
            """Handle data messages from clients"""
            try:
                # Decode the data
                message_str = data.data.decode('utf-8')
                message = json.loads(message_str)

                command = message.get('command')
                logger.info(f"📨 Received command: {command}")

                if command == 'next':
                    self.handle_next_command()
                elif command == 'previous':
                    self.handle_previous_command()
                else:
                    logger.warning(f"Unknown command: {command}")

            except Exception as e:
                logger.error(f"Error handling data message: {e}")

    def handle_next_command(self):
        """Handle 'next' command - skip to next random song"""
        logger.info("⏭️  Next command received - skipping to next song")
        self.skip_requested = True
        self.skip_direction = 'next'
        # Reset history index to play new songs
        self.history_index = -1

    def handle_previous_command(self):
        """Handle 'previous' command - go back to previous song"""
        if not self.song_history:
            logger.info("⏮️  No previous songs in history")
            return

        logger.info("⏮️  Previous command received - going to previous song")
        self.skip_requested = True
        self.skip_direction = 'previous'

    async def broadcast_song_info(self, song: Dict, status: str = "playing"):
        """Broadcast current song info to all participants"""
        try:
            message = {
                'type': 'song_info',
                'status': status,
                'song': {
                    'title': song.get('title', 'Unknown'),
                    'language': song.get('language', 'Unknown'),
                    'filename': song.get('filename', '')
                },
                'history_count': len(self.song_history)
            }

            # Publish data to all participants
            await self.room.local_participant.publish_data(
                json.dumps(message).encode('utf-8'),
                reliable=True
            )
            logger.info(f"📤 Broadcasted song info: {song['title']}")

        except Exception as e:
            logger.error(f"Error broadcasting song info: {e}")

    async def download_from_cdn(self, url: str) -> bytes:
        """Download MP3 file from CDN"""
        try:
            logger.info(f"📥 Downloading from CDN...")
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status != 200:
                        raise Exception(f"CDN returned status {response.status}")

                    audio_data = await response.read()
                    size_mb = len(audio_data) / (1024 * 1024)
                    logger.info(f"✅ Downloaded {size_mb:.2f} MB")
                    return audio_data
        except Exception as e:
            logger.error(f"❌ Failed to download from CDN: {e}")
            raise

    async def convert_to_pcm(self, audio_data: bytes) -> tuple:
        """Convert MP3 to PCM format for LiveKit"""
        try:
            logger.info("🔄 Converting to PCM...")
            audio_segment = AudioSegment.from_mp3(io.BytesIO(audio_data))

            # Convert to required format: 48kHz, mono, 16-bit
            audio_segment = audio_segment.set_frame_rate(48000)
            audio_segment = audio_segment.set_channels(1)
            audio_segment = audio_segment.set_sample_width(2)  # 16-bit

            raw_audio = audio_segment.raw_data
            duration_seconds = len(audio_segment) / 1000.0

            logger.info(f"✅ Converted ({duration_seconds:.1f} seconds)")
            return raw_audio, duration_seconds
        except Exception as e:
            logger.error(f"❌ Failed to convert audio: {e}")
            raise

    async def stream_audio(self, raw_audio: bytes, title: str, duration: float):
        """Stream PCM audio to LiveKit room (with skip support)"""
        try:
            sample_rate = 48000
            frame_duration_ms = 20
            samples_per_frame = sample_rate * frame_duration_ms // 1000  # 960 samples

            total_samples = len(raw_audio) // 2  # 16-bit = 2 bytes per sample
            total_frames = total_samples // samples_per_frame

            logger.info(f"🎶 Streaming '{title}' ({total_frames} frames, {duration:.1f}s)...")

            # Progress tracking
            last_percent = 0

            for frame_num in range(total_frames):
                # Check for skip request
                if self.skip_requested:
                    logger.info("⏩ Skip requested - stopping current stream")
                    break

                if self.should_stop:
                    logger.info("⏹️  Stopping stream...")
                    break

                # Extract frame data
                start_byte = frame_num * samples_per_frame * 2
                end_byte = start_byte + (samples_per_frame * 2)
                frame_data = raw_audio[start_byte:end_byte]

                # Pad if necessary
                if len(frame_data) < samples_per_frame * 2:
                    frame_data += b'\x00' * (samples_per_frame * 2 - len(frame_data))

                # Create and capture frame
                frame = rtc.AudioFrame(
                    data=frame_data,
                    sample_rate=sample_rate,
                    num_channels=1,
                    samples_per_channel=samples_per_frame
                )

                await self.audio_source.capture_frame(frame)
                await asyncio.sleep(frame_duration_ms / 1000.0)

                # Progress indicator (every 25%)
                percent = int((frame_num / total_frames) * 100)
                if percent >= last_percent + 25:
                    logger.info(f"   Progress: {percent}%")
                    last_percent = percent

            if not self.skip_requested:
                logger.info(f"✅ Finished streaming '{title}'")

        except Exception as e:
            logger.error(f"❌ Error streaming audio: {e}")
            raise

    def get_next_song(self) -> Optional[Dict]:
        """Get next song (either from history or new random)"""
        if self.skip_direction == 'previous' and self.song_history:
            # Go back in history
            if self.history_index == -1:
                # Currently playing new songs, go to most recent history
                self.history_index = len(self.song_history) - 2  # -2 because last is current
            else:
                # Go further back
                self.history_index = max(0, self.history_index - 1)

            if self.history_index >= 0 and self.history_index < len(self.song_history):
                song = self.song_history[self.history_index]
                logger.info(f"⏮️  Playing from history (index {self.history_index}): {song['title']}")
                return song

        # Otherwise get new random song
        self.history_index = -1  # Reset to new songs
        song = self.music_service.get_random_song(self.language)
        return song

    async def play_random_song(self):
        """Fetch and play one song"""
        try:
            # Reset skip flag
            self.skip_requested = False
            skip_direction_temp = self.skip_direction
            self.skip_direction = None

            # Get next song
            song = self.get_next_song()

            if not song:
                logger.warning("No song available")
                return False

            self.current_song = song

            # Add to history if it's a new song
            if skip_direction_temp != 'previous':
                if not self.song_history or self.song_history[-1]['title'] != song['title']:
                    self.song_history.append(song)

            logger.info(f"🎵 Now playing: '{song['title']}' ({song['language']})")

            # Broadcast song info to clients
            await self.broadcast_song_info(song, "playing")

            # Download from CDN
            audio_data = await self.download_from_cdn(song['url'])

            # Convert to PCM
            raw_audio, duration = await self.convert_to_pcm(audio_data)

            # Stream to LiveKit
            await self.stream_audio(raw_audio, song['title'], duration)

            self.songs_played += 1
            logger.info(f"✅ Completed song #{self.songs_played}: '{song['title']}'")

            return True

        except Exception as e:
            logger.error(f"❌ Error playing song: {e}")
            return False

    async def run_continuous_playback(self):
        """Main loop - play songs continuously with skip support"""
        logger.info(f"🎵 Starting continuous playback (language: {self.language or 'all'})")
        logger.info("Use Next/Previous buttons in client to control playback\n")

        while not self.should_stop:
            try:
                success = await self.play_random_song()

                if not success:
                    logger.warning("Failed to play song, retrying in 5 seconds...")
                    await asyncio.sleep(5)
                    continue

                # Small gap between songs (unless skip was requested)
                if not self.should_stop and not self.skip_requested:
                    logger.info("⏸️  2 second gap before next song...\n")
                    await asyncio.sleep(2)

            except asyncio.CancelledError:
                logger.info("🛑 Playback cancelled")
                break
            except Exception as e:
                logger.error(f"❌ Error in playback loop: {e}")
                await asyncio.sleep(5)

    async def run(self):
        """Main entry point - initialize and start playback"""
        try:
            # Initialize
            if not await self.initialize():
                logger.error("Initialization failed")
                return

            # Start continuous playback
            await self.run_continuous_playback()

        except KeyboardInterrupt:
            logger.info("🛑 Interrupted by user")
        except Exception as e:
            logger.error(f"❌ Fatal error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await self.disconnect()

    async def disconnect(self):
        """Disconnect from LiveKit room"""
        try:
            self.should_stop = True
            if self.room:
                await self.room.disconnect()
                logger.info("👋 Disconnected from room")
        except Exception as e:
            logger.error(f"Error during disconnect: {e}")
