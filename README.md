# Common AI Agent (Zero-Dependency)

A lightweight AI coding agent. **No external dependencies** — runs on Python's standard library only.

## Quick Start

```bash
cd common_ai_agent
python3 src/main.py
```

Configure via environment variables or `.env` file. See `.env.example` for all options.

## Features

- **Zero Dependencies**: Standard Python 3.8+ only
- **ReAct Agent Loop**: Thought → Action → Observation cycle
- **Streaming Output**: Real-time token display
- **Sub-Agent System**: explore, plan, execute, review agents
- **Cross-Platform**: Windows, macOS, Linux support
- **Tools**:
  - `read_file`, `read_lines`, `write_file`, `replace_in_file`
  - `grep_file`, `find_files`, `list_dir`
  - `run_command`, `git_status`, `git_diff`
  - `background_task` (sub-agent delegation)
  - Verilog analysis tools (optional plugin)

## Usage

### Basic Conversation

```
> read dma/rtl/dma_top.v and explain the architecture
```

The agent uses Thought → Action → Observation loops to complete tasks autonomously.

### Explore Agent

Delegate read-only codebase exploration to a specialized sub-agent:

```
> use explore agent to check this directory
> use explore agent to analyze the DMA module
```

The explore agent uses `list_dir`, `find_files`, `grep_file`, `read_file` to investigate the codebase and returns a structured summary.

### Slash Commands

```
/help          — Show available commands
/status        — Show agent status (model, tools, context)
/compact       — Compress conversation history
/clear         — Clear conversation
/plan          — Enter plan mode for complex tasks
/exit          — Exit the agent
```

### Keyboard Shortcuts

- **ESC** — Abort current LLM inference mid-stream
- **Ctrl+C** — Exit the agent

### Multi-Agent Delegation

The primary agent can delegate tasks to specialized sub-agents:

| Agent | Role | Tools |
|-------|------|-------|
| **explore** | Read-only codebase analysis | read, grep, find, list |
| **plan** | Strategy and planning | none (reasoning only) |
| **execute** | Full tool access | all tools |
| **review** | Code review | read, grep |

```
> use explore agent to find all Verilog modules
> create a plan to refactor the DMA controller
```

## API Setup

Supports any OpenAI-compatible API endpoint (OpenAI, OpenRouter, vLLM, etc.).

```bash
export LLM_BASE_URL="your-api-base-url"
export LLM_API_KEY="your-api-key"
export LLM_MODEL_NAME="your-model-name"
```

### Sub-Agent Models

```bash
export PRIMARY_MODEL="primary-model"
export SUBAGENT_LOW_MODEL="low-cost-model"
export SUBAGENT_HIGH_MODEL="high-reasoning-model"
```

## Configuration

```bash
export MAX_ITERATIONS=100        # Max ReAct loop iterations
export RATE_LIMIT_DELAY=5        # Seconds between API calls
export SAFE_MODE=true            # Block destructive commands
export DEBUG_MODE=false          # Verbose logging
```

## Project Structure

```
common_ai_agent/
├── src/          — main.py, config.py, llm_client.py
├── core/         — tools, agent_runner, session_manager, hooks
├── lib/          — display, memory, todo_tracker
├── agents/       — sub-agent prompts (explore, plan, execute, review)
├── skills/       — pluggable skill system
└── tests/        — 142+ cross-platform tests
```

## Troubleshooting

| Error | Fix |
|-------|-----|
| HTTP 401 | Check API key |
| HTTP 429 | Increase `RATE_LIMIT_DELAY` (default: 5s) |
| Model not found | Check model name for provider |
| Timeout | Check `LLM_BASE_URL` connectivity |
