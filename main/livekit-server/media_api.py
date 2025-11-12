"""
Media API Server - Spawns music/story bots that join LiveKit rooms
Similar to livekit-media/server.py but integrated with existing services
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, List
import logging
import asyncio
import os
from dotenv import load_dotenv
from livekit import rtc, api
from pydub import AudioSegment
import io
import aiohttp

from src.services.music_service import MusicService
from src.services.story_service import StoryService
from src.utils.model_cache import model_cache

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv(".env")

# LiveKit configuration
LIVEKIT_URL = os.getenv("LIVEKIT_URL")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")

app = FastAPI(title="Cheeko Media API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services on startup
music_service: Optional[MusicService] = None
story_service: Optional[StoryService] = None
active_bots = {}  # Track active bots by room_name


@app.on_event("startup")
async def startup_event():
    global music_service, story_service

    logger.info("🚀 Initializing Media API services...")

    # Get preloaded models from cache
    embedding_model = model_cache.get_embedding_model()
    qdrant_client = model_cache.get_qdrant_client()

    # Initialize services
    music_service = MusicService(embedding_model, qdrant_client)
    story_service = StoryService(embedding_model, qdrant_client)

    await music_service.initialize()
    await story_service.initialize()

    logger.info("✅ Media API services initialized")


class StartMusicBotRequest(BaseModel):
    room_name: str       # LiveKit room name (e.g., "uuid_mac_music")
    device_mac: str      # Device MAC address
    language: Optional[str] = None
    playlist: Optional[List[dict]] = None  # Playlist with filename + language


class StartStoryBotRequest(BaseModel):
    room_name: str
    device_mac: str
    age_group: Optional[str] = None
    playlist: Optional[List[dict]] = None  # Playlist with filename + category


class StopBotRequest(BaseModel):
    room_name: str


def create_bot_token(room_name: str, bot_identity: str) -> str:
    """Create access token for bot to join room"""
    at = api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
    at.with_identity(bot_identity)
    at.with_name(bot_identity)
    at.with_grants(api.VideoGrants(
        room_join=True,
        room=room_name,
        can_publish=True,
        can_subscribe=True
    ))
    return at.to_jwt()


class MediaBot:
    """Base class for music/story bots that stream audio to LiveKit rooms"""

    def __init__(self, room_name: str, token: str, bot_type: str):
        self.room_name = room_name
        self.token = token
        self.bot_type = bot_type  # "music" or "story"

        # LiveKit components
        self.room = None
        self.audio_source = None
        self.audio_track = None
        self.should_stop = False

    async def connect_to_room(self) -> bool:
        """Connect to LiveKit room and publish audio track"""
        try:
            self.room = rtc.Room()

            await self.room.connect(LIVEKIT_URL, self.token)
            logger.info(f"✅ {self.bot_type} bot connected to room: {self.room_name}")

            # Create audio source (48kHz mono - LiveKit will handle to approom.js)
            self.audio_source = rtc.AudioSource(48000, 1)
            self.audio_track = rtc.LocalAudioTrack.create_audio_track(
                f"{self.bot_type}-audio",
                self.audio_source
            )

            # Publish audio track
            options = rtc.TrackPublishOptions(source=rtc.TrackSource.SOURCE_MICROPHONE)
            await self.room.local_participant.publish_track(self.audio_track, options)
            logger.info(f"✅ {self.bot_type} audio track published")

            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to room: {e}")
            return False

    async def download_from_cdn(self, url: str) -> bytes:
        """Download MP3 file from CDN"""
        try:
            logger.info(f"📥 Downloading from CDN: {url}")
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

    async def convert_to_pcm(self, audio_data: bytes) -> bytes:
        """Convert MP3 to PCM format for LiveKit (48kHz mono 16-bit)"""
        try:
            logger.info("🔄 Converting MP3 to PCM...")
            audio_segment = AudioSegment.from_mp3(io.BytesIO(audio_data))

            # Convert to LiveKit format: 48kHz, mono, 16-bit
            audio_segment = audio_segment.set_frame_rate(48000)
            audio_segment = audio_segment.set_channels(1)
            audio_segment = audio_segment.set_sample_width(2)  # 16-bit

            raw_audio = audio_segment.raw_data
            duration_seconds = len(audio_segment) / 1000.0

            logger.info(f"✅ Converted to PCM ({duration_seconds:.1f} seconds)")
            return raw_audio
        except Exception as e:
            logger.error(f"❌ Failed to convert audio: {e}")
            raise

    async def stream_audio_to_livekit(self, raw_audio: bytes, title: str):
        """Stream PCM audio to LiveKit room"""
        try:
            sample_rate = 48000
            frame_duration_ms = 20
            samples_per_frame = sample_rate * frame_duration_ms // 1000  # 960 samples

            total_samples = len(raw_audio) // 2  # 16-bit = 2 bytes per sample
            total_frames = total_samples // samples_per_frame

            logger.info(f"🎵 Streaming '{title}' to LiveKit ({total_frames} frames)...")

            for frame_num in range(total_frames):
                if self.should_stop:
                    logger.info("⏹️ Stopping stream...")
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

                # Progress indicator
                if frame_num % 500 == 0:
                    percent = (frame_num / total_frames) * 100
                    logger.info(f"   Progress: {percent:.1f}%")

            logger.info(f"✅ Finished streaming '{title}'")

        except Exception as e:
            logger.error(f"❌ Error streaming audio: {e}")
            raise

    async def disconnect(self):
        """Disconnect from LiveKit room"""
        try:
            self.should_stop = True
            if self.room:
                await self.room.disconnect()
                logger.info(f"👋 {self.bot_type} bot disconnected from room")
        except Exception as e:
            logger.error(f"Error during disconnect: {e}")


class StreamingAudioIterator:
    """
    Async iterator that downloads MP3 chunks from CDN and converts to LiveKit frames on-the-fly.
    This enables progressive streaming - audio starts playing immediately instead of waiting for full download.
    """

    def __init__(self, cdn_url: str, stop_event, title: str):
        self.cdn_url = cdn_url
        self.stop_event = stop_event
        self.title = title
        self.chunk_size = 64 * 1024  # 64KB chunks
        self.frame_queue = asyncio.Queue(maxsize=100)  # Buffer up to 100 frames
        self.producer_task = None
        self.session = None

    async def _produce_frames(self):
        """Background task: Download MP3 chunks, convert to PCM, create LiveKit frames"""
        try:
            logger.info(f"🎵 Starting progressive download: {self.title}")

            # Start streaming download from CDN
            self.session = aiohttp.ClientSession()
            async with self.session.get(self.cdn_url, timeout=aiohttp.ClientTimeout(total=300)) as response:
                if response.status != 200:
                    raise Exception(f"CDN returned status {response.status}")

                # MP3 decoding state
                mp3_buffer = bytearray()
                chunk_count = 0
                total_bytes = 0

                # LiveKit audio parameters
                sample_rate = 48000
                frame_duration_ms = 20
                samples_per_frame = sample_rate * frame_duration_ms // 1000  # 960 samples

                # Download and process chunks
                async for chunk in response.content.iter_chunked(self.chunk_size):
                    if self.stop_event:
                        logger.info("⏹️ Stop event triggered, halting download")
                        break

                    chunk_count += 1
                    total_bytes += len(chunk)
                    mp3_buffer.extend(chunk)

                    # Try to decode accumulated MP3 data
                    try:
                        # Attempt to decode the buffer as MP3
                        audio_segment = AudioSegment.from_mp3(io.BytesIO(bytes(mp3_buffer)))

                        # Convert to LiveKit format: 48kHz, mono, 16-bit
                        audio_segment = audio_segment.set_frame_rate(sample_rate)
                        audio_segment = audio_segment.set_channels(1)
                        audio_segment = audio_segment.set_sample_width(2)  # 16-bit

                        # Get raw PCM data
                        raw_pcm = audio_segment.raw_data

                        # Clear buffer since we successfully decoded
                        mp3_buffer.clear()

                        # Split PCM into LiveKit frames (20ms each = 960 samples)
                        total_samples = len(raw_pcm) // 2  # 16-bit = 2 bytes per sample
                        total_frames = total_samples // samples_per_frame

                        for frame_num in range(total_frames):
                            if self.stop_event:
                                break

                            # Extract frame data
                            start_byte = frame_num * samples_per_frame * 2
                            end_byte = start_byte + (samples_per_frame * 2)
                            frame_data = raw_pcm[start_byte:end_byte]

                            # Pad if necessary
                            if len(frame_data) < samples_per_frame * 2:
                                frame_data += b'\x00' * (samples_per_frame * 2 - len(frame_data))

                            # Create LiveKit AudioFrame
                            livekit_frame = rtc.AudioFrame(
                                data=frame_data,
                                sample_rate=sample_rate,
                                num_channels=1,
                                samples_per_channel=samples_per_frame
                            )

                            # Add to queue (blocks if queue is full - provides backpressure)
                            await self.frame_queue.put(livekit_frame)

                        # Log progress periodically
                        if chunk_count % 10 == 0:
                            mb_downloaded = total_bytes / (1024 * 1024)
                            logger.info(f"   📥 Downloaded {mb_downloaded:.2f} MB ({chunk_count} chunks)")

                    except Exception as decode_error:
                        # Incomplete MP3 frame - need more data
                        # Keep accumulating in mp3_buffer
                        if len(mp3_buffer) > 10 * 1024 * 1024:  # Safety: clear if buffer > 10MB
                            logger.warning(f"⚠️ MP3 buffer too large ({len(mp3_buffer)} bytes), clearing")
                            mp3_buffer.clear()
                        continue

                # Process any remaining buffered data
                if len(mp3_buffer) > 0 and not self.stop_event:
                    try:
                        audio_segment = AudioSegment.from_mp3(io.BytesIO(bytes(mp3_buffer)))
                        audio_segment = audio_segment.set_frame_rate(sample_rate).set_channels(1).set_sample_width(2)
                        raw_pcm = audio_segment.raw_data

                        # Convert remaining PCM to frames
                        total_samples = len(raw_pcm) // 2
                        total_frames = total_samples // samples_per_frame

                        for frame_num in range(total_frames):
                            start_byte = frame_num * samples_per_frame * 2
                            end_byte = start_byte + (samples_per_frame * 2)
                            frame_data = raw_pcm[start_byte:end_byte]

                            if len(frame_data) < samples_per_frame * 2:
                                frame_data += b'\x00' * (samples_per_frame * 2 - len(frame_data))

                            livekit_frame = rtc.AudioFrame(
                                data=frame_data,
                                sample_rate=sample_rate,
                                num_channels=1,
                                samples_per_channel=samples_per_frame
                            )
                            await self.frame_queue.put(livekit_frame)
                    except:
                        pass  # Ignore final incomplete data

                logger.info(f"✅ Download complete: {total_bytes / (1024 * 1024):.2f} MB")

        except Exception as e:
            logger.error(f"❌ Error in streaming producer: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Signal end of stream
            await self.frame_queue.put(None)
            if self.session:
                await self.session.close()

    async def __anext__(self):
        """Return next audio frame when ready"""
        if self.producer_task is None:
            # Start background download/conversion task
            self.producer_task = asyncio.create_task(self._produce_frames())

        # Get next frame from queue (blocks until available)
        frame = await self.frame_queue.get()

        if frame is None:
            # End of stream
            raise StopAsyncIteration

        return frame

    def __aiter__(self):
        return self


class MusicBot(MediaBot):
    """Music streaming bot"""

    def __init__(self, room_name: str, token: str, language: Optional[str] = None, playlist: Optional[List[dict]] = None):
        super().__init__(room_name, token, "music")
        self.language = language
        self.playlist = playlist  # List of {filename, category/language, title, etc.}

    async def run(self):
        """Main entry point - connect and stream music with progressive streaming"""
        try:
            # Connect to LiveKit
            if not await self.connect_to_room():
                logger.error("Failed to connect to room")
                return

            # Check if playlist is provided
            if self.playlist and len(self.playlist) > 0:
                logger.info(f"🎵 Using playlist with {len(self.playlist)} songs")

                # Loop through playlist and stream each song
                for idx, playlist_item in enumerate(self.playlist):
                    if self.should_stop:
                        logger.info("⏹️ Stopping playlist...")
                        break

                    # Extract metadata from playlist item
                    filename = playlist_item.get('filename')
                    category = playlist_item.get('category')  # For music, this is language (English, Hindi, etc.)
                    title = playlist_item.get('title', filename)

                    if not filename or not category:
                        logger.warning(f"⚠️ Skipping invalid playlist item: {playlist_item}")
                        continue

                    # Construct URL using music_service
                    song_url = music_service.get_song_url(filename, category)
                    logger.info(f"🎵 [{idx + 1}/{len(self.playlist)}] Playing: '{title}' ({category})")

                    # Stream this song using progressive streaming
                    await self._stream_song(song_url, title)

                    if self.should_stop:
                        break

                    # Small gap between songs
                    await asyncio.sleep(1)

                logger.info(f"✅ Finished playing playlist ({len(self.playlist)} songs)")
            else:
                # No playlist - fall back to random song
                logger.info("🎵 No playlist provided, playing random song")
                song = await music_service.get_random_song(language=self.language)

                if not song:
                    logger.error("No music available")
                    return

                logger.info(f"🎵 Selected: '{song['title']}' ({song['language']})")
                await self._stream_song(song['url'], song['title'])

            # Keep bot alive for a moment to ensure audio finishes
            await asyncio.sleep(2)

        except Exception as e:
            logger.error(f"❌ Music bot error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await self.disconnect()
            # Remove from active bots
            if self.room_name in active_bots:
                del active_bots[self.room_name]

    async def _stream_song(self, song_url: str, title: str):
        """Stream a single song using progressive streaming"""
        # Create streaming iterator for progressive download & conversion
        stream_iterator = StreamingAudioIterator(
            cdn_url=song_url,
            stop_event=self.should_stop,
            title=title
        )

        # Stream frames as they become available (audio starts immediately!)
        logger.info(f"🎵 Starting progressive stream to LiveKit...")
        frame_count = 0

        async for frame in stream_iterator:
            if self.should_stop:
                logger.info("⏹️ Stopping music stream...")
                break

            # Send frame to LiveKit room
            await self.audio_source.capture_frame(frame)
            frame_count += 1

            # Progress indicator every 500 frames (~10 seconds)
            if frame_count % 500 == 0:
                logger.info(f"   🎵 Streamed {frame_count} frames...")

        logger.info(f"✅ Finished streaming '{title}' ({frame_count} frames)")


class StoryBot(MediaBot):
    """Story streaming bot"""

    def __init__(self, room_name: str, token: str, age_group: Optional[str] = None, playlist: Optional[List[dict]] = None):
        super().__init__(room_name, token, "story")
        self.age_group = age_group
        self.playlist = playlist  # List of {filename, category, title, etc.}

    async def run(self):
        """Main entry point - connect and stream story with progressive streaming"""
        try:
            if not await self.connect_to_room():
                logger.error("Failed to connect to room")
                return

            # Check if playlist is provided
            if self.playlist and len(self.playlist) > 0:
                logger.info(f"📖 Using playlist with {len(self.playlist)} stories")

                # Loop through playlist and stream each story
                for idx, playlist_item in enumerate(self.playlist):
                    if self.should_stop:
                        logger.info("⏹️ Stopping playlist...")
                        break

                    # Extract metadata from playlist item
                    filename = playlist_item.get('filename')
                    category = playlist_item.get('category')  # Adventure, Bedtime, Fantasy, etc.
                    title = playlist_item.get('title', filename)

                    if not filename or not category:
                        logger.warning(f"⚠️ Skipping invalid playlist item: {playlist_item}")
                        continue

                    # Construct URL using story_service
                    story_url = story_service.get_story_url(filename, category)
                    logger.info(f"📖 [{idx + 1}/{len(self.playlist)}] Playing: '{title}' ({category})")

                    # Stream this story using progressive streaming
                    await self._stream_story(story_url, title)

                    if self.should_stop:
                        break

                    # Small gap between stories
                    await asyncio.sleep(1)

                logger.info(f"✅ Finished playing playlist ({len(self.playlist)} stories)")
            else:
                # No playlist - fall back to random story
                logger.info("📖 No playlist provided, playing random story")
                # Note: age_group is treated as category (e.g., "Adventure", "Bedtime", "Fantasy")
                story = await story_service.get_random_story(category=self.age_group)

                if not story:
                    logger.error("No story available")
                    return

                logger.info(f"📖 Selected: '{story['title']}'")
                await self._stream_story(story['url'], story['title'])

            await asyncio.sleep(2)

        except Exception as e:
            logger.error(f"❌ Story bot error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await self.disconnect()
            if self.room_name in active_bots:
                del active_bots[self.room_name]

    async def _stream_story(self, story_url: str, title: str):
        """Stream a single story using progressive streaming"""
        # Create streaming iterator for progressive download & conversion
        stream_iterator = StreamingAudioIterator(
            cdn_url=story_url,
            stop_event=self.should_stop,
            title=title
        )

        # Stream frames as they become available (audio starts immediately!)
        logger.info(f"📖 Starting progressive stream to LiveKit...")
        frame_count = 0

        async for frame in stream_iterator:
            if self.should_stop:
                logger.info("⏹️ Stopping story stream...")
                break

            # Send frame to LiveKit room
            await self.audio_source.capture_frame(frame)
            frame_count += 1

            # Progress indicator every 500 frames (~10 seconds)
            if frame_count % 500 == 0:
                logger.info(f"   📖 Streamed {frame_count} frames...")

        logger.info(f"✅ Finished streaming '{title}' ({frame_count} frames)")


@app.post("/start-music-bot")
async def start_music_bot(req: StartMusicBotRequest):
    """Start music bot that joins LiveKit room and streams music"""
    try:
        playlist_info = f", playlist: {len(req.playlist)} songs" if req.playlist else ""
        logger.info(f"🎵 Starting music bot for room: {req.room_name}, language: {req.language or 'all'}{playlist_info}")

        # Check if bot already exists for this room
        if req.room_name in active_bots:
            logger.warning(f"Bot already active for room: {req.room_name}")
            return {"status": "already_active", "room_name": req.room_name}

        # Create token for bot
        token = create_bot_token(req.room_name, "music-bot")

        # Create and start music bot with playlist
        bot = MusicBot(req.room_name, token, req.language, req.playlist)

        # Store bot reference
        active_bots[req.room_name] = bot

        # Run bot in background
        asyncio.create_task(bot.run())

        logger.info(f"✅ Music bot started for room: {req.room_name}")

        return {
            "status": "started",
            "room_name": req.room_name,
            "bot_type": "music",
            "language": req.language or "all",
            "playlist_size": len(req.playlist) if req.playlist else 0
        }

    except Exception as e:
        logger.error(f"❌ Error starting music bot: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/start-story-bot")
async def start_story_bot(req: StartStoryBotRequest):
    """Start story bot that joins LiveKit room and streams story"""
    try:
        playlist_info = f", playlist: {len(req.playlist)} stories" if req.playlist else ""
        logger.info(f"📖 Starting story bot for room: {req.room_name}{playlist_info}")

        if req.room_name in active_bots:
            logger.warning(f"Bot already active for room: {req.room_name}")
            return {"status": "already_active", "room_name": req.room_name}

        token = create_bot_token(req.room_name, "story-bot")

        # Create and start story bot with playlist
        bot = StoryBot(req.room_name, token, req.age_group, req.playlist)
        active_bots[req.room_name] = bot

        asyncio.create_task(bot.run())

        logger.info(f"✅ Story bot started for room: {req.room_name}")

        return {
            "status": "started",
            "room_name": req.room_name,
            "bot_type": "story",
            "playlist_size": len(req.playlist) if req.playlist else 0
        }

    except Exception as e:
        logger.error(f"❌ Error starting story bot: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/stop-bot")
async def stop_bot(req: StopBotRequest):
    """Stop a running bot for a specific room"""
    try:
        if req.room_name not in active_bots:
            logger.warning(f"No active bot found for room: {req.room_name}")
            return {"status": "not_found", "room_name": req.room_name}

        bot = active_bots[req.room_name]

        logger.info(f"🛑 Stopping bot for room: {req.room_name}")

        # Signal bot to stop
        bot.should_stop = True

        # Disconnect bot
        await bot.disconnect()

        # Remove from active bots
        del active_bots[req.room_name]

        logger.info(f"✅ Bot stopped for room: {req.room_name}")

        return {"status": "stopped", "room_name": req.room_name}

    except Exception as e:
        logger.error(f"❌ Error stopping bot: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "active_bots": len(active_bots),
        "music_service": music_service.is_initialized if music_service else False,
        "story_service": story_service.is_initialized if story_service else False
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003, log_level="info")
