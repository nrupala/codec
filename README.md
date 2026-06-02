# CodeC — Agentic AI Coding Assistant

CodeC is a production-grade, multi-model AI coding assistant that helps you build
software through an agentic tool loop. It plans, executes, verifies, and iterates
autonomously — accessible via CLI, Web UI, or Desktop GUI.

## Features

- **Agentic Tool Loop** — Plans steps, calls tools, feeds results back to the LLM,
  and iterates until completion (up to 15 iterations)
- **Plan-First Architecture** — Creates structured plans, tracks progress, stays on goal
- **Verification Loop** — Auto-detects test frameworks, runs tests, suggests verification
- **26 Tools** — File ops, search, shell, git, web, testing, planning, code analysis
- **Multi-Model** — OpenAI GPT-4o, Anthropic Claude, Ollama (local)
- **Session Guardian** — Path containment + shell command safety
- **Context Management** — Token estimation, auto-compression at 70% threshold
- **Cost Tracking** — Per-model token/cost persistence
- **Three Interfaces** — CLI, Web UI (FastAPI), Desktop GUI (Tkinter)
- **Hardware Abstraction** — GPU/Neural Engine detection
- **Cross-Platform** — Windows, macOS, Linux
- **77 Tests** — Comprehensive test suite

## Quick Start

```bash
pip install -r requirements.txt

# Interactive CLI (OpenAI)
set CODECK_API_KEY=sk-your-key
python -m codec

# Web UI
python -m codec --web

# Desktop GUI
python -m codec --gui

# Single command
python -m codec -c "list all Python files"
```

## Documentation

| Document | Description |
|----------|-------------|
| [User Guide](docs/user-guide.md) | Installation, usage, workflows |
| [Architecture](docs/architecture.md) | System design, components, data flow |
| [Tool Reference](docs/tool-reference.md) | All 26 tools with parameters |
| [Development](docs/development.md) | Project structure, adding tools/backends |

## Models

| Provider | Model Name | Env Variable |
|----------|-----------|-------------|
| OpenAI | `gpt-4o` (default) | `CODECK_API_KEY` |
| Anthropic | `anthropic/claude-sonnet-4-20250514` | `ANTHROPIC_API_KEY` |
| Ollama | `ollama/llama3` | (no key needed) |

## License

MIT
