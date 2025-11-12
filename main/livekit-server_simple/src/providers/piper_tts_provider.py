"""
Piper TTS Provider for LiveKit
Provides local text-to-speech using Piper
"""
import asyncio
import logging
import subprocess
import tempfile
import os
import wave
from typing import Optional
from dataclasses import dataclass
from pathlib import Path

try:
    from livekit import rtc
    from livekit.agents import tts, utils
    from livekit.agents.types import DEFAULT_API_CONNECT_OPTIONS, APIConnectOptions
    LIVEKIT_AVAILABLE = True
except ImportError:
    LIVEKIT_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class _PiperTTSOptions:
    """Options for Piper TTS configuration"""
    voice: str
    model_path: Optional[str]
    sample_rate: int
    speaker: Optional[int]


class PiperTTS(tts.TTS if LIVEKIT_AVAILABLE else object):
    """Piper TTS provider for LiveKit Agents - Local Neural TTS"""

    def __init__(
        self,
        voice: str = "en_US-amy-medium",
        model_path: Optional[str] = None,
        sample_rate: int = 22050,
        speaker: Optional[int] = None,
        piper_binary: str = "piper",
    ):
        """
        Initialize Piper TTS provider

        Args:
            voice: Voice model name (e.g., 'en_US-amy-medium', 'en_US-lessac-medium')
            model_path: Path to .onnx model file (optional, will auto-download if not provided)
            sample_rate: Output sample rate (default: 22050)
            speaker: Speaker ID for multi-speaker models (optional)
            piper_binary: Path to piper executable (default: 'piper' in PATH)
        """
        if not LIVEKIT_AVAILABLE:
            raise ImportError("livekit is not installed")

        # Check if piper is available
        try:
            result = subprocess.run(
                [piper_binary, "--help"],
                capture_output=True,
                timeout=5
            )
            # --help returns exit code 0, if command not found it raises FileNotFoundError
            if result.returncode not in [0, 2]:  # Accept both 0 and 2 as valid
                raise subprocess.CalledProcessError(result.returncode, [piper_binary, "--help"])
        except FileNotFoundError:
            raise ImportError(
                f"Piper TTS binary '{piper_binary}' not found. "
                "Install with: pip install piper-tts OR download from https://github.com/rhasspy/piper"
            )
        except subprocess.TimeoutExpired:
            raise ImportError(
                f"Piper TTS binary '{piper_binary}' timed out. "
                "Check your piper installation."
            )

        # Initialize the parent TTS class with capabilities
        super().__init__(
            capabilities=tts.TTSCapabilities(streaming=False),
            sample_rate=sample_rate,
            num_channels=1,
        )

        self._opts = _PiperTTSOptions(
            voice=voice,
            model_path=model_path,
            sample_rate=sample_rate,
            speaker=speaker
        )
        self._piper_binary = piper_binary

        logger.info(f"🎤 PiperTTS initialized with voice: {voice}, sample_rate: {sample_rate}")

    def update_options(
        self,
        *,
        voice: Optional[str] = None,
        speaker: Optional[int] = None
    ) -> None:
        """Update the TTS options dynamically"""
        if voice is not None:
            self._opts.voice = voice
        if speaker is not None:
            self._opts.speaker = speaker

    def synthesize(
        self,
        text: str,
        *,
        conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS,
    ) -> "PiperTTSChunkedStream":
        """Create a chunked stream for text synthesis"""
        return PiperTTSChunkedStream(
            tts=self,
            input_text=text,
            conn_options=conn_options
        )

    def __str__(self):
        return f"PiperTTS(voice={self._opts.voice}, sample_rate={self._opts.sample_rate})"


class PiperTTSChunkedStream(tts.ChunkedStream if LIVEKIT_AVAILABLE else object):
    """Chunked stream for Piper TTS synthesis"""

    def __init__(
        self,
        *,
        tts: PiperTTS,
        input_text: str,
        conn_options: APIConnectOptions,
    ) -> None:
        super().__init__(tts=tts, input_text=input_text, conn_options=conn_options)
        self._tts: PiperTTS = tts
        self._opts = self._tts._opts

    async def _run(self, output_emitter: tts.AudioEmitter) -> None:
        """Run the TTS synthesis and emit audio frames"""
        try:
            logger.info(f"🎤 PiperTTS synthesizing: {self._input_text[:50]}...")

            # Run Piper TTS in a subprocess
            loop = asyncio.get_event_loop()
            audio_data = await loop.run_in_executor(
                None,
                self._synthesize_sync
            )

            if not audio_data:
                logger.warning("🎤 PiperTTS: No audio generated")
                return

            # Initialize the audio emitter
            request_id = f"piper_{id(self)}"
            output_emitter.initialize(
                request_id=request_id,
                sample_rate=self._tts.sample_rate,
                num_channels=self._tts.num_channels,
                mime_type="audio/wav",
            )

            # Push audio data in chunks for streaming
            chunk_size = 4096  # 4KB chunks
            for i in range(0, len(audio_data), chunk_size):
                chunk = audio_data[i:i + chunk_size]
                output_emitter.push(chunk)

                # Yield control to event loop
                if i % (chunk_size * 4) == 0:
                    await asyncio.sleep(0)

            logger.info(f"🎤 PiperTTS: Generated {len(audio_data)} bytes of audio")

            # Flush to signal completion
            output_emitter.flush()
            logger.info(f"🎤 PiperTTS: Audio streaming completed")

        except Exception as e:
            logger.error(f"🎤 PiperTTS synthesis error: {e}", exc_info=True)
            raise

    def _synthesize_sync(self) -> bytes:
        """Synchronous synthesis (run in thread pool)"""
        try:
            # Create temporary file for output
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_output:
                output_path = temp_output.name

            try:
                # Determine model path
                if self._opts.model_path:
                    model_path = self._opts.model_path
                else:
                    # Try to construct path from voice name
                    # Check common locations: current dir, data dir, or use voice name as-is
                    voice_name = self._opts.voice
                    if not voice_name.endswith('.onnx'):
                        # Try adding .onnx extension
                        possible_paths = [
                            f"{voice_name}.onnx",
                            f"./models/{voice_name}.onnx",
                            f"./piper_models/{voice_name}.onnx",
                            voice_name  # Try as-is in case it's already a path
                        ]
                        model_path = None
                        for path in possible_paths:
                            if os.path.exists(path):
                                model_path = path
                                break

                        if not model_path:
                            raise FileNotFoundError(
                                f"Piper model not found. Please download the voice model and set PIPER_MODEL_PATH in .env.\n"
                                f"Download from: https://github.com/rhasspy/piper/releases\n"
                                f"Looking for: {voice_name}.onnx in current directory or ./models/ or ./piper_models/"
                            )
                    else:
                        model_path = voice_name

                # Build piper command
                cmd = [
                    self._tts._piper_binary,
                    "--model", model_path,
                    "--output_file", output_path,
                ]

                # Add optional parameters
                if self._opts.speaker is not None:
                    cmd.extend(["--speaker", str(self._opts.speaker)])

                logger.info(f"🎤 Running Piper TTS: {' '.join(cmd)}")

                # Run piper with text as stdin
                process = subprocess.run(
                    cmd,
                    input=self._input_text.encode('utf-8'),
                    capture_output=True,
                    timeout=30,
                    check=True
                )

                if process.returncode != 0:
                    logger.error(f"Piper TTS error: {process.stderr.decode()}")
                    return b""

                # Read the generated audio file
                with open(output_path, 'rb') as f:
                    audio_data = f.read()

                return audio_data

            finally:
                # Clean up temporary file
                if os.path.exists(output_path):
                    os.unlink(output_path)

        except subprocess.TimeoutExpired:
            logger.error("Piper TTS synthesis timeout")
            return b""
        except FileNotFoundError as e:
            logger.error(f"Piper TTS model file error: {e}")
            return b""
        except Exception as e:
            logger.error(f"Piper TTS synthesis error: {e}", exc_info=True)
            return b""


# Convenience function for quick testing
async def test_piper_tts():
    """Test Piper TTS functionality"""
    try:
        # Test if piper is available
        result = subprocess.run(
            ["piper", "--version"],
            capture_output=True,
            timeout=5
        )
        print(f"Piper version: {result.stdout.decode().strip()}")

        print("✅ Piper TTS is available!")
        print("\nTo use Piper TTS:")
        print("1. Install: pip install piper-tts")
        print("2. Or download from: https://github.com/rhasspy/piper/releases")
        print("3. Download voice models from: https://github.com/rhasspy/piper/releases")

    except FileNotFoundError:
        print("❌ Piper TTS not found. Install with:")
        print("   pip install piper-tts")
        print("   OR download from: https://github.com/rhasspy/piper/releases")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(test_piper_tts())
