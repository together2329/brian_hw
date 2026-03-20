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

## API Setup

### OpenAI

```bash
export LLM_BASE_URL="https://api.openai.com/v1"
export LLM_API_KEY="sk-proj-YOUR_KEY"
export LLM_MODEL_NAME="gpt-4o-mini"
```

Models: `gpt-4o-mini` (fast, cheap), `gpt-4o` (powerful)

### OpenRouter

```bash
export LLM_BASE_URL="https://openrouter.ai/api/v1"
export LLM_API_KEY="sk-or-v1-YOUR_KEY"
export LLM_MODEL_NAME="openrouter/z-ai/glm-4.7"
```

Free models: `meta-llama/llama-3.3-70b-instruct:free`, `google/gemini-flash-1.5:free`

### Local / vLLM

```bash
export LLM_BASE_URL="http://localhost:8000/v1"
export LLM_API_KEY="none"
export LLM_MODEL_NAME="your-model-name"
```

Any OpenAI-compatible API endpoint works.

### Sub-Agent Models

```bash
export PRIMARY_MODEL="openrouter/z-ai/glm-4.7"
export SUBAGENT_LOW_MODEL="openrouter/qwen/qwen3-next-80b-a3b-instruct"
export SUBAGENT_HIGH_MODEL="openrouter/z-ai/glm-4.7"
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
