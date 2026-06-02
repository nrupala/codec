from typing import Any, Literal

ActionType = Literal[
    "read_file", "write_file", "edit_file", "run_shell",
    "search_code", "glob_files", "web_fetch", "ask_user",
    "llm_generate", "decompose", "noop",
]


class ActionDefiner:
    def define(self, task: dict[str, Any]) -> dict[str, Any]:
        task_type = task.get("type", "general")
        desc = task.get("description", "")

        type_to_action: dict[str, ActionType] = {
            "read": "read_file",
            "write": "write_file",
            "edit": "edit_file",
            "shell": "run_shell",
            "search": "search_code",
            "list": "glob_files",
        }

        action_type = type_to_action.get(task_type, "llm_generate")

        return {
            "action_id": f"act_{task['id']}",
            "type": action_type,
            "params": {"input": desc},
            "task_id": task["id"],
            "dependencies": task.get("dependencies", []),
        }
