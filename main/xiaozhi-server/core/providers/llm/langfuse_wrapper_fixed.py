import time
from typing import Dict, Any, Generator, Optional, Union, Tuple, List
from functools import wraps
from config.langfuse_config import langfuse_config
from config.logger import setup_logging
import json
import tiktoken
from datetime import datetime, timezone

logger = setup_logging()
TAG = __name__

class LangfuseTracker:
    """Simple and effective Langfuse tracking wrapper using proper API"""

    def __init__(self):
        self.client = langfuse_config.get_client()
        self.enabled = langfuse_config.is_enabled()
        self.pricing_config = langfuse_config.get_pricing_config()
        # Store trace IDs for sessions to create proper conversation flow
        self.session_traces = {}

    def get_or_create_trace(self, session_id: str) -> str:
        """Get or create a trace ID for this session"""
        if session_id not in self.session_traces:
            trace_id = self.client.create_trace_id()
            self.session_traces[session_id] = trace_id
            logger.bind(tag=TAG).info(f"Created trace for session {session_id}: {trace_id}")
        return self.session_traces[session_id]

    def track_stt(self, provider_name: str):
        """Track STT operations with proper input/output for conversation flow"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                if not self.enabled:
                    return func(*args, **kwargs)

                start_time = time.time()
                session_id = kwargs.get('session_id', args[1] if len(args) > 1 else 'unknown')
                trace_id = self.get_or_create_trace(session_id)

                try:
                    result = func(*args, **kwargs)
                    end_time = time.time()
                    response_time = end_time - start_time

                    # Extract text result
                    text_result = result[0] if isinstance(result, tuple) else result

                    # Create STT span with proper input/output
                    span = self.client.start_span(
                        name=f"STT-{provider_name}",
                        trace_id=trace_id,
                        input={
                            "audio_format": kwargs.get('audio_format', 'opus'),
                            "audio_chunks": len(args[0]) if len(args) > 0 and args[0] else 0,
                            "session_id": session_id
                        },
                        output={
                            "transcribed_text": text_result,
                            "text_length": len(text_result) if text_result else 0
                        },
                        metadata={
                            "provider": provider_name,
                            "operation": "speech_to_text",
                            "response_time_ms": round(response_time * 1000, 2),
                            "step": "1_stt"
                        }
                    )
                    span.end()

                    # Store STT result in session for LLM tracking
                    self.session_traces[f"{session_id}_stt_output"] = text_result

                    self.client.flush()
                    logger.bind(tag=TAG).info(f"STT tracked: {session_id} -> '{text_result[:50]}...'")

                    return result

                except Exception as e:
                    end_time = time.time()
                    response_time = end_time - start_time

                    # Track error
                    error_span = self.client.start_span(
                        name=f"STT-{provider_name}-ERROR",
                        trace_id=trace_id,
                        input={"audio_format": kwargs.get('audio_format', 'opus')},
                        output={"error": str(e)},
                        level="ERROR",
                        metadata={
                            "provider": provider_name,
                            "response_time_ms": round(response_time * 1000, 2),
                            "step": "1_stt"
                        }
                    )
                    error_span.end()
                    self.client.flush()

                    logger.bind(tag=TAG).error(f"STT error tracked: {e}")
                    raise e

            return wrapper
        return decorator

    def track_llm_call(self, provider_name: str, model_name: Optional[str] = None):
        """Track LLM calls with proper input from STT and output for TTS"""
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

                trace_id = self.get_or_create_trace(session_id)

                # Prepare input - use STT output as LLM input for proper flow tracking
                stt_output = self.session_traces.get(f"{session_id}_stt_output")
                input_data = {
                    "messages": dialogue,
                    "stt_input": stt_output,  # Link STT output to LLM input
                    "message_count": len(dialogue) if dialogue else 0
                }

                try:
                    result = func(*args, **kwargs)

                    if hasattr(result, '__iter__') and not isinstance(result, str):
                        # Streaming response
                        return self._track_streaming_llm(
                            result, trace_id, provider_name, actual_model_name,
                            input_data, session_id, start_time
                        )
                    else:
                        # Non-streaming response
                        end_time = time.time()
                        response_time = end_time - start_time

                        # Track LLM generation
                        generation = self.client.start_generation(
                            name=f"LLM-{provider_name}",
                            trace_id=trace_id,
                            input=input_data,
                            output={"response": result},
                            model=actual_model_name,
                            metadata={
                                "provider": provider_name,
                                "response_time_ms": round(response_time * 1000, 2),
                                "step": "2_llm"
                            }
                        )

                        # Calculate tokens and cost
                        input_tokens = self._count_tokens(input_data, actual_model_name)
                        output_tokens = self._count_tokens(result, actual_model_name)
                        cost = self._calculate_cost(input_tokens, output_tokens, actual_model_name)

                        generation.update(
                            usage={
                                "input": input_tokens,
                                "output": output_tokens,
                                "total": input_tokens + output_tokens
                            },
                            metadata={
                                "response_time_ms": round(response_time * 1000, 2),
                                "cost_usd": cost["total_cost"]
                            }
                        )
                        generation.end()

                        # Store LLM output for TTS tracking
                        self.session_traces[f"{session_id}_llm_output"] = result

                        self.client.flush()
                        logger.bind(tag=TAG).info(f"LLM tracked: {session_id} -> '{result[:50]}...'")

                        return result

                except Exception as e:
                    end_time = time.time()
                    response_time = end_time - start_time

                    error_gen = self.client.start_generation(
                        name=f"LLM-{provider_name}-ERROR",
                        trace_id=trace_id,
                        input=input_data,
                        output={"error": str(e)},
                        model=actual_model_name,
                        level="ERROR",
                        metadata={
                            "provider": provider_name,
                            "response_time_ms": round(response_time * 1000, 2),
                            "step": "2_llm"
                        }
                    )
                    error_gen.end()
                    self.client.flush()

                    logger.bind(tag=TAG).error(f"LLM error tracked: {e}")
                    raise e

            return wrapper
        return decorator

    def track_tts(self, provider_name: str):
        """Track TTS operations with LLM output as input"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                if not self.enabled:
                    return func(*args, **kwargs)

                start_time = time.time()
                text_input = args[0] if len(args) > 0 else kwargs.get('text', '')

                # Try to get session_id from TTS provider
                session_id = 'unknown'
                if hasattr(args[0] if len(args) > 0 else None, '_current_session_id'):
                    session_id = getattr(args[0], '_current_session_id')
                elif len(args) > 0 and hasattr(args[0], 'conn') and hasattr(args[0].conn, 'session_id'):
                    session_id = args[0].conn.session_id

                trace_id = self.get_or_create_trace(session_id)

                # Get LLM output to show proper flow
                llm_output = self.session_traces.get(f"{session_id}_llm_output")

                try:
                    result = func(*args, **kwargs)
                    end_time = time.time()
                    response_time = end_time - start_time

                    # Track TTS span
                    span = self.client.start_span(
                        name=f"TTS-{provider_name}",
                        trace_id=trace_id,
                        input={
                            "text": text_input,
                            "llm_source": llm_output,  # Link LLM output to TTS input
                            "text_length": len(text_input) if text_input else 0
                        },
                        output={
                            "audio_generated": True,
                            "audio_format": "wav",
                            "characters_processed": len(text_input) if text_input else 0
                        },
                        metadata={
                            "provider": provider_name,
                            "operation": "text_to_speech",
                            "response_time_ms": round(response_time * 1000, 2),
                            "step": "3_tts"
                        }
                    )
                    span.end()
                    self.client.flush()

                    logger.bind(tag=TAG).info(f"TTS tracked: {session_id} -> '{text_input[:50]}...' to audio")

                    return result

                except Exception as e:
                    end_time = time.time()
                    response_time = end_time - start_time

                    error_span = self.client.start_span(
                        name=f"TTS-{provider_name}-ERROR",
                        trace_id=trace_id,
                        input={"text": text_input},
                        output={"error": str(e)},
                        level="ERROR",
                        metadata={
                            "provider": provider_name,
                            "response_time_ms": round(response_time * 1000, 2),
                            "step": "3_tts"
                        }
                    )
                    error_span.end()
                    self.client.flush()

                    logger.bind(tag=TAG).error(f"TTS error tracked: {e}")
                    raise e

            return wrapper
        return decorator

    def _track_streaming_llm(self, response_generator, trace_id, provider_name, model_name, input_data, session_id, start_time):
        """Track streaming LLM response"""
        output_chunks = []

        generation = self.client.start_generation(
            name=f"LLM-{provider_name}-STREAM",
            trace_id=trace_id,
            input=input_data,
            model=model_name,
            metadata={
                "provider": provider_name,
                "streaming": True,
                "step": "2_llm"
            }
        )

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

                generation.update(
                    output={"response": full_output},
                    usage={
                        "input": input_tokens,
                        "output": output_tokens,
                        "total": input_tokens + output_tokens
                    },
                    metadata={
                        "response_time_ms": round(response_time * 1000, 2),
                        "cost_usd": cost["total_cost"],
                        "chunks_count": len(output_chunks)
                    }
                )
                generation.end()

                # Store for TTS tracking
                self.session_traces[f"{session_id}_llm_output"] = full_output

                self.client.flush()
                logger.bind(tag=TAG).info(f"Streaming LLM tracked: {len(output_chunks)} chunks")

            except Exception as e:
                generation.update(
                    output={"error": str(e), "partial_response": ''.join(output_chunks)},
                    level="ERROR"
                )
                generation.end()
                self.client.flush()
                logger.bind(tag=TAG).error(f"Streaming LLM error: {e}")
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

# Global tracker instance
langfuse_tracker = LangfuseTracker()
logger.bind(tag=TAG).info(f"Fixed Langfuse tracker initialized - Enabled: {langfuse_tracker.enabled}")