"""
Remote Whisper STT Provider
Connects to remote Whisper server via HTTP API
"""
import asyncio
import logging
import httpx
import tempfile
import os
from typing import Optional, Union
from livekit.agents import stt, utils

logger = logging.getLogger(__name__)


class RemoteWhisperSTT(stt.STT):
    """Remote Whisper STT implementation via HTTP API"""

    def __init__(
        self,
        *,
        base_url: str = "http://localhost:8000",
        timeout: float = 30.0,
        language: str = "en",
    ):
        """
        Initialize Remote Whisper STT provider

        Args:
            base_url: URL of remote Whisper server
            timeout: Request timeout in seconds
            language: Language code (e.g., 'en', 'es', 'fr')
        """
        super().__init__(
            capabilities=stt.STTCapabilities(streaming=False, interim_results=False)
        )

        self._base_url = base_url.rstrip('/')
        self._timeout = timeout
        self._language = language

        logger.info(
            f"Initialized RemoteWhisperSTT with base_url={base_url}, "
            f"timeout={timeout}s, language={language}"
        )

    async def _recognize_impl(
        self,
        buffer: Union[utils.AudioBuffer, "rtc.AudioFrame"],
        *,
        language: Optional[str] = None,
        conn_options: Optional[any] = None,
    ) -> stt.SpeechEvent:
        """
        Implementation of speech recognition

        Args:
            buffer: Audio data to transcribe
            language: Override language (optional)
            conn_options: Connection options (ignored)

        Returns:
            SpeechEvent with transcription
        """
        # Convert audio to WAV file
        audio_data = self._prepare_audio(buffer)
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            temp_path = f.name
            # Write WAV header + data
            import wave
            with wave.open(temp_path, 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(16000)  # 16kHz
                wav_file.writeframes(audio_data.tobytes())
        
        try:
            # Send to remote server
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                with open(temp_path, 'rb') as audio_file:
                    files = {'audio': ('audio.wav', audio_file, 'audio/wav')}
                    
                    response = await client.post(
                        f"{self._base_url}/transcribe",
                        files=files
                    )
                    
                    response.raise_for_status()
                    result = response.json()
            
            # Extract text
            text = result.get('text', '').strip()
            
            logger.info(f"Remote Whisper transcription: {text}")
            
            # Create speech event
            return stt.SpeechEvent(
                type=stt.SpeechEventType.FINAL_TRANSCRIPT,
                alternatives=[
                    stt.SpeechData(
                        text=text,
                        language=language or self._language,
                    )
                ],
            )
        
        except Exception as e:
            logger.error(f"Remote Whisper error: {e}")
            
            # Return a fallback message instead of crashing the session
            logger.warning("Returning fallback transcription due to Whisper timeout/error")
            return stt.SpeechEvent(
                type=stt.SpeechEventType.FINAL_TRANSCRIPT,
                alternatives=[
                    stt.SpeechData(
                        text="Sorry, I didn't catch that. Could you please repeat?",
                        language=language or self._language,
                    )
                ],
            )
        
        finally:
            # Cleanup temp file
            try:
                os.unlink(temp_path)
            except:
                pass

    def _prepare_audio(self, buffer: Union[utils.AudioBuffer, "rtc.AudioFrame"]):
        """Convert audio buffer to numpy array"""
        import numpy as np
        
        # Check if buffer has 'data' attribute (works for both AudioBuffer and AudioFrame)
        if hasattr(buffer, 'data'):
            # Convert buffer data to numpy array
            if isinstance(buffer.data, (bytes, bytearray)):
                data = np.frombuffer(buffer.data, dtype=np.int16)
            else:
                data = np.array(buffer.data, dtype=np.int16)
        else:
            # Fallback: treat as raw data
            data = np.array(buffer, dtype=np.int16)
        
        return data
