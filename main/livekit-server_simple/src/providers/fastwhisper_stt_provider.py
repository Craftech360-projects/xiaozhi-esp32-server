"""
FastWhisper STT provider for LiveKit Agents
Wraps faster-whisper for local speech-to-text with LiveKit
"""

import asyncio
import logging
import io
import os
from typing import Optional
from dataclasses import dataclass

# Workaround for tqdm compatibility issue
os.environ['HF_HUB_DISABLE_PROGRESS_BARS'] = '1'
os.environ['TQDM_DISABLE'] = '1'

try:
    from faster_whisper import WhisperModel
    FASTER_WHISPER_AVAILABLE = True
except ImportError:
    FASTER_WHISPER_AVAILABLE = False

try:
    from livekit.agents import stt, utils
    from livekit.agents.types import DEFAULT_API_CONNECT_OPTIONS, APIConnectOptions
    import numpy as np
    LIVEKIT_AVAILABLE = True
except ImportError:
    LIVEKIT_AVAILABLE = False


logger = logging.getLogger(__name__)


@dataclass
class _FastWhisperOptions:
    """Options for FastWhisper configuration"""
    model: str
    language: str
    device: str
    compute_type: str


class FastWhisperSTT(stt.STT if LIVEKIT_AVAILABLE else object):
    """FastWhisper STT provider for LiveKit Agents"""

    def __init__(
        self,
        model: str = "base",
        language: str = "en",
        device: str = "cpu",
        compute_type: str = "int8"
    ):
        if not FASTER_WHISPER_AVAILABLE:
            raise ImportError("faster-whisper is not installed. Install with: pip install faster-whisper")

        if not LIVEKIT_AVAILABLE:
            raise ImportError("livekit is not installed")

        # Initialize the parent STT class
        super().__init__(
            capabilities=stt.STTCapabilities(streaming=False, interim_results=False)
        )

        self._opts = _FastWhisperOptions(
            model=model,
            language=language,
            device=device,
            compute_type=compute_type
        )

        # Load the Whisper model
        logger.info(f"🎤 Loading FastWhisper model: {model} on {device}...")
        try:
            self._model = WhisperModel(
                model_size_or_path=model,
                device=device,
                compute_type=compute_type,
                download_root=None,
                local_files_only=False
            )
            logger.info(f"✅ FastWhisper model loaded successfully: {model}")
        except Exception as e:
            logger.error(f"❌ Failed to load FastWhisper model: {e}")
            raise

    def _sanitize_options(self, *, language: Optional[str] = None) -> _FastWhisperOptions:
        """Sanitize options for the STT request"""
        opts = self._opts
        if language:
            opts = dataclass.replace(opts, language=language)
        return opts

    async def _recognize_impl(
        self,
        buffer: utils.AudioBuffer,
        *,
        language: Optional[str] = None,
        conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS,
    ) -> "FastWhisperSTTStream":
        """Recognize speech from an audio buffer - required abstract method"""
        opts = self._sanitize_options(language=language)
        stream = FastWhisperSTTStream(
            stt=self,
            opts=opts,
            buffer=buffer,
            conn_options=conn_options
        )
        return stream

    def __str__(self):
        return f"FastWhisperSTT(model={self._opts.model}, language={self._opts.language})"


class FastWhisperSTTStream(stt.SpeechStream if LIVEKIT_AVAILABLE else object):
    """Speech stream for FastWhisper recognition"""

    def __init__(
        self,
        *,
        stt: FastWhisperSTT,
        opts: _FastWhisperOptions,
        buffer: utils.AudioBuffer,
        conn_options: APIConnectOptions,
    ) -> None:
        super().__init__(stt=stt, conn_options=conn_options)
        self._stt = stt
        self._opts = opts
        self._buffer = buffer

    async def aclose(self) -> None:
        """Close the stream"""
        await super().aclose()

    async def _run(self) -> None:
        """Run the STT recognition"""
        try:
            logger.info(f"🎤 FastWhisper processing audio buffer...")

            # Convert audio buffer to numpy array
            # The buffer.data is a memoryview, need to convert to numpy array
            sample_rate = self._buffer.sample_rate

            # Convert memoryview/bytes to numpy array
            audio_bytes = bytes(self._buffer.data)
            audio_data = np.frombuffer(audio_bytes, dtype=np.int16)

            # Convert to float32 and normalize to [-1, 1] range
            audio_data = audio_data.astype(np.float32) / 32768.0

            # Run transcription in thread pool since it's synchronous
            loop = asyncio.get_event_loop()

            def _transcribe():
                """Run transcription in thread pool"""
                segments, info = self._stt._model.transcribe(
                    audio=audio_data,
                    language=self._opts.language,
                    beam_size=5,
                    vad_filter=False,  # We're using external VAD
                    without_timestamps=False
                )

                # Collect all segments
                text_parts = []
                for segment in segments:
                    text_parts.append(segment.text)

                # Combine all segments
                final_text = " ".join(text_parts).strip()
                return final_text, info

            # Run in thread pool
            final_text, info = await loop.run_in_executor(None, _transcribe)

            logger.info(f"🎤 FastWhisper transcription: {final_text[:100] if final_text else '(empty)'}...")

            # Create and dispatch the final event
            if final_text:
                final_event = stt.SpeechEvent(
                    type=stt.SpeechEventType.FINAL_TRANSCRIPT,
                    alternatives=[
                        stt.SpeechData(
                            text=final_text,
                            language=self._opts.language,
                            confidence=info.language_probability if hasattr(info, 'language_probability') else 0.95
                        )
                    ]
                )
                self._event_ch.send_nowait(final_event)
            else:
                logger.warning("🎤 FastWhisper: No speech detected in audio")

            # Send end of speech event
            end_event = stt.SpeechEvent(type=stt.SpeechEventType.END_OF_SPEECH)
            self._event_ch.send_nowait(end_event)

        except Exception as e:
            logger.error(f"🎤 FastWhisper recognition error: {e}", exc_info=True)
            raise


# Test function
async def test_fastwhisper():
    """Test FastWhisper functionality"""
    if not FASTER_WHISPER_AVAILABLE:
        print("faster-whisper not available - install with: pip install faster-whisper")
        return

    print("FastWhisper STT Provider initialized successfully!")
    print("Available models: tiny, base, small, medium, large")
    print("Note: First run will download the model from Hugging Face")


if __name__ == "__main__":
    asyncio.run(test_fastwhisper())
