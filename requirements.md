# Requirements — CodeC

## 1. Functional Requirements

### FR1: CLI Interface
- FR1.1: Accept commands via interactive REPL session
- FR1.2: Accept single commands via `-c` flag for scripting
- FR1.3: Display agent responses with markdown formatting in terminal
- FR1.4: Support command history and editing (readline)
- FR1.5: Exit cleanly on `Ctrl+C`, `/exit`, or EOF

### FR2: Prompt Engineering Module
- FR2.1: Construct prompts from raw user input
- FR2.2: Incorporate conversation history context
- FR2.3: Detect task type (coding, qa, file op, shell) from input
- FR2.4: Apply task-specific prompt templates

### FR3: Resource Allocation Module
- FR3.1: Determine whether a task needs LLM inference or direct tool execution
- FR3.2: Route LLM tasks to configured backend (API key, local endpoint)
- FR3.3: Fall back gracefully if primary backend is unavailable
- FR3.4: Report allocation decisions to logging

### FR4: Task Decomposition Engine
- FR4.1: Parse complex multi-step commands into atomic sub-tasks
- FR4.2: Produce dependency graph for sub-tasks
- FR4.3: Execute sub-tasks in dependency order
- FR4.4: Aggregate sub-task results into final response

### FR5: Execution Scheduling Module
- FR5.1: Prioritize tasks by complexity and dependency depth
- FR5.2: Execute tasks concurrently where no dependency exists
- FR5.3: Respect max concurrency limits
- FR5.4: Report schedule and progress to state manager

### FR6: State Management
- FR6.1: Track current task state (pending, running, completed, failed)
- FR6.2: Maintain conversation history across turns
- FR6.3: Track available resources (LLM credits, file handles)
- FR6.4: Persist session state to disk for recovery

### FR7: Action Definition
- FR7.1: Define actions as structured JSON objects
- FR7.2: Support action types: `read_file`, `write_file`, `edit_file`, `run_shell`, `search_code`, `web_fetch`, `ask_user`
- FR7.3: Validate action structure before execution
- FR7.4: Register new action types at runtime

### FR8: Tool Suite
- FR8.1: Read file contents by path
- FR8.2: Write/overwrite file contents
- FR8.3: Edit files via string replacement
- FR8.4: Execute shell commands with timeout and output capture
- FR8.5: Search file contents with regex (grep)
- FR8.6: Find files by glob pattern
- FR8.7: Fetch web URLs and return markdown
- FR8.8: Search the web via configured provider

### FR9: Logging
- FR9.1: Log all module actions with timestamps
- FR9.2: Log tool invocations and results
- FR9.3: Log LLM API calls including tokens and latency
- FR9.4: Rotate log files daily
- FR9.5: Support log levels: DEBUG, INFO, WARN, ERROR

### FR10: Hardware Abstraction Layer
- FR10.1: Define abstract interface for LLM backends
- FR10.2: Support OpenAI-compatible API backend
- FR10.3: Provide stub for FPGA/GPU acceleration backends
- FR10.4: Allow runtime backend selection via config

## 2. Non-Functional Requirements

### NFR1: Performance
- NFR1.1: CLI startup under 500ms
- NFR1.2: Sub-task decomposition under 2s
- NFR1.3: Tool execution overhead under 100ms (excluding LLM latency)
- NFR1.4: Concurrent tool execution for independent sub-tasks

### NFR2: Reliability
- NFR2.1: Graceful handling of LLM API errors with retry (3 attempts)
- NFR2.2: Recovery from interrupted sessions via state persistence
- NFR2.3: Input validation on all user-provided paths

### NFR3: Security
- NFR3.1: API keys read from environment variables only, never logged
- NFR3.2: Shell commands subject to allow/deny list
- NFR3.3: File operations confined to project directory (opt-out)

### NFR4: Maintainability
- NFR4.1: All modules follow single-responsibility principle
- NFR4.2: Public interfaces documented with docstrings
- NFR4.3: Test coverage >80% for core modules
- NFR4.4: Configuration in single `config.py` with env var override

### NFR5: Extensibility
- NFR5.1: New tools added via registry without modifying engine
- NFR5.2: New LLM backends via `BaseLLMBackend` subclass
- NFR5.3: New hardware accelerators via `BaseAccelerator` subclass
- NFR5.4: New agent types via `BaseAgent` subclass

## 3. Technical Requirements

### TR1: Runtime
- Python 3.11+
- Windows 10/11 (primary), Linux, macOS

### TR2: Dependencies
- `openai` — LLM backend
- `rich` — Terminal UI, markdown rendering, syntax highlighting
- `prompt_toolkit` — Interactive CLI with history and autocomplete
- `httpx` — Async HTTP for web fetch and API calls
- `aiofiles` — Async file I/O
- `pyyaml` — Config parsing

### TR3: Configuration
- `CODECK_API_KEY` — LLM API key (env var)
- `CODECK_MODEL` — Model name (default: gpt-4o)
- `CODECK_API_BASE` — Custom API endpoint
- `CODECK_MAX_TOKENS` — Max generation tokens
- `CODECK_LOG_LEVEL` — Logging verbosity
- `CODECK_PROJECT_DIR` — Sandbox directory for file operations
