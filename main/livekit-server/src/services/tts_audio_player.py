"""
TTS-Integrated Audio Player for LiveKit Agent
Plays music/stories through LiveKit's native audio player for optimal performance
"""

import logging
import asyncio
import tempfile
import os
from typing import Optional
import aiohttp
from ..utils.audio_state_manager import audio_state_manager

try:
    from livekit.agents import BackgroundAudioPlayer
    LIVEKIT_AUDIO_AVAILABLE = True
except ImportError:
    LIVEKIT_AUDIO_AVAILABLE = False

try:
    from livekit import rtc
    LIVEKIT_AVAILABLE = True
except ImportError:
    LIVEKIT_AVAILABLE = False

logger = logging.getLogger(__name__)

class TTSAudioPlayer:
    """Plays audio through LiveKit's native audio player for optimal performance"""

    def __init__(self):
        self.session = None
        self.context = None
        self.current_task: Optional[asyncio.Task] = None
        self.is_playing = False
        self.stop_event = asyncio.Event()
        self.background_audio = None
        self.temp_files = []  # Track temporary files for cleanup

    def set_session(self, session):
        """Set the LiveKit agent session"""
        self.session = session
        self._initialize_background_audio()
        logger.info("Native audio player integrated with session")

    def set_context(self, context):
        """Set the job context"""
        self.context = context
        logger.info("TTS audio player integrated with context")

    def _initialize_background_audio(self):
        """Initialize LiveKit's native background audio player"""
        try:
            if LIVEKIT_AUDIO_AVAILABLE and self.session:
                # Try to get or create background audio player
                if hasattr(self.session, 'background_audio'):
                    self.background_audio = self.session.background_audio
                    logger.info("🎵 Using session's background audio player")
                elif hasattr(self.session, '_ctx') and hasattr(self.session._ctx, 'background_audio'):
                    self.background_audio = self.session._ctx.background_audio
                    logger.info("🎵 Using context's background audio player")
                else:
                    # Create new background audio player
                    self.background_audio = BackgroundAudioPlayer()
                    logger.info("🎵 Created new background audio player")
            else:
                logger.warning("🎵 LiveKit BackgroundAudioPlayer not available - will use fallback")

        except Exception as e:
            logger.warning(f"🎵 Error initializing background audio: {e}")

    async def stop(self):
        """Stop current playback"""
        if self.current_task and not self.current_task.done():
            self.stop_event.set()
            self.current_task.cancel()
            try:
                await self.current_task
            except asyncio.CancelledError:
                pass

        # Stop background audio if available
        if self.background_audio:
            try:
                # BackgroundAudioPlayer doesn't have stop method, it stops automatically
                # when a new file is played or when the audio ends
                logger.info("🎵 Background audio will stop automatically")
            except Exception as e:
                logger.warning(f"Error with background audio: {e}")

        self.is_playing = False
        audio_state_manager.set_music_playing(False)
        self._cleanup_temp_files()
        logger.info("🎵 Native audio playback stopped")

    async def play_from_url(self, url: str, title: str = "Audio"):
        """Play audio from URL using LiveKit's native audio player"""
        await self.stop()  # Stop any current playback

        logger.info(f"🎵 NATIVE: Starting playback: {title}")
        self.is_playing = True
        self.stop_event.clear()

        # Set global music state
        audio_state_manager.set_music_playing(True, title)

        # Start playback task
        self.current_task = asyncio.create_task(self._play_via_native_player(url, title))

    async def _play_via_native_player(self, url: str, title: str):
        """Play audio using LiveKit's native audio player"""
        try:
            # Note: TTS announcement removed as session doesn't have direct say() method
            # Music will play directly without announcement

            # Option 1: Use background audio player if available
            if self.background_audio:
                logger.info(f"🎵 NATIVE: Using LiveKit BackgroundAudioPlayer for {title}")
                try:
                    # Download to temporary file for LiveKit to play
                    temp_file = await self._download_to_temp_file(url, title)
                    if temp_file:
                        # Play using LiveKit's native player - handles MP3 directly!
                        await self.background_audio.play(temp_file)
                        logger.info(f"🎵 NATIVE: Successfully played {title} via BackgroundAudioPlayer")
                        return
                except Exception as e:
                    logger.warning(f"🎵 NATIVE: BackgroundAudioPlayer failed: {e}")

            # Option 2: Fallback if native player unavailable
            logger.info(f"🎵 NATIVE: No native player available for {title}")

        except asyncio.CancelledError:
            logger.info(f"🎵 NATIVE: Playback cancelled: {title}")
            raise
        except Exception as e:
            logger.error(f"🎵 NATIVE: Error playing audio: {e}")
        finally:
            self.is_playing = False
            audio_state_manager.set_music_playing(False)
            logger.info(f"🎵 NATIVE: Finished playing: {title}")

            # Send music end signal via data channel
            try:
                if self.context and hasattr(self.context, 'room'):
                    import json
                    music_end_data = {
                        "type": "music_playback_stopped"
                    }
                    await self.context.room.local_participant.publish_data(
                        json.dumps(music_end_data).encode(),
                        topic="music_control"
                    )
                    logger.info("🎵 NATIVE: Sent music_playback_stopped via data channel")
            except Exception as e:
                logger.warning(f"🎵 NATIVE: Failed to send music end signal: {e}")

    async def _download_to_temp_file(self, url: str, title: str) -> Optional[str]:
        """Download MP3 to temporary file for LiveKit to play directly"""
        try:
            logger.info(f"🎵 NATIVE: Downloading {title} from {url}")
            timeout = aiohttp.ClientTimeout(total=15)

            # Create temporary file with MP3 extension
            temp_fd, temp_path = tempfile.mkstemp(suffix='.mp3', prefix='livekit_music_')
            os.close(temp_fd)  # Close the file descriptor, we'll write to the path

            # Try downloading with proper headers to avoid 403
            headers = {
                'User-Agent': 'LiveKit-Agent/1.0',
                'Accept': 'audio/mpeg, audio/*',
            }

            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 403:
                        logger.warning(f"Got 403 from CDN, trying S3 direct URL")
                        # Try S3 URL if CloudFront fails
                        if 'cloudfront' in url:
                            s3_url = url.replace('dbtnllz9fcr1z.cloudfront.net', 'cheeko-audio-files.s3.us-east-1.amazonaws.com')
                            async with session.get(s3_url, headers=headers) as s3_response:
                                if s3_response.status == 200:
                                    response = s3_response
                                    logger.info("Successfully fell back to S3 URL")
                                else:
                                    logger.error(f"S3 fallback also failed: HTTP {s3_response.status}")
                                    os.unlink(temp_path)
                                    return None
                        else:
                            logger.error(f"Failed to download: HTTP {response.status}")
                            os.unlink(temp_path)
                            return None
                    elif response.status != 200:
                        logger.error(f"Failed to download: HTTP {response.status}")
                        os.unlink(temp_path)
                        return None

                    # Write MP3 data directly to temp file
                    with open(temp_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            f.write(chunk)

                    file_size = os.path.getsize(temp_path)
                    logger.info(f"🎵 NATIVE: Downloaded {file_size} bytes to {temp_path}")

                    # Track temp file for cleanup
                    self.temp_files.append(temp_path)
                    return temp_path

        except Exception as e:
            logger.error(f"🎵 NATIVE: Error downloading {title}: {e}")
            if 'temp_path' in locals() and os.path.exists(temp_path):
                os.unlink(temp_path)
            return None

    def _cleanup_temp_files(self):
        """Clean up temporary audio files"""
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
                    logger.debug(f"🎵 NATIVE: Cleaned up temp file: {temp_file}")
            except Exception as e:
                logger.warning(f"Failed to cleanup temp file {temp_file}: {e}")
        self.temp_files.clear()

    # Note: Legacy complex TTS injection methods removed
    # Now using LiveKit's native BackgroundAudioPlayer which handles MP3 directly
    # without ffmpeg conversion - much more efficient!