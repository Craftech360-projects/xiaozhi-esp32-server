"""
pyttsx3 TTS Provider for LiveKit
Provides fully local, lightweight text-to-speech using system TTS engines
"""
import asyncio
import io
import logging
import wave
from typing import Optional
from livekit.agents import tts

logger = logging.getLogger(__name__)

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False
    logger.warning("pyttsx3 not installed. Install with: pip install pyttsx3")


class Pyttsx3TTS(tts.TTS):
    """pyttsx3 TTS implementation for local text-to-speech"""

    def __init__(
        self,
        *,
        rate: int = 150,
        volume: float = 1.0,
        voice_index: int = 0,
        sample_rate: int = 24000,
    ):
        """
        Initialize pyttsx3 TTS provider

        Args:
            rate: Speech rate (words per minute, default 150)
            volume: Volume level (0.0 to 1.0, default 1.0)
            voice_index: Index of voice to use (default 0 for first available)
            sample_rate: Output audio sample rate
        """
        super().__init__(
            capabilities=tts.TTSCapabilities(streaming=False),
            sample_rate=sample_rate,
            num_channels=1,
        )

        if not PYTTSX3_AVAILABLE:
            raise ImportError(
                "pyttsx3 is not installed. "
                "Install with: pip install pyttsx3"
            )

        self._rate = rate
        self._volume = volume
        self._voice_index = voice_index
        self._sample_rate = sample_rate
        self._engine: Optional[pyttsx3.Engine] = None

        logger.info(
            f"Initialized pyttsx3 TTS with rate={rate}, "
            f"volume={volume}, voice_index={voice_index}"
        )

    def _ensure_engine_initialized(self):
        """Lazy initialize the TTS engine"""
        if self._engine is None:
            logger.info("Initializing pyttsx3 engine...")
            self._engine = pyttsx3.init()

            # Set properties
            self._engine.setProperty('rate', self._rate)
            self._engine.setProperty('volume', self._volume)

            # Set voice
            voices = self._engine.getProperty('voices')
            if voices and len(voices) > self._voice_index:
                self._engine.setProperty('voice', voices[self._voice_index].id)
                logger.info(f"Using voice: {voices[self._voice_index].name}")
            else:
                logger.warning(f"Voice index {self._voice_index} not available, using default")

            logger.info("pyttsx3 engine initialized")

    def synthesize(self, text: str, *, conn_options: Optional[any] = None) -> "ChunkedStream":
        """
        Synthesize text to speech

        Args:
            text: Text to synthesize
            conn_options: Connection options (passed to stream)

        Returns:
            ChunkedStream with audio data
        """
        return Pyttsx3TTSStream(
            tts_instance=self,
            text=text,
            sample_rate=self._sample_rate,
            conn_options=conn_options,
        )

    async def _synthesize_audio(self, text: str) -> bytes:
        """
        Internal method to synthesize audio

        Args:
            text: Text to synthesize

        Returns:
            Audio data as bytes (WAV format)
        """
        self._ensure_engine_initialized()

        logger.debug(f"Synthesizing text: {text[:50]}...")

        # Run synthesis in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        audio_data = await loop.run_in_executor(
            None,
            self._synthesize_sync,
            text,
        )

        return audio_data

    def _synthesize_sync(self, text: str) -> bytes:
        """
        Synchronous synthesis (run in thread pool)

        Returns audio as WAV bytes
        """
        try:
            import tempfile
            import os

            # Create temporary file for audio output
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                tmp_path = tmp_file.name

            # Save to file (pyttsx3 saves to file)
            self._engine.save_to_file(text, tmp_path)
            self._engine.runAndWait()

            # Read the generated file
            with open(tmp_path, 'rb') as f:
                wav_bytes = f.read()

            # Clean up temporary file
            os.unlink(tmp_path)

            return wav_bytes

        except Exception as e:
            logger.error(f"Error synthesizing audio: {e}")
            # Return silence as fallback
            return self._generate_silence(1.0)

    def _generate_silence(self, duration: float) -> bytes:
        """Generate silent audio"""
        import numpy as np

        num_samples = int(duration * self._sample_rate)
        silence = np.zeros(num_samples, dtype=np.int16)

        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(self._sample_rate)
            wav_file.writeframes(silence.tobytes())

        return wav_buffer.getvalue()

    async def aclose(self):
        """Cleanup resources"""
        if self._engine is not None:
            self._engine.stop()
            self._engine = None
            logger.info("pyttsx3 TTS closed")


class Pyttsx3TTSStream(tts.ChunkedStream):
    """Audio stream for pyttsx3 TTS output"""

    def __init__(
        self,
        *,
        tts_instance: Pyttsx3TTS,
        text: str,
        sample_rate: int,
        conn_options: Optional[any] = None,
    ):
        """
        Initialize TTS stream

        Args:
            tts_instance: Pyttsx3TTS instance
            text: Text to synthesize
            sample_rate: Audio sample rate
            conn_options: Connection options (passed to ChunkedStream)
        """
        super().__init__(
            tts=tts_instance,
            input_text=text,
            conn_options=conn_options,
        )
        self._tts = tts_instance
        self._text = text
        self._sample_rate = sample_rate
        self._audio_data: Optional[bytes] = None

    async def _run(self, output_emitter):
        """Main synthesis task - required by ChunkedStream abstract class"""
        try:
            # Synthesize audio
            self._audio_data = await self._tts._synthesize_audio(self._text)

            # Emit the audio chunk using the output_emitter
            output_emitter(
                tts.SynthesizedAudio(
                    request_id="",
                    segment_id="",
                    frame=self._audio_data,
                )
            )
        except Exception as e:
            logger.error(f"Error in pyttsx3 synthesis: {e}")

    async def aclose(self):
        """Close stream"""
        await super().aclose()
        self._audio_data = None
