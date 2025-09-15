import time
from typing import Dict, Any, Generator, Optional, Union, Tuple, List
from functools import wraps
from config.langfuse_config import langfuse_config
from config.logger import setup_logging
import json
import tiktoken
from datetime import datetime, timezone

# Import latest 2025 Langfuse SDK features with @observe decorator
try:
    from langfuse import observe, Langfuse
    from langfuse.decorators import langfuse_context
    LANGFUSE_MODERN_SDK = True
except ImportError:
    try:
        from langfuse import observe, Langfuse
        langfuse_context = None
        LANGFUSE_MODERN_SDK = True
    except ImportError:
        observe = None
        langfuse_context = None
        LANGFUSE_MODERN_SDK = False

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

            # For STT, always use manual tracking due to unhashable List[bytes] parameters
            # The @observe decorator has issues with binary data even with capture_input=False
            @wraps(func)
            async def wrapper(*args, **kwargs):
                start_time = time.time()
                session_id = kwargs.get('session_id', args[2] if len(args) > 2 else 'unknown')

                result = await func(*args, **kwargs)
                processing_time = time.time() - start_time
                transcribed_text = result[0] if isinstance(result, tuple) else result

                # Manual API tracking
                trace_id = self._get_or_create_conversation_trace(session_id)
                self._store_stt_data(session_id, transcribed_text, processing_time, trace_id)

                try:
                    if self.client and transcribed_text:
                        span = self.client.start_span(
                            trace_id=trace_id,
                            name=f"🎤 STT-{provider_name}",
                            input=f"🔊 Audio: {len(args[0]) if args and args[0] else 0} chunks",
                            output=f"📝 Text: {transcribed_text}",
                            metadata={
                                "provider": provider_name,
                                "processing_time_ms": round(processing_time * 1000, 2),
                                "step": "1_stt",
                                "session_id": session_id,
                                "flow_position": "INPUT"
                            }
                        )
                        self.client.flush()
                        logger.bind(tag=TAG).info(f"STT-{provider_name}: '{transcribed_text[:50]}...' ({processing_time*1000:.0f}ms) -> LLM")
                except Exception as e:
                    logger.bind(tag=TAG).debug(f"STT tracking failed: {e}")

                return result

            return wrapper

        return decorator

    def _store_stt_data(self, session_id, transcribed_text, processing_time, trace_id):
        """Store STT data for conversation flow tracking"""
        if transcribed_text and session_id != 'unknown':
            if session_id not in self.session_data:
                self.session_data[session_id] = {}
            self.session_data[session_id].update({
                'stt_output': transcribed_text,
                'stt_timestamp': time.time(),
                'stt_processing_time': processing_time,
                'trace_id': trace_id,
                'conversation_start': time.time()
            })

    def track_llm_call(self, provider_name: str, model_name: Optional[str] = None):
        """Track LLM calls as the MIDDLE of conversation flow - shows STT input and LLM output"""
        def decorator(func):
            if not self.enabled:
                return func

            if self.modern_sdk and observe:
                # Use latest 2025 @observe decorator for LLM generation tracking
                @observe(name=f"🧠 LLM-{provider_name}", as_type="generation", capture_input=True, capture_output=True)
                @wraps(func)
                def wrapper(*args, **kwargs):
                    start_time = time.time()
                    session_id = args[1] if len(args) > 1 else kwargs.get('session_id', 'unknown')

                    # Get model and STT input
                    actual_model_name = self._get_model_name(model_name, args)
                    stt_input = self._get_stt_input(session_id, args)

                    # Call LLM function
                    result = func(*args, **kwargs)
                    processing_time = time.time() - start_time

                    # Handle streaming vs non-streaming
                    if hasattr(result, '__iter__') and not isinstance(result, str):
                        return self._track_streaming_llm_modern(result, session_id, stt_input, actual_model_name, provider_name, start_time)
                    else:
                        return self._track_non_streaming_llm_modern(result, session_id, stt_input, actual_model_name, provider_name, processing_time)

                return wrapper
            else:
                # Fallback manual tracking
                @wraps(func)
                def wrapper(*args, **kwargs):
                    start_time = time.time()
                    session_id = args[1] if len(args) > 1 else kwargs.get('session_id', 'unknown')

                    # Get model and STT input
                    actual_model_name = self._get_model_name(model_name, args)
                    stt_input = self._get_stt_input(session_id, args)
                    trace_id = self._get_conversation_trace(session_id)

                    # Call LLM function
                    result = func(*args, **kwargs)
                    processing_time = time.time() - start_time

                    # Manual tracking
                    if hasattr(result, '__iter__') and not isinstance(result, str):
                        return self._track_streaming_llm_manual(result, session_id, stt_input, actual_model_name, provider_name, start_time, trace_id)
                    else:
                        return self._track_non_streaming_llm_manual(result, session_id, stt_input, actual_model_name, provider_name, processing_time, trace_id)

                return wrapper

        return decorator

    def _get_model_name(self, model_name, args):
        """Extract model name from provider or arguments"""
        if model_name:
            return model_name
        if len(args) > 0 and hasattr(args[0], 'model_name'):
            return args[0].model_name
        return "unknown"

    def _get_stt_input(self, session_id, args):
        """Get STT input for LLM tracking"""
        # Get from session data first
        if session_id in self.session_data and 'stt_output' in self.session_data[session_id]:
            if time.time() - self.session_data[session_id].get('stt_timestamp', 0) < 60:
                return self.session_data[session_id]['stt_output']

        # Fallback: extract from dialogue
        dialogue = args[2] if len(args) > 2 else []
        for message in reversed(dialogue):
            if isinstance(message, dict) and message.get('role') == 'user':
                content = message.get('content', '')
                if content and content not in ['voice input ready', 'listening...', 'processing...']:
                    return content

        return "[No voice input detected]"

    def track_tts(self, provider_name: str):
        """Track TTS operations as the END of conversation flow - shows as dashboard OUTPUT"""
        def decorator(func):
            if not self.enabled:
                return func

            if self.modern_sdk and observe:
                # Use latest 2025 @observe decorator for TTS tracking
                @observe(name=f"🔊 TTS-{provider_name}", as_type="span", capture_input=False, capture_output=False)
                @wraps(func)
                async def wrapper(*args, **kwargs):
                    start_time = time.time()
                    text_input = args[1] if len(args) > 1 else kwargs.get('text', '')
                    session_id = self._get_session_id_from_tts(args)

                    # Call TTS function
                    result = await func(*args, **kwargs)
                    processing_time = time.time() - start_time

                    # Complete conversation tracking
                    self._complete_conversation_flow(session_id, processing_time, text_input, provider_name)

                    return result

                return wrapper
            else:
                # Fallback manual tracking
                @wraps(func)
                async def wrapper(*args, **kwargs):
                    start_time = time.time()
                    text_input = args[1] if len(args) > 1 else kwargs.get('text', '')
                    session_id = self._get_session_id_from_tts(args)

                    result = await func(*args, **kwargs)
                    processing_time = time.time() - start_time

                    # Manual TTS tracking
                    self._track_tts_manual(session_id, text_input, processing_time, provider_name)
                    self._complete_conversation_flow(session_id, processing_time, text_input, provider_name)

                    return result

                return wrapper

        return decorator

    def _get_session_id_from_tts(self, args):
        """Extract session ID from TTS provider"""
        tts_provider = args[0] if len(args) > 0 else None
        if hasattr(tts_provider, '_current_session_id'):
            return getattr(tts_provider, '_current_session_id')
        elif hasattr(tts_provider, 'conn') and hasattr(tts_provider.conn, 'session_id'):
            return tts_provider.conn.session_id
        return 'unknown'

    def _complete_conversation_flow(self, session_id, tts_processing_time, text_input, provider_name):
        """Complete the conversation flow tracking with summary"""
        if session_id in self.session_data:
            # Update session data
            self.session_data[session_id].update({
                'tts_processing_time': tts_processing_time,
                'tts_input': text_input,
                'complete': True,
                'end_time': time.time()
            })

            # Calculate total conversation time
            stt_time = self.session_data[session_id].get('stt_processing_time', 0)
            llm_time = self.session_data[session_id].get('llm_processing_time', 0)
            total_time = stt_time + llm_time + tts_processing_time

            # Log structured conversation completion
            logger.bind(tag=TAG).info(
                f"✅ Conversation Complete: "
                f"🎤 STT({stt_time*1000:.0f}ms) → "
                f"🧠 LLM({llm_time*1000:.0f}ms) → "
                f"🔊 TTS({tts_processing_time*1000:.0f}ms) = "
                f"⏱️ {total_time*1000:.0f}ms total"
            )

    # Modern @observe decorator helper methods
    def _track_streaming_llm_modern(self, response_generator, session_id, stt_input, model_name, provider_name, start_time):
        """Track streaming LLM with modern @observe"""
        output_chunks = []

        def tracked_generator():
            nonlocal output_chunks
            try:
                for chunk in response_generator:
                    if chunk:
                        output_chunks.append(str(chunk))
                    yield chunk

                # Complete tracking
                processing_time = time.time() - start_time
                full_output = ''.join(output_chunks)
                self._store_llm_data(session_id, full_output, processing_time, stt_input, model_name, provider_name)

                logger.bind(tag=TAG).info(f"🧠 LLM-{provider_name}: {len(output_chunks)} chunks → '{full_output[:50]}...' ({processing_time*1000:.0f}ms) → TTS")

            except Exception as e:
                logger.bind(tag=TAG).error(f"Streaming LLM tracking error: {e}")

        return tracked_generator()

    def _track_non_streaming_llm_modern(self, result, session_id, stt_input, model_name, provider_name, processing_time):
        """Track non-streaming LLM with modern @observe"""
        self._store_llm_data(session_id, result, processing_time, stt_input, model_name, provider_name)
        logger.bind(tag=TAG).info(f"🧠 LLM-{provider_name}: '{stt_input[:30]}...' → '{result[:50]}...' ({processing_time*1000:.0f}ms) → TTS")
        return result

    # Manual API helper methods
    def _track_streaming_llm_manual(self, response_generator, session_id, stt_input, model_name, provider_name, start_time, trace_id):
        """Track streaming LLM with manual API"""
        output_chunks = []

        def tracked_generator():
            nonlocal output_chunks
            try:
                for chunk in response_generator:
                    if chunk:
                        output_chunks.append(str(chunk))
                    yield chunk

                # Complete manual tracking
                processing_time = time.time() - start_time
                full_output = ''.join(output_chunks)
                self._store_llm_data(session_id, full_output, processing_time, stt_input, model_name, provider_name)

                # Manual API generation
                try:
                    if self.client:
                        cost_info = self._calculate_cost_info(stt_input, full_output, model_name)
                        generation = self.client.start_generation(
                            trace_id=trace_id,
                            name=f"🧠 LLM-{provider_name}",
                            model=model_name or "unknown",
                            input=f"📝 Voice: {stt_input}",
                            output=f"💭 Response: {full_output}",
                            usage=cost_info["usage"],
                            total_cost=cost_info["total_cost"],
                            metadata={
                                "provider": provider_name,
                                "streaming": True,
                                "chunks": len(output_chunks),
                                "processing_time_ms": round(processing_time * 1000, 2),
                                "step": "2_llm",
                                "session_id": session_id,
                                "flow_position": "MIDDLE"
                            }
                        )
                        self.client.flush()
                except Exception as e:
                    logger.bind(tag=TAG).debug(f"Manual LLM tracking failed: {e}")

                logger.bind(tag=TAG).info(f"🧠 LLM-{provider_name}: {len(output_chunks)} chunks → '{full_output[:50]}...' ({processing_time*1000:.0f}ms) → TTS")

            except Exception as e:
                logger.bind(tag=TAG).error(f"Streaming LLM manual tracking error: {e}")

        return tracked_generator()

    def _track_non_streaming_llm_manual(self, result, session_id, stt_input, model_name, provider_name, processing_time, trace_id):
        """Track non-streaming LLM with manual API"""
        self._store_llm_data(session_id, result, processing_time, stt_input, model_name, provider_name)

        # Manual API generation
        try:
            if self.client:
                cost_info = self._calculate_cost_info(stt_input, result, model_name)
                generation = self.client.generation(
                    trace_id=trace_id,
                    name=f"🧠 LLM-{provider_name}",
                    model=model_name or "unknown",
                    input=f"📝 Voice: {stt_input}",
                    output=f"💭 Response: {result}",
                    usage=cost_info["usage"],
                    total_cost=cost_info["total_cost"],
                    metadata={
                        "provider": provider_name,
                        "processing_time_ms": round(processing_time * 1000, 2),
                        "step": "2_llm",
                        "session_id": session_id,
                        "flow_position": "MIDDLE"
                    }
                )
                self.client.flush()
        except Exception as e:
            logger.bind(tag=TAG).debug(f"Manual LLM tracking failed: {e}")

        logger.bind(tag=TAG).info(f"🧠 LLM-{provider_name}: '{stt_input[:30]}...' → '{result[:50]}...' ({processing_time*1000:.0f}ms) → TTS")
        return result

    def _track_tts_manual(self, session_id, text_input, processing_time, provider_name):
        """Track TTS with manual API"""
        trace_id = self._get_conversation_trace(session_id)
        try:
            if self.client:
                span = self.client.span(
                    trace_id=trace_id,
                    name=f"🔊 TTS-{provider_name}",
                    input=f"💭 Text: {text_input}",
                    output=f"🎵 Audio generated ({provider_name})",
                    metadata={
                        "provider": provider_name,
                        "processing_time_ms": round(processing_time * 1000, 2),
                        "step": "3_tts",
                        "session_id": session_id,
                        "text_length": len(text_input),
                        "flow_position": "OUTPUT"
                    }
                )
                self.client.flush()
        except Exception as e:
            logger.bind(tag=TAG).debug(f"Manual TTS tracking failed: {e}")

    def _store_llm_data(self, session_id, output, processing_time, stt_input, model_name, provider_name):
        """Store LLM data for conversation flow"""
        if session_id not in self.session_data:
            self.session_data[session_id] = {}

        self.session_data[session_id].update({
            'llm_output': output,
            'llm_timestamp': time.time(),
            'llm_processing_time': processing_time,
            'llm_input': stt_input,
            'llm_model': model_name,
            'llm_provider': provider_name
        })

    def _calculate_cost_info(self, input_text, output_text, model_name):
        """Calculate comprehensive cost information"""
        input_tokens = self._count_tokens(input_text, model_name)
        output_tokens = self._count_tokens(output_text, model_name)
        cost_data = self._calculate_cost(input_tokens, output_tokens, model_name)

        return {
            "usage": {
                "input": input_tokens,
                "output": output_tokens,
                "total": input_tokens + output_tokens
            },
            "total_cost": cost_data["total_cost"]
        }

    def _track_non_streaming_llm(self, result, session_id, stt_input, model_name, provider_name, processing_time, trace_id):
        """Track non-streaming LLM response"""
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

        # MANUAL API tracking to ensure visibility
        try:
            if self.client:
                manual_generation = self.client.start_generation(
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
                        "from_stt": bool(stt_input),
                        "cost_breakdown": cost_info
                    }
                )
                logger.bind(tag=TAG).debug(f"LLM generation created successfully")

                # Flush to ensure immediate visibility
                self.client.flush()
        except Exception as e:
            logger.bind(tag=TAG).debug(f"LLM tracking failed: {e}")

        logger.bind(tag=TAG).info(f"STT → LLM → TTS: '{stt_input[:30]}...' → '{result[:30]}...' (${cost_info['total_cost']:.6f})")
        return result

    def _track_streaming_llm(self, response_generator, session_id, stt_input, model_name, provider_name, start_time, trace_id):
        """Track streaming LLM response"""
        output_chunks = []

        def tracked_generator():
            nonlocal output_chunks
            try:
                for chunk in response_generator:
                    if chunk:
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

                # MANUAL streaming tracking
                try:
                    if self.client:
                        manual_generation = self.client.start_generation(
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
                                "session_id": session_id,
                                "cost_breakdown": cost_info
                            }
                        )
                        logger.bind(tag=TAG).debug(f"Streaming LLM generation created successfully")

                        # Flush to ensure immediate visibility
                        self.client.flush()
                except Exception as e:
                    logger.bind(tag=TAG).debug(f"Streaming LLM tracking failed: {e}")

                logger.bind(tag=TAG).info(f"Streaming LLM → TTS: {len(output_chunks)} chunks → '{full_output[:30]}...' (${cost_info.get('total_cost', 0):.6f})")

            except Exception as e:
                logger.bind(tag=TAG).error(f"Streaming LLM tracking error: {e}")

        return tracked_generator()

    def _get_or_create_conversation_trace(self, session_id: str) -> str:
        """Get or create a conversation trace for the session"""
        if session_id in self.active_traces:
            return self.active_traces[session_id]

        try:
            if self.client:
                trace_id = self.client.create_trace_id()
                self.active_traces[session_id] = trace_id
                return trace_id
        except Exception as e:
            logger.bind(tag=TAG).error(f"Failed to create conversation trace: {e}")

        return session_id  # Fallback

    def _get_conversation_trace(self, session_id: str) -> Optional[str]:
        """Get existing conversation trace ID"""
        return self.active_traces.get(session_id) or self.session_data.get(session_id, {}).get('trace_id')

    def _get_conversation_context(self, session_id: str) -> Dict[str, Any]:
        """Get full conversation context for a session"""
        return self.session_data.get(session_id, {})

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
    logger.bind(tag=TAG).info("Langfuse integration FIXED - STT->LLM->TTS flow tracking enabled!")
else:
    logger.bind(tag=TAG).info("Langfuse tracking disabled")