import json
import re
from typing import Any

from codec.tools.registry import registry

AGENTIC_SYSTEM_PROMPT_TMPL = """You are CodeC, an AI coding assistant that helps with software engineering tasks.

You have access to tools you can call to accomplish tasks. To use a tool, respond with:

<tool_call>
{{"name": "tool_name", "arguments": {{"param1": "value1"}}}}
</tool_call>

After you receive the tool result, you can either call another tool or provide your final response.

AVAILABLE TOOLS:
{tool_descriptions}

ACTIVE PLAN (if any):
{plan_context}

RULES:
1. For complex multi-step tasks, first call `create_plan` to lay out your steps before executing.
2. Break complex tasks into steps. Call tools one at a time.
3. Read files before editing them to understand the current content.
4. Show the user what you find and what you plan to do.
5. For shell commands, explain what the command does before running it.
6. After writing or editing files, consider running `run_tests` to verify your changes work.
7. Use `web_search` to look up documentation, solutions, or APIs you're unsure about.
8. When done, summarize what was accomplished and the plan status.
9. All file paths are relative to the project directory.
10. Use markdown formatting in your text responses."""


class PromptEngineer:
    def __init__(self):
        self.system_prompt = self._build_system_prompt()
        self._tool_call_re = re.compile(
            r'<tool_call>\s*(\{.*?\})\s*</tool_call>', re.DOTALL
        )

    def _build_system_prompt(self) -> str:
        tools = registry.list_tools()
        desc_lines = []
        for name, desc in sorted(tools.items()):
            sig = self._get_tool_signature(name)
            desc_lines.append(f"- {sig}\n  {desc}")
        return AGENTIC_SYSTEM_PROMPT_TMPL.format(
            tool_descriptions="\n".join(desc_lines),
            plan_context="(no active plan)",
        )

    def _get_tool_signature(self, name: str) -> str:
        sigs = {
            "read_file": "read_file(path: str) -> str",
            "write_file": "write_file(path: str, content: str) -> str",
            "edit_file": "edit_file(path: str, old_string: str, new_string: str) -> str",
            "list_files": "list_files(pattern: str = \"*\") -> str",
            "run_shell": "run_shell(command: str, timeout: int = 60) -> str",
            "grep_search": "grep_search(pattern: str, include: str = \"*\") -> str",
            "glob_files": "glob_files(pattern: str) -> str",
            "web_fetch": "web_fetch(url: str, timeout: int = 30) -> str",
            "web_search": "web_search(query: str, num_results: int = 5) -> str",
            "create_plan": "create_plan(goal: str, steps: list[str]) -> str",
            "update_plan_step": "update_plan_step(step_index: int, status: str, result: str = \"\") -> str",
            "get_plan": "get_plan() -> str",
            "run_tests": "run_tests(command: str = \"\") -> str",
            "detect_test_command": "detect_test_command() -> str",
        }
        return sigs.get(name, f"{name}(...)")

    def build_agentic_messages(self, user_input: str,
                               history: list[dict[str, str]],
                               tool_results: list[dict[str, Any]] | None = None,
                               task_context: dict[str, Any] | None = None) -> list[dict[str, str]]:
        plan_context = ""
        if task_context and task_context.get("plan"):
            plan_context = task_context["plan"]

        system = self.system_prompt
        if plan_context:
            system = AGENTIC_SYSTEM_PROMPT_TMPL.format(
                tool_descriptions="\n".join(
                    f"- {self._get_tool_signature(n)}\n  {d}"
                    for n, d in sorted(registry.list_tools().items())
                ),
                plan_context=plan_context,
            )

        messages = [{"role": "system", "content": system}]

        recent = history[-30:] if len(history) > 30 else history
        for entry in recent:
            messages.append({"role": entry["role"], "content": entry["content"]})

        if tool_results:
            for tr in tool_results:
                content = f"Tool `{tr['name']}` returned:\n```\n{tr['result'][:2000]}```"
                if tr.get("error"):
                    content = f"Tool `{tr['name']}` error:\n```\n{tr['error']}```"
                messages.append({"role": "user", "content": content})
            return messages

        messages.append({"role": "user", "content": user_input})
        return messages

    def extract_tool_calls(self, text: str) -> list[dict[str, Any]]:
        calls = []
        for match in self._tool_call_re.finditer(text):
            try:
                data = json.loads(match.group(1))
                if isinstance(data, dict) and "name" in data:
                    calls.append(data)
            except json.JSONDecodeError:
                continue
        return calls

    def strip_tool_calls(self, text: str) -> str:
        return self._tool_call_re.sub("", text).strip()

    def detect_intent(self, user_input: str) -> str:
        input_lower = user_input.lower().strip()
        read_p = [r"^(read|show|display|cat|open|view|dump)\s"]
        list_p = [r"^(list|ls|dir)\s"]
        write_p = [r"^(write|create|make|generate)\s", r"^(add|insert|append)\s",
                   r"^create a (new )?(file|class|function|method|test)"]
        edit_p = [r"^(edit|update|change|modify|fix|refactor|replace)\s",
                  r"^(rename|move|delete|remove)\s"]
        search_p = [r"^(search|find|grep|look for|locate)\s",
                    r"^(where|how).*(defined|used|implemented)"]
        shell_p = [r"^(run|execute|bash|sh|npm|pip|git|docker|make|npx|yarn)\s"]
        question_p = [r"^(what|how|why|when|where|who|which|explain|describe|tell me|show me)\b"]

        for name, patterns in [
            ("read", read_p), ("list", list_p), ("write", write_p),
            ("edit", edit_p), ("search", search_p), ("shell", shell_p),
            ("question", question_p),
        ]:
            if any(re.match(p, input_lower) for p in patterns):
                return name
        if any(cmd in input_lower for cmd in ["/help", "/exit", "/clear", "/status", "/log"]):
            return "meta"
        return "general"
