from __future__ import annotations

import json
from pathlib import Path
from typing import Any

MODEL_COST_PER_1K = {
    "gpt-4o": (0.0025, 0.01),
    "gpt-4o-mini": (0.00015, 0.0006),
    "gpt-4-turbo": (0.01, 0.03),
    "gpt-3.5-turbo": (0.0005, 0.0015),
    "claude-sonnet-4": (0.003, 0.015),
    "claude-3-haiku": (0.00025, 0.00125),
    "llama3": (0.0, 0.0),
    "codellama": (0.0, 0.0),
    "deepseek-coder": (0.0, 0.0),
}


class CostTracker:
    def __init__(self, session_dir: str):
        self._file = Path(session_dir) / "costs.json"
        self._session_calls: list[dict[str, Any]] = []
        self._total_prompt_tokens = 0
        self._total_completion_tokens = 0
        self._total_cost = 0.0
        self._load()

    def _load(self):
        if self._file.exists():
            try:
                data = json.loads(self._file.read_text())
                self._total_prompt_tokens = data.get("prompt_tokens", 0)
                self._total_completion_tokens = data.get("completion_tokens", 0)
                self._total_cost = data.get("cost", 0.0)
                self._session_calls = data.get("calls", [])
            except (json.JSONDecodeError, OSError):
                pass

    def _save(self):
        self._file.parent.mkdir(parents=True, exist_ok=True)
        self._file.write_text(json.dumps({
            "prompt_tokens": self._total_prompt_tokens,
            "completion_tokens": self._total_completion_tokens,
            "cost": self._total_cost,
            "calls": self._session_calls[-500:],
        }, indent=2))

    def record_call(self, model: str, prompt_tokens: int, completion_tokens: int):
        base_model = model.split("/")[-1] if "/" in model else model
        base_model = base_model.rsplit("-", 1)[0] if base_model.count("-") > 1 else base_model
        rates = MODEL_COST_PER_1K.get(base_model, (0.001, 0.002))
        prompt_cost = (prompt_tokens / 1000) * rates[0]
        completion_cost = (completion_tokens / 1000) * rates[1]
        call_cost = prompt_cost + completion_cost

        self._total_prompt_tokens += prompt_tokens
        self._total_completion_tokens += completion_tokens
        self._total_cost += call_cost

        self._session_calls.append({
            "model": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "cost": round(call_cost, 6),
            "running_total": round(self._total_cost, 6),
        })
        self._save()

    def get_summary(self) -> dict[str, Any]:
        return {
            "total_prompt_tokens": self._total_prompt_tokens,
            "total_completion_tokens": self._total_completion_tokens,
            "total_tokens": self._total_prompt_tokens + self._total_completion_tokens,
            "total_cost": round(self._total_cost, 6),
            "total_calls": len(self._session_calls),
        }

    def format_summary(self) -> str:
        s = self.get_summary()
        return (f"Tokens: {s['total_tokens']} (prompt: {s['total_prompt_tokens']}, "
                f"completion: {s['total_completion_tokens']}) | "
                f"Cost: ${s['total_cost']:.4f} | Calls: {s['total_calls']}")

    def reset(self):
        self._session_calls.clear()
        self._total_prompt_tokens = 0
        self._total_completion_tokens = 0
        self._total_cost = 0.0
        if self._file.exists():
            self._file.unlink()
