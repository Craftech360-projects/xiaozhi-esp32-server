"""
Ollama LLM Provider for LiveKit
Provides a local LLM implementation using Ollama
"""
import aiohttp
import json
import logging
from typing import AsyncIterator, Optional
from livekit.agents import llm

logger = logging.getLogger(__name__)


class OllamaLLM(llm.LLM):
    """Ollama LLM implementation for local AI inference"""

    def __init__(
        self,
        *,
        base_url: str = "http://localhost:11434",
        model: str = "llama3.1:8b",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ):
        """
        Initialize Ollama LLM provider

        Args:
            base_url: Ollama server URL
            model: Model name (e.g., 'llama3.1:8b', 'llama2:7b', 'mistral:7b')
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
        """
        super().__init__()
        self._base_url = base_url.rstrip('/')
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens

        logger.info(
            f"Initialized Ollama LLM with model={model}, "
            f"base_url={base_url}"
        )

    async def chat(
        self,
        *,
        chat_ctx: llm.ChatContext,
        conn_options: Optional[any] = None,  # noqa: ARG002
    ) -> "llm.LLMStream":
        """
        Generate chat completion stream

        Args:
            chat_ctx: Chat context with messages
            conn_options: Connection options (not used for Ollama)

        Returns:
            LLMStream for streaming responses
        """
        # Convert chat context to Ollama format
        messages = self._build_messages(chat_ctx)

        # Build request payload
        payload = {
            "model": self._model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": self._temperature,
                "num_predict": self._max_tokens,
            }
        }

        return OllamaLLMStream(
            base_url=self._base_url,
            payload=payload,
        )

    def _build_messages(self, chat_ctx: llm.ChatContext) -> list:
        """Convert ChatContext to Ollama message format"""
        messages = []

        for msg in chat_ctx.messages:
            role = msg.role

            # Map roles to Ollama format
            if role == "system":
                messages.append({
                    "role": "system",
                    "content": msg.content
                })
            elif role == "user":
                messages.append({
                    "role": "user",
                    "content": msg.content
                })
            elif role == "assistant":
                messages.append({
                    "role": "assistant",
                    "content": msg.content
                })
            elif role == "tool":
                # Ollama may handle tool results differently
                messages.append({
                    "role": "assistant",
                    "content": f"[Tool Result]: {msg.content}"
                })

        return messages


class OllamaLLMStream(llm.LLMStream):
    """Ollama streaming response handler"""

    def __init__(
        self,
        *,
        base_url: str,
        payload: dict,
    ):
        super().__init__()
        self._base_url = base_url
        self._payload = payload
        self._session: Optional[aiohttp.ClientSession] = None
        self._response: Optional[aiohttp.ClientResponse] = None

    async def __anext__(self) -> llm.ChatChunk:
        """Stream next chunk from Ollama"""
        if self._session is None:
            self._session = aiohttp.ClientSession()
            url = f"{self._base_url}/api/chat"

            try:
                self._response = await self._session.post(
                    url,
                    json=self._payload,
                    timeout=aiohttp.ClientTimeout(total=300)  # 5 min timeout
                )
                self._response.raise_for_status()
            except Exception as e:
                logger.error(f"Ollama API error: {e}")
                await self._close()
                raise StopAsyncIteration

        if self._response is None:
            raise StopAsyncIteration

        try:
            # Read line from response stream
            line = await self._response.content.readline()

            if not line:
                await self._close()
                raise StopAsyncIteration

            # Parse JSON response
            data = json.loads(line.decode('utf-8'))

            # Check if stream is done
            if data.get("done", False):
                await self._close()
                raise StopAsyncIteration

            # Extract message content
            message = data.get("message", {})
            content = message.get("content", "")

            # Check for tool calls
            tool_calls = message.get("tool_calls", [])

            # Create chat chunk
            chunk = llm.ChatChunk(
                choices=[
                    llm.Choice(
                        delta=llm.ChoiceDelta(
                            role="assistant",
                            content=content,
                            tool_calls=self._parse_tool_calls(tool_calls) if tool_calls else None,
                        ),
                        index=0,
                    )
                ]
            )

            return chunk

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Ollama response: {e}")
            await self._close()
            raise StopAsyncIteration
        except Exception as e:
            logger.error(f"Error streaming from Ollama: {e}")
            await self._close()
            raise StopAsyncIteration

    def _parse_tool_calls(self, tool_calls: list) -> list:
        """Parse tool calls from Ollama response"""
        parsed_calls = []

        for call in tool_calls:
            parsed_calls.append({
                "id": call.get("id", ""),
                "type": "function",
                "function": {
                    "name": call.get("function", {}).get("name", ""),
                    "arguments": call.get("function", {}).get("arguments", "{}"),
                }
            })

        return parsed_calls

    async def _close(self):
        """Close HTTP session"""
        if self._response:
            self._response.close()
            self._response = None

        if self._session:
            await self._session.close()
            self._session = None

    async def aclose(self):
        """Async close method"""
        await self._close()
