"""
Unified Audio Player for LiveKit Agent
Plays music/stories through the agent's main TTS channel using session.say()
"""

import logging
import asyncio
import io
from typing import Optional, AsyncIterator
import aiohttp
from ..utils.audio_state_manager import audio_state_manager

try:
    from livekit import rtc
    LIVEKIT_AVAILABLE = True
except ImportError:
    LIVEKIT_AVAILABLE = False

try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False

logger = logging.getLogger(__name__)

class UnifiedAudioPlayer:
    """Plays audio through the agent's main TTS channel using session.say()"""

    def __init__(self):
        self.session = None
        self.context = None
        self.current_task: Optional[asyncio.Task] = None
        self.is_playing = False
        self.stop_event = asyncio.Event()
        self.session_say_task = None

    def set_session(self, session):
        """Set the LiveKit agent session"""
        self.session = session
        logger.info("Unified audio player integrated with session")

    def set_context(self, context):
        """Set the job context"""
        self.context = context
        logger.info("Unified audio player integrated with context")

    async def stop(self):
        """Stop current playback and interrupt session.say() if needed"""
        # Set stop event first
        self.stop_event.set()

        # Cancel background task
        if self.current_task and not self.current_task.done():
            self.current_task.cancel()
            try:
                await self.current_task
            except asyncio.CancelledError:
                pass

        # Interrupt session.say() if running
        if self.session_say_task:
            try:
                if hasattr(self.session_say_task, 'interrupt'):
                    self.session_say_task.interrupt()
                    logger.info("🎵 UNIFIED: Interrupted speech handle")
                else:
                    logger.warning("🎵 UNIFIED: Speech handle doesn't support interruption")
            except Exception as e:
                logger.warning(f"Error interrupting speech: {e}")

        self.is_playing = False
        # Force clear music state to allow listening transitions
        audio_state_manager.force_stop_music()
        logger.info("🎵 Unified audio playback stopped")

    async def play_from_url(self, url: str, title: str = "Audio"):
        """Play audio from URL through agent's TTS channel using session.say()"""
        await self.stop()  # Stop any current playback

        logger.info(f"🎵 UNIFIED: Starting playback: {title}")
        self.is_playing = True
        self.stop_event.clear()

        # Set global music state
        audio_state_manager.set_music_playing(True, title)

        # Start playback task
        self.current_task = asyncio.create_task(self._play_via_session_say(url, title))

        # Return immediately so the agent continues
        return f"Playing {title}"

    async def _play_via_session_say(self, url: str, title: str):
        """Play audio through session.say() with audio frames"""
        try:
            if not self.session:
                logger.error("No session available for playback")
                return

            # Download and convert audio to frames
            audio_frames = await self._download_and_convert_to_frames(url, title)

            if audio_frames:
                logger.info(f"🎵 UNIFIED: Injecting {title} into TTS queue via session.say()")

                # Use session.say() with audio frames - this puts it in the TTS queue!
                speech_handle = self.session.say(
                    text=f"Playing {title}",  # Text for transcript
                    audio=audio_frames,  # Pre-recorded audio to play
                    allow_interruptions=True,  # Allow user to interrupt
                    add_to_chat_ctx=False  # Don't add music to chat context
                )

                # Store the speech handle for potential interruption
                self.session_say_task = speech_handle

                # Wait for the speech to complete
                await speech_handle

                logger.info(f"🎵 UNIFIED: Successfully queued {title} in TTS pipeline")

        except asyncio.CancelledError:
            logger.info(f"🎵 UNIFIED: Playback cancelled: {title}")
            raise
        except Exception as e:
            logger.error(f"🎵 UNIFIED: Error playing audio: {e}")
        finally:
            self.is_playing = False
            # Force clear music state to allow listening state transitions
            audio_state_manager.force_stop_music()
            logger.info(f"🎵 UNIFIED: Finished playing: {title}")

            # Send music end signal via data channel
            await self._send_music_end_signal()

            # Send agent state change to listening mode (like normal TTS does)
            await self._send_agent_state_to_listening()

    async def _download_and_convert_to_frames(self, url: str, title: str) -> Optional[AsyncIterator[rtc.AudioFrame]]:
        """Download audio and convert to AudioFrame iterator for session.say()"""
        try:
            logger.info(f"🎵 UNIFIED: Downloading {title} from {url}")

            # Download audio
            timeout = aiohttp.ClientTimeout(total=30)
            headers = {
                'User-Agent': 'LiveKit-Agent/1.0',
                'Accept': 'audio/mpeg, audio/*',
            }

            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 403 and 'cloudfront' in url:
                        # Try S3 fallback
                        s3_url = url.replace('dbtnllz9fcr1z.cloudfront.net', 'cheeko-audio-files.s3.us-east-1.amazonaws.com')
                        logger.warning("Trying S3 fallback URL")
                        async with session.get(s3_url, headers=headers) as s3_response:
                            if s3_response.status == 200:
                                audio_data = await s3_response.read()
                            else:
                                logger.error(f"Download failed: HTTP {s3_response.status}")
                                return None
                    elif response.status == 200:
                        audio_data = await response.read()
                    else:
                        logger.error(f"Download failed: HTTP {response.status}")
                        return None

            logger.info(f"🎵 UNIFIED: Downloaded {len(audio_data)} bytes")

            # Convert to audio frames
            if PYDUB_AVAILABLE and LIVEKIT_AVAILABLE:
                return await self._create_frame_iterator(audio_data)
            else:
                logger.error("Required libraries not available for audio conversion")
                return None

        except Exception as e:
            logger.error(f"🎵 UNIFIED: Error downloading/converting: {e}")
            return None

    async def _create_frame_iterator(self, audio_data: bytes):
        """Create an async iterator of AudioFrames from audio data for session.say()"""
        try:
            # Convert MP3 to PCM using pydub
            audio_segment = AudioSegment.from_mp3(io.BytesIO(audio_data))

            # Convert to 24kHz mono for LiveKit
            audio_segment = audio_segment.set_frame_rate(24000)
            audio_segment = audio_segment.set_channels(1)
            audio_segment = audio_segment.set_sample_width(2)

            raw_audio = audio_segment.raw_data
            sample_rate = 24000
            frame_duration_ms = 20
            samples_per_frame = sample_rate * frame_duration_ms // 1000

            logger.info(f"🎵 UNIFIED: Created audio frames for {len(raw_audio)} bytes")

            # Return an async iterator
            return AudioFrameIterator(raw_audio, sample_rate, samples_per_frame, self.stop_event)

        except Exception as e:
            logger.error(f"🎵 UNIFIED: Error creating frames: {e}")
            return None

    async def _send_music_end_signal(self):
        """Send music end signal via data channel"""
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
                logger.info("🎵 UNIFIED: Sent music_playback_stopped via data channel")
        except Exception as e:
            logger.warning(f"🎵 UNIFIED: Failed to send music end signal: {e}")

    async def _send_agent_state_to_listening(self):
        """Send agent state change to listening mode (mimics normal TTS completion)"""
        try:
            if self.context and hasattr(self.context, 'room'):
                import json
                agent_state_data = {
                    "type": "agent_state_changed",
                    "data": {
                        "old_state": "speaking",
                        "new_state": "listening"
                    }
                }
                await self.context.room.local_participant.publish_data(
                    json.dumps(agent_state_data).encode(),
                    reliable=True
                )
                logger.info("🎵 UNIFIED: Sent agent_state_changed (speaking -> listening) via data channel")
        except Exception as e:
            logger.warning(f"🎵 UNIFIED: Failed to send agent state change: {e}")


class AudioFrameIterator:
    """Async iterator for audio frames"""

    def __init__(self, raw_audio: bytes, sample_rate: int, samples_per_frame: int, stop_event):
        self.raw_audio = raw_audio
        self.sample_rate = sample_rate
        self.samples_per_frame = samples_per_frame
        self.stop_event = stop_event
        self.position = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.stop_event.is_set():
            raise StopAsyncIteration

        if self.position >= len(self.raw_audio):
            raise StopAsyncIteration

        # Get next chunk
        chunk = self.raw_audio[self.position:self.position + self.samples_per_frame * 2]
        self.position += self.samples_per_frame * 2

        if len(chunk) < self.samples_per_frame * 2:
            chunk += b'\x00' * (self.samples_per_frame * 2 - len(chunk))

        frame = rtc.AudioFrame(
            data=chunk,
            sample_rate=self.sample_rate,
            num_channels=1,
            samples_per_channel=self.samples_per_frame
        )

        return frame