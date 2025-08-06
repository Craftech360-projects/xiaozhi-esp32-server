import httpx
import openai
from openai.types import CompletionUsage
from config.logger import setup_logging
from core.utils.util import check_model_key
from core.providers.llm.base import LLMProviderBase

TAG = __name__
logger = setup_logging()


class LLMProvider(LLMProviderBase):
    """
    Groq API Provider for Llama models
    Groq provides fast inference for open-source models like Llama
    """
    def __init__(self, config):
        self.model_name = config.get("model_name", "llama-3.3-70b-versatile")  # Default to Llama 3.3 70B
        self.api_key = config.get("api_key")
        self.base_url = config.get("base_url", "https://api.groq.com/openai/v1")
        
        # Groq has a default timeout of 60s, but we'll allow configuration
        timeout = config.get("timeout", 60)
        self.timeout = int(timeout) if timeout else 60

        # Model parameters with Groq-appropriate defaults
        param_defaults = {
            "max_tokens": (2048, int),  # Groq supports up to 8192 for some models
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
            f"Groq LLM initialized with model: {self.model_name}, "
            f"params: temperature={self.temperature}, max_tokens={self.max_tokens}, "
            f"top_p={self.top_p}, frequency_penalty={self.frequency_penalty}"
        )

        model_key_msg = check_model_key("Groq LLM", self.api_key)
        if model_key_msg:
            logger.bind(tag=TAG).error(model_key_msg)
            
        # Initialize OpenAI client with Groq endpoint
        self.client = openai.OpenAI(
            api_key=self.api_key, 
            base_url=self.base_url, 
            timeout=httpx.Timeout(self.timeout)
        )

    def response(self, session_id, dialogue, **kwargs):
        """
        Generate streaming response from Groq API
        """
        try:
            responses = self.client.chat.completions.create(
                model=self.model_name,
                messages=dialogue,
                stream=True,
                max_tokens=kwargs.get("max_tokens", self.max_tokens),
                temperature=kwargs.get("temperature", self.temperature),
                top_p=kwargs.get("top_p", self.top_p),
                frequency_penalty=kwargs.get("frequency_penalty", self.frequency_penalty),
            )

            is_active = True
            for chunk in responses:
                try:
                    delta = (
                        chunk.choices[0].delta
                        if getattr(chunk, "choices", None)
                        else None
                    )
                    content = delta.content if hasattr(delta, "content") else ""
                except IndexError:
                    content = ""
                    
                if content:
                    # Handle think tags for internal reasoning
                    if "<think>" in content:
                        is_active = False
                        content = content.split("<think>")[0]
                    if "</think>" in content:
                        is_active = True
                        content = content.split("</think>")[-1]
                    if is_active:
                        yield content

        except Exception as e:
            logger.bind(tag=TAG).error(f"Error in Groq response generation: {e}")
            yield f"【Groq服务响应异常: {str(e)}】"

    def response_with_functions(self, session_id, dialogue, functions=None):
        """
        Groq supports function calling through OpenAI-compatible API
        """
        try:
            stream = self.client.chat.completions.create(
                model=self.model_name, 
                messages=dialogue, 
                stream=True, 
                tools=functions
            )

            for chunk in stream:
                if getattr(chunk, "choices", None):
                    yield chunk.choices[0].delta.content, chunk.choices[0].delta.tool_calls
                # Log token usage if available
                elif isinstance(getattr(chunk, "usage", None), CompletionUsage):
                    usage_info = getattr(chunk, "usage", None)
                    logger.bind(tag=TAG).info(
                        f"Groq Token Usage - Input: {getattr(usage_info, 'prompt_tokens', 'unknown')}, "
                        f"Output: {getattr(usage_info, 'completion_tokens', 'unknown')}, "
                        f"Total: {getattr(usage_info, 'total_tokens', 'unknown')}"
                    )

        except Exception as e:
            logger.bind(tag=TAG).error(f"Error in Groq function call streaming: {e}")
            yield f"【Groq服务函数调用异常: {str(e)}】", None