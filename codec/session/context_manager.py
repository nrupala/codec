from __future__ import annotations

from typing import Any


CONTEXT_LIMITS = {
    "default": 128000,
    "gpt-4o": 128000,
    "gpt-4o-mini": 128000,
    "gpt-4-turbo": 128000,
    "claude-sonnet-4": 200000,
    "claude-3-haiku": 200000,
    "llama3": 8192,
    "codellama": 16384,
    "deepseek-coder": 16384,
}

TOKEN_ESTIMATE_PER_CHAR = 0.25
SUMMARY_TRIGGER_RATIO = 0.7


def estimate_tokens(text: str) -> int:
    return int(len(text) * TOKEN_ESTIMATE_PER_CHAR)


class ContextManager:
    def __init__(self, model: str = "gpt-4o"):
        self._model = model
        self._limit = self._get_limit(model)

    def _get_limit(self, model: str) -> int:
        for key in CONTEXT_LIMITS:
            if key in model:
                return CONTEXT_LIMITS[key]
        return CONTEXT_LIMITS["default"]

    def set_model(self, model: str):
        self._model = model
        self._limit = self._get_limit(model)

    def estimate_usage(self, messages: list[dict[str, Any]]) -> int:
        total = 0
        for msg in messages:
            total += estimate_tokens(msg.get("content", ""))
            total += 10
        return total

    def would_exceed_limit(self, messages: list[dict[str, Any]], additional: str = "") -> bool:
        current = self.estimate_usage(messages)
        additional_tokens = estimate_tokens(additional)
        return (current + additional_tokens) > (self._limit * SUMMARY_TRIGGER_RATIO)

    def needs_summarization(self, messages: list[dict[str, Any]]) -> bool:
        current = self.estimate_usage(messages)
        return current > (self._limit * SUMMARY_TRIGGER_RATIO)

    def get_summary_prompt(self, history: list[dict[str, Any]]) -> str:
        oldest_items = history[:-5] if len(history) > 5 else []
        recent_items = history[-5:] if len(history) > 5 else history
        summary = "Summarize the following conversation to preserve key context (decisions made, files discussed, user preferences):\n\n"
        for item in oldest_items:
            content = item.get("content", "")[:200]
            summary += f"[{item['role']}]: {content}\n"
        summary += "\n--- END ---\n\nProvide a concise summary preserving all technical decisions and file paths."
        return summary

    def get_compressed_context(self, history: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if len(history) <= 10:
            return history
        kept = history[-10:]
        compressed = history[:-10]
        total_tokens_removed = sum(
            estimate_tokens(m.get("content", "")) for m in compressed
        )
        kept.insert(0, {
            "role": "system",
            "content": f"[Earlier conversation compressed. Removed approximately {total_tokens_removed} tokens of early context. Key decisions preserved above.]"
        })
        return kept

    def format_limit_info(self) -> str:
        return f"Context window: {self._limit:,} tokens (model: {self._model})"
