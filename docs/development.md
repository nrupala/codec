# CodeC Development Guide

## Project Structure

```
codec/
├── codec/
│   ├── __init__.py
│   ├── __main__.py          # Entry point: python -m codec
│   ├── cli.py               # CLI interaction (interactive + single-shot)
│   ├── engine.py            # Core CodeCEngine - initializes all subsystems
│   ├── config.py            # Configuration from env vars
│   ├── agents/
│   │   ├── base.py          # BaseAgent abstract class
│   │   └── orchestrator.py  # Agentic tool loop
│   ├── modules/
│   │   ├── state_manager.py  # Session state, tasks, plans
│   │   ├── prompt_engineer.py# System prompt + tool_call parsing
│   │   ├── task_decomposer.py# Multi-command splitting
│   │   ├── resource_allocator.py
│   │   ├── scheduler.py
│   │   ├── action_definer.py
│   │   └── logger.py
│   ├── tools/
│   │   ├── registry.py      # Decorator-based tool registry
│   │   ├── file_ops.py      # read/write/edit/list
│   │   ├── shell.py         # run_shell
│   │   ├── search.py        # grep_search, glob_files
│   │   ├── web.py           # web_fetch, web_search
│   │   ├── system_tools.py  # project_summary, detect_language, etc.
│   │   ├── git_tools.py     # git_status/diff/log/commit/branch
│   │   ├── differ.py        # diff_file, edit_file_with_diff
│   │   ├── plan_tools.py    # create_plan, update_plan_step, get_plan
│   │   └── testing.py       # run_tests, detect_test_command
│   ├── llm/
│   │   ├── openai_backend.py
│   │   ├── ollama_backend.py
│   │   └── anthropic_backend.py
│   ├── session/
│   │   ├── guardian.py      # Path + shell sandbox
│   │   ├── memory.py        # Persistent key-value store
│   │   ├── cost_tracker.py  # Token/cost tracking
│   │   ├── context_manager.py# Window management + compression
│   │   └── diff_engine.py   # Unified diff computation
│   ├── bridge/
│   │   ├── os_interface.py  # Platform info, project detection
│   │   └── code_interface.py# Language detection, code analysis
│   ├── hardware/
│   │   └── abstraction.py   # GPU/neural engine detection
│   ├── web/
│   │   ├── server.py        # FastAPI web server
│   │   ├── templates/terminal.html  # Web UI template
│   │   └── static/          # CSS + JS
│   └── gui/
│       └── desktop.py       # Tkinter desktop GUI
├── tests/
│   ├── test_basic.py        # Core module tests (46)
│   └── test_advanced.py     # Advanced module tests (31)
├── docs/                    # Documentation
├── requirements.txt
└── README.md
```

## Running Tests

```bash
# All tests
python -m pytest tests/

# With coverage
python -m pytest tests/ --cov=codec

# Specific test file
python -m pytest tests/test_advanced.py -v
```

## Adding a New Tool

1. Create a new file in `codec/tools/` or add to an existing one
2. Use the `@register_tool` decorator:
```python
from codec.tools.registry import register_tool

@register_tool("tool_name", "Description of what the tool does")
async def tool_name(param1: str, param2: int = 0, project_dir: str = ".") -> str:
    # implementation
    return result
```
3. Import the module in `codec/tools/__init__.py`
4. Add signature to `PromptEngineer._get_tool_signature()` in `codec/modules/prompt_engineer.py`
5. Add tests in `tests/test_advanced.py`
6. Add to `test_registry_complete` in `tests/test_basic.py`

## Adding an LLM Backend

1. Create `codec/llm/your_backend.py`
2. Implement async `generate_with_metadata(messages) -> dict`
3. Add initialization to `CodeCEngine._init_llm_backend()` in `codec/engine.py`

## Code Style

- Python 3.11+ with type hints
- Async/await throughout
- No external dependencies beyond requirements.txt
- Functions under 50 lines where possible
- Docstrings on all public functions
- Tests for all tools and modules
