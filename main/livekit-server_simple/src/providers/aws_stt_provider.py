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
    Based on xiaozhi-server implementation but adapted for LiveKit agents
    """

    def __init__(
        self,
        *,
        language: str = "en-IN",
        region: str = "us-east-1",
        sample_rate: int = 16000,
        timeout: int = 30,
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
            f"Language: {self.language_code}, Sample Rate: {self.sample_rate}"
        )

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

    def stream(self, *, language: str = None, conn_options=None, **kwargs) -> "SpeechStream":
        """
        Create a streaming speech recognition session
        This is the correct method for streaming STT providers
        """
        return SpeechStream(
            stt=self,
            language=language or self.language_code,
            conn_options=conn_options,
            **kwargs
        )

    async def _recognize_impl(self, buffer: utils.AudioBuffer, *, language: str = None, conn_options=None, **kwargs) -> stt.SpeechEvent:
        """
        Single frame recognition - not supported by AWS Transcribe
        This method is required by the abstract base class but AWS Transcribe only supports streaming
        """
        raise NotImplementedError("Amazon Transcribe does not support single frame recognition. Use streaming mode instead.")



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


class SpeechStream(stt.SpeechStream):
    """
    Streaming speech recognition session for AWS Transcribe
    """
    
    def __init__(self, *, stt: AWSTranscribeSTT, language: str, conn_options=None, **kwargs):
        super().__init__(stt=stt, conn_options=conn_options)
        self._stt = stt
        self._language = language
        self._closed = False
        self._cleanup_done = False
        self._audio_buffer = []
        self._transcribe_task = None
        self._stream_client = None
        self._stream = None
        self._handler = None
        
    async def _run(self):
        """Main streaming task - required by abstract base class"""
        return await self._main_task()
        
    async def _main_task(self):
        """Main streaming task"""
        try:
            # Initialize AWS Transcribe streaming client
            self._stream_client = TranscribeStreamingClient(region=self._stt.aws_region)
            
            # Configure streaming parameters
            stream_params = {
                'media_sample_rate_hz': self._stt.sample_rate,
                'media_encoding': self._stt.media_encoding,
                'language_code': self._language
            }
            
            logger.debug(f"Starting AWS Transcribe stream with language: {self._language}")
            
            # Start streaming transcription
            self._stream = await self._stream_client.start_stream_transcription(**stream_params)
            
            # Create handler for the stream
            self._handler = StreamEventHandler(self._stream.output_stream, self._event_ch)
            
            # Start processing events
            await self._handler.process_events()
            
        except Exception as e:
            logger.error(f"AWS Transcribe streaming error: {e}")
            if not self._closed:
                event = stt.SpeechEvent(
                    type=stt.SpeechEventType.FINAL_TRANSCRIPT,
                    alternatives=[],
                )
                # Send error event
                try:
                    handler = StreamEventHandler(None, self._event_ch)
                    await handler._send_event(event)
                except Exception as send_error:
                    logger.error(f"Failed to send error event: {send_error}")
        finally:
            await self._cleanup()
    
    async def _cleanup(self):
        """Clean up streaming resources"""
        if self._cleanup_done:
            return
            
        try:
            self._closed = True
            self._cleanup_done = True
            
            if self._stream and hasattr(self._stream, 'input_stream'):
                try:
                    await self._stream.input_stream.end_stream()
                except Exception as stream_error:
                    # Stream might already be closed, which is fine
                    logger.debug(f"Stream already closed during cleanup: {stream_error}")
                    
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    async def aclose(self):
        """Close the speech stream"""
        if not self._closed:
            await self._cleanup()
        await super().aclose()
    
    def push_frame(self, frame: rtc.AudioFrame):
        """Push audio frame to the stream"""
        if self._closed or self._cleanup_done:
            return
            
        try:
            # Convert frame data to bytes - handle different data types
            if isinstance(frame.data, memoryview):
                # Convert memoryview to bytes directly
                audio_data = frame.data.tobytes()
            elif hasattr(frame.data, 'astype'):
                # Handle numpy arrays
                audio_data = frame.data.astype(np.int16).tobytes()
            elif hasattr(frame.data, 'tobytes'):
                # Handle other array-like objects with tobytes method
                audio_data = frame.data.tobytes()
            else:
                # Convert to numpy array first, then to bytes
                audio_data = np.frombuffer(frame.data, dtype=np.int16).tobytes()
            
            # Send to AWS Transcribe stream (only if stream is ready and not closed)
            if (self._stream and 
                hasattr(self._stream, 'input_stream') and 
                not self._closed and 
                not self._cleanup_done):
                
                # Create task to send audio data
                async def send_audio():
                    try:
                        await self._stream.input_stream.send_audio_event(audio_chunk=audio_data)
                    except Exception as send_error:
                        # Stream might be closed, which is fine during cleanup
                        if not self._closed:
                            logger.debug(f"Failed to send audio chunk: {send_error}")
                
                asyncio.create_task(send_audio())
                
        except Exception as e:
            logger.error(f"Error pushing frame: {e}")


class StreamEventHandler(TranscriptResultStreamHandler):
    """Handler for AWS Transcribe streaming events that sends to LiveKit event channel"""
    
    def __init__(self, output_stream, event_channel):
        super().__init__(output_stream)
        self._event_ch = event_channel
        self._partial_transcript = ""
        self._output_stream = output_stream
        
        # Debug: Log the event channel type and available methods
        logger.debug(f"Event channel type: {type(event_channel)}")
        logger.debug(f"Event channel methods: {[m for m in dir(event_channel) if not m.startswith('_')]}")
    
    async def _send_event(self, event):
        """Send event through the channel using the correct method"""
        try:
            # For Chan objects, use send_nowait or send
            if hasattr(self._event_ch, 'send_nowait'):
                self._event_ch.send_nowait(event)
            elif hasattr(self._event_ch, 'asend'):
                await self._event_ch.asend(event)
            elif hasattr(self._event_ch, 'send'):
                await self._event_ch.send(event)
            elif hasattr(self._event_ch, 'put'):
                await self._event_ch.put(event)
            else:
                logger.error(f"Unknown event channel type: {type(self._event_ch)}, methods: {dir(self._event_ch)}")
        except Exception as e:
            logger.error(f"Failed to send event: {e}")
        
    async def handle_transcript_event(self, transcript_event: TranscriptEvent):
        """Handle incoming transcript events and send to LiveKit"""
        try:
            results = transcript_event.transcript.results
            
            for result in results:
                if result.alternatives:
                    text = result.alternatives[0].transcript.strip()
                    
                    if text:
                        if result.is_partial:
                            # Send interim result
                            self._partial_transcript = text
                            event = stt.SpeechEvent(
                                type=stt.SpeechEventType.INTERIM_TRANSCRIPT,
                                alternatives=[
                                    stt.SpeechData(
                                        text=text,
                                        language=None,  # Will be filled by framework
                                    )
                                ],
                            )
                            await self._send_event(event)
                        else:
                            # Send final result
                            event = stt.SpeechEvent(
                                type=stt.SpeechEventType.FINAL_TRANSCRIPT,
                                alternatives=[
                                    stt.SpeechData(
                                        text=text,
                                        language=None,  # Will be filled by framework
                                    )
                                ],
                            )
                            await self._send_event(event)
                            
        except Exception as e:
            logger.error(f"Error handling transcript event: {e}")
    
    async def process_events(self):
        """Process events from the stream"""
        try:
            async for event in self._output_stream:
                await self.handle_transcript_event(event)
        except Exception as e:
            logger.error(f"Error processing events: {e}")