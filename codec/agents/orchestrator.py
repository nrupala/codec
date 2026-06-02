import time
from typing import Any

from codec.agents.base import BaseAgent
from codec.modules.prompt_engineer import PromptEngineer
from codec.modules.state_manager import StateManager, CognitiveState
from codec.modules.logger import ModuleLogger
from codec.tools.registry import registry
from codec.session.guardian import SessionGuardian
from codec.session.memory import SessionMemory
from codec.session.cost_tracker import CostTracker
from codec.session.context_manager import ContextManager


MAX_AGENTIC_ITERATIONS = 15
VERIFICATION_TOOLS = {"write_file", "edit_file", "edit_file_with_diff", "run_shell"}


class OrchestratorAgent(BaseAgent):
    def __init__(self, state_manager: StateManager, logger: ModuleLogger,
                 llm_backend=None, project_dir: str = ".",
                 guardian: SessionGuardian | None = None,
                 memory: SessionMemory | None = None,
                 cost_tracker: CostTracker | None = None,
                 context_manager: ContextManager | None = None):
        super().__init__("orchestrator")
        self.state = state_manager
        self.log = logger
        self.llm = llm_backend
        self.project_dir = project_dir
        self.guardian = guardian or SessionGuardian(project_dir)
        self.memory = memory
        self.cost_tracker = cost_tracker
        self.context_manager = context_manager
        self.prompt_engineer = PromptEngineer()
        self._verification_needed = False

    async def execute(self, task: dict, context: dict) -> dict:
        return {"content": await self.process_input(task.get("description", "")), "status": "completed"}

    async def process_input(self, user_input: str) -> str:
        self.state.set_cognitive_state(CognitiveState.ANALYZING)
        self.state.add_to_history("user", user_input)
        self.log.info(f"User input: {user_input[:100]}")

        if self.memory:
            self.memory.record_episode("user", user_input)

        intent = self.prompt_engineer.detect_intent(user_input)

        if intent in ("read", "list", "search", "shell") and self.llm is None:
            result = await self._execute_direct_tool(user_input, intent)
            content = result.get("content", "")
            self.state.add_to_history("assistant", content)
            self.state.set_cognitive_state(CognitiveState.IDLE)
            return content

        result = await self._run_agentic_loop(user_input)
        self.state.set_cognitive_state(CognitiveState.IDLE)
        return result

    async def _run_agentic_loop(self, user_input: str) -> str:
        if not self.llm:
            return "LLM not configured. Set CODECK_API_KEY or use CODECK_MODEL=ollama/..."

        final_text = ""
        tool_results: list[dict[str, Any]] = []
        wrote_files = False

        for iteration in range(MAX_AGENTIC_ITERATIONS):
            plan_context = self.state.get_plan_summary()
            current_messages = self.prompt_engineer.build_agentic_messages(
                user_input, self.state.conversation_history[:-1],
                tool_results=tool_results if tool_results else None,
                task_context={"plan": plan_context} if plan_context else None,
            )

            if self.context_manager and self.context_manager.needs_summarization(current_messages):
                self.log.info("Context window nearing limit, compressing history")
                self.state.conversation_history = self.context_manager.get_compressed_context(
                    self.state.conversation_history
                )
                current_messages = self.prompt_engineer.build_agentic_messages(
                    user_input, self.state.conversation_history[:-1],
                    tool_results=tool_results if tool_results else None,
                    task_context={"plan": plan_context} if plan_context else None,
                )

            start = time.monotonic()
            result = await self.llm.generate_with_metadata(current_messages)
            latency = int((time.monotonic() - start) * 1000)
            response_text = result.get("content", "")
            model_used = result.get("model", "unknown")
            pt = result.get("prompt_tokens", 0)
            ct = result.get("completion_tokens", 0)
            self.log.log_llm_call(model_used, pt, ct, latency, tag=f"iter_{iteration}")
            if self.cost_tracker:
                self.cost_tracker.record_call(model_used, pt, ct)

            tool_calls = self.prompt_engineer.extract_tool_calls(response_text)

            if not tool_calls:
                final_text = self.prompt_engineer.strip_tool_calls(response_text)
                if self._verification_needed and wrote_files:
                    final_text += (
                        "\n\n_Verification: Run `run_tests` to verify changes, "
                        "or continue with next steps._"
                    )
                self.state.add_to_history("assistant", final_text)
                if self.memory:
                    self.memory.record_episode("assistant", final_text[:500])
                self._verification_needed = False
                return final_text

            tool_results = []
            for tc in tool_calls:
                tool_name = tc.get("name", "")
                args = tc.get("arguments", {}) or {}
                args.pop("project_dir", None)

                if tool_name in ("read_file", "edit_file", "write_file", "list_files",
                                 "grep_search", "glob_files"):
                    for key in ("path", "project_dir"):
                        if key in args:
                            args[key] = self.guardian.contain_path(args[key])

                if tool_name == "run_shell":
                    cmd = args.get("command", "")
                    blocked = self.guardian.allow_command(cmd)
                    if blocked:
                        tool_results.append({
                            "name": tool_name,
                            "result": f"Error: {blocked}",
                            "error": "blocked",
                        })
                        self.log.warn(f"Blocked shell: {cmd}")
                        continue

                args["project_dir"] = self.project_dir
                t_start = time.monotonic()

                if tool_name in VERIFICATION_TOOLS and tool_name != "run_shell":
                    wrote_files = True

                try:
                    output = await registry.call(tool_name, **args)
                    t_latency = int((time.monotonic() - t_start) * 1000)
                    self.log.log_tool_call(tool_name, args, len(output), t_latency)
                    tool_results.append({"name": tool_name, "result": output})
                except ValueError:
                    self.log.error(f"Unknown tool: {tool_name}")
                    available = ", ".join(registry.list_tools().keys())
                    tool_results.append({
                        "name": tool_name,
                        "result": f"Error: unknown tool '{tool_name}'. Available: {available}",
                        "error": "unknown_tool",
                    })
                except Exception as e:
                    self.log.error(f"Tool {tool_name} failed: {e}")
                    tool_results.append({
                        "name": tool_name, "result": f"Error: {e}", "error": str(e),
                    })

        final_text = f"Max iterations ({MAX_AGENTIC_ITERATIONS}) reached."
        if wrote_files:
            final_text += (
                "\n\n_Verification: Run `run_tests` to verify changes made so far._"
            )
        self.state.add_to_history("assistant", final_text)
        return final_text

    async def _execute_direct_tool(self, user_input: str, intent: str) -> dict[str, Any]:
        tool_map = {
            "read": ("read_file", {"path": self._extract_path(user_input)}),
            "list": ("list_files", {"pattern": self._extract_pattern(user_input)}),
            "search": ("grep_search", {"pattern": self._extract_pattern(user_input)}),
            "shell": ("run_shell", {"command": self._extract_command(user_input)}),
        }
        info = tool_map.get(intent)
        if not info:
            return {"content": f"No tool for intent: {intent}"}
        name, params = info
        params["project_dir"] = self.project_dir

        if name == "run_shell":
            cmd = params.get("command", "")
            blocked = self.guardian.allow_command(cmd)
            if blocked:
                return {"content": f"Blocked: {blocked}"}

        start = time.monotonic()
        try:
            output = await registry.call(name, **params)
            lat = int((time.monotonic() - start) * 1000)
            self.log.log_tool_call(name, params, len(output), lat)
            return {"content": output, "status": "completed"}
        except Exception as e:
            self.log.error(f"Tool {name} failed: {e}")
            return {"content": str(e), "status": "failed"}

    def _extract_path(self, text: str) -> str:
        import re
        m = re.search(r'(?:read|show|display|open|view|cat|list|ls)\s+(\S+)', text, re.IGNORECASE)
        return m.group(1).strip("'\"`") if m and ('.' in m.group(1) or '/' in m.group(1)) else "."

    def _extract_pattern(self, text: str) -> str:
        for q in ["'", '"']:
            parts = text.split(q)
            if len(parts) >= 3:
                return parts[1]
        words = text.split()
        for w in reversed(words):
            w = w.strip("'\".,;")
            if len(w) > 2 and w not in ("the", "and", "for", "all", "matching"):
                return w
        return "*"

    def _extract_command(self, text: str) -> str:
        import re
        m = re.search(r'(?:run|execute)\s+(.*)', text, re.IGNORECASE)
        if m:
            return m.group(1).strip()
        for p in ["run ", "execute "]:
            if text.lower().startswith(p):
                return text[len(p):].strip()
        return text.strip()
