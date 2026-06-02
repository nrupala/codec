import time
from typing import Any

from codec.llm.base import BaseLLMBackend


class AnthropicBackend(BaseLLMBackend):
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514",
                 api_base: str = "https://api.anthropic.com/v1",
                 max_tokens: int = 4096):
        self._model = model.replace("anthropic/", "", 1)
        self._api_key = api_key
        self._api_base = api_base.rstrip("/")
        self._max_tokens = max_tokens

    @property
    def name(self) -> str:
        return f"anthropic/{self._model}"

    @property
    def supports_streaming(self) -> bool:
        return True

    async def generate(self, messages: list[dict[str, str]], **kwargs) -> str:
        r = await self.generate_with_metadata(messages, **kwargs)
        return r["content"]

    async def generate_with_metadata(self, messages: list[dict[str, str]], **kwargs) -> dict[str, Any]:
        import httpx
        start = time.monotonic()
        try:
            system_msg = ""
            chat_messages = []
            for m in messages:
                if m["role"] == "system":
                    system_msg = m["content"]
                else:
                    chat_messages.append({"role": m["role"], "content": m["content"]})

            body = {
                "model": kwargs.get("model", self._model),
                "max_tokens": kwargs.get("max_tokens", self._max_tokens),
                "messages": chat_messages,
            }
            if system_msg:
                body["system"] = system_msg

            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(
                    f"{self._api_base}/messages",
                    headers={
                        "x-api-key": self._api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json=body,
                )
                resp.raise_for_status()
                data = resp.json()
                latency_ms = int((time.monotonic() - start) * 1000)
                content = ""
                for block in data.get("content", []):
                    if block.get("type") == "text":
                        content += block.get("text", "")
                return {
                    "content": content,
                    "model": data.get("model", self._model),
                    "prompt_tokens": data.get("usage", {}).get("input_tokens", 0),
                    "completion_tokens": data.get("usage", {}).get("output_tokens", 0),
                    "latency_ms": latency_ms,
                }
        except Exception as e:
            latency_ms = int((time.monotonic() - start) * 1000)
            return {
                "content": f"Error: Anthropic request failed: {e}",
                "model": self._model,
                "prompt_tokens": 0, "completion_tokens": 0,
                "latency_ms": latency_ms, "error": str(e),
            }
