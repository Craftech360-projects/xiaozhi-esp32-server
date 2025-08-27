from abc import ABC, abstractmethod
from config.logger import setup_logging


TAG = __name__
logger = setup_logging()


class LLMProviderBase(ABC):
    @abstractmethod
    def response(self, session_id, dialogue):
        """LLM response generator"""
        pass

    def response_no_stream(self, system_prompt, user_prompt, **kwargs):
        try:
            # Add logging to track non-streaming calls (used by memory/intent)
            base_url = getattr(self, 'base_url', 'unknown')
            model_name = getattr(self, 'model_name', 'unknown')
            logger.bind(tag=TAG).info(f"📝 [LLM-NO-STREAM] Using {base_url} with model {model_name}")
            
            # Construct dialogue format
            dialogue = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            result = ""
            for part in self.response("", dialogue, **kwargs):
                result += part
            return result

        except Exception as e:
            logger.bind(tag=TAG).error(
                f"Error in Ollama response generation: {e}")
            return "[LLM Service Response Exception]"

    def response_with_functions(self, session_id, dialogue, functions=None):
        """
        Default implementation for function calling (streaming)
        This should be overridden by providers that support function calls


        Returns: generator that yields either text tokens or a special function call token
        """
        # For providers that don't support functions, just return regular response
        for token in self.response(session_id, dialogue):
            yield token, None
