import json
import os
from pathlib import Path
from datetime import datetime
from enum import Enum
from typing import Any


class TaskState(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class CognitiveState(str, Enum):
    INITIALIZING = "initializing"
    ANALYZING = "analyzing"
    EXECUTING = "executing"
    EVALUATING = "evaluating"
    AWAITING_INPUT = "awaiting_input"
    IDLE = "idle"


class StateManager:
    def __init__(self, session_dir: str):
        self.session_dir = Path(session_dir)
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = self.session_dir / "state.json"
        self.history_file = self.session_dir / "history.jsonl"

        self.cognitive_state = CognitiveState.IDLE
        self.tasks: dict[str, dict[str, Any]] = {}
        self.resources: dict[str, Any] = {
            "llm_calls_remaining": 100,
            "concurrent_tasks": 0,
        }
        self.conversation_history: list[dict[str, str]] = []
        self.active_plan: list[dict[str, Any]] = []
        self.plan_goal: str = ""
        self.metadata: dict[str, Any] = {
            "session_start": datetime.now().isoformat(),
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
        }
        self._load()

    def _load(self):
        if self.state_file.exists():
            try:
                data = json.loads(self.state_file.read_text())
                self.cognitive_state = CognitiveState(data.get("cognitive_state", "idle"))
                self.metadata = data.get("metadata", self.metadata)
                self.resources = data.get("resources", self.resources)
                self.active_plan = data.get("active_plan", [])
                self.plan_goal = data.get("plan_goal", "")
            except (json.JSONDecodeError, KeyError, ValueError):
                pass
        if self.history_file.exists():
            try:
                with open(self.history_file, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            self.conversation_history.append(json.loads(line))
            except json.JSONDecodeError:
                pass

    def _save(self):
        data = {
            "cognitive_state": self.cognitive_state.value,
            "metadata": self.metadata,
            "resources": self.resources,
            "active_plan": self.active_plan,
            "plan_goal": self.plan_goal,
        }
        self.state_file.write_text(json.dumps(data, indent=2))

    def set_cognitive_state(self, state: CognitiveState):
        self.cognitive_state = state
        self._save()

    def add_task(self, task_id: str, description: str, parent_id: str | None = None):
        self.tasks[task_id] = {
            "id": task_id,
            "description": description,
            "state": TaskState.PENDING.value,
            "parent_id": parent_id,
            "created_at": datetime.now().isoformat(),
            "result": None,
        }
        self.metadata["total_tasks"] += 1
        self._save()

    def update_task(self, task_id: str, state: TaskState, result: Any = None):
        if task_id in self.tasks:
            self.tasks[task_id]["state"] = state.value
            if result is not None:
                self.tasks[task_id]["result"] = result
            if state == TaskState.COMPLETED:
                self.metadata["completed_tasks"] += 1
            elif state == TaskState.FAILED:
                self.metadata["failed_tasks"] += 1
            self._save()

    def add_to_history(self, role: str, content: str):
        entry = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        }
        self.conversation_history.append(entry)
        with open(self.history_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def get_summary(self) -> dict[str, Any]:
        pending = sum(1 for t in self.tasks.values() if t["state"] == TaskState.PENDING.value)
        running = sum(1 for t in self.tasks.values() if t["state"] == TaskState.RUNNING.value)
        completed = sum(1 for t in self.tasks.values() if t["state"] == TaskState.COMPLETED.value)
        failed = sum(1 for t in self.tasks.values() if t["state"] == TaskState.FAILED.value)
        return {
            "cognitive_state": self.cognitive_state.value,
            "tasks": {"pending": pending, "running": running, "completed": completed, "failed": failed, "total": len(self.tasks)},
            "resources": self.resources,
            "conversation_length": len(self.conversation_history),
        }

    def clear_history(self):
        self.conversation_history.clear()
        self.tasks.clear()
        self.active_plan = []
        self.plan_goal = ""
        self.metadata = {
            "session_start": datetime.now().isoformat(),
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
        }
        if self.history_file.exists():
            self.history_file.unlink()
        self._save()

    def set_plan(self, steps: list[dict[str, Any]], goal: str):
        self.active_plan = steps
        self.plan_goal = goal
        self._save()

    def update_plan_step(self, step_index: int, status: str, result: Any = None):
        if 0 <= step_index < len(self.active_plan):
            self.active_plan[step_index]["status"] = status
            if result is not None:
                self.active_plan[step_index]["result"] = result
            self._save()

    def get_plan_summary(self) -> str:
        if not self.active_plan:
            return ""
        lines = [f"**Active Plan:** {self.plan_goal}"]
        for i, s in enumerate(self.active_plan):
            status = s.get("status", "pending")
            mark = {"completed": "✓", "failed": "✗", "running": "→", "pending": "·"}.get(status, "·")
            lines.append(f"  {mark} Step {i+1}: {s.get('description', '')}")
        return "\n".join(lines)
