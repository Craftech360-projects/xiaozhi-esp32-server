# media_bot.py
import asyncio
from livekit.agents import RoomAgent, WorkerOptions
import os

LIVEKIT_URL = os.getenv("LIVEKIT_URL")

class AudioBot(RoomAgent):
    def __init__(self, playlist, token):
        self.playlist = playlist
        super().__init__(WorkerOptions(url=LIVEKIT_URL, token=token))

    async def on_ready(self):
        print("🎶 Media Bot connected, starting playlist...")
        for song in self.playlist:
            print(f"▶️ Playing: {song}")
            await self.publish_audio_file(song)
        print("✅ Playlist finished")
