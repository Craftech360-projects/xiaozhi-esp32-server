import time
from typing import Dict, Any, Generator, Optional, Union, Tuple, List
from functools import wraps
from config.langfuse_config import langfuse_config
from config.logger import setup_logging
import json
import tiktoken
from datetime import datetime, timezone
# Removed TraceContext import - using simpler API

logger = setup_logging()
TAG = __name__

# DEBUG: Log when this module is imported (can be removed in production)
# print(f"\n[DEBUG] LANGFUSE WRAPPER IMPORTED! Module: {__name__}")
logger.bind(tag=TAG).info(f"Langfuse wrapper loaded: {__name__}")


class LangfuseTracker:
    """Fixed Langfuse tracking wrapper for v3+ API"""

    def __init__(self):
        self.client = langfuse_config.get_client()
        self.enabled = langfuse_config.is_enabled()
        self.pricing_config = langfuse_config.get_pricing_config()
        # Store conversation traces for proper STT->LLM->TTS flow tracking
        self.conversation_traces = {}

    def track_llm_call(self, provider_name: str, model_name: Optional[str] = None):
        """Enhanced decorator to track LLM calls with comprehensive metrics including response time"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                
                if not self.enabled:
                    logger.bind(tag=TAG).info(f"Langfuse tracking disabled - skipping {provider_name}")
                    return func(*args, **kwargs)

                # Start timing
                start_time = time.time()

                # Get model name from self if not provided
                actual_model_name = model_name
                if actual_model_name is None and len(args) > 0 and hasattr(args[0], 'model_name'):
                    actual_model_name = args[0].model_name

                # Extract session_id and dialogue from args
                session_id = args[1] if len(args) > 1 else kwargs.get('session_id', 'unknown')
                dialogue = args[2] if len(args) > 2 else kwargs.get('dialogue', [])

                # Log tracking details
                logger.bind(tag=TAG).info(f"Tracking LLM call: session={session_id}, model={actual_model_name}, provider={provider_name}")

                # Prepare input for tracking
                input_data = self._prepare_input_data(dialogue, kwargs)

                # Get conversation trace for this session
                trace = self._get_or_create_conversation_trace(session_id)

                # Create the trace/generation BEFORE calling the function
                generation = None
                try:
                    # Use the new Langfuse API
                    generation = self.client.start_generation(
                        name=f"{provider_name}_llm_call",
                        input=input_data,
                        model=actual_model_name,
                        trace_id=trace if trace else None,
                        metadata={
                            "session_id": session_id,
                            "provider": provider_name,
                            "start_time": datetime.now(timezone.utc).isoformat(),
                            "streaming": True,
                            "step": "2_llm"
                        }
                    )
                    
                    logger.bind(tag=TAG).info(f"Langfuse generation started: {generation.id if hasattr(generation, 'id') else 'unknown'}")

                    # Call the original function
                    result = func(*args, **kwargs)

                    if hasattr(result, '__iter__') and not isinstance(result, str):
                        # Streaming response - wrap the generator
                        return self._track_streaming_response_v2(
                            result, generation, start_time, input_data, actual_model_name
                        )
                    else:
                        # Non-streaming response
                        end_time = time.time()
                        response_time = end_time - start_time
                        
                        # Calculate tokens and cost
                        input_tokens = self._count_tokens(input_data, actual_model_name)
                        output_tokens = self._count_tokens(result, actual_model_name)
                        cost = self._calculate_cost(input_tokens, output_tokens, actual_model_name)
                        
                        generation.update(
                            output=result,
                            metadata={
                                "response_time_seconds": response_time,
                                "input_tokens": input_tokens,
                                "output_tokens": output_tokens,
                                "total_cost": cost["total_cost"]
                            }
                        )
                        generation.end()
                        
                        # Force flush
                        self.client.flush()
                        logger.bind(tag=TAG).info(f"LLM call tracked successfully")
                        
                        return result

                except Exception as e:
                    if generation:
                        end_time = time.time()
                        response_time = end_time - start_time
                        generation.update(
                            output=f"Error: {str(e)}",
                            level="ERROR",
                            status_message=str(e),
                            metadata={"response_time_seconds": response_time}
                        )
                        generation.end()
                        self.client.flush()
                    
                    logger.bind(tag=TAG).error(f"Langfuse tracking error: {e}")
                    raise e

            return wrapper
        return decorator

    def track_function_call(self, provider_name: str, model_name: Optional[str] = None):
        """Enhanced decorator to track function calling LLM responses"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                
                if not self.enabled:
                    logger.bind(tag=TAG).info(f"Langfuse function tracking disabled - skipping {provider_name}")
                    return func(*args, **kwargs)

                # Start timing
                start_time = time.time()

                # Get model name from self if not provided
                actual_model_name = model_name
                if actual_model_name is None and len(args) > 0 and hasattr(args[0], 'model_name'):
                    actual_model_name = args[0].model_name

                session_id = args[1] if len(args) > 1 else kwargs.get('session_id', 'unknown')
                dialogue = args[2] if len(args) > 2 else kwargs.get('dialogue', [])
                functions = kwargs.get('functions', [])

                input_data = self._prepare_input_data(dialogue, kwargs)
                input_data["available_functions"] = len(functions) if functions else 0

                # Get conversation trace for this session
                trace = self._get_or_create_conversation_trace(session_id)

                # Create the generation BEFORE calling the function
                generation = None
                try:
                    # Use the new Langfuse API
                    generation = self.client.start_generation(
                        name=f"{provider_name}_function_call",
                        input=input_data,
                        model=actual_model_name,
                        trace_id=trace if trace else None,
                        metadata={
                            "session_id": session_id,
                            "provider": provider_name,
                            "function_calling": True,
                            "available_functions": len(functions) if functions else 0,
                            "start_time": datetime.now(timezone.utc).isoformat(),
                            "streaming": True,
                            "step": "2_llm_function"
                        }
                    )
                    
                    logger.bind(tag=TAG).info(f"Langfuse function generation started: {generation.id if hasattr(generation, 'id') else 'unknown'}")

                    result = func(*args, **kwargs)

                    if hasattr(result, '__iter__'):
                        return self._track_function_streaming_response_v2(
                            result, generation, start_time, input_data, actual_model_name
                        )
                    else:
                        # Non-streaming function response
                        end_time = time.time()
                        response_time = end_time - start_time
                        
                        # Calculate tokens and cost
                        input_tokens = self._count_tokens(input_data, actual_model_name)
                        output_tokens = self._count_tokens(result, actual_model_name)
                        cost = self._calculate_cost(input_tokens, output_tokens, actual_model_name)
                        
                        generation.update(
                            output=result,
                            metadata={
                                "response_time_seconds": response_time,
                                "input_tokens": input_tokens,
                                "output_tokens": output_tokens,
                                "total_cost": cost["total_cost"],
                                "function_result": True
                            }
                        )
                        generation.end()
                        
                        # Force flush
                        self.client.flush()
                        logger.bind(tag=TAG).info(f"Function call tracked successfully")
                        
                        return result

                except Exception as e:
                    if generation:
                        end_time = time.time()
                        response_time = end_time - start_time
                        generation.update(
                            output=f"Function Error: {str(e)}",
                            level="ERROR",
                            status_message=str(e),
                            metadata={"response_time_seconds": response_time, "function_error": True}
                        )
                        generation.end()
                        self.client.flush()
                    
                    logger.bind(tag=TAG).error(f"[LANGFUSE] FUNCTION ERROR TRACKED: {e}")
                    raise e

            return wrapper
        return decorator

    def track_stt(self, provider_name: str):
        """Track STT operations with response time and create conversation trace"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                if not self.enabled:
                    return func(*args, **kwargs)

                # Start timing
                start_time = time.time()
                session_id = kwargs.get('session_id', args[1] if len(args) > 1 else 'unknown')

                try:
                    result = func(*args, **kwargs)
                    end_time = time.time()
                    response_time = end_time - start_time

                    # Extract result text
                    text_result = result[0] if isinstance(result, tuple) else result

                    # Create or get conversation trace for this session
                    trace = self._get_or_create_conversation_trace(session_id)

                    # Track STT as the first step in conversation with proper input/output
                    self._track_stt_operation_with_trace(
                        args, kwargs, text_result, provider_name, session_id, response_time, trace
                    )

                    return result

                except Exception as e:
                    end_time = time.time()
                    response_time = end_time - start_time
                    trace = self._get_or_create_conversation_trace(session_id)
                    self._track_stt_error_with_trace(
                        args, kwargs, str(e), provider_name, session_id, response_time, trace
                    )
                    raise e

            return wrapper
        return decorator

    def track_tts(self, provider_name: str):
        """Track TTS operations with response time and link to conversation trace"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                if not self.enabled:
                    return func(*args, **kwargs)

                # Start timing
                start_time = time.time()
                text_input = args[0] if len(args) > 0 else kwargs.get('text', '')
                # Try to get session_id from connection object or fall back
                session_id = 'tts_session'
                if hasattr(args[0] if len(args) > 0 else None, '_current_session_id'):
                    session_id = getattr(args[0], '_current_session_id')
                elif hasattr(args[0] if len(args) > 0 else None, 'conn') and hasattr(args[0].conn, 'session_id'):
                    session_id = args[0].conn.session_id

                try:
                    result = func(*args, **kwargs)
                    end_time = time.time()
                    response_time = end_time - start_time

                    # Get conversation trace for this session
                    trace = self._get_or_create_conversation_trace(session_id)

                    # Track TTS as the final step in conversation with proper input/output
                    self._track_tts_operation_with_trace(
                        text_input, kwargs, result, provider_name, session_id, response_time, trace
                    )

                    return result

                except Exception as e:
                    end_time = time.time()
                    response_time = end_time - start_time
                    trace = self._get_or_create_conversation_trace(session_id)
                    self._track_tts_error_with_trace(
                        text_input, str(e), provider_name, session_id, response_time, trace
                    )
                    raise e

            return wrapper
        return decorator

    def _track_generation(self, input_data, output_data, provider_name, model_name, session_id, functions=None, response_time=None):
        """Track a generation using the correct v3+ API with response time"""
        try:
            # Calculate tokens and cost
            input_tokens = self._count_tokens(input_data, model_name)
            output_tokens = self._count_tokens(output_data, model_name)
            total_tokens = input_tokens + output_tokens
            cost = self._calculate_cost(input_tokens, output_tokens, model_name)

            # Create generation using the new API
            generation = self.client.start_generation(
                name=f"{provider_name}_generation",
                input=input_data,
                model=model_name,
                metadata={
                    "session_id": session_id,
                    "provider": provider_name,
                    "function_calls_available": len(functions) if functions else 0,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": total_tokens,
                    "input_cost": cost["input_cost"],
                    "output_cost": cost["output_cost"],
                    "total_cost": cost["total_cost"],
                    "response_time_seconds": response_time if response_time else 0,
                    "response_time_ms": round(response_time * 1000, 2) if response_time else 0
                }
            )

            # Update with output
            generation.update(output=output_data)
            generation.end()

            # Flush to ensure data is sent
            self.client.flush()

        except Exception as e:
            logger.bind(tag=TAG).debug(f"Failed to track generation: {e}")

    def _track_error(self, input_data, error_msg, provider_name, model_name, session_id, response_time=None):
        """Track an error using the v3+ API with response time"""
        try:
            generation = self.client.start_generation(
                name=f"{provider_name}_error",
                input=input_data,
                model=model_name,
                level="ERROR",
                metadata={
                    "session_id": session_id,
                    "provider": provider_name,
                    "error": True
                }
            )

            generation.update(output=f"Error: {error_msg}")
            generation.end()
            self.client.flush()

        except Exception as e:
            logger.bind(tag=TAG).debug(f"Failed to track error: {e}")

    def _track_stt_operation(self, args, kwargs, result, provider_name, session_id, response_time=None):
        """Track STT operation with response time"""
        try:
            audio_format = kwargs.get('audio_format', 'opus')
            opus_data = args[0] if len(args) > 0 else []

            span = self.client.start_span(
                name=f"STT_{provider_name}",
                input={
                    "audio_metadata": {
                        "format": audio_format,
                        "file_size": len(opus_data) if opus_data else 0
                    }
                },
                metadata={
                    "session_id": session_id,
                    "provider": provider_name,
                    "operation_type": "speech_to_text",
                    "response_time_seconds": response_time if response_time else 0,
                    "response_time_ms": round(response_time * 1000, 2) if response_time else 0
                }
            )

            span.update(
                output={
                    "transcribed_text": result,
                    "text_length": len(result) if isinstance(result, str) else 0
                }
            )
            span.end()
            self.client.flush()

        except Exception as e:
            logger.bind(tag=TAG).debug(f"Failed to track STT: {e}")

    def _track_stt_error(self, args, kwargs, error_msg, provider_name, session_id):
        """Track STT error"""
        try:
            span = self.client.start_span(
                name=f"STT_{provider_name}_error",
                input={"audio_metadata": {"error": "processing_failed"}},
                level="ERROR",
                metadata={
                    "session_id": session_id,
                    "provider": provider_name,
                    "operation_type": "speech_to_text",
                    "error": True
                }
            )

            span.update(output=f"STT Error: {error_msg}")
            span.end()
            self.client.flush()

        except Exception as e:
            logger.bind(tag=TAG).debug(f"Failed to track STT error: {e}")

    def _track_tts_operation(self, text_input, kwargs, result, provider_name, session_id, response_time=None):
        """Track TTS operation with response time"""
        try:
            span = self.client.start_span(
                name=f"TTS_{provider_name}",
                input={
                    "text": text_input,
                    "text_length": len(text_input) if text_input else 0,
                    "voice_settings": self._extract_voice_settings(kwargs)
                },
                metadata={
                    "session_id": session_id,
                    "provider": provider_name,
                    "operation_type": "text_to_speech",
                    "characters_processed": len(text_input) if text_input else 0,
                    "response_time_seconds": response_time if response_time else 0,
                    "response_time_ms": round(response_time * 1000, 2) if response_time else 0
                }
            )

            span.update(
                output={
                    "audio_generated": True,
                    "success": True
                }
            )
            span.end()
            self.client.flush()

        except Exception as e:
            logger.bind(tag=TAG).debug(f"Failed to track TTS: {e}")

    def _track_tts_error(self, text_input, error_msg, provider_name, session_id):
        """Track TTS error"""
        try:
            span = self.client.span(
                name=f"TTS_{provider_name}_error",
                input={"text": text_input},
                level="ERROR",
                status_message=error_msg,
                metadata={
                    "session_id": session_id,
                    "provider": provider_name,
                    "operation_type": "text_to_speech",
                    "error": True
                }
            )

            span.update(output=f"TTS Error: {error_msg}")
            span.end()
            self.client.flush()

        except Exception as e:
            logger.bind(tag=TAG).debug(f"Failed to track TTS error: {e}")

    def _track_streaming_response(self, response_generator, input_data, provider_name, model_name, session_id):
        """Track streaming response"""
        output_chunks = []

        def tracked_generator():
            nonlocal output_chunks
            
            # Start the generation
            generation = None
            try:
                generation = self.client.generation(
                    name=f"{provider_name}_streaming_generation",
                    input=input_data,
                    model=model_name,
                    metadata={
                        "session_id": session_id,
                        "provider": provider_name,
                        "streaming": True
                    }
                )

                for chunk in response_generator:
                    output_chunks.append(chunk)
                    yield chunk

                # After streaming is complete, record the final output
                full_output = ''.join(output_chunks)
                
                # Calculate tokens and cost for the complete response
                input_tokens = self._count_tokens(input_data, model_name)
                output_tokens = self._count_tokens(full_output, model_name)
                cost = self._calculate_cost(input_tokens, output_tokens, model_name)

                generation.update(
                    output=full_output,
                    metadata={
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                        "total_tokens": input_tokens + output_tokens,
                        "input_cost": cost["input_cost"],
                        "output_cost": cost["output_cost"],
                        "total_cost": cost["total_cost"]
                    }
                )
                generation.end()
                self.client.flush()

            except Exception as e:
                if generation:
                    full_output = ''.join(output_chunks)
                    generation.update(
                        output=f"{full_output}\nError: {str(e)}",
                        level="ERROR",
                        status_message=str(e)
                    )
                    generation.end()
                    self.client.flush()
                raise e

        return tracked_generator()

    def _track_streaming_response_v2(self, response_generator, generation, start_time, input_data, model_name):
        """New improved streaming response tracker"""
        output_chunks = []
        
        def tracked_generator():
            nonlocal output_chunks
            
            try:
                for chunk in response_generator:
                    output_chunks.append(chunk)
                    yield chunk
                
                # After streaming is complete, update the generation
                end_time = time.time()
                response_time = end_time - start_time
                full_output = ''.join(output_chunks)
                
                # Calculate tokens and cost for the complete response
                input_tokens = self._count_tokens(input_data, model_name)
                output_tokens = self._count_tokens(full_output, model_name)
                cost = self._calculate_cost(input_tokens, output_tokens, model_name)

                generation.update(
                    output=full_output,
                    metadata={
                        "response_time_seconds": response_time,
                        "response_time_ms": round(response_time * 1000, 2),
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                        "total_tokens": input_tokens + output_tokens,
                        "total_cost": cost["total_cost"],
                        "chunks_count": len(output_chunks),
                        "streaming_complete": True
                    }
                )
                generation.end()
                
                # Force flush immediately after completion
                self.client.flush()
                
                logger.bind(tag=TAG).info(f"Streaming response tracked: {len(output_chunks)} chunks, {len(full_output)} chars")

            except Exception as e:
                # Handle errors in streaming
                full_output = ''.join(output_chunks)
                end_time = time.time()
                response_time = end_time - start_time
                
                generation.update(
                    output=f"{full_output}\nError: {str(e)}",
                    level="ERROR",
                    status_message=str(e),
                    metadata={
                        "response_time_seconds": response_time,
                        "partial_chunks": len(output_chunks),
                        "error_occurred": True
                    }
                )
                generation.end()
                self.client.flush()
                
                logger.bind(tag=TAG).error(f"[LANGFUSE] STREAMING ERROR TRACKED: {e}")
                raise e

        return tracked_generator()

    def _track_function_streaming_response_v2(self, response_generator, generation, start_time, input_data, model_name):
        """New improved function streaming response tracker"""
        output_chunks = []
        function_calls = []
        
        def tracked_generator():
            nonlocal output_chunks, function_calls
            
            try:
                for content, tool_calls in response_generator:
                    if content:
                        output_chunks.append(content)
                    if tool_calls:
                        function_calls.append(tool_calls)
                    yield content, tool_calls
                
                # After streaming is complete, update the generation
                end_time = time.time()
                response_time = end_time - start_time
                full_output = ''.join(filter(None, output_chunks))
                
                result_data = {
                    "content": full_output,
                    "function_calls": function_calls,
                    "function_calls_count": len(function_calls)
                }
                
                # Calculate tokens and cost for the complete response
                input_tokens = self._count_tokens(input_data, model_name)
                output_tokens = self._count_tokens(full_output, model_name)
                cost = self._calculate_cost(input_tokens, output_tokens, model_name)

                generation.update(
                    output=result_data,
                    metadata={
                        "response_time_seconds": response_time,
                        "response_time_ms": round(response_time * 1000, 2),
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                        "total_tokens": input_tokens + output_tokens,
                        "total_cost": cost["total_cost"],
                        "chunks_count": len(output_chunks),
                        "function_calls_count": len(function_calls),
                        "streaming_complete": True
                    }
                )
                generation.end()
                
                # Force flush immediately after completion
                self.client.flush()
                
                logger.bind(tag=TAG).info(f"Function streaming tracked: {len(output_chunks)} chunks, {len(function_calls)} function calls")

            except Exception as e:
                # Handle errors in streaming
                full_output = ''.join(filter(None, output_chunks))
                end_time = time.time()
                response_time = end_time - start_time
                
                generation.update(
                    output=f"Function Error: {str(e)}",
                    level="ERROR",
                    status_message=str(e),
                    metadata={
                        "response_time_seconds": response_time,
                        "partial_chunks": len(output_chunks),
                        "partial_function_calls": len(function_calls),
                        "error_occurred": True
                    }
                )
                generation.end()
                self.client.flush()
                
                logger.bind(tag=TAG).error(f"[LANGFUSE] FUNCTION STREAMING ERROR TRACKED: {e}")
                raise e

        return tracked_generator()

    def _track_function_streaming_response(self, response_generator, input_data, provider_name, model_name, session_id):
        """Track function streaming response"""
        output_chunks = []
        function_calls = []

        def tracked_generator():
            nonlocal output_chunks, function_calls
            
            generation = None
            try:
                generation = self.client.generation(
                    name=f"{provider_name}_function_streaming_generation",
                    input=input_data,
                    model=model_name,
                    metadata={
                        "session_id": session_id,
                        "provider": provider_name,
                        "streaming": True,
                        "function_calling": True
                    }
                )

                for content, tool_calls in response_generator:
                    if content:
                        output_chunks.append(content)
                    if tool_calls:
                        function_calls.append(tool_calls)
                    yield content, tool_calls

                full_output = ''.join(filter(None, output_chunks))
                result_data = {
                    "content": full_output,
                    "function_calls": function_calls,
                    "function_calls_count": len(function_calls)
                }

                # Calculate tokens and cost
                input_tokens = self._count_tokens(input_data, model_name)
                output_tokens = self._count_tokens(full_output, model_name)
                cost = self._calculate_cost(input_tokens, output_tokens, model_name)

                generation.update(
                    output=result_data,
                    usage_details={
                        "input": input_tokens,
                        "output": output_tokens,
                        "total": input_tokens + output_tokens
                    },
                    cost_details={
                        "input": cost["input_cost"],
                        "output": cost["output_cost"],
                        "total": cost["total_cost"]
                    }
                )
                generation.end()
                self.client.flush()

            except Exception as e:
                if generation:
                    generation.update(
                        output=f"Error: {str(e)}",
                        level="ERROR",
                        status_message=str(e)
                    )
                    generation.end()
                    self.client.flush()
                raise e

        return tracked_generator()

    def _get_or_create_conversation_trace(self, session_id: str):
        """Get or create a conversation trace for the session"""
        try:
            if session_id not in self.conversation_traces:
                # Create a trace ID for this conversation
                trace_id = self.client.create_trace_id()
                self.conversation_traces[session_id] = trace_id
                logger.bind(tag=TAG).info(f"Created new conversation trace for session: {session_id} with ID: {trace_id}")
            return self.conversation_traces[session_id]
        except Exception as e:
            logger.bind(tag=TAG).error(f"Failed to create conversation trace: {e}")
            return None

    def _track_stt_operation_with_trace(self, args, kwargs, result, provider_name, session_id, response_time, trace):
        """Track STT operation within conversation trace"""
        try:
            audio_format = kwargs.get('audio_format', 'opus')
            opus_data = args[0] if len(args) > 0 else []

            # Input: Audio metadata (since we can't show raw audio)
            input_data = {
                "audio_metadata": {
                    "format": audio_format,
                    "file_size": len(opus_data) if opus_data else 0,
                    "operation": "speech_to_text"
                }
            }

            # Output: Transcribed text (this becomes input for LLM)
            output_data = {
                "transcribed_text": result,
                "text_length": len(result) if isinstance(result, str) else 0
            }

            # Use the new Langfuse API
            span = self.client.start_span(
                name=f"STT_{provider_name}",
                input=input_data,
                trace_id=trace if trace else None,
                metadata={
                    "session_id": session_id,
                    "provider": provider_name,
                    "operation_type": "speech_to_text",
                    "response_time_seconds": response_time,
                    "response_time_ms": round(response_time * 1000, 2),
                    "step": "1_stt"
                }
            )
            span.update(output=output_data)
            span.end()

            self.client.flush()

        except Exception as e:
            logger.bind(tag=TAG).debug(f"Failed to track STT with trace: {e}")

    def _track_stt_error_with_trace(self, args, kwargs, error_msg, provider_name, session_id, response_time, trace):
        """Track STT error within conversation trace"""
        try:
            input_data = {"audio_metadata": {"error": "processing_failed"}}
            output_data = {"error": error_msg}

            # Use the new Langfuse API
            span = self.client.start_span(
                name=f"STT_{provider_name}_error",
                input=input_data,
                trace_id=trace if trace else None,
                level="ERROR",
                metadata={
                    "session_id": session_id,
                    "provider": provider_name,
                    "operation_type": "speech_to_text",
                    "response_time_seconds": response_time,
                    "error": True,
                    "step": "1_stt"
                }
            )
            span.update(output=output_data, status_message=error_msg)
            span.end()

            self.client.flush()

        except Exception as e:
            logger.bind(tag=TAG).debug(f"Failed to track STT error with trace: {e}")

    def _track_tts_operation_with_trace(self, text_input, kwargs, result, provider_name, session_id, response_time, trace):
        """Track TTS operation within conversation trace"""
        try:
            # Input: Text from LLM (this should be the LLM output)
            input_data = {
                "text": text_input,
                "text_length": len(text_input) if text_input else 0,
                "voice_settings": self._extract_voice_settings(kwargs),
                "operation": "text_to_speech"
            }

            # Output: Audio generated confirmation
            output_data = {
                "audio_generated": True,
                "success": True,
                "characters_processed": len(text_input) if text_input else 0
            }

            # Use the new Langfuse API
            span = self.client.start_span(
                name=f"TTS_{provider_name}",
                input=input_data,
                trace_id=trace if trace else None,
                metadata={
                    "session_id": session_id,
                    "provider": provider_name,
                    "operation_type": "text_to_speech",
                    "characters_processed": len(text_input) if text_input else 0,
                    "response_time_seconds": response_time,
                    "response_time_ms": round(response_time * 1000, 2),
                    "step": "3_tts"
                }
            )
            span.update(output=output_data)
            span.end()

            self.client.flush()

        except Exception as e:
            logger.bind(tag=TAG).debug(f"Failed to track TTS with trace: {e}")

    def _track_tts_error_with_trace(self, text_input, error_msg, provider_name, session_id, response_time, trace):
        """Track TTS error within conversation trace"""
        try:
            input_data = {"text": text_input, "operation": "text_to_speech"}
            output_data = {"error": error_msg}

            # Use the new Langfuse API
            span = self.client.start_span(
                name=f"TTS_{provider_name}_error",
                input=input_data,
                trace_id=trace if trace else None,
                level="ERROR",
                metadata={
                    "session_id": session_id,
                    "provider": provider_name,
                    "operation_type": "text_to_speech",
                    "response_time_seconds": response_time,
                    "error": True,
                    "step": "3_tts"
                }
            )
            span.update(output=output_data, status_message=error_msg)
            span.end()

            self.client.flush()

        except Exception as e:
            logger.bind(tag=TAG).debug(f"Failed to track TTS error with trace: {e}")

    def _prepare_input_data(self, dialogue, kwargs):
        """Enhanced input data preparation"""
        input_data = {
            "messages": dialogue,
            "parameters": {
                k: v for k, v in kwargs.items()
                if k not in ['session_id', 'dialogue', 'functions'] and not callable(v)
            },
            "message_count": len(dialogue) if isinstance(dialogue, list) else 0,
            "total_input_length": sum(len(str(msg)) for msg in dialogue) if isinstance(dialogue, list) else 0
        }
        return input_data

    def _extract_voice_settings(self, kwargs):
        """Extract voice settings for TTS tracking"""
        return {
            k: v for k, v in kwargs.items()
            if k in ['voice_id', 'voice_settings', 'model_id', 'output_format', 'optimize_streaming_latency']
        }

    def _count_tokens(self, text, model_name=None):
        """Enhanced token counting using tiktoken when possible"""
        try:
            if model_name and "gpt" in model_name.lower():
                # Use tiktoken for OpenAI models
                encoding_map = {
                    "gpt-4": "cl100k_base",
                    "gpt-4o": "o200k_base",
                    "gpt-3.5-turbo": "cl100k_base"
                }

                encoding_name = "cl100k_base"  # default
                for model, enc in encoding_map.items():
                    if model in model_name.lower():
                        encoding_name = enc
                        break

                encoding = tiktoken.get_encoding(encoding_name)

                if isinstance(text, str):
                    return len(encoding.encode(text))
                elif isinstance(text, dict):
                    return len(encoding.encode(json.dumps(text)))
                elif isinstance(text, list):
                    return sum(len(encoding.encode(str(item))) for item in text)

            # Fallback to estimation
            return self._estimate_tokens(text)

        except Exception as e:
            logger.bind(tag=TAG).debug(f"Token counting failed, using estimation: {e}")
            return self._estimate_tokens(text)

    def _estimate_tokens(self, text):
        """Improved token estimation"""
        if isinstance(text, str):
            # More accurate estimation: ~4 characters per token on average
            return max(1, len(text) // 4)
        elif isinstance(text, dict):
            return self._estimate_tokens(json.dumps(text))
        elif isinstance(text, list):
            return sum(self._estimate_tokens(item) for item in text)
        else:
            return max(1, len(str(text)) // 4)

    def _calculate_cost(self, input_tokens: int, output_tokens: int, model_name: str = None):
        """Enhanced cost calculation with comprehensive model support"""
        pricing = self.pricing_config.get(
            model_name, self.pricing_config["default"])

        input_cost = (input_tokens / 1000) * pricing["input"]
        output_cost = (output_tokens / 1000) * pricing["output"]
        total_cost = input_cost + output_cost

        return {
            "input_cost": round(input_cost, 6),
            "output_cost": round(output_cost, 6),
            "total_cost": round(total_cost, 6),
            "currency": "USD",
            "pricing_model": model_name or "default"
        }


# Global tracker instance
langfuse_tracker = LangfuseTracker()
logger.bind(tag=TAG).info(f"Langfuse tracker initialized - Enabled: {langfuse_tracker.enabled}")