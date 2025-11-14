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
from livekit.agents.types import DEFAULT_API_CONNECT_OPTIONS, APIConnectOptions
# We delegate WAV decoding to LiveKit's internal decoder; no need for soundfile here.

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
        """Initialize Remote Piper TTS provider.

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

    def synthesize(
        self,
        text: str,
        *,
        conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS,
    ) -> "RemotePiperChunkedStream":
        """Synthesize speech from text (LiveKit-compatible API).

        This matches the signature used by FallbackAdapter, which passes
        a `conn_options` keyword argument.
        """
        return RemotePiperChunkedStream(
            tts=self,
            input_text=text,
            conn_options=conn_options,
        )


class RemotePiperChunkedStream(tts.ChunkedStream):
    """Chunked stream for remote Piper TTS synthesis.

    Mirrors the structure of PiperTTSChunkedStream so it plays nicely with
    LiveKit's TTS pipeline and AudioEmitter.
    """

    def __init__(
        self,
        *,
        tts: RemotePiperTTS,
        input_text: str,
        conn_options: APIConnectOptions,
    ) -> None:
        super().__init__(tts=tts, input_text=input_text, conn_options=conn_options)
        self._tts: RemotePiperTTS = tts
        self._input_text = input_text
        self._base_url = tts._base_url
        self._timeout = tts._timeout
        self._sample_rate = tts.sample_rate

    async def _run(self, output_emitter: tts.AudioEmitter) -> None:
        """Run synthesis against the remote server and emit audio frames."""
        try:
            logger.info(f"🎤 RemotePiperTTS synthesizing: {self._input_text[:50]}...")

            # Call remote Piper HTTP server
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    f"{self._base_url}/synthesize",
                    json={"text": self._input_text},
                )
                response.raise_for_status()
                audio_data = response.content

            logger.info(f"🎤 RemotePiperTTS: Received {len(audio_data)} bytes")

            # Forward the WAV bytes directly; LiveKit's decoder will parse RIFF/WAVE
            audio_bytes = audio_data

            # Initialize the audio emitter
            request_id = f"remote_piper_{id(self)}"
            output_emitter.initialize(
                request_id=request_id,
                sample_rate=self._sample_rate,
                num_channels=1,
                mime_type="audio/wav",
            )

            # Stream audio in chunks
            chunk_size = 4096
            for i in range(0, len(audio_bytes), chunk_size):
                chunk = audio_bytes[i : i + chunk_size]
                output_emitter.push(chunk)

                if i % (chunk_size * 4) == 0:
                    await asyncio.sleep(0)

            logger.info("🎤 RemotePiperTTS: Audio streaming completed")
            output_emitter.flush()

        except Exception as e:
            logger.error(f"❌ RemotePiperTTS error: {e}", exc_info=True)
            raise
