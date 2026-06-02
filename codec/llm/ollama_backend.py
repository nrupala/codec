import time
import json
from typing import Any
import httpx

from codec.llm.base import BaseLLMBackend


class OllamaBackend(BaseLLMBackend):
    def __init__(self, model: str = "llama3", api_base: str = "http://localhost:11434",
                 max_tokens: int = 4096):
        self._model = model.replace("ollama/", "", 1)
        self._api_base = api_base.rstrip("/")
        self._max_tokens = max_tokens

    @property
    def name(self) -> str:
        return f"ollama/{self._model}"

    @property
    def supports_streaming(self) -> bool:
        return True

    async def generate(self, messages: list[dict[str, str]], **kwargs) -> str:
        r = await self.generate_with_metadata(messages, **kwargs)
        return r["content"]

    async def generate_with_metadata(self, messages: list[dict[str, str]], **kwargs) -> dict[str, Any]:
        start = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(f"{self._api_base}/api/chat", json={
                    "model": kwargs.get("model", self._model),
                    "messages": messages,
                    "options": {
                        "num_predict": kwargs.get("max_tokens", self._max_tokens),
                        "temperature": kwargs.get("temperature", 0.7),
                    },
                    "stream": False,
                })
                resp.raise_for_status()
                data = resp.json()
                latency_ms = int((time.monotonic() - start) * 1000)
                return {
                    "content": data.get("message", {}).get("content", ""),
                    "model": data.get("model", self._model),
                    "prompt_tokens": data.get("prompt_eval_count", 0),
                    "completion_tokens": data.get("eval_count", 0),
                    "latency_ms": latency_ms,
                }
        except httpx.ConnectError:
            latency_ms = int((time.monotonic() - start) * 1000)
            return {
                "content": f"Error: Cannot connect to Ollama at {self._api_base}. Is it running?",
                "model": self._model,
                "prompt_tokens": 0, "completion_tokens": 0,
                "latency_ms": latency_ms, "error": "connection_refused",
            }
        except Exception as e:
            latency_ms = int((time.monotonic() - start) * 1000)
            return {
                "content": f"Error: Ollama request failed: {e}",
                "model": self._model,
                "prompt_tokens": 0, "completion_tokens": 0,
                "latency_ms": latency_ms, "error": str(e),
            }
