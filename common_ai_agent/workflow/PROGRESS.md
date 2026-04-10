# Workflow Workspace System — Progress

**Branch**: `feature_workflow`
**Working dir**: `/Users/brian/Desktop/Project/brian_hw_modifiable/common_ai_agent/`
**Verified**: `python3 workflow/integrate.py -w verilog` → 13/13 PASS

---

## Status: Phase 2 COMPLETE ✅

All Phase 1 + Phase 2 implementation steps finished.

---

## What Was Built

### Phase 1 — Workspace Foundation

| File | What changed |
|------|-------------|
| `workflow/loader.py` | `WorkspaceConfig`, `load_workspace()`, `merge_prompt()`, `patch_todo_rules()`, `register_script_hooks()`, `TodoTemplateRegistry`, `_check_script_conditions()` |
| `workflow/integrate.py` | 13-check verification script |
| `workflow/prompts/` | Shared prompt fragments (identity, format, rules_normal, rules_plan) |
| `workflow/default/` | Default workspace (workspace.json, system_prompt, plan_prompt, compression_prompt, hook_messages, rules, todo_templates ×3) |
| `workflow/spec-review/` | Spec review workspace (force_skills: pcie/nvme/ucie-expert) |
| `src/config.py` | `_apply_workspace_env_early()` — workspace env before load_env_file() |
| `src/main.py` | `_workspace_config`, `_setup_workspace(name)`, `-w/--workspace` argparse |
| `core/hooks.py` | `_get_hook_message()` helper + replaced 3 hardcoded messages |
| `core/compressor.py` | `_load_default_compression_prompt()` — loads from workflow/default/ first |
| `core/skill_system/loader.py` | `extra_dirs: list` in SkillLoader |
| `core/slash_commands.py` | `/todo templates` list + `/todo template <name>` load |
| `lib/todo_tracker.py` | 5 loop fields in TodoItem, loop state machine in `mark_completed()`, `get_active_form()`, serialization, continuation prompt branch |

### Phase 2 — Harness Engineering System

| Feature | Files | Description |
|---------|-------|-------------|
| **Custom slash commands** | `workflow/loader.py` — `register_workspace_commands()`, `_make_command_handler()` | Loads `commands/*.json` per workspace, registers into SlashCommandRegistry. Handlers: bash/todo-template/prompt |
| **Todo Task Validator** | `lib/todo_tracker.py` — `validator` field + `run_validator()` | Shell command run before mark_completed(); non-zero = auto-reject with reason |
| **Prompt fragment loader** | `src/config.py` — `_load_prompt_fragment()` | Loads `workflow/prompts/<file>` into identity/format/rules sections with hardcoded fallback |
| **Plan mode rules** | `workflow/prompts/rules_plan.md` | 8 plan-mode-specific rules, injected before PLAN_MODE_PROMPT |
| **main.py wiring** | `src/main.py` step 10 | `register_workspace_commands(ws, slash_registry)` called in `_setup_workspace()` |
| **verilog workspace** | `workflow/verilog/` | RTL dev workspace — see structure below |

---

## workflow/verilog/ Structure

```
workflow/verilog/
├── workspace.json               env: MAX_ITERATIONS=200, skills.force_activate: [verilog-expert]
├── system_prompt.md             20 RTL rules (nonblocking/blocking, synthesis-safe, sim, lint)
├── plan_prompt.md               7 RTL plan-mode rules (loop tasks, validators)
├── compression_prompt.md        Preserves module names, port lists, sim status, file paths
├── rules/
│   └── verilog-workflow.md      Design/sim/lint/loop-task workflow rules
├── commands/
│   ├── lint.json                /lint [file.v] → bash:scripts/lint.sh
│   ├── sim.json                 /sim [tb.sv]   → bash:scripts/sim.sh
│   └── report.json              /report        → bash:scripts/benchmark_report.sh
├── scripts/
│   ├── hooks.json               3 hooks: post_write (.v/.sv), benchmark_tick (every iter), error_capture (on run_command errors)
│   ├── benchmark_tick.sh        Records iteration timestamp → .benchmark
│   ├── post_write.sh            Logs RTL file writes → .benchmark
│   ├── error_capture.sh         Snapshots error lines from tool output → .benchmark
│   ├── benchmark_report.sh      Session summary (iters, sim pass/fail, writes, error snaps)
│   ├── lint.sh                  Lint via verilator or iverilog; logs result
│   ├── sim.sh                   Compile+run simulation; logs PASS/FAIL
│   └── check_sim_pass.sh        Validator: checks TOOL_OUTPUT contains "0 errors, 0 warnings"
└── todo_templates/
    ├── rtl-module.json           5 tasks: interface → internals → testbench → sim-loop (validator) → lint
    └── testbench.json            4 tasks: scenarios → write tb → sim-loop (validator) → coverage
```

---

## Key Design Decisions

- **No circular imports**: hook messages stored in `builtins._WORKSPACE_HOOK_MESSAGES`
- **Config priority**: shell env > workspace.json [env] > .config > .env
- **Prompt merge modes**: prepend / append / replace
- **Loop state machine**: `mark_completed(tool_output=...)` → exit_condition check → approved or in_progress restart
- **Validator = assertion**: shell cmd, returncode != 0 → auto-reject, stderr = rejection_reason
- **Commands = fixtures**: JSON spec → callable handler registered in SlashCommandRegistry at session start
- **Script hook conditions**: 7 types (tool_names, file_extensions, every_n_iterations, min/max_iteration, output_contains, output_not_contains)
- **Prompt fragments**: `_load_prompt_fragment(filename)` → workspace override → shared workflow/prompts/ → hardcoded fallback

---

## How to Use

```bash
# Verification
cd common_ai_agent
python3 workflow/integrate.py              # default workspace
python3 workflow/integrate.py -w verilog   # 13/13 PASS

# Run with workspace
python3 src/main.py                        # no workspace
python3 src/main.py -w default            # explicit default
python3 src/main.py -w verilog           # RTL mode (MAX_ITERATIONS=200, verilog-expert)
python3 src/main.py -w spec-review       # spec review mode

# In-session — verilog workspace commands
/lint [file.v]                            # RTL lint via verilator/iverilog
/sim [tb.sv]                             # Run simulation, log to .benchmark
/report                                  # Session benchmark summary

# Todo templates
/todo templates                           # list available
/todo template rtl-module                # 5-task RTL workflow (loop+validator on sim)
/todo template testbench                 # 4-task testbench workflow
/todo template spec-analysis            # spec-review workspace template
```

---

## Todo Loop + Validator Example

```
/todo template rtl-module
# Task 4: "Simulation passed: 0 errors, 0 warnings"
# loop=true, max_loop_iterations=10, validator="bash scripts/check_sim_pass.sh"

# Attempt 1 — sim fails:
todo_update(index=4, status="completed", tool_output="Error: undeclared signal")
# → validator runs: exit 1 → auto-rejected with reason
# → exit_condition NOT met → loop_count=1, back to in_progress

# Attempt N — sim passes:
todo_update(index=4, status="completed", tool_output="Simulation: 0 errors, 0 warnings")
# → validator runs: exit 0 → OK
# → exit_condition met → status=approved
```
