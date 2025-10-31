import os
import time
import asyncio
import boto3
import logging
from amazon_transcribe.client import TranscribeStreamingClient
from amazon_transcribe.handlers import TranscriptResultStreamHandler
from amazon_transcribe.model import TranscriptEvent
from botocore.exceptions import ClientError, NoCredentialsError
from typing import Optional, List
from livekit.agents import stt
from livekit import rtc
from livekit.agents import utils
import numpy as np

logger = logging.getLogger("aws_stt_provider")


class MyEventHandler(TranscriptResultStreamHandler):
    """Custom handler for Amazon Transcribe streaming events"""
    
    def __init__(self, output_stream):
        super().__init__(output_stream)
        self.transcript_parts = []
        self.final_transcript = ""
        self.detected_language = None
        self.language_confidence = None
        self.is_complete = False
        
    async def handle_transcript_event(self, transcript_event: TranscriptEvent):
        """Handle incoming transcript events"""
        try:
            results = transcript_event.transcript.results
            
            for result in results:
                # Extract language identification if available
                if hasattr(result, 'language_identification') and result.language_identification:
                    for lang_id in result.language_identification:
                        if hasattr(lang_id, 'language_code'):
                            self.detected_language = lang_id.language_code
                            if hasattr(lang_id, 'score'):
                                self.language_confidence = lang_id.score
                            logger.debug(f"Language detected: {self.detected_language} (confidence: {self.language_confidence})")
                
                if not result.is_partial:
                    # Final result
                    for alt in result.alternatives:
                        text = alt.transcript.strip()
                        if text:
                            self.transcript_parts.append(text)
                            logger.debug(f"Final transcript part: {text}")
                else:
                    # Partial result (for real-time feedback)
                    for alt in result.alternatives:
                        text = alt.transcript.strip()
                        if text:
                            logger.debug(f"Partial transcript: {text}")
            
            # Combine all final parts
            if self.transcript_parts:
                self.final_transcript = " ".join(self.transcript_parts)
                
        except Exception as e:
            logger.error(f"Error handling transcript event: {e}")


class AWSTranscribeSTT(stt.STT):
    """
    Custom AWS Transcribe STT provider for LiveKit
    COMPLETE AUDIO ONLY - Processes complete VAD sessions for best quality
    No individual frame streaming - only complete audio from VAD triggers
    """

    def __init__(
        self,
        *,
        language: str = "en-IN",
        region: str = "us-east-1",
        sample_rate: int = 16000,
        timeout: int = 30,
        save_complete_audio: bool = True,
        complete_audio_dir: str = "aws_stt_complete_audio",
    ):
        super().__init__(
            capabilities=stt.STTCapabilities(
                streaming=True,
                interim_results=True,
            )
        )
        
        # AWS Configuration - Force reload environment variables
        from dotenv import load_dotenv
        load_dotenv(".env", override=True)  # Force reload
        
        self.aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
        self.aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        self.aws_region = region
        
        # Debug: Log what we're getting from environment
        logger.info(f"AWS credentials from env: Access Key ID: {self.aws_access_key_id[:8] if self.aws_access_key_id else 'None'}...")
        logger.info(f"AWS region: {self.aws_region}")
        
        # Validate credentials are not placeholder values
        if self.aws_access_key_id and self.aws_access_key_id.startswith('your-'):
            logger.error("AWS credentials appear to be placeholder values")
            raise ValueError("AWS credentials are placeholder values, not real credentials")
        
        # Language Configuration
        self.language_code = language
        self.sample_rate = sample_rate
        self.media_encoding = "pcm"  # Fixed for streaming
        self.timeout = timeout
        
        # Complete audio session handling
        self.save_complete_audio = save_complete_audio
        self.complete_audio_dir = complete_audio_dir
        self._complete_audio_counter = 0
        
        # Create directory for complete audio files
        if self.save_complete_audio:
            self._ensure_complete_audio_dir()
        
        # Indian languages supported by Amazon Transcribe
        self.supported_indian_languages = {
            "hi-IN": "Hindi",
            "bn-IN": "Bengali", 
            "te-IN": "Telugu",
            "ta-IN": "Tamil",
            "gu-IN": "Gujarati",
            "kn-IN": "Kannada",
            "ml-IN": "Malayalam",
            "mr-IN": "Marathi",
            "pa-IN": "Punjabi",
            "en-IN": "English (India)"
        }
        
        # Test AWS credentials
        self._init_aws_session()
        
        logger.info(
            f"AWS Transcribe STT initialized - Region: {self.aws_region}, "
            f"Language: {self.language_code}, Sample Rate: {self.sample_rate}, "
            f"Complete Audio: {self.save_complete_audio}"
        )

    def _ensure_complete_audio_dir(self):
        """Ensure the complete audio save directory exists."""
        try:
            if not os.path.exists(self.complete_audio_dir):
                os.makedirs(self.complete_audio_dir)
                logger.info(f"Created complete audio directory: {self.complete_audio_dir}")
        except Exception as e:
            logger.error(f"Failed to create complete audio directory: {e}")

    async def transcribe_complete_audio(self, audio_frames: list, session_id: str = None) -> Optional[str]:
        """Transcribe complete audio session using AWS Transcribe.
        
        This method takes the complete audio collected by VAD and sends it
        to AWS Transcribe for high-quality transcription.
        
        Args:
            audio_frames: List of rtc.AudioFrame objects from VAD
            session_id: Optional session identifier for logging
            
        Returns:
            Transcribed text or None if transcription failed
        """
        if not audio_frames:
            logger.warning("No audio frames provided for complete transcription")
            return None
            
        try:
            # Convert frames to continuous audio data
            audio_data = b""
            for frame in audio_frames:
                if hasattr(frame, 'data'):
                    if isinstance(frame.data, memoryview):
                        audio_data += frame.data.tobytes()
                    elif hasattr(frame.data, 'tobytes'):
                        audio_data += frame.data.tobytes()
                    else:
                        audio_data += bytes(frame.data)
            
            if not audio_data:
                logger.warning("No audio data extracted from frames")
                return None
            
            duration = len(audio_data) / (self.sample_rate * 2)  # 16-bit = 2 bytes per sample
            logger.info(f"🎯 [COMPLETE-STT] Processing complete audio session: {len(audio_frames)} frames, "
                       f"{len(audio_data)} bytes, {duration:.2f}s")
            
            # Save complete audio file if enabled
            if self.save_complete_audio:
                await self._save_complete_audio_file(audio_data, session_id)
            
            # Create a dedicated transcription session for complete audio
            transcription = await self._transcribe_complete_session(audio_data, session_id)
            
            if transcription:
                logger.info(f"✅ [COMPLETE-STT] Transcription successful: '{transcription}' (session: {session_id})")
            else:
                logger.warning(f"⚠️ [COMPLETE-STT] No transcription result (session: {session_id})")
                
            return transcription
            
        except Exception as e:
            logger.error(f"❌ [COMPLETE-STT] Failed to transcribe complete audio: {e}", exc_info=True)
            return None

    async def _save_complete_audio_file(self, audio_data: bytes, session_id: str = None):
        """Save complete audio data as WAV file."""
        try:
            import wave
            from datetime import datetime
            
            self._complete_audio_counter += 1
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            session_suffix = f"_{session_id}" if session_id else ""
            filename = f"complete_audio_{timestamp}_{self._complete_audio_counter:03d}{session_suffix}.wav"
            filepath = os.path.join(self.complete_audio_dir, filename)
            
            with wave.open(filepath, 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(self.sample_rate)
                wav_file.writeframes(audio_data)
            
            duration = len(audio_data) / (self.sample_rate * 2)
            logger.info(f"💾 [COMPLETE-STT] Saved complete audio: {filepath} "
                       f"(duration: {duration:.2f}s, size: {len(audio_data)} bytes)")
                       
        except Exception as e:
            logger.error(f"❌ [COMPLETE-STT] Failed to save audio file: {e}")

    async def _transcribe_complete_session(self, audio_data: bytes, session_id: str = None) -> Optional[str]:
        """Transcribe complete audio session using AWS Transcribe streaming."""
        try:
            # Create a new streaming client for this complete session
            stream_client = TranscribeStreamingClient(region=self.aws_region)
            
            # SIMPLIFIED: Use 16kHz consistently throughout the pipeline
            # ESP32 sends 16kHz audio, AWS STT processes it at 16kHz
            effective_sample_rate = 16000  # Native ESP32 sample rate
            
            # Configure streaming parameters with correct sample rate
            stream_params = {
                'media_sample_rate_hz': effective_sample_rate,
                'media_encoding': self.media_encoding,
                'language_code': self.language_code
            }
            
            logger.debug(f"🎯 [COMPLETE-STT] Starting dedicated transcription stream (session: {session_id})")
            
            # Start streaming transcription
            stream = await stream_client.start_stream_transcription(**stream_params)
            
            # Create handler to collect results
            handler = CompleteAudioHandler(stream.output_stream)
            
            # Start processing events in background
            handler_task = asyncio.create_task(handler.process_events())
            
            # Send all audio data at once (in chunks to avoid overwhelming)
            chunk_size = 8192  # 8KB chunks
            for i in range(0, len(audio_data), chunk_size):
                chunk = audio_data[i:i + chunk_size]
                await stream.input_stream.send_audio_event(audio_chunk=chunk)
                # Small delay to prevent overwhelming the stream
                await asyncio.sleep(0.01)
            
            # End the stream
            await stream.input_stream.end_stream()
            
            # Wait for processing to complete (with timeout)
            try:
                await asyncio.wait_for(handler_task, timeout=self.timeout)
            except asyncio.TimeoutError:
                logger.warning(f"⚠️ [COMPLETE-STT] Transcription timeout after {self.timeout}s")
                handler_task.cancel()
            
            # Get the final transcription
            final_transcript = handler.get_final_transcript()
            
            if final_transcript:
                logger.info(f"✅ [COMPLETE-STT] Final transcript: '{final_transcript}' (session: {session_id})")
            
            return final_transcript
            
        except Exception as e:
            logger.error(f"❌ [COMPLETE-STT] Transcription session failed: {e}", exc_info=True)
            return None

    def _init_aws_session(self):
        """Initialize AWS session and verify credentials"""
        try:
            # Create AWS session
            self.session = boto3.Session(
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.aws_region
            )
            
            # Test credentials
            sts_client = self.session.client('sts')
            identity = sts_client.get_caller_identity()
            logger.info(f"AWS credentials verified - Account: {identity.get('Account', 'Unknown')}")
            
        except NoCredentialsError:
            logger.error("AWS credentials not found")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize AWS session: {e}")
            raise

    def stream(self, *, language: str = None, conn_options=None, **kwargs) -> "CompleteAudioSpeechStream":
        """
        Create a complete audio speech recognition session
        This only processes complete VAD sessions, not individual frames
        """
        return CompleteAudioSpeechStream(
            stt=self,
            language=language or self.language_code,
            conn_options=conn_options,
            **kwargs
        )

    async def _recognize_impl(self, buffer: utils.AudioBuffer, *, language: str = None, conn_options=None, **kwargs) -> stt.SpeechEvent:
        """
        Single frame recognition - not used in complete audio mode
        This method is required by the abstract base class
        """
        raise NotImplementedError("This STT provider only processes complete VAD audio sessions, not individual frames.")



    def get_supported_languages(self) -> List[str]:
        """Get list of supported language codes"""
        return [
            'en-US', 'en-GB', 'en-AU', 'en-IN', 'en-IE', 'en-NZ', 'en-ZA', 'en-WL',
            'es-US', 'es-ES', 'fr-FR', 'fr-CA', 'de-DE', 'pt-BR', 'pt-PT',
            'it-IT', 'ja-JP', 'ko-KR', 'zh-CN', 'zh-TW',
            'ar-AE', 'ar-SA', 'hi-IN', 'th-TH', 'tr-TR', 'ru-RU',
            'nl-NL', 'da-DK', 'no-NO', 'sv-SE', 'fi-FI', 'pl-PL',
            'cs-CZ', 'hu-HU', 'ro-RO', 'bg-BG', 'hr-HR', 'sk-SK',
            'sl-SI', 'et-EE', 'lv-LV', 'lt-LT', 'mt-MT', 'el-GR',
            'he-IL', 'fa-IR', 'ur-PK', 'bn-IN', 'ta-IN', 'te-IN',
            'ml-IN', 'kn-IN', 'gu-IN', 'mr-IN', 'pa-IN'
        ]


class CompleteAudioSpeechStream(stt.SpeechStream):
    """
    Complete Audio Speech Recognition Stream for AWS Transcribe
    Only processes complete VAD audio sessions - no individual frame streaming
    """
    
    def __init__(self, *, stt: AWSTranscribeSTT, language: str, conn_options=None, **kwargs):
        super().__init__(stt=stt, conn_options=conn_options)
        self._stt = stt
        self._language = language
        self._closed = False
        logger.info(f"🎯 [COMPLETE-STT] Stream initialized - language: {language}")
        
    async def _run(self):
        """Main task - just wait for complete audio sessions"""
        logger.info(f"🎯 [COMPLETE-STT] Stream ready for complete audio sessions")
        try:
            # Just wait - actual processing happens via transcribe_complete_audio
            while not self._closed:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass
        finally:
            logger.info(f"🎯 [COMPLETE-STT] Stream closed")
    
    async def aclose(self):
        """Close the speech stream"""
        self._closed = True
        await super().aclose()
    
    def push_frame(self, frame: rtc.AudioFrame):
        """
        Individual frames are ignored - we only process complete VAD sessions
        This method exists for compatibility but does nothing
        """
        # Do nothing - we only process complete audio from VAD
        pass


class CompleteAudioHandler(TranscriptResultStreamHandler):
    """Handler for complete audio transcription sessions."""
    
    def __init__(self, output_stream):
        super().__init__(output_stream)
        self._output_stream = output_stream  # Store the output stream
        self._transcript_parts = []
        self._final_transcript = ""
        self._processing_complete = False
        
    async def handle_transcript_event(self, transcript_event: TranscriptEvent):
        """Handle transcript events for complete audio."""
        try:
            results = transcript_event.transcript.results
            
            for result in results:
                if result.alternatives:
                    text = result.alternatives[0].transcript.strip()
                    
                    if text and not result.is_partial:
                        # Only collect final results for complete audio
                        self._transcript_parts.append(text)
                        logger.debug(f"[COMPLETE-STT] Final part: '{text}'")
            
            # Update final transcript
            if self._transcript_parts:
                self._final_transcript = " ".join(self._transcript_parts)
                
        except Exception as e:
            logger.error(f"Error handling complete audio transcript event: {e}")
    
    async def process_events(self):
        """Process all events from the stream."""
        try:
            async for event in self._output_stream:
                await self.handle_transcript_event(event)
        except Exception as e:
            logger.error(f"Error processing complete audio events: {e}")
        finally:
            self._processing_complete = True
    
    def get_final_transcript(self) -> str:
        """Get the final complete transcript."""
        return self._final_transcript