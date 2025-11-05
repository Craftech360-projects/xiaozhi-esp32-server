# server.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from livekit import api
from cdn_music_bot import CDNMusicBot
import asyncio, os
from dotenv import load_dotenv
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(name)s - %(message)s'
)

# Load environment variables
load_dotenv(Path(__file__).parent / ".env")

LIVEKIT_URL = os.getenv("LIVEKIT_URL")
API_KEY = os.getenv("LIVEKIT_API_KEY")
API_SECRET = os.getenv("LIVEKIT_API_SECRET")

# Qdrant and CDN configuration
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
CLOUDFRONT_DOMAIN = os.getenv("CLOUDFRONT_DOMAIN")

app = FastAPI()

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RoomRequest(BaseModel):
    user_id: str
    language: str = None  # Optional language filter

def create_token(room_name, user_name):
    """Create access token for a user to join a room (room auto-creates)"""
    print(f"[DEBUG] Generating token for {user_name} in room {room_name}")
    at = api.AccessToken(API_KEY, API_SECRET)
    at.with_identity(user_name)
    at.with_name(user_name)
    at.with_grants(api.VideoGrants(
        room_join=True,
        room=room_name,
        can_publish=True,
        can_subscribe=True
    ))
    token = at.to_jwt()
    print(f"[DEBUG] Token generated successfully")
    return token

async def start_bot(room_name, language=None):
    """Start CDN music bot with random playback"""
    print(f"[BOT] Starting CDN music bot for room: {room_name}, language: {language or 'all'}")

    # Create token for the bot
    token = create_token(room_name, "cdn-music-bot")

    # Create and run CDN Music Bot
    bot = CDNMusicBot(
        livekit_url=LIVEKIT_URL,
        token=token,
        qdrant_url=QDRANT_URL,
        qdrant_api_key=QDRANT_API_KEY,
        cloudfront_domain=CLOUDFRONT_DOMAIN,
        language=language
    )

    await bot.run()

@app.post("/create-room")
async def create_room(req: RoomRequest):
    print(f"[API] Received request for user: {req.user_id}, language: {req.language or 'all'}")
    room_name = f"user_{req.user_id}_room"

    # Create token for client (room will auto-create on first join)
    print(f"[API] Creating token for client...")
    client_token = create_token(room_name, req.user_id)
    print(f"[API] Token created")

    # Start CDN music bot in background with language filter
    print(f"[API] Starting CDN music bot task...")
    asyncio.create_task(start_bot(room_name, req.language))
    print(f"[API] Bot task queued")

    response = {
        "roomName": room_name,
        "token": client_token,
        "livekitUrl": LIVEKIT_URL,
        "language": req.language or "all"
    }
    print(f"[API] Sending response")
    return response

@app.get("/")
async def serve_client():
    """Serve the client HTML file"""
    return FileResponse("client.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
