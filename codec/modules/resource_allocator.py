from typing import Literal

ExecutionStrategy = Literal["llm", "tool", "hybrid", "defer"]


class ResourceAllocator:
    def __init__(self):
        self.llm_credits = 1000
        self.concurrent_limit = 3

    def allocate(self, intent: str, task_complexity: float = 0.5) -> ExecutionStrategy:
        if intent == "meta":
            return "tool"
        if intent in ("read", "search", "list"):
            return "tool"
        if intent == "shell":
            return "tool"
        if intent in ("write", "edit", "refactor"):
            if task_complexity > 0.7:
                return "hybrid"
            return "llm"
        if intent == "question":
            return "llm"
        if intent == "general":
            if task_complexity > 0.6:
                return "hybrid"
            return "llm"
        return "llm"

    def estimate_complexity(self, user_input: str) -> float:
        length = len(user_input)
        word_count = len(user_input.split())
        has_multiple_requests = sum(1 for c in ["and", "then", "also", "plus"] if f" {c} " in f" {user_input.lower()} ")
        complexity = min(1.0, (length / 500) * 0.3 + (word_count / 50) * 0.3 + has_multiple_requests * 0.2 + 0.2)
        return complexity

    def use_credits(self, amount: int = 1) -> bool:
        if self.llm_credits >= amount:
            self.llm_credits -= amount
            return True
        return False

    def reset_credits(self):
        self.llm_credits = 1000
