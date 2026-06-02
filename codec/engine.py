from codec.modules.state_manager import StateManager, CognitiveState
from codec.modules.logger import ModuleLogger
from codec.modules.prompt_engineer import PromptEngineer
from codec.agents.orchestrator import OrchestratorAgent
from codec.llm.openai_backend import OpenAIBackend
from codec.llm.ollama_backend import OllamaBackend
from codec.llm.anthropic_backend import AnthropicBackend
from codec.session.guardian import SessionGuardian
from codec.session.memory import SessionMemory
from codec.session.cost_tracker import CostTracker
from codec.session.context_manager import ContextManager
from codec.session.diff_engine import DiffEngine
from codec.bridge.os_interface import OSInterface
from codec.bridge.code_interface import CodeInterface
from codec.config import Config
from codec.hardware.abstraction import hal
from codec.tools import plan_tools


class CodeCEngine:
    def __init__(self, config: Config | None = None):
        self.config = config or Config()
        self.session_dir = self.config.session_dir
        self.project_dir = self.config.resolved_project_dir

        self.logger = ModuleLogger(self.session_dir)
        self.state_manager = StateManager(self.session_dir)
        self.prompt_engineer = PromptEngineer()

        self.guardian = SessionGuardian(self.project_dir, self.logger)
        plan_tools.set_state_manager(self.state_manager)
        self.memory = SessionMemory(self.session_dir)
        self.cost_tracker = CostTracker(self.session_dir)
        self.context_manager = ContextManager(self.config.model)
        self.diff_engine = DiffEngine(self.project_dir)
        self.os_interface = OSInterface(self.project_dir)
        self.code_interface = CodeInterface(self.project_dir)

        self.llm_backend = self._init_llm_backend()

        self.orchestrator = OrchestratorAgent(
            state_manager=self.state_manager,
            logger=self.logger,
            llm_backend=self.llm_backend,
            project_dir=self.project_dir,
            guardian=self.guardian,
            memory=self.memory,
            cost_tracker=self.cost_tracker,
            context_manager=self.context_manager,
        )

        caps = hal.detect_capabilities()
        self.logger.info(f"Hardware: platform={caps.platform} gpu={caps.has_gpu} "
                         f"neural_engine={caps.has_neural_engine}")
        if self.llm_backend:
            self.logger.info(f"LLM backend: {self.llm_backend.name}")

        if self.llm_backend:
            self.logger.info(f"Context: {self.context_manager.format_limit_info()}")

        project_type = self.os_interface.detect_project_type()
        self.logger.info(f"Project type: {project_type.get('type', 'unknown')}")
        self.memory.remember("project_type", project_type.get("type", "unknown"))

    def _init_llm_backend(self):
        model = self.config.model
        if model.startswith("ollama/"):
            return OllamaBackend(
                model=model,
                api_base=self.config.api_base,
                max_tokens=self.config.max_tokens,
            )
        if model.startswith("anthropic/"):
            key = self.config.api_key
            if not key:
                self.logger.warn("ANTHROPIC_API_KEY not set")
                return None
            return AnthropicBackend(
                api_key=key,
                model=model,
                api_base=self.config.api_base,
                max_tokens=self.config.max_tokens,
            )
        key = self.config.api_key
        if not key:
            self.logger.warn("CODECK_API_KEY not set. Set it or use CODECK_MODEL=ollama/...")
            return None
        return OpenAIBackend(
            api_key=key,
            model=model,
            api_base=self.config.api_base,
            max_tokens=self.config.max_tokens,
        )

    async def process(self, user_input: str) -> str:
        if not user_input or not user_input.strip():
            return ""
        user_input = user_input.strip()
        if user_input.startswith("/"):
            return self._handle_meta(user_input)
        return await self.orchestrator.process_input(user_input)

    def _handle_meta(self, cmd: str) -> str:
        cmd = cmd.lower().strip()
        if cmd in ("/exit", "/quit"):
            raise SystemExit(0)
        if cmd == "/help":
            return ("**CodeC Commands:**\n"
                    "  `/help`      - Show this help\n"
                    "  `/exit`      - Exit CodeC\n"
                    "  `/clear`     - Clear conversation\n"
                    "  `/status`    - Show agent state\n"
                    "  `/log`       - Show recent logs\n"
                    "  `/config`    - Show configuration\n"
                    "  `/tools`     - List available tools\n"
                    "  `/memory`    - Show session memory\n"
                    "  `/guardian`  - Show sandbox restrictions\n"
                    "  `/project`   - Show project summary\n"
                    "  `/cost`      - Show token usage and cost\n"
                    "  `/context`   - Show context window info")
        if cmd == "/clear":
            self.state_manager.clear_history()
            return "Cleared."
        if cmd == "/status":
            s = self.state_manager.get_summary()
            cost = self.cost_tracker.format_summary()
            return (f"Cognitive: {s['cognitive_state']} | "
                    f"Tasks: {s['tasks']['completed']}/{s['tasks']['total']} | "
                    f"LLM: {self.llm_backend.name if self.llm_backend else 'none'} | "
                    f"Turns: {s['conversation_length']}\n{cost}")
        if cmd == "/log":
            logs = self.logger.get_recent(15)
            return "\n".join(logs) if logs else "No logs."
        if cmd == "/config":
            return (f"Model: {self.config.model}\n"
                    f"API: {self.config.api_base}\n"
                    f"Max Tokens: {self.config.max_tokens}\n"
                    f"Log Level: {self.config.log_level}\n"
                    f"Project: {self.project_dir}")
        if cmd == "/tools":
            from codec.tools.registry import registry
            return "\n".join(f"- `{n}`: {d}" for n, d in sorted(registry.list_tools().items()))
        if cmd == "/memory":
            mem = self.memory.recall_all()
            return "\n".join(f"- {k}: {v}" for k, v in mem.items()) if mem else "(empty)"
        if cmd == "/guardian":
            return self.guardian.describe_restrictions()
        if cmd == "/project":
            summary = self.code_interface.summarize_project()
            return (f"Files: {summary['total_files']} | Lines: {summary['total_lines']}\n"
                    + "\n".join(f"  {lang}: {count}" for lang, count in summary['languages'].items()))
        if cmd == "/cost":
            return self.cost_tracker.format_summary()
        if cmd == "/context":
            return self.context_manager.format_limit_info()
        return f"Unknown: {cmd}. Try /help"

    async def cleanup(self):
        self.state_manager.set_cognitive_state(CognitiveState.IDLE)
        self.logger.info("Session ended")
