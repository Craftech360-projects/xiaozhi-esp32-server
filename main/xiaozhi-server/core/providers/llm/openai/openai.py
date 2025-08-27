import httpx
import openai
import time
from openai.types import CompletionUsage
from config.logger import setup_logging
from core.utils.util import check_model_key
from core.providers.llm.base import LLMProviderBase


TAG = __name__
logger = setup_logging()



class LLMProvider(LLMProviderBase):
    def __init__(self, config):
        self.model_name = config.get("model_name")
        self.api_key = config.get("api_key")
        if "base_url" in config:
            self.base_url = config.get("base_url")
        else:
            self.base_url = config.get("url")
        # Add timeout configuration item, unit is seconds
        timeout = config.get("timeout", 300)
        self.timeout = int(timeout) if timeout else 300
        
        # Add retry configuration
        max_retries = config.get("max_retries", 2)
        self.max_retries = int(max_retries) if max_retries else 2
        retry_delay = config.get("retry_delay", 1)
        self.retry_delay = float(retry_delay) if retry_delay else 1.0


        param_defaults = {
            "max_tokens": (500, int),
            "temperature": (0.7, lambda x: round(float(x), 1)),
            "top_p": (1.0, lambda x: round(float(x), 1)),
            "frequency_penalty": (0, lambda x: round(float(x), 1)),
        }


        for param, (default, converter) in param_defaults.items():
            value = config.get(param)
            try:
                setattr(
                    self,
                    param,
                    converter(value) if value not in (None, "") else default,
                )
            except (ValueError, TypeError):
                setattr(self, param, default)


        logger.debug(
            f"Intent recognition parameter initialization: {self.temperature}, {self.max_tokens}, {self.top_p}, {self.frequency_penalty}"
        )


        model_key_msg = check_model_key("LLM", self.api_key)
        if model_key_msg:
            logger.bind(tag=TAG).error(model_key_msg)
        self.client = openai.OpenAI(
            api_key=self.api_key, 
            base_url=self.base_url, 
            timeout=httpx.Timeout(self.timeout),
            max_retries=self.max_retries
        )

    def _get_child_friendly_fallback(self, error):
        """Generate simple child-friendly fallback message"""
        return "I'm having a little trouble right now. Let's try talking again after some time!"

    def response(self, session_id, dialogue, **kwargs):
        # Retry logic for API calls
        for attempt in range(self.max_retries):
            try:
                logger.bind(tag=TAG).debug(f"LLM request attempt {attempt + 1}/{self.max_retries}")
                
                responses = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=dialogue,
                    stream=True,
                    max_tokens=kwargs.get("max_tokens", self.max_tokens),
                    temperature=kwargs.get("temperature", self.temperature),
                    top_p=kwargs.get("top_p", self.top_p),
                    frequency_penalty=kwargs.get(
                        "frequency_penalty", self.frequency_penalty
                    ),
                )

                is_active = True
                for chunk in responses:
                    try:
                        # Check if valid choice exists and content is not empty
                        delta = (
                            chunk.choices[0].delta
                            if getattr(chunk, "choices", None)
                            else None
                        )
                        content = delta.content if hasattr(delta, "content") else ""
                    except IndexError:
                        content = ""
                    if content:
                        # Handle case where tags span multiple chunks
                        if "<think>" in content:
                            is_active = False
                            content = content.split("<think>")[0]
                        if "</think>" in content:
                            is_active = True
                            content = content.split("</think>")[-1]
                        if is_active:
                            yield content
                # If we get here, the request was successful, so break out of retry loop
                break
                
            except Exception as e:
                logger.bind(tag=TAG).warning(f"LLM request attempt {attempt + 1} failed: {e}")
                
                # If this was the last attempt, provide child-friendly fallback
                if attempt == self.max_retries - 1:
                    logger.bind(tag=TAG).error(f"All {self.max_retries} LLM attempts failed: {e}")
                    
                    # Generate child-friendly fallback message based on error type
                    fallback_message = self._get_child_friendly_fallback(e)
                    logger.bind(tag=TAG).info(f"Using fallback message for children: {fallback_message}")
                    
                    yield fallback_message
                    return
                
                # Wait before retrying
                logger.bind(tag=TAG).info(f"Retrying in {self.retry_delay} seconds...")
                time.sleep(self.retry_delay)


    def response_with_functions(self, session_id, dialogue, functions=None):
        try:
            stream = self.client.chat.completions.create(
                model=self.model_name, messages=dialogue, stream=True, tools=functions
            )


            for chunk in stream:
                # Check if valid choice exists and content is not empty
                if getattr(chunk, "choices", None):
                    yield chunk.choices[0].delta.content, chunk.choices[
                        0
                    ].delta.tool_calls
                # When CompletionUsage message exists, generate Token consumption log
                elif isinstance(getattr(chunk, "usage", None), CompletionUsage):
                    usage_info = getattr(chunk, "usage", None)
                    logger.bind(tag=TAG).info(
                        f"Token consumption: input {getattr(usage_info, 'prompt_tokens', 'unknown')}, "
                        f"output {getattr(usage_info, 'completion_tokens', 'unknown')}, "
                        f"total {getattr(usage_info, 'total_tokens', 'unknown')}"
                    )


        except Exception as e:
            logger.bind(tag=TAG).error(f"Error in function call streaming: {e}")
            # Ensure the error message is properly encoded
            error_msg = str(e).encode('utf-8', errors='ignore').decode('utf-8')
            yield f"[OpenAI Service Response Exception: {error_msg}]", None