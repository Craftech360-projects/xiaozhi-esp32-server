"""
Remote Piper TTS Provider
Connects to remote Piper server via HTTP API
"""
import asyncio
import logging
import httpx
import io
from typing import Optional
from livekit.agents import tts
import soundfile as sf

logger = logging.getLogger(__name__)


class RemotePiperTTS(tts.TTS):
    """Remote Piper TTS implementation via HTTP API"""

    def __init__(
        self,
        *,
        base_url: str = "http://localhost:8001",
        timeout: float = 30.0,
        sample_rate: int = 22050,
    ):
        """
        Initialize Remote Piper TTS provider

        Args:
            base_url: URL of remote Piper server
            timeout: Request timeout in seconds
            sample_rate: Audio sample rate
        """
        super().__init__(
            capabilities=tts.TTSCapabilities(streaming=False),
            sample_rate=sample_rate,
            num_channels=1,
        )

        self._base_url = base_url.rstrip('/')
        self._timeout = timeout

        logger.info(
            f"Initialized RemotePiperTTS with base_url={base_url}, "
            f"timeout={timeout}s, sample_rate={sample_rate}"
        )

    def synthesize(self, text: str) -> "ChunkedStream":
        """
        Synthesize speech from text

        Args:
            text: Text to synthesize

        Returns:
            ChunkedStream with audio data
        """
        return ChunkedStream(
            text=text,
            base_url=self._base_url,
            timeout=self._timeout,
            sample_rate=self._sample_rate,
        )


class ChunkedStream(tts.ChunkedStream):
    """Stream for remote Piper TTS synthesis"""

    def __init__(
        self,
        *,
        text: str,
        base_url: str,
        timeout: float,
        sample_rate: int,
    ):
        super().__init__()
        self._text = text
        self._base_url = base_url
        self._timeout = timeout
        self._sample_rate = sample_rate

    async def _run(self):
        """Run synthesis and yield audio chunks"""
        try:
            logger.info(f"🎤 RemotePiperTTS synthesizing: {self._text[:50]}...")
            
            # Send request to remote server
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    f"{self._base_url}/synthesize",
                    json={'text': self._text}
                )
                
                response.raise_for_status()
                audio_data = response.content
            
            logger.info(f"🎤 RemotePiperTTS: Received {len(audio_data)} bytes")
            
            # Read WAV file
            audio_buffer = io.BytesIO(audio_data)
            data, samplerate = sf.read(audio_buffer, dtype='int16')
            
            # Convert to bytes
            audio_bytes = data.tobytes()
            
            # Yield as single chunk (non-streaming)
            request_id = self._text[:20]  # Use first 20 chars as ID
            
            yield tts.SynthesizedAudio(
                request_id=request_id,
                frame=tts.AudioFrame(
                    data=audio_bytes,
                    sample_rate=samplerate,
                    num_channels=1,
                    samples_per_channel=len(data),
                ),
            )
            
            logger.info(f"🎤 RemotePiperTTS: Audio streaming completed")
        
        except Exception as e:
            logger.error(f"❌ RemotePiperTTS error: {e}")
            raise
