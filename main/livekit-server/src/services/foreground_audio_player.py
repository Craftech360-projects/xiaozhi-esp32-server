"""
Foreground Audio Player for LiveKit Agent
Plays music/stories through the agent's main audio channel (not background)
"""

import logging
import asyncio
import io
from typing import Optional
import aiohttp
from ..utils.audio_state_manager import audio_state_manager

try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False

logger = logging.getLogger(__name__)

class ForegroundAudioPlayer:
    """Plays audio through the agent's main TTS channel (foreground mode)"""

    def __init__(self):
        self.session = None
        self.context = None
        self.current_task: Optional[asyncio.Task] = None
        self.is_playing = False
        self.stop_event = asyncio.Event()

    def set_session(self, session):
        """Set the LiveKit agent session"""
        self.session = session
        logger.info("Foreground audio player integrated with session")

    def set_context(self, context):
        """Set the job context"""
        self.context = context
        logger.info("Foreground audio player integrated with context")

    async def stop(self):
        """Stop current playback"""
        if self.current_task and not self.current_task.done():
            self.stop_event.set()
            self.current_task.cancel()
            try:
                await self.current_task
            except asyncio.CancelledError:
                pass
        self.is_playing = False

        # Clear global music state
        audio_state_manager.set_music_playing(False)

        logger.info("🎵 Foreground audio playback stopped")

    async def play_from_url(self, url: str, title: str = "Audio"):
        """Play audio from URL in foreground (agent stops talking)"""
        await self.stop()  # Stop any current playback

        logger.info(f"🎵 FOREGROUND: Starting playback: {title}")
        self.is_playing = True
        self.stop_event.clear()

        # Set global music state
        audio_state_manager.set_music_playing(True, title)

        # Start playback task
        self.current_task = asyncio.create_task(self._play_foreground_audio(url, title))

    async def _play_foreground_audio(self, url: str, title: str):
        """Play audio in foreground through main audio channel"""
        try:
            logger.info(f"🎵 FOREGROUND: Downloading {title} from {url}")

            # Download audio with timeout
            timeout = aiohttp.ClientTimeout(total=15)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        logger.error(f"Failed to download: HTTP {response.status}")
                        return

                    audio_data = await response.read()
                    logger.info(f"🎵 FOREGROUND: Downloaded {len(audio_data)} bytes for {title}")

            if not PYDUB_AVAILABLE:
                logger.error("Pydub not available - cannot play audio")
                return

            # Convert to WAV and play through session
            await self._play_through_session_audio(audio_data, title)

        except asyncio.CancelledError:
            logger.info(f"🎵 FOREGROUND: Playback cancelled: {title}")
            raise
        except Exception as e:
            logger.error(f"🎵 FOREGROUND: Error playing audio: {e}")
        finally:
            self.is_playing = False
            logger.info(f"🎵 FOREGROUND: Finished playing: {title}")

            # Clear global music state
            audio_state_manager.set_music_playing(False)

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
                    logger.info("🎵 FOREGROUND: Sent music_playback_stopped via data channel")
            except Exception as e:
                logger.warning(f"🎵 FOREGROUND: Failed to send music end signal: {e}")

    async def _play_through_session_audio(self, audio_data: bytes, title: str):
        """Play audio through the session's main audio channel"""
        try:
            # Convert MP3 to appropriate format
            audio_segment = AudioSegment.from_mp3(io.BytesIO(audio_data))

            # Get room for direct audio streaming
            room = None
            if self.context and hasattr(self.context, 'room'):
                room = self.context.room
            elif self.session and hasattr(self.session, 'room'):
                room = self.session.room

            if room:
                await self._stream_directly_to_room(room, audio_segment, title)
            else:
                logger.error("No room available for audio streaming")

        except Exception as e:
            logger.error(f"🎵 FOREGROUND: Error in session audio: {e}")

    async def _stream_directly_to_room(self, room, audio_segment, title: str):
        """Stream audio directly to room's main audio track"""
        try:
            from livekit import rtc

            # Create temporary audio source for this playback
            audio_source = rtc.AudioSource(48000, 1)  # 48kHz, mono
            audio_track = rtc.LocalAudioTrack.create_audio_track("foreground_music", audio_source)

            # Publish track temporarily
            publication = await room.local_participant.publish_track(audio_track)
            logger.info(f"🎵 FOREGROUND: Published temporary track: {publication.sid}")

            try:
                # Convert audio to proper format
                audio_segment = audio_segment.set_frame_rate(48000)
                audio_segment = audio_segment.set_channels(1)
                audio_segment = audio_segment.set_sample_width(2)

                raw_audio = audio_segment.raw_data
                sample_rate = 48000
                frame_duration_ms = 20
                samples_per_frame = sample_rate * frame_duration_ms // 1000
                total_samples = len(raw_audio) // 2
                total_frames = total_samples // samples_per_frame

                logger.info(f"🎵 FOREGROUND: Streaming {total_frames} frames for {title}")

                # Stream all frames
                for frame_num in range(total_frames):
                    if self.stop_event.is_set():
                        logger.info("🎵 FOREGROUND: Playback stopped")
                        break

                    start_byte = frame_num * samples_per_frame * 2
                    end_byte = start_byte + (samples_per_frame * 2)
                    frame_data = raw_audio[start_byte:end_byte]

                    if len(frame_data) < samples_per_frame * 2:
                        frame_data += b'\x00' * (samples_per_frame * 2 - len(frame_data))

                    frame = rtc.AudioFrame(
                        data=frame_data,
                        sample_rate=sample_rate,
                        num_channels=1,
                        samples_per_channel=samples_per_frame
                    )

                    await audio_source.capture_frame(frame)
                    await asyncio.sleep(frame_duration_ms / 1000.0)

                    # Log progress occasionally
                    if frame_num % 1000 == 0:  # Every 20 seconds
                        progress = (frame_num / total_frames) * 100
                        logger.debug(f"🎵 FOREGROUND: Progress: {progress:.1f}%")

                logger.info(f"🎵 FOREGROUND: Completed streaming {title}")

            finally:
                # Clean up the temporary track
                try:
                    await room.local_participant.unpublish_track(publication.sid)
                    logger.info("🎵 FOREGROUND: Cleaned up temporary track")
                except Exception as cleanup_error:
                    logger.warning(f"🎵 FOREGROUND: Cleanup error: {cleanup_error}")

        except Exception as e:
            logger.error(f"🎵 FOREGROUND: Streaming error: {e}")