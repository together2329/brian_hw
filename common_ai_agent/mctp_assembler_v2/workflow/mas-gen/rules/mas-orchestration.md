# MAS Orchestration Rules

MAS is a legacy planning surface. New production IP flow must use
`workflow/COMMON_ENGINE_FLOW.md`: requirements -> SSOT -> functional model ->
equivalence goals -> RTL -> lint -> cocotb/pyuvm TB -> sim -> sim-debug ->
goal-audit. Do not hand off to `/new-ip-rtl`, `/legacy-ip-rtl`, `/new-ip-tb`,
or `/legacy-ip-tb`; those command entry points are removed.

## Workflow Model

Each stage runs in its own workspace. mas-gen is responsible for:
1. Writing the MAS document — the single source of truth
2. Outputting [MAS HANDOFF] blocks to tell the user which workspace to switch to next
3. Reviewing results when other workspaces report back

You do NOT switch context internally. You hand off via explicit [MAS HANDOFF] messages.

## Handoff Protocol

When MAS is complete and ready for the next stage, output:

```
[MAS HANDOFF] → rtl-gen
Module  : <ip_name>
MAS     : <ip_name>/mas/<ip_name>_mas.md
Task    : Implement RTL from MAS §2-§8
Input   : <ip_name>/mas/<ip_name>_mas.md
Output  : <ip_name>/rtl/<ip_name>.sv, <ip_name>/list/<ip_name>.f
Switch  : /workspace rtl-gen -> /ssot-rtl <ip_name>
```

## Quality Gates

| Gate | Condition | Next workspace |
|------|-----------|----------------|
| MAS -> RTL | SSOT approved | `rtl-gen` -> `/ssot-rtl <ip>` |
| RTL -> TB | DUT compile/lint pass | `tb-gen` -> `/ssot-tb <ip>` |
| TB → SIM | TB compiles clean | `sim` → `/compile` |
| SIM → LINT | sim: 0 errors, 0 warnings | `lint` → `/lint-all` |

## File Ownership

| Workspace | Writes | Never modifies |
|-----------|--------|----------------|
| `req-gen` | `<ip>/req/<ip>_requirements.md` | everything else |
| `mas-gen` | `<ip>/mas/<ip>_mas.md` | source files |
| `rtl-gen` | `<ip>/rtl/<ip>.sv`, `<ip>/list/<ip>.f` | `tb_*.sv`, `*.md` |
| `tb-gen`  | `<ip>/tb/tb_<ip>.sv`, `<ip>/tb/tc_<ip>.sv` | `<ip>.sv` |
| `sim`     | `<ip>/sim/sim_report.txt` | source files |
| `lint`    | `<ip>/lint/lint_report.txt` | source files |

## Error Recovery

- RTL lint error → user switches to `rtl-gen`, fixes, re-runs `/lint`
- Sim error (DUT bug) → user switches to `rtl-gen`, fixes RTL
- Sim error (TB bug) → user switches to `tb-gen`, fixes TB
- Max sim iterations → output [MAS BLOCKED] report with details
