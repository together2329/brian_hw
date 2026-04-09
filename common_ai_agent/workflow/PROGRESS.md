# Workflow Workspace System — Progress

**Branch**: `feature_workflow`
**Working dir**: `/Users/brian/Desktop/Project/new_feature/`
**Source**: `/Users/brian/Desktop/Project/brian_hw/common_ai_agent/`
**Verified**: `python3 workflow/integrate.py -w verilog` → 10/10 PASS

---

## Status: COMPLETE ✅

All 12 implementation steps finished. Both locations are in sync:
- `new_feature/workflow/` — source of truth (git branch)
- `brian_hw/common_ai_agent/workflow/` — live copy (where agent runs)

---

## What Was Built

### workflow/ folder structure (40 files)

```
workflow/
├── loader.py                        ✅ WorkspaceConfig, load_workspace(), merge_prompt(),
│                                       patch_todo_rules(), register_script_hooks(),
│                                       TodoTemplateRegistry, _check_script_conditions()
├── integrate.py                     ✅ 10-check verification script
│                                       Usage: python3 workflow/integrate.py -w <name>
│
├── prompts/                         ✅ Shared prompt fragments
│   ├── format.md                    ReAct loop output format rules
│   ├── rules_normal.md              Normal execution mode rules
│   ├── rules_plan.md                Plan mode rules
│   ├── identity.md                  Agent identity string
│   ├── section_experience.md        PAST EXPERIENCE header template
│   ├── section_knowledge.md         RELEVANT KNOWLEDGE header template
│   └── section_skills.md            ACTIVE SKILLS header template
│
├── default/                         ✅ Default workspace (no-op overrides)
│   ├── workspace.json
│   ├── system_prompt.md
│   ├── plan_prompt.md
│   ├── todo_prompt.md               Template key/variable reference doc
│   ├── compression_prompt.md        STRUCTURED_SUMMARY_PROMPT exact content
│   ├── hook_messages.json           All 11 hook message templates
│   ├── rules/default.md
│   └── todo_templates/
│       ├── bugfix.json
│       ├── feature.json
│       └── refactor.json
│
├── verilog/                         ✅ RTL design workspace
│   ├── workspace.json               env overrides, force_skills: [verilog-expert, testbench-expert]
│   ├── system_prompt.md             RTL-specific rules (prepend mode)
│   ├── plan_prompt.md
│   ├── compression_prompt.md
│   ├── hook_messages.json           4 verilog-specific message overrides
│   ├── rules/verilog-workflow.md
│   ├── scripts/
│   │   ├── hooks.json               4 scheduled hooks
│   │   ├── benchmark_tick.sh        Records iter → .benchmark/iterations.jsonl
│   │   ├── post_write.sh            Records .v/.sv write events → writes.jsonl
│   │   ├── error_capture.sh         Snapshots errors → error_snapshots/
│   │   └── benchmark_report.sh      Session summary on session end
│   └── todo_templates/
│       ├── rtl-module.json          4 tasks, last has loop=true, max=10, exit_condition
│       └── testbench.json
│
└── spec-review/                     ✅ Hardware spec review workspace
    ├── workspace.json               force_skills: [pcie-expert, nvme-expert, ucie-expert, spec-navigator]
    ├── system_prompt.md             MANDATORY spec_search, cite §X.Y.Z
    ├── plan_prompt.md
    ├── compression_prompt.md        Preserves section refs verbatim
    ├── rules/spec-review-rules.md   5 strict rules (no memory answers, etc.)
    ├── scripts/
    │   ├── hooks.json
    │   └── post_session.sh          Saves session summary on end
    └── todo_templates/
        └── spec-analysis.json       4 tasks: map → analyze → cross-ref → summarize
```

---

## common_ai_agent Source Patches Applied

| File | What changed |
|------|-------------|
| `src/config.py` | `_apply_workspace_env_early()` — applies workspace.json env BEFORE load_env_file() |
| `src/main.py` | `_workspace_config`, `_setup_workspace(name)`, `-w/--workspace` argparse |
| `core/hooks.py` | `_get_hook_message()` helper + replaced 3 hardcoded messages |
| `core/compressor.py` | `_load_default_compression_prompt()` — loads from workflow/default/ first |
| `core/skill_system/loader.py` | `extra_dirs: list` in SkillLoader |
| `core/slash_commands.py` | `/todo templates` list + `/todo template <name>` load |
| `lib/todo_tracker.py` | 5 loop fields in TodoItem, loop state machine in mark_completed(), get_active_form(), to_dict() serialization, get_continuation_prompt() loop branch |

---

## Key Design Decisions

- **No circular imports**: hook messages stored in `builtins._WORKSPACE_HOOK_MESSAGES` so hooks.py never imports from workflow/
- **Config priority**: shell env > workspace.json [env] > .config > .env (via _apply_workspace_env_early)
- **Prompt merge modes**: prepend / append / replace — verilog uses prepend, spec-review uses replace
- **Loop state machine**: `mark_completed(tool_output=...)` → exit_condition check → approved or in_progress restart
- **Script hook conditions**: 7 condition types (tool_names, file_extensions, every_n_iterations, min/max_iteration, output_contains, output_not_contains)
- **TodoTemplateRegistry** methods: `list()` / `list_templates()` / `get()` / `get_template()` / `get_tasks()` (aliases for compatibility)

---

## How to Use

```bash
# Run verification
cd common_ai_agent
python3 workflow/integrate.py -w verilog     # all checks
python3 workflow/integrate.py -w spec-review

# Run with workspace
python3 src/main.py                          # no workspace (default behavior)
python3 src/main.py -w default              # explicit default
python3 src/main.py -w verilog             # RTL mode
python3 src/main.py -w spec-review         # spec review mode

# In-session slash commands
/todo templates                             # list available templates
/todo template rtl-module                   # load 4-task RTL workflow (loop on sim)
/todo template spec-analysis               # load 4-task spec analysis workflow
```

---

## Todo Loop Example

```
/todo template rtl-module
# → Task 4: "Simulation passed: 0 errors, 0 warnings" with loop=true

# Attempt 1 — sim fails:
todo_update(index=4, status="completed", tool_output="Error: undeclared signal")
# → exit_condition "0 errors, 0 warnings" NOT in output → loop_count=1, back to in_progress

# Attempt 2 — sim passes:
todo_update(index=4, status="completed", tool_output="Simulation: 0 errors, 0 warnings")
# → exit_condition met → status=approved automatically
```

---

## Remaining / Future Work

Nothing blocking. Possible extensions if needed:
- `workflow/prompts/` fragments not yet wired into `build_base_system_prompt()` — currently informational only
- No `verilog/system_prompt.md` content verified against actual verilog-expert skill (manual review recommended)
- Benchmark `.jsonl` output format not yet consumed by any visualization tool
- `/todo template` does not yet merge with existing todos (always appends) — could add `--replace` flag
