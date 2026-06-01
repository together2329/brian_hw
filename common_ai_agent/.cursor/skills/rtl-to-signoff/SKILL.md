---
name: rtl-to-signoff
description: Execute or plan the real ATLAS RTL-to-signoff flow from RTL disk checks through TB, sim, lint, coverage, synthesis, STA, PnR, and post-route STA. Use when the user asks for RTL to SignOff, RTL signoff, or full hardware closure.
---

# RTL To Signoff

This is the Cursor entrypoint for a real RTL-to-signoff loop. It follows common_ai_agent workflow semantics:

- DV/equivalence stages call `WorkflowStageEngine.run_stage()`.
- EDA stages call workflow command scripts such as `auto_syn.sh` and `auto_sta.sh`.
- Stage ownership, evidence paths, and profiles come from `STAGE_MANIFEST.json`.
- The generated summary is evidence aggregation, not a replacement validator.
- Sim-debug evidence includes FL-vs-RTL classification plus `sim/simulation_quality.json` from scoreboard semantic checks.

## Read First

- `SIGNOFF_RUNBOOK.md`
- `workflow/COMMON_ENGINE_FLOW.md`
- `doc/wiki/workflow-ownership-and-boundaries.md`
- `doc/wiki/golden-todo-evidence.md`

## Plan The Flow

From `common_ai_agent/`, inspect the commands without running them:

```bash
python3 .cursor/skills/rtl-to-signoff/scripts/rtl_to_signoff.py <ip> --profile full --plan
```

If the IP lives outside `common_ai_agent/`, pass the IP parent:

```bash
python3 .cursor/skills/rtl-to-signoff/scripts/rtl_to_signoff.py <ip> --root .. --profile full --plan
```

## Execute

Run DV/equivalence closure:

```bash
python3 .cursor/skills/rtl-to-signoff/scripts/rtl_to_signoff.py <ip> --root . --profile dv --execute
```

Run EDA closure after DV is green:

```bash
python3 .cursor/skills/rtl-to-signoff/scripts/rtl_to_signoff.py <ip> --root . --profile eda --execute
```

Run the full path:

```bash
python3 .cursor/skills/rtl-to-signoff/scripts/rtl_to_signoff.py <ip> --root . --profile full --execute
```

Run from SSOT generation when the IP does not yet have an approved SSOT:

```bash
python3 .cursor/skills/rtl-to-signoff/scripts/rtl_to_signoff.py <ip> --root . --profile ssot-to-signoff --provider fake --execute
```

## Rules

- Fix failures through the owner shown by the manifest or summary; do not edit evidence to pass.
- Treat pre-existing green JSON as stale after RTL/TB/SSOT changes.
- After TB, sim, RTL, SSOT, or equivalence-goal changes, refresh sim-debug quality evidence before final closure.
- EDA stages may require Linux, PDK paths, Yosys, OpenSTA, OpenROAD, Verilator, and tool env from `.env.example`.
- Final claims must cite fresh `logs/stage_engine/*.json`, EDA command output, or `verify/cursor_rtl_to_signoff_summary.json`.
