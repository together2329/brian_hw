# Brian Coder Agent (Zero-Dependency)

A lightweight AI agent designed for restricted Linux environments (no `sudo`, no `pip`).
**No external dependencies required.** It uses Python's standard library.

## Deployment Instructions

1. **Copy the Folder**: Copy the `brian_coder` directory to your target Linux machine.
   ```bash
   scp -r brian_coder user@target-machine:~/
   ```

2. **Configuration**:
   - The agent connects to an OpenAI-compatible LLM API (e.g., Qwen, Llama, vLLM).
   - Edit `src/config.py` or set environment variables:
     ```bash
     export LLM_BASE_URL="https://openrouter.ai/api/v1"
     export LLM_API_KEY="sk-or-v1-..."
     export LLM_MODEL_NAME="meta-llama/llama-3.3-70b-instruct:free" 
     ```

3. **Running**:
   ```bash
   cd brian_coder
   python3 src/main.py
   ```

## Features
- **Zero Dependencies**: Runs on any standard Python 3 installation.
- **ReAct Agent**: Can read/write files and run commands.
- **Tools**:
    - `read_file(path)`
    - `write_file(path, content)`
    - `run_command(command)`
    - `list_dir(path)`

## Optional Settings (Env Vars)
- **Parallel tool execution (multi-Action)**:
  - `ENABLE_REACT_PARALLEL=true|false`
  - `REACT_MAX_WORKERS=5`
  - `REACT_ACTION_TIMEOUT=30`
- **Claude Code style flow (Plan → Approve → Execute)**:
  - `CLAUDE_FLOW_MODE=off|auto|always`
  - `CLAUDE_FLOW_REQUIRE_APPROVAL=true|false`
  - `CLAUDE_FLOW_AUTO_EXECUTE=true|false`
  - `CLAUDE_FLOW_COMPLEX_TASK_CHAR_THRESHOLD=120`
  - `CLAUDE_FLOW_STEP_MAX_ITERATIONS=25`
- **Safe mode (blocks destructive commands)**:
  - `SAFE_MODE=true|false`
