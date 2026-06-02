import re
from typing import Any


class TaskDecomposer:
    def decompose(self, user_input: str) -> list[dict[str, Any]]:
        input_lower = user_input.lower().strip()
        tasks = []

        multi_part = self._split_commands(user_input)
        if len(multi_part) > 1:
            for i, part in enumerate(multi_part):
                part = part.strip()
                if part:
                    tasks.append(self._single_task(part, sequence=i))
            return tasks

        tasks.append(self._single_task(user_input, sequence=0))
        return tasks

    def _split_commands(self, user_input: str) -> list[str]:
        separators = [
            r"\band\b(?=\s)",
            r"\bthen\b",
            r"\bafter that\b",
            r"\bnext\b",
            r"\balso\b",
            r"\bplus\b",
            r"\bfollowed by\b",
        ]
        parts = [user_input]
        for sep in separators:
            new_parts = []
            for p in parts:
                split = re.split(sep, p, flags=re.IGNORECASE)
                new_parts.extend(split)
            parts = new_parts
        return [p.strip() for p in parts if p.strip()]

    def _single_task(self, description: str, sequence: int = 0) -> dict[str, Any]:
        task_type = self._classify(description)
        return {
            "id": f"task_{sequence}",
            "description": description,
            "type": task_type,
            "sequence": sequence,
            "dependencies": [] if sequence == 0 else [f"task_{i}" for i in range(sequence)],
        }

    def _classify(self, description: str) -> str:
        d = description.lower()
        if any(w in d for w in ["read", "show", "display", "view", "list", "cat"]):
            return "read"
        if any(w in d for w in ["write", "create", "generate", "make", "add"]):
            return "write"
        if any(w in d for w in ["edit", "update", "change", "modify", "fix", "refactor", "rename"]):
            return "edit"
        if any(w in d for w in ["search", "find", "grep", "locate"]):
            return "search"
        if any(w in d for w in ["run", "execute", "install", "build", "test"]):
            return "shell"
        return "general"
