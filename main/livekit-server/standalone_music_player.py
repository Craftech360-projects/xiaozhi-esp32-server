#!/usr/bin/env python3
"""
Standalone LiveKit Music Streaming Bot
Streams continuous music to a LiveKit room without AI agent
"""

import asyncio
import logging
import signal
import sys
import os
import argparse
import io
from pathlib import Path
from typing import Optional
import aiohttp
from dotenv import load_dotenv

# Add current directory to path for imports (we're already in livekit-server)
sys.path.insert(0, str(Path(__file__).parent))

try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    print("ERROR: pydub not installed. Install with: pip install pydub")
    sys.exit(1)

try:
    from livekit import rtc
    LIVEKIT_AVAILABLE = True
except ImportError:
    print("ERROR: livekit-rtc not installed. Install with: pip install livekit-rtc")
    sys.exit(1)

from src.services.music_service import MusicService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


class MusicStreamingBot:
    """Standalone music streaming bot for LiveKit rooms"""

    def __init__(self, room_name: str, language: Optional[str] = None, loop_count: Optional[int] = None):
        self.room_name = room_name
        self.language = language
        self.loop_count = loop_count  # None = infinite
        self.should_stop = False

        # LiveKit components
        self.room: Optional[rtc.Room] = None
        self.audio_source: Optional[rtc.AudioSource] = None
        self.audio_track: Optional[rtc.LocalAudioTrack] = None
        self.track_publication = None

        # Services
        self.music_service: Optional[MusicService] = None

        # Stats
        self.songs_played = 0

    async def initialize(self):
        """Initialize music service and LiveKit connection"""
        logger.info("Initializing Music Streaming Bot...")

        # Load environment variables (we're in livekit-server directory)
        env_path = Path(__file__).parent / ".env"
        if not env_path.exists():
            logger.error(f"Environment file not found: {env_path}")
            return False

        load_dotenv(env_path)
        logger.info(f"Loaded environment from {env_path}")

        # Verify required environment variables
        required_vars = ["LIVEKIT_URL", "LIVEKIT_API_KEY", "LIVEKIT_API_SECRET"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            logger.error(f"Missing required environment variables: {missing_vars}")
            return False

        # Initialize music service
        logger.info("Initializing MusicService with Qdrant...")
        self.music_service = MusicService()

        initialized = await self.music_service.initialize()
        if not initialized:
            logger.error("Failed to initialize MusicService")
            return False

        logger.info("✅ MusicService initialized successfully")

        # Connect to LiveKit room
        success = await self.connect_to_room()
        if not success:
            return False

        logger.info("✅ Initialization complete")
        return True

    async def connect_to_room(self) -> bool:
        """Connect to LiveKit room and publish audio track"""
        try:
            livekit_url = os.getenv("LIVEKIT_URL")
            api_key = os.getenv("LIVEKIT_API_KEY")
            api_secret = os.getenv("LIVEKIT_API_SECRET")

            # Generate access token
            from livekit import api
            token = api.AccessToken(api_key, api_secret)
            token.with_identity("music-bot")
            token.with_name("Music Streaming Bot")
            token.with_grants(api.VideoGrants(
                room_join=True,
                room=self.room_name,
                can_publish=True,
                can_subscribe=False  # Don't need to receive audio
            ))

            jwt_token = token.to_jwt()
            logger.info(f"Connecting to LiveKit room: {self.room_name}")

            # Create and connect room
            self.room = rtc.Room()

            # Connect to room
            await self.room.connect(livekit_url, jwt_token)
            logger.info(f"✅ Connected to room: {self.room_name}")

            # Create audio source and track
            self.audio_source = rtc.AudioSource(48000, 1)  # 48kHz, mono
            self.audio_track = rtc.LocalAudioTrack.create_audio_track("music", self.audio_source)

            # Publish audio track
            options = rtc.TrackPublishOptions(source=rtc.TrackSource.SOURCE_MICROPHONE)
            self.track_publication = await self.room.local_participant.publish_track(
                self.audio_track,
                options
            )
            logger.info("✅ Audio track published successfully")

            return True

        except Exception as e:
            logger.error(f"Failed to connect to room: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    async def stream_music_loop(self):
        """Main music streaming loop"""
        logger.info(f"Starting music loop (language: {self.language or 'all'}, loop_count: {self.loop_count or 'infinite'})")
        logger.info("Press Ctrl+C to stop\n")

        songs_to_play = self.loop_count if self.loop_count else float('inf')

        while not self.should_stop and self.songs_played < songs_to_play:
            try:
                # Fetch next song
                logger.info(f"[{self.songs_played + 1}] Fetching random song...")
                song = await self.music_service.get_random_song(self.language)

                if not song:
                    logger.warning("No song available, retrying in 5 seconds...")
                    await asyncio.sleep(5)
                    continue

                logger.info(f"🎵 Now playing: \"{song['title']}\" ({song['language']})")

                # Download and stream song
                await self.download_and_stream(song)

                self.songs_played += 1
                logger.info(f"✅ Finished: \"{song['title']}\" (total played: {self.songs_played})\n")

                # Small gap between songs
                if not self.should_stop:
                    await asyncio.sleep(1)

            except asyncio.CancelledError:
                logger.info("Music loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in music loop: {e}")
                logger.error("Skipping to next song...")
                await asyncio.sleep(2)

        if not self.should_stop:
            logger.info(f"Finished playing {self.songs_played} songs")

    async def download_and_stream(self, song: dict):
        """Download song and stream to LiveKit room"""
        url = song['url']
        title = song['title']

        try:
            # Download audio
            logger.info(f"📥 Downloading from {url[:50]}...")

            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        logger.error(f"Failed to download: HTTP {response.status}")
                        return

                    audio_data = await response.read()
                    file_size_mb = len(audio_data) / (1024 * 1024)
                    logger.info(f"✅ Downloaded {file_size_mb:.2f} MB")

            # Convert audio to PCM
            logger.info(f"🔄 Converting to PCM (48kHz, mono, 16-bit)...")
            audio_segment = AudioSegment.from_mp3(io.BytesIO(audio_data))

            # Convert to required format
            audio_segment = audio_segment.set_frame_rate(48000)
            audio_segment = audio_segment.set_channels(1)
            audio_segment = audio_segment.set_sample_width(2)  # 16-bit

            raw_audio = audio_segment.raw_data
            duration_seconds = len(audio_segment) / 1000.0
            logger.info(f"✅ Converted ({duration_seconds:.1f} seconds)")

            # Stream to LiveKit
            await self.stream_audio_data(raw_audio, title, duration_seconds)

        except Exception as e:
            logger.error(f"Error downloading/streaming song: {e}")
            import traceback
            logger.error(traceback.format_exc())

    async def stream_audio_data(self, raw_audio: bytes, title: str, duration: float):
        """Stream PCM audio data to LiveKit room"""
        sample_rate = 48000
        frame_duration_ms = 20
        samples_per_frame = sample_rate * frame_duration_ms // 1000  # 960 samples

        total_samples = len(raw_audio) // 2  # 16-bit = 2 bytes per sample
        total_frames = total_samples // samples_per_frame

        logger.info(f"🎶 Streaming {total_frames} frames ({duration:.1f}s)...")

        # Progress tracking
        last_percent = 0

        for frame_num in range(total_frames):
            if self.should_stop:
                logger.info("Stopping stream...")
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

            # Sleep for frame duration (20ms)
            await asyncio.sleep(frame_duration_ms / 1000.0)

            # Progress indicator (every 10%)
            percent = int((frame_num / total_frames) * 100)
            if percent >= last_percent + 10:
                logger.info(f"   Progress: {percent}%")
                last_percent = percent

    async def shutdown(self):
        """Graceful shutdown"""
        logger.info("\nShutting down gracefully...")
        self.should_stop = True

        try:
            # Unpublish track
            if self.track_publication and self.room:
                logger.info("Unpublishing audio track...")
                await self.room.local_participant.unpublish_track(self.track_publication.sid)

            # Disconnect from room
            if self.room:
                logger.info("Disconnecting from room...")
                await self.room.disconnect()

            logger.info("✅ Shutdown complete")

        except Exception as e:
            logger.error(f"Error during shutdown: {e}")


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Standalone LiveKit Music Streaming Bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Stream infinite music to 'background-music' room
  python standalone_music_player.py --room background-music

  # Stream 5 English songs
  python standalone_music_player.py --room test-room --language English --count 5

  # Stream Hindi music continuously
  python standalone_music_player.py --room hindi-music --language Hindi
        """
    )

    parser.add_argument(
        "--room",
        type=str,
        default="background-music",
        help="LiveKit room name to join (default: background-music)"
    )

    parser.add_argument(
        "--language",
        type=str,
        default=None,
        help="Filter by language (English, Hindi, Telugu, etc.) - default: all languages"
    )

    parser.add_argument(
        "--count",
        type=int,
        default=None,
        help="Number of songs to play (default: infinite)"
    )

    args = parser.parse_args()

    # Create bot
    bot = MusicStreamingBot(
        room_name=args.room,
        language=args.language,
        loop_count=args.count
    )

    # Setup signal handlers for graceful shutdown
    def signal_handler(sig, frame):
        logger.info("\nReceived interrupt signal")
        asyncio.create_task(bot.shutdown())

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Initialize and run
    try:
        success = await bot.initialize()
        if not success:
            logger.error("Initialization failed")
            return 1

        # Start streaming music
        await bot.stream_music_loop()

        # Shutdown
        await bot.shutdown()
        return 0

    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
        await bot.shutdown()
        return 0
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
