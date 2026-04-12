# Common AI Agent

A lightweight AI coding agent with a hardware design workflow system for RTL/verification engineers.

## Quick Start

```bash
cd common_ai_agent

# Terminal mode
python3 src/main.py

# TUI mode (recommended)
python3 src/textual_main.py
```

Configure via environment variables or `.env` file. See `.env.example` for all options.

---

## Hardware Design Workflow

Six specialized workspaces cover the full IP development lifecycle:

```
REQ → MAS → RTL → TB → SIM / LINT
```

| Workspace | `-w` name | Role | Start Command |
|-----------|-----------|------|---------------|
| **req_gen** | `req_gen` | Iterative requirement gathering with user | `/new-req` |
| **mas_gen** | `mas_gen` | Micro Architecture Spec authoring | `/new-ip` |
| **rtl_gen** | `rtl_gen` | SystemVerilog RTL implementation | `/new-ip-rtl` |
| **tb_gen**  | `tb_gen`  | Testbench + test case generation | `/new-ip-tb` |
| **sim**     | `sim`     | Compilation + simulation debug loop | `/compile` |
| **lint**    | `lint`    | Verilator lint check + fix | `/lint-all` |

### Launch a workspace

```bash
python3 src/textual_main.py -w req_gen    # gather requirements
python3 src/textual_main.py -w mas_gen    # write MAS
python3 src/textual_main.py -w rtl_gen    # implement RTL
python3 src/textual_main.py -w tb_gen     # generate TB
python3 src/textual_main.py -w sim        # simulate
python3 src/textual_main.py -w lint       # lint check
```

### IP Directory Structure

Every IP is organized under a single folder:

```
<ip_name>/
├── req/        ← req_gen writes <ip>_requirements.md
├── mas/        ← mas_gen writes <ip>_mas.md
├── rtl/        ← rtl_gen writes <ip>.sv
├── list/       ← rtl_gen writes <ip>.f  (filelist for sim/lint)
├── tb/         ← tb_gen writes tb_<ip>.sv, tc_<ip>.sv
├── sim/        ← sim writes sim_report.txt
└── lint/       ← lint writes lint_report.txt
```

### Workflow Commands

**req_gen**
| Command | Alias | Description |
|---------|-------|-------------|
| `/new-req` | `nr` | Start new requirement gathering (Phase 1–9 iterative) |
| `/refine-req` | `rr` | Fill gaps in existing requirements file |

**mas_gen**
| Command | Alias | Description |
|---------|-------|-------------|
| `/new-ip` | `ni` | New IP MAS: §1–§9 section-by-section |
| `/legacy-ip` | `li` | Legacy IP MAS delta update |

**rtl_gen**
| Command | Alias | Description |
|---------|-------|-------------|
| `/new-ip-rtl` | `nir` | New IP RTL from MAS §2–§8 |
| `/legacy-ip-rtl` | `lir` | Legacy IP RTL delta changes |
| `/lint` | `l` | Run lint on current RTL |

**tb_gen**
| Command | Alias | Description |
|---------|-------|-------------|
| `/new-ip-tb` | `nit` | New IP TB from MAS §9 DV Plan |
| `/legacy-ip-tb` | `lit` | Legacy IP TB regression update |
| `/sim` | `s` | Run simulation |

**sim**
| Command | Alias | Description |
|---------|-------|-------------|
| `/compile` | `c` | Compile with filelist |
| `/sim` | `s` | Run simulation |
| `/report` | `r` | Write sim_report.txt |

**lint**
| Command | Alias | Description |
|---------|-------|-------------|
| `/lint-all` | `la` | Lint all files in filelist |
| `/lint-file` | `lf` | Lint a single file |
| `/report` | `r` | Write lint_report.txt |

---

## Agent Features

- **ReAct Agent Loop**: Thought → Action → Observation cycle
- **Streaming Output**: Real-time token display
- **Todo System**: Section-by-section task tracking with detail + criteria per task
- **Workspace System**: Per-workflow system prompts, rules, scripts, and todo templates
- **Slash Commands**: `/help`, `/todo`, `/plan`, `/compact`, `/workspace`, and workspace-specific commands
- **Tab Autocomplete**: `/` triggers command dropdown, `@` triggers file completion
- **TUI Mode**: Full Textual-based terminal UI with todo sidebar and context bar
- **Sub-Agent System**: explore, plan, execute, review agents

---

## Tools

- `read_file`, `read_lines`, `write_file`, `replace_in_file`
- `grep_file`, `find_files`, `list_dir`
- `run_command`, `git_status`, `git_diff`
- `background_task` (sub-agent delegation)
- Verilog analysis tools (verilog-expert skill)

---

## API Setup

Supports any OpenAI-compatible API endpoint.

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

---

## Configuration

```bash
export MAX_ITERATIONS=100        # Max ReAct loop iterations
export RATE_LIMIT_DELAY=5        # Seconds between API calls
export SAFE_MODE=true            # Block destructive commands
export DEBUG_MODE=false          # Verbose logging
```

---

## Project Structure

```
common_ai_agent/
├── src/          — main.py, textual_main.py, config.py, llm_client.py
├── core/         — tools, agent_runner, session_manager, slash_commands, hooks
├── lib/          — textual_ui, todo_tracker, display
├── workflow/     — workspace definitions
│   ├── req_gen/  — requirement gathering
│   ├── mas_gen/  — micro architecture spec
│   ├── rtl_gen/  — RTL implementation
│   ├── tb_gen/   — testbench generation
│   ├── sim/      — simulation
│   └── lint/     — lint check
├── skills/       — pluggable skill system (verilog-expert, etc.)
└── tests/        — pytest test suite
```

---

## Troubleshooting

| Error | Fix |
|-------|-----|
| HTTP 401 | Check API key |
| HTTP 429 | Increase `RATE_LIMIT_DELAY` (default: 5s) |
| Model not found | Check model name for provider |
| Timeout | Check `LLM_BASE_URL` connectivity |
| Workspace not found | Run from `common_ai_agent/` directory |
