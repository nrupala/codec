# CodeC Architecture

## System Overview

CodeC is an agentic AI coding assistant with a modular architecture designed for
extensibility, safety, and multi-model LLM support.

```
┌─────────────────────────────────────────────────────┐
│                    CLI / Web / GUI                    │
├─────────────────────────────────────────────────────┤
│                    CodeCEngine                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────────┐  │
│  │Config    │ │State     │ │ Session Guardian     │  │
│  │Loader    │ │Manager   │ │ (path + shell safety) │  │
│  └──────────┘ └──────────┘ └──────────────────────┘  │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────────┐  │
│  │LLM       │ │Cost      │ │ Context Manager      │  │
│  │Backend   │ │Tracker   │ │ (window + compress)  │  │
│  └──────────┘ └──────────┘ └──────────────────────┘  │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────────┐  │
│  │Memory    │ │Diff      │ │ Prompt Engineer      │  │
│  │(JSON TTL)│ │Engine    │ │ (system prompt +     │  │
│  └──────────┘ └──────────┘ │  tool_call parsing)  │  │
│                            └──────────────────────┘  │
├─────────────────────────────────────────────────────┤
│                  OrchestratorAgent                    │
│  ┌─────────────────────────────────────────────────┐ │
│  │  Agentic Loop: Plan → Tool Call → Execute →     │ │
│  │  Verify → Repeat (up to 15 iterations)          │ │
│  └─────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────┤
│                    Tool Registry                      │
│  26 tools: read/write/edit · search · shell · git    │
│  web · plan · test · diff · project analysis         │
├─────────────────────────────────────────────────────┤
│              LLM Backends (pluggable)                 │
│  OpenAI · Anthropic Claude · Ollama (local)          │
└─────────────────────────────────────────────────────┘
```

## Key Components

### CodeCEngine (`codec/engine.py`)
Central orchestrator that initializes all subsystems. Manages the session
lifecycle, routes user input, and handles meta commands.

### OrchestratorAgent (`codec/agents/orchestrator.py`)
The agentic loop core. Receives user input, builds messages with plan context,
calls the LLM, extracts tool calls, executes them, and feeds results back.
Loops until the LLM provides a final response or max iterations reached.

### PromptEngineer (`codec/modules/prompt_engineer.py`)
Builds system prompts with tool definitions, plan context, and rules.
Parses `<tool_call>{"name":"...","arguments":{...}}</tool_call>` XML from LLM
responses. Strips tool calls to extract natural language text.

### StateManager (`codec/modules/state_manager.py`)
Persistent session state with conversation history, task tracking, and
active plan management. Saves to JSON in `.codec/` directory. Supports
cognitive state transitions (analyzing → executing → evaluating → idle).

### SessionGuardian (`codec/session/guardian.py`)
Security layer that:
- Contains file paths to the project directory (prevents escape via `..`)
- Blocks dangerous shell commands (rm -rf /, sudo, mkfs, dd, etc.)
- Allows/denies commands based on blocklist patterns

### SessionMemory (`codec/session/memory.py`)
Persistent key-value store with TTL expiry. Records episodic memories
(user inputs + assistant responses) with keyword search.

### Tool Registry (`codec/tools/registry.py`)
Decorator-based tool registration. All tools are async functions. The registry
maps tool names to functions and descriptions for dynamic system prompt building.

### Hardware Abstraction (`codec/hardware/abstraction.py`)
Detects GPU (NVIDIA CUDA), Neural Engine (Intel OpenVINO), and CPU capabilities.
Used for capability-aware fallback.

## LLM Backends

All backends implement a common interface with `generate_with_metadata(messages)`
returning `{content, model, prompt_tokens, completion_tokens}`.

| Backend | Model Prefix | Requirements |
|---------|-------------|-------------|
| OpenAI | `gpt-4o`, `gpt-4o-mini` | `CODECK_API_KEY` |
| Anthropic | `anthropic/claude-sonnet-4` | `ANTHROPIC_API_KEY` |
| Ollama | `ollama/llama3` | Ollama running on `http://localhost:11434` |

## Plan-Aware Execution Flow

1. LLM calls `create_plan(goal, steps)` to create a structured plan
2. Plan is stored in StateManager and included in subsequent system prompts
3. Each iteration shows plan progress to maintain goal alignment
4. After write/edit operations, verification hint is appended
5. LLM can call `update_plan_step(index, status)` to track progress
6. `run_tests` tool auto-detects and executes test frameworks

## Data Flow

```
User Input → PromptEngineer → Build Messages → LLM → Parse Response
                                                         ↓
                                              Has tool_call? ──yes──→ Execute Tool
                                                         │                  ↓
                                                        no             Feed Result Back
                                                         │                  │
                                                         ↓                  ↓
                                              Return to User ←────────────┘
```
