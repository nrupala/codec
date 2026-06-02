import time
from typing import Any

from openai import AsyncOpenAI

from codec.llm.base import BaseLLMBackend


class OpenAIBackend(BaseLLMBackend):
    def __init__(self, api_key: str, model: str = "gpt-4o",
                 api_base: str = "https://api.openai.com/v1",
                 max_tokens: int = 4096):
        self._model = model
        self._max_tokens = max_tokens
        self._client = AsyncOpenAI(api_key=api_key, base_url=api_base)

    @property
    def name(self) -> str:
        return f"openai/{self._model}"

    @property
    def supports_streaming(self) -> bool:
        return True

    async def generate(self, messages: list[dict[str, str]], **kwargs) -> str:
        result = await self.generate_with_metadata(messages, **kwargs)
        return result["content"]

    async def generate_with_metadata(self, messages: list[dict[str, str]], **kwargs) -> dict[str, Any]:
        start = time.monotonic()
        try:
            response = await self._client.chat.completions.create(
                model=kwargs.get("model", self._model),
                messages=messages,
                max_tokens=kwargs.get("max_tokens", self._max_tokens),
                temperature=kwargs.get("temperature", 0.7),
            )
            latency_ms = int((time.monotonic() - start) * 1000)
            choice = response.choices[0]
            return {
                "content": choice.message.content or "",
                "model": response.model,
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "latency_ms": latency_ms,
            }
        except Exception as e:
            latency_ms = int((time.monotonic() - start) * 1000)
            return {
                "content": f"Error: LLM request failed after {latency_ms}ms: {e}",
                "model": self._model,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "latency_ms": latency_ms,
                "error": str(e),
            }
