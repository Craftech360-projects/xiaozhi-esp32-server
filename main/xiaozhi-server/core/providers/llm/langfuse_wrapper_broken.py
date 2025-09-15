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
    """Simple Langfuse tracking using events for conversation flow tracking"""

    def __init__(self):
        self.client = langfuse_config.get_client()
        self.enabled = langfuse_config.is_enabled()
        self.pricing_config = langfuse_config.get_pricing_config()
        # Store conversation data for proper flow tracking
        self.session_data = {}

    def track_stt(self, provider_name: str):
        """Track STT operations using events"""
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

                    # Track STT event
                    self.client.create_event(
                        name=f"STT-{provider_name}",
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
                            "step": "1_stt",
                            "session_id": session_id
                        }
                    )

                    # Store for conversation flow
                    if session_id not in self.session_data:
                        self.session_data[session_id] = {}
                    self.session_data[session_id]['stt_output'] = text_result
                    self.session_data[session_id]['start_time'] = datetime.now().isoformat()

                    self.client.flush()
                    logger.bind(tag=TAG).info(f"STT tracked: {session_id} -> '{text_result[:50]}...'")

                    return result

                except Exception as e:
                    end_time = time.time()
                    response_time = end_time - start_time

                    # Track error event
                    self.client.create_event(
                        name=f"STT-{provider_name}-ERROR",
                        input={"audio_format": kwargs.get('audio_format', 'opus'), "session_id": session_id},
                        output={"error": str(e)},
                        level="ERROR",
                        metadata={
                            "provider": provider_name,
                            "response_time_ms": round(response_time * 1000, 2),
                            "step": "1_stt",
                            "session_id": session_id
                        }
                    )
                    self.client.flush()
                    logger.bind(tag=TAG).error(f"STT error tracked: {e}")
                    raise e

            return wrapper
        return decorator

    def track_llm_call(self, provider_name: str, model_name: Optional[str] = None):
        """Track LLM calls using events"""
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
                        return self._track_streaming_llm(
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

                        # Track LLM event
                        self.client.create_event(
                            name=f"LLM-{provider_name}",
                            input=input_data,
                            output={
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

                        # Store for TTS tracking
                        if session_id not in self.session_data:
                            self.session_data[session_id] = {}
                        self.session_data[session_id]['llm_output'] = result

                        self.client.flush()
                        logger.bind(tag=TAG).info(f"LLM tracked: {session_id} -> '{result[:50]}...'")

                        return result

                except Exception as e:
                    end_time = time.time()
                    response_time = end_time - start_time

                    self.client.create_event(
                        name=f"LLM-{provider_name}-ERROR",
                        input=input_data,
                        output={"error": str(e)},
                        level="ERROR",
                        metadata={
                            "provider": provider_name,
                            "model": actual_model_name,
                            "response_time_ms": round(response_time * 1000, 2),
                            "step": "2_llm",
                            "session_id": session_id
                        }
                    )
                    self.client.flush()
                    logger.bind(tag=TAG).error(f"LLM error tracked: {e}")
                    raise e

            return wrapper
        return decorator

    def track_function_call(self, provider_name: str, model_name: Optional[str] = None):
        """Track LLM function calls using events - same as track_llm_call but with function context"""
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
                        return self._track_streaming_function_llm(
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

                        # Track LLM function event
                        self.client.create_event(
                            name=f"LLM-{provider_name}-FUNCTION",
                            input=input_data,
                            output={
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

                        # Store for TTS tracking
                        if session_id not in self.session_data:
                            self.session_data[session_id] = {}
                        self.session_data[session_id]['llm_output'] = result

                        self.client.flush()
                        logger.bind(tag=TAG).info(f"LLM Function tracked: {session_id} -> '{result[:50] if isinstance(result, str) else str(result)[:50]}...'")

                        return result

                except Exception as e:
                    end_time = time.time()
                    response_time = end_time - start_time

                    self.client.create_event(
                        name=f"LLM-{provider_name}-FUNCTION-ERROR",
                        input=input_data,
                        output={"error": str(e)},
                        level="ERROR",
                        metadata={
                            "provider": provider_name,
                            "model": actual_model_name,
                            "response_time_ms": round(response_time * 1000, 2),
                            "function_calling": True,
                            "step": "2_llm_function",
                            "session_id": session_id
                        }
                    )
                    self.client.flush()
                    logger.bind(tag=TAG).error(f"LLM Function error tracked: {e}")
                    raise e

            return wrapper
        return decorator

    def track_tts(self, provider_name: str):
        """Track TTS operations using events"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                if not self.enabled:
                    return await func(*args, **kwargs)

                start_time = time.time()
                text_input = args[0] if len(args) > 0 else kwargs.get('text', '')

                # Try to get session_id from TTS provider
                session_id = 'unknown'
                if hasattr(args[0] if len(args) > 0 else None, '_current_session_id'):
                    session_id = getattr(args[0], '_current_session_id')
                elif len(args) > 0 and hasattr(args[0], 'conn') and hasattr(args[0].conn, 'session_id'):
                    session_id = args[0].conn.session_id

                # Get LLM output for proper flow tracking
                llm_source = ""
                if session_id in self.session_data and 'llm_output' in self.session_data[session_id]:
                    llm_source = self.session_data[session_id]['llm_output']

                try:
                    result = await func(*args, **kwargs)
                    end_time = time.time()
                    response_time = end_time - start_time

                    # Track TTS event
                    self.client.create_event(
                        name=f"TTS-{provider_name}",
                        input={
                            "text": text_input,
                            "from_llm": llm_source,  # Show the flow LLM -> TTS
                            "text_length": len(text_input) if text_input else 0,
                            "session_id": session_id
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
                            "step": "3_tts",
                            "session_id": session_id
                        }
                    )

                    # Mark conversation as complete
                    if session_id in self.session_data:
                        self.session_data[session_id]['end_time'] = datetime.now().isoformat()
                        self.session_data[session_id]['complete'] = True

                    self.client.flush()
                    logger.bind(tag=TAG).info(f"TTS tracked: {session_id} -> '{text_input[:50]}...' to audio")

                    return result

                except Exception as e:
                    end_time = time.time()
                    response_time = end_time - start_time

                    self.client.create_event(
                        name=f"TTS-{provider_name}-ERROR",
                        input={"text": text_input, "session_id": session_id},
                        output={"error": str(e)},
                        level="ERROR",
                        metadata={
                            "provider": provider_name,
                            "response_time_ms": round(response_time * 1000, 2),
                            "step": "3_tts",
                            "session_id": session_id
                        }
                    )
                    self.client.flush()
                    logger.bind(tag=TAG).error(f"TTS error tracked: {e}")
                    raise e

            return wrapper
        return decorator

    def _track_streaming_llm(self, response_generator, provider_name, model_name, input_data, session_id, start_time, stt_input):
        """Track streaming LLM response using events"""
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

                # Track streaming LLM event
                self.client.create_event(
                    name=f"LLM-{provider_name}-STREAM",
                    input=input_data,
                    output={
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

                # Store for TTS tracking
                if session_id not in self.session_data:
                    self.session_data[session_id] = {}
                self.session_data[session_id]['llm_output'] = full_output

                self.client.flush()
                logger.bind(tag=TAG).info(f"Streaming LLM tracked: {len(output_chunks)} chunks")

            except Exception as e:
                self.client.create_event(
                    name=f"LLM-{provider_name}-STREAM-ERROR",
                    input=input_data,
                    output={"error": str(e), "partial_response": ''.join(output_chunks)},
                    level="ERROR",
                    metadata={
                        "provider": provider_name,
                        "model": model_name,
                        "session_id": session_id
                    }
                )
                self.client.flush()
                logger.bind(tag=TAG).error(f"Streaming LLM error: {e}")
                raise e

        return tracked_generator()

    def _track_streaming_function_llm(self, response_generator, provider_name, model_name, input_data, session_id, start_time, functions):
        """Track streaming LLM response with function calling using events"""
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

                # Track streaming LLM function event
                self.client.create_event(
                    name=f"LLM-{provider_name}-FUNCTION-STREAM",
                    input=input_data,
                    output={
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

                # Store for TTS tracking
                if session_id not in self.session_data:
                    self.session_data[session_id] = {}
                self.session_data[session_id]['llm_output'] = full_output

                self.client.flush()
                logger.bind(tag=TAG).info(f"Streaming LLM Function tracked: {len(output_chunks)} chunks, {len(function_calls)} function calls")

            except Exception as e:
                self.client.create_event(
                    name=f"LLM-{provider_name}-FUNCTION-STREAM-ERROR",
                    input=input_data,
                    output={
                        "error": str(e),
                        "partial_response": ''.join(output_chunks),
                        "partial_function_calls": function_calls
                    },
                    level="ERROR",
                    metadata={
                        "provider": provider_name,
                        "model": model_name,
                        "function_calling": True,
                        "session_id": session_id
                    }
                )
                self.client.flush()
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
logger.bind(tag=TAG).info(f"Simple Langfuse tracker initialized - Enabled: {langfuse_tracker.enabled}")