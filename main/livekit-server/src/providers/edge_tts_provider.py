"""
EdgeTTS provider for LiveKit Agents
Wraps Microsoft Edge TTS service for use with LiveKit
"""

import asyncio
import logging
import uuid
from typing import AsyncIterable, Optional, Union
from dataclasses import dataclass

try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False

try:
    from livekit import rtc
    from livekit.agents import tts, utils
    from livekit.agents.types import DEFAULT_API_CONNECT_OPTIONS, APIConnectOptions
    LIVEKIT_AVAILABLE = True
except ImportError:
    LIVEKIT_AVAILABLE = False


logger = logging.getLogger(__name__)


@dataclass
class _EdgeTTSOptions:
    """Options for EdgeTTS configuration"""
    voice: str
    rate: str
    volume: str
    pitch: str


class EdgeTTS(tts.TTS if LIVEKIT_AVAILABLE else object):
    """EdgeTTS provider for LiveKit Agents"""

    def __init__(
        self,
        voice: str = "en-US-AvaNeural",
        rate: str = "+0%",
        volume: str = "+0%",
        pitch: str = "+0Hz",
        sample_rate: int = 22050,
        channels: int = 1
    ):
        if not EDGE_TTS_AVAILABLE:
            raise ImportError("edge-tts is not installed. Install with: pip install edge-tts")

        if not LIVEKIT_AVAILABLE:
            raise ImportError("livekit is not installed")


        # Initialize the parent TTS class with capabilities
        super().__init__(
            capabilities=tts.TTSCapabilities(streaming=False),
            sample_rate=sample_rate,
            num_channels=channels,
        )

        self._opts = _EdgeTTSOptions(
            voice=voice,
            rate=rate,
            volume=volume,
            pitch=pitch
        )

        logger.info(f"🎤 EdgeTTS initialized with voice: {voice}")

    def update_options(
        self,
        *,
        voice: Optional[str] = None,
        rate: Optional[str] = None,
        volume: Optional[str] = None,
        pitch: Optional[str] = None
    ) -> None:
        """Update the TTS options dynamically"""
        if voice is not None:
            self._opts.voice = voice
        if rate is not None:
            self._opts.rate = rate
        if volume is not None:
            self._opts.volume = volume
        if pitch is not None:
            self._opts.pitch = pitch

    def synthesize(
        self,
        text: str,
        *,
        conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS,
    ) -> "EdgeTTSChunkedStream":
        """Create a chunked stream for text synthesis"""
        return EdgeTTSChunkedStream(
            tts=self,
            input_text=text,
            conn_options=conn_options
        )

    @staticmethod
    async def list_voices() -> list:
        """
        List available EdgeTTS voices

        Returns:
            List of available voice dictionaries
        """
        if not EDGE_TTS_AVAILABLE:
            return []

        try:
            # Use the correct EdgeTTS API to list voices
            voices = await edge_tts.list_voices()

            # Format voices for easier use
            formatted_voices = []
            for voice in voices:
                formatted_voices.append({
                    'name': voice.get('Name', ''),
                    'short_name': voice.get('ShortName', ''),
                    'gender': voice.get('Gender', ''),
                    'locale': voice.get('Locale', ''),
                    'language': voice.get('Locale', '').split('-')[0] if voice.get('Locale') else '',
                    'country': voice.get('Locale', '').split('-')[1] if '-' in voice.get('Locale', '') else '',
                    'suggested_codec': voice.get('SuggestedCodec', ''),
                    'friendly_name': voice.get('FriendlyName', ''),
                    'status': voice.get('Status', ''),
                    'voice_tag': voice.get('VoiceTag', {})
                })

            logger.info(f"🎤 EdgeTTS: Found {len(formatted_voices)} voices")
            return formatted_voices

        except Exception as e:
            logger.error(f"🎤 EdgeTTS: Error listing voices: {e}")
            return []

    @staticmethod
    async def get_voices_by_language(language: str) -> list:
        """
        Get voices filtered by language

        Args:
            language: Language code (e.g., 'en', 'hi', 'te')

        Returns:
            List of voices for the specified language
        """
        all_voices = await EdgeTTS.list_voices()
        return [
            voice for voice in all_voices
            if voice['language'].lower() == language.lower()
        ]

    @staticmethod
    async def get_child_friendly_voices() -> list:
        """
        Get voices that are suitable for children

        Returns:
            List of child-friendly voices
        """
        all_voices = await EdgeTTS.list_voices()

        # Filter for voices that are typically child-friendly
        child_friendly_keywords = [
            'child', 'kid', 'young', 'girl', 'boy', 'jenny', 'aria',
            'ava', 'emma', 'olivia', 'ryan', 'jacob', 'libby', 'maisie'
        ]

        child_voices = []
        for voice in all_voices:
            voice_name = voice['name'].lower()
            friendly_name = voice['friendly_name'].lower()

            # Check if voice name contains child-friendly keywords
            if any(keyword in voice_name or keyword in friendly_name
                   for keyword in child_friendly_keywords):
                child_voices.append(voice)

        # If no specific child voices found, return some generally good voices for children
        if not child_voices:
            preferred_voices = [
                'en-US-AvaNeural',
                'en-US-EmmaNeural',
                'en-US-JennyNeural',
                'en-US-AriaNeural',
                'en-GB-LibbyNeural',
                'en-GB-MaisieNeural'
            ]

            child_voices = [
                voice for voice in all_voices
                if voice['short_name'] in preferred_voices
            ]

        logger.info(f"🎤 EdgeTTS: Found {len(child_voices)} child-friendly voices")
        return child_voices

    def __str__(self):
        return f"EdgeTTS(voice={self._opts.voice}, rate={self._opts.rate}, volume={self._opts.volume})"


class EdgeTTSChunkedStream(tts.ChunkedStream if LIVEKIT_AVAILABLE else object):
    """Chunked stream for EdgeTTS synthesis"""

    def __init__(
        self,
        *,
        tts: EdgeTTS,
        input_text: str,
        conn_options: APIConnectOptions,
    ) -> None:
        super().__init__(tts=tts, input_text=input_text, conn_options=conn_options)
        self._tts: EdgeTTS = tts
        self._opts = self._tts._opts

    async def _run(self, output_emitter: tts.AudioEmitter) -> None:
        """Run the TTS synthesis and emit audio frames"""
        try:
            logger.info(f"🎤 EdgeTTS synthesizing: {self._input_text[:50]}...")

            # Create EdgeTTS communicate instance
            communicate = edge_tts.Communicate(
                text=self._input_text,
                voice=self._opts.voice,
                rate=self._opts.rate,
                volume=self._opts.volume,
                pitch=self._opts.pitch
            )

            # Initialize the audio emitter with MP3 format (same as ElevenLabs)
            request_id = str(uuid.uuid4())[:8]
            output_emitter.initialize(
                request_id=request_id,
                sample_rate=self._tts.sample_rate,
                num_channels=self._tts.num_channels,
                mime_type="audio/mp3",
            )

            # Stream audio data directly as MP3 (same as ElevenLabs approach)
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    # Push MP3 data directly without conversion
                    output_emitter.push(chunk["data"])

            # Flush to signal completion
            output_emitter.flush()
            logger.info(f"🎤 EdgeTTS: Audio streaming completed")

        except Exception as e:
            logger.error(f"🎤 EdgeTTS synthesis error: {e}")
            raise


# Simple async function to get audio data without LiveKit frames
async def generate_audio_bytes(text: str, voice: str = "en-US-AvaNeural") -> bytes:
    """
    Simple function to generate audio bytes from text
    Useful for testing or non-LiveKit applications
    """
    try:
        communicate = edge_tts.Communicate(text=text, voice=voice)

        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]

        return audio_data
    except Exception as e:
        logger.error(f"Error generating audio bytes: {e}")
        return b""


# Convenience function for quick testing
async def test_edge_tts():
    """Test EdgeTTS functionality"""
    if not EDGE_TTS_AVAILABLE:
        print("EdgeTTS not available - install with: pip install edge-tts")
        return

    # List available voices
    voices = await EdgeTTS.list_voices()
    print(f"Available voices: {len(voices)}")

    # Show some English voices
    en_voices = await EdgeTTS.get_voices_by_language('en')
    print(f"English voices: {len(en_voices)}")
    for voice in en_voices[:5]:  # Show first 5
        print(f"  - {voice['short_name']}: {voice['friendly_name']}")

    # Show child-friendly voices
    child_voices = await EdgeTTS.get_child_friendly_voices()
    print(f"Child-friendly voices: {len(child_voices)}")
    for voice in child_voices[:3]:  # Show first 3
        print(f"  - {voice['short_name']}: {voice['friendly_name']}")

    # Test simple audio generation
    print("\nTesting audio generation...")
    audio_data = await generate_audio_bytes("Hello, I'm Cheeko!", "en-US-AvaNeural")
    print(f"Generated {len(audio_data)} bytes of audio")


if __name__ == "__main__":
    asyncio.run(test_edge_tts())