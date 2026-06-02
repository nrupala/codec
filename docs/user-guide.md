# CodeC User Guide

## Installation

```bash
git clone <repo-url> codec
cd codec
pip install -r requirements.txt
```

## Quick Start

Set your API key and run:

```bash
# With OpenAI (recommended)
set CODECK_API_KEY=sk-your-key-here
python -m codec

# Web UI
python -m codec --web

# Desktop GUI
python -m codec --gui
```

## Command Line Usage

```bash
# Interactive mode
python -m codec

# Single command
python -m codec -c "list all Python files"

# Specify project directory
python -m codec --directory /path/to/project

# Launch web UI on custom port
python -m codec --web --web-port 9000

# Launch desktop GUI
python -m codec --gui
```

## Meta Commands

| Command | Description |
|---------|-------------|
| `/help` | Show all commands |
| `/exit` | Exit CodeC |
| `/clear` | Clear conversation |
| `/status` | Show agent state and costs |
| `/log` | Show recent logs |
| `/config` | Show current configuration |
| `/tools` | List all available tools |
| `/memory` | Show session memory |
| `/guardian` | Show sandbox restrictions |
| `/project` | Show project summary |
| `/cost` | Show token usage and cost |
| `/context` | Show context window info |

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `CODECK_API_KEY` | OpenAI API key | — |
| `ANTHROPIC_API_KEY` | Anthropic API key | — |
| `CODECK_MODEL` | Model name | `gpt-4o` |
| `CODECK_API_BASE` | API base URL | — |
| `CODECK_MAX_TOKENS` | Max tokens per response | `4096` |
| `CODECK_LOG_LEVEL` | Log level (debug/info/warn/error) | `info` |
| `CODECK_PROJECT_DIR` | Project directory | current dir |

## Models

Use `CODECK_MODEL` to select:

- **OpenAI**: `gpt-4o`, `gpt-4o-mini`, `gpt-4-turbo`
- **Anthropic**: `anthropic/claude-sonnet-4-20250514`
- **Ollama**: `ollama/llama3`, `ollama/codellama`, `ollama/mistral`

## Workflow

### Step 1: Understanding
Tell CodeC what you want to do. Be specific:
```
Add a REST API endpoint at /api/users that returns a list of users from the database
```

### Step 2: Planning (Automatic)
CodeC will create a plan:
```
Plan created: Add /api/users endpoint
  Step 1: Read current API structure [pending]
  Step 2: Create route handler [pending]
  Step 3: Add database query [pending]
  Step 4: Add tests [pending]
  Step 5: Run tests to verify [pending]
```

### Step 3: Execution
CodeC executes each step, reading files, writing code, and running tests.

### Step 4: Verification
After changes, CodeC suggests running `run_tests` to verify.

### Step 5: Iteration
Review results and ask for refinements:
```
Add pagination support with page and limit parameters
```

## Tool Categories

### File Operations
`read_file`, `write_file`, `edit_file`, `edit_file_with_diff`, `diff_file`,
`list_files`, `glob_files`

### Search
`grep_search`, `web_search`, `web_fetch`

### Shell
`run_shell`

### Testing
`run_tests`, `detect_test_command`

### Git
`git_status`, `git_diff`, `git_log`, `git_commit`, `git_branch`

### Planning
`create_plan`, `update_plan_step`, `get_plan`

### Project Analysis
`project_summary`, `detect_language`, `find_functions`, `count_lines`,
`find_imports`

## Web UI

The web UI provides a terminal-style interface in your browser:

```bash
python -m codec --web
# Open http://localhost:8512
```

Features:
- Dark theme terminal-style chat
- Real-time responses
- Markdown rendering (code blocks, inline code, bold)
- Connection status indicator
- Keyboard shortcut: Enter to send

## Desktop GUI

The desktop GUI provides a standalone window:

```bash
python -m codec --gui
```

Features:
- Native Tkinter window (no extra dependencies)
- Dark theme matching web UI
- Scrolled output with color-coded messages
- Keyboard shortcut: Enter to send
- Cross-platform (Windows, macOS, Linux)

## Session Files

CodeC stores session data in `.codec/` in the project directory:

| File | Description |
|------|-------------|
| `state.json` | Session state (plan, cognitive state, metadata) |
| `history.jsonl` | Conversation history |
| `memory.json` | Persistent key-value memory |
| `costs.json` | Token usage and cost data |
| `codec.log` | Session logs |
