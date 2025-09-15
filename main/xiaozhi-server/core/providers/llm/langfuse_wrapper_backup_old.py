import time
from typing import Dict, Any, Generator, Optional, Union, Tuple, List
from functools import wraps
from config.langfuse_config import langfuse_config
from config.logger import setup_logging
import json
import tiktoken
from datetime import datetime, timezone

# Import latest Langfuse SDK features
try:
    from langfuse import observe
    from langfuse.decorators import langfuse_context
    LANGFUSE_MODERN_SDK = True
except ImportError:
    LANGFUSE_MODERN_SDK = False

logger = setup_logging()
TAG = __name__

class LangfuseTracker:
    """Modern Langfuse tracking using latest SDK patterns with fallback to legacy API"""

    def __init__(self):
        self.client = langfuse_config.get_client()
        self.enabled = langfuse_config.is_enabled()
        self.pricing_config = langfuse_config.get_pricing_config()
        self.modern_sdk = LANGFUSE_MODERN_SDK and self.enabled
        # Store conversation data for proper flow tracking
        self.session_data = {}

    def _safe_track_event(self, name, input_data, output_data, metadata):
        """Safely track using proper trace structure for dashboard visibility"""
        try:
            if not self.enabled or not self.client:
                return False

            session_id = metadata.get('session_id', 'unknown')

            # Create trace structure based on operation type
            if "STT" in name:
                return self._track_stt_simple(name, input_data, output_data, metadata, session_id)
            elif "LLM" in name:
                return self._track_llm_simple(name, input_data, output_data, metadata, session_id)
            elif "TTS" in name:
                return self._track_tts_simple(name, input_data, output_data, metadata, session_id)
            else:
                return self._track_generic_simple(name, input_data, output_data, metadata, session_id)

        except AttributeError as e:
            logger.bind(tag=TAG).error(f"Langfuse API method not available: {e}")
            return False
        except Exception as e:
            logger.bind(tag=TAG).error(f"Langfuse tracking failed: {e}")
            return False

    def _track_stt_simple(self, name, input_data, output_data, metadata, session_id):
        """Track STT using correct Langfuse API"""
        try:
            # Create trace for session if not exists
            trace_name = f"{name}-{session_id[-8:]}" if session_id != 'unknown' else name

            # Create or get trace
            trace = self.client.trace(name=trace_name, session_id=session_id)

            # Create span for STT operation
            span = self.client.span(
                trace_id=trace.id,
                name=name,
                input=input_data,
                output=output_data,
                metadata={
                    **metadata,
                    'trace_type': 'speech_to_text',
                    'session_id': session_id,
                    'operation': 'STT'
                }
            )

            self.client.flush()

            # CRITICAL: Store STT output for LLM input mapping
            transcribed_text = output_data.get('transcribed_text', '')
            if transcribed_text and session_id != 'unknown':
                if session_id not in self.session_data:
                    self.session_data[session_id] = {}
                self.session_data[session_id]['stt_output'] = transcribed_text
                self.session_data[session_id]['stt_timestamp'] = time.time()
                self.session_data[session_id]['trace_id'] = trace.id
                logger.bind(tag=TAG).info(f"STT output stored for session {session_id}: '{transcribed_text[:50]}...'")

            logger.bind(tag=TAG).info(f"STT span tracked: {transcribed_text[:50]}...")
            return True
        except Exception as e:
            logger.bind(tag=TAG).error(f"STT tracking failed: {e}")
            # Fallback to event tracking
            try:
                self.client.event(
                    name=name,
                    input=input_data,
                    output=output_data,
                    metadata=metadata
                )
                self.client.flush()
                return True
            except Exception as fallback_error:
                logger.bind(tag=TAG).error(f"STT fallback tracking failed: {fallback_error}")
            return False

    def _track_llm_simple(self, name, input_data, output_data, metadata, session_id):
        """Track LLM using correct Langfuse API with proper input/output mapping"""
        try:
            # Dashboard Input: Extract STT output (what the user actually said)
            dashboard_input = ""

            # Method 1: Check if provided in input_data
            if 'from_stt' in input_data and input_data['from_stt']:
                dashboard_input = input_data['from_stt']

            # Method 2: Check session data storage
            elif session_id in self.session_data and 'stt_output' in self.session_data[session_id]:
                dashboard_input = self.session_data[session_id]['stt_output']

            # Method 3: Extract from messages if available (skip system messages)
            elif 'messages' in input_data and input_data['messages']:
                # Look for the last user message, not system messages
                for message in reversed(input_data['messages']):
                    if isinstance(message, dict) and 'content' in message:
                        content = message['content']
                        # Skip common system/placeholder messages
                        if content and content not in ['voice input ready', 'listening...', 'processing...']:
                            dashboard_input = content
                            break

            # Method 4: Check recent session data (within last 30 seconds)
            if not dashboard_input and session_id in self.session_data:
                stt_data = self.session_data[session_id]
                if 'stt_output' in stt_data and 'stt_timestamp' in stt_data:
                    # Only use recent STT data (within 30 seconds)
                    if time.time() - stt_data['stt_timestamp'] < 30:
                        dashboard_input = stt_data['stt_output']

            # Method 5: Fallback to any text content (excluding system messages)
            if not dashboard_input:
                # Check for any text content in input_data
                for key in ['text', 'content', 'user_input', 'query']:
                    if key in input_data and input_data[key]:
                        content = input_data[key]
                        if content not in ['voice input ready', 'listening...', 'processing...']:
                            dashboard_input = content
                            break

            # Dashboard Output: LLM response that goes to TTS
            dashboard_output = output_data.get('response', '')
            if not dashboard_output:
                dashboard_output = output_data.get('content', '')

            # Final fallback: if still no input, use a meaningful default
            if not dashboard_input:
                dashboard_input = "[No STT input captured]"
                logger.bind(tag=TAG).warning(f"No STT input found for session {session_id}. Available input_data keys: {list(input_data.keys())}")

            # Debug logging
            logger.bind(tag=TAG).info(f"LLM Input extraction - Session: {session_id}, Input: '{dashboard_input[:50]}...', Output: '{dashboard_output[:50]}...'")

            # Get or create trace
            trace_id = None
            if session_id in self.session_data and 'trace_id' in self.session_data[session_id]:
                trace_id = self.session_data[session_id]['trace_id']
            else:
                trace_name = f"{name}-{session_id[-8:]}" if session_id != 'unknown' else name
                trace = self.client.trace(name=trace_name, session_id=session_id)
                trace_id = trace.id
                if session_id not in self.session_data:
                    self.session_data[session_id] = {}
                self.session_data[session_id]['trace_id'] = trace_id

            # Create generation with proper input/output
            generation = self.client.generation(
                trace_id=trace_id,
                name=name,
                model=metadata.get('model', 'unknown'),
                input=dashboard_input,  # STT output as input
                output=dashboard_output,  # LLM response as output
                metadata={
                    **metadata,
                    'trace_type': 'llm_generation',
                    'session_id': session_id,
                    'input_source': 'STT',
                    'output_destination': 'TTS',
                    'operation': 'LLM'
                }
            )

            # Add usage and cost if available
            if metadata.get('input_tokens'):
                generation = self.client.generation(
                    id=generation.id,
                    usage={
                        "input": metadata.get('input_tokens', 0),
                        "output": metadata.get('output_tokens', 0),
                        "total": metadata.get('total_tokens', 0)
                    },
                    total_cost=metadata.get('cost_usd')
                )

            self.client.flush()

            logger.bind(tag=TAG).info(f"LLM generation tracked - Input: '{dashboard_input[:30]}...' -> Output: '{dashboard_output[:30]}...'")
            return True
        except Exception as e:
            logger.bind(tag=TAG).error(f"LLM tracking failed: {e}")
            return False

    def _track_tts_simple(self, name, input_data, output_data, metadata, session_id):
        """Track TTS using correct Langfuse API"""
        try:
            # Get or create trace
            trace_id = None
            if session_id in self.session_data and 'trace_id' in self.session_data[session_id]:
                trace_id = self.session_data[session_id]['trace_id']
            else:
                trace_name = f"{name}-{session_id[-8:]}" if session_id != 'unknown' else name
                trace = self.client.trace(name=trace_name, session_id=session_id)
                trace_id = trace.id
                if session_id not in self.session_data:
                    self.session_data[session_id] = {}
                self.session_data[session_id]['trace_id'] = trace_id

            # Create span for TTS operation
            span = self.client.span(
                trace_id=trace_id,
                name=name,
                input=input_data,
                output=output_data,
                metadata={
                    **metadata,
                    'trace_type': 'text_to_speech',
                    'session_id': session_id,
                    'input_source': 'LLM',
                    'operation': 'TTS'
                }
            )

            self.client.flush()

            logger.bind(tag=TAG).info(f"TTS span tracked: {input_data.get('text', '')[:50]}...")
            return True
        except Exception as e:
            logger.bind(tag=TAG).error(f"TTS tracking failed: {e}")
            # Fallback to event tracking
            try:
                self.client.event(
                    name=name,
                    input=input_data,
                    output=output_data,
                    metadata=metadata
                )
                self.client.flush()
                logger.bind(tag=TAG).info(f"TTS fallback event tracked: {input_data.get('text', '')[:50]}...")
                return True
            except Exception as fallback_error:
                logger.bind(tag=TAG).error(f"TTS fallback tracking failed: {fallback_error}")
            return False

    def _track_generic_simple(self, name, input_data, output_data, metadata, session_id):
        """Track generic operations using correct Langfuse API"""
        try:
            # Create a trace for generic operations
            trace = self.client.trace(name=name, session_id=session_id)
            span = self.client.span(
                trace_id=trace.id,
                name=name,
                input=input_data,
                output=output_data,
                metadata=metadata
            )
            self.client.flush()
            return True
        except Exception as e:
            logger.bind(tag=TAG).error(f"Generic tracking failed: {e}")
            return False

    # Simplified tracking methods above provide dashboard visibility

    def track_stt_modern(self, provider_name: str):
        """Modern STT tracking using @observe decorator pattern"""
        def decorator(func):
            if not self.enabled or not self.modern_sdk:
                return func

            @observe(name=f"STT-{provider_name}", as_type="span")
            @wraps(func)
            async def wrapper(*args, **kwargs):
                session_id = kwargs.get('session_id', args[1] if len(args) > 1 else 'unknown')

                # Add session context to langfuse
                if hasattr(langfuse_context, 'update_current_trace'):
                    langfuse_context.update_current_trace(
                        session_id=session_id,
                        user_id=kwargs.get('user_id'),
                        metadata={
                            "step": "1_stt",
                            "provider": provider_name,
                            "session_id": session_id
                        }
                    )

                result = await func(*args, **kwargs)

                # Store for conversation flow
                text_result = result[0] if isinstance(result, tuple) else result
                if session_id not in self.session_data:
                    self.session_data[session_id] = {}
                self.session_data[session_id]['stt_output'] = text_result
                self.session_data[session_id]['start_time'] = datetime.now().isoformat()

                return result

            return wrapper
        return decorator

    def track_stt(self, provider_name: str):
        """Track STT operations with safe error handling"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                if not self.enabled:
                    return await func(*args, **kwargs)

                start_time = time.time()
                session_id = kwargs.get('session_id', args[1] if len(args) > 1 else 'unknown')

                try:
                    result = await func(*args, **kwargs)
                    end_time = time.time()
                    response_time = end_time - start_time

                    # Extract text result
                    text_result = result[0] if isinstance(result, tuple) else result

                    # Safe tracking
                    success = self._safe_track_event(
                        name=f"STT-{provider_name}",
                        input_data={
                            "audio_format": kwargs.get('audio_format', 'opus'),
                            "audio_chunks": len(args[0]) if len(args) > 0 and args[0] else 0,
                            "session_id": session_id
                        },
                        output_data={
                            "transcribed_text": text_result,
                            "text_length": len(text_result) if text_result else 0
                        },
                        metadata={
                            "provider": provider_name,
                            "operation": "speech_to_text",
                            "response_time_ms": round(response_time * 1000, 2),
                            "step": "1_stt",
                            "session_id": session_id
                        }
                    )

                    if success:
                        # Store for conversation flow
                        if session_id not in self.session_data:
                            self.session_data[session_id] = {}
                        self.session_data[session_id]['stt_output'] = text_result
                        self.session_data[session_id]['start_time'] = datetime.now().isoformat()
                        logger.bind(tag=TAG).info(f"STT tracked: {session_id} -> '{text_result[:50]}...'")

                    return result

                except Exception as e:
                    end_time = time.time()
                    response_time = end_time - start_time

                    # Safe error tracking
                    self._safe_track_event(
                        name=f"STT-{provider_name}-ERROR",
                        input_data={"audio_format": kwargs.get('audio_format', 'opus'), "session_id": session_id},
                        output_data={"error": str(e)},
                        metadata={
                            "provider": provider_name,
                            "response_time_ms": round(response_time * 1000, 2),
                            "step": "1_stt",
                            "session_id": session_id,
                            "level": "ERROR"
                        }
                    )
                    logger.bind(tag=TAG).error(f"STT error tracked: {e}")
                    raise e

            return wrapper
        return decorator

    def track_llm_modern(self, provider_name: str, model_name: Optional[str] = None):
        """Modern LLM tracking using @observe decorator pattern"""
        def decorator(func):
            if not self.enabled or not self.modern_sdk:
                return func

            @observe(name=f"LLM-{provider_name}", as_type="generation")
            @wraps(func)
            def wrapper(*args, **kwargs):
                session_id = args[1] if len(args) > 1 else kwargs.get('session_id', 'unknown')
                dialogue = args[2] if len(args) > 2 else kwargs.get('dialogue', [])

                # Get model name
                actual_model_name = model_name
                if actual_model_name is None and len(args) > 0 and hasattr(args[0], 'model_name'):
                    actual_model_name = args[0].model_name

                # Get STT input for proper flow tracking
                stt_input = ""
                if session_id in self.session_data and 'stt_output' in self.session_data[session_id]:
                    stt_input = self.session_data[session_id]['stt_output']

                # Update current generation with metadata
                if hasattr(langfuse_context, 'update_current_generation'):
                    langfuse_context.update_current_generation(
                        model=actual_model_name,
                        metadata={
                            "provider": provider_name,
                            "step": "2_llm",
                            "session_id": session_id,
                            "from_stt": stt_input
                        }
                    )

                result = func(*args, **kwargs)

                # Handle streaming vs non-streaming
                if hasattr(result, '__iter__') and not isinstance(result, str):
                    return self._track_streaming_modern(result, session_id)
                else:
                    # Store for TTS tracking
                    if session_id not in self.session_data:
                        self.session_data[session_id] = {}
                    self.session_data[session_id]['llm_output'] = result

                    # Update generation with final result
                    if hasattr(langfuse_context, 'update_current_generation'):
                        input_tokens = self._count_tokens(dialogue, actual_model_name)
                        output_tokens = self._count_tokens(result, actual_model_name)
                        cost = self._calculate_cost(input_tokens, output_tokens, actual_model_name)

                        langfuse_context.update_current_generation(
                            usage={
                                "input": input_tokens,
                                "output": output_tokens,
                                "total": input_tokens + output_tokens
                            },
                            total_cost=cost["total_cost"]
                        )

                    return result

            return wrapper
        return decorator

    def _track_streaming_modern(self, response_generator, session_id):
        """Track streaming response with modern SDK"""
        output_chunks = []

        def tracked_generator():
            nonlocal output_chunks
            for chunk in response_generator:
                output_chunks.append(chunk)
                yield chunk

            # After streaming complete, store for TTS
            full_output = ''.join(output_chunks)
            if session_id not in self.session_data:
                self.session_data[session_id] = {}
            self.session_data[session_id]['llm_output'] = full_output

        return tracked_generator()

    def track_llm_call(self, provider_name: str, model_name: Optional[str] = None):
        """Track LLM calls with safe error handling"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                if not self.enabled:
                    return func(*args, **kwargs)

                start_time = time.time()
                session_id = args[1] if len(args) > 1 else kwargs.get('session_id', 'unknown')
                dialogue = args[2] if len(args) > 2 else kwargs.get('dialogue', [])

                # Get model name
                actual_model_name = model_name
                if actual_model_name is None and len(args) > 0 and hasattr(args[0], 'model_name'):
                    actual_model_name = args[0].model_name

                # Get STT input for proper flow tracking
                stt_input = ""
                if session_id in self.session_data and 'stt_output' in self.session_data[session_id]:
                    stt_input = self.session_data[session_id]['stt_output']

                # Prepare input data
                input_data = {
                    "messages": dialogue,
                    "from_stt": stt_input,  # Show the flow STT -> LLM
                    "message_count": len(dialogue) if dialogue else 0,
                    "session_id": session_id
                }

                try:
                    result = func(*args, **kwargs)

                    if hasattr(result, '__iter__') and not isinstance(result, str):
                        # Streaming response
                        return self._track_streaming_llm_safe(
                            result, provider_name, actual_model_name,
                            input_data, session_id, start_time, stt_input
                        )
                    else:
                        # Non-streaming response
                        end_time = time.time()
                        response_time = end_time - start_time

                        # Calculate tokens and cost
                        input_tokens = self._count_tokens(input_data, actual_model_name)
                        output_tokens = self._count_tokens(result, actual_model_name)
                        cost = self._calculate_cost(input_tokens, output_tokens, actual_model_name)

                        # Safe tracking
                        success = self._safe_track_event(
                            name=f"LLM-{provider_name}",
                            input_data=input_data,
                            output_data={
                                "response": result,
                                "to_tts": result  # Show the flow LLM -> TTS
                            },
                            metadata={
                                "provider": provider_name,
                                "model": actual_model_name,
                                "response_time_ms": round(response_time * 1000, 2),
                                "input_tokens": input_tokens,
                                "output_tokens": output_tokens,
                                "total_tokens": input_tokens + output_tokens,
                                "cost_usd": cost["total_cost"],
                                "step": "2_llm",
                                "session_id": session_id
                            }
                        )

                        if success:
                            # Store for TTS tracking
                            if session_id not in self.session_data:
                                self.session_data[session_id] = {}
                            self.session_data[session_id]['llm_output'] = result
                            logger.bind(tag=TAG).info(f"LLM tracked: {session_id} -> '{result[:50]}...'")

                        return result

                except Exception as e:
                    end_time = time.time()
                    response_time = end_time - start_time

                    self._safe_track_event(
                        name=f"LLM-{provider_name}-ERROR",
                        input_data=input_data,
                        output_data={"error": str(e)},
                        metadata={
                            "provider": provider_name,
                            "model": actual_model_name,
                            "response_time_ms": round(response_time * 1000, 2),
                            "step": "2_llm",
                            "session_id": session_id,
                            "level": "ERROR"
                        }
                    )
                    logger.bind(tag=TAG).error(f"LLM error tracked: {e}")
                    raise e

            return wrapper
        return decorator

    def track_function_call(self, provider_name: str, model_name: Optional[str] = None):
        """Track LLM function calls with safe error handling"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                if not self.enabled:
                    return func(*args, **kwargs)

                start_time = time.time()
                session_id = args[1] if len(args) > 1 else kwargs.get('session_id', 'unknown')
                dialogue = args[2] if len(args) > 2 else kwargs.get('dialogue', [])
                functions = kwargs.get('functions', [])

                # Get model name
                actual_model_name = model_name
                if actual_model_name is None and len(args) > 0 and hasattr(args[0], 'model_name'):
                    actual_model_name = args[0].model_name

                # Get STT input for proper flow tracking
                stt_input = ""
                if session_id in self.session_data and 'stt_output' in self.session_data[session_id]:
                    stt_input = self.session_data[session_id]['stt_output']

                # Prepare input data with function context
                input_data = {
                    "messages": dialogue,
                    "from_stt": stt_input,  # Show the flow STT -> LLM
                    "available_functions": len(functions) if functions else 0,
                    "functions": [f.get('name', 'unknown') for f in functions] if functions else [],
                    "message_count": len(dialogue) if dialogue else 0,
                    "session_id": session_id
                }

                try:
                    result = func(*args, **kwargs)

                    if hasattr(result, '__iter__') and not isinstance(result, str):
                        # Streaming response with functions
                        return self._track_streaming_function_llm_safe(
                            result, provider_name, actual_model_name,
                            input_data, session_id, start_time, functions
                        )
                    else:
                        # Non-streaming response
                        end_time = time.time()
                        response_time = end_time - start_time

                        # Calculate tokens and cost
                        input_tokens = self._count_tokens(input_data, actual_model_name)
                        output_tokens = self._count_tokens(result, actual_model_name)
                        cost = self._calculate_cost(input_tokens, output_tokens, actual_model_name)

                        # Safe tracking
                        success = self._safe_track_event(
                            name=f"LLM-{provider_name}-FUNCTION",
                            input_data=input_data,
                            output_data={
                                "response": result,
                                "to_tts": result,  # Show the flow LLM -> TTS
                                "function_calls": True
                            },
                            metadata={
                                "provider": provider_name,
                                "model": actual_model_name,
                                "response_time_ms": round(response_time * 1000, 2),
                                "input_tokens": input_tokens,
                                "output_tokens": output_tokens,
                                "total_tokens": input_tokens + output_tokens,
                                "cost_usd": cost["total_cost"],
                                "function_calling": True,
                                "available_functions": len(functions) if functions else 0,
                                "step": "2_llm_function",
                                "session_id": session_id
                            }
                        )

                        if success:
                            # Store for TTS tracking
                            if session_id not in self.session_data:
                                self.session_data[session_id] = {}
                            self.session_data[session_id]['llm_output'] = result
                            logger.bind(tag=TAG).info(f"LLM Function tracked: {session_id}")

                        return result

                except Exception as e:
                    end_time = time.time()
                    response_time = end_time - start_time

                    self._safe_track_event(
                        name=f"LLM-{provider_name}-FUNCTION-ERROR",
                        input_data=input_data,
                        output_data={"error": str(e)},
                        metadata={
                            "provider": provider_name,
                            "model": actual_model_name,
                            "response_time_ms": round(response_time * 1000, 2),
                            "function_calling": True,
                            "step": "2_llm_function",
                            "session_id": session_id,
                            "level": "ERROR"
                        }
                    )
                    logger.bind(tag=TAG).error(f"LLM Function error tracked: {e}")
                    raise e

            return wrapper
        return decorator

    def track_tts_modern(self, provider_name: str):
        """Modern TTS tracking using @observe decorator pattern"""
        def decorator(func):
            if not self.enabled or not self.modern_sdk:
                return func

            @observe(name=f"TTS-{provider_name}", as_type="span")
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Fix: args[0] is self (TTS provider), args[1] is text
                text_input = args[1] if len(args) > 1 else kwargs.get('text', '')
                tts_provider = args[0] if len(args) > 0 else None

                # Try to get session_id from TTS provider
                session_id = 'unknown'
                if hasattr(tts_provider, '_current_session_id'):
                    session_id = getattr(tts_provider, '_current_session_id')
                elif hasattr(tts_provider, 'conn') and hasattr(tts_provider.conn, 'session_id'):
                    session_id = tts_provider.conn.session_id

                # Get LLM output for proper flow tracking
                llm_source = ""
                if session_id in self.session_data and 'llm_output' in self.session_data[session_id]:
                    llm_source = self.session_data[session_id]['llm_output']

                # Update current span with metadata
                if hasattr(langfuse_context, 'update_current_span'):
                    langfuse_context.update_current_span(
                        metadata={
                            "provider": provider_name,
                            "operation": "text_to_speech",
                            "step": "3_tts",
                            "session_id": session_id,
                            "from_llm": llm_source,
                            "text_length": len(text_input) if text_input else 0
                        }
                    )

                result = await func(*args, **kwargs)

                # Mark conversation as complete
                if session_id in self.session_data:
                    self.session_data[session_id]['end_time'] = datetime.now().isoformat()
                    self.session_data[session_id]['complete'] = True

                return result

            return wrapper
        return decorator

    def track_tts(self, provider_name: str):
        """Track TTS operations with safe error handling"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                if not self.enabled:
                    return await func(*args, **kwargs)

                start_time = time.time()
                # Fix: args[0] is self (TTS provider), args[1] is text
                text_input = args[1] if len(args) > 1 else kwargs.get('text', '')
                tts_provider = args[0] if len(args) > 0 else None

                # Try to get session_id from TTS provider
                session_id = 'unknown'
                if hasattr(tts_provider, '_current_session_id'):
                    session_id = getattr(tts_provider, '_current_session_id')
                elif hasattr(tts_provider, 'conn') and hasattr(tts_provider.conn, 'session_id'):
                    session_id = tts_provider.conn.session_id

                # Get LLM output for proper flow tracking
                llm_source = ""
                if session_id in self.session_data and 'llm_output' in self.session_data[session_id]:
                    llm_source = self.session_data[session_id]['llm_output']

                try:
                    result = await func(*args, **kwargs)
                    end_time = time.time()
                    response_time = end_time - start_time

                    # Safe tracking
                    success = self._safe_track_event(
                        name=f"TTS-{provider_name}",
                        input_data={
                            "text": text_input,
                            "from_llm": llm_source,  # Show the flow LLM -> TTS
                            "text_length": len(text_input) if text_input else 0,
                            "session_id": session_id
                        },
                        output_data={
                            "audio_generated": True,
                            "audio_format": "wav",
                            "characters_processed": len(text_input) if text_input else 0
                        },
                        metadata={
                            "provider": provider_name,
                            "operation": "text_to_speech",
                            "response_time_ms": round(response_time * 1000, 2),
                            "step": "3_tts",
                            "session_id": session_id
                        }
                    )

                    if success:
                        # Mark conversation as complete
                        if session_id in self.session_data:
                            self.session_data[session_id]['end_time'] = datetime.now().isoformat()
                            self.session_data[session_id]['complete'] = True
                        logger.bind(tag=TAG).info(f"TTS tracked: {session_id} -> '{text_input[:50]}...' to audio")

                    return result

                except Exception as e:
                    end_time = time.time()
                    response_time = end_time - start_time

                    self._safe_track_event(
                        name=f"TTS-{provider_name}-ERROR",
                        input_data={
                            "text": text_input if isinstance(text_input, str) else str(text_input),
                            "session_id": session_id
                        },
                        output_data={"error": str(e)},
                        metadata={
                            "provider": provider_name,
                            "response_time_ms": round(response_time * 1000, 2),
                            "step": "3_tts",
                            "session_id": session_id,
                            "level": "ERROR"
                        }
                    )
                    logger.bind(tag=TAG).error(f"TTS error tracked: {e}")
                    raise e

            return wrapper
        return decorator

    def _track_streaming_llm_safe(self, response_generator, provider_name, model_name, input_data, session_id, start_time, stt_input):
        """Track streaming LLM response with safe error handling"""
        output_chunks = []

        def tracked_generator():
            nonlocal output_chunks
            try:
                for chunk in response_generator:
                    output_chunks.append(chunk)
                    yield chunk

                # After streaming complete
                end_time = time.time()
                response_time = end_time - start_time
                full_output = ''.join(output_chunks)

                # Calculate tokens and cost
                input_tokens = self._count_tokens(input_data, model_name)
                output_tokens = self._count_tokens(full_output, model_name)
                cost = self._calculate_cost(input_tokens, output_tokens, model_name)

                # Safe tracking
                success = self._safe_track_event(
                    name=f"LLM-{provider_name}-STREAM",
                    input_data=input_data,
                    output_data={
                        "response": full_output,
                        "to_tts": full_output  # Show the flow LLM -> TTS
                    },
                    metadata={
                        "provider": provider_name,
                        "model": model_name,
                        "streaming": True,
                        "response_time_ms": round(response_time * 1000, 2),
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                        "total_tokens": input_tokens + output_tokens,
                        "cost_usd": cost["total_cost"],
                        "chunks_count": len(output_chunks),
                        "step": "2_llm",
                        "session_id": session_id
                    }
                )

                if success:
                    # Store for TTS tracking
                    if session_id not in self.session_data:
                        self.session_data[session_id] = {}
                    self.session_data[session_id]['llm_output'] = full_output
                    logger.bind(tag=TAG).info(f"Streaming LLM tracked: {len(output_chunks)} chunks")

            except Exception as e:
                self._safe_track_event(
                    name=f"LLM-{provider_name}-STREAM-ERROR",
                    input_data=input_data,
                    output_data={"error": str(e), "partial_response": ''.join(output_chunks)},
                    metadata={
                        "provider": provider_name,
                        "model": model_name,
                        "session_id": session_id,
                        "level": "ERROR"
                    }
                )
                logger.bind(tag=TAG).error(f"Streaming LLM error: {e}")
                raise e

        return tracked_generator()

    def _track_streaming_function_llm_safe(self, response_generator, provider_name, model_name, input_data, session_id, start_time, functions):
        """Track streaming LLM function response with safe error handling"""
        output_chunks = []
        function_calls = []

        def tracked_generator():
            nonlocal output_chunks, function_calls
            try:
                for item in response_generator:
                    if isinstance(item, tuple) and len(item) == 2:
                        # Function call response format: (content, tool_calls)
                        content, tool_calls = item
                        if content:
                            output_chunks.append(content)
                        if tool_calls:
                            function_calls.extend(tool_calls if isinstance(tool_calls, list) else [tool_calls])
                        yield item
                    else:
                        # Regular content
                        output_chunks.append(str(item))
                        yield item

                # After streaming complete
                end_time = time.time()
                response_time = end_time - start_time
                full_output = ''.join(output_chunks)

                # Calculate tokens and cost
                input_tokens = self._count_tokens(input_data, model_name)
                output_tokens = self._count_tokens(full_output, model_name)
                cost = self._calculate_cost(input_tokens, output_tokens, model_name)

                # Safe tracking
                success = self._safe_track_event(
                    name=f"LLM-{provider_name}-FUNCTION-STREAM",
                    input_data=input_data,
                    output_data={
                        "response": full_output,
                        "to_tts": full_output,  # Show the flow LLM -> TTS
                        "function_calls": function_calls,
                        "function_calls_count": len(function_calls)
                    },
                    metadata={
                        "provider": provider_name,
                        "model": model_name,
                        "streaming": True,
                        "function_calling": True,
                        "response_time_ms": round(response_time * 1000, 2),
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                        "total_tokens": input_tokens + output_tokens,
                        "cost_usd": cost["total_cost"],
                        "chunks_count": len(output_chunks),
                        "function_calls_count": len(function_calls),
                        "available_functions": len(functions) if functions else 0,
                        "step": "2_llm_function",
                        "session_id": session_id
                    }
                )

                if success:
                    # Store for TTS tracking
                    if session_id not in self.session_data:
                        self.session_data[session_id] = {}
                    self.session_data[session_id]['llm_output'] = full_output
                    logger.bind(tag=TAG).info(f"Streaming LLM Function tracked: {len(output_chunks)} chunks, {len(function_calls)} function calls")

            except Exception as e:
                self._safe_track_event(
                    name=f"LLM-{provider_name}-FUNCTION-STREAM-ERROR",
                    input_data=input_data,
                    output_data={
                        "error": str(e),
                        "partial_response": ''.join(output_chunks),
                        "partial_function_calls": function_calls
                    },
                    metadata={
                        "provider": provider_name,
                        "model": model_name,
                        "function_calling": True,
                        "session_id": session_id,
                        "level": "ERROR"
                    }
                )
                logger.bind(tag=TAG).error(f"Streaming LLM Function error: {e}")
                raise e

        return tracked_generator()

    def _count_tokens(self, text, model_name=None):
        """Count tokens for cost calculation"""
        try:
            if model_name and "gpt" in model_name.lower():
                encoding_map = {
                    "gpt-4": "cl100k_base",
                    "gpt-4o": "o200k_base",
                    "gpt-3.5-turbo": "cl100k_base"
                }

                encoding_name = "cl100k_base"
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

            # Fallback estimation
            if isinstance(text, str):
                return max(1, len(text) // 4)
            elif isinstance(text, dict):
                return max(1, len(json.dumps(text)) // 4)
            elif isinstance(text, list):
                return sum(max(1, len(str(item)) // 4) for item in text)
            else:
                return max(1, len(str(text)) // 4)

        except Exception:
            # Simple fallback
            return max(1, len(str(text)) // 4)

    def _calculate_cost(self, input_tokens: int, output_tokens: int, model_name: str = None):
        """Calculate cost based on token usage"""
        try:
            pricing = self.pricing_config.get(model_name, self.pricing_config["default"])

            input_cost = (input_tokens / 1000) * pricing["input"]
            output_cost = (output_tokens / 1000) * pricing["output"]
            total_cost = input_cost + output_cost

            return {
                "input_cost": round(input_cost, 6),
                "output_cost": round(output_cost, 6),
                "total_cost": round(total_cost, 6),
                "currency": "USD"
            }
        except Exception:
            return {
                "input_cost": 0.0,
                "output_cost": 0.0,
                "total_cost": 0.0,
                "currency": "USD"
            }

# Global tracker instance
langfuse_tracker = LangfuseTracker()

# Log initialization status
if langfuse_tracker.enabled:
    if langfuse_tracker.modern_sdk:
        logger.bind(tag=TAG).info(f"Modern Langfuse tracker initialized with @observe decorators - Enabled: True")
        logger.bind(tag=TAG).info("Available: track_stt_modern, track_llm_modern, track_tts_modern (+ legacy fallbacks)")
    else:
        logger.bind(tag=TAG).info(f"Legacy Langfuse tracker initialized with safe event tracking - Enabled: True")
        logger.bind(tag=TAG).info("Available: track_stt, track_llm_call, track_function_call, track_tts")
else:
    logger.bind(tag=TAG).info("Langfuse tracking disabled")