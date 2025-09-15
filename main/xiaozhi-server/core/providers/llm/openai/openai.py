import httpx
import openai
from openai.types import CompletionUsage
from config.logger import setup_logging
from core.utils.util import check_model_key
from core.providers.llm.base import LLMProviderBase
from core.providers.llm.langfuse_wrapper import langfuse_tracker


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
        self.client = openai.OpenAI(api_key=self.api_key, base_url=self.base_url, timeout=httpx.Timeout(self.timeout))


    @langfuse_tracker.track_llm_call("openai")
    def response(self, session_id, dialogue, **kwargs):
        logger.bind(tag=TAG).info(f"OpenAI LLM response call: session={session_id}, model={self.model_name}")
        
        try:
            logger.bind(tag=TAG).info(f"Making API call to model: {self.model_name}, messages: {len(dialogue)} messages")
            logger.bind(tag=TAG).debug(f"Last message: {dialogue[-1] if dialogue else 'None'}")

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

            logger.bind(tag=TAG).info(f"API call successful, starting to process stream")


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


        except Exception as e:
            logger.bind(tag=TAG).error(f"Error in response generation: {str(e)[:200]}")
            logger.bind(tag=TAG).error(f"Exception type: {type(e).__name__}")
            # Log more details for debugging
            import traceback
            logger.bind(tag=TAG).error(f"Full traceback: {traceback.format_exc()[:500]}")
            # Send user-friendly message instead of technical error details
            yield "Server is busy! Will get back soon."


    @langfuse_tracker.track_function_call("openai")
    def response_with_functions(self, session_id, dialogue, functions=None):
        logger.bind(tag=TAG).info(f"OpenAI function call: session={session_id}, model={self.model_name}, functions={len(functions) if functions else 0}")

        try:
            logger.bind(tag=TAG).info(f"Making function call API to model: {self.model_name}, messages: {len(dialogue)} messages")
            logger.bind(tag=TAG).debug(f"Functions provided: {functions}")
            logger.bind(tag=TAG).debug(f"Last message: {dialogue[-1] if dialogue else 'None'}")

            stream = self.client.chat.completions.create(
                model=self.model_name, messages=dialogue, stream=True, tools=functions
            )

            logger.bind(tag=TAG).info(f"Function call API successful, starting to process stream")


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
            logger.bind(tag=TAG).error(f"Error in function call streaming: {str(e)[:200]}")
            logger.bind(tag=TAG).error(f"Exception type: {type(e).__name__}")
            # Log more details for debugging
            import traceback
            logger.bind(tag=TAG).error(f"Function call traceback: {traceback.format_exc()[:500]}")
            # Send user-friendly message instead of technical error details
            yield "Server is busy! Will get back soon.", None