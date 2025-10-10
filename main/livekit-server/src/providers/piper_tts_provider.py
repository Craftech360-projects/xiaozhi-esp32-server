"""
Piper TTS Provider for LiveKit
Provides fast, lightweight, fully local text-to-speech using Piper
"""
import asyncio
import io
import logging
import wave
import numpy as np
from typing import Optional
from livekit.agents import tts

logger = logging.getLogger(__name__)

try:
    from piper import PiperVoice
    PIPER_AVAILABLE = True
except ImportError:
    PIPER_AVAILABLE = False
    logger.warning("Piper TTS not installed. Install with: pip install piper-tts")


class PiperTTS(tts.TTS):
    """Piper TTS implementation for fast local text-to-speech"""

    def __init__(
        self,
        *,
        voice: str = "en_US-lessac-medium",
        sample_rate: int = 22050,
    ):
        """
        Initialize Piper TTS provider

        Args:
            voice: Voice name (downloads automatically if needed)
            sample_rate: Output audio sample rate (default 22050)
        """
        super().__init__(
            capabilities=tts.TTSCapabilities(streaming=False),
            sample_rate=sample_rate,
            num_channels=1,
        )

        if not PIPER_AVAILABLE:
            raise ImportError(
                "Piper TTS is not installed. "
                "Install with: pip install piper-tts"
            )

        self._voice_name = voice
        self._sample_rate = sample_rate
        self._voice: Optional[PiperVoice] = None

        logger.info(
            f"Initialized Piper TTS with voice={voice}, "
            f"sample_rate={sample_rate}"
        )

    async def _ensure_voice_loaded(self):
        """Lazy load the voice model"""
        if self._voice is None:
            from pathlib import Path

            logger.info(f"Loading Piper voice: {self._voice_name}")

            # Use model_cache folder instead of user home directory
            models_dir = Path(__file__).parent.parent.parent / "model_cache" / "piper" / "voices"
            models_dir.mkdir(parents=True, exist_ok=True)

            model_path = models_dir / f"{self._voice_name}.onnx"
            config_path = models_dir / f"{self._voice_name}.onnx.json"

            logger.info(f"Piper model directory: {models_dir}")

            # Download model if not present
            if not model_path.exists() or not config_path.exists():
                logger.info(f"Downloading Piper model: {self._voice_name}")
                await self._download_model(models_dir)

            loop = asyncio.get_event_loop()

            # Load voice in thread pool to avoid blocking
            self._voice = await loop.run_in_executor(
                None,
                lambda: PiperVoice.load(str(model_path), use_cuda=False),
            )

            logger.info(f"Piper voice loaded: {self._voice_name}")

    async def _download_model(self, models_dir: "Path"):
        """Download Piper model files from HuggingFace"""
        import urllib.request

        base_url = "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/"

        files = [
            f"{self._voice_name}.onnx",
            f"{self._voice_name}.onnx.json",
        ]

        loop = asyncio.get_event_loop()

        for filename in files:
            filepath = models_dir / filename
            if not filepath.exists():
                url = base_url + filename
                logger.info(f"Downloading {filename} from HuggingFace...")
                await loop.run_in_executor(
                    None,
                    urllib.request.urlretrieve,
                    url,
                    str(filepath),
                )
                logger.info(f"Downloaded {filename}")

    def synthesize(self, text: str, *, conn_options: Optional[any] = None) -> "ChunkedStream":
        """
        Synthesize text to speech

        Args:
            text: Text to synthesize
            conn_options: Connection options (passed to stream)

        Returns:
            ChunkedStream with audio data
        """
        return PiperTTSStream(
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
        # Ensure voice model is loaded
        await self._ensure_voice_loaded()

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
        Synchronous synthesis using Piper Python API

        Returns audio as WAV bytes
        """
        try:
            # Synthesize audio (returns generator of AudioChunk objects)
            audio_generator = self._voice.synthesize(text)

            # Collect all audio chunks
            audio_chunks = []
            for audio_chunk in audio_generator:
                # AudioChunk has .audio_float_array containing float32 samples
                # Convert from float32 [-1, 1] to int16 [-32768, 32767]
                audio_int16 = (audio_chunk.audio_float_array * 32767).astype(np.int16)
                audio_chunks.append(audio_int16)

            # Concatenate all chunks
            audio_data = np.concatenate(audio_chunks)

            # Convert to WAV bytes
            wav_bytes = self._numpy_to_wav(audio_data, self._voice.config.sample_rate)

            logger.debug(f"Generated audio: {len(wav_bytes)} bytes")
            return wav_bytes

        except Exception as e:
            logger.error(f"Error synthesizing audio: {e}")
            import traceback
            traceback.print_exc()
            return self._generate_silence(1.0)

    def _numpy_to_wav(self, audio_np: np.ndarray, sample_rate: int) -> bytes:
        """
        Convert numpy array to WAV bytes

        Args:
            audio_np: Audio data as numpy array (int16)
            sample_rate: Sample rate

        Returns:
            WAV file as bytes
        """
        # Ensure audio is int16
        if audio_np.dtype != np.int16:
            audio_np = audio_np.astype(np.int16)

        # Create WAV file in memory
        wav_buffer = io.BytesIO()

        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_np.tobytes())

        return wav_buffer.getvalue()

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
        logger.info("Piper TTS closed")


class PiperTTSStream(tts.ChunkedStream):
    """Audio stream for Piper TTS output"""

    def __init__(
        self,
        *,
        tts_instance: PiperTTS,
        text: str,
        sample_rate: int,
        conn_options: Optional[any] = None,
    ):
        """
        Initialize TTS stream

        Args:
            tts_instance: PiperTTS instance
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

            # Initialize the emitter
            output_emitter.initialize(
                request_id="",
                sample_rate=self._sample_rate,
                num_channels=1,
                mime_type="audio/wav",
            )

            # Push audio data
            output_emitter.push(self._audio_data)

            # Flush to complete
            output_emitter.flush()

        except Exception as e:
            logger.error(f"Error in Piper synthesis: {e}")
            import traceback
            traceback.print_exc()

    async def aclose(self):
        """Close stream"""
        await super().aclose()
        self._audio_data = None
