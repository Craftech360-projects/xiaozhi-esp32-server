import time
from typing import Dict, Any, Generator, Optional, Union, Tuple, List
from functools import wraps
from config.langfuse_config import langfuse_config
from config.logger import setup_logging
import json
import tiktoken
from datetime import datetime, timezone

# Import latest Langfuse SDK features for modern tracking (2025 version)
try:
    from langfuse import observe
    from langfuse import Langfuse
    # Try different import paths for context
    try:
        from langfuse.decorators import langfuse_context
    except ImportError:
        try:
            from langfuse import langfuse_context
        except ImportError:
            langfuse_context = None
    LANGFUSE_MODERN_SDK = True
except ImportError:
    LANGFUSE_MODERN_SDK = False
    langfuse_context = None

logger = setup_logging()
TAG = __name__

class ModernLangfuseTracker:
    """Latest 2025 Langfuse tracking with proper STT->LLM->TTS conversation flow visibility"""

    def __init__(self):
        self.client = langfuse_config.get_client()
        self.enabled = langfuse_config.is_enabled()
        self.pricing_config = langfuse_config.get_pricing_config()
        self.modern_sdk = LANGFUSE_MODERN_SDK and self.enabled

        # Enhanced session data for full conversation flow tracking
        self.session_data = {}
        self.active_traces = {}  # Track active traces per session

        logger.bind(tag=TAG).info(f"2025 Langfuse tracker initialized - Enabled: {self.enabled}, Modern SDK: {self.modern_sdk}")

    def track_stt(self, provider_name: str):
        """Track STT operations as the START of conversation flow - shows as dashboard INPUT"""
        def decorator(func):
            if not self.enabled:
                return func

            if self.modern_sdk:
                @observe(name=f"🎤 STT-{provider_name}", as_type="span")
                @wraps(func)
                async def wrapper(*args, **kwargs):
                    # ENSURE manual tracking as backup
                    return await self._track_stt_with_fallback(func, provider_name, *args, **kwargs)
                return wrapper
            else:
                return self._create_stt_fallback_wrapper(func, provider_name)

        return decorator

    async def _track_stt_with_fallback(self, func, provider_name, *args, **kwargs):
        """STT tracking with both modern and fallback approaches"""
        start_time = time.time()
        session_id = kwargs.get('session_id', args[1] if len(args) > 1 else 'unknown')

        # Create or get the main conversation trace for this session
        trace_id = self._get_or_create_conversation_trace(session_id)

        # Update trace with session and conversation metadata (modern SDK)
        if hasattr(langfuse_context, 'update_current_trace') and langfuse_context.update_current_trace:
            try:
                langfuse_context.update_current_trace(
                    session_id=session_id,
                    name=f"🗣️ Conversation-{session_id[:8]}",
                    metadata={
                        "conversation_flow": "STT → LLM → TTS",
                        "step": "1_speech_to_text",
                        "provider": provider_name,
                        "session_id": session_id
                    },
                    tags=["conversation", "multimodal", "stt"]
                )
            except Exception as e:
                logger.bind(tag=TAG).debug(f"Modern trace update failed: {e}")

        # Call the actual STT function
        result = await func(*args, **kwargs)
        processing_time = time.time() - start_time

        # Extract transcribed text
        transcribed_text = result[0] if isinstance(result, tuple) else result

        # Store STT output for LLM input mapping
        if transcribed_text and session_id != 'unknown':
            if session_id not in self.session_data:
                self.session_data[session_id] = {}
            self.session_data[session_id]['stt_output'] = transcribed_text
            self.session_data[session_id]['stt_timestamp'] = time.time()
            self.session_data[session_id]['stt_processing_time'] = processing_time
            self.session_data[session_id]['trace_id'] = trace_id

            logger.bind(tag=TAG).info(f"STT → LLM flow: '{transcribed_text[:50]}...' (session: {session_id})")

        # Update observation (modern SDK)
        if hasattr(langfuse_context, 'update_current_observation') and langfuse_context.update_current_observation:
            try:
                langfuse_context.update_current_observation(
                    input=f"🔊 Audio chunks: {len(args[0]) if len(args) > 0 and args[0] else 0} ({kwargs.get('audio_format', 'opus')})",
                    output=transcribed_text or "[Empty transcription]",
                    metadata={
                        "provider": provider_name,
                        "processing_time_ms": round(processing_time * 1000, 2),
                        "audio_format": kwargs.get('audio_format', 'opus'),
                        "text_length": len(transcribed_text) if transcribed_text else 0,
                        "step": "1_stt",
                        "next_step": "LLM processing"
                    }
                )
            except Exception as e:
                logger.bind(tag=TAG).debug(f"Modern observation update failed: {e}")

        # FALLBACK: Manual API tracking to ensure visibility
        try:
            if self.client and transcribed_text:
                manual_span = self.client.span(
                    trace_id=trace_id,
                    name=f"🎤 STT-{provider_name}",
                    input=f"Audio chunks: {len(args[0]) if len(args) > 0 and args[0] else 0}",
                    output=transcribed_text,
                    metadata={
                        "provider": provider_name,
                        "processing_time_ms": round(processing_time * 1000, 2),
                        "step": "1_stt",
                        "session_id": session_id
                    }
                )
                logger.bind(tag=TAG).debug(f"Manual STT span created successfully")
        except Exception as e:
            logger.bind(tag=TAG).debug(f"Manual STT tracking failed: {e}")

        return result

    def _create_stt_fallback_wrapper(self, func, provider_name):
        """Create STT fallback wrapper for when modern SDK is not available"""
        @wraps(func)
        async def fallback_wrapper(*args, **kwargs):
            return await self._track_stt_with_fallback(func, provider_name, *args, **kwargs)
        return fallback_wrapper


    def track_llm_call(self, provider_name: str, model_name: Optional[str] = None):
        """Track LLM calls as the MIDDLE of conversation flow - shows STT input and LLM output"""
        def decorator(func):
            if not self.enabled:
                return func

            if self.modern_sdk:
                @observe(name=f"🧠 LLM-{provider_name}", as_type="generation")
                @wraps(func)
                def wrapper(*args, **kwargs):
                    # ENSURE manual tracking as backup
                    return self._track_llm_with_fallback(func, provider_name, model_name, *args, **kwargs)
                return wrapper
            else:
                return self._create_llm_fallback_wrapper(func, provider_name, model_name)

        return decorator

    def _track_llm_with_fallback(self, func, provider_name, model_name, *args, **kwargs):
        """LLM tracking with both modern and fallback approaches"""
        start_time = time.time()
        session_id = args[1] if len(args) > 1 else kwargs.get('session_id', 'unknown')
        dialogue = args[2] if len(args) > 2 else kwargs.get('dialogue', [])

        # Get actual model name from provider
        actual_model_name = model_name
        if actual_model_name is None and len(args) > 0 and hasattr(args[0], 'model_name'):
            actual_model_name = args[0].model_name

        # CRITICAL: Get STT input to show proper conversation flow
        stt_input = ""
        stt_processing_time = 0
        if session_id in self.session_data and 'stt_output' in self.session_data[session_id]:
            # Check if STT data is recent (within last 60 seconds for conversation context)
            if time.time() - self.session_data[session_id].get('stt_timestamp', 0) < 60:
                stt_input = self.session_data[session_id]['stt_output']
                stt_processing_time = self.session_data[session_id].get('stt_processing_time', 0)

        # Fallback: extract from dialogue if no STT data
        if not stt_input and dialogue:
            for message in reversed(dialogue):
                if isinstance(message, dict) and message.get('role') == 'user':
                    content = message.get('content', '')
                    if content and content not in ['voice input ready', 'listening...', 'processing...']:
                        stt_input = content
                        break

        # Link to conversation trace
        trace_id = self._get_conversation_trace(session_id)

        # Update generation with STT INPUT for dashboard visibility (modern SDK)
        if hasattr(langfuse_context, 'update_current_generation') and langfuse_context.update_current_generation:
            try:
                langfuse_context.update_current_generation(
                    model=actual_model_name or "unknown",
                    input=stt_input or "[No voice input detected]",  # Shows STT output as LLM input
                    metadata={
                        "provider": provider_name,
                        "model": actual_model_name,
                        "session_id": session_id,
                        "step": "2_llm_processing",
                        "from_stt": bool(stt_input),
                        "stt_processing_time_ms": round(stt_processing_time * 1000, 2) if stt_processing_time else 0,
                        "conversation_flow": "STT → LLM → TTS",
                        "trace_id": trace_id
                    }
                )
            except Exception as e:
                logger.bind(tag=TAG).debug(f"Modern LLM generation update failed: {e}")

        # Call the actual LLM function
        result = func(*args, **kwargs)
        processing_time = time.time() - start_time

        # Handle streaming vs non-streaming response
        if hasattr(result, '__iter__') and not isinstance(result, str):
            # Streaming response - wrap with manual tracking
            return self._track_streaming_llm_with_fallback(result, session_id, stt_input, actual_model_name, provider_name, start_time, trace_id)
        else:
            # Non-streaming response
            return self._track_non_streaming_llm_with_fallback(result, session_id, stt_input, actual_model_name, provider_name, processing_time, trace_id)

    def _track_non_streaming_llm_with_fallback(self, result, session_id, stt_input, model_name, provider_name, processing_time, trace_id):
        """Track non-streaming LLM response with fallback"""
        # Store LLM output for TTS mapping
        if session_id not in self.session_data:
            self.session_data[session_id] = {}
        self.session_data[session_id]['llm_output'] = result
        self.session_data[session_id]['llm_timestamp'] = time.time()
        self.session_data[session_id]['llm_processing_time'] = processing_time

        # Calculate tokens and cost
        input_tokens = self._count_tokens(stt_input, model_name)
        output_tokens = self._count_tokens(result, model_name)
        cost_info = self._calculate_cost(input_tokens, output_tokens, model_name)

        # Update generation with LLM OUTPUT and costs (modern SDK)
        if hasattr(langfuse_context, 'update_current_generation') and langfuse_context.update_current_generation:
            try:
                langfuse_context.update_current_generation(
                    output=result,  # Shows as LLM output in dashboard
                    usage={
                        "input": input_tokens,
                        "output": output_tokens,
                        "total": input_tokens + output_tokens
                    },
                    total_cost=cost_info["total_cost"],
                    metadata={
                        "processing_time_ms": round(processing_time * 1000, 2),
                        "cost_breakdown": cost_info,
                        "next_step": "TTS conversion"
                    }
                )
            except Exception as e:
                logger.bind(tag=TAG).debug(f"Modern LLM generation final update failed: {e}")

        # FALLBACK: Manual API tracking to ensure visibility
        try:
            if self.client:
                manual_generation = self.client.generation(
                    trace_id=trace_id or self._get_or_create_conversation_trace(session_id),
                    name=f"🧠 LLM-{provider_name}",
                    model=model_name or "unknown",
                    input=stt_input or "[No voice input detected]",
                    output=result,
                    usage={
                        "input": input_tokens,
                        "output": output_tokens,
                        "total": input_tokens + output_tokens
                    },
                    total_cost=cost_info["total_cost"],
                    metadata={
                        "provider": provider_name,
                        "processing_time_ms": round(processing_time * 1000, 2),
                        "step": "2_llm",
                        "session_id": session_id,
                        "from_stt": bool(stt_input)
                    }
                )
                logger.bind(tag=TAG).debug(f"Manual LLM generation created successfully")
        except Exception as e:
            logger.bind(tag=TAG).debug(f"Manual LLM tracking failed: {e}")

        logger.bind(tag=TAG).info(f"STT → LLM → TTS: '{stt_input[:30]}...' → '{result[:30]}...' (${cost_info['total_cost']:.6f})")
        return result

    def _track_streaming_llm_with_fallback(self, response_generator, session_id, stt_input, model_name, provider_name, start_time, trace_id):
        """Track streaming LLM response with fallback"""
        output_chunks = []

        def tracked_generator():
            nonlocal output_chunks
            try:
                for chunk in response_generator:
                    if chunk:  # Only append non-empty chunks
                        output_chunks.append(str(chunk))
                    yield chunk

                # Calculate final processing time
                processing_time = time.time() - start_time if start_time > 0 else 0
                full_output = ''.join(output_chunks)

                # Store for TTS mapping
                if session_id not in self.session_data:
                    self.session_data[session_id] = {}
                self.session_data[session_id]['llm_output'] = full_output
                self.session_data[session_id]['llm_timestamp'] = time.time()
                self.session_data[session_id]['llm_processing_time'] = processing_time

                # Calculate costs for tracking
                input_tokens = self._count_tokens(stt_input, model_name)
                output_tokens = self._count_tokens(full_output, model_name)
                cost_info = self._calculate_cost(input_tokens, output_tokens, model_name)

                # Update generation with complete output and costs (modern SDK)
                if hasattr(langfuse_context, 'update_current_generation') and langfuse_context.update_current_generation:
                    try:
                        langfuse_context.update_current_generation(
                            output=full_output,  # Shows as LLM output in dashboard
                            usage={
                                "input": input_tokens,
                                "output": output_tokens,
                                "total": input_tokens + output_tokens
                            },
                            total_cost=cost_info["total_cost"],
                            metadata={
                                "streaming": True,
                                "chunks_count": len(output_chunks),
                                "processing_time_ms": round(processing_time * 1000, 2),
                                "cost_breakdown": cost_info,
                                "next_step": "TTS conversion"
                            }
                        )
                    except Exception as e:
                        logger.bind(tag=TAG).debug(f"Modern streaming LLM update failed: {e}")

                # FALLBACK: Manual streaming tracking
                try:
                    if self.client:
                        manual_generation = self.client.generation(
                            trace_id=trace_id or self._get_or_create_conversation_trace(session_id),
                            name=f"🧠 LLM-{provider_name}-STREAM",
                            model=model_name or "unknown",
                            input=stt_input or "[No voice input detected]",
                            output=full_output,
                            usage={
                                "input": input_tokens,
                                "output": output_tokens,
                                "total": input_tokens + output_tokens
                            },
                            total_cost=cost_info["total_cost"],
                            metadata={
                                "provider": provider_name,
                                "streaming": True,
                                "chunks_count": len(output_chunks),
                                "processing_time_ms": round(processing_time * 1000, 2),
                                "step": "2_llm",
                                "session_id": session_id
                            }
                        )
                        logger.bind(tag=TAG).debug(f"Manual streaming LLM generation created successfully")
                except Exception as e:
                    logger.bind(tag=TAG).debug(f"Manual streaming LLM tracking failed: {e}")

                logger.bind(tag=TAG).info(f"Streaming LLM → TTS: {len(output_chunks)} chunks → '{full_output[:30]}...' (${cost_info.get('total_cost', 0):.6f} cost)")

            except Exception as e:
                logger.bind(tag=TAG).error(f"Streaming LLM tracking error: {e}")

        return tracked_generator()

    def _create_llm_fallback_wrapper(self, func, provider_name, model_name):
        """Create LLM fallback wrapper for when modern SDK is not available"""
        @wraps(func)
        def fallback_wrapper(*args, **kwargs):
            return self._track_llm_with_fallback(func, provider_name, model_name, *args, **kwargs)
        return fallback_wrapper


                    # Get actual model name from provider
                    actual_model_name = model_name
                    if actual_model_name is None and len(args) > 0 and hasattr(args[0], 'model_name'):
                        actual_model_name = args[0].model_name

                    # CRITICAL: Get STT input to show proper conversation flow
                    stt_input = ""
                    stt_processing_time = 0
                    if session_id in self.session_data and 'stt_output' in self.session_data[session_id]:
                        # Check if STT data is recent (within last 60 seconds for conversation context)
                        if time.time() - self.session_data[session_id].get('stt_timestamp', 0) < 60:
                            stt_input = self.session_data[session_id]['stt_output']
                            stt_processing_time = self.session_data[session_id].get('stt_processing_time', 0)

                    # Fallback: extract from dialogue if no STT data
                    if not stt_input and dialogue:
                        for message in reversed(dialogue):
                            if isinstance(message, dict) and message.get('role') == 'user':
                                content = message.get('content', '')
                                if content and content not in ['voice input ready', 'listening...', 'processing...']:
                                    stt_input = content
                                    break

                    # Link to conversation trace
                    trace_id = self._get_conversation_trace(session_id)

                    # Update generation with STT INPUT for dashboard visibility
                    if hasattr(langfuse_context, 'update_current_generation'):
                        langfuse_context.update_current_generation(
                            model=actual_model_name or "unknown",
                            input=stt_input or "[No voice input detected]",  # Shows STT output as LLM input
                            metadata={
                                "provider": provider_name,
                                "model": actual_model_name,
                                "session_id": session_id,
                                "step": "2_llm_processing",
                                "from_stt": bool(stt_input),
                                "stt_processing_time_ms": round(stt_processing_time * 1000, 2) if stt_processing_time else 0,
                                "conversation_flow": "STT → LLM → TTS",
                                "trace_id": trace_id
                            }
                        )

                    # Call the actual LLM function
                    result = func(*args, **kwargs)
                    processing_time = time.time() - start_time

                    # Handle streaming vs non-streaming response
                    if hasattr(result, '__iter__') and not isinstance(result, str):
                        # Streaming response - collect all chunks
                        return self._track_streaming_llm_modern(result, session_id, stt_input, actual_model_name, provider_name, start_time)
                    else:
                        # Non-streaming response
                        # Store LLM output for TTS mapping
                        if session_id not in self.session_data:
                            self.session_data[session_id] = {}
                        self.session_data[session_id]['llm_output'] = result
                        self.session_data[session_id]['llm_timestamp'] = time.time()
                        self.session_data[session_id]['llm_processing_time'] = processing_time

                        # Update generation with LLM OUTPUT and costs for dashboard
                        if hasattr(langfuse_context, 'update_current_generation'):
                            # Calculate tokens and cost
                            input_tokens = self._count_tokens(stt_input, actual_model_name)
                            output_tokens = self._count_tokens(result, actual_model_name)
                            cost_info = self._calculate_cost(input_tokens, output_tokens, actual_model_name)

                            langfuse_context.update_current_generation(
                                output=result,  # Shows as LLM output in dashboard
                                usage={
                                    "input": input_tokens,
                                    "output": output_tokens,
                                    "total": input_tokens + output_tokens
                                },
                                total_cost=cost_info["total_cost"],
                                metadata={
                                    "processing_time_ms": round(processing_time * 1000, 2),
                                    "cost_breakdown": cost_info,
                                    "next_step": "TTS conversion"
                                }
                            )

                        logger.bind(tag=TAG).info(f"STT → LLM → TTS: '{stt_input[:30]}...' → '{result[:30]}...' (${cost_info['total_cost']:.6f})")

                        return result

                return wrapper
            else:
                # Fallback to manual tracking
                @wraps(func)
                def fallback_wrapper(*args, **kwargs):
                    session_id = args[1] if len(args) > 1 else kwargs.get('session_id', 'unknown')
                    dialogue = args[2] if len(args) > 2 else kwargs.get('dialogue', [])

                    # Get STT input
                    stt_input = ""
                    if session_id in self.session_data and 'stt_output' in self.session_data[session_id]:
                        if time.time() - self.session_data[session_id].get('stt_timestamp', 0) < 30:
                            stt_input = self.session_data[session_id]['stt_output']

                    result = func(*args, **kwargs)

                    # Store for TTS
                    if session_id not in self.session_data:
                        self.session_data[session_id] = {}
                    self.session_data[session_id]['llm_output'] = result

                    # Manual tracking
                    try:
                        trace = self.client.trace(name=f"LLM-{provider_name}", session_id=session_id)
                        self.client.generation(
                            trace_id=trace.id,
                            name=f"LLM-{provider_name}",
                            model=model_name or "unknown",
                            input=stt_input or "[No STT input captured]",
                            output=result
                        )
                        self.client.flush()
                    except Exception as e:
                        logger.bind(tag=TAG).error(f"LLM fallback tracking failed: {e}")

                    return result

                return fallback_wrapper

        return decorator

    def track_tts(self, provider_name: str):
        """Track TTS operations as the END of conversation flow - shows as dashboard OUTPUT"""
        def decorator(func):
            if not self.enabled:
                return func

            if self.modern_sdk:
                @observe(name=f"🔊 TTS-{provider_name}", as_type="span")
                @wraps(func)
                async def wrapper(*args, **kwargs):
                    start_time = time.time()
                    text_input = args[1] if len(args) > 1 else kwargs.get('text', '')
                    tts_provider = args[0] if len(args) > 0 else None

                    # Get session_id from TTS provider
                    session_id = 'unknown'
                    if hasattr(tts_provider, '_current_session_id'):
                        session_id = getattr(tts_provider, '_current_session_id')
                    elif hasattr(tts_provider, 'conn') and hasattr(tts_provider.conn, 'session_id'):
                        session_id = tts_provider.conn.session_id

                    # Get conversation context from previous steps
                    conversation_context = self._get_conversation_context(session_id)
                    llm_processing_time = conversation_context.get('llm_processing_time', 0)
                    stt_processing_time = conversation_context.get('stt_processing_time', 0)

                    # Link to main conversation trace
                    trace_id = self._get_conversation_trace(session_id)

                    # Update span with LLM TEXT INPUT and AUDIO OUTPUT for dashboard
                    if hasattr(langfuse_context, 'update_current_observation'):
                        langfuse_context.update_current_observation(
                            input=text_input or "[No text from LLM]",  # Shows LLM output as TTS input
                            output=f"🎵 Audio generated ({provider_name})",  # Shows as final output
                            metadata={
                                "provider": provider_name,
                                "step": "3_text_to_speech",
                                "session_id": session_id,
                                "text_length": len(text_input),
                                "conversation_flow": "STT → LLM → TTS",
                                "from_llm": bool(conversation_context.get('llm_output')),
                                "trace_id": trace_id,
                                "total_stt_time_ms": round(stt_processing_time * 1000, 2),
                                "total_llm_time_ms": round(llm_processing_time * 1000, 2)
                            }
                        )

                    # Call the actual TTS function
                    result = await func(*args, **kwargs)
                    processing_time = time.time() - start_time

                    # Complete the conversation flow and calculate total metrics
                    if session_id in self.session_data:
                        self.session_data[session_id]['tts_processing_time'] = processing_time
                        self.session_data[session_id]['complete'] = True
                        self.session_data[session_id]['end_time'] = time.time()

                        total_time = (
                            stt_processing_time +
                            llm_processing_time +
                            processing_time
                        )

                        # Update the observation with final timing metrics
                        if hasattr(langfuse_context, 'update_current_observation'):
                            langfuse_context.update_current_observation(
                                metadata={
                                    "tts_processing_time_ms": round(processing_time * 1000, 2),
                                    "total_conversation_time_ms": round(total_time * 1000, 2),
                                    "conversation_complete": True,
                                    "flow_summary": f"STT({round(stt_processing_time*1000)}ms) → LLM({round(llm_processing_time*1000)}ms) → TTS({round(processing_time*1000)}ms)"
                                }
                            )

                        logger.bind(tag=TAG).info(f"Conversation complete: STT→LLM→TTS ({round(total_time*1000)}ms total) - Session: {session_id}")

                    return result

                return wrapper
            else:
                # Fallback to manual tracking
                @wraps(func)
                async def fallback_wrapper(*args, **kwargs):
                    text_input = args[1] if len(args) > 1 else kwargs.get('text', '')
                    result = await func(*args, **kwargs)

                    try:
                        trace = self.client.trace(name=f"TTS-{provider_name}")
                        self.client.span(
                            trace_id=trace.id,
                            name=f"TTS-{provider_name}",
                            input={"text": text_input},
                            output={"audio_generated": True}
                        )
                        self.client.flush()
                    except Exception as e:
                        logger.bind(tag=TAG).error(f"TTS fallback tracking failed: {e}")

                    return result

                return fallback_wrapper

        return decorator

    def _get_or_create_conversation_trace(self, session_id: str) -> str:
        """Get or create a conversation trace for the session"""
        if session_id in self.active_traces:
            return self.active_traces[session_id]

        try:
            if self.client:
                trace = self.client.trace(
                    name=f"🗣️ Conversation-{session_id[:8]}",
                    session_id=session_id,
                    metadata={
                        "conversation_flow": "STT → LLM → TTS",
                        "multimodal": True,
                        "session_id": session_id
                    },
                    tags=["conversation", "multimodal", "voice-chat"]
                )
                self.active_traces[session_id] = trace.id
                return trace.id
        except Exception as e:
            logger.bind(tag=TAG).error(f"Failed to create conversation trace: {e}")

        return session_id  # Fallback

    def _get_conversation_trace(self, session_id: str) -> Optional[str]:
        """Get existing conversation trace ID"""
        return self.active_traces.get(session_id) or self.session_data.get(session_id, {}).get('trace_id')

    def _get_conversation_context(self, session_id: str) -> Dict[str, Any]:
        """Get full conversation context for a session"""
        return self.session_data.get(session_id, {})

    def _track_streaming_llm_modern(self, response_generator, session_id, stt_input, model_name, provider_name, start_time=0):
        """Track streaming LLM response and collect all chunks with proper timing (modern SDK)"""
        output_chunks = []

        def tracked_generator():
            nonlocal output_chunks
            try:
                for chunk in response_generator:
                    if chunk:  # Only append non-empty chunks
                        output_chunks.append(str(chunk))
                    yield chunk

                # Calculate final processing time
                processing_time = time.time() - start_time if start_time > 0 else 0
                full_output = ''.join(output_chunks)

                # Store for TTS mapping
                if session_id not in self.session_data:
                    self.session_data[session_id] = {}
                self.session_data[session_id]['llm_output'] = full_output
                self.session_data[session_id]['llm_timestamp'] = time.time()
                self.session_data[session_id]['llm_processing_time'] = processing_time

                # Calculate costs for tracking
                input_tokens = self._count_tokens(stt_input, model_name)
                output_tokens = self._count_tokens(full_output, model_name)
                cost_info = self._calculate_cost(input_tokens, output_tokens, model_name)

                # Update generation with complete output and costs
                if hasattr(langfuse_context, 'update_current_generation'):
                    try:
                        langfuse_context.update_current_generation(
                            output=full_output,  # Shows as LLM output in dashboard
                            usage={
                                "input": input_tokens,
                                "output": output_tokens,
                                "total": input_tokens + output_tokens
                            },
                            total_cost=cost_info["total_cost"],
                            metadata={
                                "streaming": True,
                                "chunks_count": len(output_chunks),
                                "processing_time_ms": round(processing_time * 1000, 2),
                                "cost_breakdown": cost_info,
                                "next_step": "TTS conversion"
                            }
                        )
                    except Exception as e:
                        logger.bind(tag=TAG).error(f"Streaming LLM update failed: {e}")

                logger.bind(tag=TAG).info(f"Streaming LLM → TTS: {len(output_chunks)} chunks → '{full_output[:30]}...' (${cost_info.get('total_cost', 0):.6f} cost)")

            except Exception as e:
                logger.bind(tag=TAG).error(f"Streaming LLM tracking error: {e}")

        return tracked_generator()

    def _track_streaming_llm_fallback(self, response_generator, session_id, stt_input, model_name, provider_name):
        """Track streaming LLM response using manual API (fallback)"""
        output_chunks = []

        def tracked_generator():
            nonlocal output_chunks
            try:
                for chunk in response_generator:
                    if chunk:  # Only append non-empty chunks
                        output_chunks.append(str(chunk))
                    yield chunk

                # After streaming complete, manually track with full output
                full_output = ''.join(output_chunks)

                # Store for TTS mapping
                if session_id not in self.session_data:
                    self.session_data[session_id] = {}
                self.session_data[session_id]['llm_output'] = full_output
                self.session_data[session_id]['llm_timestamp'] = time.time()

                # Manual tracking for streaming
                try:
                    # Get or create trace
                    trace_id = None
                    if session_id in self.session_data and 'trace_id' in self.session_data[session_id]:
                        trace_id = self.session_data[session_id]['trace_id']
                    else:
                        trace = self.client.trace(name=f"LLM-{provider_name}", session_id=session_id)
                        trace_id = trace.id
                        if session_id not in self.session_data:
                            self.session_data[session_id] = {}
                        self.session_data[session_id]['trace_id'] = trace_id

                    # Create generation with final streaming output
                    input_tokens = self._count_tokens(stt_input, model_name)
                    output_tokens = self._count_tokens(full_output, model_name)
                    cost = self._calculate_cost(input_tokens, output_tokens, model_name)

                    generation = self.client.generation(
                        trace_id=trace_id,
                        name=f"LLM-{provider_name}-STREAM",
                        model=model_name or "unknown",
                        input=stt_input or "[No STT input captured]",
                        output=full_output,
                        metadata={
                            "provider": provider_name,
                            "model": model_name,
                            "streaming": True,
                            "chunks_count": len(output_chunks),
                            "session_id": session_id,
                            "step": "2_llm"
                        },
                        usage={
                            "input": input_tokens,
                            "output": output_tokens,
                            "total": input_tokens + output_tokens
                        },
                        total_cost=cost["total_cost"]
                    )

                    self.client.flush()

                except Exception as e:
                    logger.bind(tag=TAG).error(f"Manual streaming tracking failed: {e}")

                logger.bind(tag=TAG).info(f"Streaming LLM fallback tracked - {len(output_chunks)} chunks -> '{full_output[:30]}...'")

            except Exception as e:
                logger.bind(tag=TAG).error(f"Streaming LLM fallback error: {e}")

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
modern_langfuse_tracker = ModernLangfuseTracker()

# Backward compatibility - provide the old interface
class LangfuseTracker:
    """Backward compatibility wrapper for the old interface"""

    def __init__(self):
        self.enabled = modern_langfuse_tracker.enabled
        self.client = modern_langfuse_tracker.client
        self.session_data = modern_langfuse_tracker.session_data

    def track_stt(self, provider_name: str):
        return modern_langfuse_tracker.track_stt(provider_name)

    def track_llm_call(self, provider_name: str, model_name: Optional[str] = None):
        return modern_langfuse_tracker.track_llm_call(provider_name, model_name)

    def track_function_call(self, provider_name: str, model_name: Optional[str] = None):
        # Function calls use the same tracking as regular LLM calls
        return modern_langfuse_tracker.track_llm_call(provider_name, model_name)

    def track_tts(self, provider_name: str):
        return modern_langfuse_tracker.track_tts(provider_name)

# Create the old interface for backward compatibility
langfuse_tracker = LangfuseTracker()

# Log initialization status
if modern_langfuse_tracker.enabled:
    if modern_langfuse_tracker.modern_sdk:
        logger.bind(tag=TAG).info("Modern Langfuse tracker initialized with @observe decorators - Input/Output visibility FIXED!")
    else:
        logger.bind(tag=TAG).info("Modern Langfuse tracker initialized with manual API - Input/Output visibility FIXED!")
else:
    logger.bind(tag=TAG).info("Langfuse tracking disabled")