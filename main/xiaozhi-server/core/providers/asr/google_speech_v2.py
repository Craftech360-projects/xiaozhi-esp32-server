import os
import time
import json
import asyncio
from google.cloud import speech_v2
from google.api_core import exceptions
from google.api_core.client_options import ClientOptions
from config.logger import setup_logging
from typing import Optional, Tuple, List, AsyncIterator
from core.providers.asr.base import ASRProviderBase
from core.providers.asr.dto.dto import InterfaceType

TAG = __name__
logger = setup_logging()


class ASRProvider(ASRProviderBase):
    """
    Google Cloud Speech-to-Text v2 Provider with Chirp 2 model support
    Chirp 2 is Google's next-generation universal speech model with improved accuracy
    """

    def __init__(self, config: dict, delete_audio_file: bool):
        super().__init__(config)
        self.interface_type = InterfaceType.NON_STREAM
        
        # Google Cloud configuration
        self.project_id = config.get("project_id")
        self.location = config.get("location", "global")  # Chirp 2 is available globally
        self.credentials_path = config.get("credentials_path")
        
        # Model configuration - Chirp 2 specific
        self.model = config.get("model", "chirp_2")  # Use Chirp 2 by default
        language_codes_from_config = config.get("language_codes", ["en-US"])
        
        # Ensure language_codes is never empty (Google API requirement)
        if not language_codes_from_config or not isinstance(language_codes_from_config, list):
            self.language_codes = ["en-US"]
            logger.bind(tag=TAG).warning(f"Invalid or empty language_codes in config, using default: ['en-US']")
        else:
            self.language_codes = language_codes_from_config
        
        # Debug logging for language codes
        logger.bind(tag=TAG).info(f"Configured language_codes: {self.language_codes} (type: {type(self.language_codes)})")
        
        # Audio configuration
        self.sample_rate_hertz = config.get("sample_rate_hertz", 16000)
        self.encoding = config.get("encoding", "LINEAR16")
        
        # Recognition configuration
        self.enable_automatic_punctuation = config.get("enable_automatic_punctuation", True)
        self.enable_word_time_offsets = config.get("enable_word_time_offsets", False)
        self.enable_word_confidence = config.get("enable_word_confidence", False)
        self.enable_spoken_punctuation = config.get("enable_spoken_punctuation", False)
        self.enable_spoken_emojis = config.get("enable_spoken_emojis", False)
        
        # File management
        self.output_dir = config.get("output_dir", "./audio_files")
        self.delete_audio_file = delete_audio_file
        
        # Set credentials if provided
        if self.credentials_path:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self.credentials_path
        
        # Initialize the Speech client with v2 API
        try:
            # For Chirp 2, use regional endpoint and recognizer
            if self.model == "chirp_2":
                # Use regional API endpoint for Chirp 2
                api_endpoint = f"{self.location}-speech.googleapis.com"
                client_options = ClientOptions(api_endpoint=api_endpoint)
                self.client = speech_v2.SpeechClient(client_options=client_options)
                
                # Use regional recognizer path to match regional endpoint
                # Note: When using regional endpoint, recognizer path must also use same region
                self.recognizer_name = f"projects/{self.project_id}/locations/{self.location}/recognizers/_"
                logger.bind(tag=TAG).info(f"Using regional API endpoint: {api_endpoint}")
            else:
                # Use default global client and recognizer for standard models
                self.client = speech_v2.SpeechClient()
                self.recognizer_name = f"projects/{self.project_id}/locations/global/recognizers/_"
            
            logger.bind(tag=TAG).info(
                f"Google Speech v2 initialized with model: {self.model}, "
                f"project: {self.project_id}, recognizer: {self.recognizer_name}"
            )
        except Exception as e:
            logger.bind(tag=TAG).error(f"Failed to initialize Google Speech v2 client: {e}")
            raise
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Streaming session management
        self.streaming_sessions = {}  # conn.session_id -> streaming session data

    def _get_audio_encoding(self):
        """Map encoding string to Google Speech enum"""
        try:
            encoding_map = {
                "LINEAR16": speech_v2.ExplicitDecodingConfig.AudioEncoding.LINEAR16,
                "FLAC": speech_v2.ExplicitDecodingConfig.AudioEncoding.FLAC,
                "MULAW": speech_v2.ExplicitDecodingConfig.AudioEncoding.MULAW,
                "AMR": speech_v2.ExplicitDecodingConfig.AudioEncoding.AMR,
                "AMR_WB": speech_v2.ExplicitDecodingConfig.AudioEncoding.AMR_WB,
                "OGG_OPUS": speech_v2.ExplicitDecodingConfig.AudioEncoding.OGG_OPUS,
                "MP3": speech_v2.ExplicitDecodingConfig.AudioEncoding.MP3,
                "WEBM_OPUS": speech_v2.ExplicitDecodingConfig.AudioEncoding.WEBM_OPUS,
            }
            
            # Add SPEEX if available (not all versions support it)
            if hasattr(speech_v2.ExplicitDecodingConfig.AudioEncoding, 'SPEEX_WITH_HEADER_BYTE'):
                encoding_map["SPEEX_WITH_HEADER_BYTE"] = speech_v2.ExplicitDecodingConfig.AudioEncoding.SPEEX_WITH_HEADER_BYTE
            
            return encoding_map.get(self.encoding, speech_v2.ExplicitDecodingConfig.AudioEncoding.LINEAR16)
        except AttributeError as e:
            logger.bind(tag=TAG).warning(f"Audio encoding {self.encoding} not supported, using LINEAR16: {e}")
            return speech_v2.ExplicitDecodingConfig.AudioEncoding.LINEAR16

    async def speech_to_text(
        self, opus_data: List[bytes], session_id: str, audio_format="opus"
    ) -> Tuple[Optional[str], Optional[str]]:
        """Convert speech data to text using Google Cloud Speech v2 API with Chirp 2"""
        start_time = time.time()
        audio_file_path = None
        
        try:
            # Decode Opus to PCM if needed
            if audio_format == "opus":
                pcm_data = self.decode_opus(opus_data)
                if not pcm_data:
                    logger.bind(tag=TAG).error("Failed to decode Opus audio")
                    return "", None
            else:
                pcm_data = opus_data
            
            # Save audio to file for logging/debugging
            audio_file_path = self.save_audio_to_file(pcm_data, session_id)
            
            # Combine PCM data
            audio_content = b"".join(pcm_data)
            
            # Calculate audio length for logging
            audio_length_seconds = len(audio_content) / (self.sample_rate_hertz * 2)  # 16-bit audio
            
            # Configure recognition request - use model name as-is
            model_name = self.model
            encoding = self._get_audio_encoding()
            logger.bind(tag=TAG).debug(f"Using model: {model_name} for recognition")
            logger.bind(tag=TAG).debug(f"Audio encoding: {encoding}, sample_rate: {self.sample_rate_hertz}, audio_length: {len(audio_content)} bytes")
            
            # Configure recognition request based on model type
            if self.model == "chirp_2":
                # Use explicit decoding config for Chirp 2 with proper audio format
                config = speech_v2.RecognitionConfig(
                    explicit_decoding_config=speech_v2.ExplicitDecodingConfig(
                        encoding=encoding,
                        sample_rate_hertz=self.sample_rate_hertz,
                        audio_channel_count=1,
                    ),
                    language_codes=self.language_codes,
                    model=model_name,  # chirp_2
                    features=speech_v2.RecognitionFeatures(
                        enable_automatic_punctuation=self.enable_automatic_punctuation,
                        enable_word_time_offsets=self.enable_word_time_offsets,
                        enable_word_confidence=self.enable_word_confidence,
                        enable_spoken_punctuation=self.enable_spoken_punctuation,
                        enable_spoken_emojis=self.enable_spoken_emojis,
                        profanity_filter=False,
                    ),
                )
            else:
                # Use explicit decoding for standard models
                config = speech_v2.RecognitionConfig(
                    explicit_decoding_config=speech_v2.ExplicitDecodingConfig(
                        encoding=encoding,
                        sample_rate_hertz=self.sample_rate_hertz,
                        audio_channel_count=1,
                    ),
                    language_codes=self.language_codes,
                    model=model_name,
                    features=speech_v2.RecognitionFeatures(
                        enable_automatic_punctuation=self.enable_automatic_punctuation,
                        enable_word_time_offsets=self.enable_word_time_offsets,
                        enable_word_confidence=self.enable_word_confidence,
                        enable_spoken_punctuation=self.enable_spoken_punctuation,
                        enable_spoken_emojis=self.enable_spoken_emojis,
                        profanity_filter=False,
                    ),
                )
            
            # Create recognition request
            request = speech_v2.RecognizeRequest(
                recognizer=self.recognizer_name,
                config=config,
                content=audio_content,
            )
            
            # Perform synchronous speech recognition
            try:
                response = self.client.recognize(request=request)
                
                # Extract transcription from response
                transcript = ""
                confidence_scores = []
                
                for result in response.results:
                    # Get the best alternative (highest confidence)
                    if result.alternatives:
                        best_alternative = result.alternatives[0]
                        transcript += best_alternative.transcript + " "
                        
                        # Collect confidence scores if available
                        if hasattr(best_alternative, 'confidence'):
                            confidence_scores.append(best_alternative.confidence)
                        
                        # Log word-level details if enabled
                        if self.enable_word_time_offsets and hasattr(best_alternative, 'words'):
                            for word_info in best_alternative.words:
                                logger.bind(tag=TAG).debug(
                                    f"Word: {word_info.word}, "
                                    f"Start: {word_info.start_offset}, "
                                    f"End: {word_info.end_offset}"
                                )
                
                transcript = transcript.strip()
                
                # Calculate average confidence if available
                avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else None
                
                elapsed_time = time.time() - start_time
                logger.bind(tag=TAG).info(
                    f"Google Speech v2 (Chirp 2) transcription completed in {elapsed_time:.2f}s"
                    f"{f', confidence: {avg_confidence:.2f}' if avg_confidence else ''}: {transcript}"
                )
                
                # Log the transcript for debugging/analysis
                if transcript:
                    self.log_audio_transcript(audio_file_path, audio_length_seconds, transcript)
                
                return transcript, audio_file_path
                
            except exceptions.GoogleAPIError as e:
                logger.bind(tag=TAG).error(f"Google Speech API error: {e}")
                return "", audio_file_path
            
        except Exception as e:
            logger.bind(tag=TAG).error(
                f"Speech-to-text error: {str(e)}, type: {type(e).__name__}"
            )
            import traceback
            logger.bind(tag=TAG).debug(f"Traceback: {traceback.format_exc()}")
            return "", audio_file_path
        
        finally:
            # Clean up audio file if configured
            if self.delete_audio_file and audio_file_path and os.path.exists(audio_file_path):
                try:
                    os.remove(audio_file_path)
                    logger.bind(tag=TAG).debug(f"Deleted audio file: {audio_file_path}")
                except Exception as e:
                    logger.bind(tag=TAG).warning(
                        f"Failed to delete audio file {audio_file_path}: {e}"
                    )

    async def start_streaming_session(self, conn, session_id: str) -> bool:
        """Start a continuous streaming ASR session (like test.py approach).
        
        Args:
            conn: Connection object
            session_id: Unique session identifier
            
        Returns:
            True if session started successfully, False otherwise
        """
        try:
            logger.bind(tag=TAG).info(f"[STREAM-START] Starting continuous streaming session: {session_id}")
            
            # Check if session already exists
            if session_id in self.streaming_sessions:
                logger.bind(tag=TAG).warning(f"[STREAM-START] Session {session_id} already exists, reusing")
                return True
            
            # Validate language codes
            safe_language_codes = self.language_codes if self.language_codes else ["en-US"]
            logger.bind(tag=TAG).debug(f"[STREAM-START] Using language_codes: {safe_language_codes}")
            
            # Create session data for continuous streaming
            import queue
            audio_queue = queue.Queue()
            
            session_data = {
                'language_codes': safe_language_codes,
                'model': self.model,
                'audio_queue': audio_queue,
                'streaming_task': None,
                'final_transcript': "",
                'partial_transcript': "",
                'session_active': True,
                'audio_count': 0,
                'speech_started': False,  # Track when actual speech begins
                'responses_iterator': None
            }
            
            # Store session
            self.streaming_sessions[session_id] = session_data
            logger.bind(tag=TAG).info(f"[STREAM-START] Session {session_id} created for continuous streaming")
            
            # Start the continuous streaming task immediately
            logger.bind(tag=TAG).info(f"[STREAM-START] About to create streaming task for {session_id}")
            session_data['streaming_task'] = asyncio.create_task(
                self._continuous_streaming_task(session_id, session_data)
            )
            logger.bind(tag=TAG).info(f"[STREAM-START] Streaming task created for {session_id}")
            
            logger.bind(tag=TAG).info(f"[STREAM-START] Continuous streaming session {session_id} started successfully")
            return True
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"[STREAM-START] Failed to start streaming session {session_id}: {e}")
            import traceback
            logger.bind(tag=TAG).error(f"[STREAM-START] Traceback: {traceback.format_exc()}")
            return False

    async def _continuous_streaming_task(self, session_id: str, session_data: dict):
        """Continuous streaming task - waits for audio chunks before starting Google API stream."""
        logger.bind(tag=TAG).info(f"[CONTINUOUS-STREAM] Starting continuous streaming task for {session_id}")
        
        try:
            # Get the audio queue that was created in start_streaming_session
            audio_queue = session_data['audio_queue']
            logger.bind(tag=TAG).info(f"[CONTINUOUS-STREAM] Task initialized, waiting for audio chunks for {session_id}")
            
            # Wait for first audio chunk before starting Google API stream
            # This prevents Google API timeout when no audio is immediately available
            logger.bind(tag=TAG).info(f"[CONTINUOUS-STREAM] Waiting for first audio chunk for {session_id}")
            first_chunk = None
            
            while session_data['session_active']:
                try:
                    # Block and wait for first chunk (longer timeout)
                    first_chunk = audio_queue.get(timeout=1.0)
                    if first_chunk is None:  # End signal
                        logger.bind(tag=TAG).info(f"[CONTINUOUS-STREAM] Session ended before audio started for {session_id}")
                        return
                    
                    logger.bind(tag=TAG).info(f"[CONTINUOUS-STREAM] Got first audio chunk for {session_id} ({len(first_chunk)} bytes), starting Google API stream")
                    break
                    
                except Exception as e:
                    # Continue waiting for audio
                    continue
            
            if not session_data['session_active']:
                logger.bind(tag=TAG).info(f"[CONTINUOUS-STREAM] Session ended while waiting for audio for {session_id}")
                return
            
            # Create streaming configuration (same as test.py)
            config = speech_v2.StreamingRecognitionConfig(
                config=speech_v2.RecognitionConfig(
                    explicit_decoding_config=speech_v2.ExplicitDecodingConfig(
                        encoding=self._get_audio_encoding(),
                        sample_rate_hertz=self.sample_rate_hertz,
                        audio_channel_count=1,
                    ),
                    language_codes=session_data['language_codes'],
                    model=session_data['model'],
                    features=speech_v2.RecognitionFeatures(
                        enable_automatic_punctuation=self.enable_automatic_punctuation,
                        profanity_filter=False,
                    ),
                ),
                streaming_features=speech_v2.StreamingRecognitionFeatures(
                    interim_results=True,
                )
            )
            
            def request_generator():
                """Generator like test.py - yields config first, then audio chunks."""
                # Send config first (like test.py)
                config_request = speech_v2.StreamingRecognizeRequest(
                    recognizer=self.recognizer_name,
                    streaming_config=config
                )
                yield config_request
                logger.bind(tag=TAG).info(f"[CONTINUOUS-STREAM] Config sent for {session_id}")
                
                # Send the first chunk that triggered the stream
                chunk_count = 1
                request = speech_v2.StreamingRecognizeRequest(audio=first_chunk)
                yield request
                logger.bind(tag=TAG).info(f"[CONTINUOUS-STREAM] Generator sent first chunk ({len(first_chunk)} bytes)")
                
                # Stream remaining audio chunks continuously
                while session_data['session_active']:
                    try:
                        # Get audio chunk from queue (blocking with short timeout)
                        audio_chunk = audio_queue.get(timeout=0.1)
                        
                        if audio_chunk is None:  # End signal
                            logger.bind(tag=TAG).info(f"[CONTINUOUS-STREAM] End signal received for {session_id}")
                            break
                            
                        chunk_count += 1
                        if chunk_count <= 5:  # Log first 5 chunks to confirm generator is working
                            logger.bind(tag=TAG).info(f"[CONTINUOUS-STREAM] Generator got chunk #{chunk_count} from queue ({len(audio_chunk)} bytes)")
                        elif chunk_count % 100 == 0:  # Then log every 100th
                            logger.bind(tag=TAG).info(f"[CONTINUOUS-STREAM] Generator processing chunk #{chunk_count}")
                        
                        # Create and yield the request
                        request = speech_v2.StreamingRecognizeRequest(audio=audio_chunk)
                        yield request
                        
                        if chunk_count <= 5:
                            logger.bind(tag=TAG).info(f"[CONTINUOUS-STREAM] Generator yielded chunk #{chunk_count} to Google API")
                        
                    except Exception as e:  # Log exceptions to debug queue issues
                        if chunk_count < 10:  # Only log first few timeouts to avoid spam
                            logger.bind(tag=TAG).debug(f"[CONTINUOUS-STREAM] Generator queue timeout: {e}")
                        continue
                
                logger.bind(tag=TAG).info(f"[CONTINUOUS-STREAM] Generator finished for {session_id} ({chunk_count} chunks)")
            
            # Now start Google API streaming with audio ready
            logger.bind(tag=TAG).info(f"[CONTINUOUS-STREAM] Starting Google API streaming for {session_id}")
            
            try:
                # Create and start streaming recognize directly (like test.py)
                logger.bind(tag=TAG).info(f"[CONTINUOUS-STREAM] About to start Google API streaming for {session_id}")
                responses = self.client.streaming_recognize(requests=request_generator())
                logger.bind(tag=TAG).info(f"[CONTINUOUS-STREAM] Google API streaming call made for {session_id}")
                
                # Process responses continuously (like test.py)
                response_count = 0
                for response in responses:
                    if not session_data['session_active']:
                        logger.bind(tag=TAG).info(f"[CONTINUOUS-STREAM] Session {session_id} ended, stopping")
                        break
                    
                    response_count += 1
                    logger.bind(tag=TAG).info(f"[CONTINUOUS-STREAM] Got response #{response_count} from Google API")
                    
                    # Log full response for debugging
                    if hasattr(response, 'results'):
                        logger.bind(tag=TAG).debug(f"[CONTINUOUS-STREAM] Response has {len(response.results)} results")
                    
                    # Process results (same as test.py logic)
                    if not response.results:
                        logger.bind(tag=TAG).debug(f"[CONTINUOUS-STREAM] Response #{response_count} has no results")
                        continue
                        
                    result = response.results[0]
                    if not result.alternatives:
                        logger.bind(tag=TAG).debug(f"[CONTINUOUS-STREAM] Result has no alternatives")
                        continue
                        
                    transcript = result.alternatives[0].transcript.strip()
                    if not transcript:
                        logger.bind(tag=TAG).debug(f"[CONTINUOUS-STREAM] Transcript is empty")
                        continue
                    
                    if result.is_final:
                        session_data['final_transcript'] += transcript + " "
                        session_data['partial_transcript'] = ""
                        logger.bind(tag=TAG).info(f"[CONTINUOUS-STREAM] FINAL: '{transcript}'")
                    else:
                        session_data['partial_transcript'] = transcript
                        logger.bind(tag=TAG).info(f"[CONTINUOUS-STREAM] PARTIAL: '{transcript}'")
                
                logger.bind(tag=TAG).info(f"[CONTINUOUS-STREAM] Response processing loop ended for {session_id} ({response_count} responses)")
                
            except Exception as api_error:
                logger.bind(tag=TAG).error(f"[CONTINUOUS-STREAM] Google API error: {api_error}")
                import traceback
                logger.bind(tag=TAG).error(f"[CONTINUOUS-STREAM] API traceback: {traceback.format_exc()}")
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"[CONTINUOUS-STREAM] Error for {session_id}: {e}")
            import traceback
            logger.bind(tag=TAG).error(f"[CONTINUOUS-STREAM] Traceback: {traceback.format_exc()}")
        finally:
            logger.bind(tag=TAG).info(f"[CONTINUOUS-STREAM] Task ended for {session_id}")

    async def _simplified_streaming_task(self, session_id: str, session_data: dict):
        """Direct streaming task that initializes the Google API connection."""
        logger.bind(tag=TAG).info(f"[STREAM-TASK] Starting direct streaming task for session {session_id}")
        
        try:
            # Create streaming configuration
            config = speech_v2.StreamingRecognitionConfig(
                config=speech_v2.RecognitionConfig(
                    explicit_decoding_config=speech_v2.ExplicitDecodingConfig(
                        encoding=self._get_audio_encoding(),
                        sample_rate_hertz=self.sample_rate_hertz,
                        audio_channel_count=1,
                    ),
                    language_codes=session_data['language_codes'],
                    model=session_data['model'],
                    features=speech_v2.RecognitionFeatures(
                        enable_automatic_punctuation=self.enable_automatic_punctuation,
                        profanity_filter=False,
                    ),
                ),
                streaming_features=speech_v2.StreamingRecognitionFeatures(
                    interim_results=True,
                    enable_voice_activity_events=True,
                )
            )
            
            # Create audio queue for direct streaming
            import queue
            audio_queue = queue.Queue()
            session_data['audio_queue'] = audio_queue
            
            def audio_generator():
                """Simple generator for audio data."""
                # Send initial config
                config_request = speech_v2.StreamingRecognizeRequest(
                    recognizer=self.recognizer_name,
                    streaming_config=config
                )
                yield config_request
                logger.bind(tag=TAG).info(f"[AUDIO-GEN] Config sent for {session_id}")
                
                # Stream audio chunks as they arrive
                chunk_count = 0
                while session_data['session_active']:
                    try:
                        audio_chunk = audio_queue.get(timeout=0.1)
                        if audio_chunk is None:
                            break
                        
                        chunk_count += 1
                        logger.bind(tag=TAG).debug(f"[AUDIO-GEN] Streaming chunk #{chunk_count} ({len(audio_chunk)} bytes)")
                        yield speech_v2.StreamingRecognizeRequest(audio=audio_chunk)
                        
                    except queue.Empty:
                        continue
                    except Exception as e:
                        logger.bind(tag=TAG).error(f"[AUDIO-GEN] Generator error: {e}")
                        break
                        
                logger.bind(tag=TAG).info(f"[AUDIO-GEN] Generator finished for {session_id}, sent {chunk_count} chunks")
            
            # Start streaming recognition
            logger.bind(tag=TAG).info(f"[STREAM-TASK] Initializing Google API streaming for {session_id}")
            responses = self.client.streaming_recognize(requests=audio_generator(), timeout=60)
            session_data['responses_iterator'] = responses
            
            # Process responses in real-time
            response_count = 0
            for response in responses:
                if not session_data['session_active']:
                    break
                    
                response_count += 1
                logger.bind(tag=TAG).debug(f"[STREAM-TASK] Processing response #{response_count}")
                
                # Process results
                if hasattr(response, 'results') and response.results:
                    for result in response.results:
                        if result.alternatives:
                            transcript = result.alternatives[0].transcript.strip()
                            if transcript:
                                if result.is_final:
                                    session_data['final_transcript'] += transcript + " "
                                    session_data['partial_transcript'] = ""
                                    logger.bind(tag=TAG).info(f"[STREAM-TASK] FINAL: '{transcript}'")
                                else:
                                    session_data['partial_transcript'] = transcript
                                    logger.bind(tag=TAG).info(f"[STREAM-TASK] PARTIAL: '{transcript}'")
            
            logger.bind(tag=TAG).info(f"[STREAM-TASK] Streaming completed for {session_id} ({response_count} responses)")
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"[STREAM-TASK] Streaming error for {session_id}: {e}")
            import traceback
            logger.bind(tag=TAG).error(f"[STREAM-TASK] Traceback: {traceback.format_exc()}")
        finally:
            logger.bind(tag=TAG).info(f"[STREAM-TASK] Streaming task ended for {session_id}")

    async def stream_audio_chunk(self, conn, audio_chunk: bytes, session_id: str) -> Optional[str]:
        """Stream audio chunk to an active streaming session.
        
        Args:
            conn: Connection object
            audio_chunk: PCM audio data to stream
            session_id: Session identifier
            
        Returns:
            Latest partial transcript if available, None otherwise
        """
        try:
            # Check if streaming session exists (VAD should have started it)
            if session_id not in self.streaming_sessions:
                logger.bind(tag=TAG).debug(f"[STREAM-AUDIO] No active streaming session for {session_id}, ignoring audio chunk")
                return None
                
            session_data = self.streaming_sessions[session_id]
            session_data['audio_count'] += 1
            
            # Queue all audio chunks (including silence) for continuous streaming
            if session_data.get('audio_queue'):
                session_data['audio_queue'].put(audio_chunk)
                # Log every 10th chunk to avoid log spam
                if session_data['audio_count'] % 10 == 0:
                    logger.bind(tag=TAG).info(f"[STREAM-AUDIO] Queued chunk #{session_data['audio_count']} ({len(audio_chunk)} bytes)")
            else:
                logger.bind(tag=TAG).error(f"[STREAM-AUDIO] No audio queue for {session_id} - THIS IS THE PROBLEM!")
            
            # Return partial transcript for real-time feedback
            partial = session_data.get('partial_transcript', '')
            if partial:
                logger.bind(tag=TAG).info(f"[STREAM-AUDIO] Partial: '{partial}'")
                return partial
                
            return None
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"[STREAM-AUDIO] Error for {session_id}: {e}")
            return None

    async def end_streaming_session(self, conn, session_id: str) -> Tuple[str, Optional[str]]:
        """End the streaming ASR session and get final transcript.
        
        Args:
            conn: Connection object
            session_id: Session identifier
            
        Returns:
            Tuple of (final_transcript, file_path)
        """
        try:
            if session_id not in self.streaming_sessions:
                logger.bind(tag=TAG).warning(f"[STREAM-END] No active streaming session for {session_id}")
                return "", None
                
            session_data = self.streaming_sessions[session_id]
            logger.bind(tag=TAG).info(f"[STREAM-END] Ending streaming session: {session_id}")
            
            # Signal end of audio stream
            session_data['session_active'] = False
            
            # Send end signal to audio queue (like test.py ending)
            if session_data.get('audio_queue'):
                session_data['audio_queue'].put(None)
                logger.bind(tag=TAG).debug(f"[STREAM-END] Sent end signal to audio queue for {session_id}")
            
            logger.bind(tag=TAG).debug(f"[STREAM-END] Marked session {session_id} as inactive")
            
            # Wait for streaming task to complete
            if session_data['streaming_task']:
                try:
                    logger.bind(tag=TAG).debug(f"[STREAM-END] Waiting for streaming task to complete for {session_id}")
                    await asyncio.wait_for(session_data['streaming_task'], timeout=3.0)
                    logger.bind(tag=TAG).debug(f"[STREAM-END] Streaming task completed for {session_id}")
                except asyncio.TimeoutError:
                    logger.bind(tag=TAG).warning(f"[STREAM-END] Streaming task timeout for {session_id}, cancelling")
                    session_data['streaming_task'].cancel()
                    try:
                        await session_data['streaming_task']
                    except asyncio.CancelledError:
                        pass
            
            # Get final transcript
            final_transcript = session_data.get('final_transcript', '').strip()
            audio_count = session_data.get('audio_count', 0)
            
            logger.bind(tag=TAG).info(f"[STREAM-END] Session {session_id} processed {audio_count} audio chunks")
            logger.bind(tag=TAG).info(f"[STREAM-END] Final transcript for {session_id}: '{final_transcript}'")
            
            # Clean up session (check if exists to avoid KeyError on double-call)
            if session_id in self.streaming_sessions:
                del self.streaming_sessions[session_id]
            
            return final_transcript, None
            
        except Exception as e:
            logger.bind(tag=TAG).error(f"[STREAM-END] Error ending streaming session {session_id}: {e}")
            import traceback
            logger.bind(tag=TAG).error(f"[STREAM-END] Traceback: {traceback.format_exc()}")
            return "", None