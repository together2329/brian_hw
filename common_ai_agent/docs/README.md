# Common AI Agent (Zero-Dependency)

A lightweight AI coding agent. **No external dependencies** — runs on Python's standard library only.

## Quick Start

```bash
cd common_ai_agent
export LLM_BASE_URL="https://openrouter.ai/api/v1"
export LLM_API_KEY="sk-or-v1-..."
export LLM_MODEL_NAME="openrouter/z-ai/glm-4.7"
python3 src/main.py
```

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

## Configuration

Set via environment variables or edit `src/config.py`:

```bash
# LLM connection
export LLM_BASE_URL="https://openrouter.ai/api/v1"
export LLM_API_KEY="your-key"
export LLM_MODEL_NAME="openrouter/z-ai/glm-4.7"

# Agent settings
export MAX_ITERATIONS=100        # Max ReAct loop iterations
export RATE_LIMIT_DELAY=5        # Seconds between API calls
export SAFE_MODE=true            # Block destructive commands
export DEBUG_MODE=false          # Verbose logging
```

See [API_SETUP.md](API_SETUP.md) for detailed provider setup.

## Project Structure

```
common_ai_agent/
├── src/          — main.py, config.py, llm_client.py
├── core/         — tools, agent_runner, session_manager, hooks
├── lib/          — display, memory, todo_tracker
├── agents/       — sub-agent prompts (explore, plan, execute, review)
├── skills/       — pluggable skill system
├── tests/        — 142+ cross-platform tests
└── docs/         — documentation
```
