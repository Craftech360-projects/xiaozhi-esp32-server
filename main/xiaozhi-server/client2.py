import asyncio
import logging
from livekit import rtc, Room, RoomOptions

# --- Configuration ---
# !!! Replace with your LiveKit server URL and a valid Token !!!
# You can generate a token using the livekit-cli:
# livekit-cli create-token --join --room YOUR_ROOM_NAME --identity PYTHON_PUBLISHER
LIVEKIT_URL = "ws://your-livekit-server.com"
LIVEKIT_TOKEN = "YOUR_LIVEKIT_TOKEN"
# ---------------------


async def main():
    """
    Connects to a LiveKit room, captures audio from the default
    microphone, and publishes it. The SDK handles encoding as Opus
    by default.
    """
    room = Room()

    print(f"Connecting to {LIVEKIT_URL}...")
    try:
        await room.connect(LIVEKIT_URL, LIVEKIT_TOKEN)
        print("Successfully connected to room.")

        # 1. Create a local audio track from the default microphone
        # This is the high-level equivalent of your C code's 'capturer'
        # The SDK will use PyAudio to access the mic.
        track = rtc.LocalAudioTrack.create_microphone_track()

        # 2. Publish the track to the room
        # The SDK automatically handles encoding it to OPUS
        # before sending.
        print("Publishing microphone audio (as Opus by default)...")
        await room.local_participant.publish_track(track)
        print("Track published. You are now sending audio.")

        # Keep the script running to continue publishing
        # Press Ctrl+C to stop
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping...")

    except Exception as e:
        logging.error("An error occurred: %s", e, exc_info=True)

    finally:
        # Clean up and disconnect
        if room.is_connected:
            print("Disconnecting from room...")
            await room.disconnect()
            print("Disconnected.")

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO,
                        handlers=[
                            logging.FileHandler("publish_speech.log"),
                            logging.StreamHandler()
                        ])
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass