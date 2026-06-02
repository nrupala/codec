# CodeC User Guide

## 1. Overview

CodeC is a modular AI coding assistant that runs in your terminal. It helps with software engineering tasks — reading and writing files, running commands, searching code, and orchestrating complex development workflows through intelligent task decomposition.

## 2. Installation

### Prerequisites
- Python 3.11 or later
- An API key for your preferred LLM provider (OpenAI, Anthropic, etc.)

### Install
```bash
# Clone the repository
git clone <repo-url>
cd codec

# Install dependencies
pip install -r requirements.txt

# Set your API key
export CODECK_API_KEY="sk-..."   # Linux/macOS
set CODECK_API_KEY="sk-..."      # Windows cmd
$env:CODECK_API_KEY="sk-..."     # PowerShell
```

### Verify
```bash
python -m codec --version
```

## 3. Quick Start

### Interactive Mode
```bash
python -m codec
```
You'll see a `»` prompt. Type commands naturally:

```
» read the file src/main.py and summarize it
» find all TODO comments in the codebase
» write a function that sorts a list of integers
» run npm test and fix any failures
```

### Single Command Mode
```bash
python -m codec -c "find all unused imports in src/"
python -m codec -c "explain this repo's architecture" --directory /path/to/project
```

### Session Directory
CodeC creates a `.codec/` directory in your project root to store:
- Session state and history
- Logs
- Configuration overrides

## 4. Commands

### Built-in Commands (Meta)

| Command | Description |
|---------|-------------|
| `/help` | Show this help |
| `/exit` or `Ctrl+C` | Exit the session |
| `/clear` | Clear conversation history |
| `/status` | Show current agent state and resources |
| `/log` | Show recent log entries |
| `/config` | Show current configuration |
| `/retry` | Retry the last response |

### Natural Language Commands

CodeC understands plain English for most tasks:

**File Operations**
```
» read src/app.py
» write src/test.py with a unit test for the Calculator class
» edit src/main.py and change the port from 3000 to 8080
» list all Python files in src/
```

**Code Search**
```
» find all functions that use the database
» search for "TODO" in all files
» show me the implementation of the authenticate method
» find files that import requests
```

**Shell Operations**
```
» run npm install
» run pytest tests/ -v
» show me the git log
» check disk usage
```

**Code Generation**
```
» create a REST API endpoint for user registration in src/api.py
» write a decorator that measures execution time
» generate a SQL query for monthly sales aggregation
» create a Dockerfile for this project
```

**Analysis & Refactoring**
```
» explain how the authentication flow works
» find potential bugs in this code
» suggest improvements for performance
» refactor this function to be async
```

## 5. Features

### 5.1 Task Decomposition
Complex commands are automatically broken into sub-tasks, executed in dependency order:

```
» add user authentication with JWT to the project

→ Sub-task 1: Read current project structure
→ Sub-task 2: Create auth middleware in src/middleware/auth.py
→ Sub-task 3: Create login endpoint in src/routes/auth.py
→ Sub-task 4: Add JWT dependency to requirements.txt
```

### 5.2 Context Management
CodeC remembers the conversation across turns. Reference earlier context naturally:

```
» read src/main.py
» add error handling to the start_server function I just read
```

### 5.3 State Persistence
Sessions are saved automatically. Resume where you left off:
```bash
python -m codec  # resumes last session in current directory
```

### 5.4 Resource Allocation
CodeC decides whether a task needs LLM inference or can be handled directly by tools (reading files, running commands, etc.), optimizing for speed and cost.

## 6. Configuration

Configuration is via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `CODECK_API_KEY` | — | LLM API key (required) |
| `CODECK_MODEL` | `gpt-4o` | Model name |
| `CODECK_API_BASE` | `https://api.openai.com/v1` | API endpoint |
| `CODECK_MAX_TOKENS` | `4096` | Max response tokens |
| `CODECK_LOG_LEVEL` | `INFO` | Log verbosity |
| `CODECK_PROJECT_DIR` | `.` | Working directory |
| `CODECK_ALLOW_SHELL` | `true` | Enable shell commands |
| `CODECK_ALLOW_WEB` | `true` | Enable web access |

## 7. Logging & Monitoring

Logs are written to `.codec/logs/` with daily rotation:

```
.codec/logs/
├── codec-2025-01-01.log
├── codec-2025-01-02.log
└── ...
```

View live logs with `/log` or tail the file directly.

## 8. Architecture Overview

```
User Input → Prompt Engineer → Task Decomposer → Scheduler → Agents → Tools → Response
                  ↑                 ↑               ↑
              Resource Allocator  State Manager  Logger
```

- **Prompt Engineer**: Formats user input with context into an LLM prompt
- **Task Decomposer**: Breaks complex requests into sub-tasks
- **Scheduler**: Orders and executes sub-tasks
- **Agents**: Domain-specific execution logic (coding, analysis, etc.)
- **Tools**: Primitive operations (file I/O, shell, search)
- **State Manager**: Tracks progress across the lifecycle
- **Logger**: Records all activity for debugging and monitoring

## 9. Extending CodeC

### Adding a New Tool
Create a class that implements the tool interface and register it:

```python
from codec.tools.registry import register_tool

@register_tool("my_tool")
async def my_tool(param1: str, param2: int) -> str:
    """Does something useful."""
    return result
```

### Adding a New LLM Backend
Subclass `BaseLLMBackend` and implement `generate()`:

```python
from codec.llm.base import BaseLLMBackend

class MyBackend(BaseLLMBackend):
    async def generate(self, prompt: str, **kwargs) -> str:
        # Your implementation here
        return response
```

## 10. Troubleshooting

| Problem | Solution |
|---------|----------|
| "API key not found" | Set `CODECK_API_KEY` environment variable |
| "Model not available" | Check `CODECK_MODEL` is valid for your API |
| Slow responses | Reduce `CODECK_MAX_TOKENS` or switch to faster model |
| Shell commands blocked | Set `CODECK_ALLOW_SHELL=true` |
| File outside project | Move within `CODECK_PROJECT_DIR` or adjust config |
