"""
Audio State Manager for coordinating agent states with audio playback
"""

import logging
import asyncio
from typing import Optional

logger = logging.getLogger(__name__)

class AudioStateManager:
    """Manages audio playback state to coordinate with agent behavior"""

    _instance: Optional['AudioStateManager'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.is_music_playing = False
        self.current_track_title = None
        self.music_start_time = None
        self._initialized = True
        logger.info("AudioStateManager initialized")

    def set_music_playing(self, is_playing: bool, track_title: str = None):
        """Set music playback state"""
        self.is_music_playing = is_playing
        self.current_track_title = track_title

        if is_playing:
            self.music_start_time = asyncio.get_event_loop().time()
            logger.info(f"🎵 Music started: {track_title}")
        else:
            self.music_start_time = None
            logger.info(f"🎵 Music stopped")

    def force_stop_music(self):
        """Force stop music and clear all states"""
        self.is_music_playing = False
        self.current_track_title = None
        self.music_start_time = None
        logger.info("🎵 Music forcefully stopped and state cleared")

    def is_audio_playing(self) -> bool:
        """Check if any audio is currently playing"""
        return self.is_music_playing

    def should_suppress_agent_state_change(self, old_state: str, new_state: str) -> bool:
        """
        Determine if agent state change should be suppressed due to audio playback

        Args:
            old_state: Previous agent state
            new_state: New agent state

        Returns:
            True if the state change should be suppressed
        """
        if not self.is_music_playing:
            return False

        # Suppress transition from speaking to listening while music is playing
        if old_state == "speaking" and new_state == "listening":
            logger.info(f"🎵 Suppressing agent state change from {old_state} to {new_state} - music is playing")
            return True

        # Allow other state transitions
        return False

    def force_listening_state(self) -> bool:
        """
        Force the system to allow transitions to listening state
        Used when stopping music to ensure proper state restoration

        Returns:
            True if music was playing and needed to be stopped
        """
        was_playing = self.is_music_playing
        if was_playing:
            self.force_stop_music()
            logger.info("🎵 Forced listening state - music stopped, allowing state transitions")
        return was_playing

    def get_status(self) -> dict:
        """Get current audio status"""
        return {
            "is_music_playing": self.is_music_playing,
            "current_track": self.current_track_title,
            "music_start_time": self.music_start_time
        }

# Global instance
audio_state_manager = AudioStateManager()